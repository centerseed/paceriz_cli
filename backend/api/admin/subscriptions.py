"""
訂閱管理 API

提供管理員操作訂閱的 API 端點。

API 端點:
- GET /api/v1/admin/subscriptions - 獲取訂閱列表
- GET /api/v1/admin/subscriptions/{uid} - 獲取訂閱詳情
- POST /api/v1/admin/subscriptions/{uid}/extend - 延長訂閱
- POST /api/v1/admin/subscriptions/{uid}/cancel - 取消訂閱
"""
from flask import Blueprint, request, jsonify, g
import logging
import sys
import os

# 添加 api_service 到 Python path
API_SERVICE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../api_service'))
sys.path.insert(0, API_SERVICE_PATH)

try:
    from domains.subscription.subscription_service import subscription_service
    from data_models.subscription_models import ExtensionReason
    from firebase_admin import firestore
    from core.infrastructure.firebase_init import init_firebase

    # 確保 Firebase 已初始化
    init_firebase()
    db = firestore.client()
except ImportError as e:
    logging.warning(f"Could not import api_service modules: {e}")
    subscription_service = None
    ExtensionReason = None
    db = None

from middleware.admin_auth import require_admin, get_admin_info
from services.audit_log_service import audit_log_service

logger = logging.getLogger(__name__)

# 創建 Blueprint
admin_subscriptions_bp = Blueprint('admin_subscriptions', __name__)


