import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Dict
import os
from datetime import datetime, timedelta
import akshare as ak
import pickle

def download_stock_data(tickers: List[str], 
                       start_date: str, 
                       end_date: str,
                       cache_dir: str = 'data_cache') -> Dict[str, pd.DataFrame]:
    """
    使用akshare下载A股数据并缓存
    
    参数:
        tickers: 股票代码列表，格式为'sh/sz+6位代码'
        start_date: 开始日期，格式为'YYYY-MM-DD'
        end_date: 结束日期，格式为'YYYY-MM-DD'
        cache_dir: 缓存目录
        
    返回:
        包含OHLCV数据的字典，键为'open', 'high', 'low', 'close', 'volume'
    """
    # 创建缓存目录
    os.makedirs(cache_dir, exist_ok=True)
    
    # 缓存文件路径
    cache_file = f"{cache_dir}/stock_data_A_shares_{start_date}_to_{end_date}.pkl"
    
    # 检查缓存是否存在
    if os.path.exists(cache_file):
        print(f"从缓存加载数据: {cache_file}")
        with open(cache_file, 'rb') as f:
            return pickle.load(f)
    
    print(f"使用akshare下载A股数据...")
    
    # 初始化数据字典
    data_dict = {
        'open': pd.DataFrame(),
        'high': pd.DataFrame(),
        'low': pd.DataFrame(),
        'close': pd.DataFrame(),
        'volume': pd.DataFrame()
    }
    
    # 对每个股票代码获取数据
    for ticker in tickers:
        try:
            # 确保A股代码格式正确（带市场前缀）
            if not (ticker.startswith('sh') or ticker.startswith('sz')):
                if ticker.startswith('6'):
                    ticker = f"sh{ticker}"
                elif ticker.startswith('0') or ticker.startswith('3'):
                    ticker = f"sz{ticker}"
                else:
                    # 对于其他情况，默认为上证
                    ticker = f"sh{ticker}"
            
            # 使用akshare获取A股日线数据
            stock_data = ak.stock_zh_a_daily(symbol=ticker, adjust="qfq")
            
            # 重命名列以匹配我们的格式
            stock_data = stock_data.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '最高': 'high',
                '最低': 'low',
                '收盘': 'close',
                '成交量': 'volume'
            })
            
            # 过滤日期范围
            stock_data['date'] = pd.to_datetime(stock_data['date'])
            stock_data = stock_data[(stock_data['date'] >= start_date) & (stock_data['date'] <= end_date)]
            
            # 设置日期为索引
            stock_data = stock_data.set_index('date')
            
            # 将数据添加到相应的DataFrame中
            for key in data_dict.keys():
                if key in stock_data.columns:
                    data_dict[key][ticker] = stock_data[key]
            
            print(f"成功获取 {ticker} 的数据")
            
        except Exception as e:
            print(f"获取 {ticker} 数据失败: {e}")
    
    # 保存到缓存
    with open(cache_file, 'wb') as f:
        pickle.dump(data_dict, f)
    
    print(f"数据已保存到缓存: {cache_file}")
    
    return data_dict

