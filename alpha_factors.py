import numpy as np
import pandas as pd
from typing import Dict

class AlphaFactors:
    """
    Alpha因子计算类
    包含多个基于价格和成交量的因子计算方法
    """
    
    def __init__(self):
        """初始化AlphaFactors类"""
        pass
    
    @staticmethod
    def price_reversal(prices: pd.DataFrame, window: int = 5) -> pd.DataFrame:
        """
        价格反转因子
        基于短期价格反转现象，当价格短期内大幅上涨/下跌后，可能会出现反向调整
        
        参数:
            prices: 包含收盘价的DataFrame，索引为日期，列为股票代码
            window: 计算窗口大小，默认为5天
            
        返回:
            因子值DataFrame，索引为日期，列为股票代码
        """
        # 计算过去window天的收益率
        returns = prices.pct_change(window)
        
        # 反转因子就是收益率的负值
        alpha = -returns
        
        return alpha
    
    @staticmethod
    def volume_price_ratio(prices: pd.DataFrame, volumes: pd.DataFrame, 
                          window: int = 10) -> pd.DataFrame:
        """
        成交量价格比率因子
        计算成交量相对于价格变化的比率，识别价格变动是否有足够的成交量支撑
        
        参数:
            prices: 包含收盘价的DataFrame，索引为日期，列为股票代码
            volumes: 包含成交量的DataFrame，索引为日期，列为股票代码
            window: 计算窗口大小，默认为10天
            
        返回:
            因子值DataFrame，索引为日期，列为股票代码
        """
        # 计算价格变化率
        price_change = prices.pct_change(1).abs()
        
        # 计算成交量变化率
        volume_change = volumes.pct_change(1).abs()
        
        # 计算比率
        ratio = volume_change / (price_change + 1e-8)  # 添加小值避免除零
        
        # 使用移动平均平滑结果
        alpha = ratio.rolling(window=window).mean()
        
        return alpha
    
    @staticmethod
    def volatility_breakout(high_prices: pd.DataFrame, low_prices: pd.DataFrame, 
                           close_prices: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """
        波动率突破因子
        基于价格突破历史波动区间的信号
        
        参数:
            high_prices: 包含最高价的DataFrame，索引为日期，列为股票代码
            low_prices: 包含最低价的DataFrame，索引为日期，列为股票代码
            close_prices: 包含收盘价的DataFrame，索引为日期，列为股票代码
            window: 计算波动率的窗口大小，默认为20天
            
        返回:
            因子值DataFrame，索引为日期，列为股票代码
        """
        # 计算历史波动率
        volatility = close_prices.rolling(window=window).std()
        
        # 计算上轨和下轨
        upper_band = close_prices.shift(1) + 2 * volatility
        lower_band = close_prices.shift(1) - 2 * volatility
        
        # 计算突破信号
        # 如果最高价突破上轨，信号为1；如果最低价突破下轨，信号为-1；否则为0
        breakout_up = (high_prices > upper_band).astype(int)
        breakout_down = (low_prices < lower_band).astype(int) * (-1)
        
        # 合并信号
        alpha = breakout_up + breakout_down
        
        return alpha
    
    @staticmethod
    def calculate_all_factors(ohlcv_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        计算所有因子
        
        参数:
            ohlcv_data: 包含OHLCV数据的字典，键为'open', 'high', 'low', 'close', 'volume'
            
        返回:
            包含所有因子值的字典，键为因子名称
        """
        factors = {}
        
        # 计算价格反转因子
        factors['price_reversal'] = AlphaFactors.price_reversal(ohlcv_data['close'])
        
        # 计算成交量价格比率因子
        factors['volume_price_ratio'] = AlphaFactors.volume_price_ratio(
            ohlcv_data['close'], ohlcv_data['volume']
        )
        
        # 计算波动率突破因子
        factors['volatility_breakout'] = AlphaFactors.volatility_breakout(
            ohlcv_data['high'], ohlcv_data['low'], ohlcv_data['close']
        )
        
        return factors