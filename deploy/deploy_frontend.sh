#!/bin/bash
#
# Deploy Admin Frontend to Cloud Run
#
# Usage:
#   ./deploy_frontend.sh dev   # Deploy to dev environment
#   ./deploy_frontend.sh prod  # Deploy to prod environment
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
    # TODO: 替換為實際的 Backend URL
    API_URL="https://admin-backend-xxx-uc.a.run.app"
else
    PROJECT_ID="paceriz-prod"
    API_URL="https://admin-api.havital.com"
fi

REGION="asia-east1"
IMAGE_NAME="admin-frontend"

echo "========================================"
echo "🚀 Deploying Admin Frontend"
echo "   Environment: $ENV_TYPE"
echo "   Project: $PROJECT_ID"
echo "   API URL: $API_URL"
echo "========================================"
echo ""

# 切換到正確的 GCP 項目
echo "🔄 Switching to GCP project: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# 先構建並推送 Docker image
echo "📦 Building and pushing Docker image..."
./build_frontend.sh $ENV_TYPE true

echo ""
echo "🚀 Deploying to Cloud Run with cost-optimized settings..."
echo "   💰 Configuration:"
echo "      - min-instances: 0 (閒置時不收費)"
echo "      - max-instances: 3"
echo "      - memory: 256Mi"
echo "      - cpu: 1"
echo "      - timeout: 60s"
echo ""

# 💰 部署到 Cloud Run - 按需計費配置
gcloud run deploy $IMAGE_NAME \
    --image asia.gcr.io/$PROJECT_ID/$IMAGE_NAME:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars "REACT_APP_API_URL=$API_URL" \
    --memory 256Mi \
    --cpu 1 \
    --timeout 60 \
    --max-instances 3 \
    --min-instances 0 \
    --concurrency 80 \
    --cpu-throttling \
    --no-cpu-boost \
    --port 8080

echo ""
echo "========================================"
echo "✅ Frontend deployed successfully!"
echo ""
echo "💰 成本設置："
echo "   - min-instances: 0 (閒置時不收費)"
echo "   - 預估閒置成本: $0/月"
echo "   - 預估輕度使用: $0.5-1/月"
echo "========================================"
echo ""

# 獲取服務 URL
SERVICE_URL=$(gcloud run services describe $IMAGE_NAME --platform=managed --region=$REGION --format="value(status.url)")
echo "🌐 Service URL: $SERVICE_URL"
echo ""
echo "ℹ️  Note: Update API_URL in this script with the actual Backend URL"
echo ""
