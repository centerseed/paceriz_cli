"""
創建測試訂閱數據

在 havital-dev 環境創建一個測試用戶和訂閱，用於測試 Admin Backend UI
"""
import sys
import os
from datetime import datetime, timedelta, timezone

# 添加 api_service 到 Python path
API_SERVICE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../api_service'))
sys.path.insert(0, API_SERVICE_PATH)

from firebase_admin import firestore, auth
from core.infrastructure.firebase_init import init_firebase

# 初始化 Firebase
init_firebase()
db = firestore.client()

def create_test_data():
    """創建測試用戶和訂閱數據"""

    # 測試用戶信息
    test_email = "test-user@example.com"
    test_uid = None

    print("🔍 檢查測試用戶是否存在...")

    # 檢查用戶是否已存在
    try:
        user = auth.get_user_by_email(test_email)
        test_uid = user.uid
        print(f"✅ 測試用戶已存在: {test_email} (UID: {test_uid})")
    except auth.UserNotFoundError:
        # 創建新用戶
        print(f"📝 創建新測試用戶: {test_email}")
        user = auth.create_user(
            email=test_email,
            password="Test123456!",
            display_name="測試用戶"
        )
        test_uid = user.uid
        print(f"✅ 測試用戶已創建: {test_email} (UID: {test_uid})")

    # 創建用戶文檔
    user_data = {
        'uid': test_uid,
        'email': test_email,
        'display_name': '測試用戶',
        'created_at': datetime.now(timezone.utc),
        'is_admin': False
    }
    db.collection('users').document(test_uid).set(user_data, merge=True)
    print(f"✅ 用戶文檔已更新: users/{test_uid}")

    # 創建訂閱數據
    now = datetime.now(timezone.utc)
    trial_start = now - timedelta(days=3)  # 3天前開始試用
    trial_end = trial_start + timedelta(days=14)  # 14天試用期

    subscription_data = {
        'uid': test_uid,
        'is_premium': False,
        'trial_days': 14,
        'trial_start_at': trial_start,
        'trial_end_at': trial_end,
        'premium_start_at': None,
        'premium_end_at': None,
        'total_extension_days': 0,
        'created_at': trial_start,
        'updated_at': now,
        'stripe_customer_id': None,
        'stripe_subscription_id': None
    }

    db.collection('subscriptions').document(test_uid).set(subscription_data, merge=True)
    print(f"✅ 訂閱已創建: subscriptions/{test_uid}")
    print(f"   - 試用期: {trial_start.strftime('%Y-%m-%d')} ~ {trial_end.strftime('%Y-%m-%d')}")
    print(f"   - 剩餘天數: {(trial_end - now).days} 天")

    # 創建第二個測試用戶（付費用戶）
    test_email_2 = "test-premium@example.com"
    test_uid_2 = None

    print("\n🔍 檢查第二個測試用戶是否存在...")

    try:
        user_2 = auth.get_user_by_email(test_email_2)
        test_uid_2 = user_2.uid
        print(f"✅ 付費測試用戶已存在: {test_email_2} (UID: {test_uid_2})")
    except auth.UserNotFoundError:
        print(f"📝 創建付費測試用戶: {test_email_2}")
        user_2 = auth.create_user(
            email=test_email_2,
            password="Test123456!",
            display_name="付費測試用戶"
        )
        test_uid_2 = user_2.uid
        print(f"✅ 付費測試用戶已創建: {test_email_2} (UID: {test_uid_2})")

    # 創建付費用戶文檔
    user_data_2 = {
        'uid': test_uid_2,
        'email': test_email_2,
        'display_name': '付費測試用戶',
        'created_at': datetime.now(timezone.utc),
        'is_admin': False
    }
    db.collection('users').document(test_uid_2).set(user_data_2, merge=True)
    print(f"✅ 付費用戶文檔已更新: users/{test_uid_2}")

    # 創建付費訂閱數據
    premium_start = now - timedelta(days=30)  # 30天前開始付費
    premium_end = now + timedelta(days=335)  # 還剩335天

    subscription_data_2 = {
        'uid': test_uid_2,
        'is_premium': True,
        'trial_days': 14,
        'trial_start_at': premium_start - timedelta(days=14),
        'trial_end_at': premium_start,
        'premium_start_at': premium_start,
        'premium_end_at': premium_end,
        'total_extension_days': 0,
        'created_at': premium_start - timedelta(days=14),
        'updated_at': now,
        'stripe_customer_id': 'cus_test_123456',
        'stripe_subscription_id': 'sub_test_123456'
    }

    db.collection('subscriptions').document(test_uid_2).set(subscription_data_2, merge=True)
    print(f"✅ 付費訂閱已創建: subscriptions/{test_uid_2}")
    print(f"   - 付費期: {premium_start.strftime('%Y-%m-%d')} ~ {premium_end.strftime('%Y-%m-%d')}")
    print(f"   - 剩餘天數: {(premium_end - now).days} 天")

    print("\n" + "=" * 60)
    print("✅ 測試數據創建完成！")
    print("=" * 60)
    print(f"\n測試用戶 1 (試用中):")
    print(f"  Email: {test_email}")
    print(f"  Password: Test123456!")
    print(f"  UID: {test_uid}")
    print(f"\n測試用戶 2 (付費會員):")
    print(f"  Email: {test_email_2}")
    print(f"  Password: Test123456!")
    print(f"  UID: {test_uid_2}")
    print(f"\n您現在可以在 Admin UI 中看到這些訂閱並進行管理")


if __name__ == '__main__':
    create_test_data()
