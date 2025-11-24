/**
 * 訓練記錄列表頁面
 */
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { workoutApi } from '../services/api';
import { format } from 'date-fns';
import { ArrowLeft, Activity, Calendar, TrendingUp, Clock } from 'lucide-react';

export default function WorkoutListPage() {
  const { uid } = useParams<{ uid: string }>();
  const navigate = useNavigate();
  const [workouts, setWorkouts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (uid) {
      fetchWorkouts();
    }
  }, [uid]);

  const fetchWorkouts = async () => {
    if (!uid) return;

    setLoading(true);
    setError('');
    try {
      const response = await workoutApi.getWorkoutIndex(uid, {
        limit: 50,
      });
      setWorkouts(response.workouts || []);
    } catch (err: any) {
      setError(err.message || '獲取訓練記錄失敗');
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
    return `${minutes}:${String(secs).padStart(2, '0')} /km`;
  };

  const getActivityTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      running: '跑步',
      cycling: '騎行',
      swimming: '游泳',
      walking: '步行',
      hiking: '健行',
    };
    return labels[type] || type;
  };

  const getProviderColor = (provider: string) => {
    const colors: Record<string, string> = {
      strava: 'bg-orange-100 text-orange-800',
      garmin: 'bg-blue-100 text-blue-800',
      apple_health: 'bg-gray-100 text-gray-800',
    };
    return colors[provider] || 'bg-gray-100 text-gray-800';
  };

  const handleWorkoutClick = (workout: any) => {
    navigate(`/users/${uid}/workouts/${workout.provider}/${workout.activity_id}`);
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
      <div>
        <button
          onClick={() => navigate(`/users/${uid}`)}
          className="mb-4 inline-flex items-center text-sm text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="w-4 h-4 mr-1" />
          返回用戶詳情
        </button>
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate(`/users/${uid}`)}
          className="mb-4 inline-flex items-center text-sm text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="w-4 h-4 mr-1" />
          返回用戶詳情
        </button>

        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Activity className="w-6 h-6" />
            訓練記錄
          </h1>
          <div className="text-sm text-gray-500">
            共 {workouts.length} 筆記錄
          </div>
        </div>
      </div>

      {/* Workouts List */}
      {workouts.length > 0 ? (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    日期時間
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    類型
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    距離
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    時長
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    配速
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    心率
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    來源
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {workouts.map((workout, index) => (
                  <tr
                    key={workout.activity_id || index}
                    onClick={() => handleWorkoutClick(workout)}
                    className="hover:bg-gray-50 cursor-pointer transition-colors"
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="flex items-center gap-1">
                        <Calendar className="w-4 h-4 text-gray-400" />
                        {formatDate(workout.start_time_utc)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="flex items-center gap-1">
                        <Activity className="w-4 h-4 text-gray-400" />
                        {getActivityTypeLabel(workout.activity_type)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {workout.distance_m ? `${(workout.distance_m / 1000).toFixed(2)} km` : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="flex items-center gap-1">
                        <Clock className="w-4 h-4 text-gray-400" />
                        {formatDuration(workout.duration_s)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="flex items-center gap-1">
                        <TrendingUp className="w-4 h-4 text-gray-400" />
                        {formatPace(workout.avg_pace_s_per_km)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {workout.avg_heart_rate_bpm ? `${workout.avg_heart_rate_bpm} bpm` : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getProviderColor(workout.provider)}`}>
                        {workout.provider}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <Activity className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">尚無訓練記錄</p>
        </div>
      )}
    </div>
  );
}
