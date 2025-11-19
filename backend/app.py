"""
Admin Backend API 應用入口

這個文件是 Admin Backend 的主入口，負責：
1. 引用 api_service 的現有代碼（訂閱服務、數據模型等）
2. 註冊 Admin 路由
3. 配置 CORS 和中間件
4. 提供健康檢查端點
"""
import sys
import os
import logging

# ✅ 確保 backend 目錄在 sys.path 中（優先級最高）
BACKEND_PATH = os.path.abspath(os.path.dirname(__file__))
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

# ✅ 添加 api_service 到 Python path，以便引用現有代碼
# 注意：放在 backend 後面，避免與 backend 的 api 目錄衝突
API_SERVICE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../../api_service')
)
if API_SERVICE_PATH not in sys.path:
    sys.path.append(API_SERVICE_PATH)

from flask import Flask, jsonify
from flask_cors import CORS

# ✅ 引用 api_service 的現有代碼
try:
    from domains.subscription.subscription_service import subscription_service
    from data_models.subscription_models import Subscription, SubscriptionStatus
    from core.database.repositories.subscription_repository import subscription_repository
    print("✅ Successfully imported api_service modules")
except ImportError as e:
    print(f"⚠️  Warning: Could not import api_service modules: {e}")
    print("   This is expected if api_service is not yet set up")

# Admin 路由
try:
    from api.admin.subscriptions import admin_subscriptions_bp
    print("✅ Successfully imported admin subscriptions blueprint")
except ImportError as e:
    print(f"⚠️  Warning: Could not import admin subscriptions blueprint: {e}")
    admin_subscriptions_bp = None

try:
    from api.admin.invite_codes import admin_invite_codes_bp
    print("✅ Successfully imported admin invite codes blueprint")
except ImportError as e:
    print(f"⚠️  Warning: Could not import admin invite codes blueprint: {e}")
    admin_invite_codes_bp = None

try:
    from api.admin.analytics import admin_analytics_bp
    print("✅ Successfully imported admin analytics blueprint")
except ImportError as e:
    print(f"⚠️  Warning: Could not import admin analytics blueprint: {e}")
    admin_analytics_bp = None

try:
    from api.admin.admins import admin_admins_bp
    print("✅ Successfully imported admin admins blueprint")
except ImportError as e:
    print(f"⚠️  Warning: Could not import admin admins blueprint: {e}")
    admin_admins_bp = None

try:
    from api.admin.users import admin_users_bp
    print("✅ Successfully imported admin users blueprint")
except ImportError as e:
    print(f"⚠️  Warning: Could not import admin users blueprint: {e}")
    admin_users_bp = None

try:
    from api.admin.subscription_tools import admin_subscription_tools_bp
    print("✅ Successfully imported admin subscription tools blueprint")
except ImportError as e:
    print(f"⚠️  Warning: Could not import admin subscription tools blueprint: {e}")
    admin_subscription_tools_bp = None

try:
    from api.admin.llm_meta import admin_llm_meta_bp
    print("✅ Successfully imported admin LLM meta blueprint")
except ImportError as e:
    print(f"⚠️  Warning: Could not import admin LLM meta blueprint: {e}")
    admin_llm_meta_bp = None

# from api.admin.audit_logs import admin_audit_logs_bp

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 創建 Flask 應用
app = Flask(__name__)

# CORS 配置（只允許 admin.havital.com 和本地開發）
ALLOWED_ORIGINS = os.getenv(
    'ALLOWED_ORIGINS',
    'http://localhost:3000,http://localhost:5173,https://admin.havital.com'
).split(',')
CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=True)

# 註冊 Admin 路由
if admin_subscriptions_bp is not None:
    app.register_blueprint(admin_subscriptions_bp, url_prefix='/api/v1/admin/subscriptions')
    logger.info("✅ Registered subscriptions blueprint at /api/v1/admin/subscriptions")

if admin_invite_codes_bp is not None:
    app.register_blueprint(admin_invite_codes_bp, url_prefix='/api/v1/admin/invite-codes')
    logger.info("✅ Registered invite codes blueprint at /api/v1/admin/invite-codes")

if admin_analytics_bp is not None:
    app.register_blueprint(admin_analytics_bp, url_prefix='/api/v1/admin/analytics')
    logger.info("✅ Registered analytics blueprint at /api/v1/admin/analytics")

if admin_admins_bp is not None:
    app.register_blueprint(admin_admins_bp, url_prefix='/api/v1/admin/admins')
    logger.info("✅ Registered admins blueprint at /api/v1/admin/admins")

if admin_users_bp is not None:
    app.register_blueprint(admin_users_bp, url_prefix='/api/v1/admin/users')
    logger.info("✅ Registered users blueprint at /api/v1/admin/users")

if admin_subscription_tools_bp is not None:
    app.register_blueprint(admin_subscription_tools_bp, url_prefix='/api/v1/admin/subscription-tools')
    logger.info("✅ Registered subscription tools blueprint at /api/v1/admin/subscription-tools")

if admin_llm_meta_bp is not None:
    app.register_blueprint(admin_llm_meta_bp, url_prefix='/api/v1/admin/llm-meta')
    logger.info("✅ Registered LLM meta blueprint at /api/v1/admin/llm-meta")

# app.register_blueprint(admin_audit_logs_bp, url_prefix='/api/v1/admin/audit-logs')

# === 基礎路由 ===

@app.route('/', methods=['GET'])
def root():
    """根路徑"""
    return jsonify({
        'service': 'Havital Admin Backend API',
        'version': '1.0.0',
        'status': 'running',
        'environment': os.getenv('ENV_TYPE', 'dev'),
        'docs': '/api/v1/admin/docs'
    }), 200


@app.route('/health', methods=['GET'])
@app.route('/healthz', methods=['GET'])
def health_check():
    """健康檢查端點（Cloud Run 使用）"""
    return jsonify({
        'status': 'ok',
        'service': 'admin-backend',
        'version': '1.0.0',
        'environment': os.getenv('ENV_TYPE', 'dev')
    }), 200


# === 錯誤處理 ===

@app.errorhandler(404)
def not_found(error):
    """404 錯誤處理"""
    return jsonify({
        'error': 'Not found',
        'message': 'The requested resource does not exist'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """500 錯誤處理"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500


# === 啟動應用 ===

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    debug = os.getenv('ENV_TYPE', 'dev') == 'dev'

    logger.info("=" * 50)
    logger.info(f"🚀 Starting Admin Backend API")
    logger.info(f"   Port: {port}")
    logger.info(f"   Environment: {os.getenv('ENV_TYPE', 'dev')}")
    logger.info(f"   Debug mode: {debug}")
    logger.info(f"   Allowed origins: {ALLOWED_ORIGINS}")
    logger.info("=" * 50)

    app.run(host='0.0.0.0', port=port, debug=debug)
