"""
審計日誌服務

記錄所有管理員操作到 Firestore admin_audit_logs collection。

Firestore 結構:
    admin_audit_logs/{log_id}:
        - timestamp: datetime (UTC)
        - admin_uid: str
        - admin_email: str
        - admin_role: str (super_admin | admin)
        - action_type: str (extend_subscription, cancel_subscription, etc.)
        - target_uid: str (被操作的用戶 UID)
        - target_email: str (optional)
        - details: dict (操作詳情)
        - ip_address: str
        - user_agent: str
        - success: bool
        - error_message: str (optional)
"""
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import logging
import sys
import os

# 添加 api_service 到 Python path
API_SERVICE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../api_service'))
sys.path.insert(0, API_SERVICE_PATH)

try:
    from firebase_admin import firestore
    from core.infrastructure.firebase_init import init_firebase

    # 確保 Firebase 已初始化
    init_firebase()
    db = firestore.client()
except ImportError as e:
    logging.warning(f"Could not import Firebase modules: {e}")
    db = None

logger = logging.getLogger(__name__)


class AuditLogService:
    """審計日誌服務"""

    COLLECTION_NAME = 'admin_audit_logs'

    @staticmethod
    def log_action(
        admin_uid: str,
        admin_email: str,
        admin_role: str,
        action_type: str,
        target_uid: Optional[str] = None,
        target_email: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> Optional[str]:
        """
        記錄管理員操作

        Args:
            admin_uid: 管理員 UID
            admin_email: 管理員 Email
            admin_role: 管理員角色 (super_admin | admin)
            action_type: 操作類型 (extend_subscription, cancel_subscription, etc.)
            target_uid: 被操作的用戶 UID
            target_email: 被操作的用戶 Email (optional)
            details: 操作詳情 (dict)
            ip_address: 管理員 IP 地址
            user_agent: User Agent
            success: 操作是否成功
            error_message: 錯誤消息 (如果失敗)

        Returns:
            str: Log ID，失敗時返回 None
        """
        if db is None:
            logger.error("Firebase not initialized, cannot log action")
            return None

        try:
            log_entry = {
                'timestamp': datetime.now(timezone.utc),
                'admin_uid': admin_uid,
                'admin_email': admin_email,
                'admin_role': admin_role,
                'action_type': action_type,
                'success': success,
            }

            # 添加可選字段
            if target_uid:
                log_entry['target_uid'] = target_uid
            if target_email:
                log_entry['target_email'] = target_email
            if details:
                log_entry['details'] = details
            if ip_address:
                log_entry['ip_address'] = ip_address
            if user_agent:
                log_entry['user_agent'] = user_agent
            if error_message:
                log_entry['error_message'] = error_message

            # 寫入 Firestore
            doc_ref = db.collection(AuditLogService.COLLECTION_NAME).add(log_entry)
            log_id = doc_ref[1].id

            logger.info(
                f"✅ Audit log created: {action_type} by {admin_email} "
                f"(target: {target_uid or 'N/A'}) [log_id: {log_id}]"
            )

            return log_id

        except Exception as e:
            logger.error(f"Failed to create audit log: {e}", exc_info=True)
            return None

    @staticmethod
    def get_logs(
        admin_uid: Optional[str] = None,
        action_type: Optional[str] = None,
        target_uid: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> list:
        """
        查詢審計日誌

        Args:
            admin_uid: 篩選特定管理員的操作
            action_type: 篩選特定操作類型
            target_uid: 篩選特定目標用戶
            limit: 返回數量限制
            offset: 偏移量（分頁）

        Returns:
            list: 審計日誌列表
        """
        if db is None:
            logger.error("Firebase not initialized")
            return []

        try:
            query = db.collection(AuditLogService.COLLECTION_NAME)

            # 應用篩選條件
            if admin_uid:
                query = query.where('admin_uid', '==', admin_uid)
            if action_type:
                query = query.where('action_type', '==', action_type)
            if target_uid:
                query = query.where('target_uid', '==', target_uid)

            # 排序和分頁
            query = query.order_by('timestamp', direction='DESCENDING')
            query = query.limit(limit).offset(offset)

            # 執行查詢
            docs = query.stream()

            logs = []
            for doc in docs:
                log_data = doc.to_dict()
                log_data['log_id'] = doc.id
                logs.append(log_data)

            logger.info(f"Retrieved {len(logs)} audit logs")
            return logs

        except Exception as e:
            logger.error(f"Failed to retrieve audit logs: {e}", exc_info=True)
            return []

    @staticmethod
    def get_log_by_id(log_id: str) -> Optional[Dict[str, Any]]:
        """
        根據 ID 獲取單個審計日誌

        Args:
            log_id: 日誌 ID

        Returns:
            dict: 日誌數據，不存在時返回 None
        """
        if db is None:
            logger.error("Firebase not initialized")
            return None

        try:
            doc = db.collection(AuditLogService.COLLECTION_NAME).document(log_id).get()

            if not doc.exists:
                logger.warning(f"Audit log not found: {log_id}")
                return None

            log_data = doc.to_dict()
            log_data['log_id'] = doc.id
            return log_data

        except Exception as e:
            logger.error(f"Failed to retrieve audit log {log_id}: {e}", exc_info=True)
            return None


# 創建全局實例
audit_log_service = AuditLogService()
