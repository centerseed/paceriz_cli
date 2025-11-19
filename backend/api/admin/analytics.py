"""
數據分析 API

提供管理員查看統計數據和分析報告的 API 端點。

API 端點:
- GET /api/v1/admin/analytics/overview - 獲取總覽統計
- GET /api/v1/admin/analytics/revenue - 獲取收入統計
- GET /api/v1/admin/analytics/retention - 獲取留存分析
- GET /api/v1/admin/analytics/trends - 獲取趨勢數據
"""
from flask import Blueprint, request, jsonify, g
import logging
import sys
import os
from datetime import datetime, timezone, timedelta
from collections import defaultdict

# 添加 api_service 到 Python path
API_SERVICE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../api_service'))
sys.path.insert(0, API_SERVICE_PATH)

try:
    from domains.subscription.subscription_service import subscription_service
    from data_models.subscription_models import SubscriptionStatus, PaymentPlatform
    from firebase_admin import firestore
    from core.infrastructure.firebase_init import init_firebase

    # 確保 Firebase 已初始化
    init_firebase()
    db = firestore.client()
except ImportError as e:
    logging.warning(f"Could not import api_service modules: {e}")
    subscription_service = None
    SubscriptionStatus = None
    PaymentPlatform = None
    db = None

from middleware.admin_auth import require_admin, get_admin_info
from services.audit_log_service import audit_log_service

logger = logging.getLogger(__name__)

# 創建 Blueprint
admin_analytics_bp = Blueprint('admin_analytics', __name__)

# ========== 緩存機制 ==========
# 簡單的內存緩存，用於減少頻繁的 Firestore 全量查詢
# 緩存 TTL: 5 分鐘（管理後台數據不需要實時性）
_subscriptions_cache = {
    'data': None,
    'timestamp': None,
    'ttl': 300  # 5 minutes
}

def get_all_subscriptions_cached():
    """獲取所有訂閱（帶緩存）"""
    now = datetime.now(timezone.utc)
    cache = _subscriptions_cache

    # 檢查緩存是否有效
    if (cache['data'] is not None and
        cache['timestamp'] is not None and
        (now - cache['timestamp']).total_seconds() < cache['ttl']):
        logger.info(f"Using cached subscriptions (age: {(now - cache['timestamp']).total_seconds():.1f}s)")
        return cache['data']

    # 緩存失效，重新查詢
    logger.info("Fetching all subscriptions from Firestore (cache miss)")
    all_subscriptions = list(db.collection('subscriptions').stream())

    # 更新緩存
    cache['data'] = all_subscriptions
    cache['timestamp'] = now

    return all_subscriptions


