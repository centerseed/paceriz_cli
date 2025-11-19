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

try:
    from firebase_admin import firestore
    from utils.firebase_init import init_firebase

    # 確保 Firebase 已初始化
    init_firebase()
    db = firestore.client()
except Exception as e:
    logging.warning(f"Could not initialize Firebase: {e}")
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

        # 如果有搜尋條件，使用優化的查詢策略
        if search:
            all_users = []

            # 優化策略1: 如果搜尋內容像是完整 UID (長度 > 20)，直接查詢該文檔
            if len(search) > 20:
                try:
                    doc = users_ref.document(search).get()
                    if doc.exists:
                        user_data = doc.to_dict()
                        user_data['uid'] = doc.id
                        all_users.append(user_data)
                except Exception as e:
                    logger.debug(f"Direct UID lookup failed: {e}")

            # 優化策略2: 如果搜尋內容包含 @，可能是 email，使用精確查詢
            if '@' in search and not all_users:
                try:
                    # 嘗試精確匹配 email
                    email_docs = users_ref.where('email', '==', search.lower()).limit(10).stream()
                    for doc in email_docs:
                        user_data = doc.to_dict()
                        user_data['uid'] = doc.id
                        all_users.append(user_data)
                except Exception as e:
                    logger.debug(f"Email lookup failed: {e}")

            # 優化策略3: 如果上述都沒找到，進行部分匹配 (限制最大讀取數量)
            if not all_users:
                # ⚠️ 警告: 部分匹配需要讀取多個文檔
                # 為了避免讀取所有用戶，我們限制最大讀取數量為500
                MAX_SEARCH_DOCS = 500
                logger.warning(f"Performing partial match search (limited to {MAX_SEARCH_DOCS} docs)")

                count = 0
                for doc in users_ref.limit(MAX_SEARCH_DOCS).stream():
                    user_data = doc.to_dict()
                    user_data['uid'] = doc.id
                    count += 1

                    # 搜尋 UID 或 email (部分匹配)
                    if (search.lower() in doc.id.lower() or
                        (user_data.get('email', '').lower() and search.lower() in user_data.get('email', '').lower())):
                        all_users.append(user_data)

                if count >= MAX_SEARCH_DOCS:
                    logger.warning(f"Search reached max document limit ({MAX_SEARCH_DOCS}). Results may be incomplete.")

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


