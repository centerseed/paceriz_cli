#!/bin/bash
#
# Build Admin Backend Docker Image
#
# Usage:
#   ./build_backend.sh dev         # Build for dev (no push)
#   ./build_backend.sh dev true    # Build for dev and push
#   ./build_backend.sh prod true   # Build for prod and push
#

set -e

ENV_TYPE=${1:-dev}
PUSH_IMAGE=${2:-false}

if [ "$ENV_TYPE" != "dev" ] && [ "$ENV_TYPE" != "prod" ]; then
    echo "❌ Error: ENV_TYPE must be 'dev' or 'prod'"
    echo "Usage: $0 {dev|prod} [true|false]"
    exit 1
fi

if [ "$ENV_TYPE" = "dev" ]; then
    PROJECT_ID="havital-dev"
else
    PROJECT_ID="paceriz-prod"
fi

REGION="asia-east1"
IMAGE_NAME="admin-backend"
TAG=$(date +%Y%m%d-%H%M%S)
FULL_IMAGE_NAME="asia.gcr.io/$PROJECT_ID/$IMAGE_NAME:$TAG"
LATEST_IMAGE_NAME="asia.gcr.io/$PROJECT_ID/$IMAGE_NAME:latest"

echo "========================================"
echo "🐳 Building Admin Backend Docker Image"
echo "========================================"
echo "Environment: $ENV_TYPE"
echo "Project ID: $PROJECT_ID"
echo "Image: $FULL_IMAGE_NAME"
echo "Push: $PUSH_IMAGE"
echo "========================================"
echo ""

# 切換到 backend 目錄
cd "$(dirname "$0")/../backend"

# 配置 Docker 使用 Google Container Registry
echo "🔧 Configuring Docker for GCR..."
gcloud auth configure-docker asia.gcr.io --quiet

# 複製 api_service 到臨時目錄（供 Docker 構建使用）
echo "📦 Copying api_service for Docker build..."
rm -rf ../api_service_temp
cp -r ../../../api_service ../api_service_temp

# Build Docker image
echo "🏗️  Building Docker image..."
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --build-arg ENV_TYPE=$ENV_TYPE \
    --tag $FULL_IMAGE_NAME \
    --tag $LATEST_IMAGE_NAME \
    $([ "$PUSH_IMAGE" = "true" ] && echo "--push" || echo "--load") \
    -f Dockerfile \
    ..

# 清理臨時目錄
echo "🧹 Cleaning up..."
rm -rf ../api_service_temp

echo ""
echo "========================================"
echo "✅ Build complete!"
echo "   Image: $FULL_IMAGE_NAME"
if [ "$PUSH_IMAGE" = "true" ]; then
    echo "   ✅ Pushed to GCR"
else
    echo "   ℹ️  Not pushed (local only)"
fi
echo "========================================"
