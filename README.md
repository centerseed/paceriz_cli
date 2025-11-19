# Subscription CLI - Admin 管理後台

Havital 訂閱系統管理後台，提供完整的訂閱管理、數據分析、功能試用管理等功能。

## 📋 項目概述

### 特點

- ✅ **完全隔離**: 與 api_service 完全分離，獨立部署
- ✅ **代碼復用**: Backend 引用 api_service 的訂閱服務和數據模型
- ✅ **三層權限**: 超級管理員、普通管理員、一般用戶
- ✅ **審計日誌**: 記錄所有管理員操作
- ✅ **成本優化**: 按需計費，閒置時完全不收費（$0/月）

### 技術棧

**Backend**:
- Flask
- Firebase Admin SDK
- 引用 api_service 代碼

**Frontend**:
- React 18 + TypeScript
- Tailwind CSS
- Firebase Authentication
- React Query
- Recharts

**部署**:
- Google Cloud Run
- Docker multi-architecture (amd64, arm64)
- 按需計費配置

## 🗂️ 項目結構

```
subscription_cli/
├── backend/                # Admin Backend API (Flask)
│   ├── api/admin/         # Admin API 路由
│   ├── middleware/        # 認證中間件
│   ├── services/          # 業務服務
│   ├── config/            # 配置
│   └── app.py             # 應用入口
│
├── frontend/              # Admin Frontend (React)
│   ├── src/
│   │   ├── components/   # 通用組件
│   │   ├── pages/        # 頁面組件
│   │   ├── services/     # API 服務
│   │   └── hooks/        # 自定義 Hooks
│   └── public/
│
├── deploy/                # 部署腳本
│   ├── build_backend.sh
│   ├── deploy_backend.sh
│   ├── build_frontend.sh
│   ├── deploy_frontend.sh
│   └── deploy_all.sh
│
└── docs/                  # 文檔
    ├── API_REFERENCE.md
    ├── DEPLOYMENT.md
    └── PERMISSION_MODEL.md
```

## 🚀 快速開始

### 1. Backend 本地開發

```bash
cd backend

# 安裝依賴
pip install -r requirements.txt

# 設置環境變量
export ENV_TYPE=dev
export SUPER_ADMIN_EMAILS=your-email@gmail.com
export PORT=8080

# 運行
python app.py
```

訪問 http://localhost:8080

### 2. Frontend 本地開發

```bash
cd frontend

# 安裝依賴
npm install

# 運行
npm run dev
```

訪問 http://localhost:5173

### 3. 部署到 Cloud Run

```bash
cd deploy

# 設置超級管理員（首次）
echo 'your-email@gmail.com' | gcloud secrets create super-admin-emails --data-file=-

# 一鍵部署 Backend + Frontend
./deploy_all.sh dev  # 或 prod
```

## 🔐 權限模型

### 三層權限架構

```
超級管理員 (Super Admin)
  ↓ 環境變量白名單
  ├─ 可以添加/移除普通管理員
  ├─ 可以執行所有操作
  └─ 查看所有審計日誌

普通管理員 (Admin)
  ↓ Firestore: is_admin = true
  ├─ 可以管理訂閱
  ├─ 可以創建功能試用
  └─ 查看自己的審計日誌

一般用戶 (User)
  └─ 無法訪問 Admin UI
```

### 配置超級管理員

```bash
# 在 GCP Secret Manager 設置
echo 'admin1@gmail.com,admin2@gmail.com' | \
  gcloud secrets create super-admin-emails --data-file=-
```

### 配置普通管理員

在 Firestore 中設置：

```javascript
// Collection: users
// Document: {uid}
{
  "email": "admin@example.com",
  "is_admin": true,
  "admin_since": Timestamp
}
```

## 💰 成本優化

### 配置說明

所有服務都配置為 **按需計費**（min-instances: 0）：

- ✅ 閒置時完全不收費
- ✅ 有請求時自動啟動（冷啟動 2-5 秒）
- ✅ 15 分鐘無流量自動關閉

### 成本預估

