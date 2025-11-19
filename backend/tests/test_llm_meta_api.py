"""
測試 LLM 元數據 API
"""
import pytest
from unittest.mock import patch, Mock
from datetime import datetime, timezone


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


def test_get_weekly_plan_llm_meta_success(client, authorized_headers, mock_admin_auth):
    """測試成功獲取週課表 LLM 元數據"""
    weekly_plan_id = "test_plan_123_5"

    mock_meta_data = {
        'weekly_plan_id': weekly_plan_id,
        'uid': 'test_user',
        'race_id': 'test_race',
        'stage1': {
            'prompt': 'Stage 1 prompt content...',
            'response': 'Stage 1 response content...',
            'model': 'gemini-2.0-flash',
            'timestamp': datetime.now(timezone.utc),
            'tokens': {
                'prompt_tokens': 1000,
                'completion_tokens': 500,
                'total_tokens': 1500
            }
        },
        'stage2': {
            'prompt': 'Stage 2 prompt content...',
            'response': '{"week_of_plan": 5}',
            'model': 'gemini-2.0-flash',
            'timestamp': datetime.now(timezone.utc),
            'tokens': {
                'prompt_tokens': 800,
                'completion_tokens': 300,
                'total_tokens': 1100
            }
        },
        'created_at': datetime.now(timezone.utc),
        'updated_at': datetime.now(timezone.utc)
    }

    with patch('core.database.repositories.llm_meta_repository.llm_meta_repository.get_weekly_plan_llm_meta') as mock_get:
        mock_get.return_value = mock_meta_data

        response = client.get(
            f'/api/v1/admin/llm-meta/weekly-plans/{weekly_plan_id}/llm-meta',
            headers=authorized_headers
        )

        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        assert 'data' in result
        assert result['data']['weekly_plan_id'] == weekly_plan_id
        assert 'stage1' in result['data']
        assert 'stage2' in result['data']
        assert result['data']['stage1']['model'] == 'gemini-2.0-flash'


def test_get_weekly_plan_llm_meta_not_found(client, authorized_headers, mock_admin_auth):
    """測試獲取不存在的週課表 LLM 元數據"""
    weekly_plan_id = "nonexistent_plan"

    with patch('core.database.repositories.llm_meta_repository.llm_meta_repository.get_weekly_plan_llm_meta') as mock_get:
        mock_get.return_value = None

        response = client.get(
            f'/api/v1/admin/llm-meta/weekly-plans/{weekly_plan_id}/llm-meta',
            headers=authorized_headers
        )

        assert response.status_code == 404
        result = response.get_json()
        assert result['success'] is False
        assert 'error' in result


def test_get_weekly_summary_llm_meta_success(client, authorized_headers, mock_admin_auth):
    """測試成功獲取週回顧 LLM 元數據"""
    summary_id = "test_plan_123_4_summary"

    mock_meta_data = {
        'summary_id': summary_id,
        'uid': 'test_user',
        'weekly_plan_id': 'test_plan_123_4',
        'prompt': 'Weekly summary prompt content...',
        'model': 'gemini-2.5-flash',
        'timestamp': datetime.now(timezone.utc),
        'tokens': {
            'prompt_tokens': 2000,
            'completion_tokens': 1000,
            'total_tokens': 3000
        },
        'created_at': datetime.now(timezone.utc),
        'updated_at': datetime.now(timezone.utc)
    }

    with patch('core.database.repositories.llm_meta_repository.llm_meta_repository.get_weekly_summary_llm_meta') as mock_get:
        mock_get.return_value = mock_meta_data

        response = client.get(
            f'/api/v1/admin/llm-meta/weekly-summaries/{summary_id}/llm-meta',
            headers=authorized_headers
        )

        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        assert 'data' in result
        assert result['data']['summary_id'] == summary_id
        assert result['data']['model'] == 'gemini-2.5-flash'
        assert result['data']['prompt'] == 'Weekly summary prompt content...'


def test_get_weekly_summary_llm_meta_not_found(client, authorized_headers, mock_admin_auth):
    """測試獲取不存在的週回顧 LLM 元數據"""
    summary_id = "nonexistent_summary"

    with patch('core.database.repositories.llm_meta_repository.llm_meta_repository.get_weekly_summary_llm_meta') as mock_get:
        mock_get.return_value = None

        response = client.get(
            f'/api/v1/admin/llm-meta/weekly-summaries/{summary_id}/llm-meta',
            headers=authorized_headers
        )

        assert response.status_code == 404
        result = response.get_json()
        assert result['success'] is False
        assert 'error' in result


def test_get_weekly_plan_llm_meta_with_only_stage1(client, authorized_headers, mock_admin_auth):
    """測試獲取只有 Stage 1 的週課表 LLM 元數據"""
    weekly_plan_id = "test_plan_123_1"

    mock_meta_data = {
        'weekly_plan_id': weekly_plan_id,
        'uid': 'test_user',
        'race_id': 'test_race',
        'stage1': {
            'prompt': 'Stage 1 prompt',
            'response': 'Stage 1 response',
            'model': 'gemini-2.0-flash',
            'timestamp': datetime.now(timezone.utc),
            'tokens': {
                'prompt_tokens': 1000,
                'completion_tokens': 500,
                'total_tokens': 1500
            }
        },
        # No stage2
        'created_at': datetime.now(timezone.utc),
        'updated_at': datetime.now(timezone.utc)
    }

    with patch('core.database.repositories.llm_meta_repository.llm_meta_repository.get_weekly_plan_llm_meta') as mock_get:
        mock_get.return_value = mock_meta_data

        response = client.get(
            f'/api/v1/admin/llm-meta/weekly-plans/{weekly_plan_id}/llm-meta',
            headers=authorized_headers
        )

        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        assert 'stage1' in result['data']
        assert 'stage2' not in result['data']
