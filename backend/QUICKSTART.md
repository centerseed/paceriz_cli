# 🚀 Admin Backend API 快速開始

5 分鐘內啟動並測試 Admin Backend API！

## 📋 步驟 1：環境設置

```bash
# 使用 api_service 的 conda 環境（已包含所有依賴）
conda activate api

# 切換到 backend 目錄
cd /Users/wubaizong/havital/cloud/web_services/subscription_cli/backend
```

**注意**：Admin Backend 引用 api_service 的代碼，因此使用相同的 conda 環境，無需重複安裝依賴。

## 🔑 步驟 2：配置環境變量

```bash
# 必須設置（替換為你的 Google Email）
export SUPER_ADMIN_EMAILS=your-google-email@gmail.com

# 可選設置
export ENV_TYPE=dev
export PORT=8080

# Firebase 憑證（如果本地沒有默認憑證）
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

**注意**：確保你的 Email 是你登入 Firebase 時使用的 Google 帳號。

## 🚀 步驟 3：啟動服務

```bash
python app.py
```

你應該看到：
```
==================================================
🚀 Starting Admin Backend API
   Port: 8080
   Environment: dev
   Debug mode: True
==================================================
✅ Successfully imported api_service modules
✅ Successfully imported admin subscriptions blueprint
✅ Registered subscriptions blueprint at /api/v1/admin/subscriptions
* Running on http://0.0.0.0:8080
```

## 🧪 步驟 4：測試 API

### 測試 1：健康檢查（無需認證）

在另一個終端運行：
```bash
curl http://localhost:8080/health
```

你應該看到：
```json
{
  "status": "ok",
  "service": "admin-backend",
  "version": "1.0.0",
  "environment": "dev"
}
```

### 測試 2：獲取訂閱列表（需要認證）

#### 方法 A：使用測試腳本（簡單但不完整）

```bash
python test_admin_api.py
```

⚠️ **注意**：這個腳本使用 Custom Token，可能無法直接用於 API 認證。

#### 方法 B：使用真實的 Firebase Token（推薦）

你需要一個真實的 Firebase ID Token。有幾種獲取方式：

**選項 1：從你的 App 獲取**
1. 在你的 App 中登入（使用 Google OAuth）
2. 在瀏覽器開發者工具中找到 Firebase ID Token
3. 複製 Token

**選項 2：使用 Firebase REST API**
```bash
# 如果你有 Custom Token，可以交換為 ID Token
curl -X POST 'https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key=YOUR_FIREBASE_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{"token": "YOUR_CUSTOM_TOKEN", "returnSecureToken": true}'

# 從響應中提取 idToken
```

**測試 API**：
```bash
# 設置 Token
export FIREBASE_TOKEN="your-firebase-id-token-here"

# 測試獲取訂閱列表
curl -H "Authorization: Bearer $FIREBASE_TOKEN" \
     http://localhost:8080/api/v1/admin/subscriptions

# 測試延長訂閱
curl -X POST \
     -H "Authorization: Bearer $FIREBASE_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"days": 30, "reason": "admin_grant", "notes": "測試延長"}' \
     http://localhost:8080/api/v1/admin/subscriptions/USER_UID/extend
```

## ✅ 驗證結果

### 1. 檢查服務日誌

在啟動服務的終端中，你應該看到：
```
✅ Admin your-email@gmail.com listed subscriptions (page=1, limit=50)
✅ Admin your-email@gmail.com extended subscription for user123 by 30 days
```

### 2. 檢查 Firestore 審計日誌

訪問 [Firebase Console](https://console.firebase.google.com/)：
1. 選擇你的項目（havital-dev 或 paceriz-prod）
2. 進入 Firestore Database
3. 查看 `admin_audit_logs` collection
4. 你應該看到你的操作記錄

## 📚 完整測試指南

詳細的測試說明請參考：
- [TESTING.md](./TESTING.md) - 完整的測試指南
- [API 文檔](../docs/API_REFERENCE.md) - API 詳細文檔（TODO）

## 🐛 常見問題

### 問題 1："Firebase not initialized" 錯誤

**解決方案**：
```bash
# 確保設置了 Firebase 憑證
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# 或者使用 gcloud 默認憑證
gcloud auth application-default login
```

### 問題 2："No super admin emails configured" 警告

**解決方案**：
```bash
export SUPER_ADMIN_EMAILS=your-google-email@gmail.com
```

### 問題 3："Unauthorized" 或 "Forbidden" 錯誤

**可能原因**：
1. Token 已過期（Firebase ID Token 有效期 1 小時）
2. Email 不在超級管理員白名單中
3. Token 無效

**解決方案**：
1. 重新獲取新的 ID Token
2. 確認 `SUPER_ADMIN_EMAILS` 設置正確
3. 使用真實的 Firebase ID Token（不是 Custom Token）

### 問題 4："Service not available" 錯誤

**可能原因**：api_service 模塊無法導入

**解決方案**：
```bash
# 確保 api_service 路徑正確
ls ../../api_service

# 確保可以導入 Firebase
python -c "from core.infrastructure.firebase_init import db; print('OK')"
```

## 🎯 下一步

恭喜！你已經成功啟動並測試了 Admin Backend API。

接下來可以：
1. 📱 實現 Frontend Admin UI（使用 React）
2. 📊 添加更多 API 端點（Dashboard, Audit Logs）
3. 🚀 部署到 Cloud Run
4. 🧪 編寫更完整的測試

查看 [README.md](./README.md) 了解更多信息。

---

**需要幫助？**

查看詳細文檔：
- [TESTING.md](./TESTING.md) - 測試指南
- [README.md](./README.md) - 項目文檔
- [實施計劃](../../../api_service/docs/subscription/WEB_SERVICES_IMPLEMENTATION.md)
