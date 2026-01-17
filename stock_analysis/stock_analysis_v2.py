#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股公司分析与财报解读工具 v2.0
功能：
1. 公司分析 - 基本面、竞争力、风险、估值
2. 财报解读 - 业绩、现金流、资产结构、风险预警
3. 美观可视化 - 趋势图、杜邦分析、现金流结构、综合评分仪表盘
"""

import sys
import os

# 设置编码和路径 - Windows兼容处理
try:
    if sys.platform.startswith('win'):
        # Windows 编码处理 - 避免UnicodeEncodeError
        if hasattr(sys.stdout, 'buffer'):
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        # 设置编码环境变量
        os.environ['PYTHONIOENCODING'] = 'utf-8'
except Exception as e:
    print(f"Warning: Encoding setup failed: {e}")

# 确保脚本所在目录在 Python 路径中
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# 导入依赖
try:
    print("[DEBUG] Importing akshare...")
    import akshare as ak
    print("[DEBUG] Importing backtrader...")
    import backtrader as bt
    print("[DEBUG] Importing pandas, numpy...")
    import pandas as pd
    import numpy as np
    print("[DEBUG] Importing matplotlib...")
    import matplotlib
    matplotlib.use('Agg')  # 无头模式，避免GUI问题
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import Wedge
    print("[DEBUG] Importing seaborn...")
    import seaborn as sns
    import json
    from datetime import datetime
    import time
    import warnings
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from functools import lru_cache

    print("[DEBUG] Importing local modules...")
    # 导入新的数据获取模块
    import data_fetcher

    # 从配置文件导入常量
    from config import MAX_WORKERS, FONT_FAMILY, COLORS, DCF_CONFIG, DDM_CONFIG, EVA_CONFIG
    print("[DEBUG] All imports successful!")

    warnings.filterwarnings('ignore')
except ImportError as e:
    print(f"ERROR: Missing dependency: {e}", file=sys.stderr)
    print(f"Please run: pip install -r requirements.txt", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"ERROR: Import failed: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 全局线程池（复用，避免频繁创建销毁）
_EXECUTOR = ThreadPoolExecutor(max_workers=MAX_WORKERS)

# ==================== 样式设置 ====================
sns.set_theme(style="whitegrid")
# 使用从配置中导入的字体
plt.rcParams['font.sans-serif'] = [FONT_FAMILY, 'PingFang SC', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150

# 导入本地模块
try:
    import analysis
    import industry_compare  # 行业对比模块 (基于 akshare)
except ImportError as e:
    print(f"ERROR: 缺少本地模块: {e}", file=sys.stderr)
    sys.exit(1)

import platform
from matplotlib import font_manager

# ==================== 期货配置 ====================
FUTURES_MAPPING = {
    # 贵金属
    '黄金': {'symbol': 'AU', 'exchange': 'SHFE', 'sina_name': '黄金'},
    '白银': {'symbol': 'AG', 'exchange': 'SHFE', 'sina_name': '白银'},
    #有色金属
    '铜': {'symbol': 'CU', 'exchange': 'SHFE', 'sina_name': '铜'},
    '铝': {'symbol': 'AL', 'exchange': 'SHFE', 'sina_name': '铝'},
    '锌': {'symbol': 'ZN', 'exchange': 'SHFE', 'sina_name': '锌'},
    '铅': {'symbol': 'PB', 'exchange': 'SHFE', 'sina_name': '铅'},
    '镍': {'symbol': 'NI', 'exchange': 'SHFE', 'sina_name': '镍'},
    '锡': {'symbol': 'SN', 'exchange': 'SHFE', 'sina_name': '锡'},
    # 黑色系
    '螺纹钢': {'symbol': 'RB', 'exchange': 'SHFE', 'sina_name': '螺纹钢'},
    '热卷': {'symbol': 'HC', 'exchange': 'SHFE', 'sina_name': '热轧卷板'},
    '铁矿石': {'symbol': 'I', 'exchange': 'DCE', 'sina_name': '铁矿石'},
    '焦炭': {'symbol': 'J', 'exchange': 'DCE', 'sina_name': '焦炭'},
    '焦煤': {'symbol': 'JM', 'exchange': 'DCE', 'sina_name': '焦煤'},
    # 能源化工
    '原油': {'symbol': 'SC', 'exchange': 'INE', 'sina_name': '上海原油'},
    '燃油': {'symbol': 'FU', 'exchange': 'SHFE', 'sina_name': '燃料油'},
    '沥青': {'symbol': 'BU', 'exchange': 'SHFE', 'sina_name': '沥青'},
    '橡胶': {'symbol': 'RU', 'exchange': 'SHFE', 'sina_name': '天然橡胶'},
    '塑料': {'symbol': 'L', 'exchange': 'DCE', 'sina_name': '塑料'},
    'PVC': {'symbol': 'V', 'exchange': 'DCE', 'sina_name': 'PVC'},
    'PTA': {'symbol': 'TA', 'exchange': 'CZCE', 'sina_name': 'PTA'},
    '甲醇': {'symbol': 'MA', 'exchange': 'CZCE', 'sina_name': '甲醇'},
    '玻璃': {'symbol': 'FG', 'exchange': 'CZCE', 'sina_name': '玻璃'},
    '纯碱': {'symbol': 'SA', 'exchange': 'CZCE', 'sina_name': '纯碱'},
    # 农产品
    '豆粕': {'symbol': 'M', 'exchange': 'DCE', 'sina_name': '豆粕'},
    '豆油': {'symbol': 'Y', 'exchange': 'DCE', 'sina_name': '豆油'},
    '棕榈油': {'symbol': 'P', 'exchange': 'DCE', 'sina_name': '棕榈油'},
    '玉米': {'symbol': 'C', 'exchange': 'DCE', 'sina_name': '玉米'},
    '棉花': {'symbol': 'CF', 'exchange': 'CZCE', 'sina_name': '棉花'},
    '白糖': {'symbol': 'SR', 'exchange': 'CZCE', 'sina_name': '白糖'},
    '鸡蛋': {'symbol': 'JD', 'exchange': 'DCE', 'sina_name': '鸡蛋'},
    '生猪': {'symbol': 'LH', 'exchange': 'DCE', 'sina_name': '生猪'},
    '苹果': {'symbol': 'AP', 'exchange': 'CZCE', 'sina_name': '苹果'},
    '红枣': {'symbol': 'CJ', 'exchange': 'CZCE', 'sina_name': '红枣'},
}

INVENTORY_MAPPING = {
    '铜': '沪铜', '铝': '沪铝', '锌': '沪锌', '铅': '沪铅', '镍': '沪镍',
    '锡': '沪锡', '黄金': '沪金', '白银': '沪银', '螺纹钢': '螺纹钢', '豆粕': '豆粕',
}


# ==================== 量化回测模块 ====================
# 定义 Backtrader 数据源
class AkShareData(bt.feeds.PandasData):
    """
    自定义数据源，适配 akshare 数据格式
    """
    params = (
        ('datetime', None),
        ('open', -1),
        ('high', -1),
        ('low', -1),
        ('close', -1),
        ('volume', -1),
        ('openinterest', -1)
    )

# 定义量化交易策略：简单的SMA交叉策略
class SmaCross(bt.Strategy):
    params = (
        ('short_period', 50),
        ('long_period', 200),
        ('printlog', False),
    )
    
    def __init__(self):
        # 定义两个简单移动平均线
        self.short_sma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.short_period)
        self.long_sma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.long_period)
        self.crossover = bt.indicators.CrossOver(self.short_sma, self.long_sma)

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def next(self):
        # 当短期SMA上穿长期SMA时买入
        if self.crossover > 0:
            if not self.position:
                self.log("金叉出现，买入！")
                self.buy(size=100) # 买入100股
        # 当短期SMA下穿长期SMA时卖出
        elif self.crossover < 0:
            if self.position:
                self.log("死叉出现，卖出！")
                self.close() # 全部卖出

class StockAnalyzer:
    def __init__(self, stock_code):
        """初始化分析器"""
        self.stock_code = stock_code
        self.stock_name = ""
        self.industry = ""
        self.output_dir = f"分析报告_{self.stock_code}_{datetime.now().strftime('%Y%m%d_%H%M')}"
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # 数据存储
        self.financial_data = None       # 财务摘要数据
        self.balance_sheet = None        # 资产负债表
        self.cash_flow_data = None       # 现金流量表
        self.current_valuation = {}      # 当前估值
        self.valuation_history = None    # 历史估值
        self.dividend_data = None        # 分红数据
        self.stock_kline = None          # K线数据（技术分析）
        self.northbound_data = None      # 北向资金数据
        self.margin_data = None          # 两融数据
        self.income_statement = None     # 新增：利润表
        self.total_shares = 0            # 新增：总股本
        self.shareholder_data = {}       # 新增：股东数据
        
        # 评分系统
        self.scores = {
            'growth': 0,        # 成长性
            'profitability': 0, # 盈利能力
            'stability': 0,     # 稳定性
            'safety': 0,        # 财务安全
            'valuation': 0      # 估值吸引力
        }
        
        # 报告文本收集器
        self.report_lines = []
        
        # 关键数据收集（用于结构化输出）
        self.report_data = {
            'basic_info': {},
            'fundamentals': {},
            'competitiveness': {},
            'risks': [],
            'valuation': {},
            'cash_flow': {},
            'warnings': [],
            'scores': {}
        }
        
        # 缓存：避免重复计算
        self._annual_df_cache = None
        
    @property
    def annual_df(self):
        """缓存的年度财务数据（只读）"""
        if self._annual_df_cache is None and self.financial_data is not None:
            self._annual_df_cache = self.financial_data[self.financial_data['截止日期'].dt.month == 12]
        return self._annual_df_cache
    
    def _log(self, text):
        """同时打印并收集报告文本"""
        print(text)
        self.report_lines.append(text)

    def _safe_float(self, value, default=0.0):
        """安全转换为浮点数"""
        try:
            if pd.isna(value) or value == '--' or value == '':
                return default
            return float(value)
        except (ValueError, TypeError):
            return default

    def _format_number(self, num, unit='亿'):
        """格式化数字"""
        if pd.isna(num) or num == '':
            return "--"
        try:
            num = float(num)
            if unit == '亿':
                return f"{num/1e8:.2f}亿"
            elif unit == '%':
                return f"{num:.2f}%"
            else:
                return f"{num:.2f}"
        except:
            return str(num)

    def _calculate_single_quarter_data(self, df):
        return analysis.calculate_single_quarter_data(df)

    def _calculate_ma_slope(self, series, period=120):
        return analysis.calculate_ma_slope(series, period)
    
    def _calculate_rsi(self, series, period=14):
        return analysis.calculate_rsi(series, period)
        
    def _calculate_macd(self, series, fast=12, slow=26, signal=9):
        return analysis.calculate_macd(series, fast, slow, signal)
        
    def _calculate_kdj(self, high, low, close, n=9, m1=3, m2=3):
        return analysis.calculate_kdj(high, low, close, n, m1, m2)

    def _calculate_ttm_series(self, df, col_name):
        return analysis.calculate_ttm_series(df, col_name)

    # ==================== 数据获取模块 ====================
    def fetch_data(self):
        """
        通过调用外部 data_fetcher 模块来获取所有数据
        """
        all_data = data_fetcher.fetch_all_data(self.stock_code)
        
        # 将获取的数据赋值给类的属性
        self.stock_name = all_data.get('stock_name')
        self.industry = all_data.get('industry')
        self.total_shares = all_data.get('total_shares')
        self.financial_data = all_data.get('financial_abstract')
        self.balance_sheet = all_data.get('balance_sheet')
        self.income_statement = all_data.get('income_statement')
        self.cash_flow_data = all_data.get('cash_flow')
        self.stock_kline = all_data.get('kline')
        self.dividend_data = all_data.get('dividend')
        self.northbound_data = all_data.get('northbound')
        self.shareholder_data = all_data.get('shareholder')
        self.current_valuation = all_data.get('current_valuation')



    # ==================== 核心增量分析模块（最重要）====================
    def analyze_growth_momentum(self):
        """功能0：增量分析 - 最重要的分析维度"""
        self._log("\n" + "="*60)
        self._log(f"  🚀【增量分析】{self.stock_name} ({self.stock_code})")
        self._log(f"  ⭐ 核心问题：业绩增量是否有预期？")
        self._log("="*60)
        
        if self.financial_data is None:
            self._log("❌ 无财务数据")
            return
        
        df = self.financial_data
        annual_df = self.annual_df  # 使用缓存
        
        # 计算单季度数据
        quarterly_df = self._calculate_single_quarter_data(df)
        
        # 初始化增量数据收集
        self.report_data['growth_momentum'] = {
            'summary': '',
            'quarterly_trend': [],
            'annual_trend': [],
            'growth_quality': '',
            'expectation': ''
        }
        
        self._log("\n" + "="*60)
        self._log("  📈 一、增量核心指标")
        self._log("="*60)
        
        # 1. 季度增量分析（最敏感）
        self._analyze_quarterly_growth(quarterly_df)
        
        # 2. 年度增量趋势
        self._analyze_annual_growth_trend(annual_df)
        
        # 3. 增长质量评估
        self._analyze_growth_quality(df)
        
        # 4. 预期判断
        self._analyze_expectation(df, annual_df)
        
        # 5. 生成增量可视化
        self._plot_growth_momentum(df, annual_df)
    
    def _analyze_quarterly_growth(self, df):
        """季度增量分析 - 最敏感的增量信号"""
        self._log("\n📊 1. 季度增量变化（关键！）")
        self._log("-" * 75)
        
        rev_col = next((c for c in df.columns if '营业总收入' in c or '营业收入' in c), None)
        profit_col = '净利润' if '净利润' in df.columns else None
        deducted_col = next((c for c in df.columns if '扣非' in c and '净利' in c), None)
        
        if not rev_col or not profit_col:
            self._log("  ⚠️ 数据不足")
            return
        
        # 获取最近12期数据（约3年季度），确保有足够数据计算同比环比
        recent = df.tail(12).copy()
        
        quarterly_data = []
        for idx, row in recent.iterrows():
            date = row['截止日期']
            quarter = f"{date.year}Q{(date.month-1)//3 + 1}"
            rev = self._safe_float(row[rev_col])
            profit = self._safe_float(row[profit_col])
            deducted = self._safe_float(row[deducted_col]) if deducted_col else 0
            quarterly_data.append({
                'quarter': quarter,
                'date': date,
                'revenue': rev,
                'profit': profit,
                'deducted': deducted
            })
        
        if len(quarterly_data) < 5:
            self._log("  ⚠️ 季度数据不足5期")
            return
        
        # 表头
        self._log(f"  {'季度':<8} {'营收(亿)':<10} {'同比':<9} {'环比':<9} {'净利(亿)':<10} {'同比':<9} {'环比':<9} {'净利率':<8}")
        self._log("  " + "-" * 73)
        
        yoy_revenues = []
        yoy_profits = []
        qoq_revenues = []
        qoq_profits = []
        
        # 只展示最近8个季度
        display_data = quarterly_data[-8:]
        
        for i, q in enumerate(display_data):
            # 找同期数据（去年同季度）
            yoy_q = None
            # 找上期数据（上个季度）
            qoq_q = None
            
            # 在完整列表中查找
            current_idx = quarterly_data.index(q)
            
            # 查找同比 (向前找4个季度)
            if current_idx >= 4:
                yoy_q = quarterly_data[current_idx - 4]
            
            # 查找环比 (向前找1个季度)
            if current_idx >= 1:
                qoq_q = quarterly_data[current_idx - 1]
            
            rev_yi = q['revenue'] / 1e8
            profit_yi = q['profit'] / 1e8
            net_margin = (q['profit'] / q['revenue'] * 100) if q['revenue'] > 0 else 0
            
            # 计算营收同比
            if yoy_q and yoy_q['revenue'] > 0:
                rev_yoy = (q['revenue'] - yoy_q['revenue']) / yoy_q['revenue']
                yoy_revenues.append(rev_yoy)
            else:
                rev_yoy = None
                
            # 计算营收环比
            if qoq_q and qoq_q['revenue'] > 0:
                rev_qoq = (q['revenue'] - qoq_q['revenue']) / qoq_q['revenue']
                qoq_revenues.append(rev_qoq)
            else:
                rev_qoq = None
            
            # 计算净利同比
            if yoy_q and abs(yoy_q['profit']) > 0:
                profit_yoy = (q['profit'] - yoy_q['profit']) / abs(yoy_q['profit'])
                yoy_profits.append(profit_yoy)
            else:
                profit_yoy = None
                
            # 计算净利环比
            if qoq_q and abs(qoq_q['profit']) > 0:
                profit_qoq = (q['profit'] - qoq_q['profit']) / abs(qoq_q['profit'])
                qoq_profits.append(profit_qoq)
            else:
                profit_qoq = None
            
            rev_yoy_str = f"{rev_yoy:+.1%}" if rev_yoy is not None else "-"
            rev_qoq_str = f"{rev_qoq:+.1%}" if rev_qoq is not None else "-"
            profit_yoy_str = f"{profit_yoy:+.1%}" if profit_yoy is not None else "-"
            profit_qoq_str = f"{profit_qoq:+.1%}" if profit_qoq is not None else "-"
            margin_str = f"{net_margin:.1f}%"
            
            self._log(f"  {q['quarter']:<8} {rev_yi:<10.2f} {rev_yoy_str:<9} {rev_qoq_str:<9} {profit_yi:<10.2f} {profit_yoy_str:<9} {profit_qoq_str:<9} {margin_str:<8}")
        
        # 分析趋势
        self._log("\n  📋 增量趋势判断:")
        
        if len(yoy_revenues) >= 2:
            recent_rev_trend = yoy_revenues[-1] - yoy_revenues[-2]
            latest_rev_yoy = yoy_revenues[-1]
            
            # 营收增速评级
            if latest_rev_yoy > 0.3:
                self._log(f"  ✅ 营收增速 {latest_rev_yoy:.1%}，高增长！")
                self.scores['growth'] += 30
            elif latest_rev_yoy > 0.1:
                self._log(f"  ✅ 营收增速 {latest_rev_yoy:.1%}，稳健增长")
                self.scores['growth'] += 15
            elif latest_rev_yoy > 0:
                self._log(f"  🔶 营收增速 {latest_rev_yoy:.1%}，低增长")
            else:
                self._log(f"  ❌ 营收同比下滑 {latest_rev_yoy:.1%}")
                self.scores['growth'] -= 20
            
            # 趋势加速/减速
            if recent_rev_trend > 0.05:
                self._log(f"  ⬆️ 营收加速：增速环比提升 {recent_rev_trend:.1%}")
            elif recent_rev_trend < -0.05:
                self._log(f"  ⬇️ 营收减速：增速环比下降 {abs(recent_rev_trend):.1%}")
            
            # 困境反转信号
            if len(yoy_revenues) >= 3:
                if yoy_revenues[-3] < 0 and yoy_revenues[-2] < 0 and yoy_revenues[-1] > 0:
                    self._log(f"  🚀 【重要信号】营收出现困境反转！(负转正)")
        
        if len(yoy_profits) >= 2:
            latest_profit_yoy = yoy_profits[-1]
            
            if latest_profit_yoy > 0.5:
                self._log(f"  ✅ 利润爆发式增长 {latest_profit_yoy:.1%}！")
            elif latest_profit_yoy > 0.2:
                self._log(f"  ✅ 利润高增长 {latest_profit_yoy:.1%}")
            elif latest_profit_yoy > 0:
                self._log(f"  🔶 利润正增长 {latest_profit_yoy:.1%}")
            else:
                self._log(f"  ❌ 利润下滑 {latest_profit_yoy:.1%}")
                
            # 利润剪刀差 (利润增速 > 营收增速)
            if len(yoy_revenues) >= 1 and latest_profit_yoy > yoy_revenues[-1] + 0.1:
                 self._log(f"  ✂️ 利润释放加速 (利润增速 > 营收增速 10%以上)")
        
        # 保存数据（转换日期为字符串以便JSON序列化）
        quarterly_data_json = [
            {
                'quarter': q['quarter'],
                'date': q['date'].strftime('%Y-%m-%d'),
                'revenue_yi': round(q['revenue'] / 1e8, 2),
                'profit_yi': round(q['profit'] / 1e8, 2),
            } for q in quarterly_data
        ]
        self.report_data['growth_momentum']['quarterly_trend'] = quarterly_data_json
    
    def _analyze_annual_growth_trend(self, annual_df):
        """年度增量趋势分析"""
        self._log("\n📊 2. 年度增量趋势")
        self._log("-" * 40)
        
        if len(annual_df) < 3:
            self._log("  ⚠️ 年度数据不足3年")
            return
        
        rev_col = next((c for c in annual_df.columns if '营业总收入' in c or '营业收入' in c), None)
        profit_col = '净利润' if '净利润' in annual_df.columns else None
        
        recent = annual_df.tail(5)
        
        self._log(f"  {'年份':<8} {'营收(亿)':<12} {'增速':<10} {'净利(亿)':<12} {'增速':<10}")
        self._log("  " + "-" * 52)
        
        prev_rev, prev_profit = None, None
        growth_rates = []
        
        for idx, row in recent.iterrows():
            year = row['截止日期'].year
            rev = self._safe_float(row[rev_col]) / 1e8
            profit = self._safe_float(row[profit_col]) / 1e8
            
            if prev_rev and prev_rev > 0:
                rev_growth = (rev * 1e8 - prev_rev * 1e8) / (prev_rev * 1e8)
            else:
                rev_growth = None
            
            if prev_profit and prev_profit > 0:
                profit_growth = (profit * 1e8 - prev_profit * 1e8) / (prev_profit * 1e8)
            else:
                profit_growth = None
            
            rev_g_str = f"{rev_growth:+.1%}" if rev_growth is not None else "-"
            profit_g_str = f"{profit_growth:+.1%}" if profit_growth is not None else "-"
            
            self._log(f"  {year:<8} {rev:<12.2f} {rev_g_str:<10} {profit:<12.2f} {profit_g_str:<10}")
            
            # 记录到report_data
            self.report_data['growth_momentum']['annual_trend'].append({
                'year': year,
                'revenue_yi': round(rev, 2),
                'profit_yi': round(profit, 2),
                'rev_growth': round(rev_growth, 4) if rev_growth else None,
                'profit_growth': round(profit_growth, 4) if profit_growth else None,
            })
            
            if rev_growth is not None and profit_growth is not None:
                growth_rates.append({'year': year, 'rev_growth': rev_growth, 'profit_growth': profit_growth})
            
            prev_rev, prev_profit = rev, profit
        
        # 计算CAGR (复合年均增长率)
        if len(annual_df) >= 4:
            try:
                latest = annual_df.iloc[-1]
                three_years_ago = annual_df.iloc[-4] # 3年前 (例如 2024, 2023, 2022, 2021)
                
                rev_latest = self._safe_float(latest[rev_col])
                rev_start = self._safe_float(three_years_ago[rev_col])
                
                profit_latest = self._safe_float(latest[profit_col])
                profit_start = self._safe_float(three_years_ago[profit_col])
                
                self._log("\n  📈 长期增长能力 (CAGR):")
                
                rev_cagr_3, profit_cagr_3 = None, None
                rev_cagr_5, profit_cagr_5 = None, None
                
                if rev_start > 0 and rev_latest > 0:
                    rev_cagr_3 = (rev_latest / rev_start) ** (1/3) - 1
                    self._log(f"    • 3年营收CAGR: {rev_cagr_3:.1%}")
                
                if profit_start > 0 and profit_latest > 0:
                    profit_cagr_3 = (profit_latest / profit_start) ** (1/3) - 1
                    self._log(f"    • 3年净利CAGR: {profit_cagr_3:.1%}")
                    
                # 5年CAGR
                if len(annual_df) >= 6:
                    five_years_ago = annual_df.iloc[-6]
                    rev_start_5 = self._safe_float(five_years_ago[rev_col])
                    profit_start_5 = self._safe_float(five_years_ago[profit_col])
                    
                    if rev_start_5 > 0 and rev_latest > 0:
                        rev_cagr_5 = (rev_latest / rev_start_5) ** (1/5) - 1
                        self._log(f"    • 5年营收CAGR: {rev_cagr_5:.1%}")
                    
                    if profit_start_5 > 0 and profit_latest > 0:
                        profit_cagr_5 = (profit_latest / profit_start_5) ** (1/5) - 1
                        self._log(f"    • 5年净利CAGR: {profit_cagr_5:.1%}")
                
                # 记录CAGR到report_data
                self.report_data['growth_momentum']['cagr'] = {
                    'rev_3y': round(rev_cagr_3, 4) if rev_cagr_3 else None,
                    'profit_3y': round(profit_cagr_3, 4) if profit_cagr_3 else None,
                    'rev_5y': round(rev_cagr_5, 4) if rev_cagr_5 else None,
                    'profit_5y': round(profit_cagr_5, 4) if profit_cagr_5 else None,
                }
            except Exception as e:
                pass

        # 增长持续性分析
        if len(growth_rates) >= 3:
            self._log("\n  📋 增长持续性:")
            consecutive_growth = sum(1 for g in growth_rates if g['rev_growth'] > 0)
            if consecutive_growth == len(growth_rates):
                self._log(f"  ✅ 连续{len(growth_rates)}年营收正增长，增长持续性强！")
                self.report_data['growth_momentum']['summary'] = '持续增长型'
            elif consecutive_growth >= len(growth_rates) - 1:
                self._log(f"  🔶 近{len(growth_rates)}年中{consecutive_growth}年正增长")
                self.report_data['growth_momentum']['summary'] = '波动增长型'
            else:
                self._log(f"  ⚠️ 增长不稳定，需关注业务周期性")
                self.report_data['growth_momentum']['summary'] = '周期波动型'
    
    def _analyze_growth_quality(self, df):
        """增长质量分析"""
        self._log("\n📊 3. 增长质量评估")
        self._log("-" * 40)
        
        rev_col = next((c for c in df.columns if '营业总收入' in c or '营业收入' in c), None)
        profit_col = '净利润' if '净利润' in df.columns else None
        deducted_col = next((c for c in df.columns if '扣非' in c and '净利' in c), None)
        cfo_col = next((c for c in df.columns if '经营' in c and '现金' in c and '净' in c), None)
        
        latest = df.iloc[-1]
        
        quality_score = 0
        quality_notes = []
        
        # 1. 扣非净利润 vs 净利润
        if profit_col and deducted_col:
            profit = self._safe_float(latest[profit_col])
            deducted = self._safe_float(latest[deducted_col])
            
            if profit > 0:
                deducted_ratio = deducted / profit
                if deducted_ratio > 0.8:
                    self._log(f"  ✅ 扣非占比 {deducted_ratio:.1%}，盈利质量高")
                    quality_score += 30
                    quality_notes.append("扣非占比高")
                elif deducted_ratio > 0.5:
                    self._log(f"  🔶 扣非占比 {deducted_ratio:.1%}，有非经常性收益")
                    quality_score += 10
                else:
                    self._log(f"  ⚠️ 扣非占比仅 {deducted_ratio:.1%}，非经常性损益过高！")
                    quality_notes.append("非经常性损益高")
        
        # 2. 现金流匹配度
        if cfo_col and profit_col:
            cfo = self._safe_float(latest[cfo_col])
            profit = self._safe_float(latest[profit_col])
            
            if profit > 0:
                cash_ratio = cfo / profit
                if cash_ratio > 1:
                    self._log(f"  ✅ 净现比 {cash_ratio:.2f}，现金流强劲")
                    quality_score += 30
                    quality_notes.append("现金流优秀")
                elif cash_ratio > 0.5:
                    self._log(f"  🔶 净现比 {cash_ratio:.2f}，现金流一般")
                    quality_score += 10
                else:
                    self._log(f"  ⚠️ 净现比 {cash_ratio:.2f}，现金流弱")
                    quality_notes.append("现金流弱")
        
        # 3. 毛利率趋势
        gross_col = next((c for c in df.columns if '毛利率' in c), None)
        if gross_col and len(df) >= 4:
            recent_gross = df.tail(4)[gross_col].apply(self._safe_float)
            gross_trend = recent_gross.iloc[-1] - recent_gross.iloc[0]
            
            if gross_trend > 2:
                self._log(f"  ✅ 毛利率上升 {gross_trend:.1f}pp，定价权增强")
                quality_score += 20
                quality_notes.append("毛利率上升")
            elif gross_trend < -2:
                self._log(f"  ⚠️ 毛利率下滑 {gross_trend:.1f}pp，竞争加剧")
                quality_notes.append("毛利率下滑")
        
        # 综合评价
        self._log(f"\n  📋 增长质量评分: {quality_score}/80")
        
        # 记录增长质量详情
        self.report_data['growth_momentum']['quality_score'] = quality_score
        self.report_data['growth_momentum']['quality_notes'] = quality_notes
        
        if quality_score >= 60:
            self.report_data['growth_momentum']['growth_quality'] = '优秀'
            self._log(f"  → 增长质量: 优秀 ✅")
        elif quality_score >= 30:
            self.report_data['growth_momentum']['growth_quality'] = '一般'
            self._log(f"  → 增长质量: 一般 🔶")
        else:
            self.report_data['growth_momentum']['growth_quality'] = '较弱'
            self._log(f"  → 增长质量: 较弱 ⚠️")
    
    def _analyze_expectation(self, df, annual_df):
        """预期判断 - 核心中的核心 (全面升级版)"""
        self._log("\n" + "="*60)
        self._log("  ⭐ 4. 增量预期判断（多维综合评估）")
        self._log("="*60)
        
        signals_positive = []
        signals_negative = []
        
        # ------------------------------------------------------
        # 1. ✅ 基本面指标（长期预期核心）
        # ------------------------------------------------------
        self._log("\n  [1] 基本面预期 (长期核心)")
        
        # (1) EPS增长率 (用净利润替代近似)
        profit_col = '净利润' if '净利润' in df.columns else None
        if len(annual_df) >= 4 and profit_col:
            profits = annual_df.tail(4)[profit_col].apply(self._safe_float)
            if profits.iloc[0] > 0 and profits.iloc[-1] > 0:
                cagr = (profits.iloc[-1] / profits.iloc[0]) ** (1/3) - 1
                if cagr > 0.15:
                    signals_positive.append(f"近3年净利CAGR {cagr:.1%} (>15%)")
                    self._log(f"    • 成长性: 强劲 (CAGR={cagr:.1%})")
                elif cagr > 0.05:
                    self._log(f"    • 成长性: 稳健 (CAGR={cagr:.1%})")
                else:
                    signals_negative.append(f"近3年净利CAGR {cagr:.1%} (增长停滞)")
                    self._log(f"    • 成长性: 停滞 (CAGR={cagr:.1%})")
        
        # (2) ROE (净资产收益率)
        roe_col = next((c for c in df.columns if '净资产收益率' in c), None)
        if roe_col:
            latest_roe = self._safe_float(df.iloc[-1][roe_col])
            if latest_roe > 15:
                signals_positive.append(f"ROE {latest_roe:.1f}% (>15%)")
                self._log(f"    • 资本效率: 优秀 (ROE={latest_roe:.1f}%)")
            elif latest_roe > 10:
                self._log(f"    • 资本效率: 良好 (ROE={latest_roe:.1f}%)")
            else:
                signals_negative.append(f"ROE {latest_roe:.1f}% (偏低)")
                self._log(f"    • 资本效率: 一般 (ROE={latest_roe:.1f}%)")
        
        # (3) 毛利率趋势
        gross_col = next((c for c in df.columns if '毛利率' in c), None)
        if gross_col and len(df) >= 5:
            recent_gross = df.tail(5)[gross_col].apply(self._safe_float)
            if recent_gross.is_monotonic_increasing:
                signals_positive.append("毛利率连续上升 (定价权增强)")
                self._log(f"    • 盈利质量: 毛利率提升")
            elif recent_gross.iloc[-1] < recent_gross.iloc[0] - 5:
                signals_negative.append("毛利率明显下滑")
                self._log(f"    • 盈利质量: 毛利率下滑")
        
        # (4) 现金流/净利润
        cfo_col = next((c for c in df.columns if '经营' in c and '现金' in c and '净' in c), None)
        if cfo_col and profit_col:
            cfo = self._safe_float(df.iloc[-1][cfo_col])
            profit = self._safe_float(df.iloc[-1][profit_col])
            if profit > 0:
                ratio = cfo / profit
                if ratio > 1:
                    signals_positive.append(f"净现比 {ratio:.2f} (>1)")
                    self._log(f"    • 现金流: 真金白银 (净现比={ratio:.2f})")
                elif ratio < 0.5:
                    signals_negative.append(f"净现比 {ratio:.2f} (偏低)")
                    self._log(f"    • 现金流: 较弱 (净现比={ratio:.2f})")
        
        # ------------------------------------------------------
        # [2] 估值与增长匹配度 (PEG)
        # ------------------------------------------------------
        self._log("\n  [2] 估值与增长匹配度 (PEG)")
        
        pe_ttm = self.current_valuation.get('pe_ttm', 0)
        if pe_ttm > 0:
            # 计算增长率 G (优先使用3年CAGR)
            g_rate = 0
            if 'cagr' in locals() and cagr > 0:
                g_rate = cagr * 100
            
            if g_rate > 0:
                peg = pe_ttm / g_rate
                self._log(f"    • 当前PE(TTM): {pe_ttm:.1f}")
                self._log(f"    • 参考增长率(G): {g_rate:.1f}% (基于3年CAGR)")
                
                if peg < 0.8:
                    self._log(f"    • PEG = {peg:.2f} (低估，极具性价比) ✅")
                    signals_positive.append(f"PEG {peg:.2f} < 0.8")
                elif peg < 1.2:
                    self._log(f"    • PEG = {peg:.2f} (合理) 🔶")
                else:
                    self._log(f"    • PEG = {peg:.2f} (偏高，需高增长消化) ⚠️")
            else:
                self._log(f"    • 无法计算PEG (无有效增长率)")
        else:
            self._log(f"    • 无法计算PEG (亏损或无PE)")

        # ------------------------------------------------------
        # 2. ✅ 估值指标（判断贵不贵）
        # ------------------------------------------------------
        self._log("\n  [2] 估值预期 (安全边际)")
        
        pe = self.current_valuation.get('pe_ttm', 0)
        pb = self.current_valuation.get('pb', 0)
        
        # (1) PEG (短期增长率)
        if pe > 0 and len(annual_df) >= 2 and profit_col:
            latest_profit = self._safe_float(annual_df.iloc[-1][profit_col])
            prev_profit = self._safe_float(annual_df.iloc[-2][profit_col])
            if prev_profit > 0:
                g = (latest_profit - prev_profit) / prev_profit * 100
                if g > 0:
                    peg = pe / g
                    if peg < 1:
                        signals_positive.append(f"PEG(短期) {peg:.2f} (<1 低估)")
                        self._log(f"    • PEG(短期): {peg:.2f} (低估)")
                    elif peg > 2:
                        signals_negative.append(f"PEG(短期) {peg:.2f} (>2 高估)")
                        self._log(f"    • PEG(短期): {peg:.2f} (高估)")
                    else:
                        self._log(f"    • PEG(短期): {peg:.2f} (合理)")
        
        # (2) PB (针对银行/周期)
        if pb > 0:
            if pb < 1:
                self._log(f"    • PB: {pb:.2f} (破净)")
                if '银行' in self.industry:
                    signals_positive.append(f"银行股破净 PB {pb:.2f}")
            elif pb > 10:
                signals_negative.append(f"PB {pb:.2f} (极高)")
        
        # (3) 股息率
        if self.dividend_data is not None and len(self.dividend_data) > 0:
            try:
                # 简单估算：取最近一次分红 * 4 (假设季度) 或 直接取最近年度分红
                # 这里简化处理：若最近一年有分红记录，计算股息率
                latest_div = self.dividend_data.iloc[0] # 假设按日期降序
                # 需要具体列名，暂且跳过复杂计算，仅作定性判断
                pass
            except:
                pass

        # ------------------------------------------------------
        # 3. ✅ 市场情绪与资金 (短期催化)
        # ------------------------------------------------------
        self._log("\n  [3] 资金与情绪 (短期催化)")
        
        # (1) 北向资金
        if self.northbound_data is not None and len(self.northbound_data) >= 5:
            nb_recent = self.northbound_data.tail(5)
            # 排除日期列，寻找数值列
            nb_col = next((c for c in nb_recent.columns if '持股' in c and '日期' not in c), None)
            if nb_col:
                try:
                    val_end = self._safe_float(nb_recent[nb_col].iloc[-1])
                    val_start = self._safe_float(nb_recent[nb_col].iloc[0])
                    trend = val_end - val_start
                    
                    if trend > 0:
                        signals_positive.append("北向资金近期加仓")
                        self._log(f"    • 北向资金: 加仓趋势")
                    else:
                        signals_negative.append("北向资金近期减仓")
                        self._log(f"    • 北向资金: 减仓趋势")
                except:
                    self._log(f"    • 北向资金: 数据解析错误")
        else:
            self._log(f"    • 北向资金: 无数据")
            
        # (2) 融资融券 (情绪指标)
        if self.margin_data is not None:
            # 融资余额高通常代表散户看多，融券余额高代表看空
            # 这里仅展示数据
            try:
                rzye = self._safe_float(self.margin_data.get('融资余额'))
                rqye = self._safe_float(self.margin_data.get('融券余额'))
                if rzye > 0:
                    self._log(f"    • 融资余额: {self._format_number(rzye)}")
                if rqye > 0:
                    self._log(f"    • 融券余额: {self._format_number(rqye)}")
            except:
                pass

        # ------------------------------------------------------
        # 4. ✅ 技术面辅助 (择时信号)
        # ------------------------------------------------------
        self._log("\n  [4] 技术面信号 (辅助择时)")
        
        if self.stock_kline is not None and len(self.stock_kline) > 120:
            closes = self.stock_kline['收盘']
            
            # (1) 120日均线趋势
            ma120_slope = self._calculate_ma_slope(closes, 120)
            if ma120_slope > 5:
                signals_positive.append("120日均线向上 (中期多头)")
                self._log(f"    • 趋势: 中期向上 (斜率{ma120_slope:.1f})")
            elif ma120_slope < -5:
                signals_negative.append("120日均线向下 (中期空头)")
                self._log(f"    • 趋势: 中期向下 (斜率{ma120_slope:.1f})")
            else:
                self._log(f"    • 趋势: 震荡整理")
            
            # (2) RSI(14)
            rsi = self._calculate_rsi(closes, 14).iloc[-1]
            if rsi < 30:
                signals_positive.append(f"RSI {rsi:.1f} (超卖)")
                self._log(f"    • RSI: {rsi:.1f} (超卖区)")
            elif rsi > 70:
                signals_negative.append(f"RSI {rsi:.1f} (超买)")
                self._log(f"    • RSI: {rsi:.1f} (超买区)")
            else:
                self._log(f"    • RSI: {rsi:.1f} (中性)")
            
            # (3) MACD (10,20,8)
            dif, dea, macd = self._calculate_macd(closes, fast=10, slow=20, signal=8)
            latest_dif = dif.iloc[-1]
            latest_dea = dea.iloc[-1]
            latest_macd = macd.iloc[-1]
            prev_macd = macd.iloc[-2] if len(macd) > 1 else 0
            
            if latest_dif > latest_dea and prev_macd < 0 and latest_macd > 0:
                signals_positive.append("MACD金叉")
                self._log(f"    • MACD: 金叉信号 (DIF={latest_dif:.2f})")
            elif latest_dif < latest_dea and prev_macd > 0 and latest_macd < 0:
                signals_negative.append("MACD死叉")
                self._log(f"    • MACD: 死叉信号 (DIF={latest_dif:.2f})")
            elif latest_dif > 0 and latest_dea > 0:
                self._log(f"    • MACD: 多头区间 (DIF={latest_dif:.2f})")
            elif latest_dif < 0 and latest_dea < 0:
                self._log(f"    • MACD: 空头区间 (DIF={latest_dif:.2f})")
            else:
                self._log(f"    • MACD: 中性 (DIF={latest_dif:.2f})")
            
            # (4) KDJ
            highs = self.stock_kline['最高']
            lows = self.stock_kline['最低']
            k, d, j = self._calculate_kdj(highs, lows, closes)
            latest_k = k.iloc[-1]
            latest_d = d.iloc[-1]
            latest_j = j.iloc[-1]
            
            if latest_j < 20:
                signals_positive.append(f"KDJ超卖 (J={latest_j:.1f})")
                self._log(f"    • KDJ: J={latest_j:.1f} (超卖区)")
            elif latest_j > 80:
                signals_negative.append(f"KDJ超买 (J={latest_j:.1f})")
                self._log(f"    • KDJ: J={latest_j:.1f} (超买区)")
            elif len(k) > 1 and latest_k > latest_d and k.iloc[-2] < d.iloc[-2]:
                signals_positive.append("KDJ金叉")
                self._log(f"    • KDJ: 金叉信号 (K={latest_k:.1f}, D={latest_d:.1f})")
            elif len(k) > 1 and latest_k < latest_d and k.iloc[-2] > d.iloc[-2]:
                signals_negative.append("KDJ死叉")
                self._log(f"    • KDJ: 死叉信号 (K={latest_k:.1f}, D={latest_d:.1f})")
            else:
                self._log(f"    • KDJ: K={latest_k:.1f}, D={latest_d:.1f}, J={latest_j:.1f}")
        else:
            self._log(f"    • 技术指标: 数据不足")

        # ------------------------------------------------------
        # 结论汇总
        # ------------------------------------------------------
        self._log("\n  " + "="*56)
        self._log("  📊 综合预期结论")
        self._log("  " + "-"*56)
        
        if signals_positive:
            self._log("  ✅ 积极信号:")
            for s in signals_positive:
                self._log(f"     + {s}")
        
        if signals_negative:
            self._log("  ⚠️ 风险信号:")
            for s in signals_negative:
                self._log(f"     - {s}")
        
        net_score = len(signals_positive) - len(signals_negative)
        
        if net_score >= 2:
            expectation = "积极"
            self._log(f"\n  📣 最终判定: 🟢 增量预期【积极】")
            self._log(f"     基本面/资金面共振，建议重点关注")
        elif net_score >= 0:
            expectation = "中性"
            self._log(f"\n  📣 最终判定: 🟡 增量预期【中性】")
            self._log(f"     多空信号交织，建议观望或轻仓")
        else:
            expectation = "谨慎"
            self._log(f"\n  📣 最终判定: 🔴 增量预期【谨慎】")
            self._log(f"     风险信号主导，建议规避")
        
        # 记录信号到report_data
        self.report_data['growth_momentum']['signals'] = {
            'positive': signals_positive,
            'negative': signals_negative,
            'net_score': net_score,
        }
        self.report_data['growth_momentum']['expectation'] = expectation
        self._log("  " + "="*56)

    def _plot_growth_momentum(self, df, annual_df):
        """生成增量分析图表"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        rev_col = next((c for c in df.columns if '营业总收入' in c or '营业收入' in c), None)
        profit_col = '净利润' if '净利润' in df.columns else None
        
        # 图1: 季度营收增速走势
        ax1 = axes[0, 0]
        recent = df.tail(12)
        
        quarters = []
        rev_yoys = []
        
        for idx, row in recent.iterrows():
            date = row['截止日期']
            quarter = f"{date.year}Q{(date.month-1)//3 + 1}"
            
            # 找同期
            yoy_data = df[
                (df['截止日期'].dt.month == date.month) & 
                (df['截止日期'].dt.year == date.year - 1)
            ]
            
            if not yoy_data.empty and rev_col:
                prev_rev = self._safe_float(yoy_data.iloc[0][rev_col])
                curr_rev = self._safe_float(row[rev_col])
                if prev_rev > 0:
                    yoy = (curr_rev - prev_rev) / prev_rev * 100
                    quarters.append(quarter)
                    rev_yoys.append(yoy)
        
        if quarters:
            colors = [COLORS['success'] if y > 0 else COLORS['danger'] for y in rev_yoys]
            bars = ax1.bar(quarters, rev_yoys, color=colors, alpha=0.8)
            ax1.axhline(y=0, color='gray', linestyle='--', linewidth=1)
            ax1.set_title('季度营收同比增速 (%)', fontsize=12, fontweight='bold')
            ax1.set_ylabel('同比增速 %')
            ax1.tick_params(axis='x', rotation=45)
            
            # 添加数值标签
            for bar, val in zip(bars, rev_yoys):
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                        f'{val:.1f}%', ha='center', va='bottom', fontsize=8)
        
        # 图2: 季度净利增速走势
        ax2 = axes[0, 1]
        
        profit_yoys = []
        profit_quarters = []
        
        for idx, row in recent.iterrows():
            date = row['截止日期']
            quarter = f"{date.year}Q{(date.month-1)//3 + 1}"
            
            yoy_data = df[
                (df['截止日期'].dt.month == date.month) & 
                (df['截止日期'].dt.year == date.year - 1)
            ]
            
            if not yoy_data.empty and profit_col:
                prev_profit = self._safe_float(yoy_data.iloc[0][profit_col])
                curr_profit = self._safe_float(row[profit_col])
                if prev_profit > 0:
                    yoy = (curr_profit - prev_profit) / prev_profit * 100
                    profit_quarters.append(quarter)
                    profit_yoys.append(yoy)
        
        if profit_quarters:
            colors = [COLORS['success'] if y > 0 else COLORS['danger'] for y in profit_yoys]
            bars = ax2.bar(profit_quarters, profit_yoys, color=colors, alpha=0.8)
            ax2.axhline(y=0, color='gray', linestyle='--', linewidth=1)
            ax2.set_title('季度净利润同比增速 (%)', fontsize=12, fontweight='bold')
            ax2.set_ylabel('同比增速 %')
            ax2.tick_params(axis='x', rotation=45)
            
            for bar, val in zip(bars, profit_yoys):
                ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                        f'{val:.1f}%', ha='center', va='bottom', fontsize=8)
        
        # 图3: 年度营收净利双轴图
        ax3 = axes[1, 0]
        
        if len(annual_df) >= 3:
            years = annual_df.tail(5)['截止日期'].dt.year.astype(str)
            revenues = annual_df.tail(5)[rev_col].apply(self._safe_float) / 1e8 if rev_col else []
            profits = annual_df.tail(5)[profit_col].apply(self._safe_float) / 1e8 if profit_col else []
            
            x = np.arange(len(years))
            width = 0.35
            
            bars1 = ax3.bar(x - width/2, revenues, width, label='营收', color=COLORS['revenue'], alpha=0.8)
            
            ax3_twin = ax3.twinx()
            bars2 = ax3_twin.bar(x + width/2, profits, width, label='净利润', color=COLORS['profit'], alpha=0.8)
            
            ax3.set_xlabel('年份')
            ax3.set_ylabel('营收 (亿)', color=COLORS['revenue'])
            ax3_twin.set_ylabel('净利润 (亿)', color=COLORS['profit'])
            ax3.set_xticks(x)
            ax3.set_xticklabels(years)
            ax3.set_title('年度营收与净利润', fontsize=12, fontweight='bold')
            
            # 合并图例
            lines1, labels1 = ax3.get_legend_handles_labels()
            lines2, labels2 = ax3_twin.get_legend_handles_labels()
            ax3.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        # 图4: 增量预期信号板（修复中文显示）
        ax4 = axes[1, 1]
        ax4.axis('off')
        
        expectation = self.report_data['growth_momentum'].get('expectation', '未知')
        quality = self.report_data['growth_momentum'].get('growth_quality', '未知')
        summary = self.report_data['growth_momentum'].get('summary', '未知')
        
        # 根据预期设置背景色和图标
        if expectation == '积极':
            bg_color = '#e8f5e9'
            exp_icon = '🟢'
            exp_text = '有增量预期'
        elif expectation == '谨慎':
            bg_color = '#ffebee'
            exp_icon = '🔴'
            exp_text = '增量预期转弱'
        else:
            bg_color = '#fff8e1'
            exp_icon = '🟡'
            exp_text = '增量中性'
        
        ax4.set_facecolor(bg_color)
        
        # 使用多行文本，不用monospace字体
        ax4.text(0.5, 0.85, '📊 增量分析总结', transform=ax4.transAxes, fontsize=14,
                fontweight='bold', ha='center', va='center')
        
        ax4.text(0.5, 0.65, f'增长类型: {summary}', transform=ax4.transAxes, fontsize=12,
                ha='center', va='center')
        
        ax4.text(0.5, 0.50, f'增长质量: {quality}', transform=ax4.transAxes, fontsize=12,
                ha='center', va='center')
        
        ax4.text(0.5, 0.35, f'增量预期: {exp_icon} {exp_text}', transform=ax4.transAxes, fontsize=13,
                ha='center', va='center', fontweight='bold')
        
        # 添加边框效果
        ax4.add_patch(plt.Rectangle((0.05, 0.15), 0.9, 0.75, fill=False, 
                                    edgecolor='gray', linewidth=2, transform=ax4.transAxes))
        
        ax4.set_title('增量预期信号', fontsize=12, fontweight='bold')
        
        plt.suptitle(f'{self.stock_name} ({self.stock_code}) - 增量分析', 
                    fontsize=14, fontweight='bold', y=1.02)
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/0_增量分析.png", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ 生成图表: 0_增量分析.png")

    # ==================== 公司分析模块 ====================
    def analyze_company(self):
        """功能1：公司全面分析"""
        self._log("\n" + "="*60)
        self._log(f"  【公司分析报告】{self.stock_name} ({self.stock_code})")
        self._log(f"  行业: {self.industry} | 分析日期: {datetime.now().strftime('%Y-%m-%d')}")
        self._log("="*60)
        
        if self.financial_data is None:
            self._log("❌ 无财务数据，无法分析")
            return
        
        df = self.financial_data
        annual_df = self.annual_df  # 使用缓存
        latest = df.iloc[-1]
        
        # 1. 基本面概览
        self._analyze_fundamentals(df, annual_df)
        
        # 2. 核心竞争力
        self._analyze_competitiveness(df, latest)

        # 2.1 同行业对比 (同花顺数据)
        self._analyze_industry_comparison()
        
        # 3. 财务安全与风险
        self._analyze_risks(df, latest)
        
        # 4. 分红能力
        self._analyze_dividend()
        
        # 5. 估值分析
        self._analyze_valuation()
        
        # 6. 综合评分
        self._calculate_scores(df, annual_df, latest)
        
        # 7. 生成可视化
        self._plot_company_analysis(annual_df, df)
    
    def _analyze_fundamentals(self, df, annual_df):
        """分析基本面：增长与行业阶段"""
        self._log("\n📊 1. 基本面概览")
        self._log("-" * 40)
        
        rev_col = next((c for c in df.columns if '营业总收入' in c or '营业收入' in c), None)
        profit_col = '净利润' if '净利润' in df.columns else None
        deducted_col = next((c for c in df.columns if '扣非' in c and '净利' in c), None)
        
        if len(annual_df) >= 3 and rev_col and profit_col:
            recent_3y = annual_df.tail(3)
            
            rev_start = self._safe_float(recent_3y.iloc[0][rev_col])
            rev_end = self._safe_float(recent_3y.iloc[-1][rev_col])
            profit_start = self._safe_float(recent_3y.iloc[0][profit_col])
            profit_end = self._safe_float(recent_3y.iloc[-1][profit_col])
            
            self._log(f"  • 最新营收: {self._format_number(rev_end)}")
            self._log(f"  • 最新净利润: {self._format_number(profit_end)}")
            
            # 计算营收CAGR
            if rev_start > 0 and rev_end > 0:
                rev_cagr = (rev_end / rev_start) ** 0.5 - 1
                self._log(f"  • 近3年营收CAGR: {rev_cagr:+.1%}")
            else:
                rev_cagr = 0
                self._log(f"  • 近3年营收CAGR: 无法计算 (存在负值)")
            
            # 计算净利CAGR - 需要处理负利润情况
            if profit_start > 0 and profit_end > 0:
                profit_cagr = (profit_end / profit_start) ** 0.5 - 1
                self._log(f"  • 近3年净利CAGR: {profit_cagr:+.1%}")
            elif profit_end < 0:
                self._log(f"  • 近3年净利CAGR: ⚠️ 当前亏损，无法计算")
                self.scores['growth'] = max(self.scores['growth'] - 20, 0)
            elif profit_start < 0 and profit_end > 0:
                self._log(f"  • 近3年净利CAGR: ✅ 扭亏为盈")
                self.scores['growth'] = 60
            else:
                self._log(f"  • 近3年净利CAGR: 无法计算")
            
            # 判断行业阶段
            if rev_cagr > 0.20:
                stage = "🚀 高速成长期"
                self.scores['growth'] = 90
            elif rev_cagr > 0.10:
                stage = "📈 稳健成长期"
                self.scores['growth'] = 70
            elif rev_cagr > 0.03:
                stage = "📊 成熟稳定期"
                self.scores['growth'] = 50
            elif profit_end < 0:
                stage = "🔴 亏损期"
                self.scores['growth'] = 10
            else:
                stage = "⚠️ 衰退/转型期"
                self.scores['growth'] = 30
            self._log(f"  • 行业阶段: {stage}")
        
        # 扣非净利润分析
        if deducted_col:
            latest = df.iloc[-1]
            net_profit = self._safe_float(latest[profit_col])
            deducted_profit = self._safe_float(latest[deducted_col])
            
            if net_profit != 0:
                deducted_ratio = deducted_profit / net_profit
                non_recurring = (net_profit - deducted_profit) / net_profit
                
                self._log(f"\n  📋 扣非净利润分析:")
                self._log(f"     净利润: {self._format_number(net_profit)}")
                self._log(f"     扣非净利润: {self._format_number(deducted_profit)}")
                self._log(f"     非经常性损益占比: {non_recurring:.1%}")
                
                if non_recurring > 0.3:
                    self._log(f"     ⚠️ 警告: 非经常性损益占比过高，盈利质量需关注！")
                elif non_recurring < 0:
                    self._log(f"     ⚠️ 注意: 存在非经常性亏损")
    
    def _analyze_competitiveness(self, df, latest):
        """分析核心竞争力：护城河"""
        self._log("\n🏰 2. 核心竞争力评估")
        self._log("-" * 40)
        
        # 毛利率
        gross_col = next((c for c in df.columns if '毛利率' in c), None)
        # 净利率  
        net_margin_col = next((c for c in df.columns if '净利率' in c or '销售净利率' in c), None)
        # ROE
        roe_col = next((c for c in df.columns if '净资产收益率' in c), None)
        
        moat_score = 0
        
        if gross_col:
            gross_margin = self._safe_float(latest[gross_col])
            # 计算毛利率稳定性（近5年标准差）
            recent_5y = df[df['截止日期'].dt.month == 12].tail(5)
            if len(recent_5y) > 1:
                gross_std = recent_5y[gross_col].apply(self._safe_float).std()
                self._log(f"  • 毛利率: {gross_margin:.1f}% (波动: ±{gross_std:.1f}%)")
            else:
                self._log(f"  • 毛利率: {gross_margin:.1f}%")
            
            if gross_margin > 50:
                self._log(f"    → 极高毛利，具备强定价权/品牌溢价")
                moat_score += 30
            elif gross_margin > 30:
                self._log(f"    → 较高毛利，有一定竞争优势")
                moat_score += 20
            elif gross_margin > 15:
                self._log(f"    → 毛利一般，竞争较激烈")
                moat_score += 10
        
        if net_margin_col:
            net_margin = self._safe_float(latest[net_margin_col])
            self._log(f"  • 净利率: {net_margin:.1f}%")
            if net_margin > 20:
                moat_score += 20
            elif net_margin > 10:
                moat_score += 10
        
        if roe_col:
            roe = self._safe_float(latest[roe_col])
            self._log(f"  • ROE(净资产收益率): {roe:.1f}%")
            
            if roe > 20:
                self._log(f"    → 卓越的资本回报能力")
                moat_score += 30
            elif roe > 15:
                self._log(f"    → 优秀的资本回报")
                moat_score += 20
            elif roe > 10:
                self._log(f"    → 良好的资本回报")
                moat_score += 10
        
        # 护城河综合评估
        if moat_score >= 60:
            self._log(f"\n  🏆 护城河评估: 强 (得分: {moat_score})")
        elif moat_score >= 40:
            self._log(f"\n  ✅ 护城河评估: 中等 (得分: {moat_score})")
        else:
            self._log(f"\n  ⚠️ 护城河评估: 较弱 (得分: {moat_score})")
        
        self.scores['profitability'] = min(moat_score, 100)

    def _analyze_industry_comparison(self):
        """同行业对比分析 (基于 akshare)"""
        self._log("\n📊 2.1 同行业对比")
        self._log("-" * 60)
        
        # 使用已知行业或尝试查找
        industry_name = self.industry
        
        # 如果行业名称为空或"未知"，尝试从行业板块查找
        if not industry_name or industry_name == "未知":
            self._log("  ⚠️ 未获取到行业信息，跳过同行业对比")
            return
        
        # 获取行业成分股对比
        df = industry_compare.get_industry_comparison(industry_name, self.stock_code)
        self.industry_comp_df = df
        
        if df is None or df.empty:
            self._log(f"  ⚠️ 获取 [{industry_name}] 行业成分股失败")
            return
        
        # 获取行业统计
        stats = industry_compare.get_industry_stats(industry_name)
        if stats:
            self._log(f"  行业: {industry_name} | 成分股: {stats.get('成分股数', 'N/A')} 家")
            pe_median = stats.get('PE中位数')
            pb_median = stats.get('PB中位数')
            if pe_median:
                self._log(f"  行业PE中位数: {pe_median:.1f} | 行业PB中位数: {pb_median:.2f}" if pb_median else f"  行业PE中位数: {pe_median:.1f}")
        
        # 打印表头
        self._log(f"\n  {'标记':<2} {'名称':<6} | {'股价':<8} | {'涨跌幅':<6} | {'PE':<6} | {'PB':<5}")
        self._log(f"  {'-'*50}")
        
        # 显示前5名和本公司
        shown_count = 0
        shown_myself = False
        my_row = None
        
        for _, row in df.iterrows():
            code = str(row.get('代码', ''))
            is_me = (code == self.stock_code)
            
            if is_me:
                my_row = row
                shown_myself = True
            
            # 只显示前5名
            if shown_count < 5:
                name = str(row.get('名称', ''))[:4]
                price = row.get('股价', 0)
                change = row.get('涨跌幅', 0)
                pe = row.get('PE(动态)', 0)
                pb = row.get('PB', 0)
                
                prefix = "👉" if is_me else "  "
                price_str = f"{price:.2f}" if price else "-"
                change_str = f"{change:+.2f}%" if change else "-"
                pe_str = f"{pe:.1f}" if pe and pe > 0 else "-"
                pb_str = f"{pb:.2f}" if pb and pb > 0 else "-"
                
                self._log(f"  {prefix} {name:<6} | {price_str:<8} | {change_str:<6} | {pe_str:<6} | {pb_str:<5}")
                shown_count += 1
        
        # 如果本公司不在前5，单独显示
        if not shown_myself and my_row is not None:
            self._log(f"  ...")
            name = str(my_row.get('名称', ''))[:4]
            price = my_row.get('股价', 0)
            change = my_row.get('涨跌幅', 0)
            pe = my_row.get('PE(动态)', 0)
            pb = my_row.get('PB', 0)
            
            price_str = f"{price:.2f}" if price else "-"
            change_str = f"{change:+.2f}%" if change else "-"
            pe_str = f"{pe:.1f}" if pe and pe > 0 else "-"
            pb_str = f"{pb:.2f}" if pb and pb > 0 else "-"
            
            self._log(f"  👉 {name:<6} | {price_str:<8} | {change_str:<6} | {pe_str:<6} | {pb_str:<5}")
        elif not shown_myself:
            self._log(f"\n  (注: 未在 [{industry_name}] 行业中找到本公司)")

    def _analyze_risks(self, df, latest):
        """分析财务风险"""
        self._log("\n⚠️ 3. 财务风险评估")
        self._log("-" * 40)
        
        risk_items = []
        safety_score = 100
        
        # 资产负债率
        debt_col = next((c for c in df.columns if '资产负债率' in c), None)
        if debt_col:
            debt_ratio = self._safe_float(latest[debt_col])
            self._log(f"  • 资产负债率: {debt_ratio:.1f}%")
            
            if debt_ratio > 70:
                risk_items.append("🔴 高负债风险")
                safety_score -= 30
            elif debt_ratio > 50:
                self._log(f"    → 负债水平适中")
            else:
                self._log(f"    → 负债较低，财务稳健")
                safety_score += 10
        
        # 流动比率（从资产负债表获取）
        if self.balance_sheet is not None and len(self.balance_sheet) > 0:
            bs_latest = self.balance_sheet.iloc[-1]
            
            # 尝试获取流动资产和流动负债
            current_assets = self._safe_float(bs_latest.get('流动资产合计'))
            current_liab = self._safe_float(bs_latest.get('流动负债合计'))
            
            if current_liab > 0:
                current_ratio = current_assets / current_liab
                self._log(f"  • 流动比率: {current_ratio:.2f}")
                
                if current_ratio < 1:
                    risk_items.append("🔴 短期偿债压力")
                    safety_score -= 20
                elif current_ratio > 2:
                    self._log(f"    → 短期偿债能力强")
            
            # 应收账款与坏账风险 (最大坏账可能)
            receivables = self._safe_float(bs_latest.get('应收账款'))
            notes_recv = self._safe_float(bs_latest.get('应收票据'))
            other_recv = self._safe_float(bs_latest.get('其他应收款'))
            
            # 广义应收款 = 应收 + 票据 + 其他 (可能是坏账的极限)
            broad_receivables = receivables + notes_recv + other_recv
            
            revenue_col = next((c for c in df.columns if '营业总收入' in c or '营业收入' in c), None)
            total_assets = self._safe_float(bs_latest.get('资产总计'))
            
            if revenue_col and broad_receivables > 0:
                revenue = self._safe_float(latest[revenue_col])
                
                if revenue > 0:
                    recv_to_rev = broad_receivables / revenue
                    recv_to_asset = broad_receivables / total_assets if total_assets > 0 else 0
                    
                    self._log(f"  • 广义应收款: {self._format_number(broad_receivables)} (含票据/其他)")
                    self._log(f"  • 应收/营收比: {recv_to_rev:.1%}")
                    self._log(f"  • 最大坏账敞口/总资产: {recv_to_asset:.1%}")
                    
                    if recv_to_rev > 0.6:
                        risk_items.append("🔴 应收账款过高 (可能虚增营收)")
                        safety_score -= 20
                    elif recv_to_rev > 0.3:
                        risk_items.append("🟠 回款压力较大")
                        safety_score -= 10
            
            # 存货风险
            inventory = self._safe_float(bs_latest.get('存货'))
            if revenue_col and inventory > 0:
                if revenue > 0:
                    inventory_ratio = inventory / revenue
                    self._log(f"  • 存货/营收: {inventory_ratio:.1%}")
                    
                    if inventory_ratio > 0.5:
                        risk_items.append("🟠 存货占比高 (可能有积压)")
                        safety_score -= 10
        
        # 输出风险汇总
        if risk_items:
            self._log(f"\n  ⚠️ 主要风险点:")
            for item in risk_items:
                self._log(f"     {item}")
            self.report_data['risks'] = risk_items
        else:
            self._log(f"\n  ✅ 未发现重大财务风险")
        
        self.scores['safety'] = max(safety_score, 0)
    
    def _analyze_dividend(self):
        """分析分红能力"""
        self._log("\n💰 4. 分红能力")
        self._log("-" * 40)
        
        if self.dividend_data is None or len(self.dividend_data) == 0:
            self._log("  • 暂无分红记录")
            return
        
        # 计算近5年分红情况
        try:
            recent_div = self.dividend_data.head(5)  # 假设按时间倒序
            total_div = 0
            div_count = len(recent_div)
            
            self._log(f"  • 近5年分红次数: {div_count} 次")
            
            # 计算股息率（如果有当前市值）
            if self.current_valuation.get('total_mv', 0) > 0:
                # 这里简化处理，实际应该计算更精确的股息率
                mv = self.current_valuation['total_mv']
                self._log(f"  • 当前总市值: {self._format_number(mv)}")
                
            if div_count >= 3:
                self._log(f"    → 分红记录良好，股东回报意识较强")
                self.scores['stability'] += 20
        except Exception as e:
            self._log(f"  • 分红数据解析失败: {e}")
    
    def _analyze_valuation(self):
        """估值分析"""
        self._log("\n📈 5. 估值分析")
        self._log("-" * 40)
        
        if not self.current_valuation:
            self._log("  • 无法获取估值数据")
            return
        
        pe = self.current_valuation.get('pe_ttm', 0)
        pb = self.current_valuation.get('pb', 0)
        mv = self.current_valuation.get('total_mv', 0)
        
        self._log(f"  • 当前股价: ¥{self.current_valuation.get('price', 0):.2f}")
        self._log(f"  • 总市值: {self._format_number(mv)}")
        self._log(f"  • PE(TTM): {pe:.1f}")
        self._log(f"  • PB: {pb:.2f}")
        
        # 估值评价
        valuation_score = 50  # 基准分
        
        if pe > 0:
            if pe < 15:
                self._log(f"    → PE较低，可能被低估")
                valuation_score += 30
            elif pe < 30:
                self._log(f"    → PE合理区间")
                valuation_score += 10
            elif pe < 50:
                self._log(f"    → PE偏高，注意成长性是否匹配")
                valuation_score -= 10
            else:
                self._log(f"    → PE过高，需谨慎")
                valuation_score -= 20
        
        if pb > 0:
            if pb < 1:
                self._log(f"    → 破净股，需分析资产质量")
            elif pb < 2:
                self._log(f"    → PB较低")
                valuation_score += 10
        
        # 适合的投资者类型
        self._log(f"\n  📌 投资者类型建议:")
        if pe < 20 and self.scores.get('growth', 0) < 50:
            self._log(f"     适合: 价值投资型 (低估值稳健股)")
        elif self.scores.get('growth', 0) > 70:
            self._log(f"     适合: 成长投资型 (高增长追踪)")
        else:
            self._log(f"     适合: 均衡配置型")
        
        self.scores['valuation'] = max(min(valuation_score, 100), 0)
    
    def _calculate_scores(self, df, annual_df, latest):
        """计算综合评分"""
        # 稳定性评分 - 基于盈利波动
        if len(annual_df) >= 3:
            profit_col = '净利润' if '净利润' in annual_df.columns else None
            if profit_col:
                profits = annual_df[profit_col].apply(self._safe_float).tail(5)
                if len(profits) > 1 and profits.mean() != 0:
                    cv = profits.std() / abs(profits.mean())  # 变异系数
                    if cv < 0.2:
                        self.scores['stability'] = 80
                    elif cv < 0.5:
                        self.scores['stability'] = 60
                    else:
                        self.scores['stability'] = 40
    
    # ==================== 量化回测模块 ====================
    def run_backtest(self):
        """功能3：运行量化回测"""
        self._log("\n" + "="*60)
        self._log(f"  🤖【量化回测】{self.stock_name} ({self.stock_code})")
        self._log("="*60)
        
        if self.stock_kline is None or len(self.stock_kline) < 200:
            self._log("❌ K线数据不足，无法回测 (需要至少200天)")
            return
            
        try:
            # 1. 准备数据
            df = self.stock_kline.copy()
            # 映射列名
            df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '最高': 'high',
                '最低': 'low',
                '收盘': 'close',
                '成交量': 'volume'
            }, inplace=True)
            
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            df['openinterest'] = 0
            
            # 2. 设置回测引擎
            cerebro = bt.Cerebro()
            data = AkShareData(dataname=df)
            cerebro.adddata(data)
            
            # 3. 添加策略
            cerebro.addstrategy(SmaCross, printlog=False)
            
            # 4. 设置资金和佣金
            start_cash = 1000000.0
            cerebro.broker.set_cash(start_cash)
            cerebro.broker.setcommission(commission=0.001)
            
            # 5. 添加分析器
            cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe_ratio')
            cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
            cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
            
            self._log(f"  • 初始资金: {start_cash:,.2f}")
            self._log(f"  • 回测区间: {df.index[0].date()} 至 {df.index[-1].date()}")
            self._log(f"  • 策略模型: 双均线交叉 (SMA50/SMA200)")
            
            # 6. 运行回测
            results = cerebro.run()
            strat = results[0]
            
            # 7. 输出结果
            end_cash = cerebro.broker.getvalue()
            profit = end_cash - start_cash
            profit_pct = (profit / start_cash) * 100
            
            sharpe_info = strat.analyzers.sharpe_ratio.get_analysis()
            sharpe = sharpe_info.get('sharperatio', None)
            
            drawdown_info = strat.analyzers.drawdown.get_analysis()
            max_dd = drawdown_info.max.drawdown
            
            self._log("-" * 40)
            self._log(f"  ✅ 回测完成")
            self._log(f"  • 最终资金: {end_cash:,.2f}")
            self._log(f"  • 收益金额: {profit:,.2f}")
            
            if profit > 0:
                self._log(f"  • 收益率: +{profit_pct:.2f}% 🟢")
            else:
                self._log(f"  • 收益率: {profit_pct:.2f}% 🔴")
                
            self._log(f"  • 夏普比率: {sharpe:.2f}" if sharpe is not None else "  • 夏普比率: N/A")
            self._log(f"  • 最大回撤: {max_dd:.2f}%")
            
            # 简单的评价
            if profit_pct > 20 and max_dd < 15:
                self._log("\n  🏆 策略表现: 优秀")
            elif profit_pct > 0:
                self._log("\n  👌 策略表现: 良好")
            else:
                self._log("\n  ⚠️ 策略表现: 亏损")
                
            # 保存回测图表
            try:
                # 切换到非交互式后端，避免弹出窗口
                import matplotlib
                matplotlib.use('Agg')
                import matplotlib.pyplot as plt
                
                # backtrader plot with iplot=False to prevent popup
                figs = cerebro.plot(style='candlestick', barup='red', bardown='green', volume=False, iplot=False)
                if figs and figs[0] and figs[0][0]:
                    fig = figs[0][0]
                    fig.set_size_inches(16, 9)
                    fig.savefig(f"{self.output_dir}/99_回测结果.png", dpi=100)
                    plt.close(fig)
                    self._log(f"  ✓ 生成图表: 99_回测结果.png")
                else:
                    self._log(f"  ⚠ 回测图表生成失败: 无有效图形对象")
            except Exception as e:
                self._log(f"  ⚠ 无法生成回测图表: {e}")

        except Exception as e:
            self._log(f"  ⚠ 回测运行失败: {e}")
            import traceback
            traceback.print_exc()

    # ==================== 财报解读模块 ====================
    def analyze_financial_report(self):
        """功能2：财报深度解读"""
        self._log("\n" + "="*60)
        self._log(f"  【财报深度解读】{self.stock_name}")
        self._log("="*60)
        
        if self.financial_data is None:
            self._log("❌ 无财务数据")
            return
        
        df = self.financial_data.copy()
        latest = df.iloc[-1]
        report_date = latest['截止日期'].strftime('%Y-%m-%d')
        
        self._log(f"\n  📅 解读财报期: {report_date}")
        
        # 1. 核心业绩表现
        self._analyze_performance(df, latest)
        
        # 2. 现金流健康度
        self._analyze_cash_flow(df, latest)
        
        # 3. 资产负债结构
        self._analyze_balance_structure()
        
        # 4. 风险预警
        self._analyze_warnings(df, latest)
        
        # 5. 生成财报可视化
        self._plot_financial_report(df)
    
    def _analyze_performance(self, df, latest):
        """分析核心业绩"""
        self._log("\n📊 1. 核心业绩表现")
        self._log("-" * 40)
        
        rev_col = next((c for c in df.columns if '营业总收入' in c or '营业收入' in c), None)
        profit_col = '净利润' if '净利润' in df.columns else None
        deducted_col = next((c for c in df.columns if '扣非' in c and '净利' in c), None)
        gross_col = next((c for c in df.columns if '毛利率' in c), None)
        net_margin_col = next((c for c in df.columns if '净利率' in c), None)
        
        if rev_col:
            rev = self._safe_float(latest[rev_col])
            self._log(f"  • 营业收入: {self._format_number(rev)}")
        
        if profit_col:
            profit = self._safe_float(latest[profit_col])
            self._log(f"  • 净利润: {self._format_number(profit)}")
        
        if deducted_col:
            deducted = self._safe_float(latest[deducted_col])
            self._log(f"  • 扣非净利润: {self._format_number(deducted)}")
        
        # 同比分析
        prev_year = df[df['截止日期'] == (latest['截止日期'] - pd.DateOffset(years=1))]
        if not prev_year.empty and rev_col and profit_col:
            prev = prev_year.iloc[0]
            prev_rev = self._safe_float(prev[rev_col])
            prev_profit = self._safe_float(prev[profit_col])
            
            if prev_rev > 0:
                rev_yoy = (self._safe_float(latest[rev_col]) - prev_rev) / prev_rev
                self._log(f"  • 营收同比: {rev_yoy:+.1%}")
            
            if prev_profit > 0:
                profit_yoy = (self._safe_float(latest[profit_col]) - prev_profit) / prev_profit
                self._log(f"  • 净利同比: {profit_yoy:+.1%}")
                
                # 更合理的"增收不增利"判断
                if rev_yoy > 0.1 and profit_yoy < rev_yoy * 0.5:
                    self._log(f"  ⚠️ 增收不增利: 营收增速显著高于利润增速，关注成本控制")
                elif profit_yoy > rev_yoy * 1.5:
                    self._log(f"  ✅ 利润弹性: 利润增速快于营收，经营杠杆释放")
        
        # 毛利率净利率趋势
        if gross_col and net_margin_col:
            gross = self._safe_float(latest[gross_col])
            net_margin = self._safe_float(latest[net_margin_col])
            self._log(f"\n  • 毛利率: {gross:.1f}%")
            self._log(f"  • 净利率: {net_margin:.1f}%")
    
    def _analyze_cash_flow(self, df, latest):
        """分析现金流健康度"""
        self._log("\n💵 2. 现金流健康度")
        self._log("-" * 40)
        
        if self.cash_flow_data is None or len(self.cash_flow_data) == 0:
            self._log("  • 现金流数据缺失，尝试从财务摘要获取...")
            
            # 从财务摘要尝试获取
            cfo_col = next((c for c in df.columns if '经营' in c and '现金' in c and '净' in c), None)
            if cfo_col:
                cfo = self._safe_float(latest[cfo_col])
                profit_col = '净利润' if '净利润' in df.columns else None
                if profit_col:
                    net_profit = self._safe_float(latest[profit_col])
                    if net_profit != 0:
                        ratio = cfo / net_profit
                        self._log(f"  • 经营现金流: {self._format_number(cfo)}")
                        self._log(f"  • 净现比: {ratio:.2f}")
                        
                        if ratio > 1.2:
                            self._log(f"    → 盈利质量优秀，现金流充裕")
                        elif ratio > 0.8:
                            self._log(f"    → 盈利质量良好")
                        elif ratio > 0:
                            self._log(f"    → 盈利转化现金效率一般")
                        else:
                            self._log(f"    ⚠️ 经营现金流为负，需关注回款")
            return
        
        # 从现金流量表获取详细数据
        cf_latest = self.cash_flow_data.iloc[-1]
        
        cfo = self._safe_float(cf_latest.get('经营活动产生的现金流量净额'))
        cfi = self._safe_float(cf_latest.get('投资活动产生的现金流量净额'))
        cff = self._safe_float(cf_latest.get('筹资活动产生的现金流量净额'))
        
        self._log(f"  • 经营活动现金流: {self._format_number(cfo)}")
        self._log(f"  • 投资活动现金流: {self._format_number(cfi)}")
        self._log(f"  • 筹资活动现金流: {self._format_number(cff)}")
        
        # 现金流特征判断
        self._log(f"\n  📋 现金流特征:")
        if cfo > 0 and cfi < 0 and cff < 0:
            self._log(f"    → 「奶牛型」经营赚钱，投资扩张，还在还债/分红")
        elif cfo > 0 and cfi < 0 and cff > 0:
            self._log(f"    → 「扩张型」经营+融资都在投入")
        elif cfo < 0 and cfi > 0:
            self._log(f"    → 「收缩型」靠卖资产维持，需警惕")
        elif cfo < 0 and cff > 0:
            self._log(f"    → 「融资依赖型」靠借钱维持，风险较高")
        
        # 净现比
        profit_col = '净利润' if '净利润' in df.columns else None
        if profit_col:
            net_profit = self._safe_float(latest[profit_col])
            if net_profit > 0 and cfo != 0:
                ratio = cfo / net_profit
                self._log(f"\n  • 净现比: {ratio:.2f}")
    
    def _analyze_balance_structure(self):
        """分析资产负债结构"""
        self._log("\n🏦 3. 资产负债结构")
        self._log("-" * 40)
        
        if self.balance_sheet is None or len(self.balance_sheet) == 0:
            self._log("  • 资产负债表数据缺失")
            return
        
        bs = self.balance_sheet.iloc[-1]
        prev_bs = self.balance_sheet.iloc[-2] if len(self.balance_sheet) > 1 else None
        
        # 关键科目
        total_assets = self._safe_float(bs.get('资产总计'))
        total_liab = self._safe_float(bs.get('负债合计'))
        receivables = self._safe_float(bs.get('应收账款'))
        inventory = self._safe_float(bs.get('存货'))
        cash = self._safe_float(bs.get('货币资金'))
        
        if total_assets > 0:
            self._log(f"  • 总资产: {self._format_number(total_assets)}")
            self._log(f"  • 资产负债率: {total_liab/total_assets:.1%}")
            self._log(f"  • 货币资金: {self._format_number(cash)} ({cash/total_assets:.1%})")
            self._log(f"  • 应收账款: {self._format_number(receivables)} ({receivables/total_assets:.1%})")
            self._log(f"  • 存货: {self._format_number(inventory)} ({inventory/total_assets:.1%})")
        
        # 与上期对比
        if prev_bs is not None:
            prev_receivables = self._safe_float(prev_bs.get('应收账款'))
            prev_inventory = self._safe_float(prev_bs.get('存货'))
            
            if prev_receivables > 0:
                recv_change = (receivables - prev_receivables) / prev_receivables
                if recv_change > 0.3:
                    self._log(f"  ⚠️ 应收账款较上期增长 {recv_change:.1%}，关注回款风险")
            
            if prev_inventory > 0:
                inv_change = (inventory - prev_inventory) / prev_inventory
                if inv_change > 0.3:
                    self._log(f"  ⚠️ 存货较上期增长 {inv_change:.1%}，关注滞销风险")
    
    def _analyze_warnings(self, df, latest):
        """风险预警"""
        self._log("\n🚨 4. 风险预警信号")
        self._log("-" * 40)
        
        warnings = []
        
        # 1. 非经常性损益占比
        profit_col = '净利润' if '净利润' in df.columns else None
        deducted_col = next((c for c in df.columns if '扣非' in c and '净利' in c), None)
        
        if profit_col and deducted_col:
            net_profit = self._safe_float(latest[profit_col])
            deducted = self._safe_float(latest[deducted_col])
            
            if net_profit != 0:
                non_recurring_ratio = (net_profit - deducted) / abs(net_profit)
                if non_recurring_ratio > 0.5:
                    warnings.append(f"🔴 非经常性损益占比过高 ({non_recurring_ratio:.1%})，盈利质量存疑")
                elif non_recurring_ratio > 0.3:
                    warnings.append(f"🟠 非经常性损益占比较高 ({non_recurring_ratio:.1%})")
        
        # 2. 连续亏损检查
        if profit_col:
            recent_profits = df.tail(4)[profit_col].apply(self._safe_float)
            neg_count = (recent_profits < 0).sum()
            if neg_count >= 2:
                warnings.append(f"🔴 近4期中有{neg_count}期亏损")
        
        # 3. 毛利率大幅下滑
        gross_col = next((c for c in df.columns if '毛利率' in c), None)
        if gross_col and len(df) > 1:
            current_gross = self._safe_float(latest[gross_col])
            prev_gross = self._safe_float(df.iloc[-2][gross_col])
            if prev_gross > 0:
                gross_change = current_gross - prev_gross
                if gross_change < -5:
                    warnings.append(f"🟠 毛利率环比下滑 {gross_change:.1f}个百分点")
        
        # 输出
        if warnings:
            for w in warnings:
                self._log(f"  {w}")
        else:
            self._log("  ✅ 未发现明显风险信号")
        
        # 收集风险预警数据
        self.report_data['financial_warnings'] = warnings

    def _calculate_single_quarter_data(self, df):
        """
        将累计季报数据转换为单季度数据。
        - Q1: 单季度 = Q1累计
        - Q2: 单季度 = Q2累计 - Q1累计
        - Q3: 单季度 = Q3累计 - Q2累计
        - Q4: 单季度 = Q4(年报)累计 - Q3累计
        """
        if df is None or df.empty:
            return pd.DataFrame()

        df = df.copy()
        date_col = '截止日期'
        if date_col not in df.columns:
            return pd.DataFrame()
        
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(by=date_col).set_index(date_col)

        numeric_cols = df.select_dtypes(include=np.number).columns

        # 复制一份用于存储单季度数据
        df_sq = df.copy()
        
        # 获取所有存在的年份
        years = df.index.year.unique()
        
        for year in years:
            # 找到当年的季度报告日期
            q1_date = df[(df.index.year == year) & (df.index.month == 3)].index.max()
            q2_date = df[(df.index.year == year) & (df.index.month == 6)].index.max()
            q3_date = df[(df.index.year == year) & (df.index.month == 9)].index.max()
            q4_date = df[(df.index.year == year) & (df.index.month == 12)].index.max()
            
            # 计算单季度数据
            if pd.notna(q2_date) and pd.notna(q1_date):
                df_sq.loc[q2_date, numeric_cols] = df.loc[q2_date, numeric_cols] - df.loc[q1_date, numeric_cols]
            
            if pd.notna(q3_date) and pd.notna(q2_date):
                df_sq.loc[q3_date, numeric_cols] = df.loc[q3_date, numeric_cols] - df.loc[q2_date, numeric_cols]

            if pd.notna(q4_date) and pd.notna(q3_date):
                df_sq.loc[q4_date, numeric_cols] = df.loc[q4_date, numeric_cols] - df.loc[q3_date, numeric_cols]

        return df_sq.reset_index()

    def _calculate_ttm_series(self, df, col_name):
        """计算滚动(TTM)数据序列"""
        if df is None or col_name not in df.columns:
            return pd.Series()
        
        # 确保按日期排序
        date_col = '报告日' if '报告日' in df.columns else '截止日期'
        if date_col not in df.columns:
            return pd.Series()
            
        temp_df = df[[date_col, col_name]].copy().sort_values(date_col)
        temp_df[col_name] = temp_df[col_name].apply(self._safe_float)
        ttm_series = {}
        
        for idx, row in temp_df.iterrows():
            curr_date = row[date_col]
            curr_val = row[col_name]
            
            # 如果是年报(12月)，TTM就是当年值
            if curr_date.month == 12:
                ttm_series[curr_date] = curr_val
            else:
                # 查找上一年年报
                prev_year_end = pd.Timestamp(year=curr_date.year - 1, month=12, day=31)
                # 查找上一年同期
                prev_year_same = pd.Timestamp(year=curr_date.year - 1, month=curr_date.month, day=curr_date.day)
                # 尝试模糊匹配日期（月末）
                prev_annual = temp_df[temp_df[date_col].dt.year == curr_date.year - 1]
                prev_annual = prev_annual[prev_annual[date_col].dt.month == 12]
                
                prev_same = temp_df[temp_df[date_col].dt.year == curr_date.year - 1]
                prev_same = prev_same[prev_same[date_col].dt.month == curr_date.month]
                
                if not prev_annual.empty and not prev_same.empty:
                    val_annual = prev_annual.iloc[0][col_name]
                    val_same = prev_same.iloc[0][col_name]
                    ttm_val = curr_val + val_annual - val_same
                    ttm_series[curr_date] = ttm_val
                else:
                    ttm_series[curr_date] = np.nan # 无法计算
                    
        return pd.Series(ttm_series).sort_index()

    def _prepare_advanced_data(self):
        """准备高级分析所需的数据 (TTM, EVA, 估值)"""
        data = {}
        
        # 1. 基础TTM数据
        # 优先使用利润表/现金流量表，因为它们更详细
        inc_df = self.income_statement
        cf_df = self.cash_flow_data
        bs_df = self.balance_sheet
        abs_df = self.financial_data
        
        # 映射列名
        # 营收
        rev_col = next((c for c in inc_df.columns if '营业总收入' in c), None) if inc_df is not None else None
        if not rev_col and abs_df is not None: rev_col = next((c for c in abs_df.columns if '营业总收入' in c), None)
        
        # 净利润
        profit_col = next((c for c in inc_df.columns if '净利润' in c), None) if inc_df is not None else None
        
        # 研发费用
        rd_col = next((c for c in inc_df.columns if '研发费用' in c), None) if inc_df is not None else None
        
        # 现金流
        ocf_col = next((c for c in cf_df.columns if '经营' in c and '净额' in c), None) if cf_df is not None else None
        icf_col = next((c for c in cf_df.columns if '投资' in c and '净额' in c), None) if cf_df is not None else None
        cff_col = next((c for c in cf_df.columns if '筹资' in c and '净额' in c), None) if cf_df is not None else None  # CFF = Cash Flow from Financing (筹资现金流)
        ncf_col = next((c for c in cf_df.columns if '现金及现金等价物净增加额' in c), None) if cf_df is not None else None
        
        # 计算TTM序列
        data['ttm_rev'] = self._calculate_ttm_series(inc_df if inc_df is not None else abs_df, rev_col)
        data['ttm_profit'] = self._calculate_ttm_series(inc_df if inc_df is not None else abs_df, profit_col)
        data['ttm_rd'] = self._calculate_ttm_series(inc_df, rd_col)
        data['ttm_ocf'] = self._calculate_ttm_series(cf_df, ocf_col)
        data['ttm_icf'] = self._calculate_ttm_series(cf_df, icf_col)
        data['ttm_cff'] = self._calculate_ttm_series(cf_df, cff_col)  # 筹资活动现金流
        data['ttm_ncf'] = self._calculate_ttm_series(cf_df, ncf_col)
        
        # 2. EVA计算 (需要结合资产负债表 - 时点数，不需要TTM)
        # EVA = NOPAT - Capital * WACC
        # NOPAT = NetProfit + (Interest + R&D)*(1-TaxRate)
        # Capital = Equity + Debt - NonInterestLiab - CIP
        
        eva_series = {}
        if inc_df is not None and bs_df is not None:
            # 找到共同的日期
            common_dates = inc_df['报告日'].unique()
            
            for date in common_dates:
                try:
                    # 获取当期(TTM)的利润表数据
                    ttm_profit = data['ttm_profit'].get(date, 0)
                    ttm_rd = data['ttm_rd'].get(date, 0)
                    
                    # 获取当期(TTM)的利息和所得税
                    # 注意：利息费用在利润表中可能叫"利息费用"或"财务费用"下的利息支出
                    # 这里简化处理，尝试获取
                    int_col = next((c for c in inc_df.columns if '利息费用' in c), None)
                    tax_col = next((c for c in inc_df.columns if '所得税' in c), None)
                    total_profit_col = next((c for c in inc_df.columns if '利润总额' in c), None)
                    
                    ttm_int = self._calculate_ttm_series(inc_df, int_col).get(date, 0) if int_col else 0
                    ttm_tax = self._calculate_ttm_series(inc_df, tax_col).get(date, 0) if tax_col else 0
                    ttm_total_profit = self._calculate_ttm_series(inc_df, total_profit_col).get(date, 0) if total_profit_col else 0
                    
                    # 计算税率
                    tax_rate = ttm_tax / ttm_total_profit if ttm_total_profit > 0 else 0.15
                    tax_rate = max(0, min(tax_rate, 0.5)) # 限制在0-50%
                    
                    # NOPAT
                    nopat = ttm_profit + (ttm_int + ttm_rd) * (1 - tax_rate)
                    
                    # 获取资产负债表数据 (使用期末值)
                    bs_row = bs_df[bs_df['报告日'] == date]
                    if bs_row.empty: continue
                    bs_row = bs_row.iloc[0]
                    
                    # 优先使用归属于母公司的权益
                    equity_col = next((c for c in bs_df.columns if '归属于母公司' in c and '权益' in c), None)
                    if not equity_col:
                        equity_col = next((c for c in bs_df.columns if '所有者权益合计' in c or '股东权益合计' in c), '')
                    equity = self._safe_float(bs_row.get(equity_col, 0))
                    liab = self._safe_float(bs_row.get(next((c for c in bs_df.columns if '负债合计' in c), ''), 0))
                    cip = self._safe_float(bs_row.get(next((c for c in bs_df.columns if '在建工程' in c), ''), 0))
                    
                    # 无息流动负债
                    notes_pay = self._safe_float(bs_row.get(next((c for c in bs_df.columns if '应付票据' in c), ''), 0))
                    acct_pay = self._safe_float(bs_row.get(next((c for c in bs_df.columns if '应付账款' in c), ''), 0))
                    adv_pay = self._safe_float(bs_row.get(next((c for c in bs_df.columns if '预收' in c), ''), 0))
                    contract_liab = self._safe_float(bs_row.get(next((c for c in bs_df.columns if '合同负债' in c), ''), 0))
                    payroll = self._safe_float(bs_row.get(next((c for c in bs_df.columns if '应付职工' in c), ''), 0))
                    tax_pay = self._safe_float(bs_row.get(next((c for c in bs_df.columns if '应交税费' in c), ''), 0))
                    
                    non_int_liab = notes_pay + acct_pay + adv_pay + contract_liab + payroll + tax_pay
                    
                    # 调整后资本
                    invested_capital = equity + liab - non_int_liab - cip
                    
                    # WACC (假设8%)
                    wacc = 0.08
                    
                    eva = nopat - invested_capital * wacc
                    eva_series[date] = eva
                except:
                    pass
        
        data['eva'] = pd.Series(eva_series).sort_index()
        
        # 3. 历史估值数据 (日频)
        # 需要将财报数据(TTM)对齐到日频K线
        if self.stock_kline is not None and not data['ttm_profit'].empty:
            kline = self.stock_kline.copy()
            kline = kline.set_index('日期').sort_index()
            
            # 创建一个包含TTM数据的DataFrame，索引为报告日
            ttm_profit_df = pd.DataFrame({'ttm_profit': data['ttm_profit']})
            ttm_rev_df = pd.DataFrame({'ttm_rev': data['ttm_rev']})
            
            # 填充Equity (使用最新财报数据，非TTM)
            equity_series = {}
            if bs_df is not None:
                # 优先使用归属于母公司的权益
                eq_col = next((c for c in bs_df.columns if '归属于母公司' in c and '权益' in c), None)
                if not eq_col:
                    eq_col = next((c for c in bs_df.columns if '所有者权益合计' in c or '股东权益合计' in c), None)
                if eq_col:
                    for idx, row in bs_df.iterrows():
                        equity_series[row['报告日']] = self._safe_float(row[eq_col])
            equity_df = pd.DataFrame({'equity': pd.Series(equity_series)})
            
            # 分别合并每个TTM序列到日频
            full_df = kline.copy()
            
            # 合并 ttm_profit
            full_df = full_df.join(ttm_profit_df, how='left')
            full_df['ttm_profit'] = full_df['ttm_profit'].ffill()
            
            # 合并 ttm_rev
            full_df = full_df.join(ttm_rev_df, how='left')
            full_df['ttm_rev'] = full_df['ttm_rev'].ffill()
            
            # 合并 equity
            full_df = full_df.join(equity_df, how='left')
            full_df['equity'] = full_df['equity'].ffill()
            
            # 只保留有交易的日期
            full_df = full_df.dropna(subset=['收盘'])
            
            # 计算估值
            # 市值 = 收盘 * 总股本
            full_df['market_cap'] = full_df['收盘'] * self.total_shares
            
            # PE = 市值 / 净利润
            full_df['pe'] = full_df['market_cap'] / full_df['ttm_profit']
            
            # PB = 市值 / 净资产
            full_df['pb'] = full_df['market_cap'] / full_df['equity']
            
            # PS = 市值 / 营收
            full_df['ps'] = full_df['market_cap'] / full_df['ttm_rev']
            
            data['valuation_daily'] = full_df
            
        return data

    # ==================== 可视化模块 ====================
    def _plot_company_analysis(self, annual_df, df):
        """生成公司分析相关图表 (高级版)"""
        
        # 准备数据
        data = self._prepare_advanced_data()
        
        # 设置绘图风格
        sns.set_theme(style="whitegrid")
        # 字体设置
        import platform
        if platform.system() == 'Darwin':
            plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
        elif platform.system() == 'Windows':
            plt.rcParams['font.sans-serif'] = ['SimHei']
        else:
            plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei']
        plt.rcParams['axes.unicode_minus'] = False
        
        # ------------------------------------------------------
        # 图1: 滚动总营收（柱状图）+ 滚动净利润（折线图）
        # ------------------------------------------------------
        try:
            fig, ax1 = plt.subplots(figsize=(12, 6))
            
            # 转换为亿元
            dates = data['ttm_rev'].index
            revs_yi = data['ttm_rev'].values / 1e8
            profits_yi = data['ttm_profit'].reindex(dates).values / 1e8
            
            # 营收柱状图
            ax1.bar(dates, revs_yi, width=60, color='skyblue', label='滚动营收(TTM)', alpha=0.6)
            ax1.set_ylabel('营收 (亿元)', color='skyblue')
            ax1.tick_params(axis='y', labelcolor='skyblue')
            
            # 净利润折线图
            ax2 = ax1.twinx()
            ax2.plot(dates, profits_yi, color='orange', marker='o', linewidth=2, label='滚动净利润(TTM)')
            ax2.set_ylabel('净利润 (亿元)', color='orange')
            ax2.tick_params(axis='y', labelcolor='orange')
            
            plt.title(f'{self.stock_name} - 滚动营收与净利润趋势 (TTM)')
            
            # 合并图例
            lines, labels = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines + lines2, labels + labels2, loc='upper left')
            
            plt.tight_layout()
            plt.savefig(f"{self.output_dir}/00_营收利润滚动.png")
            plt.close()
            print(f"  ✓ 生成图表: 00_营收利润滚动.png")
        except Exception as e:
            print(f"  ⚠ 生成图表1失败: {e}")

        # ------------------------------------------------------
        # 图2: 滚动营收/现金流 + 净现比 (含金量指标)
        # ------------------------------------------------------
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
            
            # 限制10年数据
            cutoff_10y = pd.Timestamp.now() - pd.DateOffset(years=10)
            
            # 转换为亿元并过滤10年
            rev_yi = data['ttm_rev'] / 1e8
            rev_yi = rev_yi[rev_yi.index >= cutoff_10y]
            ocf_yi = data['ttm_ocf'] / 1e8
            ocf_yi = ocf_yi[ocf_yi.index >= cutoff_10y]
            profit_yi = data['ttm_profit'] / 1e8
            profit_yi = profit_yi[profit_yi.index >= cutoff_10y]
            
            # 上图：营收 vs 经营现金流
            ax1.plot(rev_yi.index, rev_yi.values, label='滚动营收', marker='o', linewidth=2)
            ax1.plot(ocf_yi.index, ocf_yi.values, label='滚动经营现金流', marker='s', linewidth=2)
            ax1.set_ylabel('金额 (亿元)')
            ax1.legend(loc='upper left')
            ax1.set_title(f'{self.stock_name} - 营收与经营现金流趋势 (TTM)')
            ax1.grid(True, alpha=0.3)
            
            # 下图：净现比 = 经营现金流 / 净利润
            common_idx = ocf_yi.index.intersection(profit_yi.index)
            net_cash_ratio = ocf_yi[common_idx] / profit_yi[common_idx]
            net_cash_ratio = net_cash_ratio.replace([np.inf, -np.inf], np.nan).dropna()
            
            if not net_cash_ratio.empty:
                colors = ['green' if x >= 1 else 'red' for x in net_cash_ratio.values]
                ax2.bar(net_cash_ratio.index, net_cash_ratio.values, width=60, color=colors, alpha=0.7)
                ax2.axhline(y=1.0, color='black', linestyle='--', linewidth=2, label='健康线 (=1)')
                ax2.set_ylabel('净现比')
                ax2.set_title('净现比 = 经营现金流 / 净利润 (>1表示利润含金量高)')
                ax2.legend(loc='upper left')
                ax2.grid(True, alpha=0.3)
                
                # 标注最新值
                latest_ratio = net_cash_ratio.iloc[-1]
                ax2.annotate(f'当前: {latest_ratio:.2f}', xy=(net_cash_ratio.index[-1], latest_ratio),
                            xytext=(5, 5), textcoords='offset points', fontsize=10, fontweight='bold',
                            color='green' if latest_ratio >= 1 else 'red')
            
            plt.tight_layout()
            plt.savefig(f"{self.output_dir}/01_营收现金流滚动.png")
            plt.close()
            print(f"  ✓ 生成图表: 01_营收现金流滚动.png")
        except Exception as e:
            print(f"  ⚠ 生成图表2失败: {e}")

        # ------------------------------------------------------
        # 图3: 滚动现金流净额 + 滚动各项现金流 (5年约20期)
        # ------------------------------------------------------
        try:
            fig, ax = plt.subplots(figsize=(14, 7))
            
            # 确保显示足够长的时间线 (近5年)
            cutoff_date = pd.Timestamp.now() - pd.DateOffset(years=5)
            
            # 辅助函数：过滤并排序，转换为亿元
            def filter_recent(series):
                filtered = series[series.index >= cutoff_date].sort_index()
                return filtered / 1e8  # 转换为亿元
            
            ncf = filter_recent(data['ttm_ncf'])
            ocf = filter_recent(data['ttm_ocf'])
            icf = filter_recent(data['ttm_icf'])
            cff = filter_recent(data['ttm_cff'])  # 筹资活动现金流 (Cash Flow from Financing)
            
            if not ncf.empty:
                # 绘制折线并添加数据点标记
                ax.plot(ocf.index, ocf.values, label='经营现金流', linewidth=2, marker='o', markersize=4, color='green')
                ax.plot(icf.index, icf.values, label='投资现金流', linewidth=2, marker='s', markersize=4, color='red')
                ax.plot(cff.index, cff.values, label='筹资现金流', linewidth=2, marker='^', markersize=4, color='purple')
                ax.plot(ncf.index, ncf.values, label='净现金流', linewidth=2.5, color='black', linestyle='--', marker='D', markersize=4)
                
                ax.set_ylabel('现金流 (亿元)')
                ax.set_title(f'{self.stock_name} - 现金流结构趋势 (TTM, 近5年约{len(ocf)}期)')
                ax.legend(loc='best')
                ax.axhline(y=0, color='gray', linestyle='-', alpha=0.5, linewidth=1)
                ax.grid(True, alpha=0.3)
                
                # 添加x轴日期格式化
                ax.xaxis.set_major_locator(plt.MaxNLocator(10))
                plt.xticks(rotation=45)
                
                plt.tight_layout()
                plt.savefig(f"{self.output_dir}/02_现金流结构滚动.png")
                plt.close()
                print(f"  ✓ 生成图表: 02_现金流结构滚动.png")
            else:
                print(f"  ⚠ 生成图表3失败: 数据不足")
        except Exception as e:
            print(f"  ⚠ 生成图表3失败: {e}")

        # ------------------------------------------------------
        # 图4: 股价走势（折线图）+ 季度营收（柱状图）- 10年视角
        # ------------------------------------------------------
        try:
            fig, ax1 = plt.subplots(figsize=(14, 6))

            # 获取滚动营收数据 (TTM)
            if 'ttm_rev' in data and not data['ttm_rev'].empty:
                # 营收柱状图
                ttm_rev = data['ttm_rev']
                
                # 限制10年数据
                cutoff_10y = pd.Timestamp.now() - pd.DateOffset(years=10)
                ttm_rev = ttm_rev[ttm_rev.index >= cutoff_10y]
                
                revs_yi = ttm_rev / 1e8 # 转换为亿元
                dates = ttm_rev.index

                ax1.bar(dates, revs_yi, width=60, color='lightgreen', label='滚动营收(TTM)', alpha=0.6)
                ax1.set_ylabel('营收 (亿元)', color='green')
                ax1.tick_params(axis='y', labelcolor='green')

                # 股价折线图
                if self.stock_kline is not None:
                    kline_df = self.stock_kline.copy()
                    ax2 = ax1.twinx()
                    
                    ax2.plot(kline_df['日期'], kline_df['收盘'], color='blue', linewidth=1.5, label='股价 (收盘价)')
                    ax2.set_ylabel('股价 (元)', color='blue')
                    ax2.tick_params(axis='y', labelcolor='blue')
                    
                    # 设置x轴范围为10年
                    min_date = max(cutoff_10y, min(dates.min(), kline_df['日期'].min()))
                    max_date = max(dates.max(), kline_df['日期'].max())
                    ax1.set_xlim(min_date, max_date)
                
                plt.title(f'{self.stock_name} - 股价与滚动营收趋势 (近10年)')
                
                # 合并图例
                lines, labels = ax1.get_legend_handles_labels()
                if self.stock_kline is not None:
                    lines2, labels2 = ax2.get_legend_handles_labels()
                    ax1.legend(lines + lines2, labels + labels2, loc='upper left')
                else:
                    ax1.legend(loc='upper left')
                
                ax1.grid(True, alpha=0.3)
                plt.tight_layout()
                plt.savefig(f"{self.output_dir}/03_市值营收滚动.png")
                plt.close()
                print(f"  ✓ 生成图表: 03_市值营收滚动.png")
            else:
                print(f"  ⚠ 生成图表3失败: 无滚动营收数据")

        except Exception as e:
            print(f"  ⚠ 生成图表4失败: {e}")

        # ------------------------------------------------------
        # 图5: 历史PE/PB/PS + 市值 (高低估曲线) + 分位点
        # ------------------------------------------------------
        try:
            if 'valuation_daily' in data:
                val_df = data['valuation_daily'].copy()
                
                fig, axes = plt.subplots(3, 1, figsize=(14, 18), sharex=True)
                
                indicators = [('pe', '市盈率(PE)'), ('pb', '市净率(PB)'), ('ps', '市销率(PS)')]
                percentile_info = []
                
                for i, (col, name) in enumerate(indicators):
                    ax = axes[i]
                    
                    if col not in val_df.columns:
                        continue
                    
                    # 过滤异常值 (如负值或极大值)
                    series = val_df[col].dropna()
                    
                    if series.empty:
                        continue
                    
                    # 简单过滤：只看正值且小于合理范围
                    q01 = series.quantile(0.01)
                    q99 = series.quantile(0.99)
                    series_clean = series[(series > max(0, q01)) & (series < q99 * 1.2)]
                    
                    if series_clean.empty:
                        continue
                    
                    mean = series_clean.mean()
                    std = series_clean.std()
                    
                    # 计算当前值的分位数
                    current_val = series_clean.iloc[-1]
                    percentile = (series_clean < current_val).sum() / len(series_clean) * 100
                    percentile_info.append(f"{name}: {current_val:.1f} ({percentile:.0f}%分位)")
                    
                    # 绘制估值线
                    ax.plot(series_clean.index, series_clean.values, label=name, color='blue', linewidth=1.5)
                    
                    # 绘制高低估区间
                    ax.axhline(mean, color='black', linestyle='--', label=f'平均值: {mean:.1f}')
                    ax.axhline(mean + std, color='red', linestyle=':', label=f'+1 STD: {mean+std:.1f}')
                    ax.axhline(mean - std, color='green', linestyle=':', label=f'-1 STD: {mean-std:.1f}')
                    ax.fill_between(series_clean.index, mean - std, mean + std, color='gray', alpha=0.1)
                    
                    # 标注当前值
                    ax.annotate(f'当前: {current_val:.1f}\n({percentile:.0f}%分位)', 
                                xy=(series_clean.index[-1], current_val),
                                xytext=(10, 0), textcoords='offset points',
                                fontsize=10, color='blue', fontweight='bold',
                                bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
                    
                    ax.set_ylabel(name, color='blue')
                    ax.tick_params(axis='y', labelcolor='blue')
                    ax.legend(loc='upper left')
                    ax.grid(True, alpha=0.3)
                    
                    # 副轴绘制市值 (柱状图)
                    if 'market_cap' in val_df.columns:
                        ax_mv = ax.twinx()
                        mv_series = val_df['market_cap'].dropna() / 1e8  # 转换为亿元
                        if not mv_series.empty:
                            mv_resampled = mv_series.resample('W').mean()
                            ax_mv.bar(mv_resampled.index, mv_resampled.values, width=5, color='orange', alpha=0.2, label='市值')
                            ax_mv.set_ylabel('市值 (亿元)', color='orange')
                            ax_mv.tick_params(axis='y', labelcolor='orange')
                            ax_mv.grid(False)
                
                # 在主标题中显示分位信息
                title = f'{self.stock_name} - 历史估值波段分析 (近10年)'
                subtitle = ' | '.join(percentile_info) if percentile_info else ''
                plt.suptitle(f"{title}\n{subtitle}", fontsize=14)
                plt.tight_layout()
                plt.savefig(f"{self.output_dir}/04_估值分析.png")
                plt.close()
                print(f"  ✓ 生成图表: 04_估值分析.png")
            else:
                print(f"  ⚠ 生成图表5失败: 无valuation_daily数据")
        except Exception as e:
            print(f"  ⚠ 生成图表5失败: {e}")

        # ------------------------------------------------------
        # 图6: 滚动研发投入（折线图）/ 滚动总营收（柱状图）
        # ------------------------------------------------------
        try:
            fig, ax1 = plt.subplots(figsize=(12, 6))
            
            # 限制10年数据
            cutoff_10y = pd.Timestamp.now() - pd.DateOffset(years=10)
            
            # 转换为亿元并过滤10年
            rev_yi = data['ttm_rev'] / 1e8
            rev_yi = rev_yi[rev_yi.index >= cutoff_10y]
            
            # 营收柱状图
            ax1.bar(rev_yi.index, rev_yi.values, width=60, color='#e0e0e0', label='滚动营收')
            ax1.set_ylabel('营收 (亿元)')
            
            # 研发投入折线图
            if not data['ttm_rd'].empty and data['ttm_rd'].sum() > 0:
                rd_yi = data['ttm_rd'] / 1e8
                rd_yi = rd_yi[rd_yi.index >= cutoff_10y]
                ax2 = ax1.twinx()
                ax2.plot(rd_yi.index, rd_yi.values, color='purple', marker='o', label='滚动研发投入')
                ax2.set_ylabel('研发投入 (亿元)', color='purple')
                
                # 稀疏标注：只标注最新值、最高值、最低值
                rd_ratio = data['ttm_rd'] / data['ttm_rev'] * 100
                valid_rd = rd_yi.dropna()
                if not valid_rd.empty:
                    # 最新值
                    latest_idx = valid_rd.index[-1]
                    latest_val = valid_rd.iloc[-1]
                    latest_ratio = rd_ratio.loc[latest_idx]
                    ax2.annotate(f'{latest_val:.1f}亿 ({latest_ratio:.1f}%)', xy=(latest_idx, latest_val),
                                xytext=(5, 5), textcoords='offset points', fontsize=9, color='purple', fontweight='bold')
                    
                    # 最高值
                    max_idx = valid_rd.idxmax()
                    max_val = valid_rd.max()
                    if max_idx != latest_idx:
                        max_ratio = rd_ratio.loc[max_idx]
                        ax2.annotate(f'高:{max_val:.1f}亿 ({max_ratio:.1f}%)', xy=(max_idx, max_val),
                                    xytext=(0, 8), textcoords='offset points', fontsize=8, color='red')
                    
                    # 最低值
                    min_idx = valid_rd.idxmin()
                    min_val = valid_rd.min()
                    if min_idx != latest_idx and min_idx != max_idx:
                        min_ratio = rd_ratio.loc[min_idx]
                        ax2.annotate(f'低:{min_val:.1f}亿 ({min_ratio:.1f}%)', xy=(min_idx, min_val),
                                    xytext=(0, -12), textcoords='offset points', fontsize=8, color='green')
            
            plt.title(f'{self.stock_name} - 研发投入趋势 (TTM滚动)')
            ax1.legend(loc='upper left')
            # 添加说明
            fig.text(0.99, 0.01, '注: TTM=最近四个季度滚动合计 | 数据来源: 利润表', 
                    fontsize=8, color='gray', ha='right', va='bottom')
            plt.tight_layout()
            plt.savefig(f"{self.output_dir}/05_研发投入滚动.png")
            plt.close()
            print(f"  ✓ 生成图表: 05_研发投入滚动.png")
        except Exception as e:
            print(f"  ⚠ 生成图表6失败: {e}")

        # ------------------------------------------------------
        # 图7: 利润率结构分析（毛利率 + 净利率 + 期间费用率）
        # ------------------------------------------------------
        try:
            inc_df = self.income_statement
            if inc_df is not None:
                # 获取各项数据
                cost_col = next((c for c in inc_df.columns if '营业成本' in c), None)
                profit_col = next((c for c in inc_df.columns if c == '净利润'), None)
                
                # 期间费用
                sale_exp_col = next((c for c in inc_df.columns if '销售费用' in c), None)
                admin_exp_col = next((c for c in inc_df.columns if '管理费用' in c), None)
                fin_exp_col = next((c for c in inc_df.columns if '财务费用' in c), None)
                rd_exp_col = next((c for c in inc_df.columns if '研发费用' in c), None)
                
                ttm_rev = data['ttm_rev']
                ttm_cost = self._calculate_ttm_series(inc_df, cost_col) if cost_col else pd.Series()
                ttm_profit = data['ttm_profit']
                
                # 计算各项TTM费用
                ttm_sale = self._calculate_ttm_series(inc_df, sale_exp_col) if sale_exp_col else pd.Series()
                ttm_admin = self._calculate_ttm_series(inc_df, admin_exp_col) if admin_exp_col else pd.Series()
                ttm_fin = self._calculate_ttm_series(inc_df, fin_exp_col) if fin_exp_col else pd.Series()
                ttm_rd = self._calculate_ttm_series(inc_df, rd_exp_col) if rd_exp_col else pd.Series()
                
                common_idx = ttm_rev.index.intersection(ttm_cost.index).intersection(ttm_profit.index)
                
                # 限制10年数据
                cutoff_10y = pd.Timestamp.now() - pd.DateOffset(years=10)
                common_idx = common_idx[common_idx >= cutoff_10y]
                
                if len(common_idx) > 0:
                    # 计算各项比率
                    gross_margin = (ttm_rev[common_idx] - ttm_cost[common_idx]) / ttm_rev[common_idx] * 100
                    net_margin = ttm_profit[common_idx] / ttm_rev[common_idx] * 100
                    
                    # 期间费用率
                    total_exp = pd.Series(0, index=common_idx)
                    for exp_series in [ttm_sale, ttm_admin, ttm_fin, ttm_rd]:
                        if not exp_series.empty:
                            total_exp = total_exp.add(exp_series.reindex(common_idx).fillna(0), fill_value=0)
                    exp_ratio = total_exp / ttm_rev[common_idx] * 100
                    
                    fig, ax = plt.subplots(figsize=(12, 6))
                    
                    ax.plot(gross_margin.index, gross_margin.values, marker='o', color='brown', 
                           label='毛利率', linewidth=2)
                    ax.plot(net_margin.index, net_margin.values, marker='s', color='blue', 
                           label='净利率', linewidth=2)
                    ax.plot(exp_ratio.index, exp_ratio.values, marker='^', color='gray', 
                           label='期间费用率', linewidth=2, linestyle='--')
                    
                    # 稀疏标注：只标注最新值
                    for series, name, color in [(gross_margin, '毛利率', 'brown'), 
                                                 (net_margin, '净利率', 'blue'),
                                                 (exp_ratio, '费用率', 'gray')]:
                        if not series.empty:
                            latest_val = series.iloc[-1]
                            ax.annotate(f'{latest_val:.1f}%', xy=(series.index[-1], latest_val),
                                       xytext=(5, 0), textcoords='offset points', 
                                       fontsize=10, color=color, fontweight='bold')
                    
                    ax.set_ylabel('比率 (%)')
                    ax.set_title(f'{self.stock_name} - 利润率结构分析 (TTM)')
                    ax.legend(loc='upper left')
                    ax.grid(True, alpha=0.3)
                    
                    plt.tight_layout()
                    plt.savefig(f"{self.output_dir}/06_利润率结构.png")
                    plt.close()
                    print(f"  ✓ 生成图表: 06_利润率结构.png")
        except Exception as e:
            print(f"  ⚠ 生成图表7失败: {e}")

        # ------------------------------------------------------
        # 图8: 滚动EVA + 自由现金流 (FCF)
        # ------------------------------------------------------
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
            
            # 限制10年数据
            cutoff_10y = pd.Timestamp.now() - pd.DateOffset(years=10)
            
            # 上图：EVA
            if not data['eva'].empty:
                eva_yi = data['eva'] / 1e8  # 转换为亿元
                eva_yi = eva_yi[eva_yi.index >= cutoff_10y]
                colors = ['red' if x < 0 else 'green' for x in eva_yi.values]
                
                ax1.bar(eva_yi.index, eva_yi.values, width=60, color=colors, alpha=0.7)
                ax1.plot(eva_yi.index, eva_yi.values, color='black', alpha=0.3, linestyle='--')
                ax1.axhline(y=0, color='black', linewidth=1)
                ax1.set_ylabel('EVA (亿元)')
                ax1.set_title(f'{self.stock_name} - 经济增加值 (EVA) 趋势')
                ax1.grid(True, alpha=0.3)
                
                # 标注最新值
                if not eva_yi.empty:
                    latest_eva = eva_yi.iloc[-1]
                    ax1.annotate(f'当前: {latest_eva:.1f}亿', xy=(eva_yi.index[-1], latest_eva),
                                xytext=(5, 5), textcoords='offset points', fontsize=10, fontweight='bold',
                                color='green' if latest_eva >= 0 else 'red')
            
            # 下图：自由现金流 FCF = 经营现金流 - 资本支出(CAPEX)
            # 从现金流量表获取资本支出
            cf_df = self.cash_flow_data
            capex_yi = pd.Series(dtype=float)
            if cf_df is not None:
                capex_col = next((c for c in cf_df.columns if '购建固定资产' in c or '购置固定资产' in c), None)
                if capex_col:
                    capex_yi = self._calculate_ttm_series(cf_df, capex_col) / 1e8
                    capex_yi = capex_yi[capex_yi.index >= cutoff_10y]
            
            ocf_yi = data['ttm_ocf'] / 1e8
            ocf_yi = ocf_yi[ocf_yi.index >= cutoff_10y]
            
            # FCF = 经营现金流 - 资本支出 (资本支出为正数)
            if not capex_yi.empty:
                common_idx = ocf_yi.index.intersection(capex_yi.index)
                fcf_yi = ocf_yi[common_idx] - capex_yi[common_idx].abs()  # 资本支出取绝对值
            else:
                # 备用方案：用投资现金流近似
                icf_yi = data['ttm_icf'] / 1e8
                icf_yi = icf_yi[icf_yi.index >= cutoff_10y]
                common_idx = ocf_yi.index.intersection(icf_yi.index)
                fcf_yi = ocf_yi[common_idx] + icf_yi[common_idx]
            
            if not fcf_yi.empty:
                colors = ['red' if x < 0 else 'blue' for x in fcf_yi.values]
                ax2.bar(fcf_yi.index, fcf_yi.values, width=60, color=colors, alpha=0.7)
                ax2.axhline(y=0, color='black', linewidth=1)
                ax2.set_ylabel('FCF (亿元)')
                ax2.set_title('自由现金流 (FCF = 经营现金流 - 资本支出)')
                ax2.grid(True, alpha=0.3)
                
                # 标注最新值
                latest_fcf = fcf_yi.iloc[-1]
                ax2.annotate(f'当前: {latest_fcf:.1f}亿', xy=(fcf_yi.index[-1], latest_fcf),
                            xytext=(5, 5), textcoords='offset points', fontsize=10, fontweight='bold',
                            color='blue' if latest_fcf >= 0 else 'red')
            
            plt.tight_layout()
            plt.savefig(f"{self.output_dir}/07_EVA与FCF.png")
            plt.close()
            print(f"  ✓ 生成图表: 07_EVA与FCF.png")
        except Exception as e:
            print(f"  ⚠ 生成图表8失败: {e}")

        # ------------------------------------------------------
        # 图9: 营运资本分析 (应收账款 vs 存货)
        # ------------------------------------------------------
        try:
            bs_df = self.balance_sheet
            if bs_df is not None:
                # 提取最近5年年报数据
                annual_bs = bs_df[bs_df['报告日'].dt.month == 12].sort_values('报告日').tail(5)
                
                if not annual_bs.empty:
                    dates = annual_bs['报告日'].dt.year.astype(str)
                    
                    # 获取应收和存货
                    rec_col = next((c for c in bs_df.columns if '应收账款' in c), None)
                    inv_col = next((c for c in bs_df.columns if '存货' in c), None)
                    
                    # 转换为亿元
                    rec_vals = annual_bs[rec_col].apply(self._safe_float).values / 1e8 if rec_col else np.zeros(len(dates))
                    inv_vals = annual_bs[inv_col].apply(self._safe_float).values / 1e8 if inv_col else np.zeros(len(dates))
                    
                    x = np.arange(len(dates))
                    width = 0.35
                    
                    fig, ax = plt.subplots(figsize=(10, 6))
                    rects1 = ax.bar(x - width/2, rec_vals, width, label='应收账款', color='skyblue')
                    rects2 = ax.bar(x + width/2, inv_vals, width, label='存货', color='orange')
                    
                    ax.set_ylabel('金额 (亿元)')
                    ax.set_title(f'{self.stock_name} - 营运资本结构 (应收 vs 存货)')
                    ax.set_xticks(x)
                    ax.set_xticklabels(dates)
                    ax.legend()
                    
                    # 自动标注数值
                    def autolabel(rects):
                        for rect in rects:
                            height = rect.get_height()
                            if height > 0:
                                ax.annotate(f'{height:.1f}亿',
                                            xy=(rect.get_x() + rect.get_width() / 2, height),
                                            xytext=(0, 3),  # 3 points vertical offset
                                            textcoords="offset points",
                                            ha='center', va='bottom', fontsize=8)
                    
                    autolabel(rects1)
                    autolabel(rects2)
                    
                    # 添加数据来源
                    ax.text(0.99, 0.01, '数据来源: 年报资产负债表', transform=ax.transAxes,
                            fontsize=8, color='gray', ha='right', va='bottom')
                    
                    plt.tight_layout()
                    plt.savefig(f"{self.output_dir}/08_营运资本结构.png")
                    plt.close()
                    print(f"  ✓ 生成图表: 08_营运资本结构.png")
        except Exception as e:
            print(f"  ⚠ 生成图表9失败: {e}")

        # ------------------------------------------------------
        # 图10: ROE杜邦分析拆解
        # ------------------------------------------------------
        try:
            # ROE = 净利率 * 总资产周转率 * 权益乘数
            # 净利率 = 净利润 / 营收
            # 总资产周转率 = 营收 / 平均总资产
            # 权益乘数 = 平均总资产 / 平均净资产
            
            # 使用TTM数据计算，限制10年
            cutoff_10y = pd.Timestamp.now() - pd.DateOffset(years=10)
            dates = data['ttm_profit'].index
            dates = dates[dates >= cutoff_10y]
            
            roe_decomp = []
            
            for date in dates:
                try:
                    # TTM数值
                    profit = data['ttm_profit'].get(date, 0)
                    rev = data['ttm_rev'].get(date, 0)
                    
                    # 资产负债表数值 (期末值近似平均值，或取期初期末平均)
                    # 这里简化取期末值
                    bs_row = bs_df[bs_df['报告日'] == date]
                    if bs_row.empty: continue
                    bs_row = bs_row.iloc[0]
                    
                    assets = self._safe_float(bs_row.get(next((c for c in bs_df.columns if '资产总计' in c), ''), 0))
                    # 优先使用归属于母公司的权益，其次是所有者权益合计
                    equity_col = next((c for c in bs_df.columns if '归属于母公司' in c and '权益' in c), None)
                    if not equity_col:
                        equity_col = next((c for c in bs_df.columns if '所有者权益合计' in c or '股东权益合计' in c), '')
                    equity = self._safe_float(bs_row.get(equity_col, 0))
                    
                    if rev > 0 and assets > 0 and equity > 0:
                        net_margin = profit / rev
                        asset_turnover = rev / assets
                        equity_multiplier = assets / equity
                        roe = net_margin * asset_turnover * equity_multiplier
                        
                        roe_decomp.append({
                            'date': date,
                            'net_margin': net_margin * 100, # %
                            'asset_turnover': asset_turnover, # 次
                            'equity_multiplier': equity_multiplier, # 倍
                            'roe': roe * 100 # %
                        })
                except:
                    pass
            
            if roe_decomp:
                roe_df = pd.DataFrame(roe_decomp).set_index('date').sort_index()
                
                fig, axes = plt.subplots(4, 1, figsize=(12, 14), sharex=True)
                ax1, ax2, ax3, ax4 = axes
                
                # 净利率
                ax1.plot(roe_df.index, roe_df['net_margin'], marker='o', color='red', label='销售净利率(%)')
                ax1.set_ylabel('净利率 (%)')
                ax1.legend(loc='upper left')
                ax1.grid(True)
                
                # 周转率
                ax2.plot(roe_df.index, roe_df['asset_turnover'], marker='s', color='blue', label='总资产周转率(次)')
                ax2.set_ylabel('周转率 (次)')
                ax2.legend(loc='upper left')
                ax2.grid(True)
                
                # 权益乘数
                ax3.plot(roe_df.index, roe_df['equity_multiplier'], marker='^', color='green', label='权益乘数(倍)')
                ax3.set_ylabel('权益乘数 (倍)')
                ax3.legend(loc='upper left')
                ax3.grid(True)

                # ROE走势
                ax4.plot(roe_df.index, roe_df['roe'], marker='o', color='black', label=f"ROE: {roe_df['roe'].iloc[-1]:.1f}%")
                ax4.axhline(y=10, color='gray', linestyle='--', linewidth=0.7, alpha=0.6)
                ax4.set_ylabel('ROE (%)')
                ax4.legend(loc='upper left')
                ax4.grid(True)
                ax4.set_ylim(0, max(roe_df['roe'].max()*1.2, 15))
                
                plt.suptitle(f'{self.stock_name} - ROE杜邦分析拆解 (TTM)', fontsize=16)
                plt.tight_layout()
                plt.savefig(f"{self.output_dir}/09_ROE杜邦分析.png")
                plt.close()
                print(f"  ✓ 生成图表: 09_ROE杜邦分析.png")
                
        except Exception as e:
            print(f"  ⚠ 生成图表09失败: {e}")

        # ------------------------------------------------------
        # 图11: 技术指标综合图 (MACD + KDJ + RSI)
        # ------------------------------------------------------
        try:
            if self.stock_kline is not None and len(self.stock_kline) > 120:
                kline = self.stock_kline.copy()
                kline = kline.set_index('日期').sort_index()
                # 取最近250个交易日
                kline = kline.tail(250)
                
                closes = kline['收盘']
                highs = kline['最高']
                lows = kline['最低']
                volumes = kline['成交量'] if '成交量' in kline.columns else None
                
                # 计算指标
                dif, dea, macd = self._calculate_macd(closes, fast=10, slow=20, signal=8)
                k, d, j = self._calculate_kdj(highs, lows, closes)
                rsi6 = self._calculate_rsi(closes, 6)
                rsi12 = self._calculate_rsi(closes, 12)
                rsi24 = self._calculate_rsi(closes, 24)
                
                fig, axes = plt.subplots(5, 1, figsize=(14, 14), sharex=True,
                                         gridspec_kw={'height_ratios': [2.6, 0.8, 1, 1, 1.1]})
                
                # 子图1: K线与均线 (包含MA120)
                ax1 = axes[0]
                ma5 = closes.rolling(5).mean()
                ma20 = closes.rolling(20).mean()
                ma60 = closes.rolling(60).mean()
                ma120 = closes.rolling(120).mean()
                boll_mid = ma20
                boll_std = closes.rolling(20).std()
                boll_upper = boll_mid + 2 * boll_std
                boll_lower = boll_mid - 2 * boll_std
                
                ax1.plot(closes.index, closes, label='收盘价', color='black', linewidth=1.2)
                ax1.plot(ma5.index, ma5, label='MA5', color='orange', linewidth=0.8)
                ax1.plot(ma20.index, ma20, label='MA20', color='blue', linewidth=0.8)
                ax1.plot(ma60.index, ma60, label='MA60', color='purple', linewidth=0.8)
                ax1.plot(ma120.index, ma120, label='MA120', color='red', linewidth=1, linestyle='--')
                ax1.plot(boll_upper.index, boll_upper, label='BOLL上轨', color='#8888ff', linewidth=0.9, linestyle='-')
                ax1.plot(boll_lower.index, boll_lower, label='BOLL下轨', color='#8888ff', linewidth=0.9, linestyle='-')
                ax1.fill_between(closes.index, boll_upper, boll_lower, color='#dfe8ff', alpha=0.4)
                
                # 标注最新价格和均线值
                latest_price = closes.iloc[-1]
                latest_ma20 = ma20.iloc[-1]
                latest_ma60 = ma60.iloc[-1]
                latest_ma120 = ma120.dropna().iloc[-1] if not ma120.dropna().empty else 0
                ax1.annotate(f'{latest_price:.2f}', xy=(closes.index[-1], latest_price),
                            xytext=(5, 0), textcoords='offset points', fontsize=9, fontweight='bold')
                
                ax1.set_ylabel('价格')
                # BOLL带宽分析（敞口/闭口）
                latest_mid = boll_mid.dropna().iloc[-1] if not boll_mid.dropna().empty else 0
                latest_bw = ((boll_upper - boll_lower) / boll_mid).dropna().iloc[-1] if not boll_mid.dropna().empty else 0
                boll_status = '敞口' if latest_bw >= 0.1 else '收口'
                
                # 价格金叉死叉 (MA5与MA20)
                ma5_arr = ma5.values
                ma20_arr = ma20.values
                dates_arr = ma5.index
                price_golden = []
                price_death = []
                for i in range(1, len(ma5_arr)):
                    if not np.isnan(ma5_arr[i]) and not np.isnan(ma20_arr[i]) and not np.isnan(ma5_arr[i-1]) and not np.isnan(ma20_arr[i-1]):
                        if ma5_arr[i-1] < ma20_arr[i-1] and ma5_arr[i] > ma20_arr[i]:
                            price_golden.append((dates_arr[i], ma5_arr[i]))
                        elif ma5_arr[i-1] > ma20_arr[i-1] and ma5_arr[i] < ma20_arr[i]:
                            price_death.append((dates_arr[i], ma5_arr[i]))
                
                for dt, val in price_golden[-2:]:
                    ax1.scatter(dt, val, marker='^', color='red', s=100, zorder=5)
                for dt, val in price_death[-2:]:
                    ax1.scatter(dt, val, marker='v', color='green', s=100, zorder=5)
                
                ax1.legend(loc='upper left', fontsize=8, ncol=5)
                ax1.set_title(f'{self.stock_name} - 技术指标综合分析 | 最新价:{latest_price:.2f} MA20:{latest_ma20:.2f} MA60:{latest_ma60:.2f} MA120:{latest_ma120:.2f} | BOLL带宽:{latest_bw:.1%}({boll_status})', fontsize=12)
                ax1.grid(True, alpha=0.3)
                
                # 子图2: 成交量
                ax_vol = axes[1]
                if volumes is not None:
                    colors_vol = ['red' if closes.iloc[i] >= closes.iloc[i-1] else 'green' 
                                  for i in range(1, len(closes))]
                    colors_vol = ['red'] + colors_vol
                    ax_vol.bar(volumes.index, volumes, color=colors_vol, alpha=0.5, width=1)
                    ax_vol.set_ylabel('VOL')
                    ax_vol.grid(True, alpha=0.3)
                
                # 子图3: MACD (10,20,8)
                ax2 = axes[2]
                colors = ['red' if m >= 0 else 'green' for m in macd]
                ax2.bar(macd.index, macd, color=colors, alpha=0.6, width=1)
                ax2.plot(dif.index, dif, label=f'DIF:{dif.iloc[-1]:.2f}', color='blue', linewidth=1)
                ax2.plot(dea.index, dea, label=f'DEA:{dea.iloc[-1]:.2f}', color='orange', linewidth=1)
                ax2.axhline(y=0, color='gray', linestyle='-', linewidth=0.5)
                
                # 标注金叉和死叉
                dif_arr = dif.values
                dea_arr = dea.values
                dates_arr = dif.index
                golden_crosses = []  # 金叉: DIF上穿DEA
                death_crosses = []   # 死叉: DIF下穿DEA
                for i in range(1, len(dif_arr)):
                    if not np.isnan(dif_arr[i]) and not np.isnan(dea_arr[i]):
                        if dif_arr[i-1] < dea_arr[i-1] and dif_arr[i] > dea_arr[i]:
                            golden_crosses.append((dates_arr[i], dif_arr[i]))
                        elif dif_arr[i-1] > dea_arr[i-1] and dif_arr[i] < dea_arr[i]:
                            death_crosses.append((dates_arr[i], dif_arr[i]))
                
                # 绘制金叉标记（红色向上三角）- 只显示最近2个
                for dt, val in golden_crosses[-2:]:
                    ax2.scatter(dt, val, marker='^', color='red', s=80, zorder=5)
                
                # 绘制死叉标记（绿色向下三角）- 只显示最近2个
                for dt, val in death_crosses[-2:]:
                    ax2.scatter(dt, val, marker='v', color='green', s=80, zorder=5)
                
                ax2.set_ylabel('MACD(10,20,8)')
                ax2.legend(loc='upper left', fontsize=8)
                ax2.grid(True, alpha=0.3)
                
                # 子图4: KDJ
                ax3 = axes[3]
                ax3.plot(k.index, k, label=f'K:{k.iloc[-1]:.1f}', color='blue', linewidth=1)
                ax3.plot(d.index, d, label=f'D:{d.iloc[-1]:.1f}', color='orange', linewidth=1)
                # J值截断到显示范围内
                j_display = j.clip(-10, 110)
                ax3.plot(j.index, j_display, label=f'J:{j.iloc[-1]:.1f}', color='purple', linewidth=1, alpha=0.7)
                ax3.axhline(y=80, color='red', linestyle='--', linewidth=0.5, alpha=0.7)
                ax3.axhline(y=20, color='green', linestyle='--', linewidth=0.5, alpha=0.7)
                
                # KDJ金叉死叉 (K与D) - 只标注最近2个
                k_arr = k.values
                d_arr = d.values
                kdj_dates = k.index
                kdj_golden = []
                kdj_death = []
                for i in range(1, len(k_arr)):
                    if not np.isnan(k_arr[i]) and not np.isnan(d_arr[i]):
                        if k_arr[i-1] < d_arr[i-1] and k_arr[i] > d_arr[i]:
                            kdj_golden.append((kdj_dates[i], k_arr[i]))
                        elif k_arr[i-1] > d_arr[i-1] and k_arr[i] < d_arr[i]:
                            kdj_death.append((kdj_dates[i], k_arr[i]))
                
                for dt, val in kdj_golden[-2:]:
                    ax3.scatter(dt, val, marker='^', color='red', s=60, zorder=5)
                for dt, val in kdj_death[-2:]:
                    ax3.scatter(dt, val, marker='v', color='green', s=60, zorder=5)
                
                ax3.set_ylabel('KDJ')
                ax3.set_ylim(-10, 110)
                ax3.legend(loc='upper left', fontsize=8)
                ax3.grid(True, alpha=0.3)
                
                # 子图5: RSI
                ax4 = axes[4]
                ax4.plot(rsi6.index, rsi6, label=f'RSI(6):{rsi6.iloc[-1]:.1f}', color='#ff7f50', linewidth=1)
                ax4.plot(rsi12.index, rsi12, label=f'RSI(12):{rsi12.iloc[-1]:.1f}', color='#9b59b6', linewidth=1)
                ax4.plot(rsi24.index, rsi24, label=f'RSI(24):{rsi24.iloc[-1]:.1f}', color='#2ecc71', linewidth=1)
                ax4.axhline(y=70, color='red', linestyle='--', linewidth=0.5, alpha=0.7)
                ax4.axhline(y=30, color='green', linestyle='--', linewidth=0.5, alpha=0.7)
                ax4.axhline(y=50, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
                
                # RSI金叉死叉 (RSI6与RSI12) - 只标注最近2个
                rsi6_arr = rsi6.values
                rsi12_arr = rsi12.values
                rsi_dates = rsi6.index
                rsi_golden = []
                rsi_death = []
                for i in range(1, len(rsi6_arr)):
                    if not np.isnan(rsi6_arr[i]) and not np.isnan(rsi12_arr[i]):
                        if rsi6_arr[i-1] < rsi12_arr[i-1] and rsi6_arr[i] > rsi12_arr[i]:
                            rsi_golden.append((rsi_dates[i], rsi6_arr[i]))
                        elif rsi6_arr[i-1] > rsi12_arr[i-1] and rsi6_arr[i] < rsi12_arr[i]:
                            rsi_death.append((rsi_dates[i], rsi6_arr[i]))
                
                for dt, val in rsi_golden[-2:]:
                    ax4.scatter(dt, val, marker='^', color='red', s=60, zorder=5)
                for dt, val in rsi_death[-2:]:
                    ax4.scatter(dt, val, marker='v', color='green', s=60, zorder=5)
                
                ax4.set_ylabel('RSI')
                ax4.set_ylim(0, 100)
                ax4.legend(loc='upper left', fontsize=8, ncol=3)
                ax4.grid(True, alpha=0.3)
                
                # 添加数据时间范围和图例说明
                start_date = closes.index[0].strftime('%Y-%m-%d')
                end_date = closes.index[-1].strftime('%Y-%m-%d')
                fig.text(0.99, 0.01, f'数据范围: {start_date} ~ {end_date} | ▲金叉(看涨) ▼死叉(看跌)',
                        fontsize=8, color='gray', ha='right', va='bottom')
                
                plt.tight_layout()
                plt.savefig(f"{self.output_dir}/10_技术指标.png")
                plt.close()
                print(f"  ✓ 生成图表: 10_技术指标.png")
        except Exception as e:
            print(f"  ⚠ 生成图表10失败: {e}")

        # ------------------------------------------------------
        # 图12: DCF估值模型
        # ------------------------------------------------------
        try:
            self._plot_dcf_valuation(data)
        except Exception as e:
            print(f"  ⚠ 生成图表12失败: {e}")

        # ------------------------------------------------------
        # 图19: 股东结构与变化
        # ------------------------------------------------------
        try:
            self._plot_shareholder_analysis()
        except Exception as e:
            print(f"  ⚠ 生成图表19失败: {e}")

        # ------------------------------------------------------
        # 图20: 运营效率分析
        # ------------------------------------------------------
        try:
            self._plot_operating_efficiency()
        except Exception as e:
            print(f"  ⚠ 生成图表20失败: {e}")

        # ------------------------------------------------------
        # 图21: 历史估值通道
        # ------------------------------------------------------
        try:
            self._plot_valuation_bands(data)
        except Exception as e:
            print(f"  ⚠ 生成图表21失败: {e}")

        # ------------------------------------------------------
        # 图22: 行业对标分析
        # ------------------------------------------------------
        try:
            self._plot_competitor_analysis()
        except Exception as e:
            print(f"  ⚠ 生成图表22失败: {e}")

        # ------------------------------------------------------
        # 图16-18: 财务概览相关图表 (独立调用，不依赖行业对标数据)
        # ------------------------------------------------------
        try:
            self._plot_financial_overview_charts()
        except Exception as e:
            print(f"  ⚠ 生成财务概览图表失败: {e}")

        # ------------------------------------------------------
        # 图13: DDM股利折现估值模型
        # ------------------------------------------------------
        try:
            self._plot_ddm_valuation()
        except Exception as e:
            print(f"  ⚠ 生成图表13失败: {e}")

        # ------------------------------------------------------
        # 图14: 股息率走势
        # ------------------------------------------------------
        try:
            self._plot_dividend_yield_trend()
        except Exception as e:
            print(f"  ⚠ 生成图表14失败: {e}")

        # ------------------------------------------------------
        # 图15: 财务费用走势
        # ------------------------------------------------------
        try:
            self._plot_financial_expense_trend()
        except Exception as e:
            print(f"  ⚠ 生成图表15失败: {e}")

    def _plot_shareholder_analysis(self):
        """生成股东分析图表"""
        if not self.shareholder_data or 'latest' not in self.shareholder_data:
            print("  ⚠ 无法生成股东分析图: 无数据")
            return

        df = self.shareholder_data['latest'].copy()
        dates = self.shareholder_data['dates']
        
        # 准备数据
        df = df.sort_values('持股数量', ascending=False).head(10)
        df['占总股本比例'] = pd.to_numeric(df['占总股本比例'], errors='coerce').fillna(0)
        
        fig = plt.figure(figsize=(16, 8))
        gs = fig.add_gridspec(1, 2, width_ratios=[1.2, 1.5])
        gs.update(wspace=0.3)

        # 子图1: 股权结构饼图
        ax1 = fig.add_subplot(gs[0])
        top_10_ratio = df['占总股本比例'].sum()
        other_ratio = 100 - top_10_ratio
        
        pie_data = df['占总股本比例'].tolist()
        pie_labels = [name[:12] + '...' if len(name) > 12 else name for name in df['股东名称']]
        
        # 如果 "其他" 占比大于一个很小的值，则加入饼图
        if other_ratio > 0.1:
            pie_data.append(other_ratio)
            pie_labels.append('其他流通股东')
            
        wedges, texts, autotexts = ax1.pie(pie_data, autopct='%1.1f%%',
                                           startangle=90, textprops={'fontsize': 9},
                                           pctdistance=0.85, radius=1.2)
        
        # 美化
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')

        ax1.legend(wedges, pie_labels, title="股东名称", loc="center", bbox_to_anchor=(0.5, -0.1), fontsize=8)
        ax1.set_title(f'十大流通股东持股结构\n(截至 {dates["latest"][:4]}-{dates["latest"][4:6]}-{dates["latest"][6:]})', fontsize=12, pad=20)


        # 子图2: 股东变化表格
        ax2 = fig.add_subplot(gs[1])
        ax2.axis('off')
        
        df_change = df[['股东名称', '占总股本比例', '较上期变化']].copy()
        
        cell_text = []
        row_colors = []

        for index, row in df_change.iterrows():
            change_val = row['较上期变化']
            if pd.isna(change_val) or abs(change_val) < 100: # 忽略微小变化
                change_str = '不变'
                color = 'gray'
            elif change_val > 0:
                change_str = f'↑ {change_val/1e4:,.1f}万'
                color = 'red'
            else:
                change_str = f'↓ {abs(change_val)/1e4:,.1f}万'
                color = 'green'
            
            cell_text.append([f" {row['股东名称']}", f"{row['占总股本比例']:.2f}% ", f" {change_str} "])
            row_colors.append(color)

        table = ax2.table(cellText=cell_text,
                          colLabels=['股东名称', '持股比例', f'较上期({dates["prev"][:4]}-{dates["prev"][4:6]})变化'],
                          loc='center',
                          cellLoc='left',
                          colWidths=[0.5, 0.2, 0.25])
        
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.5)

        # 设置表头和单元格样式
        for (i, j), cell in table.get_celld().items():
            if i == 0:
                cell.set_text_props(fontweight='bold', color='white')
                cell.set_facecolor('#40466e')
                cell.set_edgecolor('white')
            else:
                cell.set_edgecolor('white')
                if j == 2:
                    cell.get_text().set_color(row_colors[i-1])

        ax2.set_title('持股变化情况 (万股)', fontsize=12, pad=20)

        plt.suptitle(f'{self.stock_name} - 股东结构与变化分析', fontsize=16, fontweight='bold')
        plt.tight_layout(rect=[0, 0.05, 1, 0.96])
        plt.savefig(f'{self.output_dir}/19_股东结构与变化.png', dpi=300, bbox_inches='tight')
        plt.close()
        print('  ✓ 生成图表: 19_股东结构与变化.png')

    def _plot_operating_efficiency(self):
        """生成运营效率分析图表 (存货周转率 & 应收账款周转率)"""
        if self.income_statement is None or self.balance_sheet is None:
            print("  ⚠ 无法生成运营效率图: 缺少利润表或资产负债表数据")
            return

        # 数据准备
        inc = self.income_statement[self.income_statement['报告日'].dt.month == 12].sort_values('报告日')
        bs = self.balance_sheet[self.balance_sheet['报告日'].dt.month == 12].sort_values('报告日')

        # 找到公共年份
        common_years = sorted(list(set(inc['报告日'].dt.year) & set(bs['报告日'].dt.year)))
        if len(common_years) < 2:
            print("  ⚠ 运营效率分析: 年报数据不足两年")
            return
        
        inc = inc[inc['报告日'].dt.year.isin(common_years)].set_index('报告日')
        bs = bs[bs['报告日'].dt.year.isin(common_years)].set_index('报告日')

        # 获取列名
        cogs_col = next((c for c in inc.columns if '营业成本' in c), None)
        rev_col = next((c for c in inc.columns if '营业总收入' in c or '营业收入' in c), None)
        inv_col = next((c for c in bs.columns if '存货' in c), None)
        ar_col = next((c for c in bs.columns if '应收账款' in c), None)

        if not all([cogs_col, rev_col, inv_col, ar_col]):
            print("  ⚠ 运营效率分析: 缺少必要的财务列(成本/收入/存货/应收)")
            return

        results = []
        for i in range(1, len(common_years)):
            year = common_years[i]
            prev_year_date = pd.to_datetime(f'{year-1}-12-31')
            curr_year_date = pd.to_datetime(f'{year}-12-31')

            # 当年数据
            cogs = self._safe_float(inc.loc[curr_year_date, cogs_col])
            revenue = self._safe_float(inc.loc[curr_year_date, rev_col])
            
            # 平均存货/应收
            avg_inventory = (self._safe_float(bs.loc[curr_year_date, inv_col]) + self._safe_float(bs.loc[prev_year_date, inv_col])) / 2
            avg_ar = (self._safe_float(bs.loc[curr_year_date, ar_col]) + self._safe_float(bs.loc[prev_year_date, ar_col])) / 2

            inv_turnover = cogs / avg_inventory if avg_inventory > 0 else 0
            ar_turnover = revenue / avg_ar if avg_ar > 0 else 0
            
            results.append({
                'year': year,
                'inv_turnover': inv_turnover,
                'ar_turnover': ar_turnover,
            })

        if not results:
            print("  ⚠ 无法计算运营效率指标")
            return
            
        df = pd.DataFrame(results).set_index('year')

        # 绘图
        fig, axes = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
        fig.suptitle(f'{self.stock_name} - 运营效率分析', fontsize=16, fontweight='bold')
        
        # 子图1: 存货周转率
        ax1 = axes[0]
        ax1.plot(df.index, df['inv_turnover'], marker='o', color='purple', label='存货周转率(次/年)')
        ax1.set_ylabel('周转率 (次/年)')
        ax1.set_title('存货周转率 (越高越好)', fontsize=11)
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)
        # 标注数值
        for year, val in df['inv_turnover'].items():
            ax1.text(year, val, f'{val:.2f}', ha='center', va='bottom', fontsize=9)

        # 子图2: 应收账款周转率
        ax2 = axes[1]
        ax2.plot(df.index, df['ar_turnover'], marker='s', color='teal', label='应收账款周转率(次/年)')
        ax2.set_ylabel('周转率 (次/年)')
        ax2.set_title('应收账款周转率 (越高越好)', fontsize=11)
        ax2.legend(loc='upper left')
        ax2.grid(True, alpha=0.3)
        # 标注数值
        for year, val in df['ar_turnover'].items():
            ax2.text(year, val, f'{val:.2f}', ha='center', va='bottom', fontsize=9)

        ax2.set_xlabel('年份')
        ax2.xaxis.set_major_locator(plt.MaxNLocator(integer=True)) # 确保年份为整数
        
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        plt.savefig(f'{self.output_dir}/20_运营效率分析.png', dpi=300, bbox_inches='tight')
        plt.close()
        print('  ✓ 生成图表: 20_运营效率分析.png')

    def _plot_valuation_bands(self, data):
        """生成历史估值通道图 (PE/PB Bands)"""
        if 'valuation_daily' not in data or data['valuation_daily'].empty:
            print("  ⚠ 无法生成估值通道图: 缺少日度估值数据")
            return
        
        val_df = data['valuation_daily'].copy().tail(365 * 5) # 最近5年
        if val_df.empty:
            return

        fig, axes = plt.subplots(2, 1, figsize=(14, 12), sharex=True)
        fig.suptitle(f'{self.stock_name} - 历史估值通道 (PE & PB - Band)', fontsize=16, fontweight='bold')

        # 1. PE-Band
        ax1 = axes[0]
        pe_series = val_df['pe'].dropna()
        pe_series = pe_series[pe_series > 0] # 过滤负值
        q98 = pe_series.quantile(0.98) # 过滤极端高值
        pe_series = pe_series[pe_series < q98]
        
        if not pe_series.empty:
            pe_mean = pe_series.mean()
            pe_std = pe_series.std()
            
            # 计算TTM每股收益(EPS)
            ttm_eps = val_df['ttm_profit'] / self.total_shares
            
            # 计算估值通道价格
            price_pe_mean = ttm_eps * pe_mean
            price_pe_p1 = ttm_eps * (pe_mean + pe_std)
            price_pe_p2 = ttm_eps * (pe_mean + 2 * pe_std)
            price_pe_m1 = ttm_eps * (pe_mean - pe_std)

            # 绘图
            ax1.plot(val_df.index, val_df['收盘'], color='black', linewidth=1.5, label='收盘价')
            ax1.plot(val_df.index, price_pe_mean, color='blue', linestyle='--', label=f'PE均值({pe_mean:.1f}x)')
            ax1.plot(val_df.index, price_pe_p1, color='orange', linestyle=':', label=f'+1σ ({pe_mean+pe_std:.1f}x)')
            ax1.plot(val_df.index, price_pe_m1, color='green', linestyle=':', label=f'-1σ ({pe_mean-pe_std:.1f}x)')
            
            # 填充
            ax1.fill_between(val_df.index, price_pe_m1, price_pe_p1, color='blue', alpha=0.1)
            ax1.fill_between(val_df.index, price_pe_p1, price_pe_p2, color='orange', alpha=0.1)

            ax1.set_ylabel('股价 (元)')
            ax1.set_title('PE-Band (基于TTM每股收益)', fontsize=11)
            ax1.legend(loc='upper left')
            ax1.grid(True, alpha=0.3)
            ax1.set_ylim(bottom=0)

        # 2. PB-Band
        ax2 = axes[1]
        pb_series = val_df['pb'].dropna()
        pb_series = pb_series[pb_series > 0]
        q98_pb = pb_series.quantile(0.98)
        pb_series = pb_series[pb_series < q98_pb]

        if not pb_series.empty:
            pb_mean = pb_series.mean()
            pb_std = pb_series.std()

            # 计算每股净资产(BPS)
            bps = val_df['equity'] / self.total_shares
            
            # 计算估值通道价格
            price_pb_mean = bps * pb_mean
            price_pb_p1 = bps * (pb_mean + pb_std)
            price_pb_p2 = bps * (pb_mean + 2 * pb_std)
            price_pb_m1 = bps * (pb_mean - pb_std)

            # 绘图
            ax2.plot(val_df.index, val_df['收盘'], color='black', linewidth=1.5, label='收盘价')
            ax2.plot(val_df.index, price_pb_mean, color='darkviolet', linestyle='--', label=f'PB均值({pb_mean:.1f}x)')
            ax2.plot(val_df.index, price_pb_p1, color='tomato', linestyle=':', label=f'+1σ ({pb_mean+pb_std:.1f}x)')
            ax2.plot(val_df.index, price_pb_m1, color='limegreen', linestyle=':', label=f'-1σ ({pb_mean-pb_std:.1f}x)')

            # 填充
            ax2.fill_between(val_df.index, price_pb_m1, price_pb_p1, color='darkviolet', alpha=0.1)
            ax2.fill_between(val_df.index, price_pb_p1, price_pb_p2, color='tomato', alpha=0.1)
            
            ax2.set_xlabel('日期')
            ax2.set_ylabel('股价 (元)')
            ax2.set_title('PB-Band (基于每股净资产)', fontsize=11)
            ax2.legend(loc='upper left')
            ax2.grid(True, alpha=0.3)
            ax2.set_ylim(bottom=0)

        plt.tight_layout(rect=[0, 0, 1, 0.96])
        plt.savefig(f"{self.output_dir}/21_历史估值通道.png", dpi=300, bbox_inches='tight')
        plt.close()
        print('  ✓ 生成图表: 21_历史估值通道.png')

    def _plot_competitor_analysis(self):
        """生成行业对标分析雷达图"""
        # *********** 自动获取行业竞对 ***********
        competitor_codes = []
        try:
            if self.industry and self.industry != "未知":
                # 获取同行业对比数据 (排除自己)
                df_comp = industry_compare.get_industry_comparison(self.industry, self.stock_code)
                if df_comp is not None and not df_comp.empty:
                    # 排除自己
                    df_comp = df_comp[df_comp['代码'] != self.stock_code]
                    # 取前4个 (按成交额排序)
                    competitor_codes = df_comp.head(4)['代码'].astype(str).tolist()
                    print(f"  自动匹配同行业对比公司: {competitor_codes}")
        except Exception as e:
            print(f"  ⚠ 自动获取竞对失败: {e}")

        # 如果获取失败或为空，保留默认作为兜底
        if not competitor_codes:
            competitor_codes = ['601008', '601880', '603967'] 
        # ***********************************

        metrics_to_compare = {
            'PE(TTM)': {'lower_is_better': True},
            'PB': {'lower_is_better': True},
            '营收CAGR(3Y)': {'lower_is_better': False},
            '净利率': {'lower_is_better': False},
            'ROE': {'lower_is_better': False},
        }
        
        all_data = []

        # Helper function to get data for a single stock
        def get_stock_metrics(code):
            try:
                # 1. 获取公司名
                info = ak.stock_individual_info_em(symbol=code)
                name = info[info['item'] == '股票简称']['value'].values[0]

                # 2. 获取估值 - 使用 stock_zh_a_spot_em 获取实时PE/PB
                spot_df = ak.stock_zh_a_spot_em()
                stock_row = spot_df[spot_df['代码'] == code]
                if stock_row.empty:
                    raise ValueError(f"股票 {code} 不在A股实时行情中")
                pe = self._safe_float(stock_row['市盈率-动态'].iloc[0])
                pb = self._safe_float(stock_row['市净率'].iloc[0])

                # 3. 获取财务摘要 - 新格式处理
                fin_df = ak.stock_financial_abstract(symbol=code)
                # 新格式：列名是日期，行是指标
                # 找到年报日期列（以12月结尾的）
                date_cols = [c for c in fin_df.columns if c not in ['选项', '指标'] and str(c).endswith('1231')]
                if len(date_cols) < 1:
                    # 没有年报数据，使用默认值
                    net_margin, roe, cagr = 0, 0, 0
                else:
                    # 获取最新年报的净利率和ROE
                    latest_year_col = sorted(date_cols)[-1]
                    
                    # 查找净利率行
                    net_margin_row = fin_df[fin_df['指标'].str.contains('净利率', na=False)]
                    net_margin = self._safe_float(net_margin_row[latest_year_col].iloc[0]) if not net_margin_row.empty else 0
                    
                    # 查找ROE行  
                    roe_row = fin_df[fin_df['指标'].str.contains('净资产收益率', na=False)]
                    roe = self._safe_float(roe_row[latest_year_col].iloc[0]) if not roe_row.empty else 0
                    
                    # 计算3年营收CAGR
                    cagr = 0
                    if len(date_cols) >= 4:
                        sorted_years = sorted(date_cols)
                        rev_row = fin_df[fin_df['指标'].str.contains('营业总收入|营业收入', na=False, regex=True)]
                        if not rev_row.empty:
                            rev_start = self._safe_float(rev_row[sorted_years[-4]].iloc[0])
                            rev_end = self._safe_float(rev_row[sorted_years[-1]].iloc[0])
                            if rev_start > 0:
                                cagr = ((rev_end / rev_start) ** (1/3) - 1) * 100

                return {
                    'name': name,
                    'PE(TTM)': pe, 'PB': pb, '营收CAGR(3Y)': cagr, '净利率': net_margin, 'ROE': roe
                }
            except Exception as e:
                print(f"  ⚠ 获取对手 {code} 数据失败: {e}")
                return None

        print("\n  正在获取竞争对手数据...")
        # 获取主公司数据
        main_stock_data = get_stock_metrics(self.stock_code)
        if main_stock_data:
            all_data.append(main_stock_data)

        # 获取竞争对手数据
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(get_stock_metrics, code) for code in competitor_codes]
            for future in as_completed(futures):
                result = future.result()
                if result:
                    all_data.append(result)

        if len(all_data) < 2:
            print("  ⚠ 无法生成行业对标图: 有效数据不足2家")
            return

        # 数据归一化处理
        df = pd.DataFrame(all_data).set_index('name')
        df_normalized = df.copy()

        for metric, props in metrics_to_compare.items():
            min_val, max_val = df[metric].min(), df[metric].max()
            if max_val == min_val:
                df_normalized[metric] = 0.5 # Avoid division by zero
                continue
            
            # 归一化到0-1之间
            normalized_series = (df[metric] - min_val) / (max_val - min_val)
            if props['lower_is_better']:
                df_normalized[metric] = 1 - normalized_series
            else:
                df_normalized[metric] = normalized_series

        # 绘图
        labels = df_normalized.columns.tolist()
        num_vars = len(labels)
        
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
        angles += angles[:1] # 闭合

        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
        
        for i, row in df_normalized.iterrows():
            values = row.tolist()
            values += values[:1] # 闭合
            ax.plot(angles, values, 'o-', linewidth=2, label=i)
            ax.fill(angles, values, alpha=0.1)

        ax.set_thetagrids(np.degrees(angles[:-1]), labels)
        ax.set_title('行业对标分析', size=20, color='gray', y=1.1)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
        
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/22_行业对标分析.png", dpi=300, bbox_inches='tight')
        plt.close()
        print('  ✓ 生成图表: 22_行业对标分析.png')

    def _plot_financial_overview_charts(self):
        """生成财务概览相关图表 (图16: 销售费用, 图17: 供应商/客户集中度, 图18: 财务状况一览)"""
        
        # 图16: 销售费用走势
        try:
            self._plot_sales_expense_trend()
        except Exception as e:
            print(f"  ⚠ 生成图表16失败: {e}")

        # 图17: 供应商/客户集中度
        try:
            self._plot_supplier_customer_concentration()
        except Exception as e:
            print(f"  ⚠ 生成图表17失败: {e}")

        # 图18: 财务状况一览（资产/负债拆解）
        try:
            bs_df = self.balance_sheet
            if bs_df is not None and len(bs_df) > 0:
                latest_bs = bs_df.iloc[-1]
                as_of = latest_bs.get('报告日', pd.NaT)
                as_of_str = as_of.strftime('%Y-%m-%d') if isinstance(as_of, pd.Timestamp) else '最新'

                def sum_fields(fields):
                    total = 0
                    for col in fields:
                        if col in latest_bs:
                            total += self._safe_float(latest_bs[col])
                    return total / 1e8  # 亿元

                # 资产（蓝色）
                asset_items = {
                    '现金': ['货币资金'],
                    '应收款': ['应收账款', '应收票据', '应收款项融资'],
                    '预付款': ['预付款项'],
                    '存货': ['存货'],
                    '其他流动': ['其他流动资产'],
                    '长期投资': ['长期股权投资', '其他权益工具投资', '可供出售金融资产', '持有至到期投资', '其他非流动金融资产'],
                    '固定资产': ['固定资产净额', '固定资产'],
                    '无形资产&商誉': ['无形资产', '商誉'],
                    '其他固定资产': ['在建工程', '工程物资', '固定资产清理', '投资性房地产', '使用权资产', '长期待摊费用']
                }

                # 负债（红色）
                liab_items = {
                    '短期借款': ['短期借款'],
                    '应付款': ['应付账款', '应付票据', '应付账款及应付票据'],
                    '预收款': ['预收款项', '合同负债'],
                    '薪酬&税': ['应付职工薪酬', '应交税费'],
                    '其他流动负债': ['其他流动负债', '一年内到期的非流动负债'],
                    '长期借款': ['长期借款'],
                    '其他非流动负债': ['其他非流动负债', '长期应付款', '应付债券', '租赁负债']
                }

                names = list(asset_items.keys()) + list(liab_items.keys())
                values = [sum_fields(v) for v in asset_items.values()] + [sum_fields(v) for v in liab_items.values()]
                colors = ['#4a90e2'] * len(asset_items) + ['#e74c3c'] * len(liab_items)

                fig, ax = plt.subplots(figsize=(14, 6))
                x = np.arange(len(names))
                bars = ax.bar(x, values, color=colors, alpha=0.8)

                # 注记数值
                for bar in bars:
                    height = bar.get_height()
                    ax.annotate(f'{height:.1f}亿', xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3), textcoords='offset points', ha='center', va='bottom', fontsize=9)

                # 分割线 & 标签
                ax.axvline(len(asset_items) - 0.5, color='gray', linestyle='--', linewidth=1)
                ax.text(len(asset_items) / 2 - 0.5, max(values) * 1.05 if values else 0, '资产', ha='center', fontsize=11, color='#4a90e2')
                ax.text(len(asset_items) + len(liab_items) / 2 - 0.5, max(values) * 1.05 if values else 0, '负债', ha='center', fontsize=11, color='#e74c3c')

                ax.set_xticks(x)
                ax.set_xticklabels(names, rotation=30, ha='right', fontsize=9)
                ax.set_ylabel('金额 (亿元)')
                ax.set_title(f'{self.stock_name} - 财务状况一览 (报告期: {as_of_str[:7]})')
                ax.grid(True, axis='y', alpha=0.3)
                
                # 标注为0的项目
                for i, (bar, val) in enumerate(zip(bars, values)):
                    if val == 0 or val < 0.1:
                        ax.annotate('(无)', xy=(bar.get_x() + bar.get_width() / 2, 0.5),
                                   fontsize=7, color='gray', ha='center')
                
                # 添加数据来源
                ax.text(0.99, 0.01, '数据来源: 最新资产负债表', transform=ax.transAxes,
                        fontsize=8, color='gray', ha='right', va='bottom')

                plt.tight_layout()
                plt.savefig(f"{self.output_dir}/18_财务状况一览.png")
                plt.close()
                print(f"  ✓ 生成图表: 18_财务状况一览.png")
            else:
                print("  ⚠ 财务状况一览: 无资产负债表数据")
        except Exception as e:
            print(f"  ⚠ 生成图表18失败: {e}")

    def _plot_dcf_valuation(self, data):
        """DCF现金流折现估值模型"""
        # 获取必要数据
        if data['ttm_ocf'].empty or self.total_shares == 0:
            print(f"  ⚠ DCF估值: 数据不足")
            return
        
        # 获取最新TTM经营现金流
        latest_ocf = data['ttm_ocf'].iloc[-1]
        
        # 获取最新净利润 (TTM)
        latest_profit = data['ttm_profit'].iloc[-1] if not data['ttm_profit'].empty else 0
        
        # 计算历史增长率 (CAGR)
        if len(data['ttm_profit']) >= 4:
            profit_series = data['ttm_profit'].dropna()
            if len(profit_series) >= 4:
                years = len(profit_series) / 4  # 季度数转年
                start_val = profit_series.iloc[0]
                end_val = profit_series.iloc[-1]
                if start_val > 0 and end_val > 0:
                    cagr = (end_val / start_val) ** (1 / years) - 1
                else:
                    cagr = 0.10  # 默认10%
            else:
                cagr = 0.10
        else:
            cagr = 0.10
        
        # 限制增长率在合理范围
        cagr = max(0.03, min(cagr, 0.25))  # 3% ~ 25%
        
        # DCF参数
        discount_rate = 0.10  # 折现率 10%
        terminal_growth = 0.03  # 永续增长率 3%
        forecast_years = 10
        
        # 使用经营现金流作为FCF的近似 (更保守)
        base_fcf = latest_ocf * 0.7  # 假设70%可作为自由现金流
        
        # 预测未来现金流
        fcf_forecast = []
        cumulative_pv = 0
        
        for year in range(1, forecast_years + 1):
            if year <= 5:
                growth = cagr  # 前5年用历史增长率
            else:
                # 后5年线性递减到永续增长率
                growth = cagr - (cagr - terminal_growth) * (year - 5) / 5
            
            fcf = base_fcf * ((1 + growth) ** year)
            pv = fcf / ((1 + discount_rate) ** year)
            cumulative_pv += pv
            fcf_forecast.append({
                'year': year,
                'fcf': fcf / 1e8,  # 亿元
                'pv': pv / 1e8,
                'growth': growth * 100
            })
        
        # 终值 (Gordon Growth Model)
        terminal_fcf = fcf_forecast[-1]['fcf'] * 1e8 * (1 + terminal_growth)
        terminal_value = terminal_fcf / (discount_rate - terminal_growth)
        terminal_pv = terminal_value / ((1 + discount_rate) ** forecast_years)
        
        # 企业价值
        enterprise_value = cumulative_pv + terminal_pv
        
        # 股权价值 (简化：假设无净债务)
        equity_value = enterprise_value
        
        # 每股价值
        per_share_value = equity_value / self.total_shares
        
        # 当前股价
        current_price = self.current_valuation.get('price', 0)
        if current_price == 0 and self.stock_kline is not None:
            current_price = self.stock_kline['收盘'].iloc[-1]
        
        # 计算安全边际
        margin_of_safety = (per_share_value - current_price) / per_share_value * 100 if per_share_value > 0 else 0
        
        # 绘制图表
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # 子图1: 未来现金流预测
        ax1 = axes[0, 0]
        years = [f['year'] for f in fcf_forecast]
        fcfs = [f['fcf'] for f in fcf_forecast]
        pvs = [f['pv'] for f in fcf_forecast]
        
        ax1.bar(years, fcfs, color='lightblue', alpha=0.7, label='预测FCF')
        ax1.plot(years, pvs, color='red', marker='o', label='折现值(PV)')
        ax1.set_xlabel('预测年份')
        ax1.set_ylabel('金额 (亿元)')
        ax1.set_title('未来10年自由现金流预测')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 子图2: 增长率假设
        ax2 = axes[0, 1]
        growths = [f['growth'] for f in fcf_forecast]
        colors = ['green' if g > 10 else 'orange' if g > 5 else 'gray' for g in growths]
        bars2 = ax2.bar(years, growths, color=colors, alpha=0.7)
        ax2.axhline(y=terminal_growth * 100, color='red', linestyle='--', label=f'永续增长率 {terminal_growth*100:.1f}%')
        # 标注增长率数值
        for bar, g in zip(bars2, growths):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                    f'{g:.1f}%', ha='center', fontsize=7)
        ax2.set_xlabel('预测年份')
        ax2.set_ylabel('增长率 (%)')
        ax2.set_title(f'增长率假设 (前5年{cagr*100:.1f}%→永续{terminal_growth*100:.1f}%)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 子图3: 价值构成
        ax3 = axes[1, 0]
        labels = ['未来现金流现值', '终值现值']
        values = [cumulative_pv / 1e8, terminal_pv / 1e8]
        # 处理负值情况：饼图不能有负值
        if all(v > 0 for v in values):
            colors = ['steelblue', 'coral']
            wedges, texts, autotexts = ax3.pie(values, labels=labels, colors=colors, autopct='%1.1f%%',
                                                startangle=90, explode=(0.02, 0.02))
            ax3.set_title(f'DCF估值构成\n企业价值: {enterprise_value/1e8:.1f}亿')
        else:
            # 负现金流时显示柱状图替代饼图
            colors = ['steelblue' if v >= 0 else 'red' for v in values]
            bars = ax3.bar(labels, values, color=colors, alpha=0.7)
            ax3.axhline(y=0, color='black', linewidth=0.5)
            for bar, v in zip(bars, values):
                ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                        f'{v:.1f}亿', ha='center', va='bottom' if v >= 0 else 'top', fontsize=9)
            ax3.set_ylabel('金额 (亿元)')
            ax3.set_title(f'DCF估值构成\n⚠️ 存在负现金流，企业价值: {enterprise_value/1e8:.1f}亿')
            ax3.grid(True, alpha=0.3, axis='y')
        
        # 子图4: 估值结果
        ax4 = axes[1, 1]
        ax4.axis('off')
        
        result_text = f"""
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    📊 DCF估值结果 - {self.stock_name}
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    【关键假设】
    • 基准FCF: {base_fcf/1e8:.2f}亿
      (=TTM经营现金流{latest_ocf/1e8:.2f}亿 × 70%)
    • 前5年增长率: {cagr*100:.1f}%
    • 永续增长率: {terminal_growth*100:.1f}%
    • 折现率(WACC): {discount_rate*100:.1f}%
    
    【估值结果】
    • 未来现金流现值: {cumulative_pv/1e8:.1f}亿
    • 终值现值: {terminal_pv/1e8:.1f}亿
    • 企业价值: {enterprise_value/1e8:.1f}亿
    • 每股内在价值: ¥{per_share_value:.2f}
    
    【与市价比较】
    • 当前股价: ¥{current_price:.2f}
    • 安全边际: {margin_of_safety:.1f}%
    • 估值判断: {'低估 ✅' if margin_of_safety > 20 else '合理' if margin_of_safety > -10 else '高估 ⚠️'}
    
    ⚠️ 注: DCF对假设敏感，仅供参考
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        ax4.text(0.1, 0.5, result_text, transform=ax4.transAxes, fontsize=10,
                verticalalignment='center',
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
        
        plt.suptitle(f'{self.stock_name} - DCF现金流折现估值', fontsize=16)
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/11_DCF估值.png")
        plt.close()
        print(f"  ✓ 生成图表: 11_DCF估值.png")
        
        # 保存估值数据
        self.report_data['valuation']['dcf_per_share'] = round(per_share_value, 2)
        self.report_data['valuation']['dcf_margin_of_safety'] = round(margin_of_safety, 1)

    def _plot_ddm_valuation(self):
        """DDM股利折现估值模型 (适用于稳定分红公司)"""
        if self.dividend_data is None or len(self.dividend_data) == 0:
            print(f"  ⚠ DDM估值: 无分红数据")
            return
        
        if self.total_shares == 0:
            print(f"  ⚠ DDM估值: 无总股本数据")
            return
        
        # 获取历史分红数据
        div_df = self.dividend_data.copy()

        # 1) 识别日期列并排序（避免head/iloc取错顺序）
        date_col = None
        for c in ['除权除息日', '股权登记日', '实施公告日', '公告日期', '报告期', '日期']:
            if c in div_df.columns:
                date_col = c
                break
        if date_col is None:
            # 找一个包含“日/日期”的列兜底
            date_col = next((c for c in div_df.columns if ('日期' in str(c) or str(c).endswith('日'))), None)
        if date_col is not None:
            div_df[date_col] = pd.to_datetime(div_df[date_col], errors='coerce')
            div_df = div_df.dropna(subset=[date_col]).sort_values(date_col)

        # 2) 识别现金分红列：优先“派息”（每10股），否则尝试“每股/股利”列
        per_share_col = None
        per10_col = None
        if '派息' in div_df.columns:
            per10_col = '派息'
        else:
            per10_col = next((c for c in div_df.columns if ('每10股' in str(c) and ('派' in str(c) or '分红' in str(c) or '股利' in str(c)))), None)

        if per10_col is not None:
            div_df['每股分红'] = div_df[per10_col].apply(self._safe_float) / 10
            per_share_col = '每股分红'
        else:
            per_share_col = next((c for c in div_df.columns if ('每股' in str(c) and ('分红' in str(c) or '派息' in str(c) or '股利' in str(c)))), None)
            if per_share_col is None:
                print(f"  ⚠ DDM估值: 无法识别现金分红列")
                return

        div_df['dps'] = div_df[per_share_col].apply(self._safe_float)
        div_df = div_df[div_df['dps'] > 0]
        if div_df.empty:
            print(f"  ⚠ DDM估值: 无有效现金分红记录")
            return

        # 3) 汇总为“年度每股分红”（同一年多次分红要合并，否则会把单次派息当全年）
        if date_col is not None:
            div_df['year'] = div_df[date_col].dt.year
        else:
            # 没日期就退化为按出现顺序当作年度（不推荐）
            div_df['year'] = np.arange(len(div_df))

        annual_dps = div_df.groupby('year')['dps'].sum().sort_index()
        # 取最近5个完整年度（尽量排除当年未完结的分红）
        latest_year = int(annual_dps.index.max())
        current_year = datetime.now().year
        if latest_year == current_year and len(annual_dps) >= 2:
            annual_dps_used = annual_dps.iloc[-6:-1] if len(annual_dps) >= 6 else annual_dps.iloc[:-1]
        else:
            annual_dps_used = annual_dps.tail(5)

        annual_dps_used = annual_dps_used[annual_dps_used > 0]
        if len(annual_dps_used) < 2:
            print(f"  ⚠ DDM估值: 年度分红数据不足")
            return

        # 4) D0 取最近一个完整年度的年度每股分红
        d0 = float(annual_dps_used.iloc[-1])
        avg_div = float(annual_dps_used.mean())

        # 5) 增长率：用年度DPS的CAGR，更稳健，并对g做保守约束
        years_span = len(annual_dps_used) - 1
        oldest = float(annual_dps_used.iloc[0])
        newest = float(annual_dps_used.iloc[-1])
        if oldest > 0 and newest > 0 and years_span >= 1:
            div_growth = (newest / oldest) ** (1 / years_span) - 1
        else:
            div_growth = 0.03

        # DDM参数（保守默认）
        required_return = 0.10  # 要求回报率 10%
        terminal_growth = 0.03  # 永续增长率

        # g 约束：稳定分红公司通常不应长期>8%，且必须 < r
        div_growth = max(0.0, min(div_growth, 0.08))
        terminal_growth = min(terminal_growth, div_growth, required_return - 0.02)
        if terminal_growth < 0:
            terminal_growth = 0.0
        
        # 当前股价
        current_price = self.current_valuation.get('price', 0)
        if current_price == 0 and self.stock_kline is not None and len(self.stock_kline) > 0:
            current_price = self.stock_kline['收盘'].iloc[-1]

        # 当前股息率：用D0/Price
        current_yield = (d0 / current_price * 100) if current_price > 0 else 0
        
        # Gordon Growth Model: P = D1 / (r - g)
        # D1 = 下一年预期股利 = D0 * (1 + g)
        if required_return <= div_growth:
            # 避免出现爆炸估值（r-g趋近0）
            div_growth = max(0.0, required_return - 0.02)

        d1 = d0 * (1 + div_growth)
        ddm_value = d1 / (required_return - div_growth)

        # 两阶段DDM (前5年较快增长，之后永续增长)
        high_growth_rate = min(max(div_growth * 1.2, terminal_growth), 0.08)
        
        pv_high_growth = 0
        d = d0
        for year in range(1, 6):
            d = d * (1 + high_growth_rate)
            pv = d / ((1 + required_return) ** year)
            pv_high_growth += pv
        
        # 终值
        d_terminal = d * (1 + terminal_growth)
        terminal_value = d_terminal / (required_return - terminal_growth)
        pv_terminal = terminal_value / ((1 + required_return) ** 5)
        
        two_stage_value = pv_high_growth + pv_terminal
        
        # 安全边际
        margin_gordon = (ddm_value - current_price) / ddm_value * 100 if ddm_value > 0 else 0
        margin_two_stage = (two_stage_value - current_price) / two_stage_value * 100 if two_stage_value > 0 else 0
        
        # 绘制图表
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # 子图1: 年度每股分红趋势
        ax1 = axes[0, 0]
        years = annual_dps_used.index.astype(int).tolist()
        ax1.bar(years, annual_dps_used.values, color='green', alpha=0.7)
        ax1.set_xlabel('年份')
        ax1.set_ylabel('每股分红 (元)')
        ax1.set_title(f'年度每股分红 (近{len(annual_dps_used)}年)')
        ax1.grid(True, alpha=0.3)
        
        # 子图2: r/g 敏感性矩阵（用于解释估值偏离）
        ax2 = axes[0, 1]
        r_list = [0.09, 0.10, 0.11, 0.12]
        g_list = [0.01, 0.02, 0.03, 0.04]
        matrix = []
        for r in r_list:
            row = []
            for g in g_list:
                if g >= r - 0.005:
                    row.append(np.nan)
                else:
                    row.append((d0 * (1 + g)) / (r - g))
            matrix.append(row)
        mat = np.array(matrix)
        im = ax2.imshow(mat, aspect='auto', cmap='YlGnBu')
        ax2.set_xticks(range(len(g_list)))
        ax2.set_xticklabels([f"g={g*100:.0f}%" for g in g_list], fontsize=9)
        ax2.set_yticks(range(len(r_list)))
        ax2.set_yticklabels([f"r={r*100:.0f}%" for r in r_list], fontsize=9)
        ax2.set_title('Gordon模型敏感性 (基于D0年度分红)')
        for i in range(len(r_list)):
            for j in range(len(g_list)):
                val = mat[i, j]
                if np.isfinite(val):
                    ax2.text(j, i, f"{val:.1f}", ha='center', va='center', fontsize=8, color='black')
        fig.colorbar(im, ax=ax2, fraction=0.046, pad=0.04)
        
        # 子图3: 两种DDM估值对比
        ax3 = axes[1, 0]
        models = ['Gordon模型', '两阶段DDM', '当前股价']
        prices = [ddm_value, two_stage_value, current_price]
        colors = ['steelblue', 'coral', 'gray']
        bars = ax3.bar(models, prices, color=colors, alpha=0.7)
        ax3.set_ylabel('价格 (元)')
        ax3.set_title('DDM估值 vs 市价')
        for bar, val in zip(bars, prices):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(prices)*0.02,
                    f'{val:.2f}', ha='center', fontsize=10, fontweight='bold')
        # 如果估值远超市价，添加警示
        if ddm_value > current_price * 3 or two_stage_value > current_price * 3:
            ax3.text(0.5, 0.95, '⚠️ 模型估值偏离市价较大\n可能因为分红增长率假设过高',
                    transform=ax3.transAxes, ha='center', va='top', fontsize=9, color='red')
        ax3.grid(True, alpha=0.3)
        
        # 子图4: 估值结果
        ax4 = axes[1, 1]
        ax4.axis('off')
        
        result_text = f"""
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    📊 DDM估值结果 - {self.stock_name}
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    【分红数据】
    • 最近完整年度每股分红(D0): ¥{d0:.3f}
    • 近{len(annual_dps_used)}年平均年度分红: ¥{avg_div:.3f}
    • 年度分红增长率(CAGR): {div_growth*100:.1f}%
    • 当前股息率: {current_yield:.2f}%
    
    【模型假设】
    • 要求回报率: {required_return*100:.1f}%
    • 永续增长率: {terminal_growth*100:.1f}%
    
    【估值结果】
    • Gordon模型估值: ¥{ddm_value:.2f}
      安全边际: {margin_gordon:.1f}%
    • 两阶段DDM估值: ¥{two_stage_value:.2f}
      安全边际: {margin_two_stage:.1f}%
    • 当前股价: ¥{current_price:.2f}
    
    【投资建议】
    • {'股息率较高，适合价值投资 ✅' if current_yield > 3 else '股息率一般' if current_yield > 1.5 else '股息率偏低，不适合DDM ⚠️'}
    
    ⚠️ 口径说明: D0为“年度每股分红(同年多次分红已合并)”。
    ⚠️ DDM适用于稳定分红公司；若估值偏离大，请优先参考右上角敏感性矩阵。
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        ax4.text(0.1, 0.5, result_text, transform=ax4.transAxes, fontsize=10,
                verticalalignment='center',
                bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.3))
        
        plt.suptitle(f'{self.stock_name} - DDM股利折现估值', fontsize=16)
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/12_DDM估值.png")
        plt.close()
        print(f"  ✓ 生成图表: 12_DDM估值.png")
        
        # 保存估值数据
        self.report_data['valuation']['ddm_gordon'] = round(ddm_value, 2)
        self.report_data['valuation']['ddm_two_stage'] = round(two_stage_value, 2)
        self.report_data['valuation']['dividend_yield'] = round(current_yield, 2)
        self.report_data['valuation']['ddm_d0_annual'] = round(d0, 4)

    def _plot_dividend_yield_trend(self):
        """14_股息率走势图"""
        try:
            if self.dividend_data is None or len(self.dividend_data) == 0:
                print(f"  ⚠ 股息率走势: 无分红数据")
                return
            if self.stock_kline is None or len(self.stock_kline) == 0:
                print(f"  ⚠ 股息率走势: 无K线数据")
                return
            
            div_df = self.dividend_data.copy()
            
            # 识别日期列
            date_col = None
            for c in ['除权除息日', '股权登记日', '实施公告日', '公告日期', '报告期']:
                if c in div_df.columns:
                    date_col = c
                    break
            if date_col is None:
                print(f"  ⚠ 股息率走势: 无法识别日期列")
                return
            
            div_df[date_col] = pd.to_datetime(div_df[date_col], errors='coerce')
            div_df = div_df.dropna(subset=[date_col]).sort_values(date_col)
            
            # 识别派息列
            per10_col = '派息' if '派息' in div_df.columns else None
            if per10_col is None:
                per10_col = next((c for c in div_df.columns if '每10股' in str(c) and '派' in str(c)), None)
            
            if per10_col is not None:
                div_df['dps'] = div_df[per10_col].apply(self._safe_float) / 10
            else:
                per_share_col = next((c for c in div_df.columns if '每股' in str(c) and ('分红' in str(c) or '派息' in str(c))), None)
                if per_share_col:
                    div_df['dps'] = div_df[per_share_col].apply(self._safe_float)
                else:
                    print(f"  ⚠ 股息率走势: 无法识别分红列")
                    return
            
            div_df = div_df[div_df['dps'] > 0]
            div_df['year'] = div_df[date_col].dt.year
            annual_dps = div_df.groupby('year')['dps'].sum().sort_index()
            
            # 获取年末股价计算股息率
            kline = self.stock_kline.copy()
            kline['日期'] = pd.to_datetime(kline['日期'])
            kline['year'] = kline['日期'].dt.year
            year_end_prices = kline.groupby('year')['收盘'].last()
            
            # 合并计算股息率
            common_years = annual_dps.index.intersection(year_end_prices.index)
            if len(common_years) < 2:
                print(f"  ⚠ 股息率走势: 数据年份不足")
                return
            
            dividend_yields = []
            years_list = []
            for year in sorted(common_years):
                dps = annual_dps.get(year, 0)
                price = year_end_prices.get(year, 0)
                if price > 0:
                    dy = dps / price * 100
                    dividend_yields.append(dy)
                    years_list.append(year)
            
            if len(years_list) < 2:
                print(f"  ⚠ 股息率走势: 计算结果不足")
                return
            
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.bar(years_list, dividend_yields, color='green', alpha=0.7)
            ax.plot(years_list, dividend_yields, color='darkgreen', marker='o', linewidth=2)
            
            # 标注数值
            for x, y in zip(years_list, dividend_yields):
                ax.annotate(f'{y:.2f}%', xy=(x, y), xytext=(0, 5), textcoords='offset points',
                           ha='center', fontsize=9, fontweight='bold')
            
            ax.axhline(y=3, color='red', linestyle='--', alpha=0.5, label='3%参考线')
            ax.set_xlabel('年份')
            ax.set_ylabel('股息率 (%)')
            ax.set_title(f'{self.stock_name} - 历年股息率走势')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(f"{self.output_dir}/14_股息率走势.png")
            plt.close()
            print(f"  ✓ 生成图表: 14_股息率走势.png")
        except Exception as e:
            print(f"  ⚠ 股息率走势失败: {e}")

    def _plot_financial_expense_trend(self):
        """15_财务费用走势图"""
        try:
            inc_df = self.income_statement
            if inc_df is None or len(inc_df) == 0:
                print(f"  ⚠ 财务费用走势: 无利润表数据")
                return
            
            fin_col = next((c for c in inc_df.columns if '财务费用' in c), None)
            rev_col = next((c for c in inc_df.columns if '营业总收入' in c or '营业收入' in c), None)
            
            if fin_col is None:
                print(f"  ⚠ 财务费用走势: 无法识别财务费用列")
                return
            
            # 取年报数据
            inc_df = inc_df.copy()
            inc_df['报告日'] = pd.to_datetime(inc_df['报告日'], errors='coerce')
            annual = inc_df[inc_df['报告日'].dt.month == 12].sort_values('报告日').tail(8)
            
            if len(annual) < 2:
                print(f"  ⚠ 财务费用走势: 年报数据不足")
                return
            
            years = annual['报告日'].dt.year.tolist()
            fin_exp = annual[fin_col].apply(self._safe_float).values / 1e8
            
            fig, ax1 = plt.subplots(figsize=(12, 6))
            
            # 财务费用柱状图
            colors = ['red' if x > 0 else 'green' for x in fin_exp]
            bars = ax1.bar(years, fin_exp, color=colors, alpha=0.7, label='财务费用')
            ax1.set_ylabel('财务费用 (亿元)')
            ax1.axhline(y=0, color='black', linewidth=0.5)
            
            # 如果有营收，计算财务费用率
            if rev_col:
                rev = annual[rev_col].apply(self._safe_float).values / 1e8
                fin_rate = np.where(rev > 0, fin_exp / rev * 100, 0)
                ax2 = ax1.twinx()
                ax2.plot(years, fin_rate, color='blue', marker='s', linewidth=2, label='财务费用率')
                ax2.set_ylabel('财务费用率 (%)', color='blue')
                ax2.tick_params(axis='y', labelcolor='blue')
                # 标注费用率
                for x, y in zip(years, fin_rate):
                    ax2.annotate(f'{y:.1f}%', xy=(x, y), xytext=(0, 5), textcoords='offset points',
                               ha='center', fontsize=8, color='blue')
            
            ax1.set_xlabel('年份')
            ax1.set_title(f'{self.stock_name} - 财务费用走势 (正=费用支出, 负=利息收入)')
            ax1.legend(loc='upper left')
            ax1.grid(True, alpha=0.3)
            
            # 添加说明
            fig.text(0.99, 0.01, '注: 财务费用为负表示利息收入>利息支出', fontsize=8, color='gray', ha='right')
            
            plt.tight_layout()
            plt.savefig(f"{self.output_dir}/15_财务费用走势.png")
            plt.close()
            print(f"  ✓ 生成图表: 15_财务费用走势.png")
        except Exception as e:
            print(f"  ⚠ 财务费用走势失败: {e}")

    def _plot_sales_expense_trend(self):
        """16_销售费用走势图"""
        try:
            inc_df = self.income_statement
            if inc_df is None or len(inc_df) == 0:
                print(f"  ⚠ 销售费用走势: 无利润表数据")
                return
            
            sale_col = next((c for c in inc_df.columns if '销售费用' in c), None)
            rev_col = next((c for c in inc_df.columns if '营业总收入' in c or '营业收入' in c), None)
            
            if sale_col is None:
                print(f"  ⚠ 销售费用走势: 无法识别销售费用列")
                return
            
            # 取年报数据
            inc_df = inc_df.copy()
            inc_df['报告日'] = pd.to_datetime(inc_df['报告日'], errors='coerce')
            annual = inc_df[inc_df['报告日'].dt.month == 12].sort_values('报告日').tail(8)
            
            if len(annual) < 2:
                print(f"  ⚠ 销售费用走势: 年报数据不足")
                return
            
            years = annual['报告日'].dt.year.tolist()
            sale_exp = annual[sale_col].apply(self._safe_float).values / 1e8
            
            fig, ax1 = plt.subplots(figsize=(12, 6))
            
            # 销售费用柱状图
            bars = ax1.bar(years, sale_exp, color='#e74c3c', alpha=0.7, label='销售费用')
            ax1.set_ylabel('销售费用 (亿元)')
            
            # 标注金额
            for bar in bars:
                height = bar.get_height()
                ax1.annotate(f'{height:.1f}', xy=(bar.get_x() + bar.get_width()/2, height),
                            xytext=(0, 3), textcoords='offset points', ha='center', fontsize=9)
            
            # 如果有营收，计算销售费用率
            if rev_col:
                rev = annual[rev_col].apply(self._safe_float).values / 1e8
                sale_rate = np.where(rev > 0, sale_exp / rev * 100, 0)
                ax2 = ax1.twinx()
                ax2.plot(years, sale_rate, color='purple', marker='o', linewidth=2, label='销售费用率')
                ax2.set_ylabel('销售费用率 (%)', color='purple')
                ax2.tick_params(axis='y', labelcolor='purple')
                # 标注费用率
                for x, y in zip(years, sale_rate):
                    ax2.annotate(f'{y:.1f}%', xy=(x, y), xytext=(0, 5), textcoords='offset points',
                               ha='center', fontsize=8, color='purple')
            
            ax1.set_xlabel('年份')
            ax1.set_title(f'{self.stock_name} - 销售费用走势')
            ax1.legend(loc='upper left')
            ax1.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(f"{self.output_dir}/16_销售费用走势.png")
            plt.close()
            print(f"  ✓ 生成图表: 16_销售费用走势.png")
        except Exception as e:
            print(f"  ⚠ 销售费用走势失败: {e}")

    def _plot_supplier_customer_concentration(self):
        """17_供应商客户集中度图"""
        try:
            # 尝试从akshare获取前五大客户/供应商数据
            try:
                # 前五大客户
                customer_df = ak.stock_zyjs_ths(symbol=self.stock_code, indicator="客户")
                # 前五大供应商
                supplier_df = ak.stock_zyjs_ths(symbol=self.stock_code, indicator="供应商")
            except:
                customer_df = None
                supplier_df = None
            
            if (customer_df is None or len(customer_df) == 0) and (supplier_df is None or len(supplier_df) == 0):
                # 如果获取不到，尝试从年报数据构造提示
                print(f"  ⚠ 供应商客户集中度: 无法获取数据 (需年报披露)")
                return
            
            fig, axes = plt.subplots(1, 2, figsize=(14, 6))
            
            # 左图：客户集中度
            ax1 = axes[0]
            if customer_df is not None and len(customer_df) > 0:
                # 按年份取最新
                if '报告期' in customer_df.columns:
                    customer_df['报告期'] = pd.to_datetime(customer_df['报告期'], errors='coerce')
                    customer_df = customer_df.sort_values('报告期')
                
                # 找比例列
                ratio_col = next((c for c in customer_df.columns if '比例' in str(c) or '占比' in str(c)), None)
                if ratio_col:
                    # 按年份分组取前五合计
                    if '报告期' in customer_df.columns:
                        customer_df['year'] = customer_df['报告期'].dt.year
                        yearly = customer_df.groupby('year')[ratio_col].apply(
                            lambda x: x.apply(self._safe_float).head(5).sum()
                        ).tail(5)
                        ax1.bar(yearly.index.astype(str), yearly.values, color='#3498db', alpha=0.7)
                        ax1.set_ylabel('前五大客户占比 (%)')
                        for i, (x, y) in enumerate(zip(yearly.index.astype(str), yearly.values)):
                            ax1.annotate(f'{y:.1f}%', xy=(x, y), xytext=(0, 3), textcoords='offset points',
                                        ha='center', fontsize=9)
                    else:
                        # 只取最新一批
                        vals = customer_df[ratio_col].apply(self._safe_float).head(5)
                        ax1.bar(range(1, len(vals)+1), vals.values, color='#3498db', alpha=0.7)
                        ax1.set_xlabel('客户排名')
                        ax1.set_ylabel('占比 (%)')
            ax1.set_title('前五大客户集中度')
            ax1.grid(True, alpha=0.3)
            ax1.axhline(y=50, color='red', linestyle='--', alpha=0.5, label='50%警戒线')
            ax1.legend()
            
            # 右图：供应商集中度
            ax2 = axes[1]
            if supplier_df is not None and len(supplier_df) > 0:
                if '报告期' in supplier_df.columns:
                    supplier_df['报告期'] = pd.to_datetime(supplier_df['报告期'], errors='coerce')
                    supplier_df = supplier_df.sort_values('报告期')
                
                ratio_col = next((c for c in supplier_df.columns if '比例' in str(c) or '占比' in str(c)), None)
                if ratio_col:
                    if '报告期' in supplier_df.columns:
                        supplier_df['year'] = supplier_df['报告期'].dt.year
                        yearly = supplier_df.groupby('year')[ratio_col].apply(
                            lambda x: x.apply(self._safe_float).head(5).sum()
                        ).tail(5)
                        ax2.bar(yearly.index.astype(str), yearly.values, color='#e67e22', alpha=0.7)
                        ax2.set_ylabel('前五大供应商占比 (%)')
                        for i, (x, y) in enumerate(zip(yearly.index.astype(str), yearly.values)):
                            ax2.annotate(f'{y:.1f}%', xy=(x, y), xytext=(0, 3), textcoords='offset points',
                                        ha='center', fontsize=9)
                    else:
                        vals = supplier_df[ratio_col].apply(self._safe_float).head(5)
                        ax2.bar(range(1, len(vals)+1), vals.values, color='#e67e22', alpha=0.7)
                        ax2.set_xlabel('供应商排名')
                        ax2.set_ylabel('占比 (%)')
            ax2.set_title('前五大供应商集中度')
            ax2.grid(True, alpha=0.3)
            ax2.axhline(y=50, color='red', linestyle='--', alpha=0.5, label='50%警戒线')
            ax2.legend()
            
            plt.suptitle(f'{self.stock_name} - 供应商/客户集中度分析', fontsize=14)
            plt.tight_layout()
            plt.savefig(f"{self.output_dir}/17_供应商客户集中度.png")
            plt.close()
            print(f"  ✓ 生成图表: 17_供应商客户集中度.png")
        except Exception as e:
            print(f"  ⚠ 供应商客户集中度失败: {e}")

    def _plot_financial_report(self, df):
        """生成财报解读相关图表"""
        
        # 图5: 现金流结构图
        self._plot_cash_flow_structure()
        
        # 图6: 应收账款与存货趋势
        self._plot_working_capital()

    def analyze_comprehensive_trade_signal(self):
        """
        综合分析技术指标，提供更全面的交易信号参考。
        结合 趋势、动量、波动性 三个维度进行判断。
        免责声明: 此功能基于技术指标，仅供学习和参考，不构成任何投资建议。
        """
        if self.stock_kline is None or len(self.stock_kline) < 200:
            return {'signal': '未知', 'reason': '技术指标数据不足(需要至少200天数据)。', 'score': 0}

        df = self.stock_kline.copy().set_index('日期').sort_index().tail(250) # 分析最近约一年的数据
        
        # --- 1. 趋势分析 (Trend) ---
        closes = df['收盘']
        ma20 = closes.rolling(20).mean()
        ma60 = closes.rolling(60).mean()
        
        price = closes.iloc[-1]
        last_ma20 = ma20.iloc[-1]
        last_ma60 = ma60.iloc[-1]
        
        trend_score = 0
        trend_reasons = []
        if price > last_ma20 > last_ma60:
            trend_score = 100
            trend_reasons.append("价格处于MA20和MA60之上，呈多头排列，趋势强劲。")
        elif price > last_ma60:
            trend_score = 60
            trend_reasons.append("价格站上MA60(季线)，中期趋势向好。")
        elif price < last_ma20 < last_ma60:
            trend_score = 0
            trend_reasons.append("价格处于MA20和MA60之下，呈空头排列，趋势较弱。")
        else:
            trend_score = 40
            trend_reasons.append("价格在均线间震荡，趋势不明朗。")

        # --- 2. 动量分析 (Momentum) ---
        dif, dea, macd_hist = self._calculate_macd(closes, fast=10, slow=20, signal=8)
        k, d, j = self._calculate_kdj(df['最高'], df['最低'], closes)
        
        momentum_score = 50  # 中性分
        momentum_reasons = []
        
        # 检查最近3天的交叉情况
        macd_golden_cross = False
        kdj_golden_cross = False
        macd_death_cross = False
        kdj_death_cross = False
        
        for i in range(-3, 0):
            if dif.iloc[i-1] < dea.iloc[i-1] and dif.iloc[i] > dea.iloc[i]: macd_golden_cross = True
            if k.iloc[i-1] < d.iloc[i-1] and k.iloc[i] > d.iloc[i]: kdj_golden_cross = True
            if dif.iloc[i-1] > dea.iloc[i-1] and dif.iloc[i] < dea.iloc[i]: macd_death_cross = True
            if k.iloc[i-1] > d.iloc[i-1] and k.iloc[i] < d.iloc[i]: kdj_death_cross = True
        
        if macd_golden_cross and kdj_golden_cross:
            momentum_score = 100
            momentum_reasons.append("MACD与KDJ近期共振形成金叉，买入动能增强。")
        elif macd_golden_cross or kdj_golden_cross:
            momentum_score = 75
            momentum_reasons.append(f"{'MACD' if macd_golden_cross else 'KDJ'}出现金叉信号。")
        
        if macd_death_cross and kdj_death_cross:
            momentum_score = 0
            momentum_reasons.append("MACD与KDJ近期共振形成死叉，卖出动能增强。")
        elif macd_death_cross or kdj_death_cross:
            momentum_score = 25
            momentum_reasons.append(f"{'MACD' if macd_death_cross else 'KDJ'}出现死叉信号。")

        if not momentum_reasons:
            momentum_reasons.append("无明显金叉或死叉信号，动能中性。")

        # --- 3. 波动性/超买超卖 (Volatility) ---
        rsi = self._calculate_rsi(closes, 14)
        last_rsi = rsi.iloc[-1]
        
        volatility_score = 50 # 中性分
        volatility_reasons = []
        if last_rsi > 80:
            volatility_score = 0
            volatility_reasons.append(f"RSI({last_rsi:.1f})进入严重超买区，短期回调风险高。")
        elif last_rsi > 70:
            volatility_score = 25
            volatility_reasons.append(f"RSI({last_rsi:.1f})进入超买区，注意追高风险。")
        elif last_rsi < 20:
            volatility_score = 100
            volatility_reasons.append(f"RSI({last_rsi:.1f})进入严重超卖区，可能存在反弹机会。")
        elif last_rsi < 30:
            volatility_score = 75
            volatility_reasons.append(f"RSI({last_rsi:.1f})进入超卖区，下跌动能趋缓。")
        else:
            volatility_reasons.append(f"RSI({last_rsi:.1f})处于中性区域({30-70})。")

        # --- 综合评分与结论 ---
        # 权重: 趋势40%, 动量40%, 波动性20%
        final_score = trend_score * 0.4 + momentum_score * 0.4 + volatility_score * 0.2
        
        if final_score >= 80:
            signal = "强力买入"
        elif final_score >= 60:
            signal = "买入"
        elif final_score > 40:
            signal = "观望"
        elif final_score > 20:
            signal = "卖出"
        else:
            signal = "强力卖出"
            
        # 信号修正：在强势下跌趋势中，即使有金叉也应谨慎
        if trend_score < 30 and signal in ["强力买入", "买入"]:
            signal = "观望"
            trend_reasons.append("注意：尽管有买入信号，但整体趋势偏弱，建议谨慎观望。")

        all_reasons = trend_reasons + momentum_reasons + volatility_reasons
        
        return {
            'signal': signal,
            'reason': " ".join(all_reasons),
            'score': int(final_score),
            'details': {
                'trend': {'score': trend_score, 'reason': " ".join(trend_reasons)},
                'momentum': {'score': momentum_score, 'reason': " ".join(momentum_reasons)},
                'volatility': {'score': volatility_score, 'reason': " ".join(volatility_reasons)},
            }
        }
    
    def _plot_revenue_profit_trend(self, annual_df):
        """营收与净利润趋势图"""
        if annual_df.empty:
            return
        
        rev_col = next((c for c in annual_df.columns if '营业总收入' in c or '营业收入' in c), None)
        if not rev_col:
            return
        
        fig, ax1 = plt.subplots(figsize=(12, 6))
        
        years = annual_df['截止日期'].dt.year.astype(str)
        revenues = annual_df[rev_col].apply(self._safe_float) / 1e8
        profits = annual_df['净利润'].apply(self._safe_float) / 1e8
        
        # 营收柱状图
        bars = ax1.bar(years, revenues, color=COLORS['revenue'], alpha=0.8, label='营业收入')
        ax1.set_ylabel('营业收入 (亿元)', color=COLORS['revenue'], fontsize=11)
        ax1.tick_params(axis='y', labelcolor=COLORS['revenue'])
        
        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{height:.1f}', ha='center', va='bottom', fontsize=9, color=COLORS['dark'])
        
        # 净利润折线图
        ax2 = ax1.twinx()
        line = ax2.plot(years, profits, color=COLORS['profit'], marker='o', 
                       linewidth=2.5, markersize=8, label='净利润')
        ax2.set_ylabel('净利润 (亿元)', color=COLORS['profit'], fontsize=11)
        ax2.tick_params(axis='y', labelcolor=COLORS['profit'])
        
        # 净利润数值标签
        for i, (x, y) in enumerate(zip(years, profits)):
            ax2.text(x, y + profits.max()*0.03, f'{y:.1f}', 
                    ha='center', va='bottom', fontsize=9, color=COLORS['profit'], fontweight='bold')
        
        plt.title(f'{self.stock_name} ({self.stock_code}) - 营收与净利润趋势', 
                 fontsize=14, fontweight='bold', pad=20)
        
        # 合并图例
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', frameon=True)
        
        ax1.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/F1_营收利润趋势.png", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ 生成图表: F1_营收利润趋势.png")
    
    def _plot_margin_trend(self, df):
        """毛利率净利率趋势图"""
        gross_col = next((c for c in df.columns if '毛利率' in c), None)
        net_col = next((c for c in df.columns if '净利率' in c), None)
        
        if not gross_col or not net_col:
            return
        
        recent = df.tail(12)  # 最近12期
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        dates = recent['截止日期'].dt.strftime('%Y-%m')
        gross_margins = recent[gross_col].apply(self._safe_float)
        net_margins = recent[net_col].apply(self._safe_float)
        
        ax.plot(dates, gross_margins, marker='o', linewidth=2, markersize=6, 
               color=COLORS['primary'], label='毛利率')
        ax.plot(dates, net_margins, marker='s', linewidth=2, markersize=6, 
               color=COLORS['secondary'], label='净利率')
        
        ax.fill_between(dates, gross_margins, net_margins, alpha=0.2, color=COLORS['warning'])
        
        ax.set_ylabel('比率 (%)', fontsize=11)
        ax.set_xlabel('报告期', fontsize=11)
        plt.title(f'{self.stock_name} - 毛利率与净利率走势', fontsize=14, fontweight='bold')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/F2_利润率趋势.png", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ 生成图表: F2_利润率趋势.png")
    
    def _plot_score_radar(self):
        """综合评分雷达图"""
        categories = ['成长性', '盈利能力', '稳定性', '财务安全', '估值吸引力']
        values = [
            self.scores.get('growth', 50),
            self.scores.get('profitability', 50),
            self.scores.get('stability', 50),
            self.scores.get('safety', 50),
            self.scores.get('valuation', 50)
        ]
        
        # 闭合雷达图
        values += values[:1]
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        angles += angles[:1]
        
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        
        ax.plot(angles, values, 'o-', linewidth=2, color=COLORS['primary'])
        ax.fill(angles, values, alpha=0.25, color=COLORS['primary'])
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=12)
        ax.set_ylim(0, 100)
        
        # 添加分数标签
        for angle, value, cat in zip(angles[:-1], values[:-1], categories):
            ax.text(angle, value + 5, f'{value:.0f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # 综合评分
        avg_score = np.mean(values[:-1])
        plt.title(f'{self.stock_name} - 综合评分: {avg_score:.0f}/100', 
                 fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/F3_综合评分.png", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ 生成图表: F3_综合评分.png")
    
    def _plot_dupont_analysis(self, df):
        """ROE杜邦分析图"""
        # 需要: 净利率、总资产周转率、权益乘数
        net_margin_col = next((c for c in df.columns if '净利率' in c), None)
        roe_col = next((c for c in df.columns if '净资产收益率' in c), None)
        
        if not net_margin_col or not roe_col:
            return
        
        latest = df.iloc[-1]
        net_margin = self._safe_float(latest[net_margin_col])
        roe = self._safe_float(latest[roe_col])
        
        # 从资产负债表计算权益乘数和周转率
        if self.balance_sheet is not None and len(self.balance_sheet) > 0:
            bs = self.balance_sheet.iloc[-1]
            total_assets = self._safe_float(bs.get('资产总计'))
            # 优先使用归属于母公司的权益
            total_equity = self._safe_float(bs.get('归属于母公司股东权益合计')) or \
                           self._safe_float(bs.get('所有者权益合计')) or \
                           self._safe_float(bs.get('股东权益合计'))
            
            if total_equity > 0:
                equity_multiplier = total_assets / total_equity
                
                # 反推周转率: ROE = 净利率 * 周转率 * 权益乘数
                if net_margin > 0 and equity_multiplier > 0:
                    turnover = roe / (net_margin * equity_multiplier) * 100
                    
                    # 绘制杜邦分析图
                    fig, ax = plt.subplots(figsize=(10, 6))
                    
                    components = ['净利率', '总资产周转率', '权益乘数', 'ROE']
                    values = [net_margin, turnover, equity_multiplier, roe]
                    colors = [COLORS['primary'], COLORS['secondary'], COLORS['warning'], COLORS['success']]
                    
                    bars = ax.barh(components, values, color=colors, height=0.5)
                    
                    # 添加数值标签
                    for bar, val, comp in zip(bars, values, components):
                        if comp in ['净利率', 'ROE']:
                            label = f'{val:.1f}%'
                        elif comp == '总资产周转率':
                            label = f'{val:.2f}次'
                        else:
                            label = f'{val:.2f}倍'
                        ax.text(val + 0.5, bar.get_y() + bar.get_height()/2, label,
                               va='center', fontsize=11, fontweight='bold')
                    
                    ax.set_xlabel('数值', fontsize=11)
                    ax.set_title(f'{self.stock_name} - ROE杜邦分析 (ROE = 净利率 × 周转率 × 杠杆)',
                               fontsize=14, fontweight='bold')
                    ax.grid(True, alpha=0.3, axis='x')
                    
                    plt.tight_layout()
                    plt.savefig(f"{self.output_dir}/F4_杜邦分析.png", dpi=300, bbox_inches='tight')
                    plt.close()
                    print(f"  ✓ 生成图表: F4_杜邦分析.png")
    
    def _plot_cash_flow_structure(self):
        """现金流结构图"""
        if self.cash_flow_data is None or len(self.cash_flow_data) == 0:
            return
        
        # 获取最近4期
        recent = self.cash_flow_data.tail(4)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        dates = recent['报告日'].dt.strftime('%Y-%m')
        
        # 容错处理列名
        cfo_col = next((c for c in recent.columns if '经营' in c and '净额' in c), None)
        cfi_col = next((c for c in recent.columns if '投资' in c and '净额' in c), None)
        cff_col = next((c for c in recent.columns if '筹资' in c and '净额' in c), None)
        
        cfo = recent[cfo_col].apply(self._safe_float) / 1e8 if cfo_col else pd.Series([0]*len(recent))
        cfi = recent[cfi_col].apply(self._safe_float) / 1e8 if cfi_col else pd.Series([0]*len(recent))
        cff = recent[cff_col].apply(self._safe_float) / 1e8 if cff_col else pd.Series([0]*len(recent))
        
        x = np.arange(len(dates))
        width = 0.25
        
        ax.bar(x - width, cfo, width, label='经营活动', color=COLORS['success'])
        ax.bar(x, cfi, width, label='投资活动', color=COLORS['primary'])
        ax.bar(x + width, cff, width, label='筹资活动', color=COLORS['secondary'])
        
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax.set_ylabel('现金流净额 (亿元)', fontsize=11)
        ax.set_xticks(x)
        ax.set_xticklabels(dates)
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.title(f'{self.stock_name} - 现金流结构', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/F5_现金流结构.png", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ 生成图表: F5_现金流结构.png")
    
    def _plot_working_capital(self):
        """营运资本趋势图（应收+存货）"""
        if self.balance_sheet is None or len(self.balance_sheet) < 4:
            return
        
        recent = self.balance_sheet.tail(8)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        dates = recent['报告日'].dt.strftime('%Y-%m')
        receivables = recent['应收账款'].apply(self._safe_float) / 1e8
        inventory = recent['存货'].apply(self._safe_float) / 1e8
        
        ax.bar(dates, receivables, label='应收账款', color=COLORS['warning'], alpha=0.8)
        ax.bar(dates, inventory, bottom=receivables, label='存货', color=COLORS['info'], alpha=0.8)
        
        ax.set_ylabel('金额 (亿元)', fontsize=11)
        ax.set_xlabel('报告期', fontsize=11)
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        plt.xticks(rotation=45)
        
        plt.title(f'{self.stock_name} - 应收账款与存货趋势', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/F6_营运资本.png", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  ✓ 生成图表: F6_营运资本.png")
    
    # ==================== Dashboard合并图表 ====================
    def _generate_dashboard_charts(self):
        """生成合并的Dashboard图表，方便整体查看"""
        self._generate_fundamental_dashboard()
        self._generate_valuation_dashboard()
        self._generate_expense_dashboard()
    
    def _generate_fundamental_dashboard(self):
        """基本面概览Dashboard (2x2): 营收利润、利润率、现金流、ROE"""
        try:
            fig, axes = plt.subplots(2, 2, figsize=(16, 12))
            fig.suptitle(f'{self.stock_name} - 基本面概览 Dashboard', fontsize=16, fontweight='bold', y=0.98)
            
            # 准备数据
            inc_df = self.income_statement
            cf_df = self.cash_flow_data
            fin_df = self.financial_data
            
            if fin_df is None:
                plt.close()
                return
            
            # === 子图1: 营收与净利润趋势 ===
            ax1 = axes[0, 0]
            annual_df = fin_df[fin_df['截止日期'].dt.month == 12].tail(6)
            if len(annual_df) >= 2:
                rev_col = next((c for c in annual_df.columns if '营业总收入' in c), None)
                profit_col = '净利润' if '净利润' in annual_df.columns else None
                
                if rev_col and profit_col:
                    years = annual_df['截止日期'].dt.year.astype(str)
                    rev = annual_df[rev_col].apply(self._safe_float) / 1e8
                    profit = annual_df[profit_col].apply(self._safe_float) / 1e8
                    
                    x = np.arange(len(years))
                    width = 0.35
                    ax1.bar(x - width/2, rev, width, label='营收', color=COLORS['revenue'], alpha=0.8)
                    ax1.bar(x + width/2, profit, width, label='净利润', color=COLORS['profit'], alpha=0.8)
                    ax1.set_xticks(x)
                    ax1.set_xticklabels(years)
                    ax1.set_ylabel('亿元')
                    ax1.legend(loc='upper left')
                    ax1.set_title('年度营收与净利润', fontsize=11, fontweight='bold')
                    ax1.grid(True, alpha=0.3, axis='y')
            
            # === 子图2: 利润率结构 ===
            ax2 = axes[0, 1]
            gross_col = next((c for c in fin_df.columns if '毛利率' in c), None)
            net_col = next((c for c in fin_df.columns if '净利率' in c or '销售净利率' in c), None)
            
            if gross_col and net_col:
                recent = fin_df[fin_df['截止日期'].dt.month == 12].tail(6)
                if len(recent) >= 2:
                    years = recent['截止日期'].dt.year.astype(str)
                    gross = recent[gross_col].apply(self._safe_float)
                    net = recent[net_col].apply(self._safe_float)
                    
                    ax2.plot(years, gross, 'o-', color='brown', linewidth=2, markersize=6, label='毛利率')
                    ax2.plot(years, net, 's-', color='blue', linewidth=2, markersize=6, label='净利率')
                    ax2.set_ylabel('%')
                    ax2.legend(loc='best')
                    ax2.set_title('利润率趋势', fontsize=11, fontweight='bold')
                    ax2.grid(True, alpha=0.3)
            
            # === 子图3: 现金流结构 ===
            ax3 = axes[1, 0]
            if cf_df is not None and len(cf_df) >= 4:
                recent_cf = cf_df.tail(4)
                cfo_col = next((c for c in cf_df.columns if '经营' in c and '净额' in c), None)
                cfi_col = next((c for c in cf_df.columns if '投资' in c and '净额' in c), None)
                cff_col = next((c for c in cf_df.columns if '筹资' in c and '净额' in c), None)
                
                if cfo_col:
                    dates = recent_cf['报告日'].dt.strftime('%Y-%m') if '报告日' in recent_cf.columns else recent_cf.index.astype(str)
                    cfo = recent_cf[cfo_col].apply(self._safe_float) / 1e8 if cfo_col else [0]*len(recent_cf)
                    cfi = recent_cf[cfi_col].apply(self._safe_float) / 1e8 if cfi_col else [0]*len(recent_cf)
                    cff = recent_cf[cff_col].apply(self._safe_float) / 1e8 if cff_col else [0]*len(recent_cf)
                    
                    x = np.arange(len(dates))
                    width = 0.25
                    ax3.bar(x - width, cfo, width, label='经营', color='green', alpha=0.8)
                    ax3.bar(x, cfi, width, label='投资', color='red', alpha=0.8)
                    ax3.bar(x + width, cff, width, label='筹资', color='purple', alpha=0.8)
                    ax3.axhline(y=0, color='black', linewidth=0.5)
                    ax3.set_xticks(x)
                    ax3.set_xticklabels(dates)
                    ax3.set_ylabel('亿元')
                    ax3.legend(loc='best', fontsize=8)
                    ax3.set_title('现金流结构', fontsize=11, fontweight='bold')
                    ax3.grid(True, alpha=0.3, axis='y')
            
            # === 子图4: ROE趋势 ===
            ax4 = axes[1, 1]
            roe_col = next((c for c in fin_df.columns if 'ROE' in c or '净资产收益率' in c), None)
            if roe_col:
                annual = fin_df[fin_df['截止日期'].dt.month == 12].tail(6)
                if len(annual) >= 2:
                    years = annual['截止日期'].dt.year.astype(str)
                    roe = annual[roe_col].apply(self._safe_float)
                    
                    colors = ['green' if v >= 15 else 'orange' if v >= 10 else 'red' for v in roe]
                    ax4.bar(years, roe, color=colors, alpha=0.8)
                    ax4.axhline(y=15, color='green', linestyle='--', linewidth=1, label='优秀线(15%)')
                    ax4.axhline(y=10, color='orange', linestyle='--', linewidth=1, label='良好线(10%)')
                    ax4.set_ylabel('%')
                    ax4.legend(loc='best', fontsize=8)
                    ax4.set_title('ROE趋势', fontsize=11, fontweight='bold')
                    ax4.grid(True, alpha=0.3, axis='y')
            
            plt.tight_layout(rect=[0, 0, 1, 0.96])
            plt.savefig(f"{self.output_dir}/D1_基本面Dashboard.png", dpi=200, bbox_inches='tight')
            plt.close()
            print(f"  ✓ 生成合并图表: D1_基本面Dashboard.png")
        except Exception as e:
            plt.close()
            print(f"  ⚠ 基本面Dashboard生成失败: {e}")
    
    def _generate_valuation_dashboard(self):
        """估值分析Dashboard (2x2): PE/PB历史、DCF、DDM、股息率"""
        try:
            fig, axes = plt.subplots(2, 2, figsize=(16, 12))
            fig.suptitle(f'{self.stock_name} - 估值分析 Dashboard', fontsize=16, fontweight='bold', y=0.98)
            
            # === 子图1: PE/PB历史分位 ===
            ax1 = axes[0, 0]
            pe = self.current_valuation.get('pe_ttm', 0)
            pb = self.current_valuation.get('pb', 0)
            
            # 简单的估值区间示意
            categories = ['PE(TTM)', 'PB']
            values = [pe, pb]
            colors = []
            for i, v in enumerate(values):
                if i == 0:  # PE
                    colors.append('green' if v < 15 else 'orange' if v < 25 else 'red')
                else:  # PB
                    colors.append('green' if v < 2 else 'orange' if v < 4 else 'red')
            
            bars = ax1.barh(categories, values, color=colors, alpha=0.8, height=0.5)
            ax1.set_xlabel('倍数')
            ax1.set_title('当前估值水平', fontsize=11, fontweight='bold')
            for bar, val in zip(bars, values):
                ax1.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2, 
                        f'{val:.1f}', va='center', fontsize=12, fontweight='bold')
            ax1.grid(True, alpha=0.3, axis='x')
            
            # === 子图2: PEG分析 ===
            ax2 = axes[0, 1]
            # 计算不同增长假设下的PEG
            g_rates = [5, 10, 15, 20, 25]
            pegs = [pe / g if g > 0 else 0 for g in g_rates]
            colors_peg = ['green' if p < 1 else 'orange' if p < 2 else 'red' for p in pegs]
            
            bars2 = ax2.bar([f'G={g}%' for g in g_rates], pegs, color=colors_peg, alpha=0.8)
            ax2.axhline(y=1, color='green', linestyle='--', linewidth=2, label='PEG=1 (合理)')
            ax2.axhline(y=2, color='orange', linestyle='--', linewidth=1, label='PEG=2')
            ax2.set_ylabel('PEG')
            ax2.set_title(f'PEG敏感性分析 (当前PE={pe:.1f})', fontsize=11, fontweight='bold')
            ax2.legend(loc='upper right', fontsize=8)
            ax2.grid(True, alpha=0.3, axis='y')
            
            # === 子图3: 市值与净利润对比 ===
            ax3 = axes[1, 0]
            mv = self.current_valuation.get('total_mv', 0) / 1e8
            
            fin_df = self.financial_data
            if fin_df is not None:
                profit_col = '净利润' if '净利润' in fin_df.columns else None
                if profit_col:
                    annual = fin_df[fin_df['截止日期'].dt.month == 12].tail(5)
                    if len(annual) >= 1:
                        profits = annual[profit_col].apply(self._safe_float) / 1e8
                        years = annual['截止日期'].dt.year.astype(str).tolist()
                        
                        # 添加当前市值作为对比
                        x = np.arange(len(years) + 1)
                        bar_vals = list(profits) + [mv]
                        bar_labels = years + ['当前市值']
                        bar_colors = ['blue'] * len(years) + ['red']
                        
                        ax3.bar(x, bar_vals, color=bar_colors, alpha=0.8)
                        ax3.set_xticks(x)
                        ax3.set_xticklabels(bar_labels, rotation=0)
                        ax3.set_ylabel('亿元')
                        ax3.set_title('历史净利润 vs 当前市值', fontsize=11, fontweight='bold')
                        
                        # 计算并标注平均PE
                        avg_profit = profits.mean()
                        if avg_profit > 0:
                            implied_pe = mv / avg_profit
                            ax3.text(0.95, 0.95, f'隐含PE(5年均值)={implied_pe:.1f}x', 
                                    transform=ax3.transAxes, ha='right', va='top',
                                    fontsize=10, bbox=dict(boxstyle='round', facecolor='wheat'))
                        ax3.grid(True, alpha=0.3, axis='y')
            
            # === 子图4: 股息率走势 ===
            ax4 = axes[1, 1]
            if self.dividend_data is not None and len(self.dividend_data) > 0 and self.stock_kline is not None:
                try:
                    div_df = self.dividend_data.copy()
                    date_col = next((c for c in div_df.columns if '日' in c and ('除' in c or '股权' in c)), None)
                    per10_col = next((c for c in div_df.columns if '派息' in c or '10派' in c), None)
                    
                    if date_col and per10_col:
                        div_df[date_col] = pd.to_datetime(div_df[date_col], errors='coerce')
                        div_df = div_df.dropna(subset=[date_col])
                        div_df['year'] = div_df[date_col].dt.year
                        div_df['dps'] = div_df[per10_col].apply(self._safe_float) / 10
                        
                        annual_dps = div_df.groupby('year')['dps'].sum().tail(6)
                        
                        # 获取年末股价
                        kline = self.stock_kline.copy()
                        kline['year'] = kline['日期'].dt.year
                        year_end_prices = kline.groupby('year')['收盘'].last()
                        
                        common_years = sorted(set(annual_dps.index) & set(year_end_prices.index))
                        if len(common_years) >= 2:
                            yields = [(annual_dps[y] / year_end_prices[y] * 100) for y in common_years]
                            
                            colors_dy = ['green' if y >= 3 else 'orange' if y >= 1.5 else 'gray' for y in yields]
                            ax4.bar([str(y) for y in common_years], yields, color=colors_dy, alpha=0.8)
                            ax4.axhline(y=3, color='green', linestyle='--', linewidth=1, label='高股息线(3%)')
                            ax4.set_ylabel('股息率 %')
                            ax4.set_title('历史股息率', fontsize=11, fontweight='bold')
                            ax4.legend(loc='upper right', fontsize=8)
                            ax4.grid(True, alpha=0.3, axis='y')
                except Exception:
                    ax4.text(0.5, 0.5, '股息率数据不足', ha='center', va='center', transform=ax4.transAxes)
                    ax4.set_title('历史股息率', fontsize=11, fontweight='bold')
            else:
                ax4.text(0.5, 0.5, '无分红数据', ha='center', va='center', transform=ax4.transAxes)
                ax4.set_title('历史股息率', fontsize=11, fontweight='bold')
            
            plt.tight_layout(rect=[0, 0, 1, 0.96])
            plt.savefig(f"{self.output_dir}/D2_估值Dashboard.png", dpi=200, bbox_inches='tight')
            plt.close()
            print(f"  ✓ 生成合并图表: D2_估值Dashboard.png")
        except Exception as e:
            plt.close()
            print(f"  ⚠ 估值Dashboard生成失败: {e}")
    
    def _generate_expense_dashboard(self):
        """费用结构Dashboard (2x2): 销售、管理、研发、财务费用"""
        try:
            fig, axes = plt.subplots(2, 2, figsize=(14, 10))
            fig.suptitle(f'{self.stock_name} - 费用结构 Dashboard (近6年)', fontsize=16, fontweight='bold', y=0.98)
            
            inc_df = self.income_statement
            if inc_df is None:
                plt.close()
                return
            
            inc_df = inc_df.copy()
            inc_df['报告日'] = pd.to_datetime(inc_df['报告日'], errors='coerce')
            annual = inc_df[inc_df['报告日'].dt.month == 12].tail(6)
            
            if len(annual) < 2:
                plt.close()
                return
            
            years = annual['报告日'].dt.year.astype(str)
            rev_col = next((c for c in annual.columns if '营业总收入' in c or '营业收入' in c), None)
            rev = annual[rev_col].apply(self._safe_float) / 1e8 if rev_col else None
            
            # 辅助绘图函数
            def plot_expense(ax, col_name, title, bar_color, line_color, line_style):
                col = next((c for c in annual.columns if col_name in c), None)
                if col:
                    exp = annual[col].apply(self._safe_float) / 1e8
                    
                    # 绘制柱状图
                    if col_name == '财务费用':
                         colors = ['#e74c3c' if x > 0 else '#2ecc71' for x in exp.values]
                         ax.bar(years, exp, color=colors, alpha=0.7, label=title)
                         ax.axhline(0, color='black', linewidth=0.5)
                    else:
                         ax.bar(years, exp, color=bar_color, alpha=0.7, label=title)
                    
                    ax.set_ylabel('费用 (亿元)', color=bar_color if col_name != '财务费用' else 'black')
                    ax.set_title(title, fontsize=11, fontweight='bold')
                    
                    # 绘制占营收比例
                    if rev is not None:
                        ax_twin = ax.twinx()
                        ratio = (exp.values / rev.values * 100)
                        ax_twin.plot(years, ratio, color=line_color, marker='o', linestyle=line_style, linewidth=1.5, label='费率(%)')
                        ax_twin.set_ylabel('占营收 %', color=line_color)
                        ax_twin.tick_params(axis='y', labelcolor=line_color)
                        
                        # 标注最新值
                        last_ratio = ratio[-1]
                        ax_twin.annotate(f'{last_ratio:.1f}%', xy=(years.iloc[-1], last_ratio),
                                       xytext=(0, 5), textcoords='offset points', 
                                       fontsize=9, fontweight='bold', color=line_color)

                    ax.grid(True, alpha=0.3)
                    return True
                return False

            # === 1. 销售费用 (左上) - 橙色 ===
            plot_expense(axes[0, 0], '销售费用', '销售费用', '#f39c12', '#d35400', '--')
            
            # === 2. 管理费用 (右上) - 蓝色 ===
            plot_expense(axes[0, 1], '管理费用', '管理费用', '#3498db', '#2980b9', '-.')
            
            # === 3. 研发费用 (左下) - 紫色 ===
            plot_expense(axes[1, 0], '研发费用', '研发费用', '#9b59b6', '#8e44ad', ':')
            
            # === 4. 财务费用 (右下) - 红/绿 ===
            plot_expense(axes[1, 1], '财务费用', '财务费用 (红支绿收)', 'gray', 'black', '-')
            
            plt.tight_layout()
            plt.subplots_adjust(top=0.92)
            plt.savefig(f"{self.output_dir}/D3_费用Dashboard.png", dpi=200, bbox_inches='tight')
            plt.close()
            print(f"  ✓ 生成合并图表: D3_费用Dashboard.png")
        except Exception as e:
            plt.close()
            print(f"  ⚠ 费用Dashboard生成失败: {e}")
    
    def analyze_trade_signals(self):
        """分析交易信号 (汇总)"""
        signals = {
            'positive': [],
            'negative': []
        }
        
        # 收集增量分析中的信号
        growth_signals = self.report_data.get('growth_momentum', {}).get('signals', {})
        if growth_signals:
            signals['positive'].extend(growth_signals.get('positive', []))
            signals['negative'].extend(growth_signals.get('negative', []))
            
        # 收集风险信号
        risks = self.report_data.get('risks', [])
        signals['negative'].extend(risks)
        
        return signals

    # ==================== 报告生成 ====================
    def generate_summary(self):
        """生成分析总结 - 客观、有条理、有依据"""
        
        # 生成Dashboard合并图表
        self._generate_dashboard_charts()
        
        self._log("\n" + "="*70)
        self._log("  📋 投资分析总结报告")
        self._log("="*70)
        
        avg_score = np.mean(list(self.scores.values()))
        
        # ------------------ 第一部分：基本信息 ------------------
        self._log(f"\n{'─'*70}")
        self._log(f"  一、标的概况")
        self._log(f"{'─'*70}")
        self._log(f"  公司名称: {self.stock_name}")
        self._log(f"  股票代码: {self.stock_code}")
        self._log(f"  所属行业: {self.industry}")
        self._log(f"  分析日期: {datetime.now().strftime('%Y-%m-%d')}")
        
        # 估值快照
        pe = self.current_valuation.get('pe_ttm', 0)
        pb = self.current_valuation.get('pb', 0)
        price = self.current_valuation.get('price', 0)
        mv = self.current_valuation.get('total_mv', 0) / 1e8
        self._log(f"\n  当前股价: ¥{price:.2f}")
        self._log(f"  总市值: {mv:.1f}亿")
        self._log(f"  PE(TTM): {pe:.1f}  |  PB: {pb:.2f}")
        
        # ------------------ 第二部分：核心结论 ------------------
        self._log(f"\n{'─'*70}")
        self._log(f"  二、核心结论 (综合评分: {avg_score:.0f}/100)")
        self._log(f"{'─'*70}")
        
        # 评分可视化
        score_names = {
            'growth': '成长性',
            'profitability': '盈利能力',
            'stability': '稳定性',
            'safety': '财务安全',
            'valuation': '估值吸引力'
        }
        for key, name in score_names.items():
            score = self.scores.get(key, 0)
            bar = '█' * int(score/10) + '░' * (10 - int(score/10))
            self._log(f"     {name:<8}: {bar} {score:.0f}")
        
        # 投资建议
        self._log(f"\n  【投资评级】")
        if avg_score >= 75:
            self._log(f"     ⭐⭐⭐⭐⭐ 优质标的，值得重点关注")
        elif avg_score >= 60:
            self._log(f"     ⭐⭐⭐⭐☆ 质地较好，可纳入观察池")
        elif avg_score >= 45:
            self._log(f"     ⭐⭐⭐☆☆ 表现中等，需深入研究")
        else:
            self._log(f"     ⭐⭐☆☆☆ 风险较高，建议谨慎")
        
        # ------------------ 第三部分：关键依据 ------------------
        self._log(f"\n{'─'*70}")
        self._log(f"  三、关键依据")
        self._log(f"{'─'*70}")
        
        # 从财务数据提取关键指标
        if self.financial_data is not None and len(self.financial_data) > 0:
            latest = self.financial_data.iloc[-1]
            
            rev_col = next((c for c in self.financial_data.columns if '营业总收入' in c or '营业收入' in c), None)
            profit_col = '净利润' if '净利润' in self.financial_data.columns else None
            gross_col = next((c for c in self.financial_data.columns if '毛利率' in c), None)
            net_margin_col = next((c for c in self.financial_data.columns if '净利率' in c), None)
            roe_col = next((c for c in self.financial_data.columns if '净资产收益率' in c), None)
            debt_col = next((c for c in self.financial_data.columns if '资产负债率' in c), None)
            cfo_col = next((c for c in self.financial_data.columns if '经营' in c and '现金' in c), None)
            
            rev = self._safe_float(latest[rev_col]) / 1e8 if rev_col else 0
            profit = self._safe_float(latest[profit_col]) / 1e8 if profit_col else 0
            gross = self._safe_float(latest[gross_col]) if gross_col else 0
            net_margin = self._safe_float(latest[net_margin_col]) if net_margin_col else 0
            roe = self._safe_float(latest[roe_col]) if roe_col else 0
            debt_ratio = self._safe_float(latest[debt_col]) if debt_col else 0
            cfo = self._safe_float(latest[cfo_col]) / 1e8 if cfo_col else 0
            
            self._log(f"\n  【盈利能力】")
            self._log(f"     最新营收: {rev:.2f}亿  |  净利润: {profit:.2f}亿")
            self._log(f"     毛利率: {gross:.1f}%  |  净利率: {net_margin:.1f}%  |  ROE: {roe:.1f}%")
            
            # 盈利能力评价
            if gross > 40 and net_margin > 15 and roe > 15:
                self._log(f"     → 盈利能力优秀，具备较强的产品定价权和成本控制能力")
            elif gross > 25 and net_margin > 8 and roe > 10:
                self._log(f"     → 盈利能力良好，经营效率尚可")
            else:
                self._log(f"     → 盈利能力一般，需关注行业竞争格局")
            
            self._log(f"\n  【财务安全】")
            self._log(f"     资产负债率: {debt_ratio:.1f}%")
            if debt_ratio < 40:
                self._log(f"     → 财务结构稳健，抗风险能力强")
            elif debt_ratio < 60:
                self._log(f"     → 负债水平适中，财务状况正常")
            else:
                self._log(f"     → 负债较高，需关注偿债压力")
            
            # 现金流
            if cfo > 0 and profit > 0:
                cash_ratio = cfo / profit
                self._log(f"\n  【现金流质量】")
                self._log(f"     经营现金流: {cfo:.2f}亿  |  净现比: {cash_ratio:.2f}")
                if cash_ratio >= 1:
                    self._log(f"     → 利润含金量高，经营现金流充沛")
                elif cash_ratio >= 0.5:
                    self._log(f"     → 现金流一般，需关注应收款回收")
                else:
                    self._log(f"     → 现金流较弱，存在利润质量隐患")
        
        # 成长性评价
        growth_data = self.report_data.get('growth_momentum', {})
        if growth_data:
            self._log(f"\n  【成长能力】")
            summary = growth_data.get('summary', '')
            quality = growth_data.get('growth_quality', '')
            if summary:
                self._log(f"     增长类型: {summary}")
            if quality:
                self._log(f"     增长质量: {quality}")
        
        # 从年报计算CAGR并展示
        if self.financial_data is not None and len(self.financial_data) >= 4:
            annual_df = self.financial_data[self.financial_data['截止日期'].dt.month == 12]
            if len(annual_df) >= 4:
                try:
                    rev_col = next((c for c in self.financial_data.columns if '营业总收入' in c or '营业收入' in c), None)
                    profit_col = '净利润' if '净利润' in self.financial_data.columns else None
                    
                    if rev_col and profit_col:
                        latest_rev = self._safe_float(annual_df.iloc[-1][rev_col])
                        start_rev = self._safe_float(annual_df.iloc[-4][rev_col])
                        latest_profit = self._safe_float(annual_df.iloc[-1][profit_col])
                        start_profit = self._safe_float(annual_df.iloc[-4][profit_col])
                        
                        if start_rev > 0 and latest_rev > 0:
                            rev_cagr = (latest_rev / start_rev) ** (1/3) - 1
                            self._log(f"     3年营收CAGR: {rev_cagr:.1%}")
                        if start_profit > 0 and latest_profit > 0:
                            profit_cagr = (latest_profit / start_profit) ** (1/3) - 1
                            self._log(f"     3年净利CAGR: {profit_cagr:.1%}")
                            
                            # 增长评价
                            if profit_cagr > 0.2:
                                self._log(f"     → 高成长标的，保持快速增长")
                            elif profit_cagr > 0.1:
                                self._log(f"     → 稳健成长，增长质量较好")
                            elif profit_cagr > 0:
                                self._log(f"     → 低速增长，需关注增长动力")
                            else:
                                self._log(f"     → 增长乏力，业绩承压")
                except Exception:
                    pass
        
        # ------------------ 第四部分：风险提示 ------------------
        self._log(f"\n{'─'*70}")
        self._log(f"  四、风险提示")
        self._log(f"{'─'*70}")
        
        risks = self.report_data.get('risks', [])
        warnings = self.report_data.get('warnings', [])
        financial_warnings = self.report_data.get('financial_warnings', [])
        
        all_risks = risks + warnings + financial_warnings
        if all_risks:
            for i, risk in enumerate(all_risks[:8], 1):  # 最多显示8条
                self._log(f"     {i}. {risk}")
        else:
            self._log(f"     暂未发现明显风险信号")
        
        # ------------------ 第五部分：操作建议 ------------------
        self._log(f"\n{'─'*70}")
        self._log(f"  五、操作建议")
        self._log(f"{'─'*70}")
        
        # 基于PE估值判断
        if pe > 0:
            if pe < 15:
                val_status = "低估区间"
            elif pe < 25:
                val_status = "合理区间"
            elif pe < 40:
                val_status = "偏高区间"
            else:
                val_status = "高估区间"
            self._log(f"     估值状态: {val_status} (PE={pe:.1f})")
        
        # PEG分析
        if pe > 0 and self.financial_data is not None and len(self.financial_data) >= 4:
            annual_df = self.financial_data[self.financial_data['截止日期'].dt.month == 12]
            if len(annual_df) >= 4:
                try:
                    profit_col = '净利润' if '净利润' in self.financial_data.columns else None
                    if profit_col:
                        latest_profit = self._safe_float(annual_df.iloc[-1][profit_col])
                        start_profit = self._safe_float(annual_df.iloc[-4][profit_col])
                        if start_profit > 0 and latest_profit > 0:
                            profit_cagr = (latest_profit / start_profit) ** (1/3) - 1
                            if profit_cagr > 0:
                                peg = pe / (profit_cagr * 100)
                                self._log(f"     PEG(基于3年CAGR): {peg:.2f}")
                                if peg < 0.8:
                                    self._log(f"     → PEG<0.8，成长性价比高")
                                elif peg < 1.2:
                                    self._log(f"     → PEG合理，估值与增长匹配")
                                elif peg < 2:
                                    self._log(f"     → PEG偏高，需更高增长支撑")
                                else:
                                    self._log(f"     → PEG过高，估值可能透支增长预期")
                except Exception:
                    pass
        
        # 技术面快照
        if self.stock_kline is not None and len(self.stock_kline) > 60:
            try:
                kline = self.stock_kline.copy()
                closes = kline['收盘'].values
                latest_price = closes[-1]
                ma20 = np.mean(closes[-20:]) if len(closes) >= 20 else 0
                ma60 = np.mean(closes[-60:]) if len(closes) >= 60 else 0
                
                self._log(f"\n  【技术面参考】")
                self._log(f"     当前价: ¥{latest_price:.2f}  |  MA20: ¥{ma20:.2f}  |  MA60: ¥{ma60:.2f}")
                
                if latest_price > ma20 > ma60:
                    self._log(f"     → 多头排列，趋势向上")
                elif latest_price < ma20 < ma60:
                    self._log(f"     → 空头排列，趋势向下")
                else:
                    self._log(f"     → 震荡整理，等待方向选择")
            except Exception:
                pass
        
        # 综合建议
        self._log(f"\n  【综合建议】")
        if avg_score >= 70 and pe < 30:
            self._log(f"     基本面优良，估值合理，可考虑逢低布局")
        elif avg_score >= 60 and pe < 40:
            self._log(f"     质地尚可，建议持续跟踪，等待更好买点")
        elif avg_score >= 50:
            self._log(f"     表现中等，建议进一步研究业务逻辑和竞争格局")
        else:
            self._log(f"     风险因素较多，建议保持观望或谨慎参与")
        
        # DCF/DDM估值结论
        val_data = self.report_data.get('valuation', {})
        if val_data.get('dcf_per_share') or val_data.get('ddm_gordon'):
            self._log(f"\n  【估值模型参考】")
            
            if val_data.get('dcf_per_share'):
                dcf_val = val_data['dcf_per_share']
                dcf_mos = val_data.get('dcf_margin_of_safety', 0)
                self._log(f"     DCF估值: ¥{dcf_val:.2f}/股  (安全边际: {dcf_mos:+.1f}%")
            
            if val_data.get('ddm_gordon'):
                ddm_g = val_data['ddm_gordon']
                ddm_2 = val_data.get('ddm_two_stage', 0)
                div_yield = val_data.get('dividend_yield', 0)
                self._log(f"     DDM估值: Gordon ¥{ddm_g:.2f} | 两阶段 ¥{ddm_2:.2f}")
                self._log(f"     当前股息率: {div_yield:.2f}%")
            
            # 估值综合判断
            if val_data.get('dcf_per_share') and price > 0:
                dcf_val = val_data['dcf_per_share']
                if price < dcf_val * 0.8:
                    self._log(f"     → 当前价低于DCF估值20%+，存在安全边际")
                elif price < dcf_val:
                    self._log(f"     → 当前价接近DCF内在价值")
                else:
                    self._log(f"     → 当前价高于DCF估值，注意估值风险")

        # ------------------ 第六部分：交易信号参考 ------------------
        self._log(f"\n{'─'*70}")
        self._log(f"  六、交易信号参考")
        self._log(f"{'─'*70}")
        self._log(f"     ⚠️ 免责声明: 此部分基于技术指标生成，仅供参考，不构成投资建议。")
        
        trade_signal_info = self.analyze_trade_signals()
        signal = trade_signal_info.get('signal', '未知')
        reason = trade_signal_info.get('reason', '未能生成信号')
        
        signal_color = "🟢" if signal == '买入' else "🔴" if signal == '卖出' else "🟡"
        
        self._log(f"\n  【信号判断】: {signal_color} {signal}")
        self._log(f"  【判断依据】: {reason}")
        self._log(f"     (信号逻辑: MACD与KDJ共振金叉/死叉)")
        self._log(f"     (详情请参考图表 `10_技术指标.png`)")

        
        self._log(f"\n  【免责声明】")
        self._log(f"     本报告基于公开财务数据自动生成，仅供参考，不构成投资建议。")
        self._log(f"     投资有风险，入市需谨慎。")
        
        self._log(f"\n{'─'*70}")
        self._log(f"  📂 图表已保存至: {self.output_dir}/")
        self._log(f"{'─'*70}")
        
        # 保存报告
        self._save_report()
        self._save_structured_data(avg_score)
    
    def _save_report(self):
        """保存文字分析报告"""
        report_path = f"{self.output_dir}/分析报告.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.report_lines))
        print(f"  ✓ 文字报告已保存: {report_path}")
    
    def _save_structured_data(self, avg_score):
        """保存结构化数据（JSON格式）- 完整版"""
        import json
        
        # 收集关键数据
        data = {
            'meta': {
                'stock_code': self.stock_code,
                'stock_name': self.stock_name,
                'industry': self.industry,
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_shares_yi': round(self.total_shares / 1e8, 2) if self.total_shares else 0,
            },
            'scores': {
                'overall': round(avg_score, 1),
                'growth': self.scores.get('growth', 0),
                'profitability': self.scores.get('profitability', 0),
                'stability': self.scores.get('stability', 0),
                'safety': self.scores.get('safety', 0),
                'valuation': self.scores.get('valuation', 0),
            },
            'valuation': {
                'price': self.current_valuation.get('price', 0),
                'pe_ttm': self.current_valuation.get('pe_ttm', 0),
                'pb': self.current_valuation.get('pb', 0),
                'ps': self.current_valuation.get('ps', 0),
                'total_mv_yi': round(self.current_valuation.get('total_mv', 0) / 1e8, 2),
                'source': self.current_valuation.get('source', ''),
            },
            'fundamentals': {},
            'cash_flow': {},
            'annual_trend': [],
            'growth_momentum': self.report_data.get('growth_momentum', {}),
            'technical': {},
            'dividend': {},
            'risks': self.report_data.get('risks', []),
            'warnings': self.report_data.get('warnings', []),
            'financial_warnings': self.report_data.get('financial_warnings', []),
        }
        
        # 从财务数据提取关键指标
        if self.financial_data is not None:
            latest = self.financial_data.iloc[-1]
            
            rev_col = next((c for c in self.financial_data.columns if '营业总收入' in c or '营业收入' in c), None)
            profit_col = '净利润' if '净利润' in self.financial_data.columns else None
            deducted_col = next((c for c in self.financial_data.columns if '扣非' in c and '净利' in c), None)
            gross_col = next((c for c in self.financial_data.columns if '毛利率' in c), None)
            net_margin_col = next((c for c in self.financial_data.columns if '净利率' in c), None)
            roe_col = next((c for c in self.financial_data.columns if '净资产收益率' in c), None)
            debt_col = next((c for c in self.financial_data.columns if '资产负债率' in c), None)
            
            data['fundamentals'] = {
                'report_date': latest['截止日期'].strftime('%Y-%m-%d'),
                'revenue_yi': round(self._safe_float(latest[rev_col]) / 1e8, 2) if rev_col else None,
                'net_profit_yi': round(self._safe_float(latest[profit_col]) / 1e8, 2) if profit_col else None,
                'deducted_profit_yi': round(self._safe_float(latest[deducted_col]) / 1e8, 2) if deducted_col else None,
                'gross_margin_pct': round(self._safe_float(latest[gross_col]), 2) if gross_col else None,
                'net_margin_pct': round(self._safe_float(latest[net_margin_col]), 2) if net_margin_col else None,
                'roe_pct': round(self._safe_float(latest[roe_col]), 2) if roe_col else None,
                'debt_ratio_pct': round(self._safe_float(latest[debt_col]), 2) if debt_col else None,
            }
            
            # 年度趋势数据
            annual_df = self.financial_data[self.financial_data['截止日期'].dt.month == 12].tail(6)
            annual_trend = []
            for _, row in annual_df.iterrows():
                annual_trend.append({
                    'year': int(row['截止日期'].year),
                    'revenue_yi': round(self._safe_float(row[rev_col]) / 1e8, 2) if rev_col else None,
                    'net_profit_yi': round(self._safe_float(row[profit_col]) / 1e8, 2) if profit_col else None,
                    'gross_margin_pct': round(self._safe_float(row[gross_col]), 2) if gross_col else None,
                    'roe_pct': round(self._safe_float(row[roe_col]), 2) if roe_col else None,
                })
            data['annual_trend'] = annual_trend
        
        # 现金流数据
        if self.cash_flow_data is not None and len(self.cash_flow_data) > 0:
            recent_cf = self.cash_flow_data.tail(4)
            cfo_col = next((c for c in self.cash_flow_data.columns if '经营' in c and '净额' in c), None)
            cfi_col = next((c for c in self.cash_flow_data.columns if '投资' in c and '净额' in c), None)
            cff_col = next((c for c in self.cash_flow_data.columns if '筹资' in c and '净额' in c), None)
            
            cf_trend = []
            for _, row in recent_cf.iterrows():
                date_val = row.get('报告日', row.get('截止日期'))
                cf_trend.append({
                    'date': date_val.strftime('%Y-%m') if hasattr(date_val, 'strftime') else str(date_val),
                    'cfo_yi': round(self._safe_float(row[cfo_col]) / 1e8, 2) if cfo_col else None,
                    'cfi_yi': round(self._safe_float(row[cfi_col]) / 1e8, 2) if cfi_col else None,
                    'cff_yi': round(self._safe_float(row[cff_col]) / 1e8, 2) if cff_col else None,
                })
            data['cash_flow'] = {
                'trend': cf_trend,
                'latest_cfo_yi': cf_trend[-1]['cfo_yi'] if cf_trend else None,
            }
        
        # 资产负债表数据
        if self.balance_sheet is not None and len(self.balance_sheet) > 0:
            latest_bs = self.balance_sheet.iloc[-1]
            
            # 动态查找列名
            total_assets_col = next((c for c in self.balance_sheet.columns if '资产总' in c or '总资产' in c), None)
            total_liab_col = next((c for c in self.balance_sheet.columns if '负债合计' in c or '负债总' in c), None)
            cash_col = next((c for c in self.balance_sheet.columns if '货币资金' in c), None)
            receivable_col = next((c for c in self.balance_sheet.columns if '应收账款' in c and '应收账款融资' not in c), None)
            inventory_col = next((c for c in self.balance_sheet.columns if c == '存货'), None)
            equity_col = next((c for c in self.balance_sheet.columns if '所有者权益' in c or '股东权益' in c), None)
            
            data['balance_sheet'] = {
                'report_date': latest_bs.get('报告日', latest_bs.get('截止日期', '')),
                'total_assets_yi': round(self._safe_float(latest_bs.get(total_assets_col, 0)) / 1e8, 2) if total_assets_col else None,
                'total_liabilities_yi': round(self._safe_float(latest_bs.get(total_liab_col, 0)) / 1e8, 2) if total_liab_col else None,
                'cash_yi': round(self._safe_float(latest_bs.get(cash_col, 0)) / 1e8, 2) if cash_col else None,
                'receivables_yi': round(self._safe_float(latest_bs.get(receivable_col, 0)) / 1e8, 2) if receivable_col else None,
                'inventory_yi': round(self._safe_float(latest_bs.get(inventory_col, 0)) / 1e8, 2) if inventory_col else None,
                'equity_yi': round(self._safe_float(latest_bs.get(equity_col, 0)) / 1e8, 2) if equity_col else None,
            }
        
        # 费用数据
        if self.income_statement is not None and len(self.income_statement) > 0:
            inc_df = self.income_statement.copy()
            inc_df['报告日'] = pd.to_datetime(inc_df['报告日'], errors='coerce')
            annual_inc = inc_df[inc_df['报告日'].dt.month == 12].tail(5)
            
            if len(annual_inc) >= 1:
                sale_col = next((c for c in annual_inc.columns if '销售费用' in c), None)
                admin_col = next((c for c in annual_inc.columns if '管理费用' in c), None)
                fin_col = next((c for c in annual_inc.columns if '财务费用' in c), None)
                rd_col = next((c for c in annual_inc.columns if '研发费用' in c), None)
                rev_col = next((c for c in annual_inc.columns if '营业总收入' in c or '营业收入' in c), None)
                
                expense_trend = []
                for _, row in annual_inc.iterrows():
                    rev_val = self._safe_float(row.get(rev_col, 0))
                    sale_val = self._safe_float(row.get(sale_col, 0))
                    admin_val = self._safe_float(row.get(admin_col, 0))
                    fin_val = self._safe_float(row.get(fin_col, 0))
                    rd_val = self._safe_float(row.get(rd_col, 0))
                    
                    expense_trend.append({
                        'year': int(row['报告日'].year),
                        'revenue_yi': round(rev_val / 1e8, 2),
                        'sales_expense_yi': round(sale_val / 1e8, 2) if sale_col else None,
                        'admin_expense_yi': round(admin_val / 1e8, 2) if admin_col else None,
                        'financial_expense_yi': round(fin_val / 1e8, 2) if fin_col else None,
                        'rd_expense_yi': round(rd_val / 1e8, 2) if rd_col else None,
                        'sales_ratio_pct': round(sale_val / rev_val * 100, 2) if rev_val > 0 and sale_col else None,
                        'rd_ratio_pct': round(rd_val / rev_val * 100, 2) if rev_val > 0 and rd_col else None,
                    })
                data['expense_trend'] = expense_trend
        
        # 技术指标
        if self.stock_kline is not None and len(self.stock_kline) >= 120:
            closes = self.stock_kline['收盘']
            ma5 = closes.rolling(5).mean().iloc[-1]
            ma20 = closes.rolling(20).mean().iloc[-1]
            ma60 = closes.rolling(60).mean().iloc[-1]
            ma120 = closes.rolling(120).mean().iloc[-1]
            
            rsi = self._calculate_rsi(closes, 14).iloc[-1]
            dif, dea, macd = self._calculate_macd(closes, fast=10, slow=20, signal=8)
            k, d, j = self._calculate_kdj(self.stock_kline['最高'], self.stock_kline['最低'], closes)
            
            data['technical'] = {
                'latest_price': round(closes.iloc[-1], 2),
                'ma5': round(ma5, 2),
                'ma20': round(ma20, 2),
                'ma60': round(ma60, 2),
                'ma120': round(ma120, 2),
                'rsi14': round(rsi, 1),
                'macd': {
                    'dif': round(dif.iloc[-1], 3),
                    'dea': round(dea.iloc[-1], 3),
                    'histogram': round(macd.iloc[-1], 3),
                },
                'kdj': {
                    'k': round(k.iloc[-1], 1),
                    'd': round(d.iloc[-1], 1),
                    'j': round(j.iloc[-1], 1),
                },
                'trend': 'bullish' if closes.iloc[-1] > ma60 else 'bearish',
            }

            # 添加K线历史数据 (OHLCV) - 用于前端交互式图表
            # 限制最近 500 个交易日
            kline_history = []
            recent_kline = self.stock_kline.tail(500)
            for _, row in recent_kline.iterrows():
                kline_history.append({
                    'date': row['日期'].strftime('%Y-%m-%d') if hasattr(row['日期'], 'strftime') else str(row['日期']),
                    'open': round(row['开盘'], 2),
                    'high': round(row['最高'], 2),
                    'low': round(row['最低'], 2),
                    'close': round(row['收盘'], 2),
                    'volume': int(row['成交量']),
                })
            data['kline_history'] = kline_history

        # 添加行业对比数据
        if hasattr(self, 'industry_comp_df') and self.industry_comp_df is not None and not self.industry_comp_df.empty:
            industry_comp = []
            for _, row in self.industry_comp_df.iterrows():
                industry_comp.append({
                    'code': str(row.get('代码', '')),
                    'name': str(row.get('名称', '')),
                    'price': round(row.get('股价', 0), 2) if row.get('股价') else None,
                    'change_pct': round(row.get('涨跌幅', 0), 2) if row.get('涨跌幅') else None,
                    'pe': round(row.get('PE(动态)', 0), 2) if row.get('PE(动态)') else None,
                    'pb': round(row.get('PB', 0), 2) if row.get('PB') else None,
                    'market_cap': round(row.get('总市值', 0) / 1e8, 2) if row.get('总市值') else None,
                })
            data['industry_comparison'] = industry_comp
        
        # 分红数据
        if self.dividend_data is not None and len(self.dividend_data) > 0:
            div_df = self.dividend_data.copy()
            date_col = next((c for c in div_df.columns if '日' in c and ('除' in c or '股权' in c)), None)
            per10_col = next((c for c in div_df.columns if '派息' in c or '10派' in c), None)
            
            if date_col and per10_col:
                div_df[date_col] = pd.to_datetime(div_df[date_col], errors='coerce')
                div_df = div_df.dropna(subset=[date_col])
                div_df['year'] = div_df[date_col].dt.year
                div_df['dps'] = div_df[per10_col].apply(self._safe_float) / 10
                
                annual_dps = div_df.groupby('year')['dps'].sum().tail(5)
                
                div_history = []
                for year, dps in annual_dps.items():
                    div_history.append({'year': int(year), 'dps': round(dps, 4)})
                
                data['dividend'] = {
                    'history': div_history,
                    'latest_dps': round(annual_dps.iloc[-1], 4) if len(annual_dps) > 0 else 0,
                    'dividend_count': len(self.dividend_data),
                }
        
        # 合并valuation里的DCF/DDM结果
        if 'valuation' in self.report_data:
            for key in ['dcf_per_share', 'dcf_margin_of_safety', 'ddm_gordon', 'ddm_two_stage', 'dividend_yield', 'ddm_d0_annual']:
                if key in self.report_data['valuation']:
                    data['valuation'][key] = self.report_data['valuation'][key]
        
        # 保存JSON
        json_path = f"{self.output_dir}/analysis_data.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        print(f"  ✓ 结构化数据已保存: {json_path}")


