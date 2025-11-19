# Admin Backend API 測試指南

本文檔說明如何測試 Admin Backend API。

## 📋 前提條件

### 1. 設置環境

```bash
cd web_services/subscription_cli/backend

# 安裝依賴
pip install -r requirements.txt

# 設置環境變量
export ENV_TYPE=dev
export SUPER_ADMIN_EMAILS=your-google-email@gmail.com
export PORT=8080

# 如果需要，設置 Google Application Credentials
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

### 2. 啟動服務

```bash
python app.py
```

應該看到：
```
==================================================
🚀 Starting Admin Backend API
   Port: 8080
   Environment: dev
   Debug mode: True
   Allowed origins: [...]
==================================================
✅ Successfully imported api_service modules
✅ Successfully imported admin subscriptions blueprint
✅ Registered subscriptions blueprint at /api/v1/admin/subscriptions
```

---

## 🧪 測試方法

### 方法 1：使用測試腳本（推薦）

我們提供了一個 Python 測試腳本來自動獲取 Firebase Token 並測試 API。

```bash
# 使用測試腳本
python test_admin_api.py
```

這個腳本會：
1. 啟動本地 OAuth 流程
2. 獲取 Firebase ID Token
3. 測試所有 Admin API 端點

### 方法 2：手動獲取 Token

#### 步驟 1：獲取 Firebase ID Token

有幾種方式：

**選項 A：使用 Firebase Console**
1. 訪問 [Firebase Console](https://console.firebase.google.com/)
2. 選擇你的項目
3. 進入 Authentication → Users
4. 使用 Firebase Auth 登入你的 Google 帳號
5. 在瀏覽器開發者工具的 Network 標籤中找到 ID Token

**選項 B：使用 Firebase CLI**
```bash
# 安裝 Firebase CLI
npm install -g firebase-tools

# 登入
firebase login

# 獲取 ID Token（需要自己編寫腳本）
```

**選項 C：使用簡單的 Python 腳本**
```python
import firebase_admin
from firebase_admin import auth, credentials

# 初始化 Firebase
cred = credentials.Certificate('path/to/service-account.json')
firebase_admin.initialize_app(cred)

# 創建 custom token（僅用於測試）
custom_token = auth.create_custom_token('your-uid')
print(f"Custom Token: {custom_token.decode()}")

# 注意：custom token 需要通過 Firebase Auth REST API 交換為 ID token
```

#### 步驟 2：使用 Token 測試 API

將 Token 保存到環境變量：
```bash
export FIREBASE_TOKEN="your-firebase-id-token-here"
```

---

## 🔍 API 測試用例

### 1. 健康檢查（無需認證）

```bash
curl http://localhost:8080/health
```

預期輸出：
```json
{
  "status": "ok",
  "service": "admin-backend",
  "version": "1.0.0",
  "environment": "dev"
}
```

### 2. 獲取訂閱列表（需要認證）

```bash
curl -X GET http://localhost:8080/api/v1/admin/subscriptions \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -H "Content-Type: application/json"
```

預期輸出：
```json
{
  "data": [
    {
      "uid": "user123",
      "email": "user@example.com",
      "display_name": "Test User",
      "trial_start_at": "2025-11-03T00:00:00Z",
      "trial_end_at": "2025-11-17T23:59:59Z",
      "is_premium": false,
      ...
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 1,
    "total_pages": 1
  }
}
```

**測試不同的查詢參數**：
```bash
# 分頁
curl "http://localhost:8080/api/v1/admin/subscriptions?page=1&limit=10" \
  -H "Authorization: Bearer $FIREBASE_TOKEN"

# 篩選試用中的用戶
curl "http://localhost:8080/api/v1/admin/subscriptions?status=in_trial" \
  -H "Authorization: Bearer $FIREBASE_TOKEN"

# 篩選付費用戶
curl "http://localhost:8080/api/v1/admin/subscriptions?status=premium_active" \
  -H "Authorization: Bearer $FIREBASE_TOKEN"
```

### 3. 獲取訂閱詳情

```bash
curl -X GET http://localhost:8080/api/v1/admin/subscriptions/USER_UID \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -H "Content-Type: application/json"
```

預期輸出：
```json
{
  "user": {
    "uid": "USER_UID",
    "email": "user@example.com",
    "display_name": "Test User",
    "created_at": "2025-10-01T12:00:00Z"
  },
  "subscription": {
    "status": "in_trial",
    "has_premium_access": true,
    "trial_start_at": "2025-11-03T00:00:00Z",
    "trial_end_at": "2025-11-17T23:59:59Z",
    ...
  },
  "invite_code": {
    "code": "HAVIT123",
    "usage_count": 5,
    ...
  }
}
```

### 4. 延長訂閱

```bash
curl -X POST http://localhost:8080/api/v1/admin/subscriptions/USER_UID/extend \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "days": 30,
    "reason": "admin_grant",
    "notes": "VIP 大客戶特別贈送"
  }'
