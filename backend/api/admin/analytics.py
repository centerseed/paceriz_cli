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

try:
    from firebase_admin import firestore
    from utils.firebase_init import init_firebase

    # 確保 Firebase 已初始化
    init_firebase()
    db = firestore.client()
except Exception as e:
    logging.warning(f"Could not initialize Firebase: {e}")
    db = None

# Try to import api_service modules (optional dependencies)
try:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../api_service')))
    from domains.subscription.subscription_service import subscription_service
    from data_models.subscription_models import SubscriptionStatus, PaymentPlatform
except ImportError as e:
    logging.warning(f"Could not import api_service modules: {e}")
    subscription_service = None
    SubscriptionStatus = None
    PaymentPlatform = None

from middleware.admin_auth import require_admin, get_admin_info
from services.audit_log_service import audit_log_service

logger = logging.getLogger(__name__)

# 創建 Blueprint
admin_analytics_bp = Blueprint('admin_analytics', __name__)

# ========== 緩存機制 ==========
# 簡單的內存緩存，用於減少頻繁的 Firestore 查詢
# 緩存 TTL: 5 分鐘（管理後台數據不需要實時性）
_analytics_cache = {
    'overview': {'data': None, 'timestamp': None},
    'revenue': {'data': None, 'timestamp': None},
    'retention': {'data': None, 'timestamp': None},
    'trends': {'data': None, 'timestamp': None, 'days': None},
    'ttl': 300  # 5 minutes
}

def get_cached_data(cache_key, days=None):
    """獲取緩存數據"""
    now = datetime.now(timezone.utc)
    cache_entry = _analytics_cache.get(cache_key, {})

    # 檢查緩存是否有效
    if (cache_entry.get('data') is not None and
        cache_entry.get('timestamp') is not None and
        (now - cache_entry['timestamp']).total_seconds() < _analytics_cache['ttl']):

        # 對於 trends，還需要檢查 days 參數是否匹配
        if cache_key == 'trends' and days and cache_entry.get('days') != days:
            return None

        logger.info(f"Using cached {cache_key} (age: {(now - cache_entry['timestamp']).total_seconds():.1f}s)")
        return cache_entry['data']

    return None

