"""
測試健康檢查端點
"""
import pytest


def test_health_endpoint(client):
    """測試健康檢查端點"""
    response = client.get('/health')

    assert response.status_code == 200

    data = response.get_json()
    assert data['status'] == 'ok'
    assert 'service' in data
    assert 'version' in data
    assert 'environment' in data


def test_health_endpoint_returns_correct_environment(client):
    """測試健康檢查返回正確的環境"""
    response = client.get('/health')

    data = response.get_json()
    # 在測試環境中應該是 'dev'
    assert data['environment'] in ['dev', 'prod']
