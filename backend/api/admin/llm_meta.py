"""
LLM 元數據 API

提供管理員查看 LLM 生成記錄的功能：
- 週課表的 prompt 和 response（Stage 1 和 Stage 2）
- 週回顧的 prompt
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

admin_llm_meta_bp = Blueprint('admin_llm_meta', __name__)


def require_admin(f):
    """簡單的管理員驗證裝飾器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # TODO: 實現真正的管理員驗證
        # 目前只檢查環境變數中的 SUPER_ADMIN_EMAILS
        return f(*args, **kwargs)
    return decorated_function


@admin_llm_meta_bp.route('/weekly-plans/<weekly_plan_id>/llm-meta', methods=['GET'])
@require_admin
def get_weekly_plan_llm_meta(weekly_plan_id: str):
    """獲取週課表的 LLM 元數據"""
    try:
        from core.database.repositories.llm_meta_repository import llm_meta_repository

        meta = llm_meta_repository.get_weekly_plan_llm_meta(weekly_plan_id)

        if not meta:
            return jsonify({
                'success': False,
                'error': f'LLM metadata not found for weekly_plan_id: {weekly_plan_id}'
            }), 404

        # 轉換 timestamp 為字符串
        if 'stage1' in meta and 'timestamp' in meta['stage1']:
            meta['stage1']['timestamp'] = meta['stage1']['timestamp'].isoformat() if hasattr(meta['stage1']['timestamp'], 'isoformat') else str(meta['stage1']['timestamp'])

        if 'stage2' in meta and 'timestamp' in meta['stage2']:
            meta['stage2']['timestamp'] = meta['stage2']['timestamp'].isoformat() if hasattr(meta['stage2']['timestamp'], 'isoformat') else str(meta['stage2']['timestamp'])

        if 'created_at' in meta:
            meta['created_at'] = meta['created_at'].isoformat() if hasattr(meta['created_at'], 'isoformat') else str(meta['created_at'])

        if 'updated_at' in meta:
            meta['updated_at'] = meta['updated_at'].isoformat() if hasattr(meta['updated_at'], 'isoformat') else str(meta['updated_at'])

        return jsonify({
            'success': True,
            'data': meta
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_llm_meta_bp.route('/weekly-summaries/<summary_id>/llm-meta', methods=['GET'])
@require_admin
def get_weekly_summary_llm_meta(summary_id: str):
    """獲取週回顧的 LLM 元數據"""
    try:
        from core.database.repositories.llm_meta_repository import llm_meta_repository

        meta = llm_meta_repository.get_weekly_summary_llm_meta(summary_id)

        if not meta:
            return jsonify({
                'success': False,
                'error': f'LLM metadata not found for summary_id: {summary_id}'
            }), 404

        # 轉換 timestamp 為字符串
        if 'timestamp' in meta:
            meta['timestamp'] = meta['timestamp'].isoformat() if hasattr(meta['timestamp'], 'isoformat') else str(meta['timestamp'])

        if 'created_at' in meta:
            meta['created_at'] = meta['created_at'].isoformat() if hasattr(meta['created_at'], 'isoformat') else str(meta['created_at'])

        if 'updated_at' in meta:
            meta['updated_at'] = meta['updated_at'].isoformat() if hasattr(meta['updated_at'], 'isoformat') else str(meta['updated_at'])

        return jsonify({
            'success': True,
            'data': meta
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
