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
# Matplotlib 全局字体设置
# 'Arial Unicode MS' (macOS), 'SimHei' (Windows), 'WenQuanYi Micro Hei' (Linux)
FONT_FAMILY = 'Arial Unicode MS' 

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

# 数据源配置开关
DATA_SOURCE_CONFIG = {
    'USE_TONGHUASHUN': False,  # 是否启用同花顺（问财）数据源（需要 pywencai + Node.js）
    'USE_AKSHARE_ONLY': True,  # 仅使用 akshare（默认推荐）
}
