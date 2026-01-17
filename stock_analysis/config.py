# -*- coding: utf-8 -*-
"""
配置文件：用于存放模型假设、常量和样式配置
"""

# ==================== 模型假设 ====================

# DCF (Discounted Cash Flow) 估值模型参数
DCF_CONFIG = {
    'DISCOUNT_RATE': 0.10,       # 折现率 (WACC)
    'TERMINAL_GROWTH': 0.03,   # 永续增长率
    'FORECAST_YEARS': 10,        # 预测年限
    'FCF_RATIO_OF_OCF': 0.7    # 自由现金流占经营现金流的比例 (保守估计)
}

# DDM (Dividend Discount Model) 股利折现模型参数
DDM_CONFIG = {
    'REQUIRED_RETURN': 0.10,     # 要求回报率
    'TERMINAL_GROWTH': 0.03,   # 永续增长率 (g)
    'G_LIMIT': 0.08,             # 增长率g的上限，防止g > r
}

# EVA (Economic Value Added) 经济增加值模型参数
EVA_CONFIG = {
    'WACC': 0.08  # 加权平均资本成本 (WACC)
}

# ==================== 行业对标 ====================
# 在行业对标分析图中使用，可自行修改
COMPETITOR_CODES = ['601008', '601880', '603967']

# ==================== 样式与颜色 ====================
# Matplotlib 全局字体设置 - 跨平台自适应
# 'Arial Unicode MS' (macOS), 'SimHei' (Windows), 'WenQuanYi Micro Hei' (Linux)
import platform
import matplotlib.font_manager as fm

# 根据操作系统选择合适的字体
_system = platform.system()
if _system == 'Darwin':  # macOS
    FONT_FAMILY = 'Arial Unicode MS'
elif _system == 'Windows':
    FONT_FAMILY = 'SimHei'
else:  # Linux
    FONT_FAMILY = 'WenQuanYi Micro Hei'

# 如果首选字体不可用，尝试备选字体
_fonts = [FONT_FAMILY, 'SimHei', 'Arial Unicode MS', 'WenQuanYi Micro Hei', 'DejaVu Sans']
_available_fonts = {f.name for f in fm.fontManager.ttflist}
for font in _fonts:
    if font in _available_fonts:
        FONT_FAMILY = font
        break
else:
    # 如果都不可用，使用系统默认
    FONT_FAMILY = 'sans-serif' 

# 颜色主题
COLORS = {
    'primary': '#2E86AB',      # 主色-蓝
    'secondary': '#A23B72',    # 次色-紫红
    'success': '#28A745',      # 成功-绿
    'warning': '#FFC107',      # 警告-黄
    'danger': '#DC3545',       # 危险-红
    'info': '#17A2B8',         # 信息-青
    'light': '#F8F9FA',
    'dark': '#343A40',
    'revenue': '#4C72B0',      # 营收-蓝
    'profit': '#DD8452',       # 利润-橙
    'cash': '#55A868',         # 现金-绿
}

# ==================== API & 数据源 ====================
# 并行获取数据时的最大线程数
MAX_WORKERS = 8

# 获取K线数据时的年限
KLINE_YEARS = 10

# ==================== AI 分析配置 ====================
import os

# AI API 配置
AI_CONFIG = {
    'API_KEY': os.getenv('ANTHROPIC_API_KEY', ''),
    'BASE_URL': os.getenv('ANTHROPIC_BASE_URL', 'https://api.minimaxi.com/anthropic'),
    'MODEL': os.getenv('ANTHROPIC_MODEL', 'MiniMax-M2.1'),
    'TIMEOUT': int(os.getenv('API_TIMEOUT_MS', '60000')),
    'PROXY': {
        'http': os.getenv('HTTP_PROXY'),
        'https': os.getenv('HTTPS_PROXY')
    } if os.getenv('HTTP_PROXY') else None
}
