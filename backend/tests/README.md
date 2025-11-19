# Admin Backend 測試指南

## 📋 測試結構

```
backend/
├── pytest.sh              # 測試執行腳本（類似 api_service/unitest.sh）
└── tests/
    ├── __init__.py
    ├── conftest.py        # Pytest 配置和 fixtures
    ├── test_health.py     # 健康檢查測試
    ├── test_admin_auth.py # 管理員認證測試
    └── test_subscription_api.py  # 訂閱 API 測試
```

## 🚀 執行測試

### 基本用法

```bash
# 執行所有測試
cd /Users/wubaizong/havital/cloud/web_services/subscription_cli/backend
./pytest.sh dev

# 執行測試並生成覆蓋率報告
./pytest.sh dev --coverage

# 執行特定測試文件
./pytest.sh dev tests/test_health.py

# 查看幫助
./pytest.sh --help
```

### 環境要求

1. **Conda 環境**：`api`
2. **環境變數**：
   - `SUPER_ADMIN_EMAILS`：Super Admin 郵箱（預設：centerseedwu@gmail.com）
   - `ENV_TYPE`：環境類型（dev/prod）

3. **GCP 專案**：
   - dev → havital-dev
   - prod → paceriz-prod

## 🧪 測試類型

### 1. 健康檢查測試 (`test_health.py`)
- 測試 `/health` 端點
- 驗證服務狀態和環境配置

### 2. 認證測試 (`test_admin_auth.py`)
- 測試無 token 的請求（401）
- 測試無效 token 的請求（401）
- 測試非管理員用戶的請求（403）
- 測試 Super Admin 的請求（200）

### 3. 訂閱 API 測試 (`test_subscription_api.py`)
- 測試列表訂閱端點
- 測試獲取訂閱詳情
- 測試延長訂閱（各種邊界情況）
- 測試取消訂閱

## 📦 Fixtures

### 可用的 Fixtures（定義在 `conftest.py`）

- `app`：Flask 應用實例
- `client`：Flask 測試 client
- `mock_firebase_admin`：Mock Firebase Admin SDK
- `mock_firestore`：Mock Firestore client
- `admin_token`：測試用 admin token
- `test_subscription_data`：測試用試用訂閱數據
- `test_premium_subscription_data`：測試用付費訂閱數據

### 使用示例

```python
def test_something(client, mock_firestore, test_subscription_data):
    """測試某個功能"""
    # 使用 fixtures
    response = client.get('/api/v1/admin/subscriptions')
    assert response.status_code == 200
```

## ✅ 測試覆蓋範圍

當前測試涵蓋：

### ✅ 已測試
- [x] 健康檢查端點
- [x] 管理員認證中介層
- [x] 訂閱列表 API（基本功能）
- [x] 延長訂閱 API（參數驗證）

### ⚠️ 待補充
- [ ] 取消訂閱 API 完整測試
- [ ] 審計日誌服務測試
- [ ] 邀請碼查詢測試
- [ ] 分頁功能詳細測試
- [ ] 錯誤處理完整測試

## 🔍 調試技巧

### 1. 查看詳細輸出
```bash
# -v 顯示詳細測試名稱
# -s 顯示 print 輸出
./pytest.sh dev
```

### 2. 只運行特定測試
```bash
# 運行特定測試函數
pytest tests/test_health.py::test_health_endpoint -v

# 運行包含特定關鍵字的測試
pytest tests/ -k "auth" -v
```

### 3. 查看覆蓋率報告
```bash
./pytest.sh dev --coverage
open htmlcov/index.html
```

## 🐛 常見問題

### 1. Import 錯誤
**問題**：`ModuleNotFoundError: No module named 'domains'`

**解決**：確保 `PYTHONPATH` 包含 `api_service`：
```bash
export PYTHONPATH=$(pwd):$(pwd)/../../../api_service
```

### 2. Firebase 初始化錯誤
**問題**：`Firebase app already initialized`

**解決**：測試會自動處理 Firebase 初始化，確保使用 `mock_firebase_admin` fixture。

### 3. 認證失敗
**問題**：測試一直返回 401

**解決**：確保使用 `authorized_headers` fixture 或 `mock_admin_auth` fixture。

## 📊 測試報告示例

```
======================== test session starts =========================
collected 10 items

tests/test_health.py::test_health_endpoint PASSED           [ 10%]
tests/test_health.py::test_health_endpoint_returns_correct_environment PASSED [ 20%]
tests/test_admin_auth.py::test_require_admin_decorator_without_token PASSED [ 30%]
tests/test_admin_auth.py::test_require_admin_decorator_with_invalid_token PASSED [ 40%]
tests/test_admin_auth.py::test_require_admin_decorator_with_non_admin_user PASSED [ 50%]
tests/test_admin_auth.py::test_require_admin_decorator_with_super_admin PASSED [ 60%]
tests/test_subscription_api.py::test_list_subscriptions_requires_auth PASSED [ 70%]
tests/test_subscription_api.py::test_extend_subscription_invalid_days PASSED [ 80%]
tests/test_subscription_api.py::test_extend_subscription_invalid_reason PASSED [ 90%]
tests/test_subscription_api.py::test_extend_subscription_too_many_days PASSED [100%]

======================== 10 passed in 2.45s ==========================
```

## 🎯 最佳實踐

1. **使用 Fixtures**：避免重複的設置代碼
2. **Mock 外部依賴**：Firebase, Firestore, subscription_service
3. **測試邊界情況**：無效輸入、極端值、錯誤狀態
4. **清晰的測試名稱**：`test_<功能>_<情況>`
5. **單一職責**：每個測試只驗證一個功能點

## 📝 添加新測試

### 步驟

1. 在 `tests/` 目錄創建新文件（命名：`test_*.py`）
2. Import 需要的 fixtures
3. 編寫測試函數（命名：`test_*`）
4. 運行測試驗證

### 示例

```python
# tests/test_new_feature.py
import pytest

def test_new_feature(client, authorized_headers):
    """測試新功能"""
    response = client.get('/api/v1/admin/new-feature', headers=authorized_headers)
    assert response.status_code == 200
    assert response.get_json()['success'] is True
```

## 🔗 相關文檔

- [Pytest 官方文檔](https://docs.pytest.org/)
- [Flask Testing 指南](https://flask.palletsprojects.com/en/2.3.x/testing/)
- API Service 測試指南：`/Users/wubaizong/havital/cloud/api_service/TESTING_GUIDELINES.md`

---

**版本**: 1.0.0
**最後更新**: 2025-11-03
**維護者**: Havital Dev Team
