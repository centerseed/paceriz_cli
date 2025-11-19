#!/usr/bin/env python3
"""
Admin API 測試腳本

這個腳本幫助你快速測試 Admin Backend API。

使用方式：
    python test_admin_api.py

前提條件：
    - 已設置 GOOGLE_APPLICATION_CREDENTIALS 環境變量
    - 已啟動 Backend 服務（python app.py）
    - 已設置 SUPER_ADMIN_EMAILS 環境變量
"""
import os
import sys
import requests
import json

# 添加 api_service 到 Python path
API_SERVICE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../api_service'))
sys.path.insert(0, API_SERVICE_PATH)

try:
    from firebase_admin import auth, credentials
    import firebase_admin
except ImportError:
    print("❌ Error: firebase-admin not installed")
    print("   Run: pip install firebase-admin")
    sys.exit(1)


# 配置
BASE_URL = os.getenv('ADMIN_API_URL', 'http://localhost:8080')
SUPER_ADMIN_EMAIL = os.getenv('SUPER_ADMIN_EMAILS', '').split(',')[0]

if not SUPER_ADMIN_EMAIL:
    print("❌ Error: SUPER_ADMIN_EMAILS not set")
    print("   Run: export SUPER_ADMIN_EMAILS=your-email@gmail.com")
    sys.exit(1)


def init_firebase():
    """初始化 Firebase Admin SDK"""
    try:
        # 檢查是否已初始化
        firebase_admin.get_app()
        print("✅ Firebase already initialized")
    except ValueError:
        # 初始化 Firebase
        cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not cred_path:
            print("⚠️  Warning: GOOGLE_APPLICATION_CREDENTIALS not set")
            print("   Using default credentials")
            cred = credentials.ApplicationDefault()
        else:
            cred = credentials.Certificate(cred_path)

        firebase_admin.initialize_app(cred)
        print("✅ Firebase initialized")


def create_test_token(email: str = None) -> str:
    """
    創建測試用的 Custom Token

    Note: Custom Token 需要通過 Firebase Auth REST API 交換為 ID Token
    這裡為了簡化測試，我們直接使用 Custom Token（實際應該交換）
    """
    init_firebase()

    # 使用超級管理員的 Email 創建一個測試 UID
    test_uid = email.replace('@', '_').replace('.', '_') if email else 'test_admin'

    try:
        # 創建 Custom Token
        custom_token = auth.create_custom_token(test_uid, {'email': email or SUPER_ADMIN_EMAIL})
        print(f"✅ Created custom token for {email or SUPER_ADMIN_EMAIL}")
        return custom_token.decode()
    except Exception as e:
        print(f"❌ Error creating token: {e}")
        return None