@admin_subscriptions_bp.route('', methods=['GET'])
@admin_subscriptions_bp.route('/', methods=['GET'])
@require_admin
def list_subscriptions():
    """
    獲取訂閱列表

    Query Parameters:
        - page: 頁碼（默認 1）
        - limit: 每頁數量（默認 50，最大 100）
        - status: 篩選狀態 (in_trial, premium_active, expired, all)

    Returns:
        {
            "data": [...],
            "pagination": {
                "page": 1,
                "limit": 50,
                "total": 100,
                "total_pages": 2
            }
        }
    """
    if subscription_service is None or db is None:
        return jsonify({'error': 'Service not available'}), 503

    try:
        # 獲取查詢參數
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 50)), 100)
        status_filter = request.args.get('status', 'all')

        # 計算偏移量
        offset = (page - 1) * limit

        # 查詢訂閱
        query = db.collection('subscriptions')

        # 應用狀態篩選
        if status_filter == 'in_trial':
            # 試用中的用戶
            query = query.where('trial_start_at', '!=', None)
        elif status_filter == 'premium_active':
            # 付費中的用戶
            query = query.where('is_premium', '==', True)

        # 使用聚合查詢獲取總數（高效，不讀取文檔內容）
        agg_result = query.count().get()
        total = agg_result[0][0].value

        # 分頁查詢
        docs = list(query.limit(limit).offset(offset).stream())

        # 批量獲取用戶信息（減少查詢次數）
        uids = [doc.id for doc in docs]
        users_map = {}

        if uids:
            # Firestore 批量查詢最多支持 30 個，分批處理
            for i in range(0, len(uids), 30):
                batch_uids = uids[i:i+30]
                users_docs = db.collection('users').where('__name__', 'in', batch_uids).stream()
                for user_doc in users_docs:
                    users_map[user_doc.id] = user_doc.to_dict()

        # 格式化數據
        subscriptions = []
        for doc in docs:
            data = doc.to_dict()
            data['uid'] = doc.id

            # 從批量查詢結果獲取用戶信息
            if doc.id in users_map:
                user_data = users_map[doc.id]
                data['email'] = user_data.get('email')
                data['display_name'] = user_data.get('display_name')

            subscriptions.append(data)

        # 計算總頁數
        total_pages = (total + limit - 1) // limit

        admin_info = get_admin_info()
        logger.info(f"Admin {admin_info['email']} listed subscriptions (page={page}, limit={limit})")

        return jsonify({
            'data': subscriptions,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'total_pages': total_pages
            }
        }), 200

    except ValueError as e:
        return jsonify({'error': 'Invalid parameters', 'message': str(e)}), 400
    except Exception as e:
        logger.error(f"Error listing subscriptions: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@admin_subscriptions_bp.route('/<uid>', methods=['GET'])
@require_admin
def get_subscription(uid: str):
    """
    獲取訂閱詳情

    Args:
        uid: 用戶 UID

    Returns:
        {
            "user": {...},
            "subscription": {...},
            "invite_code": {...}
        }
    """
    if subscription_service is None or db is None:
        return jsonify({'error': 'Service not available'}), 503

    try:
        # 獲取訂閱信息
        subscription = subscription_service.get_subscription_summary(uid)

        if not subscription:
            return jsonify({'error': 'Subscription not found'}), 404

        # 獲取用戶信息
        user_doc = db.collection('users').document(uid).get()
        user_data = user_doc.to_dict() if user_doc.exists else {}

        # 獲取邀請碼信息
        invite_code_doc = db.collection('invite_codes').where('owner_uid', '==', uid).limit(1).stream()
        invite_code = None
        for doc in invite_code_doc:
            invite_code = doc.to_dict()
            invite_code['code'] = doc.id
            break

        admin_info = get_admin_info()
        logger.info(f"Admin {admin_info['email']} viewed subscription for {uid}")

        return jsonify({
            'user': {
                'uid': uid,
                'email': user_data.get('email'),
                'display_name': user_data.get('display_name'),
                'created_at': user_data.get('created_at')
            },
            'subscription': subscription,
            'invite_code': invite_code
        }), 200

    except Exception as e:
        logger.error(f"Error getting subscription for {uid}: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@admin_subscriptions_bp.route('/<uid>/extend', methods=['POST'])
@require_admin
def extend_subscription(uid: str):
    """
    延長訂閱

    Request Body:
        {
            "days": int,
            "reason": str (admin_grant, compensation, promotion, other),
            "notes": str (optional)
        }

    Returns:
        {
            "success": true,
            "new_end_at": "2026-01-30T23:59:59Z",
            "total_extension_days": 60
        }
    """
    if subscription_service is None:
        return jsonify({'error': 'Service not available'}), 503

    try:
        # 解析請求
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400

        days = data.get('days')
        reason_str = data.get('reason', 'admin_grant')
        notes = data.get('notes', '')

        # 驗證參數
        if not days or not isinstance(days, int) or days <= 0:
            return jsonify({'error': 'Invalid days parameter'}), 400

        if days > 365:
            return jsonify({'error': 'Cannot extend more than 365 days at once'}), 400

        # 轉換 reason 字符串為 ExtensionReason 枚舉
        try:
            reason = ExtensionReason(reason_str)
        except ValueError:
            return jsonify({'error': f'Invalid reason: {reason_str}'}), 400

        # 獲取管理員信息
        admin_info = get_admin_info()
        admin_uid = admin_info['uid']
        admin_email = admin_info['email']

        # 獲取用戶信息
        user_doc = db.collection('users').document(uid).get()
        target_email = user_doc.get('email') if user_doc.exists else None

        # 執行延長
        result = subscription_service.extend_subscription(
            uid=uid,
            days=days,
            reason=reason,
            granted_by=admin_uid,
            notes=notes
        )

        # 記錄審計日誌
        audit_log_service.log_action(
            admin_uid=admin_uid,
            admin_email=admin_email,
            admin_role=admin_info['role'],
            action_type='extend_subscription',
            target_uid=uid,
            target_email=target_email,
            details={
                'days': days,
                'reason': reason,
                'notes': notes,
                'new_end_at': result.get('new_end_at'),
                'total_extension_days': result.get('total_extension_days')
            },
            ip_address=request.headers.get('X-Forwarded-For', request.remote_addr),
            user_agent=request.headers.get('User-Agent'),
            success=True
        )

        logger.info(f"✅ Admin {admin_email} extended subscription for {uid} by {days} days")

        return jsonify(result), 200

    except ValueError as e:
        # 記錄失敗的審計日誌
        admin_info = get_admin_info()
        audit_log_service.log_action(
            admin_uid=admin_info['uid'],
            admin_email=admin_info['email'],
            admin_role=admin_info['role'],
            action_type='extend_subscription',
            target_uid=uid,
            details=data,
            ip_address=request.headers.get('X-Forwarded-For', request.remote_addr),
            user_agent=request.headers.get('User-Agent'),
            success=False,
            error_message=str(e)
        )
        return jsonify({'error': 'Invalid request', 'message': str(e)}), 400
    except Exception as e:
        logger.error(f"Error extending subscription for {uid}: {e}", exc_info=True)
        # 記錄失敗的審計日誌
        admin_info = get_admin_info()
        audit_log_service.log_action(
            admin_uid=admin_info['uid'],
            admin_email=admin_info['email'],
            admin_role=admin_info['role'],
            action_type='extend_subscription',
            target_uid=uid,
            details=data,
            ip_address=request.headers.get('X-Forwarded-For', request.remote_addr),
            user_agent=request.headers.get('User-Agent'),
            success=False,
            error_message=str(e)
        )
        return jsonify({'error': 'Internal server error'}), 500


@admin_subscriptions_bp.route('/<uid>/cancel', methods=['POST'])
@require_admin
def cancel_subscription(uid: str):
    """
    取消訂閱

    Request Body:
        {
            "reason": str,
            "notes": str (optional)
        }

    Returns:
        {
            "success": true,
            "cancelled_at": "2025-11-03T14:30:00Z"
        }
    """
    if subscription_service is None or db is None:
        return jsonify({'error': 'Service not available'}), 503

    try:
        # 解析請求
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid request body'}), 400

        reason = data.get('reason', 'admin_cancel')
        notes = data.get('notes', '')

        # 獲取管理員信息
        admin_info = get_admin_info()
        admin_uid = admin_info['uid']
        admin_email = admin_info['email']

        # 獲取用戶信息
        user_doc = db.collection('users').document(uid).get()
        target_email = user_doc.get('email') if user_doc.exists else None

        # 執行取消（這裡簡化實現，實際應該調用 subscription_service 的方法）
        from datetime import datetime, timezone
        cancelled_at = datetime.now(timezone.utc)

        # 更新 Firestore（簡化版本）
        db.collection('subscriptions').document(uid).update({
            'is_premium': False,
            'cancelled_at': cancelled_at,
            'cancel_reason': reason,
            'cancelled_by': admin_uid,
            'updated_at': cancelled_at
        })

        # 記錄審計日誌
        audit_log_service.log_action(
            admin_uid=admin_uid,
            admin_email=admin_email,
            admin_role=admin_info['role'],
            action_type='cancel_subscription',
            target_uid=uid,
            target_email=target_email,
            details={
                'reason': reason,
                'notes': notes,
                'cancelled_at': cancelled_at.isoformat()
            },
            ip_address=request.headers.get('X-Forwarded-For', request.remote_addr),
            user_agent=request.headers.get('User-Agent'),
            success=True
        )

        logger.info(f"✅ Admin {admin_email} cancelled subscription for {uid}")

        return jsonify({
            'success': True,
            'cancelled_at': cancelled_at.isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error cancelling subscription for {uid}: {e}", exc_info=True)
        # 記錄失敗的審計日誌
        admin_info = get_admin_info()
        audit_log_service.log_action(
            admin_uid=admin_info['uid'],
            admin_email=admin_info['email'],
            admin_role=admin_info['role'],
            action_type='cancel_subscription',
            target_uid=uid,
            details=data if 'data' in locals() else {},
            ip_address=request.headers.get('X-Forwarded-For', request.remote_addr),
            user_agent=request.headers.get('User-Agent'),
            success=False,
            error_message=str(e)
        )
        return jsonify({'error': 'Internal server error'}), 500
