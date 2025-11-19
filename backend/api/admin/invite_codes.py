"""
邀請碼管理 API

提供管理員操作邀請碼的 API 端點。

API 端點:
- GET /api/v1/admin/invite-codes - 獲取邀請碼列表
- GET /api/v1/admin/invite-codes/{code} - 獲取邀請碼詳情
- GET /api/v1/admin/invite-codes/{code}/usages - 獲取邀請碼使用記錄
- POST /api/v1/admin/invite-codes/{code}/disable - 禁用邀請碼
- GET /api/v1/admin/invite-codes/stats - 獲取邀請碼統計
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
    from data_models.subscription_models import InviteCode, InviteCodeUsage
    from firebase_admin import firestore
    from core.infrastructure.firebase_init import init_firebase

    # 確保 Firebase 已初始化
    init_firebase()
    db = firestore.client()
except ImportError as e:
    logging.warning(f"Could not import api_service modules: {e}")
    subscription_service = None
    InviteCode = None
    InviteCodeUsage = None
    db = None

from middleware.admin_auth import require_admin, get_admin_info
from services.audit_log_service import audit_log_service

logger = logging.getLogger(__name__)

# 創建 Blueprint
admin_invite_codes_bp = Blueprint('admin_invite_codes', __name__)


@admin_invite_codes_bp.route('', methods=['GET'])
@admin_invite_codes_bp.route('/', methods=['GET'])
@require_admin
def list_invite_codes():
    """
    獲取邀請碼列表

    Query Parameters:
        - page: 頁碼（默認 1）
        - limit: 每頁數量（默認 50，最大 100）
        - status: 篩選狀態 (active, inactive, all)
        - owner_uid: 按擁有者 UID 篩選

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
        owner_uid = request.args.get('owner_uid')

        # 計算偏移量
        offset = (page - 1) * limit

        # 查詢邀請碼
        query = db.collection('invite_codes').order_by('created_at', direction=firestore.Query.DESCENDING)

        # 應用篩選
        if status_filter == 'active':
            query = query.where('is_active', '==', True)
        elif status_filter == 'inactive':
            query = query.where('is_active', '==', False)

        if owner_uid:
            query = query.where('owner_uid', '==', owner_uid)

        # 使用聚合查詢獲取總數（高效，不讀取文檔內容）
        agg_result = query.count().get()
        total = agg_result[0][0].value

        # 分頁查詢
        docs = list(query.limit(limit).offset(offset).stream())

        # 格式化數據
        invite_codes = []
        for doc in docs:
            try:
                code_data = doc.to_dict()
                code_data['code'] = doc.id  # 確保包含 code 字段

                # 轉換為 Pydantic 模型進行驗證
                invite_code = InviteCode.from_dict(code_data)

                # 獲取使用次數（從數據庫）
                invite_codes.append({
                    'code': invite_code.code,
                    'owner_uid': invite_code.owner_uid,
                    'usage_count': invite_code.usage_count,
                    'max_usage': invite_code.max_usage,
                    'reward_days': invite_code.reward_days,
                    'is_active': invite_code.is_active,
                    'created_at': invite_code.created_at.isoformat() if invite_code.created_at else None,
                    'updated_at': invite_code.updated_at.isoformat() if invite_code.updated_at else None,
                })
            except Exception as e:
                logger.warning(f"Failed to parse invite code {doc.id}: {e}")
                continue

        # 計算分頁信息
        total_pages = (total + limit - 1) // limit

        return jsonify({
            'data': invite_codes,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'total_pages': total_pages
            }
        }), 200

    except Exception as e:
        logger.error(f"Error listing invite codes: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_invite_codes_bp.route('/<code>', methods=['GET'])
@require_admin
def get_invite_code(code: str):
    """
    獲取邀請碼詳情

    Args:
        code: 邀請碼

    Returns:
        {
            "invite_code": {...},
            "owner": {...},
            "statistics": {
                "total_usages": 5,
                "rewarded_usages": 3,
                "pending_rewards": 2
            }
        }
    """
    if subscription_service is None or db is None:
        return jsonify({'error': 'Service not available'}), 503

    try:
        # 獲取邀請碼
        invite_code = subscription_service.repo.get_invite_code(code.upper())
        if not invite_code:
            return jsonify({'error': 'Invite code not found'}), 404

        # 獲取擁有者信息
        owner_sub = subscription_service.repo.get_subscription(invite_code.owner_uid)
        owner_info = {
            'uid': invite_code.owner_uid,
            'has_subscription': owner_sub is not None,
            'is_premium': owner_sub.is_premium if owner_sub else False
        }

        # 獲取使用記錄並統計
        usages = subscription_service.repo.get_invite_code_usages_by_inviter(invite_code.owner_uid)

        # 過濾出當前邀請碼的使用記錄
        code_usages = [u for u in usages if u.code == code.upper()]

        total_usages = len(code_usages)
        rewarded_usages = sum(1 for u in code_usages if u.reward_granted)
        pending_rewards = total_usages - rewarded_usages

        return jsonify({
            'invite_code': {
                'code': invite_code.code,
                'owner_uid': invite_code.owner_uid,
                'usage_count': invite_code.usage_count,
                'max_usage': invite_code.max_usage,
                'reward_days': invite_code.reward_days,
                'refund_period_days': invite_code.refund_period_days,
                'is_active': invite_code.is_active,
                'created_at': invite_code.created_at.isoformat() if invite_code.created_at else None,
                'updated_at': invite_code.updated_at.isoformat() if invite_code.updated_at else None,
            },
            'owner': owner_info,
            'statistics': {
                'total_usages': total_usages,
                'rewarded_usages': rewarded_usages,
                'pending_rewards': pending_rewards
            }
        }), 200

    except Exception as e:
        logger.error(f"Error getting invite code {code}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_invite_codes_bp.route('/<code>/usages', methods=['GET'])
@require_admin
def get_invite_code_usages(code: str):
    """
    獲取邀請碼使用記錄

    Args:
        code: 邀請碼

    Returns:
        {
            "data": [
                {
                    "invitee_uid": "...",
                    "used_at": "...",
                    "reward_granted": true,
                    "reward_granted_at": "..."
                }
            ]
        }
    """
    if subscription_service is None or db is None:
        return jsonify({'error': 'Service not available'}), 503

    try:
        # 獲取邀請碼（驗證存在）
        invite_code = subscription_service.repo.get_invite_code(code.upper())
        if not invite_code:
            return jsonify({'error': 'Invite code not found'}), 404

        # 查詢使用記錄
        query = db.collection('invite_code_usages').where('code', '==', code.upper()).order_by('used_at', direction=firestore.Query.DESCENDING)
        docs = query.stream()

        usages = []
        for doc in docs:
            try:
                usage_data = doc.to_dict()
                usage = InviteCodeUsage.from_dict(usage_data)

                usages.append({
                    'invitee_uid': usage.invitee_uid,
                    'inviter_uid': usage.inviter_uid,
                    'used_at': usage.used_at.isoformat() if usage.used_at else None,
                    'reward_granted': usage.reward_granted,
                    'reward_granted_at': usage.reward_granted_at.isoformat() if usage.reward_granted_at else None,
                    'reward_days': usage.reward_days,
                    'inviter_past_refund_period': usage.inviter_past_refund_period,
                    'invitee_past_refund_period': usage.invitee_past_refund_period
                })
            except Exception as e:
                logger.warning(f"Failed to parse invite code usage {doc.id}: {e}")
                continue

        return jsonify({
            'data': usages,
            'total': len(usages)
        }), 200

    except Exception as e:
        logger.error(f"Error getting invite code usages for {code}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_invite_codes_bp.route('/<code>/disable', methods=['POST'])
@require_admin
def disable_invite_code(code: str):
    """
    禁用邀請碼

    Args:
        code: 邀請碼

    Returns:
        {
            "success": true,
            "message": "Invite code disabled"
        }
    """
    if subscription_service is None or db is None:
        return jsonify({'error': 'Service not available'}), 503

    try:
        # 獲取邀請碼（驗證存在）
        invite_code = subscription_service.repo.get_invite_code(code.upper())
        if not invite_code:
            return jsonify({'error': 'Invite code not found'}), 404

        if not invite_code.is_active:
            return jsonify({'error': 'Invite code is already inactive'}), 400

        # 禁用邀請碼
        subscription_service.repo.update_invite_code(code.upper(), {
            'is_active': False
        })

        # 記錄審計日誌
        admin_info = get_admin_info()
        audit_log_service.log_action(
            action='disable_invite_code',
            admin_uid=admin_info['uid'],
            admin_email=admin_info['email'],
            resource_type='invite_code',
            resource_id=code.upper(),
            details={
                'code': code.upper(),
                'owner_uid': invite_code.owner_uid
            },
            ip_address=request.remote_addr
        )

        logger.info(f"Invite code {code.upper()} disabled by admin {admin_info['email']}")

        return jsonify({
            'success': True,
            'message': 'Invite code disabled successfully'
        }), 200

    except Exception as e:
        logger.error(f"Error disabling invite code {code}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_invite_codes_bp.route('/stats', methods=['GET'])
@require_admin
def get_invite_code_stats():
    """
    獲取邀請碼統計信息

    Returns:
        {
            "total_codes": 100,
            "active_codes": 85,
            "inactive_codes": 15,
            "total_usages": 350,
            "rewarded_usages": 280,
            "pending_rewards": 70,
            "conversion_rate": 0.85
        }
    """
    if subscription_service is None or db is None:
        return jsonify({'error': 'Service not available'}), 503

    try:
        # 使用聚合查詢統計邀請碼（高效，不讀取文檔內容）
        codes_ref = db.collection('invite_codes')
        total_codes = codes_ref.count().get()[0][0].value
        active_codes = codes_ref.where('is_active', '==', True).count().get()[0][0].value
        inactive_codes = total_codes - active_codes

        # 使用聚合查詢統計使用記錄
        usages_ref = db.collection('invite_code_usages')
        total_usages = usages_ref.count().get()[0][0].value
        rewarded_usages = usages_ref.where('reward_granted', '==', True).count().get()[0][0].value
        pending_rewards = total_usages - rewarded_usages

        # 計算轉換率（已發放獎勵 / 總使用次數）
        conversion_rate = (rewarded_usages / total_usages) if total_usages > 0 else 0.0

        return jsonify({
            'total_codes': total_codes,
            'active_codes': active_codes,
            'inactive_codes': inactive_codes,
            'total_usages': total_usages,
            'rewarded_usages': rewarded_usages,
            'pending_rewards': pending_rewards,
            'conversion_rate': round(conversion_rate, 3)
        }), 200

    except Exception as e:
        logger.error(f"Error getting invite code stats: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
