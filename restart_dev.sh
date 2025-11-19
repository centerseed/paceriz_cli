#!/bin/bash

echo "🛑 停止所有運行中的服務..."

# 停止所有 Python backend 進程
pkill -f "python app.py"

# 停止所有 npm dev server
pkill -f "npm run dev"
pkill -f "vite"

echo "✅ 已停止所有服務"
echo ""

# 等待進程完全停止
sleep 2

echo "🚀 啟動開發環境 (havital-dev)..."
echo ""

# 確保使用 dev 環境
export GOOGLE_CLOUD_PROJECT=havital-dev
gcloud config set project havital-dev

echo "📦 啟動後端服務器 (Port 8080)..."
cd /Users/wubaizong/havital/cloud/web_services/subscription_cli/backend
source ~/.zshrc
conda activate api
export PYTHONPATH=/Users/wubaizong/havital/cloud/api_service:$PYTHONPATH
export SUPER_ADMIN_EMAILS="centerseedwu@gmail.com"
export ENV_TYPE=dev
export PORT=8080
python app.py > /tmp/subscription_backend_dev.log 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"
echo "   Backend log: /tmp/subscription_backend_dev.log"
echo ""

# 等待後端啟動
sleep 3

echo "🎨 啟動前端服務器 (Port 5173)..."
cd /Users/wubaizong/havital/cloud/web_services/subscription_cli/frontend
npm run dev > /tmp/subscription_frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"
echo "   Frontend log: /tmp/subscription_frontend.log"
echo ""

echo "✅ 所有服務已啟動！"
echo ""
echo "📍 訪問地址:"
echo "   Backend:  http://localhost:8080"
echo "   Frontend: http://localhost:5173"
echo ""
echo "📋 查看日誌:"
echo "   Backend:  tail -f /tmp/subscription_backend_dev.log"
echo "   Frontend: tail -f /tmp/subscription_frontend.log"
echo ""
echo "🛑 停止服務: pkill -f 'python app.py' && pkill -f 'npm run dev'"
