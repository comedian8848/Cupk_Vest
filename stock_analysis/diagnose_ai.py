#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 配置诊断脚本
"""
import os
import sys
import json

def diagnose():
    print("=" * 50)
    print("🤖 AI Configuration Diagnosis")
    print("=" * 50)
    
    # 1. Check Environment Variables
    print("\n[1] Checking Environment Variables...")
    env_vars = [
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_BASE_URL",
        "ANTHROPIC_MODEL",
        "API_TIMEOUT_MS",
        "HTTP_PROXY",
        "HTTPS_PROXY"
    ]
    
    config = {}
    for var in env_vars:
        value = os.getenv(var)
        config[var] = value
        status = "✅ Set" if value else "⚠️ Not Set"
        masked_value = value[:8] + "..." if value and "KEY" in var else value
        print(f"  - {var}: {status} ({masked_value})")

    if not config["ANTHROPIC_API_KEY"]:
        print("\n❌ Error: ANTHROPIC_API_KEY is missing!")
        print("Please set it in your .env file or environment.")
        return

    # 2. Check Client Initialization
    print("\n[2] Testing Client Initialization...")
    try:
        from ai_client import UnifiedAIClient
        client = UnifiedAIClient()
        print("✅ UnifiedAIClient initialized successfully")
    except ImportError:
        print("❌ Error: Could not import UnifiedAIClient. Check ai_client.py")
        return
    except Exception as e:
        print(f"❌ Error initializing client: {e}")
        return

    # 3. Test API Call
    print("\n[3] Testing API Call (Simple Hello)...")
    try:
        response = client.analyze("Say 'Hello' in JSON format: {'message': 'Hello'}")
        print("✅ API Call Successful!")
        print(f"Response: {response}")
    except Exception as e:
        print(f"❌ API Call Failed: {e}")

if __name__ == "__main__":
    diagnose()
