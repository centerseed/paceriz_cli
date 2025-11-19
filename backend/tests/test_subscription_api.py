"""
測試訂閱管理 API
"""
import pytest
from unittest.mock import patch, Mock
from datetime import datetime, timedelta, timezone


@pytest.fixture
def authorized_headers():
    """提供已授權的 headers"""
    return {
        'Authorization': 'Bearer test_admin_token',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def mock_admin_auth():
    """Mock 管理員認證"""
    with patch('firebase_admin.auth.verify_id_token') as mock_verify:
        mock_verify.return_value = {
            'uid': 'admin_uid',
            'email': 'centerseedwu@gmail.com'
        }
        yield mock_verify


def test_list_subscriptions_requires_auth(client):
    """測試列表訂閱需要認證"""
    response = client.get('/api/v1/admin/subscriptions')
    assert response.status_code == 401


def test_list_subscriptions_success(client, authorized_headers, mock_admin_auth, mock_firestore):
    """測試成功獲取訂閱列表"""
    # Mock Firestore 返回訂閱數據
    mock_doc1 = Mock()
    mock_doc1.id = 'user_1'
    mock_doc1.to_dict.return_value = {
        'uid': 'user_1',
        'is_premium': True
    }

    mock_doc2 = Mock()
    mock_doc2.id = 'user_2'
    mock_doc2.to_dict.return_value = {
        'uid': 'user_2',
        'is_premium': False
    }

    # Mock users collection
    mock_user_doc = Mock()
    mock_user_doc.exists = True
    mock_user_doc.to_dict.return_value = {
        'email': 'test@example.com',
        'display_name': 'Test User'
    }

    mock_firestore.collection.return_value.stream.return_value = [mock_doc1, mock_doc2]
    mock_firestore.collection.return_value.document.return_value.get.return_value = mock_user_doc

    response = client.get('/api/v1/admin/subscriptions', headers=authorized_headers)

    assert response.status_code == 200
    data = response.get_json()
    assert 'data' in data
    assert 'pagination' in data


def test_get_subscription_detail_not_found(client, authorized_headers, mock_admin_auth, mock_firestore):
    """測試獲取不存在的訂閱"""
    with patch('domains.subscription.subscription_service.subscription_service.get_subscription_summary') as mock_get:
        mock_get.return_value = None

        response = client.get('/api/v1/admin/subscriptions/nonexistent_uid', headers=authorized_headers)

        assert response.status_code == 404


def test_extend_subscription_invalid_days(client, authorized_headers, mock_admin_auth):
    """測試延長訂閱 - 無效的天數"""
    data = {
        'days': -10,  # 負數
        'reason': 'admin_grant'
    }

    response = client.post(
        '/api/v1/admin/subscriptions/test_uid/extend',
        headers=authorized_headers,
        json=data
    )

    assert response.status_code == 400


def test_extend_subscription_invalid_reason(client, authorized_headers, mock_admin_auth):
    """測試延長訂閱 - 無效的原因"""
    data = {
        'days': 30,
        'reason': 'invalid_reason'  # 不在 ExtensionReason 枚舉中
    }

    response = client.post(
        '/api/v1/admin/subscriptions/test_uid/extend',
        headers=authorized_headers,
        json=data
    )

    assert response.status_code == 400


def test_extend_subscription_too_many_days(client, authorized_headers, mock_admin_auth):
    """測試延長訂閱 - 超過 365 天"""
    data = {
        'days': 400,  # 超過 365
        'reason': 'admin_grant'
    }

    response = client.post(
        '/api/v1/admin/subscriptions/test_uid/extend',
        headers=authorized_headers,
        json=data
    )

    assert response.status_code == 400


def test_extend_subscription_success(client, authorized_headers, mock_admin_auth, mock_firestore):
    """測試成功延長訂閱"""
    data = {
        'days': 30,
        'reason': 'admin_grant',
        'notes': 'Test extension'
    }

    # Mock subscription_service.extend_subscription
    with patch('domains.subscription.subscription_service.subscription_service.extend_subscription') as mock_extend:
        now = datetime.now(timezone.utc)
        new_end = now + timedelta(days=30)

        mock_extend.return_value = {
            'success': True,
            'new_end_at': new_end.isoformat(),
            'total_extension_days': 30
        }

        # Mock user document
        mock_user_doc = Mock()
        mock_user_doc.exists = True
        mock_user_doc.get.return_value = 'test@example.com'
        mock_firestore.collection.return_value.document.return_value.get.return_value = mock_user_doc

        response = client.post(
            '/api/v1/admin/subscriptions/test_uid/extend',
            headers=authorized_headers,
            json=data
        )

        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        assert 'new_end_at' in result
