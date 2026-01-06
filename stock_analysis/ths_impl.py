# -*- coding: utf-8 -*-
"""
同花顺数据接口实现 (基于 pywencai)
功能：
1. 获取同行业对比数据 (毛利率、增速、ROE、市值等)
2. 获取供应链数据 (前五大客户/供应商占比)

注意：pywencai 接口经常变动，且需要 Node.js 环境
建议优先使用 akshare，此模块仅作为补充数据源
"""

import pandas as pd
import time
from config import DATA_SOURCE_CONFIG

try:
    import pywencai
    HAS_PYWENCAI = True
except ImportError:
    HAS_PYWENCAI = False

# 配置开关检查
ENABLED = DATA_SOURCE_CONFIG.get('USE_TONGHUASHUN', False) and HAS_PYWENCAI

def check_dependencies():
    """检查是否安装了必要依赖"""
    if not ENABLED:
        if not HAS_PYWENCAI:
            print("ℹ️  未启用同花顺数据源（pywencai 未安装）")
        else:
            print("ℹ️  同花顺数据源已禁用（config.py 中 USE_TONGHUASHUN=False）")
        return False
    
    print("✓ 同花顺数据源已启用")
    return True

def get_industry_comparison(symbol):
    """
    获取同行业对比数据
    指标: 销售毛利率, 净利润增速, ROE, 总市值, 每股净资产
    
    注意：pywencai 0.9+ 版本返回格式已改为 dict，本函数暂不可用
    建议使用 akshare 的行业数据接口替代
    """
    if not ENABLED:
        return None
    
    # 构造自然语言查询语句
    query = f"{symbol}及同行业成分股 销售毛利率 净利润增长率 净资产收益率(摊薄) 总市值 每股净资产 所属同花顺行业"
    
    try:
        # ⚠️ pywencai 新版本返回 dict 而非 DataFrame，需要适配
        result = pywencai.get(query=query, loop=True)
        
        # 新版本处理（返回字典）
        if isinstance(result, dict):
            print("⚠️  pywencai 返回格式已变更为 dict，暂不支持解析")
            print(f"   可用键: {list(result.keys())}")
            return None
        
        # 旧版本处理（返回 DataFrame）
        df = result
        if df is None or df.empty:
            return None
            
        # 问财返回的列名通常很长（包含时间），需要模糊匹配清洗
        # 例如: "销售毛利率(20230930)" -> "销售毛利率"
        rename_map = {}
        for col in df.columns:
            if '销售毛利率' in col and '同行业' not in col:
                rename_map[col] = '毛利率'
            elif '净利润增长率' in col and '同行业' not in col:
                rename_map[col] = '净利增速'
            elif '净资产收益率' in col and '同行业' not in col:
                rename_map[col] = 'ROE'
            elif '总市值' in col and '同行业' not in col:
                rename_map[col] = '总市值'
            elif '每股净资产' in col and '同行业' not in col:
                rename_map[col] = 'BVPS'
            elif '股票代码' in col:
                rename_map[col] = '代码'
            elif '股票简称' in col:
                rename_map[col] = '名称'
                
        df = df.rename(columns=rename_map)
        
        # 保留关键列
        required_cols = ['代码', '名称', '毛利率', '净利增速', 'ROE', '总市值', 'BVPS']
        # 过滤掉不存在的列
        final_cols = [c for c in required_cols if c in df.columns]
        
        result_df = df[final_cols].copy()
        
        # 数据类型转换
        for col in ['毛利率', '净利增速', 'ROE', '总市值', 'BVPS']:
            if col in result_df.columns:
                result_df[col] = pd.to_numeric(result_df[col], errors='coerce')
        
        # 按市值排序
        if '总市值' in result_df.columns:
            result_df = result_df.sort_values('总市值', ascending=False)
            
        return result_df
        
    except Exception as e:
        print(f"⚠ 获取同行业对比失败: {e}")
        return None

def get_supply_chain_info(symbol):
    """
    获取前五大客户/供应商占比
    
    注意：pywencai 新版本接口已变更，暂不可用
    """
    if not ENABLED:
        return None
        
    query = f"{symbol} 前五大客户占比 前五大供应商占比"
    
    try:
        df = pywencai.get(query=query, loop=False)
        if df is None or df.empty:
            return None
            
        # 清洗列名
        result = {}
        for col in df.columns:
            if '前五大客户' in col and '占比' in col:
                val = df.iloc[0][col]
                result['top5_customers_pct'] = val
            if '前五大供应商' in col and '占比' in col:
                val = df.iloc[0][col]
                result['top5_suppliers_pct'] = val
                
        return result
    except Exception as e:
        print(f"⚠ 获取供应链数据失败: {e}")
        return None

if __name__ == "__main__":
    # 测试代码
    if check_dependencies():
        print("Testing 002683...")
        print(get_industry_comparison("002683"))
        print(get_supply_chain_info("002683"))
