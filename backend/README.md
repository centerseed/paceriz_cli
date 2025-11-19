# Admin Backend API

Admin 後台的 Backend API 服務，提供訂閱管理、數據儀表板等功能。

## 📋 特點

- ✅ 復用 api_service 的現有代碼（訂閱服務、數據模型）
- ✅ 三層權限控制（超級管理員、普通管理員、一般用戶）
- ✅ 審計日誌記錄所有管理員操作
- ✅ 按需計費配置（min-instances: 0）

## 🚀 本地開發

### 環境準備

```bash
# 安裝依賴
pip install -r requirements.txt

# 設置環境變量
export ENV_TYPE=dev
export SUPER_ADMIN_EMAILS=your-email@gmail.com
export PORT=8080
```

### 運行應用

```bash
# 開發模式
python app.py

# 生產模式（使用 Gunicorn）
gunicorn --bind 0.0.0.0:8080 --workers 2 --threads 4 app:app
```

### 測試

```bash
# 健康檢查
curl http://localhost:8080/health

# 預期輸出
{
  "status": "ok",
  "service": "admin-backend",
  "version": "1.0.0",
  "environment": "dev"
}
```

## 🔐 權限配置

### 超級管理員

超級管理員通過環境變量配置：

```bash
# 單個管理員
export SUPER_ADMIN_EMAILS=admin@example.com

# 多個管理員（逗號分隔）
export SUPER_ADMIN_EMAILS=admin1@example.com,admin2@example.com
```

### 普通管理員

普通管理員在 Firestore 中配置：

```javascript
// Firestore: users/{uid}
{
  "email": "admin@example.com",
  "is_admin": true,
  "admin_since": Timestamp
}
```

## 📦 部署

### Docker 構建

```bash
# 構建
docker build -t admin-backend .

# 運行
docker run -p 8080:8080 \
  -e ENV_TYPE=dev \
  -e SUPER_ADMIN_EMAILS=your-email@gmail.com \
  admin-backend
```

### Cloud Run 部署

使用部署腳本：

```bash
cd ../deploy
./deploy_backend.sh dev  # 或 prod
```

## 📚 API 文檔

### 健康檢查

```http
GET /health
GET /healthz

Response:
{
  "status": "ok",
  "service": "admin-backend",
  "version": "1.0.0"
}
```

### Admin API（TODO: 實施後更新）

- `/api/v1/admin/subscriptions` - 訂閱管理
- `/api/v1/admin/dashboard` - 數據儀表板
- `/api/v1/admin/audit-logs` - 審計日誌

## 🔧 項目結構

```
backend/
├── api/
│   └── admin/          # Admin API 路由
├── middleware/         # 認證中間件
├── services/           # 業務服務
├── config/             # 配置
├── app.py              # 應用入口
├── requirements.txt    # 依賴
└── Dockerfile          # Docker 配置
```

## 💰 成本優化

部署配置為按需計費：

- `min-instances: 0` - 閒置時不收費
- `max-instances: 3` - 控制成本上限
- `memory: 512Mi` - 適當的內存配置
- `cpu: 1` - 1 vCPU 足夠

預估成本：
- 閒置時：$0/月
- 輕度使用（每天 10-50 次）：$1-3/月
- 中度使用（每天 100-200 次）：$5-10/月

## 📝 注意事項

1. **引用 api_service 代碼**：Backend 通過設置 `sys.path` 來引用 api_service 的代碼
2. **Firebase 初始化**：使用 api_service 的 Firebase 配置
3. **環境變量**：確保設置 `SUPER_ADMIN_EMAILS` 才能登入
4. **CORS**：只允許 `admin.havital.com` 和 `localhost`

## 🔗 相關文檔

- [實施計劃](../../../api_service/docs/subscription/WEB_SERVICES_IMPLEMENTATION.md)
- [Admin UI 設計](../../../api_service/docs/subscription/ADMIN_WEB_UI.md)
- [部署指南](../docs/DEPLOYMENT.md)
