#!/bin/bash
#
# Build Admin Frontend Docker Image
#
# Usage:
#   ./build_frontend.sh dev         # Build for dev (no push)
#   ./build_frontend.sh dev true    # Build for dev and push
#   ./build_frontend.sh prod true   # Build for prod and push
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
IMAGE_NAME="admin-frontend"
TAG=$(date +%Y%m%d-%H%M%S)
FULL_IMAGE_NAME="asia.gcr.io/$PROJECT_ID/$IMAGE_NAME:$TAG"
LATEST_IMAGE_NAME="asia.gcr.io/$PROJECT_ID/$IMAGE_NAME:latest"

echo "========================================"
echo "🐳 Building Admin Frontend Docker Image"
echo "========================================"
echo "Environment: $ENV_TYPE"
echo "Project ID: $PROJECT_ID"
echo "Image: $FULL_IMAGE_NAME"
echo "Push: $PUSH_IMAGE"
echo "========================================"
echo ""

# 切換到 frontend 目錄
cd "$(dirname "$0")/../frontend"

# 配置 Docker 使用 Google Container Registry
echo "🔧 Configuring Docker for GCR..."
gcloud auth configure-docker asia.gcr.io --quiet

# Build Docker image (multi-stage: npm build + nginx)
echo "🏗️  Building Docker image..."
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --build-arg REACT_APP_ENV=$ENV_TYPE \
    --tag $FULL_IMAGE_NAME \
    --tag $LATEST_IMAGE_NAME \
    $([ "$PUSH_IMAGE" = "true" ] && echo "--push" || echo "--load") \
    .

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