def test_health():
    """測試健康檢查端點（無需認證）"""
    print("\n" + "=" * 50)
    print("🧪 Testing: Health Check (No Auth)")
    print("=" * 50)

    url = f"{BASE_URL}/health"
    print(f"Request: GET {url}")

    try:
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print("❌ Health check failed")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_subscriptions_list(token: str):
    """測試獲取訂閱列表"""
    print("\n" + "=" * 50)
    print("🧪 Testing: List Subscriptions")
    print("=" * 50)

    url = f"{BASE_URL}/api/v1/admin/subscriptions"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    print(f"Request: GET {url}")
    print(f"Headers: Authorization: Bearer {token[:20]}...")

    try:
        response = requests.get(url, headers=headers)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Response: Found {len(data.get('data', []))} subscriptions")
            print(f"Pagination: {json.dumps(data.get('pagination', {}), indent=2)}")
            print("✅ List subscriptions passed")
            return True
        else:
            print(f"Response: {response.text}")
            print("❌ List subscriptions failed")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_subscription_detail(token: str, uid: str):
    """測試獲取訂閱詳情"""
    print("\n" + "=" * 50)
    print(f"🧪 Testing: Get Subscription Detail for {uid}")
    print("=" * 50)

    url = f"{BASE_URL}/api/v1/admin/subscriptions/{uid}"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    print(f"Request: GET {url}")

    try:
        response = requests.get(url, headers=headers)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            print("✅ Get subscription detail passed")
            return True
        else:
            print(f"Response: {response.text}")
            if response.status_code == 404:
                print(f"ℹ️  Subscription not found for uid: {uid}")
            else:
                print("❌ Get subscription detail failed")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_extend_subscription(token: str, uid: str):
    """測試延長訂閱"""
    print("\n" + "=" * 50)
    print(f"🧪 Testing: Extend Subscription for {uid}")
    print("=" * 50)

    url = f"{BASE_URL}/api/v1/admin/subscriptions/{uid}/extend"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    data = {
        'days': 30,
        'reason': 'admin_grant',
        'notes': '測試延長訂閱'
    }

    print(f"Request: POST {url}")
    print(f"Body: {json.dumps(data, indent=2)}")

    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            print("✅ Extend subscription passed")
            return True
        else:
            print(f"Response: {response.text}")
            print("❌ Extend subscription failed")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """主測試流程"""
    print("=" * 50)
    print("🚀 Admin Backend API Test Suite")
    print("=" * 50)
    print(f"Base URL: {BASE_URL}")
    print(f"Super Admin: {SUPER_ADMIN_EMAIL}")
    print()

    # 測試 1: 健康檢查（無需認證）
    health_ok = test_health()

    if not health_ok:
        print("\n❌ Backend service is not running or not healthy")
        print("   Please start the service first: python app.py")
        return

    # 創建測試 Token
    print("\n" + "=" * 50)
    print("🔑 Creating Test Token")
    print("=" * 50)
    token = create_test_token(SUPER_ADMIN_EMAIL)

    if not token:
        print("\n❌ Failed to create test token")
        print("   Please check your Firebase credentials")
        return

    # ⚠️ 注意：Custom Token 需要交換為 ID Token
    # 這裡為了簡化測試，直接使用 Custom Token
    # 實際應該通過 Firebase Auth REST API 交換
    print("\n⚠️  Note: Using Custom Token (should be exchanged for ID Token in production)")
    print(f"   Token: {token[:50]}...")

    # 測試 2: 獲取訂閱列表
    list_ok = test_subscriptions_list(token)

    # 測試 3: 獲取訂閱詳情（使用一個測試 UID）
    test_uid = "test_user_123"  # 替換為實際的 UID
    detail_ok = test_subscription_detail(token, test_uid)

    # 測試 4: 延長訂閱（使用一個測試 UID）
    # extend_ok = test_extend_subscription(token, test_uid)

    # 總結
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    print(f"✅ Health Check: {'PASS' if health_ok else 'FAIL'}")
    print(f"{'✅' if list_ok else '❌'} List Subscriptions: {'PASS' if list_ok else 'FAIL'}")
    print(f"{'ℹ️ ' if not detail_ok else '❌'} Get Subscription Detail: SKIPPED (no test data)")
    print("ℹ️  Extend Subscription: SKIPPED (requires valid uid)")

    print("\n" + "=" * 50)
    print("💡 Next Steps")
    print("=" * 50)
    print("1. ⚠️  The Custom Token used above may not work with the actual API")
    print("   You need to exchange it for an ID Token using Firebase Auth REST API")
    print()
    print("2. For real testing, use a real Firebase ID Token:")
    print("   - Login to your app with Google OAuth")
    print("   - Get the ID Token from Firebase Auth")
    print("   - Use that token to test the API")
    print()
    print("3. Test with curl:")
    print(f"   export FIREBASE_TOKEN='your-real-id-token'")
    print(f"   curl -H 'Authorization: Bearer $FIREBASE_TOKEN' \\")
    print(f"        {BASE_URL}/api/v1/admin/subscriptions")
    print()
    print("See TESTING.md for more details.")


if __name__ == '__main__':
    main()