@admin_analytics_bp.route('/overview', methods=['GET'])
@require_admin
def get_overview():
    """
    獲取總覽統計

    Returns:
        {
            "total_users": 1000,
            "trial_users": 300,
            "premium_users": 150,
            "active_premium_users": 120,
            "today_new_users": 5,
            "this_week_new_users": 35,
            "this_month_new_users": 150,
            "trial_conversion_rate": 0.5,
            "churn_rate": 0.05
        }
    """
    if subscription_service is None or db is None:
        return jsonify({'error': 'Service not available'}), 503

    try:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=now.weekday())
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # 獲取所有訂閱（使用緩存）
        all_subscriptions = get_all_subscriptions_cached()

        total_users = len(all_subscriptions)
        trial_users = 0
        premium_users = 0
        active_premium_users = 0
        today_new = 0
        week_new = 0
        month_new = 0

        converted_users = 0  # 從試用轉為付費的用戶數
        total_churned = 0    # 已流失的用戶數

        for doc in all_subscriptions:
            try:
                data = doc.to_dict()

                # 統計試用和付費用戶
                trial_start = data.get('trial_start_at')
                trial_end = data.get('trial_end_at')
                is_premium = data.get('is_premium', False)
                premium_end = data.get('premium_end_at')

                # 試用中（未過期且非付費）
                if trial_start and trial_end and not is_premium:
                    if isinstance(trial_end, datetime):
                        if trial_end > now:
                            trial_users += 1

                # 付費用戶（曾經付費）
                if is_premium:
                    premium_users += 1
                    converted_users += 1

                    # 活躍付費用戶（付費未過期）
                    if premium_end:
                        if isinstance(premium_end, datetime) and premium_end > now:
                            active_premium_users += 1
                        elif isinstance(premium_end, datetime) and premium_end < now:
                            total_churned += 1

                # 統計新增用戶
                created_at = data.get('created_at')
                if created_at:
                    if isinstance(created_at, datetime):
                        if created_at >= today_start:
                            today_new += 1
                        if created_at >= week_start:
                            week_new += 1
                        if created_at >= month_start:
                            month_new += 1

            except Exception as e:
                logger.warning(f"Failed to process subscription {doc.id}: {e}")
                continue

        # 計算轉換率（從試用轉為付費的比率）
        trial_conversion_rate = (converted_users / max(total_users, 1))

        # 計算流失率（已過期付費用戶 / 總付費用戶）
        churn_rate = (total_churned / max(premium_users, 1))

        return jsonify({
            'total_users': total_users,
            'trial_users': trial_users,
            'premium_users': premium_users,
            'active_premium_users': active_premium_users,
            'today_new_users': today_new,
            'this_week_new_users': week_new,
            'this_month_new_users': month_new,
            'trial_conversion_rate': round(trial_conversion_rate, 3),
            'churn_rate': round(churn_rate, 3)
        }), 200

    except Exception as e:
        logger.error(f"Error getting overview statistics: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_analytics_bp.route('/revenue', methods=['GET'])
@require_admin
def get_revenue():
    """
    獲取收入統計

    Returns:
        {
            "current_month_revenue": 15000,
            "last_month_revenue": 14000,
            "annual_recurring_revenue": 180000,
            "average_revenue_per_user": 150,
            "by_platform": {
                "stripe": 10000,
                "apple_iap": 3000,
                "google_play": 2000
            }
        }
    """
    if subscription_service is None or db is None:
        return jsonify({'error': 'Service not available'}), 503

    try:
        now = datetime.now(timezone.utc)
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # 計算上個月的開始和結束
        last_month_end = current_month_start - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # 獲取所有付費訂閱
        premium_subscriptions = list(
            db.collection('subscriptions')
            .where('is_premium', '==', True)
            .stream()
        )

        # 假設月費價格（實際應該從訂閱數據中獲取）
        MONTHLY_PRICE = 150  # TWD 150/月（示例價格）

        current_month_revenue = 0
        last_month_revenue = 0
        by_platform = defaultdict(int)
        active_subscriptions = 0

        for doc in premium_subscriptions:
            try:
                data = doc.to_dict()
                premium_start = data.get('premium_start_at')
                premium_end = data.get('premium_end_at')
                payment_platform = data.get('payment_platform')

                if not premium_start or not premium_end:
                    continue

                # 檢查是否在當前月有活躍訂閱
                if isinstance(premium_start, datetime) and isinstance(premium_end, datetime):
                    # 訂閱在當前月內活躍
                    if premium_start <= now and premium_end >= current_month_start:
                        current_month_revenue += MONTHLY_PRICE
                        active_subscriptions += 1

                        # 按平台統計
                        if payment_platform:
                            by_platform[payment_platform] += MONTHLY_PRICE

                    # 訂閱在上個月活躍
                    if premium_start <= last_month_end and premium_end >= last_month_start:
                        last_month_revenue += MONTHLY_PRICE

            except Exception as e:
                logger.warning(f"Failed to process subscription {doc.id}: {e}")
                continue

        # 計算年度經常性收入（ARR）= 活躍訂閱數 * 月費 * 12
        arr = active_subscriptions * MONTHLY_PRICE * 12

        # 計算每用戶平均收入（ARPU）
        arpu = (current_month_revenue / max(active_subscriptions, 1))

        return jsonify({
            'current_month_revenue': current_month_revenue,
            'last_month_revenue': last_month_revenue,
            'annual_recurring_revenue': arr,
            'average_revenue_per_user': round(arpu, 2),
            'active_subscriptions': active_subscriptions,
            'by_platform': dict(by_platform)
        }), 200

    except Exception as e:
        logger.error(f"Error getting revenue statistics: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_analytics_bp.route('/retention', methods=['GET'])
@require_admin
def get_retention():
    """
    獲取留存分析

    Returns:
        {
            "day_7_retention": 0.75,
            "day_30_retention": 0.60,
            "month_1_retention": 0.55,
            "month_3_retention": 0.45
        }
    """
    if subscription_service is None or db is None:
        return jsonify({'error': 'Service not available'}), 503

    try:
        now = datetime.now(timezone.utc)
        day_7_ago = now - timedelta(days=7)
        day_30_ago = now - timedelta(days=30)
        month_3_ago = now - timedelta(days=90)

        # 獲取所有訂閱（使用緩存）
        all_subscriptions = get_all_subscriptions_cached()

        # 統計各時間段的留存
        users_7_days_ago = 0
        retained_7_days = 0

        users_30_days_ago = 0
        retained_30_days = 0

        users_90_days_ago = 0
        retained_90_days = 0

        for doc in all_subscriptions:
            try:
                data = doc.to_dict()
                created_at = data.get('created_at')
                premium_end = data.get('premium_end_at')
                trial_end = data.get('trial_end_at')

                if not created_at or not isinstance(created_at, datetime):
                    continue

                # 檢查用戶是否還活躍（付費未過期或試用未過期）
                is_active = False
                if premium_end and isinstance(premium_end, datetime) and premium_end > now:
                    is_active = True
                elif trial_end and isinstance(trial_end, datetime) and trial_end > now:
                    is_active = True

                # 7 天留存
                if created_at <= day_7_ago:
                    users_7_days_ago += 1
                    if is_active:
                        retained_7_days += 1

                # 30 天留存
                if created_at <= day_30_ago:
                    users_30_days_ago += 1
                    if is_active:
                        retained_30_days += 1

                # 90 天留存
                if created_at <= month_3_ago:
                    users_90_days_ago += 1
                    if is_active:
                        retained_90_days += 1

            except Exception as e:
                logger.warning(f"Failed to process subscription {doc.id}: {e}")
                continue

        # 計算留存率
        day_7_retention = (retained_7_days / max(users_7_days_ago, 1))
        day_30_retention = (retained_30_days / max(users_30_days_ago, 1))
        month_3_retention = (retained_90_days / max(users_90_days_ago, 1))

        return jsonify({
            'day_7_retention': round(day_7_retention, 3),
            'day_30_retention': round(day_30_retention, 3),
            'month_3_retention': round(month_3_retention, 3),
            'cohort_7_days': {
                'total_users': users_7_days_ago,
                'retained_users': retained_7_days
            },
            'cohort_30_days': {
                'total_users': users_30_days_ago,
                'retained_users': retained_30_days
            },
            'cohort_90_days': {
                'total_users': users_90_days_ago,
                'retained_users': retained_90_days
            }
        }), 200

    except Exception as e:
        logger.error(f"Error getting retention analysis: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@admin_analytics_bp.route('/trends', methods=['GET'])
@require_admin
def get_trends():
    """
    獲取趨勢數據（過去 30 天）

    Query Parameters:
        - days: 要獲取的天數（默認 30，最大 90）

    Returns:
        {
            "dates": ["2025-11-01", "2025-11-02", ...],
            "new_users": [5, 8, 12, ...],
            "new_premium_users": [1, 2, 1, ...],
            "active_users": [100, 105, 115, ...]
        }
    """
    if subscription_service is None or db is None:
        return jsonify({'error': 'Service not available'}), 503

    try:
        # 獲取查詢參數
        days = min(int(request.args.get('days', 30)), 90)

        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=days)

        # 獲取所有訂閱（使用緩存）
        all_subscriptions = get_all_subscriptions_cached()

        # 初始化趨勢數據
        trends_data = {}
        for i in range(days + 1):
            date = start_date + timedelta(days=i)
            date_key = date.strftime('%Y-%m-%d')
            trends_data[date_key] = {
                'new_users': 0,
                'new_premium_users': 0,
                'active_users': 0
            }

        # 統計每天的數據
        for doc in all_subscriptions:
            try:
                data = doc.to_dict()
                created_at = data.get('created_at')
                premium_start = data.get('premium_start_at')
                premium_end = data.get('premium_end_at')
                trial_end = data.get('trial_end_at')

                # 統計新用戶
                if created_at and isinstance(created_at, datetime):
                    if created_at >= start_date:
                        date_key = created_at.strftime('%Y-%m-%d')
                        if date_key in trends_data:
                            trends_data[date_key]['new_users'] += 1

                # 統計新付費用戶
                if premium_start and isinstance(premium_start, datetime):
                    if premium_start >= start_date:
                        date_key = premium_start.strftime('%Y-%m-%d')
                        if date_key in trends_data:
                            trends_data[date_key]['new_premium_users'] += 1

                # 統計每天的活躍用戶數
                for i in range(days + 1):
                    date = start_date + timedelta(days=i)
                    date_key = date.strftime('%Y-%m-%d')

                    # 檢查用戶在該日期是否活躍
                    is_active = False
                    if premium_end and isinstance(premium_end, datetime) and premium_end >= date:
                        if premium_start and isinstance(premium_start, datetime) and premium_start <= date:
                            is_active = True
                    elif trial_end and isinstance(trial_end, datetime) and trial_end >= date:
                        if created_at and isinstance(created_at, datetime) and created_at <= date:
                            is_active = True

                    if is_active:
                        trends_data[date_key]['active_users'] += 1

            except Exception as e:
                logger.warning(f"Failed to process subscription {doc.id}: {e}")
                continue

        # 格式化輸出
        sorted_dates = sorted(trends_data.keys())
        return jsonify({
            'dates': sorted_dates,
            'new_users': [trends_data[date]['new_users'] for date in sorted_dates],
            'new_premium_users': [trends_data[date]['new_premium_users'] for date in sorted_dates],
            'active_users': [trends_data[date]['active_users'] for date in sorted_dates]
        }), 200

    except Exception as e:
        logger.error(f"Error getting trends data: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
