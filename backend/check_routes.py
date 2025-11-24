#!/usr/bin/env python3
"""
檢查 Flask app 的所有已註冊路由
"""
import sys
import os

# 設置環境變量
os.environ['GOOGLE_CLOUD_PROJECT'] = 'paceriz-prod'
os.environ['SUPER_ADMIN_EMAILS'] = 'centerseedwu@gmail.com'
os.environ['ENV_TYPE'] = 'prod'

# 添加 backend 到 path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 導入 app
from app import app

print("=" * 80)
print("所有已註冊的路由:")
print("=" * 80)

# 列出所有路由
for rule in app.url_map.iter_rules():
    methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
    print(f"{rule.endpoint:50s} {methods:20s} {rule.rule}")

print()
print("=" * 80)
print("搜尋 readiness 相關路由:")
print("=" * 80)

readiness_routes = [rule for rule in app.url_map.iter_rules() if 'readiness' in rule.rule]
if readiness_routes:
    for rule in readiness_routes:
        methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        print(f"✅ {rule.endpoint:50s} {methods:20s} {rule.rule}")
else:
    print("❌ 沒有找到 readiness 路由！")