class FuturesAnalyzer:
    """期货分析器"""
    def __init__(self, symbol):
        self.symbol = symbol.upper()
        self.name = self._get_name(self.symbol)
        self.output_dir = f"期货分析_{self.name}_{datetime.now().strftime('%Y%m%d')}"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        self.price_data = None
        
    def _get_name(self, symbol):
        mapping = {
            'AU0': '黄金主连', 'AG0': '白银主连', 'CU0': '沪铜主连', 'AL0': '沪铝主连',
            'ZN0': '沪锌主连', 'PB0': '沪铅主连', 'NI0': '沪镍主连', 'SN0': '沪锡主连',
            'TA0': 'PTA主连', 'MA0': '甲醇主连', 'V0': 'PVC主连', 'RB0': '螺纹钢主连',
            'I0': '铁矿石主连', 'JD0': '鸡蛋主连', 'C0': '玉米主连', 'M0': '豆粕主连',
            'Y0': '豆油主连', 'P0': '棕榈油主连', 'CF0': '棉花主连', 'SR0': '白糖主连',
            'RU0': '橡胶主连', 'SC0': '原油主连', 'PG0': 'LPG主连', 'EB0': '苯乙烯主连',
            'SA0': '纯碱主连', 'FG0': '玻璃主连', 'UR0': '尿素主连'
        }
        return mapping.get(symbol, symbol)

    def fetch_data(self):
        print(f"正在获取 {self.name} ({self.symbol}) 数据...")
        try:
            # 获取主连行情
            self.price_data = ak.futures_main_sina(symbol=self.symbol)
            self.price_data['日期'] = pd.to_datetime(self.price_data['日期'])
            
            # 计算均线
            self.price_data = self.price_data.sort_values('日期')
            self.price_data['MA20'] = self.price_data['收盘价'].rolling(window=20).mean()
            self.price_data['MA60'] = self.price_data['收盘价'].rolling(window=60).mean()
            self.price_data['MA120'] = self.price_data['收盘价'].rolling(window=120).mean()
            
            print(f"  ✓ 行情数据获取成功: {len(self.price_data)} 条")
        except Exception as e:
            print(f"  ✗ 数据获取失败: {e}")
            import traceback
            traceback.print_exc()

    def analyze_trend(self):
        if self.price_data is None or self.price_data.empty:
            return
            
        print("正在分析趋势...")
        df = self.price_data.copy()
        
        # 绘制K线趋势图
        plt.figure(figsize=(14, 8))
        
        # 绘制收盘价和均线
        plt.plot(df['日期'], df['收盘价'], label='收盘价', color='#333333', linewidth=1.5, alpha=0.8)
        plt.plot(df['日期'], df['MA20'], label='MA20 (月线)', color=COLORS['warning'], linewidth=1.5, linestyle='--')
        plt.plot(df['日期'], df['MA60'], label='MA60 (季线)', color=COLORS['primary'], linewidth=1.5, linestyle='--')
        plt.plot(df['日期'], df['MA120'], label='MA120 (半年线)', color=COLORS['secondary'], linewidth=1.5, linestyle='--')
        
        # 标注最高最低点
        max_idx = df['收盘价'].idxmax()
        min_idx = df['收盘价'].idxmin()
        max_date = df.loc[max_idx, '日期']
        max_price = df.loc[max_idx, '收盘价']
        min_date = df.loc[min_idx, '日期']
        min_price = df.loc[min_idx, '收盘价']
        
        plt.annotate(f'最高: {max_price}', xy=(max_date, max_price), xytext=(10, 10), 
                     textcoords='offset points', arrowprops=dict(arrowstyle='->', color='red'))
        plt.annotate(f'最低: {min_price}', xy=(min_date, min_price), xytext=(10, -20), 
                     textcoords='offset points', arrowprops=dict(arrowstyle='->', color='green'))

        plt.title(f"{self.name} ({self.symbol}) 价格趋势分析", fontsize=18)
        plt.xlabel("日期", fontsize=12)
        plt.ylabel("价格", fontsize=12)
        plt.legend(loc='best')
        plt.grid(True, alpha=0.3)
        
        # 保存图片
        output_path = f"{self.output_dir}/{self.symbol}_trend.png"
        plt.savefig(output_path, bbox_inches='tight')
        plt.close()
        print(f"  ✓ 趋势图已保存: {output_path}")
        
        # 生成成交量图
        plt.figure(figsize=(14, 4))
        # 使用 fill_between 代替 bar，防止数据量过大时显示为空
        plt.fill_between(df['日期'], df['成交量'], 0, color=COLORS['info'], alpha=0.4, label='成交量')
        plt.plot(df['日期'], df['成交量'], color=COLORS['info'], alpha=0.8, linewidth=0.5)
        
        plt.title(f"{self.name} 成交量变化 (全历史)", fontsize=14)
        plt.grid(True, alpha=0.3)
        plt.legend()
        vol_path = f"{self.output_dir}/{self.symbol}_volume.png"
        plt.savefig(vol_path, bbox_inches='tight')
        plt.close()
        print(f"  ✓ 成交量图已保存: {vol_path}")
        
        # 生成近期成交量图 (最近250个交易日)
        if len(df) > 250:
            recent_df = df.iloc[-250:]
            plt.figure(figsize=(14, 4))
            plt.bar(recent_df['日期'], recent_df['成交量'], color=COLORS['info'], alpha=0.6, label='成交量', width=0.8)
            plt.title(f"{self.name} 近一年成交量变化", fontsize=14)
            plt.grid(True, alpha=0.3)
            plt.legend()
            recent_vol_path = f"{self.output_dir}/{self.symbol}_volume_recent.png"
            plt.savefig(recent_vol_path, bbox_inches='tight')
            plt.close()
            print(f"  ✓ 近期成交量图已保存: {recent_vol_path}")

    def generate_report(self):
        if self.price_data is None or self.price_data.empty:
            return
            
        df = self.price_data.sort_values('日期')
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        change = latest['收盘价'] - prev['收盘价']
        pct_change = (change / prev['收盘价']) * 100
        
        # 计算近期涨跌幅
        last_20 = df.iloc[-20:] if len(df) >= 20 else df
        low_20 = last_20['收盘价'].min()
        high_20 = last_20['收盘价'].max()
        
        report = f"""# {self.name} ({self.symbol}) 分析报告
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 1. 最新行情
- **日期**: {latest['日期'].strftime('%Y-%m-%d')}
- **收盘价**: {latest['收盘价']}
- **涨跌**: {change:.2f} ({pct_change:.2f}%)
- **成交量**: {latest['成交量']}
- **持仓量**: {latest['持仓量']}

## 2. 技术指标
- **MA20**: {latest.get('MA20', 'N/A'):.2f}
- **MA60**: {latest.get('MA60', 'N/A'):.2f}
- **MA120**: {latest.get('MA120', 'N/A'):.2f}

## 3. 近期表现 (近20交易日)
- **最高价**: {high_20}
- **最低价**: {low_20}
- **波动幅度**: {((high_20 - low_20) / low_20 * 100):.2f}%

## 4. 趋势判断
"""
        # 简单趋势判断
        ma20 = latest.get('MA20')
        ma60 = latest.get('MA60')
        price = latest['收盘价']
        
        if pd.notna(ma20) and pd.notna(ma60):
            if price > ma20 and ma20 > ma60:
                report += "- **短期趋势**: 上升 (价格 > MA20 > MA60)\\n"
            elif price < ma20 and ma20 < ma60:
                report += "- **短期趋势**: 下降 (价格 < MA20 < MA60)\\n"
            else:
                report += "- **短期趋势**: 震荡\\n"
        
        with open(f"{self.output_dir}/report.md", "w", encoding="utf-8") as f:
            f.write(report)
        print(f"  ✓ 分析报告已生成: {self.output_dir}/report.md")


