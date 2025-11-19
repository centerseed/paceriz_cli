"""
測試訂閱測試工具 API
"""
import pytest
from unittest.mock import patch, Mock


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


def test_start_trial_success(client, authorized_headers, mock_admin_auth):
    """測試成功開始試用期"""
    data = {
        'uid': 'test_uid',
        'trial_days': 14
    }

    with patch('domains.subscription.subscription_service.subscription_service.start_trial') as mock_start:
        mock_start.return_value = {
            'trial_start': '2024-01-01T00:00:00Z',
            'trial_end': '2024-01-15T00:00:00Z',
            'status': 'trial'
        }

        response = client.post(
            '/api/v1/admin/subscription-tools/start-trial',
            headers=authorized_headers,
            json=data
        )

        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        assert 'message' in result
        assert 'data' in result
        assert result['data']['uid'] == 'test_uid'
        assert result['data']['trial_days'] == 14


def test_start_trial_missing_uid(client, authorized_headers, mock_admin_auth):
    """測試開始試用期 - 缺少 uid"""
    data = {
        'trial_days': 14
    }

    response = client.post(
        '/api/v1/admin/subscription-tools/start-trial',
        headers=authorized_headers,
        json=data
    )

    assert response.status_code == 400
    result = response.get_json()
    assert 'error' in result


def test_add_whitelist_success(client, authorized_headers, mock_admin_auth):
    """測試成功加入白名單"""
    data = {
        'uid': 'test_uid',
        'reason': 'test_account',
        'granted_by': 'admin'
    }

    with patch('domains.subscription.subscription_service.subscription_service.add_to_whitelist') as mock_add:
        mock_add.return_value = {
            'granted_at': '2024-01-01T00:00:00Z'
        }

        response = client.post(
            '/api/v1/admin/subscription-tools/add-whitelist',
            headers=authorized_headers,
            json=data
        )

        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        assert 'message' in result
        assert 'data' in result


def test_remove_whitelist_success(client, authorized_headers, mock_admin_auth):
    """測試成功移出白名單"""
    data = {
        'uid': 'test_uid'
    }

    with patch('domains.subscription.subscription_service.subscription_service.remove_from_whitelist') as mock_remove:
        mock_remove.return_value = {
            'removed': True
        }

        response = client.post(
            '/api/v1/admin/subscription-tools/remove-whitelist',
            headers=authorized_headers,
            json=data
        )

        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        assert 'message' in result


def test_extend_subscription_success(client, authorized_headers, mock_admin_auth):
    """測試成功延長訂閱"""
    data = {
        'uid': 'test_uid',
        'days': 7,
        'reason': 'admin',
        'granted_by': 'admin',
        'notes': 'Test extension'
    }

    with patch('domains.subscription.subscription_service.subscription_service.extend_subscription') as mock_extend:
        mock_extend.return_value = {
            'new_end_date': '2024-01-15T00:00:00Z',
            'total_days': 21
        }

        response = client.post(
            '/api/v1/admin/subscription-tools/extend',
            headers=authorized_headers,
            json=data
        )

        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        assert 'message' in result
        assert 'data' in result
        assert result['data']['days'] == 7


def test_extend_subscription_missing_days(client, authorized_headers, mock_admin_auth):
    """測試延長訂閱 - 缺少 days"""
    data = {
        'uid': 'test_uid',
        'reason': 'admin'
    }

    response = client.post(
        '/api/v1/admin/subscription-tools/extend',
        headers=authorized_headers,
        json=data
    )

    assert response.status_code == 400
    result = response.get_json()
    assert 'error' in result


def test_check_subscription_success(client, authorized_headers, mock_admin_auth):
    """測試成功檢查訂閱狀態"""
    with patch('domains.subscription.subscription_service.subscription_service.get_subscription_summary') as mock_summary, \
         patch('domains.subscription.subscription_service.subscription_service.can_access_premium_features') as mock_access, \
         patch('domains.subscription.subscription_service.subscription_service.is_whitelisted') as mock_whitelist:

        mock_summary.return_value = {
            'status': 'trial',
            'trial_end': '2024-01-15T00:00:00Z'
        }
        mock_access.return_value = True
        mock_whitelist.return_value = False

        response = client.get(
            '/api/v1/admin/subscription-tools/check/test_uid',
            headers=authorized_headers
        )

        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        assert 'data' in result
        assert result['data']['has_premium_access'] is True
        assert result['data']['is_whitelisted'] is False


def test_test_auto_trial_success(client, authorized_headers, mock_admin_auth):
    """測試自動試用功能"""
    data = {
        'uid': 'new_user_uid'
    }

    with patch('domains.subscription.subscription_service.subscription_service.get_subscription_summary') as mock_summary, \
         patch('domains.subscription.subscription_service.subscription_service.can_access_premium_features') as mock_access, \
         patch('domains.subscription.subscription_service.subscription_service.AUTO_START_TRIAL_FOR_NEW_USERS', True), \
         patch('domains.subscription.subscription_service.subscription_service.AUTO_TRIAL_DAYS', 14):

        # 第一次調用：沒有訂閱記錄
        mock_summary.side_effect = [
            {'status': 'no_trial'},  # 第一次查詢
            {'status': 'trial', 'trial_end': '2024-01-15T00:00:00Z'}  # 第二次查詢
        ]
        mock_access.return_value = True

        response = client.post(
            '/api/v1/admin/subscription-tools/test-auto-trial',
            headers=authorized_headers,
            json=data
        )

        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        assert 'message' in result
        assert 'data' in result


def test_test_auto_trial_already_has_subscription(client, authorized_headers, mock_admin_auth):
    """測試自動試用 - 用戶已有訂閱"""
    data = {
        'uid': 'existing_user_uid'
    }

    with patch('domains.subscription.subscription_service.subscription_service.get_subscription_summary') as mock_summary:
        mock_summary.return_value = {
            'status': 'trial'  # 已有試用記錄
        }

        response = client.post(
            '/api/v1/admin/subscription-tools/test-auto-trial',
            headers=authorized_headers,
            json=data
        )

        assert response.status_code == 400
        result = response.get_json()
        assert result['success'] is False
        assert 'error' in result
