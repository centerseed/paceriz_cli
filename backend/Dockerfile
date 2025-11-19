# ======================================
# Admin Backend Dockerfile
# ======================================
#
# 多階段構建：
# 1. Base stage: 安裝系統依賴
# 2. Dependencies stage: 安裝 Python 依賴
# 3. Final stage: 複製代碼和運行應用
#

# === Base Stage ===
FROM python:3.11-slim AS base

# 設置環境變量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# === Dependencies Stage ===
FROM base AS deps

# 複製 api_service 的 requirements.txt（backend 使用相同依賴）
COPY ../api_service/requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# === Final Stage ===
FROM deps AS final

# 設置環境變量
ARG ENV_TYPE=dev
ENV ENV_TYPE=$ENV_TYPE

# 複製 Backend 代碼
COPY . .

# 複製 api_service 代碼（供引用）
# 注意：需要在構建時將 api_service 目錄複製進來
COPY ../api_service /api_service

# 暴露端口
EXPOSE 8080

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 啟動命令
CMD gunicorn \
    --bind 0.0.0.0:${PORT:-8080} \
    --workers 2 \
    --threads 4 \
    --worker-class gthread \
    --worker-tmp-dir /dev/shm \
    --timeout 300 \
    --log-level info \
    --access-logfile - \
    --error-logfile - \
    app:app
