"""
Firebase 初始化工具

使用 Application Default Credentials (ADC) 初始化 Firebase Admin SDK
"""
import logging
import firebase_admin
from firebase_admin import credentials

logger = logging.getLogger(__name__)

_initialized = False


def init_firebase():
    """
    初始化 Firebase Admin SDK

    使用 Application Default Credentials (ADC):
    - 從 GOOGLE_APPLICATION_CREDENTIALS 環境變量讀取服務帳號金鑰
    - 或使用 gcloud 配置的默認憑證
    - 或使用 Cloud Run / GCE 的元數據服務器
    """
    global _initialized

    if _initialized:
        logger.debug("Firebase already initialized")
        return

    try:
        # 檢查是否已經初始化
        firebase_admin.get_app()
        logger.info("Firebase app already exists")
        _initialized = True
        return
    except ValueError:
        # App 不存在，需要初始化
        pass

    try:
        # 使用 Application Default Credentials
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred)
        logger.info("✅ Firebase initialized with Application Default Credentials")
        _initialized = True
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        raise
