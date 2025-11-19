# 訂閱管理後台設置指南

## 🔐 Firebase Authentication 設置

### 1. 啟用 Google Sign-in Provider

**重要**：在使用 Google 登入前，您需要先在 Firebase Console 啟用此功能。

步驟：
1. 前往 [Firebase Console](https://console.firebase.google.com/)
2. 選擇項目：**havital-dev**
3. 點擊左側菜單 **Authentication**
4. 切換到 **Sign-in method** 標籤
5. 找到 **Google** 提供者
6. 點擊 **Enable** / **啟用**
7. 設置支持郵箱（預設為您的 Firebase 帳號郵箱）
8. 點擊 **Save** / **儲存**

### 2. 驗證 Super Admin 設置

您的 Super Admin 郵箱是：**centerseedwu@gmail.com**

此郵箱通過環境變數 `SUPER_ADMIN_EMAILS` 設置，已經在後端啟動時配置。

## 🚀 啟動服務

### Backend (端口 8080)

```bash
cd /Users/wubaizong/havital/cloud/web_services/subscription_cli/backend
source ~/.zshrc
conda activate api
export SUPER_ADMIN_EMAILS="centerseedwu@gmail.com"
export ENV_TYPE=dev
export PORT=8080
python app.py
```

### Frontend (端口 5173)

```bash
cd /Users/wubaizong/havital/cloud/web_services/subscription_cli/frontend
npm run dev
```

## 🧪 測試登入流程

### 方法 1：Google OAuth（推薦）

1. 打開前端：http://localhost:5173
2. 點擊「使用 Google 帳號登入」按鈕
3. 選擇您的 Google 帳號 (centerseedwu@gmail.com)
4. 授權應用訪問
5. 自動跳轉到訂閱管理頁面

### 方法 2：Email/Password

需要先在 Firebase Console 手動創建用戶：
1. Firebase Console → Authentication → Users
2. 點擊 **Add user**
3. 輸入 Email 和 Password
4. 使用這組帳密在登入頁面登入

## 🔍 故障排除

### 問題：401 Unauthorized

**可能原因**：
1. Google Sign-in Provider 未在 Firebase 啟用
2. 環境變數 `SUPER_ADMIN_EMAILS` 未設置
3. Firebase token 過期或無效

**解決方案**：
1. 確認 Firebase Console 已啟用 Google Provider
2. 重新啟動後端（確保環境變數正確）
3. 在前端清除 localStorage 並重新登入

### 檢查後端日誌

```bash
# 查看後端是否正確載入 Super Admin
cd /Users/wubaizong/havital/cloud/web_services/subscription_cli/backend
grep "Super admin" <後端日誌文件>
```

預期輸出：
```
✅ Super admin emails configured: 1 admin(s)
   - centerseedwu@gmail.com
```

### 測試 API 健康狀態

```bash
curl http://localhost:8080/health
```

預期輸出：
```json
{
  "environment": "dev",
  "service": "admin-backend",
  "status": "ok",
  "version": "1.0.0"
}
```

## 📋 權限系統

### 三級權限架構

1. **Super Admin**（超級管理員）
   - 通過環境變數 `SUPER_ADMIN_EMAILS` 設置
   - 擁有所有權限
   - 可以管理其他 Admin

2. **Admin**（普通管理員）
   - 在 Firestore `users` 集合中設置 `is_admin: true`
   - 可以管理訂閱
   - 無法管理其他 Admin

3. **User**（一般用戶）
   - 普通應用用戶
   - 無法訪問管理後台

### 當前 Super Admin

- **centerseedwu@gmail.com**

## 🎯 下一步

1. ✅ 啟用 Firebase Google Sign-in Provider
2. ✅ 測試登入流程
3. ✅ 驗證訂閱列表顯示
4. ✅ 測試延長訂閱功能
5. [ ] 部署到 Cloud Run（需要時）

## 🆘 需要幫助？

如果遇到問題，請提供：
1. 前端瀏覽器 Console 的錯誤訊息
2. 後端日誌輸出
3. 具體的操作步驟

---

**版本**: 1.0.0
**最後更新**: 2025-11-03
**環境**: havital-dev