def load_sample_data() -> Dict[str, pd.DataFrame]:
    """
    加载示例数据（优先从缓存加载，如果缓存不存在则尝试下载，下载失败则生成模拟数据）
    
    返回:
        包含OHLCV数据的字典，键为'open', 'high', 'low', 'close', 'volume'
    """
    # 设置日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365*3)  # 3年数据
    
    # 选择更多A股股票代码，增加样本量
    tickers = [
        # 上证50成分股
        'sh600519', 'sh601318', 'sh600036', 'sh600276', 'sh601166', 
        'sh600887', 'sh601888', 'sh601398', 'sh600030', 'sh601288',
        'sh601628', 'sh601857', 'sh600028', 'sh601988', 'sh601328',
        'sh601088', 'sh600000', 'sh600104', 'sh600050', 'sh601668'
    ]
    
    # 缓存目录
    cache_dir = 'data_cache'
    
    # 缓存文件路径
    cache_file = f"{cache_dir}/stock_data_A_shares_{start_date.strftime('%Y-%m-%d')}_to_{end_date.strftime('%Y-%m-%d')}.pkl"
    
    # 检查缓存是否存在
    if os.path.exists(cache_file):
        print(f"从缓存加载数据: {cache_file}")
        with open(cache_file, 'rb') as f:
            return pickle.load(f)
    
    try:
        # 尝试下载实际数据
        return download_stock_data(tickers, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), cache_dir)
    except Exception as e:
        print(f"无法下载数据: {e}")
        print("生成模拟数据...")
        
        # 生成模拟数据
        dates = pd.date_range(start=start_date, end=end_date, freq='B')
        n_dates = len(dates)
        n_tickers = len(tickers)
        
        # 创建基础价格序列
        base_price = 100 * np.ones((n_dates, n_tickers))
        
        # 添加随机走势
        for i in range(1, n_dates):
            # 每日回报在-2%到2%之间
            daily_returns = np.random.normal(0.0005, 0.015, n_tickers)
            base_price[i] = base_price[i-1] * (1 + daily_returns)
        
        # 创建OHLCV数据
        ohlcv_data = {}
        
        # 收盘价
        close = pd.DataFrame(base_price, index=dates, columns=tickers)
        
        # 开盘价（基于前一天收盘价加上小的随机变动）
        open_prices = close.shift(1) * (1 + np.random.normal(0, 0.005, (n_dates, n_tickers)))
        open_prices.iloc[0] = close.iloc[0] * (1 + np.random.normal(0, 0.005, n_tickers))
        
        # 最高价和最低价
        daily_volatility = 0.015
        high = pd.DataFrame(
            np.maximum(close.values, open_prices.values) * (1 + np.random.uniform(0, daily_volatility, (n_dates, n_tickers))),
            index=dates, columns=tickers
        )
        low = pd.DataFrame(
            np.minimum(close.values, open_prices.values) * (1 - np.random.uniform(0, daily_volatility, (n_dates, n_tickers))),
            index=dates, columns=tickers
        )
        
        # 成交量（与价格波动正相关）
        price_changes = np.abs(close.pct_change().values)
        volume_base = np.random.uniform(1e6, 5e6, (n_dates, n_tickers))
        volume = pd.DataFrame(
            volume_base * (1 + 5 * price_changes),
            index=dates, columns=tickers
        )
        
        # 填充NaN值
        open_prices = open_prices.fillna(method='bfill')
        high = high.fillna(method='bfill')
        low = low.fillna(method='bfill')
        close = close.fillna(method='bfill')
        volume = volume.fillna(method='bfill')
        
        ohlcv_data = {
            'open': open_prices,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        }
        
        # 保存模拟数据到缓存
        os.makedirs(cache_dir, exist_ok=True)
        with open(cache_file, 'wb') as f:
            pickle.dump(ohlcv_data, f)
        
        return ohlcv_data

def save_results(results: Dict, output_dir: str = 'results') -> None:
    """
    保存回测结果
    
    参数:
        results: 回测结果字典
        output_dir: 输出目录
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存相关性矩阵
    if 'correlation_matrix' in results:
        # 直接保存相关性矩阵，不进行额外处理
        results['correlation_matrix'].to_csv(f"{output_dir}/correlation_matrix.csv")
        
        # 绘制相关性热图并立即保存关闭
        correlation_matrix = results['correlation_matrix']
        factor_names = list(correlation_matrix.columns)
        corr_values = correlation_matrix.values
        
        plt.figure(figsize=(10, 8))
        # 使用NumPy数组绘制热图
        im = plt.imshow(corr_values, cmap='coolwarm', vmin=-1, vmax=1)
        
        # 添加颜色条
        plt.colorbar(im)
        
        # 设置坐标轴标签
        plt.xticks(np.arange(len(factor_names)), factor_names, rotation=45)
        plt.yticks(np.arange(len(factor_names)), factor_names)
        
        # 在每个单元格中添加文本，根据值的类型设置不同的格式
        for i in range(len(factor_names)):
            for j in range(len(factor_names)):
                value = corr_values[i, j]
                # 如果值接近整数（差值小于1e-10），则保留1位小数，否则保留4位小数
                if abs(value - round(value)) < 1e-10:
                    text_value = f'{value:.1f}'
                else:
                    text_value = f'{value:.4f}'
                
                plt.text(j, i, text_value,
                       ha="center", va="center", color="black")
        
        plt.title('Factor Correlation Matrix')
        plt.tight_layout()
        plt.savefig(f"{output_dir}/correlation_matrix.png", dpi=300, bbox_inches='tight')
        plt.close()  # 确保关闭图像
    
    # 保存因子表现摘要
    summary = {}
    for name, result in results.items():
        if isinstance(result, dict) and 'sharpe_ratio' in result:
            summary[name] = {
                'sharpe_ratio': result['sharpe_ratio'],
                'mean_ic': result['mean_ic'],
                'ic_ir': result['ic_ir']
            }
    
    summary_df = pd.DataFrame(summary).T
    summary_df.to_csv(f"{output_dir}/factor_summary.csv")
    
    # 绘制多空收益率曲线并立即保存关闭
    plt.figure(figsize=(12, 6))
    for name, result in results.items():
        if isinstance(result, dict) and 'returns' in result:
            (result['returns'] + 1).cumprod().plot(label=f"{name} (Sharpe: {result['sharpe_ratio']:.2f})")
    
    plt.title('Cumulative Long-Short Returns')
    plt.xlabel('Date')
    plt.ylabel('Cumulative Return')
    plt.legend()
    plt.grid(True)
    plt.savefig(f"{output_dir}/long_short_returns.png", dpi=300, bbox_inches='tight')
    plt.close()  # 确保关闭图像