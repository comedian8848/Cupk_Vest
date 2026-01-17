# 🛢️ BlackOil 股票分析系统 (Cupk_Vest)

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-16+-green.svg)](https://nodejs.org/)
[![React](https://img.shields.io/badge/React-19-61dafb.svg)](https://react.dev/)
[![AI](https://img.shields.io/badge/AI-Claude%2FAnthropic-purple.svg)](https://www.anthropic.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> 🚀 专业级 A股/期货 深度分析系统，融合传统量化模型与大模型 AI 解读，提供全方位的投资决策支持。

**核心特性**：
- ✅ **AI 深度解读**：基于 LLM (Claude/MiniMax) 生成投资建议、风险提示与价格预测
- ✅ **行业对标**：一键生成同行业核心指标（ROE、PE、毛利等）对比雷达图与表格
- ✅ **导出对比**：行业对比支持 CSV/JSON 导出
- ✅ **专业图表**：20+ 种专业分析图表自动生成（增量分析、杜邦分析、现金流结构等）
- ✅ **量化估值**：集成 DCF (现金流折现)、DDM (股利折现) 与相对估值模型
- ✅ **跨平台**：完美支持 macOS / Windows / Linux，Bloomberg 风格暗色专业界面

## 📋 目录

- [快速开始](#快速开始)
- [AI 功能配置](#ai-功能配置)
- [前端设置入口](#前端设置入口)
- [系统架构](#系统架构)
- [功能特性](#功能特性)
- [环境要求](#环境要求)
- [启动方法](#启动方法)
- [常见问题](#常见问题)
- [项目结构](#项目结构)

---

## 🚀 快速开始

**30 秒启动**：

```bash
# 1. 克隆或进入项目目录
cd Cupk_Vest

# 2. 安装 Python 依赖 (确保已激活虚拟环境)
cd stock_analysis
pip install -r requirements.txt
cd ..

# 3. 安装前端依赖
cd web_dashboard
npm install
cd ..

# 4. 运行环境诊断
python diagnose.py

# 5. 一键启动服务
python start_dashboard.py

# 6. 浏览器访问
# http://localhost:5173
```

**使用流程**：
1. 点击「新建分析」，输入股票代码（如 `600519`）。
2. 分析完成后，查看「核心摘要」Dashboard。
3. 通过首页「设置」配置 AI（或使用环境变量）。
4. 切换至 **「AI 分析」** 标签，点击生成深度研报。
5. 切换至 **「交互分析」** 标签，查看同行业对比数据。

---

## 🤖 AI 功能配置

本系统支持兼容 Anthropic API 格式的多种大模型服务（如 MiniMax, DeepSeek, 智谱GLM 等）。

### 1. 设置环境变量（服务端）
在项目根目录或 `stock_analysis` 目录下创建 `.env` 文件（或直接设置系统环境变量）：

```bash
# AI API 配置（必需）
# 示例：使用 MiniMax (兼容 Anthropic 协议)
ANTHROPIC_API_KEY=your-api-key-here
# 或使用 ANTHROPIC_AUTH_TOKEN 形式
# ANTHROPIC_AUTH_TOKEN=your-auth-token
ANTHROPIC_BASE_URL=https://api.minimaxi.com/anthropic
ANTHROPIC_MODEL=MiniMax-M2.1

# 可选：超时与重试
# API_TIMEOUT_MS=60000
# AI_RETRY_COUNT=2
# AI_RETRY_BACKOFF=0.8

# 可选：代理配置
# HTTP_PROXY=http://127.0.0.1:7890
# HTTPS_PROXY=http://127.0.0.1:7890

# 前端 API（可选）
# VITE_API_BASE=http://localhost:5001/api
```

### 2. 验证配置
运行诊断脚本检查 AI 连接：
```bash
python stock_analysis/diagnose_ai.py
```

---

## ⚙️ 前端设置入口

首页右上角新增「设置」入口，可在 UI 中手动配置 AI（不会写入服务器，仅保存到浏览器本地存储并随请求发送）：
- API Key / Auth Token
- Base URL
- Model
- Timeout
- Proxy

适用于本地测试或多模型切换场景。

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Dashboard (React)                     │
│           [Recharts 图表]  [AI 报告组件]  [行业对比]           │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP API (RESTful)
┌─────────────────────▼───────────────────────────────────────┐
│                  Flask Backend Server                        │
│         [任务调度]  [数据缓存]  [AI Client]                  │
└──────────┬───────────────────────────────┬──────────────────┘
           │ subprocess                    │ HTTP Request
┌──────────▼────────────────────┐    ┌─────▼──────────────────┐
│  stock_analysis_v2.py 引擎     │    │   LLM API Service      │
│ (AkShare + Backtrader + MPL)  │    │ (Claude/MiniMax/etc.)  │
└───────────────────────────────┘    └────────────────────────┘
```

---

## 功能特性

### 🧠 AI 智能分析 (New)
- **投资建议**：明确的 买入/持有/卖出 评级、目标价与止损价。
- **核心逻辑**：自动提炼财报亮点（如营收突破、毛利提升）与潜在风险。
- **走势预测**：基于数据的价格区间预测（乐观/中性/悲观）。

### ⚔️ 行业对比交互 (New)
- **多维雷达图**：从成长、盈利、安全、估值等维度对比个股与行业均值。
- **差异分析表**：直观展示核心指标（ROE、净利率等）的优劣势（优于/弱于行业）。

### 📈 传统深度分析
- **核心概览**：Dashboard、增量分析、杜邦分析。
- **趋势分析**：营收利润滚动、现金流滚动、市值营收滚动。
- **估值建模**：PE/PB 通道、DCF 绝对估值、DDM 股息折现。
- **财务健康**：EVA 经济增加值、现金流结构、营运资本分析。
- **技术分析**：MA/MACD/RSI 指标、历史回测。

---

## 环境要求

| 组件 | 最低版本 | 推荐版本 | 说明 |
|------|----------|----------|------|
| Python | 3.9+ | 3.11+ | 核心分析环境 |
| Node.js | 16+ | 18+ | 前端运行环境 |
| npm | 8+ | 9+ | 包管理工具 |

---

## 启动方法细节

### macOS / Linux
推荐使用 `venv` 或 `conda` 管理环境：

```bash
# 1. 准备 Python 环境
cd stock_analysis
pip install -r requirements.txt

# 2. 准备前端
cd ../web_dashboard
npm install

# 3. 启动
cd ..
python3 start_dashboard.py
```

### Windows
建议使用 **Anaconda Prompt** 或 **PowerShell**：

```powershell
# 1. 安装依赖
cd stock_analysis
pip install -r requirements.txt

# 2. 启动
cd ..
python start_dashboard.py
```
> 注意：Windows 用户如果遇到中文乱码，系统会自动尝试修复，无需额外操作。

---

## 常见问题

### 1. 页面显示 "Network Error" 或白屏？
- 确保后端服务已启动（终端显示 `🚀 BlackOil Report Server`）。
- 检查 `stock_analysis/requirements.txt` 依赖是否全部安装。
- 若使用了 `.env` 中的 `VITE_API_BASE`，修改后需重启前端。
- 尝试运行 `python stock_analysis/server.py` 单独启动后端查看报错。

### 2. AI 分析提示错误？
- 检查 `ANTHROPIC_API_KEY` 或 `ANTHROPIC_AUTH_TOKEN` 是否正确设置。
- 使用首页「设置」入口确认前端配置。
- 运行 `python stock_analysis/diagnose_ai.py` 诊断连接。
- 确认是否需要配置代理（国内网络环境）。

### 3. 图表中文乱码？
- 系统会自动检测操作系统并使用合适字体（macOS: Arial Unicode MS, Windows: SimHei）。
- 如仍有乱码，请检查系统是否安装了对应字体库。

---

## 项目结构

```
Cupk_Vest/
├── start_dashboard.py          # 🚀 一键启动脚本
├── diagnose.py                 # 🔧 环境诊断工具
├── README.md                   # 📖 本文档
│
├── stock_analysis/             # 📊 后端核心
│   ├── server.py               # API 服务器 (含 AI 路由)
│   ├── ai_client.py            # AI 客户端封装
│   ├── ai_analyzer.py          # AI 分析逻辑
│   ├── industry_compare.py     # 行业数据获取
│   ├── stock_analysis_v2.py    # 量化分析引擎
│   └── requirements.txt        # Python 依赖
│
└── web_dashboard/              # ⚛️ 前端应用
    ├── src/
    │   ├── components/
    │   │   ├── AIReport/       # 🤖 AI 报告组件
    │   │   ├── IndustryComparison/ # ⚔️ 行业对比组件
    │   │   └── ...
    │   ├── api.js               # 前端 API 统一封装
    │   ├── App.jsx             # 主逻辑
    │   └── ...
    └── package.json            # 前端依赖
```

---

## 📜 License

MIT License