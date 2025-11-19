import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { inviteCodeApi } from '../services/api';
import {
  ArrowLeft,
  CheckCircle,
  XCircle,
  Users,
  Gift,
  Calendar,
  AlertCircle,
  TrendingUp
} from 'lucide-react';
import type { InviteCodeDetail, InviteCodeUsage } from '../types/inviteCode';

export default function InviteCodeDetailPage() {
  const { code } = useParams<{ code: string }>();
  const navigate = useNavigate();

  const [detail, setDetail] = useState<InviteCodeDetail | null>(null);
  const [usages, setUsages] = useState<InviteCodeUsage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (code) {
      fetchDetail();
      fetchUsages();
    }
  }, [code]);

  const fetchDetail = async () => {
    try {
      setLoading(true);
      setError(null);
      const detail = await inviteCodeApi.get(code!);
      setDetail(detail);
    } catch (err: any) {
      console.error('Error fetching invite code detail:', err);
      setError(err.response?.data?.error || 'Failed to load invite code details');
    } finally {
      setLoading(false);
    }
  };

  const fetchUsages = async () => {
    try {
      const response = await inviteCodeApi.getUsages(code!);
      setUsages(response.data);
    } catch (err: any) {
      console.error('Error fetching usages:', err);
    }
  };

  const handleDisable = async () => {
    if (!confirm(`確定要禁用邀請碼 ${code}？`)) {
      return;
    }

    try {
      await inviteCodeApi.disable(code!);
      alert('邀請碼已禁用');
      fetchDetail();
    } catch (err: any) {
      console.error('Error disabling invite code:', err);
      alert(err.response?.data?.error || '禁用失敗');
    }
  };

  const getStatusBadge = (isActive: boolean) => {
    if (isActive) {
      return (
        <span className="inline-flex items-center gap-1 px-3 py-1 text-sm font-medium rounded-full bg-green-100 text-green-700">
          <CheckCircle className="w-4 h-4" />
          啟用中
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-3 py-1 text-sm font-medium rounded-full bg-gray-100 text-gray-600">
        <XCircle className="w-4 h-4" />
        已禁用
      </span>
    );
  };

  const getRewardBadge = (granted: boolean) => {
    if (granted) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-700">
          <CheckCircle className="w-3 h-3" />
          已發放
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-700">
        <AlertCircle className="w-3 h-3" />
        待發放
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="p-6">
        <button
          onClick={() => navigate('/invite-codes')}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          返回列表
        </button>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-medium text-red-900 mb-1">載入錯誤</h3>
            <p className="text-sm text-red-700">{error || '邀請碼不存在'}</p>
          </div>
        </div>
      </div>
    );
  }

  const { invite_code, owner, statistics } = detail;

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/invite-codes')}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          返回列表
        </button>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              邀請碼: <span className="font-mono">{invite_code.code}</span>
            </h1>
            <p className="text-gray-600">
              擁有者: <span className="font-mono text-sm">{invite_code.owner_uid}</span>
            </p>
          </div>
          <div className="flex items-center gap-3">
            {getStatusBadge(invite_code.is_active)}
            {invite_code.is_active && (
              <button
                onClick={handleDisable}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                禁用邀請碼
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600 mb-2">使用進度</div>
          <div className="text-3xl font-bold text-gray-900 mb-3">
            {invite_code.usage_count}/{invite_code.max_usage}
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full ${
                invite_code.usage_count >= invite_code.max_usage
                  ? 'bg-red-500'
                  : invite_code.usage_count / invite_code.max_usage >= 0.8
                  ? 'bg-yellow-500'
                  : 'bg-green-500'
              }`}
              style={{
                width: `${Math.min((invite_code.usage_count / invite_code.max_usage) * 100, 100)}%`
              }}
            />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600 mb-2">總使用次數</div>
          <div className="flex items-center gap-3">
            <Users className="w-8 h-8 text-blue-500" />
            <span className="text-3xl font-bold text-gray-900">
              {statistics.total_usages}
            </span>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600 mb-2">已發放獎勵</div>
          <div className="flex items-center gap-3">
            <CheckCircle className="w-8 h-8 text-green-500" />
            <span className="text-3xl font-bold text-gray-900">
              {statistics.rewarded_usages}
            </span>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600 mb-2">待發放獎勵</div>
          <div className="flex items-center gap-3">
            <AlertCircle className="w-8 h-8 text-yellow-500" />
            <span className="text-3xl font-bold text-gray-900">
              {statistics.pending_rewards}
            </span>
          </div>
        </div>
      </div>

      {/* Details Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Invite Code Info */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">邀請碼資訊</h2>
          </div>
          <div className="px-6 py-4 space-y-4">
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">邀請碼</span>
              <span className="font-mono font-medium text-gray-900">{invite_code.code}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">獎勵天數</span>
              <span className="font-medium text-gray-900">{invite_code.reward_days} 天</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">退費期</span>
              <span className="font-medium text-gray-900">{invite_code.refund_period_days} 天</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">創建時間</span>
              <span className="text-sm text-gray-900">
                {new Date(invite_code.created_at).toLocaleString('zh-TW')}
              </span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span className="text-sm text-gray-600">更新時間</span>
              <span className="text-sm text-gray-900">
                {new Date(invite_code.updated_at).toLocaleString('zh-TW')}
              </span>
            </div>
          </div>
        </div>

        {/* Owner Info */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">擁有者資訊</h2>
          </div>
          <div className="px-6 py-4 space-y-4">
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">用戶 UID</span>
              <span className="font-mono text-sm text-gray-900">{owner.uid}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">訂閱狀態</span>
              {owner.has_subscription ? (
                <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-700">
                  <CheckCircle className="w-3 h-3" />
                  有訂閱
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-600">
                  <XCircle className="w-3 h-3" />
                  無訂閱
                </span>
              )}
            </div>
            <div className="flex justify-between items-center py-2">
              <span className="text-sm text-gray-600">會員類型</span>
              {owner.is_premium ? (
                <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-purple-100 text-purple-700">
                  <Gift className="w-3 h-3" />
                  付費會員
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-600">
                  試用會員
                </span>
              )}
            </div>
            <div className="pt-3">
              <button
                onClick={() => navigate(`/subscriptions/${owner.uid}`)}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                查看訂閱詳情
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Usage Records */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">使用記錄</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  被邀請人
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  使用時間
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  獎勵天數
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  獎勵狀態
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  發放時間
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  退費期檢查
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {usages.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                    暫無使用記錄
                  </td>
                </tr>
              ) : (
                usages.map((usage, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <button
                        onClick={() => navigate(`/subscriptions/${usage.invitee_uid}`)}
                        className="font-mono text-sm text-blue-600 hover:text-blue-900"
                      >
                        {usage.invitee_uid.substring(0, 12)}...
                      </button>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(usage.used_at).toLocaleString('zh-TW')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {usage.reward_days} 天
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getRewardBadge(usage.reward_granted)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {usage.reward_granted_at
                        ? new Date(usage.reward_granted_at).toLocaleString('zh-TW')
                        : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-gray-600">邀請人:</span>
                          {usage.inviter_past_refund_period ? (
                            <CheckCircle className="w-4 h-4 text-green-500" />
                          ) : (
                            <XCircle className="w-4 h-4 text-gray-400" />
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-gray-600">被邀請人:</span>
                          {usage.invitee_past_refund_period ? (
                            <CheckCircle className="w-4 h-4 text-green-500" />
                          ) : (
                            <XCircle className="w-4 h-4 text-gray-400" />
                          )}
                        </div>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
