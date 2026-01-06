#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试同花顺（pywencai）接口是否可用
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_pywencai_basic():
    """测试 pywencai 基础功能"""
    print("=" * 60)
    print("测试 1: 检查 pywencai 是否安装")
    print("=" * 60)
    
    try:
        import pywencai
        print("✓ pywencai 已安装")
    except ImportError as e:
        print(f"✗ pywencai 未安装: {e}")
        print("\n安装方法: pip install pywencai")
        print("注意: 需要系统安装 Node.js 环境")
        return False
    
    print("\n" + "=" * 60)
    print("测试 2: 简单查询测试")
    print("=" * 60)
    
    try:
        result = pywencai.get(query='贵州茅台 总市值', loop=False)
        print(f"✓ 查询成功")
        print(f"  返回类型: {type(result)}")
        
        if isinstance(result, dict):
            print(f"  返回的键: {list(result.keys())[:5]}...")
            print("\n⚠️  pywencai 新版本返回 dict 而非 DataFrame")
            print("   当前代码需要适配新版接口格式")
        else:
            print(f"  返回列: {result.columns.tolist() if hasattr(result, 'columns') else 'N/A'}")
            
    except Exception as e:
        print(f"✗ 查询失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("测试 3: 同行业对比查询")
    print("=" * 60)
    
    try:
        query = "600519及同行业成分股 销售毛利率 净利润增长率 净资产收益率 总市值"
        result = pywencai.get(query=query, loop=False)
        print(f"✓ 行业对比查询成功")
        print(f"  返回类型: {type(result)}")
        
        if isinstance(result, dict):
            print(f"  可用键: {list(result.keys())}")
        
    except Exception as e:
        print(f"✗ 行业对比查询失败: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("结论")
    print("=" * 60)
    print("✓ pywencai 基础功能正常")
    print("✗ 但接口格式已变更（dict 而非 DataFrame）")
    print("\n建议:")
    print("1. 暂时禁用同花顺数据源（config.py 中 USE_TONGHUASHUN=False）")
    print("2. 等待 pywencai 接口稳定或改用其他数据源")
    print("3. 或者重写 ths_impl.py 适配新版 dict 格式")
    
    return True

if __name__ == "__main__":
    test_pywencai_basic()
