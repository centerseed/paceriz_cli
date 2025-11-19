"""
Admin 配置文件

管理超級管理員白名單和角色定義。
超級管理員列表從環境變量 SUPER_ADMIN_EMAILS 讀取（逗號分隔）。
"""
import os
import logging

logger = logging.getLogger(__name__)

# 超級管理員白名單（從環境變量讀取，用逗號分隔）
SUPER_ADMIN_EMAILS_RAW = os.getenv('SUPER_ADMIN_EMAILS', '')

# 解析並清理 Email 列表
SUPER_ADMIN_EMAILS = [
    email.strip()
    for email in SUPER_ADMIN_EMAILS_RAW.split(',')
    if email.strip()
]

# 日誌記錄配置狀態
if not SUPER_ADMIN_EMAILS:
    logger.warning("⚠️  No super admin emails configured!")
    logger.warning("   Set SUPER_ADMIN_EMAILS environment variable to enable super admin access")
else:
    logger.info(f"✅ Super admin emails configured: {len(SUPER_ADMIN_EMAILS)} admin(s)")
    for email in SUPER_ADMIN_EMAILS:
        logger.info(f"   - {email}")


class AdminRole:
    """管理員角色枚舉"""
    SUPER_ADMIN = 'super_admin'  # 超級管理員（環境變量白名單）
    ADMIN = 'admin'              # 普通管理員（Firestore is_admin: true）


# 導出配置
__all__ = ['SUPER_ADMIN_EMAILS', 'AdminRole']
