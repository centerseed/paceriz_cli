#!/bin/bash

echo "🚀 同時啟動 DEV 和 PROD 環境後端..."
echo ""

# 停止所有之前的 backend
echo "🛑 停止所有運行中的後端服務..."
pkill -f "python app.py"

# 等待進程完全停止
sleep 2

echo ""
echo "=" * 50
echo "📦 啟動 DEV 後端 (Port 8080)..."
echo "=" * 50

# 啟動 DEV backend on port 8080
export GOOGLE_CLOUD_PROJECT=havital-dev
cd /Users/wubaizong/havital/cloud/web_services/subscription_cli/backend
source ~/.zshrc
conda activate api
export PYTHONPATH=/Users/wubaizong/havital/cloud/api_service:$PYTHONPATH
export SUPER_ADMIN_EMAILS="centerseedwu@gmail.com"
export ENV_TYPE=dev
export PORT=8080
python app.py > /tmp/subscription_backend_dev.log 2>&1 &
DEV_PID=$!
echo "   ✅ DEV Backend PID: $DEV_PID"
echo "   📋 DEV Backend log: /tmp/subscription_backend_dev.log"
echo ""

# 等待 dev backend 啟動
sleep 3

echo ""
echo "=" * 50
echo "📦 啟動 PROD 後端 (Port 8081)..."
echo "=" * 50

# 啟動 PROD backend on port 8081
export GOOGLE_CLOUD_PROJECT=paceriz-prod
cd /Users/wubaizong/havital/cloud/web_services/subscription_cli/backend
export ENV_TYPE=prod
export PORT=8081
python app.py > /tmp/subscription_backend_prod.log 2>&1 &
PROD_PID=$!
echo "   ✅ PROD Backend PID: $PROD_PID"
echo "   📋 PROD Backend log: /tmp/subscription_backend_prod.log"
echo ""

# 等待 prod backend 啟動
sleep 3

echo ""
echo "=" * 50
echo "🎨 啟動前端服務器 (Port 5173)..."
echo "=" * 50

# 停止之前的 frontend
pkill -f "npm run dev"
pkill -f "vite"
sleep 1

cd /Users/wubaizong/havital/cloud/web_services/subscription_cli/frontend
npm run dev > /tmp/subscription_frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   ✅ Frontend PID: $FRONTEND_PID"
echo "   📋 Frontend log: /tmp/subscription_frontend.log"
echo ""

echo "=" * 50
echo "✅ 所有服務已啟動！"
echo "=" * 50
echo ""
echo "📍 訪問地址:"
echo "   DEV Backend:   http://localhost:8080"
echo "   PROD Backend:  http://localhost:8081"
echo "   Frontend:      http://localhost:5173"
echo ""
echo "📋 查看日誌:"
echo "   DEV:      tail -f /tmp/subscription_backend_dev.log"
echo "   PROD:     tail -f /tmp/subscription_backend_prod.log"
echo "   Frontend: tail -f /tmp/subscription_frontend.log"
echo ""
echo "🛑 停止所有服務:"
echo "   pkill -f 'python app.py' && pkill -f 'npm run dev'"
echo ""
echo "💡 現在你可以在網頁上自由切換 DEV/PROD 環境，無需重啟！"
echo ""
