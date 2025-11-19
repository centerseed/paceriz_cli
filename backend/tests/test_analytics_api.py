"""
Analytics API Tests

測試數據分析相關的 API endpoints
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch
from google.cloud import firestore


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
def test_subscription_data():
    """測試用訂閱數據"""
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)

    return [
        {
            'uid': 'user1',
            'trial_start_at': thirty_days_ago,
            'trial_end_at': now + timedelta(days=7),
            'is_premium': True,
            'premium_start_at': now - timedelta(days=23),
            'premium_end_at': now + timedelta(days=30),
            'payment_platform': 'stripe',
            'created_at': thirty_days_ago,
            'updated_at': now,
        },
        {
            'uid': 'user2',
            'trial_start_at': seven_days_ago,
            'trial_end_at': now + timedelta(days=7),
            'is_premium': False,
            'created_at': seven_days_ago,
            'updated_at': now,
        },
        {
            'uid': 'user3',
            'trial_start_at': now - timedelta(days=60),
            'trial_end_at': now - timedelta(days=53),
            'is_premium': True,
            'premium_start_at': now - timedelta(days=53),
            'premium_end_at': now + timedelta(days=30),
            'payment_platform': 'apple',
            'created_at': now - timedelta(days=60),
            'updated_at': now,
        },
    ]


def test_get_overview_success(client, authorized_headers, mock_admin_auth, mock_firestore, test_subscription_data):
    """測試成功獲取總覽統計"""
    # Setup mock Firestore
    mock_docs = []
    for data in test_subscription_data:
        mock_doc = Mock()
        mock_doc.to_dict.return_value = data
        mock_docs.append(mock_doc)

    mock_firestore.collection().stream.return_value = mock_docs

    # Make request
    response = client.get('/api/v1/admin/analytics/overview', headers=authorized_headers)

    # Assertions
    assert response.status_code == 200
    data = response.get_json()

    assert 'total_users' in data
    assert 'trial_users' in data
    assert 'premium_users' in data
    assert 'active_premium_users' in data
    assert 'trial_conversion_rate' in data
    assert 'churn_rate' in data

    assert data['total_users'] == 3
    assert data['premium_users'] == 2


def test_get_overview_unauthorized(client):
    """測試未授權訪問總覽統計"""
    response = client.get('/api/v1/admin/analytics/overview')
    assert response.status_code == 401


def test_get_revenue_success(client, authorized_headers, mock_admin_auth, mock_firestore, test_subscription_data):
    """測試成功獲取收入統計"""
    # Setup mock Firestore
    mock_docs = []
    for data in test_subscription_data:
        mock_doc = Mock()
        mock_doc.to_dict.return_value = data
        mock_docs.append(mock_doc)

    mock_firestore.collection().stream.return_value = mock_docs

    # Make request
    response = client.get('/api/v1/admin/analytics/revenue', headers=authorized_headers)

    # Assertions
    assert response.status_code == 200
    data = response.get_json()

    assert 'current_month_revenue' in data
    assert 'last_month_revenue' in data
    assert 'annual_recurring_revenue' in data
    assert 'average_revenue_per_user' in data
    assert 'by_platform' in data

    # Verify platform breakdown
    assert 'stripe' in data['by_platform']
    assert 'apple' in data['by_platform']


def test_get_revenue_unauthorized(client):
    """測試未授權訪問收入統計"""
    response = client.get('/api/v1/admin/analytics/revenue')
    assert response.status_code == 401


def test_get_retention_success(client, authorized_headers, mock_admin_auth, mock_firestore, test_subscription_data):
    """測試成功獲取留存分析"""
    # Setup mock Firestore
    mock_docs = []
    for data in test_subscription_data:
        mock_doc = Mock()
        mock_doc.to_dict.return_value = data
        mock_docs.append(mock_doc)

    mock_firestore.collection().stream.return_value = mock_docs

    # Make request
    response = client.get('/api/v1/admin/analytics/retention', headers=authorized_headers)

    # Assertions
    assert response.status_code == 200
    data = response.get_json()

    assert 'day_7_retention' in data
    assert 'day_30_retention' in data
    assert 'month_3_retention' in data

    # Retention rates should be between 0 and 1
    assert 0 <= data['day_7_retention'] <= 1
    assert 0 <= data['day_30_retention'] <= 1
    assert 0 <= data['month_3_retention'] <= 1


def test_get_retention_unauthorized(client):
    """測試未授權訪問留存分析"""
    response = client.get('/api/v1/admin/analytics/retention')
    assert response.status_code == 401


def test_get_trends_success(client, authorized_headers, mock_admin_auth, mock_firestore, test_subscription_data):
    """測試成功獲取趨勢數據"""
    # Setup mock Firestore
    mock_docs = []
    for data in test_subscription_data:
        mock_doc = Mock()
        mock_doc.to_dict.return_value = data
        mock_docs.append(mock_doc)

    mock_firestore.collection().stream.return_value = mock_docs

    # Make request with default 30 days
    response = client.get('/api/v1/admin/analytics/trends', headers=authorized_headers)

    # Assertions
    assert response.status_code == 200
    data = response.get_json()

    assert 'dates' in data
    assert 'new_users' in data
    assert 'new_premium_users' in data
    assert 'active_users' in data

    # Should have 30 days of data
    assert len(data['dates']) == 30
    assert len(data['new_users']) == 30
    assert len(data['new_premium_users']) == 30
    assert len(data['active_users']) == 30


def test_get_trends_custom_days(client, authorized_headers, mock_admin_auth, mock_firestore, test_subscription_data):
    """測試使用自定義天數獲取趨勢數據"""
    # Setup mock Firestore
    mock_docs = []
    for data in test_subscription_data:
        mock_doc = Mock()
        mock_doc.to_dict.return_value = data
        mock_docs.append(mock_doc)

    mock_firestore.collection().stream.return_value = mock_docs

    # Make request with 7 days
    response = client.get('/api/v1/admin/analytics/trends?days=7', headers=authorized_headers)

    # Assertions
    assert response.status_code == 200
    data = response.get_json()

    # Should have 7 days of data
    assert len(data['dates']) == 7
    assert len(data['new_users']) == 7


def test_get_trends_invalid_days(client, authorized_headers, mock_admin_auth):
    """測試使用無效天數參數"""
    # Days > 90 should be capped at 90
    response = client.get('/api/v1/admin/analytics/trends?days=100', headers=authorized_headers)

    # Should still succeed but cap at 90 days
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['dates']) == 90


def test_get_trends_unauthorized(client):
    """測試未授權訪問趨勢數據"""
    response = client.get('/api/v1/admin/analytics/trends')
    assert response.status_code == 401


def test_analytics_with_empty_database(client, authorized_headers, mock_admin_auth, mock_firestore):
    """測試空數據庫情況"""
    # Setup mock Firestore to return empty results
    mock_firestore.collection().stream.return_value = []

    # Test overview
    response = client.get('/api/v1/admin/analytics/overview', headers=authorized_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['total_users'] == 0
    assert data['premium_users'] == 0

    # Test revenue
    response = client.get('/api/v1/admin/analytics/revenue', headers=authorized_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['current_month_revenue'] == 0
    assert data['annual_recurring_revenue'] == 0

    # Test retention
    response = client.get('/api/v1/admin/analytics/retention', headers=authorized_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['day_7_retention'] == 0
    assert data['day_30_retention'] == 0

    # Test trends
    response = client.get('/api/v1/admin/analytics/trends', headers=authorized_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['dates']) == 30
    assert all(count == 0 for count in data['new_users'])


def test_analytics_admin_only_access(client):
    """測試只有 admin 可以訪問分析 API"""
    # Test with no auth headers (unauthorized)

    response = client.get('/api/v1/admin/analytics/overview')
    assert response.status_code == 401

    response = client.get('/api/v1/admin/analytics/revenue')
    assert response.status_code == 401

    response = client.get('/api/v1/admin/analytics/retention')
    assert response.status_code == 401

    response = client.get('/api/v1/admin/analytics/trends')
    assert response.status_code == 401
