# Admin Frontend

Admin 後台的 Frontend UI，使用 React + TypeScript + Tailwind CSS 構建。

## 📋 特點

- ⚛️ React 18 + TypeScript
- 🎨 Tailwind CSS + 響應式設計
- 🔥 Firebase Authentication
- 📊 Recharts 數據可視化
- 🔄 React Query 數據管理
- 🚀 Vite 快速構建

## 🚀 本地開發

### 安裝依賴

```bash
npm install
```

### 開發模式

```bash
npm run dev
```

訪問 http://localhost:5173

### 構建生產版本

```bash
npm run build
```

構建結果在 `dist/` 目錄。

### 預覽生產構建

```bash
npm run preview
```

## 🔐 環境變量

創建 `.env.local` 文件：

```env
VITE_API_URL=http://localhost:8080
VITE_FIREBASE_API_KEY=your-api-key
VITE_FIREBASE_PROJECT_ID=your-project-id
```

## 📦 部署

### Docker 構建

```bash
# 構建
docker build -t admin-frontend .

# 運行
docker run -p 8080:8080 admin-frontend
```

### Cloud Run 部署

使用部署腳本：

```bash
cd ../deploy
./deploy_frontend.sh dev  # 或 prod
```

## 🎨 頁面結構

```
src/
├── components/         # 通用組件
│   ├── Layout/        # 布局（Header, Sidebar）
│   ├── Charts/        # 圖表組件
│   └── Tables/        # 表格組件
├── pages/             # 頁面組件
│   ├── Dashboard/     # 儀表板
│   ├── Subscriptions/ # 訂閱管理
│   ├── FeatureTrials/ # 功能試用
│   ├── InviteCodes/   # 邀請碼
│   ├── AuditLogs/     # 審計日誌
│   └── Login/         # 登入頁面
├── services/          # API 服務
├── hooks/             # 自定義 Hooks
├── contexts/          # Context（Auth, Theme）
└── types/             # TypeScript 類型
```

## 💰 成本優化

部署配置為按需計費：

- `min-instances: 0` - 閒置時不收費
- `memory: 256Mi` - 小內存（靜態文件）
- Nginx 提供靜態文件，性能高

預估成本：
- 閒置時：$0/月
- 輕度使用：$0.5-1/月
- 中度使用：$2-3/月

## 📝 開發規範

### 組件命名

- 組件文件使用 PascalCase：`UserCard.tsx`
- Hook 文件使用 camelCase：`useAuth.ts`
- 工具文件使用 camelCase：`helpers.ts`

### 導入順序

```typescript
// 1. React 和第三方庫
import React from 'react'
import { useQuery } from '@tanstack/react-query'

// 2. 組件
import { Header } from '@/components/Layout/Header'

// 3. Hooks 和服務
import { useAuth } from '@/hooks/useAuth'
import { api } from '@/services/api'

// 4. 類型
import type { User } from '@/types'

// 5. 樣式
import './styles.css'
```

## 🔗 相關文檔

- [實施計劃](../../../api_service/docs/subscription/WEB_SERVICES_IMPLEMENTATION.md)
- [Admin UI 設計](../../../api_service/docs/subscription/ADMIN_WEB_UI.md)
- [部署指南](../docs/DEPLOYMENT.md)