```

預期輸出：
```json
{
  "success": true,
  "new_end_at": "2026-01-30T23:59:59Z",
  "total_extension_days": 30
}
```

**測試不同的延長原因**：
```bash
# 補償
curl -X POST http://localhost:8080/api/v1/admin/subscriptions/USER_UID/extend \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "days": 7,
    "reason": "compensation",
    "notes": "系統故障補償"
  }'

# 促銷
curl -X POST http://localhost:8080/api/v1/admin/subscriptions/USER_UID/extend \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "days": 14,
    "reason": "promotion",
    "notes": "雙十一活動"
  }'
```

### 5. 取消訂閱

```bash
curl -X POST http://localhost:8080/api/v1/admin/subscriptions/USER_UID/cancel \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "user_request",
    "notes": "用戶主動要求取消"
  }'
```

預期輸出：
```json
{
  "success": true,
  "cancelled_at": "2025-11-03T14:30:00Z"
}
```

---

## 🔐 認證測試

### 測試超級管理員權限

確保你的 Email 在 `SUPER_ADMIN_EMAILS` 中：
```bash
export SUPER_ADMIN_EMAILS=your-google-email@gmail.com
```

使用你的 Google 帳戶 Token 測試 API。

### 測試普通管理員權限

1. 在 Firestore 中設置一個用戶為管理員：
   ```javascript
   // Collection: users
   // Document: {test_admin_uid}
   {
     "email": "testadmin@example.com",
     "is_admin": true,
     "admin_since": "2025-11-03T12:00:00Z"
   }
   ```

2. 使用這個用戶的 Token 測試 API。

### 測試未授權訪問

使用一個沒有 admin 權限的用戶 Token：
```bash
curl -X GET http://localhost:8080/api/v1/admin/subscriptions \
  -H "Authorization: Bearer $INVALID_TOKEN"
```

預期輸出：
```json
{
  "error": "Forbidden",
  "message": "Admin access required"
}
```

---

## 🐛 常見問題

### 1. "Firebase not initialized" 錯誤

**原因**: 沒有設置 Google Application Credentials

**解決方案**:
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

或者確保在正確的 GCP 項目環境中運行。

### 2. "Super admin emails configured: 0 admin(s)" 警告

**原因**: 沒有設置 `SUPER_ADMIN_EMAILS`

**解決方案**:
```bash
export SUPER_ADMIN_EMAILS=your-google-email@gmail.com
```

### 3. "Token expired" 錯誤

**原因**: Firebase ID Token 過期（有效期 1 小時）

**解決方案**: 重新獲取新的 ID Token。

### 4. "Service not available" 錯誤

**原因**: api_service 模塊導入失敗

**解決方案**: 確保 api_service 路徑正確，並且 Firebase 已初始化。

---

## 📊 審計日誌驗證

所有管理員操作都會記錄到 Firestore 的 `admin_audit_logs` collection。

在 Firestore Console 中檢查：
```
admin_audit_logs/{log_id}:
  - timestamp: 2025-11-03T14:30:00Z
  - admin_uid: "your_uid"
  - admin_email: "your-email@gmail.com"
  - admin_role: "super_admin"
  - action_type: "extend_subscription"
  - target_uid: "user123"
  - details: {days: 30, reason: "admin_grant", ...}
  - ip_address: "127.0.0.1"
  - success: true
```

---

## 🎯 完整測試流程

```bash
# 1. 設置環境
export ENV_TYPE=dev
export SUPER_ADMIN_EMAILS=your-google-email@gmail.com
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# 2. 啟動服務
python app.py

# 3. 獲取 Firebase Token（在另一個終端）
# （使用測試腳本或手動獲取）
export FIREBASE_TOKEN="your-token-here"

# 4. 測試健康檢查
curl http://localhost:8080/health

# 5. 測試訂閱列表
curl -H "Authorization: Bearer $FIREBASE_TOKEN" \
     http://localhost:8080/api/v1/admin/subscriptions

# 6. 測試延長訂閱
curl -X POST \
     -H "Authorization: Bearer $FIREBASE_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"days": 30, "reason": "admin_grant", "notes": "測試"}' \
     http://localhost:8080/api/v1/admin/subscriptions/USER_UID/extend

# 7. 檢查 Firestore 審計日誌
# 訪問 Firebase Console → Firestore → admin_audit_logs
```

---

## 📝 下一步

- [ ] 實施 Dashboard API
- [ ] 實施 Audit Logs API
- [ ] 實施 Frontend UI
- [ ] 集成測試
- [ ] 部署到 Cloud Run

---

**版本**: 1.0.0
**最後更新**: 2025-11-03
