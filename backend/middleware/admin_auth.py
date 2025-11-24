"""
Admin 認證中間件

提供 @require_admin 和 @require_super_admin 裝飾器用於保護 Admin API。

認證流程：
1. 從 Authorization header 獲取 Firebase Token
2. 驗證 Token 並獲取用戶信息
3. 檢查是否為超級管理員（環境變量白名單）
4. 如果不是超級管理員，檢查 Firestore 中的 is_admin
5. 設置 g.admin_uid, g.admin_email, g.is_super_admin 等全局變量
"""
from functools import wraps
from flask import request, jsonify, g
import logging
import sys
import os

try:
    from firebase_admin import auth, firestore
    from utils.firebase_init import init_firebase

    # 確保 Firebase 已初始化
    init_firebase()
    db = firestore.client()
except Exception as e:
    logging.warning(f"Could not initialize Firebase: {e}")
    auth = None
    db = None

from config.admin_config import SUPER_ADMIN_EMAILS, AdminRole

logger = logging.getLogger(__name__)


def require_admin(f):
    """
    要求管理員權限（普通管理員或超級管理員）

    使用方式:
        @admin_bp.route('/subscriptions')
        @require_admin
        def list_subscriptions():
            # 可以通過 g.admin_uid, g.admin_email, g.is_super_admin 獲取管理員信息
            pass

    Returns:
        - 200: 認證成功，執行被裝飾的函數
        - 401: Token 缺失或無效
        - 403: 沒有管理員權限
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 檢查 Firebase 是否已初始化
        if auth is None or db is None:
            logger.error("Firebase not initialized")
            return jsonify({'error': 'Server configuration error'}), 500

        # 1. 獲取 Authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            logger.warning("Missing or invalid Authorization header")
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Missing or invalid Authorization header'
            }), 401

        token = auth_header.replace('Bearer ', '')

        # 2. 驗證 Firebase Token
        try:
            decoded_token = auth.verify_id_token(token)
            uid = decoded_token['uid']
            email = decoded_token.get('email')

            if not email:
                logger.warning(f"Token missing email for uid: {uid}")
                return jsonify({
                    'error': 'Unauthorized',
                    'message': 'Email not found in token'
                }), 401

        except auth.ExpiredIdTokenError:
            logger.warning("Token expired")
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Token expired'
            }), 401
        except auth.InvalidIdTokenError:
            logger.warning("Invalid token")
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Invalid token'
            }), 401
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Token verification failed'
            }), 401

        # 3. 檢查是否為超級管理員（環境變量白名單）
        if email in SUPER_ADMIN_EMAILS:
            logger.info(f"✅ Super admin authenticated: {email}")
            g.admin_uid = uid
            g.admin_email = email
            g.admin_role = AdminRole.SUPER_ADMIN
            g.is_super_admin = True
            return f(*args, **kwargs)

        # 4. 檢查是否為系統 Admin（Firestore）
        try:
            user_doc = db.collection('users').document(uid).get()
            if user_doc.exists and user_doc.get('is_admin'):
                logger.info(f"✅ Admin authenticated: {email}")
                g.admin_uid = uid
                g.admin_email = email
                g.admin_role = AdminRole.ADMIN
                g.is_super_admin = False
                return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error checking admin status for uid {uid}: {e}")
            return jsonify({
                'error': 'Server error',
                'message': 'Error checking permissions'
            }), 500

        # 5. 沒有權限
        logger.warning(f"❌ Unauthorized access attempt by: {email}")
        return jsonify({
            'error': 'Forbidden',
            'message': 'Admin access required'
        }), 403

    return decorated_function


def require_super_admin(f):
    """
    要求超級管理員權限

    使用方式:
        @admin_bp.route('/admins/add')
        @require_super_admin
        def add_admin():
            pass

    Returns:
        - 200: 認證成功，執行被裝飾的函數
        - 401: Token 缺失或無效
        - 403: 沒有超級管理員權限
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 檢查 Firebase 是否已初始化
        if auth is None:
            logger.error("Firebase not initialized")
            return jsonify({'error': 'Server configuration error'}), 500

        # 獲取 Authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            logger.warning("Missing or invalid Authorization header")
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Missing or invalid Authorization header'
            }), 401

        token = auth_header.replace('Bearer ', '')

        # 驗證 Firebase Token
        try:
            decoded_token = auth.verify_id_token(token)
            uid = decoded_token['uid']
            email = decoded_token.get('email')

            if not email:
                return jsonify({
                    'error': 'Unauthorized',
                    'message': 'Email not found in token'
                }), 401

        except Exception as e:
            logger.warning(f"Token verification failed: {e}")
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Token verification failed'
            }), 401

        # 檢查是否為超級管理員
        if email not in SUPER_ADMIN_EMAILS:
            logger.warning(f"❌ Unauthorized super admin access attempt by: {email}")
            return jsonify({
                'error': 'Forbidden',
                'message': 'Super admin access required'
            }), 403

        logger.info(f"✅ Super admin authenticated: {email}")
        g.admin_uid = uid
        g.admin_email = email
        g.admin_role = AdminRole.SUPER_ADMIN
        g.is_super_admin = True

        return f(*args, **kwargs)

    return decorated_function


def get_admin_info():
    """
    獲取當前登入的管理員信息（僅在 @require_admin 或 @require_super_admin 之後調用）

    Returns:
        dict: {
            'uid': str,
            'email': str,
            'role': str,
            'is_super_admin': bool
        }
    """
    return {
        'uid': g.get('admin_uid'),
        'email': g.get('admin_email'),
        'role': g.get('admin_role'),
        'is_super_admin': g.get('is_super_admin', False)
    }
