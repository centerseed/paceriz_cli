#!/usr/bin/env python3
"""
列出 admin_users_bp 的所有路由
"""
import sys
import os

# 添加 backend 到 path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from api.admin.users import admin_users_bp

print(f"Blueprint name: {admin_users_bp.name}")
print(f"Blueprint URL prefix: {admin_users_bp.url_prefix}")
print()
print("Registered routes:")

for rule in admin_users_bp.url_values_defaults or []:
    print(f"  - {rule}")

# 這個方法在 blueprint 註冊前不會顯示路由
# 我們需要檢查 deferred functions
print()
print(f"Number of deferred functions: {len(admin_users_bp.deferred_functions)}")
print()

# 讓我們手動檢查 blueprint 對象的所有屬性
import inspect
print("All routes defined in blueprint:")
for name, obj in inspect.getmembers(admin_users_bp):
    if name.startswith('_'):
        continue
    if callable(obj) and hasattr(obj, '__name__'):
        print(f"  - {name}: {obj}")
