"""
管理員管理 API

提供管理員列表、授予權限、撤銷權限等功能。
只有 Super Admin 可以訪問這些 endpoints。
"""
from flask import Blueprint, jsonify, request, g
from middleware.admin_auth import require_super_admin
from datetime import datetime, timezone
import logging
import sys
import os

try:
    from firebase_admin import firestore
    from utils.firebase_init import init_firebase

    # 確保 Firebase 已初始化
    init_firebase()
    db = firestore.client()
except Exception as e:
    logging.warning(f"Could not initialize Firebase: {e}")
    db = None

from services.audit_log_service import audit_log_service
from config.admin_config import SUPER_ADMIN_EMAILS

logger = logging.getLogger(__name__)

admin_admins_bp = Blueprint('admin_admins', __name__)


@admin_admins_bp.route('', methods=['GET'])
@require_super_admin
def list_admins():
    """
    列出所有管理員

    Query Parameters:
        - page: int (default=1) - 頁碼
        - limit: int (default=20, max=100) - 每頁數量
        - role: str (optional) - 篩選角色 (super_admin, admin)

    Returns:
        {
            "data": [
                {
                    "uid": str,
                    "email": str,
                    "role": str,  # "super_admin" or "admin"
                    "is_super_admin": bool,
                    "display_name": str,
                    "created_at": str,
                    "last_login": str
                }
            ],
            "pagination": {
                "total": int,
                "page": int,
                "limit": int,
                "total_pages": int
            }
        }
    """
    try:
        # 獲取查詢參數
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 20)), 100)
        role_filter = request.args.get('role')  # 'super_admin', 'admin', or None

        admins_list = []

        # 1. 添加所有 Super Admins（從環境變數）
        if not role_filter or role_filter == 'super_admin':
            for email in SUPER_ADMIN_EMAILS:
                try:
                    # 嘗試從 Firebase Auth 獲取用戶信息
                    from firebase_admin import auth
                    user = auth.get_user_by_email(email)

                    admin_data = {
                        'uid': user.uid,
                        'email': email,
                        'role': 'super_admin',
                        'is_super_admin': True,
                        'display_name': user.display_name or email.split('@')[0],
                        'created_at': datetime.fromtimestamp(user.user_metadata.creation_timestamp / 1000, tz=timezone.utc).isoformat() if user.user_metadata.creation_timestamp else None,
                        'last_login': datetime.fromtimestamp(user.user_metadata.last_sign_in_timestamp / 1000, tz=timezone.utc).isoformat() if user.user_metadata.last_sign_in_timestamp else None,
                    }
                    admins_list.append(admin_data)
                except Exception as e:
                    logger.warning(f"Could not get user info for super admin {email}: {e}")
                    # 即使無法獲取詳細信息，也添加基本信息
                    admins_list.append({
                        'uid': None,
                        'email': email,
                        'role': 'super_admin',
                        'is_super_admin': True,
                        'display_name': email.split('@')[0],
                        'created_at': None,
                        'last_login': None,
                    })

        # 2. 從 Firestore 獲取所有 is_admin = true 的用戶
        if not role_filter or role_filter == 'admin':
            query = db.collection('users').where('is_admin', '==', True).stream()

            for doc in query:
                user_data = doc.to_dict()
                email = user_data.get('email')

                # 跳過 Super Admin（他們已經在上面添加過了）
                if email in SUPER_ADMIN_EMAILS:
                    continue

                admin_data = {
                    'uid': doc.id,
                    'email': email,
                    'role': 'admin',
                    'is_super_admin': False,
                    'display_name': user_data.get('display_name', email.split('@')[0] if email else 'Unknown'),
                    'created_at': user_data.get('created_at').isoformat() if user_data.get('created_at') else None,
                    'last_login': user_data.get('last_login').isoformat() if user_data.get('last_login') else None,
                }
                admins_list.append(admin_data)

        # 3. 排序（Super Admin 優先，然後按 email 排序）
        admins_list.sort(key=lambda x: (not x['is_super_admin'], x['email']))

        # 4. 分頁
        total = len(admins_list)
        total_pages = (total + limit - 1) // limit
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_admins = admins_list[start_idx:end_idx]

        logger.info(f"Super admin {g.admin_email} listed {total} admins (page={page}, limit={limit})")

        return jsonify({
            'data': paginated_admins,
            'pagination': {
                'total': total,
                'page': page,
                'limit': limit,
                'total_pages': total_pages
            }
        }), 200

    except Exception as e:
        logger.error(f"Error listing admins: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@admin_admins_bp.route('/<uid>/grant', methods=['POST'])
@require_super_admin
def grant_admin(uid: str):
    """
    授予用戶管理員權限

    只有 Super Admin 可以執行此操作。
    將用戶的 is_admin 欄位設置為 true。

    Path Parameters:
        - uid: str - 用戶 UID

    Request Body:
        {
            "reason": str (optional) - 授予權限的原因
        }

    Returns:
        {
            "message": str,
            "admin": {
                "uid": str,
                "email": str,
                "is_admin": bool
            }
        }
    """
    try:
        data = request.get_json() or {}
        reason = data.get('reason', 'No reason provided')

        # 1. 檢查用戶是否存在
        user_ref = db.collection('users').document(uid)
        user_doc = user_ref.get()

        if not user_doc.exists:
            return jsonify({'error': 'User not found'}), 404

        user_data = user_doc.to_dict()
        email = user_data.get('email')

        # 2. 檢查是否已經是 Super Admin
        if email in SUPER_ADMIN_EMAILS:
            return jsonify({
                'error': 'User is already a super admin',
                'message': 'Super admins are configured via environment variables'
            }), 400

        # 3. 檢查是否已經是 Admin
        if user_data.get('is_admin'):
            return jsonify({
                'error': 'User is already an admin',
                'admin': {
                    'uid': uid,
                    'email': email,
                    'is_admin': True
                }
            }), 400

        # 4. 授予管理員權限
        user_ref.update({
            'is_admin': True,
            'admin_granted_at': datetime.now(timezone.utc),
            'admin_granted_by': g.admin_uid,
            'updated_at': datetime.now(timezone.utc)
        })

        # 5. 記錄審計日誌
        audit_log_service.log_action(
            action='grant_admin',
            admin_uid=g.admin_uid,
            admin_email=g.admin_email,
            target_uid=uid,
            details={
                'target_email': email,
                'reason': reason
            }
        )

        logger.info(f"Super admin {g.admin_email} granted admin permission to {email} (uid={uid})")

        return jsonify({
            'message': f'Admin permission granted to {email}',
            'admin': {
                'uid': uid,
                'email': email,
                'is_admin': True
            }
        }), 200

    except Exception as e:
        logger.error(f"Error granting admin permission to uid {uid}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@admin_admins_bp.route('/<uid>/revoke', methods=['POST'])
@require_super_admin
def revoke_admin(uid: str):
    """
    撤銷用戶的管理員權限

    只有 Super Admin 可以執行此操作。
    將用戶的 is_admin 欄位設置為 false。

    注意：不能撤銷 Super Admin 的權限（Super Admin 通過環境變數配置）。

    Path Parameters:
        - uid: str - 用戶 UID

    Request Body:
        {
            "reason": str (optional) - 撤銷權限的原因
        }

    Returns:
        {
            "message": str,
            "admin": {
                "uid": str,
                "email": str,
                "is_admin": bool
            }
        }
    """
    try:
        data = request.get_json() or {}
        reason = data.get('reason', 'No reason provided')

        # 1. 檢查用戶是否存在
        user_ref = db.collection('users').document(uid)
        user_doc = user_ref.get()

        if not user_doc.exists:
            return jsonify({'error': 'User not found'}), 404

        user_data = user_doc.to_dict()
        email = user_data.get('email')

        # 2. 檢查是否為 Super Admin
        if email in SUPER_ADMIN_EMAILS:
            return jsonify({
                'error': 'Cannot revoke super admin permission',
                'message': 'Super admins are configured via environment variables and cannot be modified'
            }), 400

        # 3. 檢查是否為 Admin
        if not user_data.get('is_admin'):
            return jsonify({
                'error': 'User is not an admin',
                'admin': {
                    'uid': uid,
                    'email': email,
                    'is_admin': False
                }
            }), 400

        # 4. 撤銷管理員權限
        user_ref.update({
            'is_admin': False,
            'admin_revoked_at': datetime.now(timezone.utc),
            'admin_revoked_by': g.admin_uid,
            'updated_at': datetime.now(timezone.utc)
        })

        # 5. 記錄審計日誌
        audit_log_service.log_action(
            action='revoke_admin',
            admin_uid=g.admin_uid,
            admin_email=g.admin_email,
            target_uid=uid,
            details={
                'target_email': email,
                'reason': reason
            }
        )

        logger.info(f"Super admin {g.admin_email} revoked admin permission from {email} (uid={uid})")

        return jsonify({
            'message': f'Admin permission revoked from {email}',
            'admin': {
                'uid': uid,
                'email': email,
                'is_admin': False
            }
        }), 200

    except Exception as e:
        logger.error(f"Error revoking admin permission from uid {uid}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@admin_admins_bp.route('/audit-logs', methods=['GET'])
@require_super_admin
def get_audit_logs():
    """
    獲取審計日誌

    Query Parameters:
        - limit: int (default=100, max=500) - 返回的日誌數量
        - action: str (optional) - 篩選特定操作類型

    Returns:
        {
            "data": [
                {
                    "id": str,
                    "action": str,
                    "admin_uid": str,
                    "admin_email": str,
                    "target_uid": str,
                    "details": dict,
                    "created_at": str
                }
            ],
            "total": int
        }
    """
    try:
        limit = min(int(request.args.get('limit', 100)), 500)
        action_filter = request.args.get('action')

        # 查詢審計日誌
        query = db.collection('audit_logs').order_by('created_at', direction=firestore.Query.DESCENDING).limit(limit)

        if action_filter:
            query = query.where('action', '==', action_filter)

        logs = []
        for doc in query.stream():
            log_data = doc.to_dict()
            logs.append({
                'id': doc.id,
                'action': log_data.get('action'),
                'admin_uid': log_data.get('admin_uid'),
                'admin_email': log_data.get('admin_email'),
                'target_uid': log_data.get('target_uid'),
                'details': log_data.get('details', {}),
                'created_at': log_data.get('created_at').isoformat() if log_data.get('created_at') else None,
            })

        logger.info(f"Super admin {g.admin_email} retrieved {len(logs)} audit logs")

        return jsonify({
            'data': logs,
            'total': len(logs)
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving audit logs: {e}")
        return jsonify({'error': 'Internal server error'}), 500
