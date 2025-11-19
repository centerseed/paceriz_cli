#!/bin/bash
#
# Deploy Admin Backend to Cloud Run
#
# Usage:
#   ./deploy_backend.sh dev   # Deploy to dev environment
#   ./deploy_backend.sh prod  # Deploy to prod environment
#

set -e

ENV_TYPE=${1:-dev}

if [ "$ENV_TYPE" != "dev" ] && [ "$ENV_TYPE" != "prod" ]; then
    echo "❌ Error: ENV_TYPE must be 'dev' or 'prod'"
    echo "Usage: $0 {dev|prod}"
    exit 1
fi

if [ "$ENV_TYPE" = "dev" ]; then
    PROJECT_ID="havital-dev"
else
    PROJECT_ID="paceriz-prod"
fi

REGION="asia-east1"
IMAGE_NAME="admin-backend"

echo "========================================"
echo "🚀 Deploying Admin Backend"
echo "   Environment: $ENV_TYPE"
echo "   Project: $PROJECT_ID"
echo "========================================"
echo ""

# 切換到正確的 GCP 項目
echo "🔄 Switching to GCP project: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# 先構建並推送 Docker image
echo "📦 Building and pushing Docker image..."
./build_backend.sh $ENV_TYPE true

# 從 Secret Manager 載入超級管理員列表
echo ""
echo "🔑 Loading Super Admin emails from Secret Manager..."
SUPER_ADMIN_EMAILS=$(gcloud secrets versions access latest --secret="super-admin-emails" 2>/dev/null || echo "")

if [ -z "$SUPER_ADMIN_EMAILS" ]; then
    echo ""
    echo "========================================"
    echo "❌ Error: SUPER_ADMIN_EMAILS not set"
    echo "========================================"
    echo ""
    echo "Please set up Super Admin emails in Secret Manager:"
    echo ""
    echo "  # Create secret (first time)"
    echo "  echo 'your-email@gmail.com' | gcloud secrets create super-admin-emails --data-file=-"
    echo ""
    echo "  # Update secret (if already exists)"
    echo "  echo 'your-email@gmail.com' | gcloud secrets versions add super-admin-emails --data-file=-"
    echo ""
    echo "  # Multiple admins (comma-separated)"
    echo "  echo 'admin1@gmail.com,admin2@gmail.com' | gcloud secrets versions add super-admin-emails --data-file=-"
    echo ""
    exit 1
fi

echo "✅ Super Admin emails loaded"
echo ""

# 💰 部署到 Cloud Run - 按需計費配置
echo "🚀 Deploying to Cloud Run with cost-optimized settings..."
echo "   💰 Configuration:"
echo "      - min-instances: 0 (閒置時不收費)"
echo "      - max-instances: 3"
echo "      - memory: 512Mi"
echo "      - cpu: 1"
echo "      - timeout: 300s"
echo ""

gcloud run deploy $IMAGE_NAME \
    --image asia.gcr.io/$PROJECT_ID/$IMAGE_NAME:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars "ENV_TYPE=$ENV_TYPE,SUPER_ADMIN_EMAILS=$SUPER_ADMIN_EMAILS" \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 3 \
    --min-instances 0 \
    --concurrency 80 \
    --cpu-throttling \
    --no-cpu-boost \
    --port 8080

echo ""
echo "========================================"
echo "✅ Backend deployed successfully!"
echo ""
echo "💰 成本設置："
echo "   - min-instances: 0 (閒置時不收費)"
echo "   - 預估閒置成本: $0/月"
echo "   - 預估輕度使用: $1-3/月"
echo "========================================"
echo ""

# 獲取服務 URL
SERVICE_URL=$(gcloud run services describe $IMAGE_NAME --platform=managed --region=$REGION --format="value(status.url)")
echo "🌐 Service URL: $SERVICE_URL"
echo ""
echo "測試健康檢查："
echo "  curl $SERVICE_URL/health"
echo ""
