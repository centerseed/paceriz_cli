"""
測試管理員認證中介層
"""
import pytest
from unittest.mock import patch, Mock


def test_require_admin_decorator_without_token(client):
    """測試沒有 token 時的請求"""
    response = client.get('/api/v1/admin/subscriptions')

    # 應該返回 401 Unauthorized
    assert response.status_code == 401


def test_require_admin_decorator_with_invalid_token(client):
    """測試使用無效 token 的請求"""
    headers = {
        'Authorization': 'Bearer invalid_token_123'
    }

    with patch('firebase_admin.auth.verify_id_token') as mock_verify:
        # 模擬 token 驗證失敗
        mock_verify.side_effect = Exception("Invalid token")

        response = client.get('/api/v1/admin/subscriptions', headers=headers)

        # 應該返回 401 Unauthorized
        assert response.status_code == 401


def test_require_admin_decorator_with_non_admin_user(client, mock_firestore):
    """測試非管理員用戶的請求"""
    headers = {
        'Authorization': 'Bearer valid_token_but_not_admin'
    }

    with patch('firebase_admin.auth.verify_id_token') as mock_verify:
        # 模擬驗證成功，但用戶不是管理員
        mock_verify.return_value = {
            'uid': 'normal_user_123',
            'email': 'normal@example.com'
        }

        # Mock Firestore 返回非管理員用戶
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            'uid': 'normal_user_123',
            'email': 'normal@example.com',
            'is_admin': False
        }

        mock_firestore.collection.return_value.document.return_value.get.return_value = mock_doc

        response = client.get('/api/v1/admin/subscriptions', headers=headers)

        # 應該返回 403 Forbidden
        assert response.status_code == 403


def test_require_admin_decorator_with_super_admin(client, mock_firestore):
    """測試 Super Admin 的請求"""
    headers = {
        'Authorization': 'Bearer super_admin_token'
    }

    with patch('firebase_admin.auth.verify_id_token') as mock_verify:
        # 模擬驗證成功，且是 Super Admin
        mock_verify.return_value = {
            'uid': 'super_admin_uid',
            'email': 'centerseedwu@gmail.com'
        }

        # Mock Firestore 返回 Super Admin 用戶
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            'uid': 'super_admin_uid',
            'email': 'centerseedwu@gmail.com',
            'is_admin': True
        }

        # Mock subscriptions collection
        mock_firestore.collection.return_value.document.return_value.get.return_value = mock_doc
        mock_firestore.collection.return_value.stream.return_value = []

        response = client.get('/api/v1/admin/subscriptions', headers=headers)

        # 應該成功 (200)
        assert response.status_code == 200
