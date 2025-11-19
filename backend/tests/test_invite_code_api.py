"""
測試邀請碼管理 API

遵循用戶要求：補上對應的測試確保功能正確
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


@pytest.fixture
def test_invite_code_data():
    """提供測試用的邀請碼數據"""
    now = datetime.now(timezone.utc)
    return {
        'code': 'ABC12345',
        'owner_uid': 'user_123',
        'usage_count': 3,
        'max_usage': 10,
        'reward_days': 7,
        'refund_period_days': 14,
        'is_active': True,
        'created_at': now - timedelta(days=30),
        'updated_at': now
    }


@pytest.fixture
def test_invite_code_usage_data():
    """提供測試用的邀請碼使用記錄數據"""
    now = datetime.now(timezone.utc)
    return {
        'code': 'ABC12345',
        'inviter_uid': 'user_123',
        'invitee_uid': 'user_456',
        'used_at': now - timedelta(days=10),
        'reward_granted': False,
        'reward_granted_at': None,
        'reward_days': 7,
        'inviter_past_refund_period': False,
        'invitee_past_refund_period': False
    }


# ===== List Invite Codes Tests =====

def test_list_invite_codes_requires_auth(client):
    """測試列表邀請碼需要認證"""
    response = client.get('/api/v1/admin/invite-codes')
    assert response.status_code == 401


def test_list_invite_codes_success(client, authorized_headers, mock_admin_auth, mock_firestore, test_invite_code_data):
    """測試成功獲取邀請碼列表"""
    # Mock Firestore 返回邀請碼數據
    mock_doc = Mock()
    mock_doc.id = 'ABC12345'
    mock_doc.to_dict.return_value = test_invite_code_data

    mock_query = Mock()
    mock_query.where.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.stream.return_value = [mock_doc]

    mock_firestore.collection.return_value = mock_query

    response = client.get('/api/v1/admin/invite-codes', headers=authorized_headers)

    assert response.status_code == 200
    data = response.get_json()
    assert 'data' in data
    assert 'pagination' in data
    assert len(data['data']) > 0
    assert data['data'][0]['code'] == 'ABC12345'


def test_list_invite_codes_with_pagination(client, authorized_headers, mock_admin_auth, mock_firestore, test_invite_code_data):
    """測試邀請碼列表分頁"""
    # Mock 多個邀請碼
    mock_docs = []
    for i in range(3):
        mock_doc = Mock()
        mock_doc.id = f'CODE{i}'
        doc_data = test_invite_code_data.copy()
        doc_data['code'] = f'CODE{i}'
        mock_doc.to_dict.return_value = doc_data
        mock_docs.append(mock_doc)

    mock_query = Mock()
    mock_query.where.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.stream.return_value = mock_docs

    mock_firestore.collection.return_value = mock_query

    response = client.get('/api/v1/admin/invite-codes?page=1&limit=2', headers=authorized_headers)

    assert response.status_code == 200
    data = response.get_json()
    assert data['pagination']['page'] == 1
    assert data['pagination']['limit'] == 2
    assert data['pagination']['total'] == 3


def test_list_invite_codes_filter_by_status(client, authorized_headers, mock_admin_auth, mock_firestore, test_invite_code_data):
    """測試按狀態篩選邀請碼"""
    # Mock active invite codes
    mock_doc = Mock()
    mock_doc.id = 'ACTIVE01'
    mock_doc.to_dict.return_value = test_invite_code_data

    mock_query = Mock()
    mock_query.where.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.stream.return_value = [mock_doc]

    mock_firestore.collection.return_value = mock_query

    response = client.get('/api/v1/admin/invite-codes?status=active', headers=authorized_headers)

    assert response.status_code == 200
    data = response.get_json()
    assert len(data['data']) > 0
    # Verify where was called with is_active filter
    mock_query.where.assert_called()


def test_list_invite_codes_filter_by_owner(client, authorized_headers, mock_admin_auth, mock_firestore, test_invite_code_data):
    """測試按擁有者 UID 篩選邀請碼"""
    mock_doc = Mock()
    mock_doc.id = 'ABC12345'
    mock_doc.to_dict.return_value = test_invite_code_data

    mock_query = Mock()
    mock_query.where.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.stream.return_value = [mock_doc]

    mock_firestore.collection.return_value = mock_query

    response = client.get('/api/v1/admin/invite-codes?owner_uid=user_123', headers=authorized_headers)

    assert response.status_code == 200
    data = response.get_json()
    assert len(data['data']) > 0


# ===== Get Invite Code Detail Tests =====

def test_get_invite_code_requires_auth(client):
    """測試獲取邀請碼詳情需要認證"""
    response = client.get('/api/v1/admin/invite-codes/ABC12345')
    assert response.status_code == 401


def test_get_invite_code_not_found(client, authorized_headers, mock_admin_auth):
    """測試獲取不存在的邀請碼"""
    with patch('domains.subscription.subscription_service.subscription_service.repo.get_invite_code') as mock_get:
        mock_get.return_value = None

        response = client.get('/api/v1/admin/invite-codes/NOTEXIST', headers=authorized_headers)

        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data


def test_get_invite_code_success(client, authorized_headers, mock_admin_auth, test_invite_code_data):
    """測試成功獲取邀請碼詳情"""
    from data_models.subscription_models import InviteCode, Subscription

    # Create mock invite code
    mock_invite_code = InviteCode.from_dict(test_invite_code_data)

    # Mock subscription (owner)
    mock_subscription = Mock()
    mock_subscription.is_premium = True

    with patch('domains.subscription.subscription_service.subscription_service.repo.get_invite_code') as mock_get_code, \
         patch('domains.subscription.subscription_service.subscription_service.repo.get_subscription') as mock_get_sub, \
         patch('domains.subscription.subscription_service.subscription_service.repo.get_invite_code_usages_by_inviter') as mock_get_usages:

        mock_get_code.return_value = mock_invite_code
        mock_get_sub.return_value = mock_subscription
        mock_get_usages.return_value = []

        response = client.get('/api/v1/admin/invite-codes/ABC12345', headers=authorized_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert 'invite_code' in data
        assert 'owner' in data
        assert 'statistics' in data
        assert data['invite_code']['code'] == 'ABC12345'
        assert data['statistics']['total_usages'] == 0


def test_get_invite_code_with_usages(client, authorized_headers, mock_admin_auth, test_invite_code_data, test_invite_code_usage_data):
    """測試獲取邀請碼詳情（含使用記錄統計）"""
    from data_models.subscription_models import InviteCode, InviteCodeUsage

    mock_invite_code = InviteCode.from_dict(test_invite_code_data)

    # Create mock usages
    usage1_data = test_invite_code_usage_data.copy()
    usage1_data['reward_granted'] = True
    usage1 = InviteCodeUsage.from_dict(usage1_data)

    usage2_data = test_invite_code_usage_data.copy()
    usage2_data['invitee_uid'] = 'user_789'
    usage2_data['reward_granted'] = False
    usage2 = InviteCodeUsage.from_dict(usage2_data)

    mock_subscription = Mock()
    mock_subscription.is_premium = True

    with patch('domains.subscription.subscription_service.subscription_service.repo.get_invite_code') as mock_get_code, \
         patch('domains.subscription.subscription_service.subscription_service.repo.get_subscription') as mock_get_sub, \
         patch('domains.subscription.subscription_service.subscription_service.repo.get_invite_code_usages_by_inviter') as mock_get_usages:

        mock_get_code.return_value = mock_invite_code
        mock_get_sub.return_value = mock_subscription
        mock_get_usages.return_value = [usage1, usage2]

        response = client.get('/api/v1/admin/invite-codes/ABC12345', headers=authorized_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['statistics']['total_usages'] == 2
        assert data['statistics']['rewarded_usages'] == 1
        assert data['statistics']['pending_rewards'] == 1


# ===== Get Invite Code Usages Tests =====

def test_get_invite_code_usages_requires_auth(client):
    """測試獲取邀請碼使用記錄需要認證"""
    response = client.get('/api/v1/admin/invite-codes/ABC12345/usages')
    assert response.status_code == 401


def test_get_invite_code_usages_code_not_found(client, authorized_headers, mock_admin_auth):
    """測試獲取不存在邀請碼的使用記錄"""
    with patch('domains.subscription.subscription_service.subscription_service.repo.get_invite_code') as mock_get:
        mock_get.return_value = None

        response = client.get('/api/v1/admin/invite-codes/NOTEXIST/usages', headers=authorized_headers)

        assert response.status_code == 404


def test_get_invite_code_usages_success(client, authorized_headers, mock_admin_auth, mock_firestore, test_invite_code_data, test_invite_code_usage_data):
    """測試成功獲取邀請碼使用記錄"""
    from data_models.subscription_models import InviteCode

    mock_invite_code = InviteCode.from_dict(test_invite_code_data)

    # Mock usage documents
    mock_usage_doc = Mock()
    mock_usage_doc.id = 'usage_1'
    mock_usage_doc.to_dict.return_value = test_invite_code_usage_data

    mock_query = Mock()
    mock_query.where.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.stream.return_value = [mock_usage_doc]

    mock_firestore.collection.return_value = mock_query

    with patch('domains.subscription.subscription_service.subscription_service.repo.get_invite_code') as mock_get_code:
        mock_get_code.return_value = mock_invite_code

        response = client.get('/api/v1/admin/invite-codes/ABC12345/usages', headers=authorized_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert 'total' in data
        assert data['total'] >= 0


# ===== Disable Invite Code Tests =====

def test_disable_invite_code_requires_auth(client):
    """測試禁用邀請碼需要認證"""
    response = client.post('/api/v1/admin/invite-codes/ABC12345/disable')
    assert response.status_code == 401


def test_disable_invite_code_not_found(client, authorized_headers, mock_admin_auth):
    """測試禁用不存在的邀請碼"""
    with patch('domains.subscription.subscription_service.subscription_service.repo.get_invite_code') as mock_get:
        mock_get.return_value = None

        response = client.post('/api/v1/admin/invite-codes/NOTEXIST/disable', headers=authorized_headers)

        assert response.status_code == 404


def test_disable_invite_code_already_inactive(client, authorized_headers, mock_admin_auth, test_invite_code_data):
    """測試禁用已經禁用的邀請碼"""
    from data_models.subscription_models import InviteCode

    inactive_data = test_invite_code_data.copy()
    inactive_data['is_active'] = False
    mock_invite_code = InviteCode.from_dict(inactive_data)

    with patch('domains.subscription.subscription_service.subscription_service.repo.get_invite_code') as mock_get:
        mock_get.return_value = mock_invite_code

        response = client.post('/api/v1/admin/invite-codes/ABC12345/disable', headers=authorized_headers)

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data


def test_disable_invite_code_success(client, authorized_headers, mock_admin_auth, test_invite_code_data):
    """測試成功禁用邀請碼"""
    from data_models.subscription_models import InviteCode

    mock_invite_code = InviteCode.from_dict(test_invite_code_data)

    with patch('domains.subscription.subscription_service.subscription_service.repo.get_invite_code') as mock_get, \
         patch('domains.subscription.subscription_service.subscription_service.repo.update_invite_code') as mock_update, \
         patch('services.audit_log_service.audit_log_service.log_action') as mock_log:

        mock_get.return_value = mock_invite_code

        response = client.post('/api/v1/admin/invite-codes/ABC12345/disable', headers=authorized_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

        # Verify update was called
        mock_update.assert_called_once()
        call_args = mock_update.call_args
        assert call_args[0][0] == 'ABC12345'
        assert call_args[0][1]['is_active'] is False

        # Verify audit log was created
        mock_log.assert_called_once()


# ===== Get Invite Code Stats Tests =====

def test_get_invite_code_stats_requires_auth(client):
    """測試獲取邀請碼統計需要認證"""
    response = client.get('/api/v1/admin/invite-codes/stats')
    assert response.status_code == 401


def test_get_invite_code_stats_success(client, authorized_headers, mock_admin_auth, mock_firestore):
    """測試成功獲取邀請碼統計"""
    # Mock invite codes
    mock_code_docs = []
    for i in range(5):
        mock_doc = Mock()
        mock_doc.to_dict.return_value = {'is_active': i < 3}  # 3 active, 2 inactive
        mock_code_docs.append(mock_doc)

    # Mock usages
    mock_usage_docs = []
    for i in range(10):
        mock_doc = Mock()
        mock_doc.to_dict.return_value = {'reward_granted': i < 7}  # 7 rewarded, 3 pending
        mock_usage_docs.append(mock_doc)

    def mock_stream(*args, **kwargs):
        # Check collection name from call stack
        if 'invite_codes' in str(args):
            return mock_code_docs
        else:
            return mock_usage_docs

    mock_collection = Mock()
    mock_collection.stream.side_effect = mock_stream

    mock_firestore.collection.return_value = mock_collection

    response = client.get('/api/v1/admin/invite-codes/stats', headers=authorized_headers)

    assert response.status_code == 200
    data = response.get_json()
    assert 'total_codes' in data
    assert 'active_codes' in data
    assert 'inactive_codes' in data
    assert 'total_usages' in data
    assert 'rewarded_usages' in data
    assert 'pending_rewards' in data
    assert 'conversion_rate' in data


def test_get_invite_code_stats_empty_database(client, authorized_headers, mock_admin_auth, mock_firestore):
    """測試空數據庫的統計"""
    mock_collection = Mock()
    mock_collection.stream.return_value = []

    mock_firestore.collection.return_value = mock_collection

    response = client.get('/api/v1/admin/invite-codes/stats', headers=authorized_headers)

    assert response.status_code == 200
    data = response.get_json()
    assert data['total_codes'] == 0
    assert data['total_usages'] == 0
    assert data['conversion_rate'] == 0.0


# ===== Error Handling Tests =====

def test_list_invite_codes_service_unavailable(client, authorized_headers, mock_admin_auth):
    """測試服務不可用時的錯誤處理"""
    with patch('api.admin.invite_codes.subscription_service', None):
        response = client.get('/api/v1/admin/invite-codes', headers=authorized_headers)
        assert response.status_code == 503


def test_get_invite_code_internal_error(client, authorized_headers, mock_admin_auth):
    """測試內部錯誤處理"""
    with patch('domains.subscription.subscription_service.subscription_service.repo.get_invite_code') as mock_get:
        mock_get.side_effect = Exception("Database error")

        response = client.get('/api/v1/admin/invite-codes/ABC12345', headers=authorized_headers)

        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
