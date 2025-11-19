# 部署腳本

這個目錄包含所有用於構建和部署 Admin 系統的腳本。

## 📋 腳本列表

| 腳本 | 用途 | 使用方式 |
|------|------|---------|
| `build_backend.sh` | 構建 Backend Docker image | `./build_backend.sh dev [true]` |
| `build_frontend.sh` | 構建 Frontend Docker image | `./build_frontend.sh dev [true]` |
| `deploy_backend.sh` | 部署 Backend 到 Cloud Run | `./deploy_backend.sh dev` |
| `deploy_frontend.sh` | 部署 Frontend 到 Cloud Run | `./deploy_frontend.sh dev` |
| `deploy_all.sh` | 一鍵部署 Backend + Frontend | `./deploy_all.sh dev` |

## 🚀 快速開始

### 1. 首次部署前的準備

```bash
# 1. 登入 Google Cloud
gcloud auth login

# 2. 設置超級管理員列表
echo 'your-email@gmail.com' | gcloud secrets create super-admin-emails --data-file=-

# 3. 驗證配置
gcloud secrets versions access latest --secret="super-admin-emails"
```

### 2. 部署到 Dev 環境

```bash
# 一鍵部署 Backend + Frontend
./deploy_all.sh dev
```

### 3. 部署到 Prod 環境

```bash
# 一鍵部署到生產環境
./deploy_all.sh prod
```

## 📦 單獨構建和部署

### Backend

```bash
# 僅構建（不推送）
./build_backend.sh dev

# 構建並推送到 GCR
./build_backend.sh dev true

# 部署到 Cloud Run
./deploy_backend.sh dev
```

### Frontend

```bash
# 僅構建（不推送）
./build_frontend.sh dev

# 構建並推送到 GCR
./build_frontend.sh dev true

# 部署到 Cloud Run
./deploy_frontend.sh dev
```

## 🔐 超級管理員配置

### 創建超級管理員

```bash
# 首次創建
echo 'your-email@gmail.com' | gcloud secrets create super-admin-emails --data-file=-

# 添加多個管理員（逗號分隔）
echo 'admin1@gmail.com,admin2@gmail.com' | gcloud secrets create super-admin-emails --data-file=-
```

### 更新超級管理員列表

```bash
# 更新現有 secret
echo 'new-admin@gmail.com' | gcloud secrets versions add super-admin-emails --data-file=-

# 查看當前配置
gcloud secrets versions access latest --secret="super-admin-emails"
```

## 💰 成本優化說明

所有部署都使用成本優化配置：

### Backend
```yaml
min-instances: 0      # 閒置時完全不收費
max-instances: 3      # 限制最大實例
memory: 512Mi         # 適當的內存
cpu: 1                # 1 vCPU
timeout: 300s         # 5 分鐘超時
cpu-throttling: true  # 啟用 CPU 節流
```

### Frontend
```yaml
min-instances: 0      # 閒置時完全不收費
max-instances: 3      # 限制最大實例
memory: 256Mi         # 小內存（靜態文件）
cpu: 1                # 1 vCPU
timeout: 60s          # 1 分鐘超時
cpu-throttling: true  # 啟用 CPU 節流
```

### 成本預估

| 使用場景 | Backend | Frontend | 總計 |
|---------|---------|----------|------|
| 完全閒置 | $0/月 | $0/月 | **$0/月** |
| 輕度使用（每天 10-50 次） | $1-3/月 | $0.5-1/月 | **$2-4/月** |
| 中度使用（每天 100-200 次） | $5-10/月 | $2-3/月 | **$7-13/月** |

## 🔍 驗證部署

### 檢查服務狀態

```bash
# Backend
gcloud run services describe admin-backend --region asia-east1

# Frontend
gcloud run services describe admin-frontend --region asia-east1
```

### 測試健康檢查

```bash
# 獲取服務 URL
BACKEND_URL=$(gcloud run services describe admin-backend --region asia-east1 --format="value(status.url)")
FRONTEND_URL=$(gcloud run services describe admin-frontend --region asia-east1 --format="value(status.url)")

# 測試 Backend
curl $BACKEND_URL/health

# 測試 Frontend
curl $FRONTEND_URL/health
```

### 檢查成本設置

```bash
# 驗證 min-instances = 0
gcloud run services describe admin-backend --region asia-east1 \
    --format="value(spec.template.metadata.annotations['autoscaling.knative.dev/minScale'])"

# 應該輸出: 0
```

## 🐛 常見問題

### 1. 權限錯誤

```bash
# 確保有正確的權限
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="user:your-email@gmail.com" \
    --role="roles/run.admin"
```

### 2. Docker 構建失敗

```bash
# 清理 Docker cache
docker system prune -a

# 重新構建
./build_backend.sh dev
```

### 3. Secret Manager 錯誤

```bash
# 檢查 secret 是否存在
gcloud secrets list

# 創建 secret（如果不存在）
echo 'your-email@gmail.com' | gcloud secrets create super-admin-emails --data-file=-
```

### 4. 部署超時

```bash
# 增加部署超時時間
gcloud run deploy admin-backend \
    --timeout 600 \
    ...
```

## 📚 相關文檔

- [Backend README](../backend/README.md)
- [Frontend README](../frontend/README.md)
- [實施計劃](../../../api_service/docs/subscription/WEB_SERVICES_IMPLEMENTATION.md)

## 🔗 有用的 gcloud 命令

```bash
# 查看所有 Cloud Run 服務
gcloud run services list --region asia-east1

# 查看服務日誌
gcloud run services logs read admin-backend --region asia-east1

# 刪除服務
gcloud run services delete admin-backend --region asia-east1

# 更新環境變量
gcloud run services update admin-backend \
    --region asia-east1 \
    --set-env-vars "KEY=VALUE"
```
