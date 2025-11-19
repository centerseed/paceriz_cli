#!/usr/bin/env python3
"""
檢查 Firestore 中的 rolling_trends 數據
"""
import os
os.environ['GOOGLE_CLOUD_PROJECT'] = 'paceriz-prod'

from utils.firebase_init import init_firebase
from firebase_admin import firestore
import json

# 初始化 Firebase
init_firebase()
db = firestore.client()

# 測試用戶 UID
test_uid = 'E4IU0VafRAdlNXoVHFzN0LZmOZ82'

print(f"檢查 rolling_trends/{test_uid}")
print("=" * 80)

# 查詢 rolling_trends
rolling_trends_ref = db.collection('rolling_trends').document(test_uid)
rolling_trends_doc = rolling_trends_ref.get()

if rolling_trends_doc.exists:
    print("✅ 找到 rolling_trends 文檔")
    print()

    data = rolling_trends_doc.to_dict()

    # 檢查每個指標
    for metric in ['speed', 'endurance', 'race_fitness', 'training_load', 'recovery']:
        print(f"\n📊 {metric}:")
        if metric in data:
            metric_data = data[metric]
            if isinstance(metric_data, dict):
                # 顯示 trend_data 結構
                if 'dates' in metric_data:
                    print(f"   dates: {len(metric_data['dates'])} 個日期")
                    print(f"   第一個: {metric_data['dates'][0] if metric_data['dates'] else 'N/A'}")
                    print(f"   最後一個: {metric_data['dates'][-1] if metric_data['dates'] else 'N/A'}")
                if 'values' in metric_data:
                    print(f"   values: {len(metric_data['values'])} 個數值")
                    if metric_data['values']:
                        print(f"   範圍: {min(metric_data['values']):.1f} - {max(metric_data['values']):.1f}")
                if 'direction' in metric_data:
                    print(f"   direction: {metric_data['direction']}")

                # 顯示完整數據結構（前 3 個鍵）
                print(f"   鍵: {list(metric_data.keys())[:5]}")
            else:
                print(f"   ⚠️  不是字典類型: {type(metric_data)}")
        else:
            print(f"   ❌ 不存在")

    # 顯示完整的文檔結構（縮短版）
    print("\n" + "=" * 80)
    print("完整文檔鍵:")
    print(list(data.keys()))

else:
    print("❌ 沒有找到 rolling_trends 文檔")
    print()
    print("檢查 collection 中是否有任何文檔...")

    # 列出 rolling_trends collection 中的所有文檔
    all_docs = list(db.collection('rolling_trends').limit(5).stream())
    if all_docs:
        print(f"找到 {len(all_docs)} 個文檔:")
        for doc in all_docs:
            print(f"  - {doc.id}")
    else:
        print("rolling_trends collection 是空的")
