import React, { useState, useEffect } from 'react';
import { analyticsApi } from '../services/api';
import {
  Users,
  TrendingUp,
  DollarSign,
  Activity,
  ArrowUp,
  ArrowDown,
  AlertCircle
} from 'lucide-react';
import {
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

interface OverviewStats {
  total_users: number;
  trial_users: number;
  premium_users: number;
  active_premium_users: number;
  new_users_today: number;
  new_users_this_week: number;
  new_users_this_month: number;
  trial_conversion_rate: number;
  churn_rate: number;
}

interface RevenueStats {
  current_month_revenue: number;
  last_month_revenue: number;
  annual_recurring_revenue: number;
  average_revenue_per_user: number;
  by_platform: {
    [key: string]: {
      count: number;
      revenue: number;
    };
  };
}

interface RetentionStats {
  day_7_retention: number;
  day_30_retention: number;
  month_3_retention: number;
}

interface TrendData {
  dates: string[];
  new_users: number[];
  new_premium_users: number[];
  active_users: number[];
}

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

export default function DashboardPage() {
  const [overview, setOverview] = useState<OverviewStats | null>(null);
  const [revenue, setRevenue] = useState<RevenueStats | null>(null);
  const [retention, setRetention] = useState<RetentionStats | null>(null);
  const [trends, setTrends] = useState<TrendData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [trendDays, setTrendDays] = useState(30);

  useEffect(() => {
    fetchAllData();
  }, [trendDays]);

  const fetchAllData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [overviewData, revenueData, retentionData, trendsData] = await Promise.all([
        analyticsApi.getOverview(),
        analyticsApi.getRevenue(),
        analyticsApi.getRetention(),
        analyticsApi.getTrends(trendDays),
      ]);

      setOverview(overviewData);
      setRevenue(revenueData);
      setRetention(retentionData);
      setTrends(trendsData);
    } catch (err: any) {
      console.error('Error fetching analytics data:', err);
      setError(err.response?.data?.error || '載入數據失敗');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('zh-TW', {
      style: 'currency',
      currency: 'TWD',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  // Transform trend data for recharts
  const trendChartData = trends
    ? trends.dates.map((date, index) => ({
        date: new Date(date).toLocaleDateString('zh-TW', { month: '2-digit', day: '2-digit' }),
        新用戶: trends.new_users[index],
        新付費用戶: trends.new_premium_users[index],
        活躍用戶: trends.active_users[index],
      }))
    : [];

  // Transform platform data for pie chart
  const platformChartData = revenue
    ? Object.entries(revenue.by_platform).map(([platform, data]) => ({
        name: platform === 'stripe' ? 'Stripe' : platform === 'apple' ? 'Apple IAP' : platform,
        value: data.count,
        revenue: data.revenue,
      }))
    : [];

  const revenueChange = revenue
    ? ((revenue.current_month_revenue - revenue.last_month_revenue) / Math.max(revenue.last_month_revenue, 1)) * 100
    : 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
        <div>
          <h3 className="font-medium text-red-900 mb-1">載入錯誤</h3>
          <p className="text-sm text-red-700">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">數據儀表板</h1>
        <p className="text-gray-600">訂閱系統數據總覽與分析</p>
      </div>

      {/* Overview Stats Cards */}
      {overview && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Total Users */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">總用戶數</p>
                <p className="text-3xl font-bold text-gray-900">{overview.total_users}</p>
                <p className="text-xs text-gray-500 mt-2">
                  本月新增: {overview.new_users_this_month}
                </p>
              </div>
              <div className="p-3 bg-blue-100 rounded-lg">
                <Users className="w-8 h-8 text-blue-600" />
              </div>
            </div>
          </div>

          {/* Premium Users */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">付費用戶</p>
                <p className="text-3xl font-bold text-gray-900">{overview.premium_users}</p>
                <p className="text-xs text-gray-500 mt-2">
                  活躍: {overview.active_premium_users}
                </p>
              </div>
              <div className="p-3 bg-green-100 rounded-lg">
                <TrendingUp className="w-8 h-8 text-green-600" />
              </div>
            </div>
          </div>

          {/* Monthly Revenue */}
          {revenue && (
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">本月收入</p>
                  <p className="text-3xl font-bold text-gray-900">
                    {formatCurrency(revenue.current_month_revenue)}
                  </p>
                  <div className="flex items-center gap-1 mt-2">
                    {revenueChange >= 0 ? (
                      <ArrowUp className="w-3 h-3 text-green-600" />
                    ) : (
                      <ArrowDown className="w-3 h-3 text-red-600" />
                    )}
                    <p className={`text-xs ${revenueChange >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {Math.abs(revenueChange).toFixed(1)}% vs 上月
                    </p>
                  </div>
                </div>
                <div className="p-3 bg-purple-100 rounded-lg">
                  <DollarSign className="w-8 h-8 text-purple-600" />
                </div>
              </div>
            </div>
          )}

          {/* Conversion Rate */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">試用轉換率</p>
                <p className="text-3xl font-bold text-gray-900">
                  {formatPercentage(overview.trial_conversion_rate)}
                </p>
                <p className="text-xs text-gray-500 mt-2">
                  流失率: {formatPercentage(overview.churn_rate)}
                </p>
              </div>
              <div className="p-3 bg-orange-100 rounded-lg">
                <Activity className="w-8 h-8 text-orange-600" />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trends Line Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">用戶趨勢</h2>
            <select
              value={trendDays}
              onChange={(e) => setTrendDays(Number(e.target.value))}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500"
            >
              <option value={7}>最近 7 天</option>
              <option value={30}>最近 30 天</option>
              <option value={90}>最近 90 天</option>
            </select>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trendChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="新用戶" stroke="#3B82F6" strokeWidth={2} />
              <Line type="monotone" dataKey="新付費用戶" stroke="#10B981" strokeWidth={2} />
              <Line type="monotone" dataKey="活躍用戶" stroke="#F59E0B" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Platform Distribution Pie Chart */}
        {revenue && platformChartData.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">付款平台分佈</h2>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={platformChartData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {platformChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: any, name: any, props: any) => [
                  `${value} 用戶 (${formatCurrency(props.payload.revenue)})`,
                  name
                ]} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Retention and Revenue Details */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Retention Stats */}
        {retention && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">用戶留存率</h2>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm text-gray-600">7 天留存</span>
                  <span className="text-lg font-semibold text-gray-900">
                    {formatPercentage(retention.day_7_retention)}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ width: `${retention.day_7_retention * 100}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm text-gray-600">30 天留存</span>
                  <span className="text-lg font-semibold text-gray-900">
                    {formatPercentage(retention.day_30_retention)}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-green-600 h-2 rounded-full"
                    style={{ width: `${retention.day_30_retention * 100}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm text-gray-600">3 個月留存</span>
                  <span className="text-lg font-semibold text-gray-900">
                    {formatPercentage(retention.month_3_retention)}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-purple-600 h-2 rounded-full"
                    style={{ width: `${retention.month_3_retention * 100}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Revenue Details */}
        {revenue && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">收入詳情</h2>
            <div className="space-y-4">
              <div className="flex justify-between items-center py-3 border-b border-gray-200">
                <span className="text-sm text-gray-600">本月收入 (MRR)</span>
                <span className="text-lg font-semibold text-gray-900">
                  {formatCurrency(revenue.current_month_revenue)}
                </span>
              </div>

              <div className="flex justify-between items-center py-3 border-b border-gray-200">
                <span className="text-sm text-gray-600">上月收入</span>
                <span className="text-lg font-semibold text-gray-900">
                  {formatCurrency(revenue.last_month_revenue)}
                </span>
              </div>

              <div className="flex justify-between items-center py-3 border-b border-gray-200">
                <span className="text-sm text-gray-600">年度經常性收入 (ARR)</span>
                <span className="text-lg font-semibold text-gray-900">
                  {formatCurrency(revenue.annual_recurring_revenue)}
                </span>
              </div>

              <div className="flex justify-between items-center py-3">
                <span className="text-sm text-gray-600">平均每用戶收入 (ARPU)</span>
                <span className="text-lg font-semibold text-gray-900">
                  {formatCurrency(revenue.average_revenue_per_user)}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
