#!/usr/bin/env python3
"""
檢查 Firestore 中是否有 readiness 數據
"""
import os
os.environ['GOOGLE_CLOUD_PROJECT'] = 'paceriz-prod'

from utils.firebase_init import init_firebase
from firebase_admin import firestore

# 初始化 Firebase
init_firebase()
db = firestore.client()

# 測試用戶 UID
test_uid = 'E4IU0VafRAdlNXoVHFzN0LZmOZ82'

print(f"檢查用戶 {test_uid} 的 readiness 數據...")
print()

# 查詢 users/{uid}/training_readiness 子集合
readiness_ref = db.collection('users').document(test_uid).collection('training_readiness')

print("📊 查詢所有 readiness 文檔...")
all_docs = list(readiness_ref.limit(10).stream())

if not all_docs:
    print("❌ 沒有找到任何 readiness 數據")
    print()
    print("檢查用戶文檔是否存在...")
    user_doc = db.collection('users').document(test_uid).get()
    if user_doc.exists:
        print(f"✅ 用戶文檔存在")
        user_data = user_doc.to_dict()
        print(f"   Email: {user_data.get('email')}")
        print(f"   Display Name: {user_data.get('display_name')}")
    else:
        print(f"❌ 用戶文檔不存在")
else:
    print(f"✅ 找到 {len(all_docs)} 個 readiness 文檔:")
    print()

    for doc in all_docs:
        print(f"📄 文檔 ID: {doc.id}")
        data = doc.to_dict()

        # 顯示所有欄位
        for key in ['speed', 'endurance', 'race_fitness', 'training_load', 'recovery']:
            if key in data:
                metric = data[key]
                if isinstance(metric, dict):
                    score = metric.get('score', 'N/A')
                    print(f"   {key}: {score}")
                else:
                    print(f"   {key}: {metric}")
        print()
