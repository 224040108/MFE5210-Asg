from utils import load_sample_data, save_results
from backtest import AlphaBacktest
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings("ignore")

# 设置matplotlib的中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体
plt.rcParams['axes.unicode_minus'] = False  # 显示负号

print("开始获取A股数据...")

# 加载数据
data = load_sample_data()

# 打印数据基本信息
print("\n数据概览:")
for key, df in data.items():
    if not df.empty:
        print(f"{key} 数据形状: {df.shape}")
        print(f"股票代码: {df.columns.tolist()}")
        print(f"日期范围: {df.index.min()} 至 {df.index.max()}")
        print("-" * 50)

# 初始化回测
backtest = AlphaBacktest(data)

# 计算因子
backtest.calculate_factors()

# 设置统一的分组数量
quantiles = 3

# 评估因子 - 使用3个分组
results = backtest.evaluate_all_factors(quantiles=quantiles)

# 保存结果
save_results(results)

# 绘制因子收益率 - 只绘制有效结果的因子
valid_factors = []
plt.close('all')  # 关闭所有现有图像
for name in backtest.factors.keys():
    if name in results and isinstance(results[name], dict) and 'returns' in results[name]:
        if not results[name]['returns'].empty and not results[name]['returns'].isna().all():
            valid_factors.append(name)
            backtest.plot_factor_returns(name, quantiles=quantiles)

print(f"绘制了 {len(valid_factors)} 个有效因子的收益率图")

# 绘制因子相关性
if len(valid_factors) > 1:  # 只有当有多个有效因子时才绘制相关性
    backtest.plot_factor_correlation()

print("A股因子分析完成!")