"""
訂閱測試工具 API

提供開發環境下的訂閱管理功能：
- 開始試用
- 白名單管理
- 延長訂閱
- 檢查訂閱狀態
"""
import sys
import os

# Add api_service to path
API_SERVICE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../../../api_service')
)
if API_SERVICE_PATH not in sys.path:
    sys.path.append(API_SERVICE_PATH)

from flask import Blueprint, request, jsonify
from functools import wraps
from datetime import datetime

from domains.subscription.subscription_service import subscription_service
from data_models.subscription_models import ExtensionReason

admin_subscription_tools_bp = Blueprint('admin_subscription_tools', __name__)


def require_admin(f):
    """簡單的管理員驗證裝飾器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # TODO: 實現真正的管理員驗證
        # 目前只檢查環境變數中的 SUPER_ADMIN_EMAILS
        return f(*args, **kwargs)
    return decorated_function


@admin_subscription_tools_bp.route('/start-trial', methods=['POST'])
@require_admin
def start_trial():
    """開始試用期"""
    try:
        data = request.json
        uid = data.get('uid')
        trial_days = data.get('trial_days', 14)

        if not uid:
            return jsonify({'error': 'uid is required'}), 400

        result = subscription_service.start_trial(
            uid=uid,
            trial_days=trial_days
        )

        return jsonify({
            'success': True,
            'message': f'成功為用戶 {uid} 開始 {trial_days} 天試用',
            'data': {
                'uid': uid,
                'trial_days': trial_days,
                'trial_start': result.get('trial_start'),
                'trial_end': result.get('trial_end'),
                'status': result.get('status')
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@admin_subscription_tools_bp.route('/add-whitelist', methods=['POST'])
@require_admin
def add_whitelist():
    """加入白名單"""
    try:
        data = request.json
        uid = data.get('uid')
        reason = data.get('reason', 'test_account')
        granted_by = data.get('granted_by', 'admin')

        if not uid:
            return jsonify({'error': 'uid is required'}), 400

        result = subscription_service.add_to_whitelist(
            uid=uid,
            reason=reason,
            granted_by=granted_by
        )

        return jsonify({
            'success': True,
            'message': f'成功將用戶 {uid} 加入白名單',
            'data': {
                'uid': uid,
                'reason': reason,
                'granted_by': granted_by,
                'granted_at': result.get('granted_at')
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@admin_subscription_tools_bp.route('/remove-whitelist', methods=['POST'])
@require_admin
def remove_whitelist():
    """移出白名單"""
    try:
        data = request.json
        uid = data.get('uid')

        if not uid:
            return jsonify({'error': 'uid is required'}), 400

        result = subscription_service.remove_from_whitelist(uid=uid)

        return jsonify({
            'success': True,
            'message': f'成功將用戶 {uid} 移出白名單',
            'data': result
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@admin_subscription_tools_bp.route('/extend', methods=['POST'])
@require_admin
def extend_subscription():
    """延長訂閱"""
    try:
        data = request.json
        uid = data.get('uid')
        days = data.get('days')
        reason = data.get('reason', 'admin')
        granted_by = data.get('granted_by', 'admin')
        notes = data.get('notes')

        if not uid:
            return jsonify({'error': 'uid is required'}), 400
        if not days:
            return jsonify({'error': 'days is required'}), 400

        # 解析原因
        reason_map = {
            'admin': ExtensionReason.ADMIN_GRANT,
            'referral': ExtensionReason.REFERRAL_REWARD,
            'promotion': ExtensionReason.PROMOTION,
            'compensation': ExtensionReason.COMPENSATION,
            'other': ExtensionReason.OTHER
        }
        extension_reason = reason_map.get(reason, ExtensionReason.ADMIN_GRANT)

        result = subscription_service.extend_subscription(
            uid=uid,
            days=days,
            reason=extension_reason,
            granted_by=granted_by,
            notes=notes
        )

        return jsonify({
            'success': True,
            'message': f'成功為用戶 {uid} 延長 {days} 天訂閱',
            'data': {
                'uid': uid,
                'days': days,
                'reason': reason,
                'new_end_date': result.get('new_end_date'),
                'total_days': result.get('total_days')
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@admin_subscription_tools_bp.route('/check/<uid>', methods=['GET'])
@require_admin
def check_subscription(uid: str):
    """檢查訂閱狀態"""
    try:
        # 獲取訂閱摘要
        summary = subscription_service.get_subscription_summary(uid=uid)

        # 檢查權限
        has_access = subscription_service.can_access_premium_features(
            uid=uid,
            auto_start_trial=False
        )

        # 檢查白名單
        is_whitelisted = subscription_service.is_whitelisted(uid=uid)

        return jsonify({
            'success': True,
            'data': {
                'summary': summary,
                'has_premium_access': has_access,
                'is_whitelisted': is_whitelisted
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@admin_subscription_tools_bp.route('/test-auto-trial', methods=['POST'])
@require_admin
def test_auto_trial():
    """測試自動試用功能"""
    try:
        data = request.json
        uid = data.get('uid')

        if not uid:
            return jsonify({'error': 'uid is required'}), 400

        # 先檢查是否有訂閱
        summary = subscription_service.get_subscription_summary(uid=uid)

        if summary.get('status') != 'no_trial':
            return jsonify({
                'success': False,
                'error': f"用戶已有訂閱記錄，狀態: {summary.get('status')}。自動試用僅對沒有訂閱記錄的用戶生效。"
            }), 400

        # 測試自動試用
        has_access = subscription_service.can_access_premium_features(
            uid=uid,
            auto_start_trial=True
        )

        # 獲取新的訂閱狀態
        new_summary = subscription_service.get_subscription_summary(uid=uid)

        return jsonify({
            'success': True,
            'message': '自動試用測試成功' if has_access else '自動試用失敗',
            'data': {
                'has_access': has_access,
                'auto_start_trial_enabled': subscription_service.AUTO_START_TRIAL_FOR_NEW_USERS,
                'auto_trial_days': subscription_service.AUTO_TRIAL_DAYS,
                'summary': new_summary
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


# ========== Apple IAP Mock 測試 API ==========

@admin_subscription_tools_bp.route('/iap/set-mock-mode', methods=['POST'])
@require_admin
def set_iap_mock_mode():
    """設置 IAP Mock Adapter 測試模式（僅開發環境）"""
    try:
        # 僅在開發環境允許
        if os.environ.get('ENVIRONMENT') != 'dev':
            return jsonify({
                'success': False,
                'error': 'Only available in dev environment'
            }), 403

        data = request.json
        mode = data.get('mode', 'success')

        # 驗證模式
        valid_modes = ['success', 'expired', 'invalid', 'malformed', 'server_error']
        if mode not in valid_modes:
            return jsonify({
                'success': False,
                'error': f'Invalid mode. Must be one of: {", ".join(valid_modes)}'
            }), 400

        # 設置 Mock Adapter
        from tests.mocks.mock_apple_iap_adapter import MockAppleIAPAdapter
        from domains.subscription.services.unified_iap_service import unified_iap_service

        mock_adapter = MockAppleIAPAdapter()
        mock_adapter.set_mode(mode)
        unified_iap_service.set_apple_adapter(mock_adapter)
        unified_iap_service.clear_audit_log()

        return jsonify({
            'success': True,
            'message': f'Mock mode set to: {mode}',
            'data': {'mode': mode}
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@admin_subscription_tools_bp.route('/iap/test-verify', methods=['POST'])
@require_admin
def test_iap_verify():
    """測試 IAP 購買驗證"""
    try:
        data = request.json
        uid = data.get('uid')
        platform = data.get('platform', 'apple')
        purchase_token = data.get('purchase_token', 'test_receipt')

        if not uid:
            return jsonify({'error': 'uid is required'}), 400

        from domains.subscription.services.unified_iap_service import unified_iap_service

        # 驗證購買
        result = unified_iap_service.verify_purchase(platform, purchase_token, uid)

        # 獲取訂閱狀態
        subscription = unified_iap_service.get_subscription_status(uid)

        return jsonify({
            'success': True,
            'data': {
                'verification': {
                    'success': result.success,
                    'platform': result.platform.value if result.success else None,
                    'subscription_info': result.subscription_info if result.success else None,
                    'error': result.error if not result.success else None
                },
                'subscription_status': subscription
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@admin_subscription_tools_bp.route('/iap/test-restore', methods=['POST'])
@require_admin
def test_iap_restore():
    """測試 IAP 恢復購買"""
    try:
        data = request.json
        uid = data.get('uid')
        platform = data.get('platform', 'apple')
        purchase_token = data.get('purchase_token', 'restore_receipt')

        if not uid:
            return jsonify({'error': 'uid is required'}), 400

        from domains.subscription.services.unified_iap_service import unified_iap_service

        # 恢復購買
        result = unified_iap_service.restore_purchases(platform, purchase_token, uid)

        # 獲取訂閱狀態
        subscription = unified_iap_service.get_subscription_status(uid)

        return jsonify({
            'success': True,
            'data': {
                'restore': {
                    'success': result.success,
                    'platform': result.platform.value if result.success else None,
                    'subscription_info': result.subscription_info if result.success else None,
                    'error': result.error if not result.success else None
                },
                'subscription_status': subscription
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@admin_subscription_tools_bp.route('/iap/test-webhook', methods=['POST'])
@require_admin
def test_iap_webhook():
    """測試 IAP Webhook 處理"""
    try:
        data = request.json
        webhook_type = data.get('webhook_type', 'refund')

        from tests.fixtures.apple_iap_fixtures import AppleIAPFixtures
        from domains.subscription.services.unified_iap_service import unified_iap_service

        # 獲取對應的 webhook fixture
        webhook_map = {
            'refund': AppleIAPFixtures.refund_webhook,
            'renew': AppleIAPFixtures.did_renew_webhook,
            'fail_to_renew': AppleIAPFixtures.did_fail_to_renew_webhook
        }

        if webhook_type not in webhook_map:
            return jsonify({
                'success': False,
                'error': f'Invalid webhook_type. Must be one of: {", ".join(webhook_map.keys())}'
            }), 400

        webhook = webhook_map[webhook_type]()

        # 處理 webhook
        success = unified_iap_service.handle_webhook('apple', webhook)

        # 獲取審計日誌
        audit_logs = unified_iap_service.get_audit_log()

        return jsonify({
            'success': True,
            'data': {
                'webhook_processed': success,
                'webhook_type': webhook_type,
                'webhook_data': webhook,
                'audit_log': audit_logs[-3:] if len(audit_logs) > 0 else []  # 最近 3 條記錄
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@admin_subscription_tools_bp.route('/iap/audit-log', methods=['GET'])
@require_admin
def get_iap_audit_log():
    """獲取 IAP 審計日誌"""
    try:
        from domains.subscription.services.unified_iap_service import unified_iap_service

        audit_logs = unified_iap_service.get_audit_log()

        return jsonify({
            'success': True,
            'data': {
                'total_count': len(audit_logs),
                'logs': audit_logs
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@admin_subscription_tools_bp.route('/iap/clear-audit-log', methods=['POST'])
@require_admin
def clear_iap_audit_log():
    """清除 IAP 審計日誌"""
    try:
        from domains.subscription.services.unified_iap_service import unified_iap_service

        unified_iap_service.clear_audit_log()

        return jsonify({
            'success': True,
            'message': 'Audit log cleared'
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