def set_cached_data(cache_key, data, days=None):
    """設置緩存數據"""
    now = datetime.now(timezone.utc)
    if cache_key not in _analytics_cache:
        _analytics_cache[cache_key] = {}

    _analytics_cache[cache_key]['data'] = data
    _analytics_cache[cache_key]['timestamp'] = now
    if days is not None:
        _analytics_cache[cache_key]['days'] = days

    logger.info(f"Cached {cache_key} data")


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
        # 檢查緩存
        cached_result = get_cached_data('overview')
        if cached_result is not None:
            return jsonify(cached_result), 200

        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=now.weekday())
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        subscriptions_ref = db.collection('subscriptions')

        # ✅ 優化1: 使用聚合查詢獲取總用戶數（不讀取文檔內容）
        total_users = subscriptions_ref.count().get()[0][0].value

        # ✅ 優化2: 使用聚合查詢統計付費用戶數
        premium_users_count = subscriptions_ref.where('is_premium', '==', True).count().get()[0][0].value

        # ✅ 優化3: 使用 where 過濾活躍試用用戶（試用未過期且非付費）
        # 注意: Firestore 不支援同時使用多個不等式，所以我們分批查詢
        trial_users = 0
        try:
            # 查詢試用結束時間大於現在的用戶
            trial_docs = subscriptions_ref.where('trial_end_at', '>', now).where('is_premium', '==', False).limit(1000).stream()
            trial_users = sum(1 for _ in trial_docs)
        except Exception as e:
            logger.warning(f"Failed to count trial users: {e}")

        # ✅ 優化4: 使用 where 過濾活躍付費用戶
        active_premium_users = 0
        total_churned = 0
        try:
            # 查詢付費結束時間大於現在的用戶（活躍）
            active_premium_docs = subscriptions_ref.where('is_premium', '==', True).where('premium_end_at', '>', now).limit(2000).stream()
            active_premium_users = sum(1 for _ in active_premium_docs)

            # 計算流失用戶數 = 總付費 - 活躍付費
            total_churned = max(premium_users_count - active_premium_users, 0)
        except Exception as e:
            logger.warning(f"Failed to count active premium users: {e}")

        # ✅ 優化5: 使用 where 過濾新增用戶（按時間範圍）
        today_new = 0
        week_new = 0
        month_new = 0
        try:
            # 今日新增
            today_new = subscriptions_ref.where('created_at', '>=', today_start).count().get()[0][0].value

            # 本週新增
            week_new = subscriptions_ref.where('created_at', '>=', week_start).count().get()[0][0].value

            # 本月新增
            month_new = subscriptions_ref.where('created_at', '>=', month_start).count().get()[0][0].value
        except Exception as e:
            logger.warning(f"Failed to count new users: {e}")

        # 計算轉換率（付費用戶 / 總用戶）
        trial_conversion_rate = (premium_users_count / max(total_users, 1))

        # 計算流失率（已過期付費用戶 / 總付費用戶）
        churn_rate = (total_churned / max(premium_users_count, 1))

        result = {
            'total_users': total_users,
            'trial_users': trial_users,
            'premium_users': premium_users_count,
            'active_premium_users': active_premium_users,
            'today_new_users': today_new,
            'this_week_new_users': week_new,
            'this_month_new_users': month_new,
            'trial_conversion_rate': round(trial_conversion_rate, 3),
            'churn_rate': round(churn_rate, 3)
        }

        # 設置緩存
        set_cached_data('overview', result)

        return jsonify(result), 200

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
        # 檢查緩存
        cached_result = get_cached_data('revenue')
        if cached_result is not None:
            return jsonify(cached_result), 200

        now = datetime.now(timezone.utc)
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # 計算上個月的開始和結束
        last_month_end = current_month_start - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # 假設月費價格（實際應該從訂閱數據中獲取）
        MONTHLY_PRICE = 150  # TWD 150/月（示例價格）

        # ✅ 優化: 只查詢活躍付費訂閱（付費未過期）而非所有付費訂閱
        subscriptions_ref = db.collection('subscriptions')

        # 查詢當前月活躍的付費訂閱（限制最大1000筆）
        current_active = list(
            subscriptions_ref
            .where('is_premium', '==', True)
            .where('premium_end_at', '>=', current_month_start)
            .limit(1000)
            .stream()
        )

        current_month_revenue = 0
        by_platform = defaultdict(int)
        active_subscriptions = 0

        for doc in current_active:
            try:
                data = doc.to_dict()
                premium_start = data.get('premium_start_at')
                payment_platform = data.get('payment_platform')

                # 確認在當前月內確實活躍
                if isinstance(premium_start, datetime) and premium_start <= now:
                    current_month_revenue += MONTHLY_PRICE
                    active_subscriptions += 1

                    # 按平台統計
                    if payment_platform:
                        by_platform[payment_platform] += MONTHLY_PRICE

            except Exception as e:
                logger.warning(f"Failed to process subscription {doc.id}: {e}")
                continue

        # 查詢上個月活躍的付費訂閱
        last_month_active = subscriptions_ref.where('is_premium', '==', True).where('premium_end_at', '>=', last_month_start).limit(1000).stream()

        last_month_revenue = 0
        for doc in last_month_active:
            try:
                data = doc.to_dict()
                premium_start = data.get('premium_start_at')
                premium_end = data.get('premium_end_at')

                # 確認在上個月內確實活躍
                if isinstance(premium_start, datetime) and isinstance(premium_end, datetime):
                    if premium_start <= last_month_end and premium_end >= last_month_start:
                        # 避免重複計算（當前月也活躍的訂閱）
                        if not (premium_end >= current_month_start):
                            last_month_revenue += MONTHLY_PRICE

            except Exception as e:
                logger.warning(f"Failed to process subscription {doc.id}: {e}")
                continue

        # 補上當前月也活躍的訂閱
        last_month_revenue += current_month_revenue

        # 計算年度經常性收入（ARR）= 活躍訂閱數 * 月費 * 12
        arr = active_subscriptions * MONTHLY_PRICE * 12

        # 計算每用戶平均收入（ARPU）
        arpu = (current_month_revenue / max(active_subscriptions, 1))

        result = {
            'current_month_revenue': current_month_revenue,
            'last_month_revenue': last_month_revenue,
            'annual_recurring_revenue': arr,
            'average_revenue_per_user': round(arpu, 2),
            'active_subscriptions': active_subscriptions,
            'by_platform': dict(by_platform)
        }

        # 設置緩存
        set_cached_data('revenue', result)

        return jsonify(result), 200

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
        # 檢查緩存
        cached_result = get_cached_data('retention')
        if cached_result is not None:
            return jsonify(cached_result), 200

        now = datetime.now(timezone.utc)
        day_7_ago = now - timedelta(days=7)
        day_30_ago = now - timedelta(days=30)
        month_3_ago = now - timedelta(days=90)

        subscriptions_ref = db.collection('subscriptions')

        # ✅ 優化: 使用 where 過濾特定時間範圍的用戶
        # 7天前創建的用戶總數
        users_7_days_ago = subscriptions_ref.where('created_at', '<=', day_7_ago).count().get()[0][0].value

        # 30天前創建的用戶總數
        users_30_days_ago = subscriptions_ref.where('created_at', '<=', day_30_ago).count().get()[0][0].value

        # 90天前創建的用戶總數
        users_90_days_ago = subscriptions_ref.where('created_at', '<=', month_3_ago).count().get()[0][0].value

        # 統計活躍用戶（7天、30天、90天群組）
        # 注意: 由於 Firestore 限制,我們需要分別查詢付費和試用活躍用戶
        retained_7_days = 0
        retained_30_days = 0
        retained_90_days = 0

        # 查詢活躍付費用戶（限制1000筆）
        active_premium = list(subscriptions_ref.where('is_premium', '==', True).where('premium_end_at', '>', now).limit(1000).stream())

        # 查詢活躍試用用戶（限制1000筆）
        active_trial = list(subscriptions_ref.where('is_premium', '==', False).where('trial_end_at', '>', now).limit(1000).stream())

        # 統計各時間段的留存
        for doc in active_premium + active_trial:
            try:
                data = doc.to_dict()
                created_at = data.get('created_at')

                if not created_at or not isinstance(created_at, datetime):
                    continue

                # 7天留存
                if created_at <= day_7_ago:
                    retained_7_days += 1

                # 30天留存
                if created_at <= day_30_ago:
                    retained_30_days += 1

                # 90天留存
                if created_at <= month_3_ago:
                    retained_90_days += 1

            except Exception as e:
                logger.warning(f"Failed to process subscription {doc.id}: {e}")
                continue

        # 計算留存率
        day_7_retention = (retained_7_days / max(users_7_days_ago, 1))
        day_30_retention = (retained_30_days / max(users_30_days_ago, 1))
        month_3_retention = (retained_90_days / max(users_90_days_ago, 1))

        result = {
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
        }

        # 設置緩存
        set_cached_data('retention', result)

        return jsonify(result), 200

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

        # 檢查緩存
        cached_result = get_cached_data('trends', days=days)
        if cached_result is not None:
            return jsonify(cached_result), 200

        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=days)

        subscriptions_ref = db.collection('subscriptions')

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

        # ✅ 優化1: 只查詢時間範圍內創建的用戶（新用戶統計）
        new_users_docs = list(
            subscriptions_ref
            .where('created_at', '>=', start_date)
            .limit(2000)
            .stream()
        )

        for doc in new_users_docs:
            try:
                data = doc.to_dict()
                created_at = data.get('created_at')

                if created_at and isinstance(created_at, datetime):
                    date_key = created_at.strftime('%Y-%m-%d')
                    if date_key in trends_data:
                        trends_data[date_key]['new_users'] += 1

            except Exception as e:
                logger.warning(f"Failed to process new user {doc.id}: {e}")
                continue

        # ✅ 優化2: 只查詢時間範圍內開始付費的用戶（新付費用戶統計）
        new_premium_docs = list(
            subscriptions_ref
            .where('is_premium', '==', True)
            .where('premium_start_at', '>=', start_date)
            .limit(2000)
            .stream()
        )

        for doc in new_premium_docs:
            try:
                data = doc.to_dict()
                premium_start = data.get('premium_start_at')

                if premium_start and isinstance(premium_start, datetime):
                    date_key = premium_start.strftime('%Y-%m-%d')
                    if date_key in trends_data:
                        trends_data[date_key]['new_premium_users'] += 1

            except Exception as e:
                logger.warning(f"Failed to process new premium user {doc.id}: {e}")
                continue

        # ✅ 優化3: 活躍用戶統計 - 簡化版本
        # 注意: 完整的每日活躍用戶統計需要遍歷所有用戶，這裡使用近似算法
        # 只統計最後一天的活躍用戶數，其他天使用估算
        logger.info("Calculating active users for trends (simplified)")

        # 查詢今日活躍的付費用戶
        active_premium_today = subscriptions_ref.where('is_premium', '==', True).where('premium_end_at', '>', now).limit(1000).stream()
        active_premium_count = sum(1 for _ in active_premium_today)

        # 查詢今日活躍的試用用戶
        active_trial_today = subscriptions_ref.where('is_premium', '==', False).where('trial_end_at', '>', now).limit(1000).stream()
        active_trial_count = sum(1 for _ in active_trial_today)

        # 今日總活躍用戶
        total_active_today = active_premium_count + active_trial_count

        # 對於歷史日期，使用線性估算（從 start_date 的活躍用戶數到今日的活躍用戶數）
        # 這是一個簡化的方法，避免對每一天都進行全量查詢
        for i in range(days + 1):
            date_key = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
            # 簡單估算: 假設活躍用戶數線性增長
            estimated_active = int(total_active_today * (0.8 + 0.2 * i / days))  # 從80%增長到100%
            trends_data[date_key]['active_users'] = estimated_active

        # 最後一天使用實際值
        today_key = now.strftime('%Y-%m-%d')
        if today_key in trends_data:
            trends_data[today_key]['active_users'] = total_active_today

        # 格式化輸出
        sorted_dates = sorted(trends_data.keys())
        result = {
            'dates': sorted_dates,
            'new_users': [trends_data[date]['new_users'] for date in sorted_dates],
            'new_premium_users': [trends_data[date]['new_premium_users'] for date in sorted_dates],
            'active_users': [trends_data[date]['active_users'] for date in sorted_dates],
            'note': 'Active users are estimated for performance. For exact data, please use a dedicated analytics tool.'
        }

        # 設置緩存
        set_cached_data('trends', result, days=days)

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error getting trends data: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
