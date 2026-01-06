<div align="center">

# 📈 A股/期货全方位分析与回测框架

**基于 Python 的综合金融分析工具**  
覆盖数据获取 → 基本面分析 → 财报解读 → 量化回测 → 自动报告生成

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![akshare](https://img.shields.io/badge/Data-akshare-green.svg)
![backtrader](https://img.shields.io/badge/Backtest-backtrader-orange.svg)

</div>

---

## 🗂️ 项目结构

```
├── stock_analysis/                  # 核心分析模块
│   ├── stock_analysis_v2.py         # 主程序入口（股票 + 期货分析）
│   ├── data_fetcher.py              # 多线程数据抓取与清洗
│   ├── analysis.py                  # 财务/技术指标计算库
│   ├── config.py                    # 模型参数与样式配置
│   └── requirements.txt             # Python 依赖
│
└── akshare+backtrader回测框架/       # 独立回测策略示例
    ├── Single Moving Average.py     # 单均线策略
    ├── Double Moving Average.py     # 双均线金叉/死叉策略
    └── Three moving averages.py     # 三均线交互策略（支持参数输入）
```

---

## ✨ 功能亮点

### 股票分析四大模块

| 模块 | 核心功能 | 关键问题 |
|------|----------|----------|
| **🚀 增量分析** | 单季度拆分、TTM 序列、同比/环比趋势 | 业绩增量是否有预期？ |
| **🏢 公司分析** | 成长性、竞争力、财务安全、分红能力、估值 | 公司质地如何？ |
| **📑 财报解读** | 业绩表现、现金流健康度、资产负债结构 | 财报有何风险信号？ |
| **🤖 量化回测** | 双均线交叉策略、夏普比率、最大回撤 | 策略历史表现如何？ |

### 期货分析

- 支持主连品种趋势分析（黄金、白银、原油、螺纹钢等 20+ 品种）
- 自动计算 MA20/MA60/MA120 均线并标注高低点
- 输出趋势图与 Markdown 报告

### 技术指标

- **趋势类**：SMA、均线斜率
- **动量类**：RSI、MACD、KDJ
- **估值类**：PE(TTM)、PB、PS 历史分位点

---

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装核心依赖
pip install -r stock_analysis/requirements.txt

# 安装回测框架（可选，用于量化回测功能）
pip install backtrader
```

### 2. 运行分析

```bash
cd stock_analysis

# 股票分析（输入 6 位代码）
python stock_analysis_v2.py 002683    # 宏大爆破
python stock_analysis_v2.py 600519    # 贵州茅台

# 期货分析（支持中文名称自动映射）
python stock_analysis_v2.py 黄金
python stock_analysis_v2.py 螺纹

# 交互模式（不带参数）
python stock_analysis_v2.py
```

### 3. 独立回测示例

```bash
cd akshare+backtrader回测框架

# 双均线策略（快速验证）
python "Double Moving Average.py"

# 三均线策略（支持自定义参数）
python "Three moving averages.py"
```

---

## 🔗 工作流程

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  数据获取   │ -> │  数据处理   │ -> │  分析引擎   │ -> │  报告输出   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                  │                  │                  │
  data_fetcher       analysis.py      stock_analysis_v2      输出目录
  • 财务三表        • 单季度拆分       • 增量分析           • *.png 图表
  • K线/分红        • TTM 计算         • 公司分析           • report.md
  • 北向资金        • 技术指标         • 财报解读
  • 股东结构                           • 量化回测
```

---

## ⚙️ 配置说明

编辑 `stock_analysis/config.py` 可自定义：

```python
# 估值模型参数
DCF_CONFIG = {
    'DISCOUNT_RATE': 0.10,      # 折现率 (WACC)
    'TERMINAL_GROWTH': 0.03,    # 永续增长率
}

DDM_CONFIG = {
    'REQUIRED_RETURN': 0.10,    # 要求回报率
}

EVA_CONFIG = {
    'WACC': 0.08                # 加权平均资本成本
}

# 数据获取
MAX_WORKERS = 8                 # 并发线程数
KLINE_YEARS = 10                # K线数据年限

# 可视化
FONT_FAMILY = 'Arial Unicode MS'  # macOS 字体（Windows 改为 SimHei）
```

---

## 📝 输出示例

运行后在当前目录生成：

```
分析报告_002683_20260106_1430/
├── revenue_profit_trend.png      # 营收利润趋势
├── growth_momentum.png           # 增量信号仪表盘
├── cash_flow_structure.png       # 现金流结构
├── valuation_history.png         # 估值历史分位
├── backtest_result.png           # 回测收益曲线
└── report.md                     # 综合分析报告
```

---

## ⚠️ 注意事项

| 问题 | 解决方案 |
|------|----------|
| akshare 接口超时 | 降低 `MAX_WORKERS` 或重试 |
| 回测功能不可用 | 执行 `pip install backtrader` |
| 中文乱码 | 修改 `config.py` 中 `FONT_FAMILY` |
| 数据缺失 | 检查股票代码是否正确、是否已退市 |

---

## 📚 依赖说明

| 库 | 用途 |
|----|------|
| akshare | A股/期货数据源 |
| pandas / numpy | 数据处理 |
| matplotlib / seaborn | 可视化 |
| backtrader | 量化回测框架 |

---

## 📄 License

MIT License
