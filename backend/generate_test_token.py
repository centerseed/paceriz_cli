#!/usr/bin/env python3
"""
生成測試用 Firebase ID Token（用於 dev 環境）

在 dev 環境中，firebase_init.py 的 monkey-patch 會接受任何 JWT token
並從中提取 uid 和 email。
"""
import jwt
from datetime import datetime, timedelta

def generate_test_token(uid: str, email: str):
    """
    生成測試用 JWT token

    Args:
        uid: 用戶 UID
        email: 用戶 Email

    Returns:
        JWT token string
    """
    payload = {
        'uid': uid,
        'user_id': uid,
        'sub': uid,
        'email': email,
        'email_verified': True,
        'iat': int(datetime.utcnow().timestamp()),
        'exp': int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
        'aud': 'havital-dev',
        'iss': 'https://securetoken.google.com/havital-dev'
    }

    # 在 dev 模式下，簽名不重要（不會被驗證）
    token = jwt.encode(payload, 'dev-secret', algorithm='HS256')
    return token

if __name__ == '__main__':
    # 生成 super admin token
    super_admin_email = 'centerseedwu@gmail.com'
    super_admin_uid = 'test-super-admin-uid'

    token = generate_test_token(super_admin_uid, super_admin_email)

    print("=" * 80)
    print("🔑 測試用 Firebase ID Token")
    print("=" * 80)
    print(f"Email: {super_admin_email}")
    print(f"UID: {super_admin_uid}")
    print(f"Role: Super Admin")
    print("-" * 80)
    print(f"Token: {token}")
    print("=" * 80)
    print()
    print("使用方式:")
    print(f'curl -H "Authorization: Bearer {token}" \\')
    print("     http://127.0.0.1:8080/api/v1/admin/subscriptions")
    print()
