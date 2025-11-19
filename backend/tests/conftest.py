"""
Pytest 配置文件

提供測試 fixtures 和配置
"""
import os
import sys
import pytest
from unittest.mock import Mock, patch

# 添加 api_service 到 Python path
API_SERVICE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../api_service'))
sys.path.insert(0, API_SERVICE_PATH)


@pytest.fixture(scope="session")
def app():
    """創建 Flask app fixture"""
    # 設置測試環境變數
    os.environ['ENV_TYPE'] = 'dev'
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['FLASK_DEBUG'] = '0'
    os.environ['SUPER_ADMIN_EMAILS'] = 'centerseedwu@gmail.com'

    # Import app
    from app import app as flask_app

    # 配置測試模式
    flask_app.config['TESTING'] = True

    yield flask_app


@pytest.fixture
def client(app):
    """創建測試 client"""
    return app.test_client()


@pytest.fixture
def mock_firebase_admin():
    """Mock Firebase Admin SDK"""
    with patch('firebase_admin.auth.verify_id_token') as mock_verify:
        # 模擬驗證成功的 token
        mock_verify.return_value = {
            'uid': 'test_admin_uid',
            'email': 'centerseedwu@gmail.com'
        }
        yield mock_verify


@pytest.fixture
def mock_firestore():
    """Mock Firestore client"""
    with patch('firebase_admin.firestore.client') as mock_client:
        mock_db = Mock()
        mock_client.return_value = mock_db
        yield mock_db


@pytest.fixture
def admin_token():
    """提供測試用的 admin token"""
    # 這是一個假的 token，用於測試
    return "test_admin_token_for_testing"


@pytest.fixture
def test_subscription_data():
    """提供測試用的訂閱數據"""
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    return {
        'uid': 'test_user_123',
        'is_premium': False,
        'trial_days': 14,
        'trial_start_at': now - timedelta(days=3),
        'trial_end_at': now + timedelta(days=11),
        'premium_start_at': None,
        'premium_end_at': None,
        'total_extension_days': 0,
        'created_at': now - timedelta(days=3),
        'updated_at': now,
        'stripe_customer_id': None,
        'stripe_subscription_id': None,
        'extension_history': []
    }


@pytest.fixture
def test_premium_subscription_data():
    """提供測試用的付費訂閱數據"""
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    return {
        'uid': 'test_premium_456',
        'is_premium': True,
        'trial_days': 14,
        'trial_start_at': now - timedelta(days=44),
        'trial_end_at': now - timedelta(days=30),
        'premium_start_at': now - timedelta(days=30),
        'premium_end_at': now + timedelta(days=335),
        'total_extension_days': 0,
        'created_at': now - timedelta(days=44),
        'updated_at': now,
        'stripe_customer_id': 'cus_test_123',
        'stripe_subscription_id': 'sub_test_123',
        'extension_history': []
    }
