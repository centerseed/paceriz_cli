# 環境切換說明

## 🎯 設計理念

雙後端架構：同時運行 DEV 和 PROD 兩個後端實例，前端可以即時切換環境，無需重啟任何服務。

## 🏗️ 架構

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Port 5173)                      │
│                                                               │
│  環境切換器 → 自動切換 API URL 和 Firebase 配置              │
└─────────────────────────────────────────────────────────────┘
                           ↓                    ↓
          ┌────────────────────────┐  ┌────────────────────────┐
          │   DEV Backend          │  │   PROD Backend         │
          │   Port 8080            │  │   Port 8081            │
          │   ↓                    │  │   ↓                    │
          │   havital-dev          │  │   paceriz-prod         │
          │   (Firebase)           │  │   (Firebase)           │
          └────────────────────────┘  └────────────────────────┘
```

## 🚀 快速開始

### 方法 1：一鍵啟動所有服務（推薦）

```bash
cd /Users/wubaizong/havital/cloud/web_services/subscription_cli
./start_both.sh
```

這個腳本會：
1. 停止所有運行中的舊服務
2. 啟動 DEV 後端 (Port 8080)
3. 啟動 PROD 後端 (Port 8081)
4. 啟動前端 (Port 5173)

### 方法 2：分別啟動

```bash
# 啟動 DEV 後端
./restart_dev.sh

# 啟動 PROD 後端（在另一個終端）
./restart_prod.sh

# 啟動前端（如果 start_both.sh 沒有啟動）
cd frontend && npm run dev
```

## 🔄 環境切換

### 在網頁上切換

1. 打開 http://localhost:5173
2. 登入後，在頁面頂部可以看到環境切換器
3. 點擊環境切換器，選擇 **Development** 或 **Production**
4. 前端會自動重新加載並連接到對應的後端

### 自動檢測

- 前端會每 10 秒自動檢測後端環境
- 如果前後端環境不一致，會顯示紅色警告橫幅
- 警告橫幅會提示你需要執行的操作

## 📍 端點說明

| 服務 | Port | 環境 | Firebase Project | 用途 |
|------|------|------|------------------|------|
| Frontend | 5173 | 動態切換 | - | 網頁介面 |
| DEV Backend | 8080 | dev | havital-dev | 開發環境後端 |
| PROD Backend | 8081 | prod | paceriz-prod | 生產環境後端 |

## 📋 查看日誌

```bash
# DEV Backend
tail -f /tmp/subscription_backend_dev.log

# PROD Backend
tail -f /tmp/subscription_backend_prod.log

# Frontend
tail -f /tmp/subscription_frontend.log
```

## 🛑 停止服務

```bash
# 停止所有後端
pkill -f "python app.py"

# 停止前端
pkill -f "npm run dev"

# 或者只停止特定後端
pkill -f "PORT=8080 python app.py"  # 停止 DEV
pkill -f "PORT=8081 python app.py"  # 停止 PROD
```

## 🔍 健康檢查

```bash
# 檢查 DEV 後端
curl http://localhost:8080/health

# 檢查 PROD 後端
curl http://localhost:8081/health
```

應該看到類似輸出：
```json
{
  "status": "ok",
  "service": "admin-backend",
  "version": "1.0.0",
  "environment": "dev"  // 或 "prod"
}
```

## 🎨 環境差異

### DEV 環境 (Port 8080)
- Firebase Project: `havital-dev`
- 資料庫：開發測試資料
- 顏色標示：綠色
- 適用於：開發、測試新功能

### PROD 環境 (Port 8081)
- Firebase Project: `paceriz-prod`
- 資料庫：正式用戶資料
- 顏色標示：紅色
- 適用於：查看正式環境資料、緊急操作

## ⚠️ 注意事項

1. **兩個後端必須同時運行**才能自由切換環境
2. 如果只啟動一個後端，切換到另一個環境會顯示連線錯誤
3. 前端會自動檢測後端環境並顯示警告（如果不一致）
4. PROD 環境請謹慎操作，所有操作都會影響正式用戶

## 🔧 技術細節

### 前端環境配置
文件：`frontend/src/config/environments.ts`

```typescript
export const environments = {
  dev: {
    name: 'Development',
    apiBaseUrl: 'http://localhost:8080',  // DEV 後端
    firebase: { /* havital-dev config */ }
  },
  prod: {
    name: 'Production',
    apiBaseUrl: 'http://localhost:8081',  // PROD 後端
    firebase: { /* paceriz-prod config */ }
  }
}
```

### 環境切換機制
1. 用戶點擊環境切換器
2. 更新 `localStorage.currentEnvironment`
3. 頁面重新加載
4. Firebase 和 API client 使用新的配置初始化

### 後端環境檢測
1. 前端定期輪詢 `/health` 端點
2. 比對前端環境 vs 後端環境
3. 不一致時顯示警告橫幅

## 📝 常見問題

**Q: 為什麼需要兩個後端？**
A: 為了實現即時環境切換，無需重啟服務，提升開發效率。

**Q: 兩個後端會不會資源衝突？**
A: 不會，它們使用不同的 port 和不同的 Firebase project，完全隔離。

**Q: 如果我只想啟動一個環境怎麼辦？**
A: 使用 `./restart_dev.sh` 或 `./restart_prod.sh` 單獨啟動。

**Q: 環境切換後資料不對？**
A: 檢查頁面頂部的警告橫幅，確認對應的後端已經啟動。

## 🎯 最佳實踐

1. **每天開始工作時**：執行 `./start_both.sh` 啟動所有服務
2. **開發測試**：使用 DEV 環境
3. **查看正式資料**：切換到 PROD 環境
4. **結束工作**：執行 `pkill -f "python app.py"` 停止所有後端

## 📚 相關文件

- `start_both.sh` - 一鍵啟動所有服務
- `restart_dev.sh` - 啟動/重啟 DEV 後端
- `restart_prod.sh` - 啟動/重啟 PROD 後端
- `frontend/src/config/environments.ts` - 環境配置
- `frontend/src/components/Layout.tsx` - 環境切換 UI
