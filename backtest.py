import numpy as np
import pandas as pd
from typing import Dict
import matplotlib.pyplot as plt
import seaborn as sns
import os  # 添加这一行
from alpha_factors import AlphaFactors

class AlphaBacktest:
    """
    Alpha因子回测框架
    用于评估Alpha因子的有效性
    """
    
    def __init__(self, ohlcv_data: Dict[str, pd.DataFrame]):
        """
        初始化回测框架
        
        参数:
            ohlcv_data: 包含OHLCV数据的字典，键为'open', 'high', 'low', 'close', 'volume'
        """
        self.ohlcv_data = ohlcv_data
        self.factors = {}
        self.returns = ohlcv_data['close'].pct_change(1).shift(-1)  # 使用下一期收益率
    
    def calculate_factors(self) -> None:
        """计算所有Alpha因子"""
        # 过滤数据，去除缺失值过多的日期
        valid_dates = []
        for date in self.ohlcv_data['close'].index:
            # 如果该日期至少有80%的股票有数据，则保留
            non_na_count = self.ohlcv_data['close'].loc[date].notna().sum()
            if non_na_count >= 0.8 * len(self.ohlcv_data['close'].columns):
                valid_dates.append(date)
        
        # 只保留有效日期的数据
        filtered_data = {}
        for key, df in self.ohlcv_data.items():
            filtered_data[key] = df.loc[valid_dates]
        
        # 使用过滤后的数据计算因子
        self.factors = AlphaFactors.calculate_all_factors(filtered_data)
    
    def calculate_factor_returns(self, factor_name: str, quantiles: int = 3) -> pd.DataFrame:
        """
        计算因子分组收益率
        
        参数:
            factor_name: 因子名称
            quantiles: 分组数量，默认为3
            
        返回:
            分组收益率DataFrame
        """
        if not self.factors:
            self.calculate_factors()
            
        factor = self.factors[factor_name]
        
        # 对每个时间点的因子值进行分组
        quantile_labels = [f'Q{i+1}' for i in range(quantiles)]
        
        # 初始化一个空的DataFrame来存储分组结果
        factor_quantiles = pd.DataFrame(index=factor.index, columns=factor.columns)
        
        # 对每一行（每个时间点）单独进行分组处理
        for dt in factor.index:
            row = factor.loc[dt]
            # 检查是否有足够的不同值进行分组
            unique_valid_values = row.dropna().unique()
            
            if len(unique_valid_values) >= quantiles:
                # 有足够的不同值，可以正常分组
                try:
                    factor_quantiles.loc[dt] = pd.qcut(
                        row.rank(method='first'), 
                        q=quantiles, 
                        labels=quantile_labels,
                        duplicates='drop'  # 处理可能的重复边界
                    )
                except Exception as e:
                    # 如果仍然出错，则跳过这一行
                    print(f"分组错误 {dt}: {e}")
                    continue
            else:
                # 没有足够的不同值，跳过这一行
                print(f"日期 {dt} 的不同因子值不足 {quantiles} 个，跳过分组")
                continue
        
        # 计算每个分组的平均收益率
        group_returns = {}
        for q in quantile_labels:
            mask = factor_quantiles == q
            group_returns[q] = (self.returns * mask).mean(axis=1)
            
        return pd.DataFrame(group_returns)
    
    def calculate_long_short_returns(self, factor_name: str, quantiles: int = 3) -> pd.Series:
        """
        计算多空组合收益率
        
        参数:
            factor_name: 因子名称
            quantiles: 分组数量，默认为3
            
        返回:
            多空组合收益率Series
        """
        group_returns = self.calculate_factor_returns(factor_name, quantiles)
        
        # 检查是否有足够的分组
        if f'Q{quantiles}' in group_returns.columns and 'Q1' in group_returns.columns:
            long_short_returns = group_returns[f'Q{quantiles}'] - group_returns['Q1']
            return long_short_returns
        else:
            # 如果没有足够的分组，返回一个空的Series
            print(f"警告: 因子 {factor_name} 没有足够的分组进行多空组合计算")
            return pd.Series(index=self.returns.index)
    
    def calculate_factor_ic(self, factor_name: str) -> pd.Series:
        """
        计算因子IC值（Information Coefficient）
        
        参数:
            factor_name: 因子名称
            
        返回:
            因子IC值Series
        """
        if not self.factors:
            self.calculate_factors()
            
        factor = self.factors[factor_name]
        
        # 计算每个时间点的秩相关系数
        ic_series = pd.Series(index=factor.index)
        for dt in factor.index:
            if dt in self.returns.index:
                f = factor.loc[dt]
                r = self.returns.loc[dt]
                # 去除缺失值
                valid = ~(f.isna() | r.isna())
                if valid.sum() > 0:
                    ic_series[dt] = f[valid].corr(r[valid], method='spearman')
                    
        return ic_series
    
    def calculate_sharpe_ratio(self, returns: pd.Series, annualization: int = 252) -> float:
        """
        计算夏普比率
        
        参数:
            returns: 收益率Series
            annualization: 年化因子，默认为252（交易日）
            
        返回:
            夏普比率
        """
        mean_return = returns.mean() * annualization
        std_return = returns.std() * np.sqrt(annualization)
        return mean_return / std_return if std_return != 0 else 0
    
    def calculate_factor_correlation(self) -> pd.DataFrame:
        """
        计算因子间相关性
        
        返回:
            因子相关性矩阵
        """
        if not self.factors:
            self.calculate_factors()
            
        # 将所有因子值合并为一个DataFrame
        factor_values = {}
        for name, factor in self.factors.items():
            # 将每个因子展平为一列
            stacked = factor.stack().reset_index()
            # 确保列名正确
            stacked.columns = ['date', 'ticker', 'value']
            stacked['factor'] = name
            factor_values[name] = stacked
            
        # 合并所有因子
        all_factors = pd.concat(factor_values.values())
        
        # 透视表以获得宽格式数据
        pivot_factors = all_factors.pivot_table(
            index=['date', 'ticker'],  # 使用实际的列名而不是level_0, level_1
            columns='factor',
            values='value'
        )
        
        # 计算相关性矩阵
        correlation_matrix = pivot_factors.corr()
        
        # 确保相关性矩阵是一个简单的DataFrame，没有多级索引
        if isinstance(correlation_matrix.index, pd.MultiIndex):
            correlation_matrix = correlation_matrix.reset_index(level=0, drop=True)
        
        return correlation_matrix
    
    def evaluate_all_factors(self, quantiles: int = 3) -> Dict:
        """
        评估所有因子的表现
        
        参数:
            quantiles: 分组数量，默认为3
            
        返回:
            包含评估结果的字典
        """
        if not self.factors:
            self.calculate_factors()
            
        results = {}
        
        # 计算每个因子的多空收益率和夏普比率
        for name in self.factors.keys():
            long_short_returns = self.calculate_long_short_returns(name, quantiles)
            
            # 检查收益率是否为空
            if long_short_returns.empty or long_short_returns.isna().all():
                print(f"警告: 因子 {name} 的多空收益率为空，跳过评估")
                continue
                
            sharpe = self.calculate_sharpe_ratio(long_short_returns)
            ic_series = self.calculate_factor_ic(name)
            
            results[name] = {
                'sharpe_ratio': sharpe,
                'mean_ic': ic_series.mean(),
                'ic_ir': ic_series.mean() / ic_series.std() if ic_series.std() != 0 else 0,
                'returns': long_short_returns
            }
            
        # 计算因子相关性
        correlation_matrix = self.calculate_factor_correlation()
        results['correlation_matrix'] = correlation_matrix
        
        # 计算平均夏普比率
        sharpe_ratios = [r['sharpe_ratio'] for r in results.values() if isinstance(r, dict)]
        results['average_sharpe'] = np.mean(sharpe_ratios) if sharpe_ratios else 0
        
        return results
    
    def plot_factor_returns(self, factor_name: str, quantiles: int = 3) -> None:
        """
        绘制因子分组收益率
        
        参数:
            factor_name: 因子名称
            quantiles: 分组数量，默认为3
        """
        group_returns = self.calculate_factor_returns(factor_name, quantiles)
        
        # 检查是否有有效数据
        if group_returns.empty:
            print(f"警告: 因子 {factor_name} 没有有效的分组收益率，跳过绘图")
            return
        
        # 关闭之前的所有图像，避免空白图像
        plt.close('all')
        
        # 只有在有有效数据时才创建图像
        fig, ax = plt.subplots(figsize=(12, 6))
        (group_returns + 1).cumprod().plot(ax=ax)
        ax.set_title(f'{factor_name} Factor Quantile Returns')
        ax.set_xlabel('Date')
        ax.set_ylabel('Cumulative Return')
        ax.legend()
        ax.grid(True)
        plt.tight_layout()
        
        # 保存图像到results目录
        os.makedirs('results', exist_ok=True)
        plt.savefig(f"results/{factor_name}_returns.png", dpi=300, bbox_inches='tight')
        
        # 显示图像
        plt.show()
    
    def plot_factor_correlation(self) -> None:
        """绘制因子相关性热图"""
        if not self.factors:
            self.calculate_factors()
            
        correlation_matrix = self.calculate_factor_correlation()
        
        # 获取因子名称列表
        factor_names = list(correlation_matrix.columns)
        
        # 将相关性矩阵转换为NumPy数组
        corr_values = correlation_matrix.values
        
        # 创建一个图形和一个轴对象
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # 使用轴对象绘制热图
        im = ax.imshow(corr_values, cmap='coolwarm', vmin=-1, vmax=1)
        
        # 添加颜色条
        fig.colorbar(im, ax=ax)
        
        # 设置坐标轴标签
        ax.set_xticks(np.arange(len(factor_names)))
        ax.set_yticks(np.arange(len(factor_names)))
        ax.set_xticklabels(factor_names, rotation=45)
        ax.set_yticklabels(factor_names)
        
        # 在每个单元格中添加文本，根据值的类型设置不同的格式
        for i in range(len(factor_names)):
            for j in range(len(factor_names)):
                value = corr_values[i, j]
                # 如果值接近整数（差值小于1e-10），则保留1位小数，否则保留4位小数
                if abs(value - round(value)) < 1e-10:
                    text_value = f'{value:.1f}'
                else:
                    text_value = f'{value:.4f}'
                
                ax.text(j, i, text_value,
                               ha="center", va="center", color="black")
        
        ax.set_title('Factor Correlation Matrix')
        plt.tight_layout()
        
        # 保存图像到results目录
        os.makedirs('results', exist_ok=True)
        plt.savefig(f"results/correlation_matrix_interactive.png", dpi=300, bbox_inches='tight')
        
        # 显示图像但不立即关闭
        plt.show()