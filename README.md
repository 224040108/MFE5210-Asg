# Alpha因子开发项目

本项目开发并回测了三个量化投资Alpha因子，用于捕捉市场中的异常收益机会。通过对A股市场数据的分析，评估了不同因子的有效性和相关性。

## 项目结构

- alpha_factors.py: 包含三个Alpha因子的实现
- backtest.py: 因子回测框架，用于评估因子表现
- utils.py: 数据加载、处理和结果保存的工具函数
- launch.py: 主程序入口，运行整个回测流程
- data_cache/: 缓存下载的股票数据
- results/: 保存回测结果和图表

## Alpha因子

1. 价格反转因子 (Price Reversal)
  - 类型: 中频、横截面、多空
  - 数据: 价格数据
  - 原理: 基于短期价格反转现象，当股票短期内大幅上涨/下跌后，可能会出现反向调整
  - 参考文献: Jegadeesh, N., & Titman, S. (1993). Returns to buying winners and selling losers: Implications for stock market efficiency. The Journal of Finance, 48(1), 65-91.
  - 计算方法: 过去5天收益率的负值

2. 成交量价格比率因子 (Volume-Price Ratio)
  - 类型: 中频、横截面、多空
  - 数据: 价格和成交量数据
  - 原理: 计算成交量相对于价格变化的比率，识别价格变动是否有足够的成交量支撑
  - 参考文献: Blume, L., Easley, D., & O'Hara, M. (1994). Market statistics and technical analysis: The role of volume. The Journal of Finance, 49(1), 153-181.
  - 计算方法: 成交量变化率除以价格变化率的10天移动平均

3. 波动率突破因子 (Volatility Breakout)
  - 类型: 高频、时间序列、多空
  - 数据: 高低开收价格数据
  - 原理: 基于价格突破历史波动区间的信号，捕捉价格突破后的动量
  - 参考文献: Bollinger, J. (2002). Bollinger on Bollinger Bands. McGraw-Hill.
  - 计算方法: 价格突破上轨(+2σ)为1，突破下轨(-2σ)为-1，否则为0，σ为20天收盘价的标准差

## 因子表现

项目通过以下指标评估因子表现：

- 夏普比率 (Sharpe Ratio): 衡量风险调整后的收益
- 信息系数 (IC): 因子值与未来收益的相关性
- IC IR: 信息比率，衡量IC的稳定性

回测结果保存在 results/ 目录下，包括：

- 因子表现摘要 (factor_summary.csv)
- 因子相关性矩阵 (correlation_matrix.csv 和 correlation_matrix.png)
- 多空组合累积收益图 (long_short_returns.png)
- 各因子分组收益图 ({factor_name}_returns.png)

### 相关性矩阵

下表和图展示了三个因子之间的相关性：

<table class="feishu-table">
<tr class="width-enforcer">
<td style="width:25.00%;"></td>
<td style="width:25.00%;"></td>
<td style="width:25.00%;"></td>
<td style="width:25.00%;"></td>
</tr>
<tr>
<th>
因子
</th>
<th>
价格反转
</th>
<th>
波动率突破
</th>
<th>
成交量价格比率
</th>
</tr>
<tr>
<td>
价格反转
</td>
<td>
1.00
</td>
<td>
-0.1505849973281564
</td>
<td>
-0.007131985371945082
</td>
</tr>
<tr>
<td>
波动率突破
</td>
<td>
-0.1505849973281564
</td>
<td>
1.00
</td>
<td>
0.02426297294614914
</td>
</tr>
<tr>
<td>
成交量价格比率
</td>
<td>
-0.007131985371945082
</td>
<td>
0.02426297294614914
</td>
<td>
1.00
</td>
</tr>
</table>

![text](https://github.com/224040108/MFE5210-Asg/blob/main/results/correlation_matrix_interactive.png)

所有因子之间的最大相关性为0.23，满足相关性不超过0.5的要求。

### 因子表现摘要

<table class="feishu-table">
<tr class="width-enforcer">
<td style="width:25.00%;"></td>
<td style="width:25.00%;"></td>
<td style="width:25.00%;"></td>
<td style="width:25.00%;"></td>
</tr>
<tr>
<th>
因子
</th>
<th>
夏普比率
</th>
<th>
平均IC
</th>
<th>
IC IR
</th>
</tr>
<tr>
<td>
价格反转
</td>
<td>
0.20866491551559097
</td>
<td>
0.010502548146664265
</td>
<td>
0.029628277831200804
</td>
</tr>
<tr>
<td>
成交量价格比率
</td>
<td>
0.22034632992684686
</td>
<td>
0.025466723448890317
</td>
<td>
0.0905660094852853
</td>
</tr>
<tr>
<td>
波动率突破
</td>
<td>
-0.245107712611164
</td>
<td>
0.017652369266955657
</td>
<td>
0.06987605136061265
</td>
</tr>
</table>

## 数据来源

项目使用 akshare 库获取A股市场数据，并支持本地缓存以加快重复运行速度。

## 参考文献

1. Asness, C. S., Moskowitz, T. J., & Pedersen, L. H. (2013). Value and momentum everywhere. The Journal of Finance, 68(3), 929-985.
2. Blume, L., Easley, D., & O'Hara, M. (1994). Market statistics and technical analysis: The role of volume. The Journal of Finance, 49(1), 153-181.
3. Bollinger, J. (2002). Bollinger on Bollinger Bands. McGraw-Hill.
4. Fama, E. F., & French, K. R. (1992). The cross-section of expected stock returns. The Journal of Finance , 47(2), 427-465.
5. Grinblatt, M., & Moskowitz, T. J. (2004). Predicting stock price movements from past returns: The role of consistency and tax-loss selling. Journal of Financial Economics, 71(3), 541-579.
6. Jegadeesh, N., & Titman, S. (1993). Returns to buying winners and selling losers: Implications for stock market efficiency. The Journal of Finance, 48(1), 65-91.
7. Lo, A. W., & MacKinlay, A. C. (1990). When are contrarian profits due to stock market overreaction? The Review of Financial Studies, 3(2), 175-205.





