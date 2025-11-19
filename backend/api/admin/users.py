"""
用戶管理 API

提供管理員查看用戶資訊的 API 端點。

API 端點:
- GET /api/v1/admin/users - 獲取用戶列表
- GET /api/v1/admin/users/{uid} - 獲取用戶詳情
"""
from flask import Blueprint, request, jsonify, g
import logging
import sys
import os
from datetime import datetime

# 添加 api_service 到 Python path
API_SERVICE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../api_service'))
sys.path.insert(0, API_SERVICE_PATH)

try:
    from firebase_admin import firestore
    from core.infrastructure.firebase_init import init_firebase

    # 確保 Firebase 已初始化
    init_firebase()
    db = firestore.client()
except ImportError as e:
    logging.warning(f"Could not import api_service modules: {e}")
    db = None

from middleware.admin_auth import require_admin

logger = logging.getLogger(__name__)

# 創建 Blueprint
admin_users_bp = Blueprint('admin_users', __name__)


@admin_users_bp.route('', methods=['GET'])
@admin_users_bp.route('/', methods=['GET'])
@require_admin
def list_users():
    """
    獲取用戶列表

    Query Parameters:
        - page: 頁碼（默認 1）
        - limit: 每頁數量（默認 50，最大 100）
        - search: 搜尋 UID 或 email

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
    if db is None:
        return jsonify({'error': 'Service not available'}), 503

    try:
        # 獲取查詢參數
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 50)), 100)
        search = request.args.get('search', '').strip()

        # 計算偏移量
        offset = (page - 1) * limit

        # 查詢用戶
        users_ref = db.collection('users')

        # 如果有搜尋條件，先獲取所有用戶再過濾（Firestore 不支援 LIKE 查詢）
        if search:
            all_users = []
            for doc in users_ref.stream():
                user_data = doc.to_dict()
                user_data['uid'] = doc.id

                # 搜尋 UID 或 email
                if (search.lower() in doc.id.lower() or
                    (user_data.get('email', '').lower() and search.lower() in user_data.get('email', '').lower())):
                    all_users.append(user_data)

            # 分頁
            total = len(all_users)
            users = all_users[offset:offset + limit]
        else:
            # 沒有搜尋條件，直接分頁查詢
            docs = users_ref.limit(limit).offset(offset).stream()
            users = []
            for doc in docs:
                user_data = doc.to_dict()
                user_data['uid'] = doc.id
                users.append(user_data)

            # 使用 Firestore 聚合查詢獲取總數（不讀取文檔內容，高效！）
            agg_result = users_ref.count().get()
            total = agg_result[0][0].value

        # 格式化用戶數據
        formatted_users = []
        for user in users:
            formatted_user = {
                'uid': user.get('uid'),
                'email': user.get('email'),
                'display_name': user.get('display_name'),
                'preferred_language': user.get('preferred_language', 'zh-TW'),
                'vdot': user.get('vdot'),
                'is_admin': user.get('is_admin', False),
                'data_source': user.get('data_source'),  # 主要數據來源
                'garmin_connected': bool(user.get('garmin_tokens')),
                'strava_connected': bool(user.get('strava_tokens')),
                'apple_health_connected': bool(user.get('apple_health_last_sync')),
                'created_at': user.get('created_at'),
                'updated_at': user.get('updated_at'),
                'last_login_at': user.get('last_login_at'),
            }
            formatted_users.append(formatted_user)

        # 計算總頁數
        total_pages = (total + limit - 1) // limit

        return jsonify({
            'data': formatted_users,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'total_pages': total_pages
            }
        }), 200

    except Exception as e:
        logger.error(f"Error listing users: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_users_bp.route('/<uid>', methods=['GET'])
@require_admin
def get_user(uid: str):
    """
    獲取用戶詳情

    Args:
        uid: 用戶 UID

    Returns:
        完整的用戶數據
    """
    if db is None:
        return jsonify({'error': 'Service not available'}), 503

    try:
        # 獲取用戶文檔
        user_ref = db.collection('users').document(uid)
        user_doc = user_ref.get()

        if not user_doc.exists:
            return jsonify({'error': 'User not found'}), 404

        user_data = user_doc.to_dict()
        user_data['uid'] = uid

        # 返回完整用戶數據（包含所有欄位）
        return jsonify(user_data), 200

    except Exception as e:
        logger.error(f"Error getting user {uid}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_users_bp.route('/<uid>/training-overview', methods=['GET'])
@require_admin
def get_user_training_overview(uid: str):
    """
    獲取用戶的訓練總覽

    Args:
        uid: 用戶 UID

    Returns:
        訓練總覽數據（從 plan_race_run_overview collection）
    """
    if db is None:
        return jsonify({'error': 'Service not available'}), 503

    try:
        # 先獲取用戶的 active_training_id
        user_ref = db.collection('users').document(uid)
        user_doc = user_ref.get()

        if not user_doc.exists:
            return jsonify({'error': 'User not found'}), 404

        user_data = user_doc.to_dict()
        active_training_id = user_data.get('active_training_id')

        if not active_training_id:
            return jsonify({'training_overview': None, 'message': 'No active training plan'}), 200

        # 查詢 plan_race_run_overview collection
        plan_ref = db.collection('plan_race_run_overview').document(active_training_id)
        plan_doc = plan_ref.get()

        if not plan_doc.exists:
            return jsonify({'training_overview': None, 'message': 'Training plan overview not found'}), 200

        plan_data = plan_doc.to_dict()

        # 返回訓練總覽數據
        return jsonify({
            'training_overview': plan_data.get('overview'),
            'training_id': active_training_id,
            'created_at': plan_data.get('created_at'),
        }), 200

    except Exception as e:
        logger.error(f"Error getting training overview for user {uid}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_users_bp.route('/<uid>/weekly-plan', methods=['GET'])
@require_admin
def get_user_weekly_plan(uid: str):
    """
    獲取用戶的週課表

    Args:
        uid: 用戶 UID

    Returns:
        週課表數據
    """
    if db is None:
        return jsonify({'error': 'Service not available'}), 503

    try:
        # 獲取用戶的 active_weekly_plan_id
        user_data = db.collection('users').document(uid).get().to_dict()

        if not user_data:
            return jsonify({'error': 'User not found'}), 404

        active_weekly_plan_id = user_data.get('active_weekly_plan_id')

        if not active_weekly_plan_id:
            return jsonify({
                'weekly_plan': None,
                'weekly_plan_id': None,
            }), 200

        # 從 plan_race_run_weekly collection 獲取週課表
        weekly_ref = db.collection('plan_race_run_weekly').document(active_weekly_plan_id)
        weekly_doc = weekly_ref.get()

        if not weekly_doc.exists:
            return jsonify({
                'weekly_plan': None,
                'weekly_plan_id': active_weekly_plan_id,
            }), 200

        weekly_data = weekly_doc.to_dict()

        return jsonify({
            'weekly_plan': weekly_data,
            'weekly_plan_id': active_weekly_plan_id,
            'created_at': weekly_data.get('created_at'),
        }), 200

    except Exception as e:
        logger.error(f"Error getting weekly plan for user {uid}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_users_bp.route('/<uid>/weekly-summary', methods=['GET'])
@require_admin
def get_user_weekly_summary(uid: str):
    """
    獲取用戶的週回顧（上週）

    週回顧 ID 計算規則：
    - 從 active_weekly_plan_id 提取：{prefix}_{week_number}
    - 週回顧 ID：{prefix}_{week_number-1}_summary
    - 例如：003bcz2NC4aLX0PgJARs_11 -> 003bcz2NC4aLX0PgJARs_10_summary

    Args:
        uid: 用戶 UID

    Returns:
        JSON: {
            'weekly_summary': 週回顧數據 or None,
            'summary_id': 週回顧文檔 ID or None,
        }
    """
    try:
        # 獲取用戶數據
        user_ref = db.collection('users').document(uid)
        user_doc = user_ref.get()

        if not user_doc.exists:
            return jsonify({'error': 'User not found'}), 404

        user_data = user_doc.to_dict()
        active_weekly_plan_id = user_data.get('active_weekly_plan_id')

        if not active_weekly_plan_id:
            return jsonify({
                'weekly_summary': None,
                'summary_id': None,
            }), 200

        # 解析週課表 ID，計算上週的週回顧 ID
        # 格式：{prefix}_{week_number}
        # 例如：003bcz2NC4aLX0PgJARs_11
        try:
            parts = active_weekly_plan_id.rsplit('_', 1)
            if len(parts) != 2:
                logger.warning(f"Invalid weekly_plan_id format: {active_weekly_plan_id}")
                return jsonify({
                    'weekly_summary': None,
                    'summary_id': None,
                }), 200

            prefix = parts[0]  # 003bcz2NC4aLX0PgJARs
            current_week = int(parts[1])  # 11

            # 上週的週數
            last_week = current_week - 1

            if last_week < 1:
                # 第一週沒有上週回顧
                return jsonify({
                    'weekly_summary': None,
                    'summary_id': None,
                }), 200

            # 構建週回顧 ID
            summary_id = f"{prefix}_{last_week}_summary"

        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to parse weekly_plan_id {active_weekly_plan_id}: {e}")
            return jsonify({
                'weekly_summary': None,
                'summary_id': None,
            }), 200

        # 從 weekly_summary collection 獲取週回顧
        summary_ref = db.collection('weekly_summary').document(summary_id)
        summary_doc = summary_ref.get()

        if not summary_doc.exists:
            return jsonify({
                'weekly_summary': None,
                'summary_id': summary_id,
            }), 200

        summary_data = summary_doc.to_dict()

        return jsonify({
            'weekly_summary': summary_data,
            'summary_id': summary_id,
            'week_number': last_week,
            'created_at': summary_data.get('created_at'),
        }), 200

    except Exception as e:
        logger.error(f"Error getting weekly summary for user {uid}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
