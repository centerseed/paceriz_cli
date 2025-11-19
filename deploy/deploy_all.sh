#!/bin/bash
#
# Deploy Both Admin Backend and Frontend to Cloud Run
#
# Usage:
#   ./deploy_all.sh dev   # Deploy to dev environment
#   ./deploy_all.sh prod  # Deploy to prod environment
#

set -e

ENV_TYPE=${1:-dev}

if [ "$ENV_TYPE" != "dev" ] && [ "$ENV_TYPE" != "prod" ]; then
    echo "❌ Error: ENV_TYPE must be 'dev' or 'prod'"
    echo "Usage: $0 {dev|prod}"
    exit 1
fi

echo "========================================"
echo "🚀 Deploying Admin System"
echo "   Environment: $ENV_TYPE"
echo "   💰 Cost-Optimized Configuration"
echo "   (閒置時完全不收費)"
echo "========================================"
echo ""

# 檢查 gcloud 是否已登入
if ! gcloud auth print-access-token &>/dev/null; then
    echo "❌ Error: Not logged in to gcloud"
    echo "Please run: gcloud auth login"
    exit 1
fi

# === Step 1: Deploy Backend ===
echo "📦 Step 1/2: Deploying Backend..."
echo "========================================"
./deploy_backend.sh $ENV_TYPE

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Backend deployment failed"
    exit 1
fi

echo ""
echo "✅ Backend deployed successfully!"
echo ""

# 等待 Backend 完全啟動
echo "⏳ Waiting for Backend to be ready (10 seconds)..."
sleep 10
echo ""

# === Step 2: Deploy Frontend ===
echo "📦 Step 2/2: Deploying Frontend..."
echo "========================================"
./deploy_frontend.sh $ENV_TYPE

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Frontend deployment failed"
    exit 1
fi

echo ""
echo "========================================"
echo "✅ All services deployed successfully!"
echo ""
echo "📊 成本預估："
echo "   - Backend (閒置): $0/月"
echo "   - Frontend (閒置): $0/月"
echo "   - 合計閒置成本: $0/月"
echo "   - 輕度使用: ~$2-5/月"
echo "   - 中度使用: ~$5-10/月"
echo ""
echo "🎉 Admin System is ready to use!"
echo ""
echo "📝 Next steps:"
echo "   1. 設置 Super Admin emails (如果尚未設置)"
echo "   2. 配置 Cloud Load Balancer (如需自定義域名)"
echo "   3. 在 Firestore 添加普通管理員 (設置 is_admin: true)"
echo "========================================"
