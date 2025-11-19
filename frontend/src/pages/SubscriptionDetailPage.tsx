/**
 * 訂閱詳情頁面
 */
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { subscriptionApi } from '../services/api';
import { SubscriptionDetail } from '../types/subscription';
import { format } from 'date-fns';
import { ArrowLeft, Calendar, User } from 'lucide-react';
import { PaymentPlatformBadge, getPaymentPlatformDescription } from '../utils/paymentPlatform';

export default function SubscriptionDetailPage() {
  const { uid } = useParams<{ uid: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<SubscriptionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Extend modal state
  const [showExtendModal, setShowExtendModal] = useState(false);
  const [extendDays, setExtendDays] = useState(30);
  const [extendReason, setExtendReason] = useState('admin_grant');
  const [extending, setExtending] = useState(false);

  useEffect(() => {
    if (uid) {
      fetchSubscription();
    }
  }, [uid]);

  const fetchSubscription = async () => {
    if (!uid) return;

    setLoading(true);
    setError('');
    try {
      const response = await subscriptionApi.get(uid);
      setData(response);
    } catch (err: any) {
      setError(err.message || '獲取訂閱詳情失敗');
    } finally {
      setLoading(false);
    }
  };

  const handleExtend = async () => {
    if (!uid) return;

    setExtending(true);
    try {
      await subscriptionApi.extend(uid, extendDays, extendReason);
      alert(`成功延長訂閱 ${extendDays} 天！`);
      setShowExtendModal(false);
      fetchSubscription(); // Refresh data
    } catch (err: any) {
      alert(`延長訂閱失敗：${err.message}`);
    } finally {
      setExtending(false);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '-';
    try {
      return format(new Date(dateString), 'yyyy-MM-dd HH:mm');
    } catch {
      return dateString;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'in_trial':
        return 'bg-blue-100 text-blue-800';
      case 'premium_active':
        return 'bg-green-100 text-green-800';
      case 'expired':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'in_trial':
        return '試用中';
      case 'premium_active':
        return '付費會員';
      case 'expired':
        return '已過期';
      default:
        return status;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">載入中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
        {error}
      </div>
    );
  }

  if (!data) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded-md">
        未找到訂閱數據
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/subscriptions')}
          className="inline-flex items-center text-blue-600 hover:text-blue-700 mb-4"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          返回列表
        </button>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">訂閱詳情</h1>
        <p className="text-gray-600">{data.subscription.uid}</p>
      </div>

      {/* Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600 mb-2">訂閱狀態</div>
          <span className={`inline-block px-3 py-1 text-sm font-medium rounded-full ${getStatusColor(data.subscription.status)}`}>
            {getStatusText(data.subscription.status)}
          </span>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600 mb-2">付款平台</div>
          <div className="mt-2">
            <PaymentPlatformBadge platform={data.subscription.payment_platform} />
          </div>
          <div className="text-xs text-gray-500 mt-2">
            {getPaymentPlatformDescription(data.subscription.payment_platform)}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600 mb-2">試用天數</div>
          <div className="text-2xl font-bold text-gray-900">{data.subscription.trial_days} 天</div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600 mb-2">延長天數</div>
          <div className="text-2xl font-bold text-gray-900">{data.subscription.total_extension_days} 天</div>
        </div>
      </div>

      {/* User Info */}
      <div className="bg-white rounded-lg shadow mb-6">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center">
            <User className="w-5 h-5 mr-2" />
            用戶資訊
          </h2>
        </div>
        <div className="px-6 py-4 grid grid-cols-2 gap-4">
          <div>
            <div className="text-sm text-gray-600 mb-1">UID</div>
            <div className="text-sm font-medium text-gray-900">{data.user.uid}</div>
          </div>
          <div>
            <div className="text-sm text-gray-600 mb-1">Email</div>
            <div className="text-sm font-medium text-gray-900">{data.user.email || '-'}</div>
          </div>
          <div>
            <div className="text-sm text-gray-600 mb-1">顯示名稱</div>
            <div className="text-sm font-medium text-gray-900">{data.user.display_name || '-'}</div>
          </div>
          <div>
            <div className="text-sm text-gray-600 mb-1">創建時間</div>
            <div className="text-sm font-medium text-gray-900">{formatDate(data.user.created_at)}</div>
          </div>
        </div>
      </div>

      {/* Subscription Details */}
      <div className="bg-white rounded-lg shadow mb-6">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center">
            <Calendar className="w-5 h-5 mr-2" />
            訂閱詳情
          </h2>
        </div>
        <div className="px-6 py-4 grid grid-cols-2 gap-4">
          <div>
            <div className="text-sm text-gray-600 mb-1">試用開始</div>
            <div className="text-sm font-medium text-gray-900">{formatDate(data.subscription.trial_start_at)}</div>
          </div>
          <div>
            <div className="text-sm text-gray-600 mb-1">試用結束</div>
            <div className="text-sm font-medium text-gray-900">{formatDate(data.subscription.trial_end_at)}</div>
          </div>
          <div>
            <div className="text-sm text-gray-600 mb-1">是否付費會員</div>
            <div className="text-sm font-medium text-gray-900">{data.subscription.is_premium ? '是' : '否'}</div>
          </div>
          <div>
            <div className="text-sm text-gray-600 mb-1">有效訪問權限</div>
            <div className="text-sm font-medium text-gray-900">{data.subscription.has_premium_access ? '是' : '否'}</div>
          </div>
          <div>
            <div className="text-sm text-gray-600 mb-1">邀請碼</div>
            <div className="text-sm font-medium text-gray-900">{data.invite_code || '-'}</div>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex space-x-4">
        <button
          onClick={() => setShowExtendModal(true)}
          className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-md transition-colors"
        >
          延長訂閱
        </button>
      </div>

      {/* Extend Modal */}
      {showExtendModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">延長訂閱</h3>

            <div className="space-y-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  延長天數
                </label>
                <input
                  type="number"
                  value={extendDays}
                  onChange={(e) => setExtendDays(Number(e.target.value))}
                  min="1"
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  延長原因
                </label>
                <select
                  value={extendReason}
                  onChange={(e) => setExtendReason(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="admin_grant">管理員贈送</option>
                  <option value="compensation">補償</option>
                  <option value="promotion">促銷活動</option>
                </select>
              </div>
            </div>

            <div className="flex space-x-4">
              <button
                onClick={handleExtend}
                disabled={extending}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-md transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {extending ? '處理中...' : '確認延長'}
              </button>
              <button
                onClick={() => setShowExtendModal(false)}
                disabled={extending}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 font-medium rounded-md hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                取消
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
