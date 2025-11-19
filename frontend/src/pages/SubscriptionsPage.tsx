/**
 * 訂閱列表頁面
 */
import React, { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { subscriptionApi } from '../services/api';
import { Subscription, SubscriptionListResponse } from '../types/subscription';
import { format } from 'date-fns';
import { PaymentPlatformBadge } from '../utils/paymentPlatform';
import { Search, Filter } from 'lucide-react';

export default function SubscriptionsPage() {
  const [data, setData] = useState<SubscriptionListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'premium' | 'trial' | 'expired'>('all');
  const navigate = useNavigate();

  useEffect(() => {
    fetchSubscriptions();
  }, [page]);

  const fetchSubscriptions = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await subscriptionApi.list({ page, limit: 20 });
      setData(response);
    } catch (err: any) {
      setError(err.message || '獲取訂閱列表失敗');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (subscription: Subscription) => {
    const now = new Date();
    const trialEnd = subscription.trial_end_at ? new Date(subscription.trial_end_at) : null;
    const premiumEnd = subscription.premium_end_at ? new Date(subscription.premium_end_at) : null;

    if (subscription.is_premium && premiumEnd && premiumEnd > now) {
      return <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">付費會員</span>;
    } else if (trialEnd && trialEnd > now) {
      return <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">試用中</span>;
    } else {
      return <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded-full">已過期</span>;
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

  // 篩選和搜尋邏輯
  const filteredData = useMemo(() => {
    if (!data) return null;

    let filtered = [...data.data];

    // 搜尋過濾 (UID 或 Email)
    if (searchTerm) {
      const lowerSearch = searchTerm.toLowerCase();
      filtered = filtered.filter((sub) =>
        sub.uid.toLowerCase().includes(lowerSearch)
      );
    }

    // 狀態過濾
    if (statusFilter !== 'all') {
      const now = new Date();
      filtered = filtered.filter((sub) => {
        const trialEnd = sub.trial_end_at ? new Date(sub.trial_end_at) : null;
        const premiumEnd = sub.premium_end_at ? new Date(sub.premium_end_at) : null;

        if (statusFilter === 'premium') {
          return sub.is_premium && premiumEnd && premiumEnd > now;
        } else if (statusFilter === 'trial') {
          return trialEnd && trialEnd > now && !(sub.is_premium && premiumEnd && premiumEnd > now);
        } else if (statusFilter === 'expired') {
          return (!trialEnd || trialEnd <= now) && (!premiumEnd || premiumEnd <= now || !sub.is_premium);
        }
        return true;
      });
    }

    return {
      ...data,
      data: filtered,
      pagination: {
        ...data.pagination,
        total: filtered.length,
      },
    };
  }, [data, searchTerm, statusFilter]);

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

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">訂閱管理</h1>
        <p className="text-gray-600">管理用戶的訂閱狀態</p>
      </div>

      {/* Stats */}
      {data && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm text-gray-600 mb-1">總訂閱數</div>
            <div className="text-3xl font-bold text-gray-900">{data.pagination.total}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm text-gray-600 mb-1">當前頁面</div>
            <div className="text-3xl font-bold text-gray-900">{data.pagination.page} / {data.pagination.total_pages}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-sm text-gray-600 mb-1">每頁數量</div>
            <div className="text-3xl font-bold text-gray-900">{data.pagination.limit}</div>
          </div>
        </div>
      )}

      {/* Search and Filter */}
      <div className="mb-6 flex flex-col sm:flex-row gap-4">
        {/* Search Box */}
        <div className="flex-1 relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            placeholder="搜索訂閱用戶 UID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          />
        </div>

        {/* Status Filter */}
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Filter className="h-5 w-5 text-gray-400" />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as any)}
            className="block w-full pl-10 pr-10 py-2 border border-gray-300 rounded-md leading-5 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          >
            <option value="all">所有狀態</option>
            <option value="premium">付費會員</option>
            <option value="trial">試用中</option>
            <option value="expired">已過期</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white shadow-md rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                用戶 UID
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                狀態
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                付款平台
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                試用結束時間
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                延長天數
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                操作
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredData?.data.map((subscription) => (
              <tr key={subscription.uid} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {subscription.uid}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {getStatusBadge(subscription)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <PaymentPlatformBadge platform={subscription.payment_platform} />
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatDate(subscription.trial_end_at)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {subscription.total_extension_days} 天
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-600">
                  <button
                    onClick={() => navigate(`/subscriptions/${subscription.uid}`)}
                    className="hover:underline"
                  >
                    查看詳情
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Pagination */}
        {data && data.pagination.total_pages > 1 && (
          <div className="bg-gray-50 px-6 py-4 flex items-center justify-between border-t border-gray-200">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              上一頁
            </button>
            <span className="text-sm text-gray-700">
              第 {page} 頁，共 {data.pagination.total_pages} 頁
            </span>
            <button
              onClick={() => setPage(Math.min(data.pagination.total_pages, page + 1))}
              disabled={page === data.pagination.total_pages}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              下一頁
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
