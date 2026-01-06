# Akshare Backtrader 策略

本项目使用 [Backtrader](https://www.backtrader.com/) 框架实现量化交易策略，并利用 [Akshare](https://github.com/akfamily/akshare) 获取中国 A 股市场的历史数据。

## 概览

本仓库包含基于平安银行（000001）日线数据的移动平均线交叉策略示例。

## 环境要求

确保已安装以下 Python 库：

```bash
pip install akshare pandas backtrader matplotlib
```

## 文件说明

- **Double Moving Average.py**:
  - 实现双移动平均线交叉策略。
  - 当快线（5日）上穿慢线（10日）时买入。
  - 当快线下穿慢线时卖出。

- **Single Moving Average.py**:
  - 实现单移动平均线策略。
  - 当收盘价上穿 30 日均线（SMA）时买入。
  - 当收盘价下穿 30 日均线时卖出。

- **Three moving averages.py**:
  - 当前包含一个单移动平均线策略（与上述类似）。
  - *注意：文件名暗示未来将实现三移动平均线策略。*

## 使用方法

直接使用 Python 运行任意策略脚本：

```bash
python "Double Moving Average.py"
```

每个脚本将执行以下操作：
1. 获取股票 `000001`（平安银行）从 2025年1月1日 到 2026年1月5日 的历史数据。
2. 清洗并格式化数据以适配 Backtrader。
3. 以 100,000 的初始资金运行回测。
4. 打印最终投资组合价值、夏普比率（Sharpe Ratio）和收益率（Return）。
5. 显示回测结果的图表。

## Vest 股票与期货分析工具

`vest` 目录下包含一套完整的 A 股上市公司分析与财报解读工具（v2.0），同时也支持期货分析。

**主要功能：**

1.  **全方位公司分析**：覆盖基本面、核心竞争力、财务风险及估值水平。
2.  **财报深度解读**：自动分析业绩表现、现金流健康度、资产负债结构及风险预警。
3.  **量化回测**：内置基于 Backtrader 的简单均线交叉策略回测功能。
4.  **期货分析**：支持期货主连行情获取、趋势分析及可视化。
5.  **数据可视化**：生成包括趋势图、杜邦分析、综合评分仪表盘在内的丰富图表。

**核心文件：**

- `stock_analysis_v2.py`: 主程序入口，支持股票和期货分析，集成数据获取、分析与报告生成。
- `data_fetcher.py`: 负责从 Akshare 并行获取各类金融数据。
- `analysis.py`: 包含财务指标计算与技术分析算法的核心逻辑。

**使用方式：**

进入 `vest` 目录：

```bash
cd vest
```

运行分析工具（支持股票代码或期货代码）：

```bash
# 股票分析 (如：平安银行)
python stock_analysis_v2.py 000001

# 期货分析 (如：黄金主连)
python stock_analysis_v2.py AU0
# 或
python stock_analysis_v2.py 黄金
```

如果不带参数运行，程序将提示输入代码。