| 使用場景 | Backend | Frontend | 總計 |
|---------|---------|----------|------|
| 完全閒置 | $0/月 | $0/月 | **$0/月** |
| 輕度使用（每天 10-50 次） | $1-3/月 | $0.5-1/月 | **$2-4/月** |
| 中度使用（每天 100-200 次） | $5-10/月 | $2-3/月 | **$7-13/月** |

**對比常駐實例**（min-instances: 1）：
- 即使閒置也要 $15-23/月
- **節省**: 閒置時節省 100%，輕度使用節省 80-90%

## 📚 功能列表

### ✅ 已實現

- [x] 基礎架構搭建
- [x] Backend 應用入口
- [x] Frontend 項目配置
- [x] 部署腳本
- [x] 成本優化配置
- [x] 文檔

### 🚧 開發中

- [ ] 認證中間件實現
- [ ] 訂閱管理 API
- [ ] 功能試用管理 API
- [ ] 數據儀表板 API
- [ ] 審計日誌系統
- [ ] Frontend UI 實現

## 📖 文檔

### 項目文檔

- [Backend README](./backend/README.md) - Backend 開發指南
- [Frontend README](./frontend/README.md) - Frontend 開發指南
- [部署指南](./deploy/README.md) - 部署腳本使用說明

### 設計文檔

- [實施計劃](../../api_service/docs/subscription/WEB_SERVICES_IMPLEMENTATION.md) - 完整實施計劃
- [Admin UI 設計](../../api_service/docs/subscription/ADMIN_WEB_UI.md) - UI/UX 設計
- [訂閱系統設計](../../api_service/docs/subscription/SUBSCRIPTION_PDD.md) - 產品設計

## 🔧 開發工作流

### 1. 開發新功能

```bash
# 1. 在 Backend 實現 API
cd backend/api/admin
# 創建新的 API 路由文件

# 2. 在 Frontend 實現 UI
cd frontend/src/pages
# 創建新的頁面組件

# 3. 本地測試
cd backend && python app.py  # Terminal 1
cd frontend && npm run dev   # Terminal 2

# 4. 部署
cd deploy && ./deploy_all.sh dev
```

### 2. 更新部署

```bash
# 只更新 Backend
cd deploy && ./deploy_backend.sh dev

# 只更新 Frontend
cd deploy && ./deploy_frontend.sh dev

# 同時更新
cd deploy && ./deploy_all.sh dev
```

## 🐛 故障排除

### Backend 無法啟動

```bash
# 檢查環境變量
echo $SUPER_ADMIN_EMAILS
echo $ENV_TYPE

# 檢查 api_service 路徑
ls -la ../../api_service
```

### Frontend 構建失敗

```bash
# 清理依賴
rm -rf node_modules package-lock.json
npm install

# 重新構建
npm run build
```

### 部署失敗

```bash
# 檢查 GCP 認證
gcloud auth list
gcloud config get-value project

# 檢查 Secret Manager
gcloud secrets list
gcloud secrets versions access latest --secret="super-admin-emails"
```

## 🔗 相關鏈接

### 生產環境

- Backend API: https://admin-api.havital.com
- Frontend UI: https://admin.havital.com

### 開發環境

- Backend API: https://admin-backend-xxx.run.app
- Frontend UI: https://admin-frontend-xxx.run.app

### GCP Console

- [Cloud Run Services](https://console.cloud.google.com/run)
- [Secret Manager](https://console.cloud.google.com/security/secret-manager)
- [Cloud Logging](https://console.cloud.google.com/logs)

## 📝 注意事項

1. **不要直接修改 api_service**: Backend 只引用，不修改
2. **超級管理員配置**: 必須在 Secret Manager 設置才能登入
3. **成本監控**: 定期檢查 Cloud Run 使用量和成本
4. **安全**: 所有操作都記錄到審計日誌

## 🤝 貢獻指南

1. Fork 項目
2. 創建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

## 📄 License

Copyright © 2025 Havital. All rights reserved.

---

**Version**: 1.0.0
**Last Updated**: 2025-11-03
**Status**: Phase 1 Complete ✅ (基礎架構搭建完成)