@admin_users_bp.route('/<uid>/readiness', methods=['GET'])
@require_admin
def get_user_readiness(uid: str):
    """
    獲取用戶最新的訓練準備度

    Args:
        uid: 用戶 UID

    Query Parameters:
        date: 可選，指定日期 (YYYY-MM-DD)，默認為今天

    Returns:
        訓練準備度數據，如果沒有數據則返回 null
    """
    logger.info(f"========== GET READINESS REQUEST for uid={uid} ==========")

    if db is None:
        logger.error("Database not initialized")
        return jsonify({'error': 'Service not available'}), 503

    try:
        from datetime import timedelta

        # 獲取日期參數，默認為今天
        date_str = request.args.get('date')
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                logger.error(f"Invalid date format: {date_str}")
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        else:
            target_date = datetime.now()

        logger.info(f"Target date: {target_date.strftime('%Y-%m-%d')}")

        # 查詢 users/{uid}/training_readiness/{date} subcollection
        date_doc_id = target_date.strftime('%Y-%m-%d')
        logger.info(f"Querying document: users/{uid}/training_readiness/{date_doc_id}")

        readiness_ref = db.collection('users').document(uid).collection('training_readiness').document(date_doc_id)
        readiness_doc = readiness_ref.get()
        logger.info(f"Document exists: {readiness_doc.exists}")

        if readiness_doc.exists:
            readiness_data = readiness_doc.to_dict()
            readiness_data['doc_id'] = date_doc_id
            logger.info(f"Found readiness data for {uid} on {date_doc_id}")

            # 注入 trend_data 從 readiness_metrics/{uid}/rolling_trends/current
            try:
                rolling_trends_ref = db.collection('readiness_metrics').document(uid).collection('rolling_trends').document('current')
                rolling_trends_doc = rolling_trends_ref.get()

                if rolling_trends_doc.exists:
                    rolling_trends = rolling_trends_doc.to_dict()
                    logger.info(f"Found rolling_trends for {uid}")

                    # 只取最近 21 天的數據
                    trend_data_dict = {}
                    for metric_name in ['speed', 'endurance', 'race_fitness', 'training_load', 'recovery']:
                        if metric_name in rolling_trends:
                            metric_trend = rolling_trends[metric_name]
                            dates = metric_trend.get('dates', [])
                            values = metric_trend.get('values', [])
                            direction = metric_trend.get('direction', 'stable')

                            # 只取最後 21 天
                            if len(dates) > 21:
                                dates = dates[-21:]
                                values = values[-21:]

                            trend_data_dict[metric_name] = {
                                'dates': dates,
                                'values': values,
                                'direction': direction
                            }

                    # 為每個指標注入 trend_data
                    for metric_name in ['speed', 'endurance', 'race_fitness', 'training_load', 'recovery']:
                        if metric_name in readiness_data and metric_name in trend_data_dict:
                            # 如果 readiness_data[metric_name] 還沒有 trend_data，注入它
                            if isinstance(readiness_data[metric_name], dict):
                                if 'trend_data' not in readiness_data[metric_name] or readiness_data[metric_name]['trend_data'] is None:
                                    readiness_data[metric_name]['trend_data'] = trend_data_dict[metric_name]
                                    logger.info(f"Injected trend_data for {metric_name}")
                else:
                    logger.warning(f"No rolling_trends found for {uid}")
            except Exception as e:
                logger.error(f"Error reading rolling_trends for {uid}: {e}")

            return jsonify({
                'readiness': readiness_data,
                'found_for_date': True
            }), 200

        # 如果當天沒有數據，簡單地列出最近的文檔
        logger.info(f"No data for {date_doc_id}, fetching recent documents")
        recent_docs = list(db.collection('users')
                          .document(uid)
                          .collection('training_readiness')
                          .limit(10)
                          .stream())

        if recent_docs:
            # 按文檔 ID (日期) 排序，取最新的
            recent_docs.sort(key=lambda x: x.id, reverse=True)
            latest_doc = recent_docs[0]
            readiness_data = latest_doc.to_dict()
            readiness_data['doc_id'] = latest_doc.id
            logger.info(f"Returning data from {latest_doc.id}")

            # 注入 trend_data 從 readiness_metrics/{uid}/rolling_trends/current
            try:
                rolling_trends_ref = db.collection('readiness_metrics').document(uid).collection('rolling_trends').document('current')
                rolling_trends_doc = rolling_trends_ref.get()

                if rolling_trends_doc.exists:
                    rolling_trends = rolling_trends_doc.to_dict()
                    logger.info(f"Found rolling_trends for {uid} (fallback)")

                    # 只取最近 21 天的數據
                    trend_data_dict = {}
                    for metric_name in ['speed', 'endurance', 'race_fitness', 'training_load', 'recovery']:
                        if metric_name in rolling_trends:
                            metric_trend = rolling_trends[metric_name]
                            dates = metric_trend.get('dates', [])
                            values = metric_trend.get('values', [])
                            direction = metric_trend.get('direction', 'stable')

                            # 只取最後 21 天
                            if len(dates) > 21:
                                dates = dates[-21:]
                                values = values[-21:]

                            trend_data_dict[metric_name] = {
                                'dates': dates,
                                'values': values,
                                'direction': direction
                            }

                    # 為每個指標注入 trend_data
                    for metric_name in ['speed', 'endurance', 'race_fitness', 'training_load', 'recovery']:
                        if metric_name in readiness_data and metric_name in trend_data_dict:
                            if isinstance(readiness_data[metric_name], dict):
                                if 'trend_data' not in readiness_data[metric_name] or readiness_data[metric_name]['trend_data'] is None:
                                    readiness_data[metric_name]['trend_data'] = trend_data_dict[metric_name]
                                    logger.info(f"Injected trend_data for {metric_name} (fallback)")
                else:
                    logger.warning(f"No rolling_trends found for {uid} (fallback)")
            except Exception as e:
                logger.error(f"Error reading rolling_trends for {uid} (fallback): {e}")

            return jsonify({
                'readiness': readiness_data,
                'found_for_date': False,
                'message': f'Returned data from {latest_doc.id}'
            }), 200

        logger.warning(f"No readiness data found for user {uid}")
        return jsonify({
            'readiness': None,
            'found_for_date': False,
            'message': 'No readiness data found'
        }), 200

    except Exception as e:
        logger.error(f"Error getting readiness for user {uid}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_users_bp.route('/<uid>/readiness/history', methods=['GET'])
@require_admin
def get_user_readiness_history(uid: str):
    """
    獲取用戶訓練準備度歷史記錄

    Args:
        uid: 用戶 UID

    Query Parameters:
        days: 查詢天數，默認 28 天，最大 90 天

    Returns:
        訓練準備度歷史數據列表
    """
    if db is None:
        logger.error("Database not initialized")
        return jsonify({'error': 'Service not available'}), 503

    try:
        # 獲取查詢天數
        days = min(int(request.args.get('days', 28)), 90)
        logger.info(f"Fetching readiness history for user {uid}, days={days}")

        # 簡單地列出所有文檔，避免 where 查詢需要索引的問題
        all_docs = list(db.collection('users')
                       .document(uid)
                       .collection('training_readiness')
                       .stream())

        logger.info(f"Found {len(all_docs)} total readiness documents for user {uid}")

        # 按文檔 ID (日期) 排序，取最近的
        all_docs.sort(key=lambda x: x.id, reverse=True)

        history_data = []
        for doc in all_docs[:days]:
            data = doc.to_dict()
            data['doc_id'] = doc.id
            history_data.append(data)

        return jsonify({
            'history': history_data,
            'days': days,
            'count': len(history_data)
        }), 200

    except Exception as e:
        logger.error(f"Error getting readiness history for user {uid}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e), 'details': 'Check server logs'}), 500
