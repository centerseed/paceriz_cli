# Frontend Environment Setup

此項目使用環境變數來存儲敏感配置，如 Firebase API keys。

## ⚠️ 安全說明

**絕對不應該**將以下內容提交到 git：
- `.env.development`
- `.env.production`
- 任何包含實際憑證的 `.env*` 文件

所有 `.env*` 文件都已被添加到 `.gitignore`。

## 設定步驟

### 1. 複製環境模板
```bash
cp frontend/.env.example frontend/.env.development
```

### 2. 填充 Firebase 憑證

編輯 `frontend/.env.development` 並填入您的 Firebase 配置：

```env
# Development Firebase Configuration
VITE_FIREBASE_DEV_API_KEY=<您的開發 API Key>
VITE_FIREBASE_DEV_AUTH_DOMAIN=<您的開發 Auth Domain>
VITE_FIREBASE_DEV_PROJECT_ID=<您的開發 Project ID>
VITE_FIREBASE_DEV_STORAGE_BUCKET=<您的開發 Storage Bucket>
VITE_FIREBASE_DEV_MESSAGING_SENDER_ID=<您的開發 Messaging Sender ID>
VITE_FIREBASE_DEV_APP_ID=<您的開發 App ID>
VITE_FIREBASE_DEV_MEASUREMENT_ID=<您的開發 Measurement ID>

# Optional: API Base URLs
VITE_API_BASE_URL_DEV=http://localhost:8080
```

### 3. 生產環境配置

類似地創建 `frontend/.env.production`：

```bash
cp frontend/.env.example frontend/.env.production
```

然後填入生產環境的憑證。

## 獲取 Firebase 配置

1. 登入 [Firebase Console](https://console.firebase.google.com)
2. 選擇您的項目
3. 在設定 → 項目設定中，找到「Web 應用」配置
4. 複製配置值到相應的環境變數

## 開發

```bash
cd frontend
npm install
npm run dev
```

應用會自動從 `frontend/.env.development` 載入配置。

## 生產構建

```bash
npm run build
```

這將使用 `frontend/.env.production` 中的配置（或系統環境變數）。

## 環境變數名稱約定

- `VITE_*` 前綴：這些變數會暴露給前端應用
- `VITE_FIREBASE_DEV_*`：開發環境 Firebase 配置
- `VITE_FIREBASE_PROD_*`：生產環境 Firebase 配置

## 注意事項

- 永遠不要在 commit message 或代碼中洩露 API keys
- 定期輪換和更新您的 Firebase API keys
- 在共享開發環境中，每個開發者應該有各自的 `.env.development` 文件
- 使用 Firebase 安全規則來限制 API key 的存取權限
