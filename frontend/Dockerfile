# ======================================
# Admin Frontend Dockerfile
# ======================================
#
# 多階段構建：
# 1. Build stage: 構建 React 應用
# 2. Production stage: 使用 Nginx 提供靜態文件
#

# === Build Stage ===
FROM node:18-alpine AS build

WORKDIR /app

# 複製 package files
COPY package*.json ./

# 安裝依賴
RUN npm ci

# 複製源代碼
COPY . .

# 構建應用
ARG REACT_APP_ENV=dev
ENV REACT_APP_ENV=$REACT_APP_ENV

RUN npm run build

# === Production Stage ===
FROM nginx:alpine

# 複製構建結果
COPY --from=build /app/dist /usr/share/nginx/html

# 複製 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 8080

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# 啟動 Nginx
CMD ["nginx", "-g", "daemon off;"]
