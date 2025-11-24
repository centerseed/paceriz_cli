/**
 * 訓練記錄詳情頁面
 * 顯示訓練的詳細數據，包括心率和配速圖表
 */
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { workoutApi } from '../services/api';
import { format } from 'date-fns';
import {
  ArrowLeft,
  Activity,
  Calendar,
  Clock,
  TrendingUp,
  Heart,
  MapPin,
  Zap,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

export default function WorkoutDetailPage() {
  const { uid, provider, activityId } = useParams<{
    uid: string;
    provider: string;
    activityId: string;
  }>();
  const navigate = useNavigate();
  const [workout, setWorkout] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (uid && provider && activityId) {
      fetchWorkoutDetail();
    }
  }, [uid, provider, activityId]);

  const fetchWorkoutDetail = async () => {
    if (!uid || !provider || !activityId) return;

    setLoading(true);
    setError('');
    try {
      const response = await workoutApi.getWorkoutDetail(uid, provider, activityId);
      setWorkout(response.workout);
    } catch (err: any) {
      setError(err.message || '獲取訓練詳情失敗');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string | any) => {
    if (!dateString) return '-';
    try {
      if (typeof dateString === 'object' && '_seconds' in dateString) {
        return format(new Date(dateString._seconds * 1000), 'yyyy-MM-dd HH:mm');
      }
      return format(new Date(dateString), 'yyyy-MM-dd HH:mm');
    } catch {
      return String(dateString);
    }
  };

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    if (hours > 0) {
      return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    }
    return `${minutes}:${String(secs).padStart(2, '0')}`;
  };

  const formatPace = (seconds_per_km: number) => {
    if (!seconds_per_km) return '-';
    const minutes = Math.floor(seconds_per_km / 60);
    const secs = Math.floor(seconds_per_km % 60);
    return `${minutes}:${String(secs).padStart(2, '0')}`;
  };

  // 準備圖表數據
  const prepareChartData = () => {
    if (!workout?.laps || workout.laps.length === 0) {
      return [];
    }

    return workout.laps.map((lap: any, index: number) => ({
      lap: index + 1,
      pace: lap.avg_pace_s_per_km ? lap.avg_pace_s_per_km / 60 : null, // 轉換為分鐘
      heartRate: lap.avg_heart_rate_bpm || null,
      distance: lap.total_distance_m ? (lap.total_distance_m / 1000).toFixed(2) : null,
    }));
  };

  const chartData = prepareChartData();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">載入中...</div>
      </div>
    );
  }

  if (error || !workout) {
    return (
      <div>
        <button
          onClick={() => navigate(`/users/${uid}/workouts`)}
          className="mb-4 inline-flex items-center text-sm text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="w-4 h-4 mr-1" />
          返回訓練列表
        </button>
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
          {error || '訓練記錄不存在'}
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate(`/users/${uid}/workouts`)}
          className="mb-4 inline-flex items-center text-sm text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="w-4 h-4 mr-1" />
          返回訓練列表
        </button>

        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Activity className="w-6 h-6" />
            訓練詳情
          </h1>
          <span className="text-sm text-gray-500">
            {provider} · {activityId}
          </span>
        </div>
      </div>

      {/* 基本信息卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center gap-2 text-gray-600 mb-2">
            <Calendar className="w-4 h-4" />
            <span className="text-xs font-medium uppercase">開始時間</span>
          </div>
          <div className="text-lg font-bold text-gray-900">{formatDate(workout.start_time_utc)}</div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center gap-2 text-gray-600 mb-2">
            <MapPin className="w-4 h-4" />
            <span className="text-xs font-medium uppercase">距離</span>
          </div>
          <div className="text-lg font-bold text-gray-900">
            {workout.distance_m ? `${(workout.distance_m / 1000).toFixed(2)} km` : '-'}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center gap-2 text-gray-600 mb-2">
            <Clock className="w-4 h-4" />
            <span className="text-xs font-medium uppercase">時長</span>
          </div>
          <div className="text-lg font-bold text-gray-900">{formatDuration(workout.duration_s)}</div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center gap-2 text-gray-600 mb-2">
            <TrendingUp className="w-4 h-4" />
            <span className="text-xs font-medium uppercase">平均配速</span>
          </div>
          <div className="text-lg font-bold text-gray-900">
            {workout.avg_pace_s_per_km ? `${formatPace(workout.avg_pace_s_per_km)} /km` : '-'}
          </div>
        </div>
      </div>

      {/* 進階數據 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center gap-2 text-red-600 mb-2">
            <Heart className="w-4 h-4" />
            <span className="text-xs font-medium uppercase">平均心率</span>
          </div>
          <div className="text-lg font-bold text-gray-900">
            {workout.avg_heart_rate_bpm ? `${workout.avg_heart_rate_bpm} bpm` : '-'}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center gap-2 text-red-600 mb-2">
            <Heart className="w-4 h-4" />
            <span className="text-xs font-medium uppercase">最大心率</span>
          </div>
          <div className="text-lg font-bold text-gray-900">
            {workout.max_heart_rate_bpm ? `${workout.max_heart_rate_bpm} bpm` : '-'}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center gap-2 text-orange-600 mb-2">
            <Zap className="w-4 h-4" />
            <span className="text-xs font-medium uppercase">消耗卡路里</span>
          </div>
          <div className="text-lg font-bold text-gray-900">
            {workout.calories ? `${workout.calories} kcal` : '-'}
          </div>
        </div>
      </div>

      {/* 圖表區域 */}
      {chartData.length > 0 && (
        <div className="space-y-6">
          {/* 配速圖表 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              配速分析
            </h2>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="lap"
                  label={{ value: '圈數', position: 'insideBottom', offset: -5 }}
                />
                <YAxis
                  label={{ value: '配速 (分鐘/公里)', angle: -90, position: 'insideLeft' }}
                  domain={['dataMin - 0.5', 'dataMax + 0.5']}
                  tickFormatter={(value) => value.toFixed(1)}
                />
                <Tooltip
                  formatter={(value: any, name: string) => {
                    if (name === 'pace') {
                      const minutes = Math.floor(value);
                      const seconds = Math.round((value - minutes) * 60);
                      return [`${minutes}:${String(seconds).padStart(2, '0')} /km`, '配速'];
                    }
                    return [value, name];
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="pace"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  name="配速"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* 心率圖表 */}
          {chartData.some((d) => d.heartRate) && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Heart className="w-5 h-5 text-red-600" />
                心率分析
              </h2>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="lap"
                    label={{ value: '圈數', position: 'insideBottom', offset: -5 }}
                  />
                  <YAxis
                    label={{ value: '心率 (bpm)', angle: -90, position: 'insideLeft' }}
                    domain={['dataMin - 10', 'dataMax + 10']}
                  />
                  <Tooltip formatter={(value: any) => [`${value} bpm`, '心率']} />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="heartRate"
                    stroke="#ef4444"
                    strokeWidth={2}
                    dot={{ r: 4 }}
                    name="心率"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* Laps 數據表格 */}
      {workout.laps && workout.laps.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6 mt-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">圈速數據</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    圈數
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    距離
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    時長
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    配速
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    平均心率
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    最大心率
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {workout.laps.map((lap: any, index: number) => (
                  <tr key={index}>
                    <td className="px-4 py-3 text-sm text-gray-900">{lap.lap_number || index + 1}</td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {lap.total_distance_m ? `${(lap.total_distance_m / 1000).toFixed(2)} km` : '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {formatDuration(lap.total_time_s)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {lap.avg_pace_s_per_km ? `${formatPace(lap.avg_pace_s_per_km)} /km` : '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {lap.avg_heart_rate_bpm ? `${lap.avg_heart_rate_bpm} bpm` : '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {lap.max_heart_rate_bpm ? `${lap.max_heart_rate_bpm} bpm` : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