# ==================== 期货分析模块 ====================
class FuturesAnalyzer:
    def __init__(self, name_or_symbol):
        """
        初始化期货分析器
        :param name_or_symbol: 中文名称(如'黄金') 或 代码(如'AU')
        """
        self.name = self._resolve_name(name_or_symbol)
        self.config = FUTURES_MAPPING.get(self.name, {})
        self.symbol = self.config.get('symbol', name_or_symbol)
        
        # 数据存储
        self.history_data = None    # 行情数据
        self.spot_price = None      # 现货/基差数据
        self.inventory = None       # 库存数据
        self.holdings = None        # 持仓数据
        
        # 分析结果
        self.signals = []
        self.score = 50 # 初始中性评分
        self.final_report = {'final_score': 0, 'suggestion': 'N/A', 'signals': []}
        
        print(f"🔧 初始化期货分析器: {self.name} ({self.symbol})")

    def _resolve_name(self, query):
        """解析输入名称到标准中文名"""
        if query in FUTURES_MAPPING: return query
        for k, v in FUTURES_MAPPING.items():
            if v['symbol'] == query.upper(): return k
        for k in FUTURES_MAPPING.keys():
            if query in k: return k
        return query

    def fetch_all_data(self):
        """获取所有相关数据"""
        print("📥 开始获取数据...")
        # 1. 先并行获取 行情 和 库存
        with ThreadPoolExecutor(max_workers=2) as executor:
            t1 = executor.submit(self._fetch_history)
            t2 = executor.submit(self._fetch_inventory)
            t1.result()
            t2.result()
        # 2. 获取现货/基差数据
        self._fetch_spot_price()
        # 3. 获取持仓数据
        if self.spot_price and 'dominant_contract' in self.spot_price:
             self._fetch_holdings(self.spot_price['dominant_contract'])
        print("✅ 数据获取完成")

    def _fetch_history(self):
        try:
            main_code = f"{self.symbol}0"
            df = ak.futures_main_sina(symbol=main_code)
            df['日期'] = pd.to_datetime(df['日期'])
            for col in ['开盘价', '最高价', '最低价', '收盘价', '成交量', '持仓量']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            self.history_data = df
            print(f"  - 行情数据: {len(df)} 条")
        except Exception as e:
            print(f"  ❌ 获取行情失败: {e}")

    def _fetch_inventory(self):
        try:
            em_name = INVENTORY_MAPPING.get(self.name)
            if em_name:
                df = ak.futures_inventory_em(symbol=em_name)
                df['日期'] = pd.to_datetime(df['日期'])
                df['库存'] = pd.to_numeric(df['库存'], errors='coerce')
                self.inventory = df
                print(f"  - 库存数据: {len(df)} 条 (来源: 东财-{em_name})")
        except Exception as e:
            print(f"  ❌ 获取库存失败: {e}")

    def _fetch_spot_price(self):
        try:
            for i in range(5):
                 d_check = (datetime.now() - pd.Timedelta(days=i)).strftime('%Y%m%d')
                 try:
                     df = ak.futures_spot_price(date=d_check)
                     if df is not None and not df.empty:
                         row = df[df['symbol'] == self.symbol]
                         if not row.empty:
                             self.spot_price = row.iloc[0].to_dict()
                             print(f"  - 现货基差: 现货 {self.spot_price.get('spot_price')}, 基差 {self.spot_price.get('dom_basis')} (日期: {d_check})")
                             return
                 except: pass
        except Exception as e:
            print(f"  ⚠️ 基差数据获取受限: {e}")
            
    def _fetch_holdings(self, contract):
        try:
            self.holdings = {}
            for i in range(5):
                 d_check = (datetime.now() - pd.Timedelta(days=i)).strftime('%Y%m%d')
                 try:
                     df_long = ak.futures_hold_pos_sina(symbol='持买单量', contract=contract, date=d_check)
                     df_short = ak.futures_hold_pos_sina(symbol='持卖单量', contract=contract, date=d_check)
                     if (df_long is not None and not df_long.empty) and (df_short is not None and not df_short.empty):
                         self.holdings = {'long': df_long, 'short': df_short, 'date': d_check, 'contract': contract}
                         print(f"  - 持仓数据: 获取成功 (合约: {contract}, 日期: {d_check})")
                         return
                 except: pass
        except Exception as e:
             print(f"  ⚠️ 持仓数据获取受限: {e}")

    def analyze(self):
        if self.history_data is None or self.history_data.empty:
            print("❌ 无法分析: 无行情数据")
            return
        print("\n🧠 开始深度分析...")
        self._analyze_trend()
        self._analyze_volatility()
        self._analyze_fundamentals()
        self._analyze_basis()
        self._analyze_holdings()
        self._generate_conclusion()

    def _analyze_trend(self):
        df = self.history_data.copy()
        close = df['收盘价']
        df['MA5'] = close.rolling(5).mean()
        df['MA20'] = close.rolling(20).mean()
        df['MA60'] = close.rolling(60).mean()
        
        current = df.iloc[-1]
        
        if current['收盘价'] > current['MA5'] > current['MA20'] > current['MA60']:
            self.signals.append({'type': 'bull', 'msg': '均线多头排列', 'score': 15})
        elif current['收盘价'] < current['MA5'] < current['MA20'] < current['MA60']:
            self.signals.append({'type': 'bear', 'msg': '均线空头排列', 'score': -15})
            
        exp12 = close.ewm(span=12, adjust=False).mean()
        exp26 = close.ewm(span=26, adjust=False).mean()
        macd = exp12 - exp26
        signal = macd.ewm(span=9, adjust=False).mean()
        hist = macd - signal
        
        curr_hist = hist.iloc[-1]; prev_hist = hist.iloc[-2]
        if curr_hist > 0 and prev_hist < 0: self.signals.append({'type': 'bull', 'msg': 'MACD金叉', 'score': 10})
        elif curr_hist < 0 and prev_hist > 0: self.signals.append({'type': 'bear', 'msg': 'MACD死叉', 'score': -10})
        
        self.history_data = df

    def _analyze_volatility(self):
        df = self.history_data
        delta = df['收盘价'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        curr_rsi = rsi.iloc[-1]
        
        if curr_rsi > 80: self.signals.append({'type': 'risk', 'msg': f'RSI超买({curr_rsi:.1f})', 'score': -5})
        elif curr_rsi < 20: self.signals.append({'type': 'opp', 'msg': f'RSI超卖({curr_rsi:.1f})', 'score': 5})
        
        df['log_ret'] = np.log(df['收盘价'] / df['收盘价'].shift(1))
        volatility = df['log_ret'].rolling(20).std() * np.sqrt(242)
        vol_rank = volatility.rolling(242).rank(pct=True).iloc[-1]
        if vol_rank > 0.9: self.signals.append({'type': 'info', 'msg': f'波动率极高({vol_rank:.0%})', 'score': 0})

    def _analyze_fundamentals(self):
        if self.inventory is not None and not self.inventory.empty:
            curr = self.inventory.iloc[-1]['库存']
            prev = self.inventory.iloc[-2]['库存'] if len(self.inventory) > 1 else curr
            chg = (curr - prev) / prev
            inv_series = self.inventory['库存'].tail(52)
            rank = (curr - inv_series.min()) / (inv_series.max() - inv_series.min() + 1e-6)
            
            if rank < 0.2 and chg < 0: self.signals.append({'type': 'bull', 'msg': f'低库存+去库({chg:.1%})', 'score': 10})
            elif rank > 0.8 and chg > 0: self.signals.append({'type': 'bear', 'msg': f'高库存+累库({chg:.1%})', 'score': -10})

    def _analyze_basis(self):
        if self.spot_price:
            basis = self.spot_price.get('dom_basis', 0)
            spot = self.spot_price.get('spot_price', 1)
            rate = basis / spot if spot else 0
            if rate > 0.02: self.signals.append({'type': 'bull', 'msg': f'深贴水({rate:.1%})', 'score': 10})
            elif rate < -0.02: self.signals.append({'type': 'bear', 'msg': f'深升水({rate:.1%})', 'score': -10})

    def _analyze_holdings(self):
        if self.holdings and 'long' in self.holdings:
            try:
                df_long = self.holdings['long']
                df_short = self.holdings['short']
                v_long = df_long.iloc[:, 2].apply(lambda x: float(x) if str(x).replace('.','').isdigit() else 0).sum()    
                v_short = df_short.iloc[:, 2].apply(lambda x: float(x) if str(x).replace('.','').isdigit() else 0).sum()  
                if v_long + v_short > 0:
                    ratio = (v_long - v_short) / (v_long + v_short)
                    if ratio > 0.05: self.signals.append({'type': 'bull', 'msg': f'主力净多({ratio:.1%})', 'score': 5})
                    elif ratio < -0.05: self.signals.append({'type': 'bear', 'msg': f'主力净空({ratio:.1%})', 'score': -5})
            except: pass

    def _generate_conclusion(self):
        final_score = self.score + sum(s['score'] for s in self.signals)
        final_score = max(0, min(100, final_score))
        sug = "观望"
        if final_score >= 80: sug = "强力做多"
        elif final_score >= 60: sug = "做多"
        elif final_score <= 20: sug = "强力做空"
        elif final_score <= 40: sug = "做空"
        
        self.final_report = {'final_score': final_score, 'suggestion': sug, 'signals': self.signals}
        print(f"\n📊 综合评分: {final_score:.0f} [{sug}]")
        for s in self.signals: print(f"  - {s['msg']} ({s['score']:+})")

    def plot_analysis(self):
        if self.history_data is None: return
        df = self.history_data.tail(242)
        plt.figure(figsize=(16, 12)); plt.clf()
        
        ax1 = plt.subplot(211)
        ax1.plot(df['日期'], df['收盘价'], label='Price')
        ax1.plot(df['日期'], df['MA20'], label='MA20')
        ax1.plot(df['日期'], df['MA60'], label='MA60')
        ax1.set_title(f"{self.name} ({self.symbol}) 期货分析")
        ax1.legend()
        
        ax2 = plt.subplot(212, sharex=ax1)
        if self.inventory is not None:
            inv = self.inventory.set_index('日期').reindex(df['日期'], method='ffill')
            ax2.fill_between(inv.index, inv['库存'], color='green', alpha=0.3, label='库存')
            ax2.legend()
        
        file_path = f"期货报告_{self.symbol}_{datetime.now().strftime('%Y%m%d')}.png"
        plt.savefig(file_path, bbox_inches='tight')
        print(f"📈 图表已保存: {file_path}")


def main():
    """主函数"""
    print("="*50)
    print("      Analysis Pro 投资分析工具 v3.0 (Stock/Futures)")
    print("      (支持: A股深度分析 / 期货全维分析)")
    print("="*50)

    if len(sys.argv) < 2:
        print("\\n[使用说明]")
        print("用法: python stock_analysis_v2.py <代码>")
        print("示例:")
        print("  A股: 600519 (茅台), 000858 (五粮液)")
        print("  期货: 螺纹钢, 黄金, 沪铜, RB, AU, CU")
        
        code = input("\\n请输入代码或名称: ").strip()
        if not code:
            code = "002683"
    else:
        code = sys.argv[1]
    
    start_time = time.time()
    
    # 1. 判断是否为期货 (检查是否在映射表中 或 包含字母)
    is_futures = False
    
    # 检查中文名
    if code in FUTURES_MAPPING: is_futures = True
    # 检查代码 (字母开头通常是期货，如 RB, AU; 数字开头是股票)
    elif code[0].isalpha() or code.upper() in [v['symbol'] for v in FUTURES_MAPPING.values()]: is_futures = True
    
    if is_futures:
        # ----- 期货模式 -----
        print(f"\\n🚀 启动期货分析模式: {code}")
        try:
            analyzer = FuturesAnalyzer(code)
            analyzer.fetch_all_data()
            analyzer.analyze()
            analyzer.plot_analysis()
        except Exception as e:
            print(f"\\n❌ 期货分析出错: {e}")
            import traceback; traceback.print_exc()
            
    else:
        # ----- A股模式 -----
        print(f"\\n🚀 启动A股分析模式: {code}")
        try:
            analyzer = StockAnalyzer(code)
            analyzer.fetch_data()
            
            # 分析阶段
            # 1. 增量分析
            analyzer.analyze_growth_momentum()
            
            # 2. 公司深度分析
            analyzer.analyze_company()
            
            # 3. 财报解读
            analyzer.analyze_financial_report()
            
            # 4. 回测 (可选，耗时较长)
            analyzer.run_backtest()
            
            analyzer.generate_summary()
        except Exception as e:
            print(f"\\n❌ A股分析出错: {e}")
            import traceback; traceback.print_exc()
    
    total_time = time.time() - start_time
    print(f"\\n⏱️ 总耗时: {total_time:.1f}s")


if __name__ == "__main__":
    main()
