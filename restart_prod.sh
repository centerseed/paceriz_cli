#!/bin/bash

echo "🚀 啟動生產環境後端 (paceriz-prod) on Port 8081..."
echo ""

# 停止之前的 prod backend（如果有）
pkill -f "PORT=8081 python app.py"

# 等待進程完全停止
sleep 1

# 確保使用 prod 環境
export GOOGLE_CLOUD_PROJECT=paceriz-prod

echo "📦 啟動 PROD 後端服務器 (Port 8081)..."
cd /Users/wubaizong/havital/cloud/web_services/subscription_cli/backend
source ~/.zshrc
conda activate api
export PYTHONPATH=/Users/wubaizong/havital/cloud/api_service:$PYTHONPATH
export SUPER_ADMIN_EMAILS="centerseedwu@gmail.com"
export ENV_TYPE=prod
export PORT=8081
python app.py > /tmp/subscription_backend_prod.log 2>&1 &
BACKEND_PID=$!
echo "   ✅ PROD Backend PID: $BACKEND_PID"
echo "   📋 PROD Backend log: /tmp/subscription_backend_prod.log"
echo ""

# 等待後端啟動
sleep 3

echo "✅ PROD 後端已啟動！"
echo ""
echo "📍 訪問地址:"
echo "   PROD Backend:  http://localhost:8081"
echo ""
echo "📋 查看日誌:"
echo "   tail -f /tmp/subscription_backend_prod.log"
echo ""
echo "🛑 停止服務: pkill -f 'PORT=8081 python app.py'"
echo ""
