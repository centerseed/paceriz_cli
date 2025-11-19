/**
 * 用戶詳情頁面
 */
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { usersApi, llmMetaApi } from '../services/api';
import { format } from 'date-fns';
import {
  ArrowLeft, User as UserIcon, Mail, Calendar, Activity,
  Heart, Trophy, Target, TrendingUp, Clock, MapPin, ChevronDown, ChevronRight,
  Eye
} from 'lucide-react';
import SubscriptionTools from '../components/SubscriptionTools';
import LLMMetaModal from '../components/LLMMetaModal';

export default function UserDetailPage() {
  const { uid } = useParams<{ uid: string }>();
  const navigate = useNavigate();
  const [user, setUser] = useState<any>(null);
  const [trainingOverview, setTrainingOverview] = useState<any>(null);
  const [weeklyPlan, setWeeklyPlan] = useState<any>(null);
  const [weeklySummary, setWeeklySummary] = useState<any>(null);
  const [readiness, setReadiness] = useState<any>(null);
  const [readinessHistory, setReadinessHistory] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [stagesExpanded, setStagesExpanded] = useState(false);

  // LLM Meta Modal state
  const [llmMetaModal, setLlmMetaModal] = useState<{
    isOpen: boolean;
    type: 'weekly-plan' | 'weekly-summary' | null;
    data: any;
  }>({
    isOpen: false,
    type: null,
    data: null,
  });

  useEffect(() => {
    if (uid) {
      fetchUser();
    }
  }, [uid]);

  const fetchUser = async () => {
    if (!uid) return;

    setLoading(true);
    setError('');
    try {
      const [userResponse, trainingResponse, weeklyResponse, summaryResponse, readinessResponse, readinessHistoryResponse] = await Promise.all([
        usersApi.get(uid),
        usersApi.getTrainingOverview(uid).catch(() => ({ training_overview: null })),
        usersApi.getWeeklyPlan(uid).catch(() => ({ weekly_plan: null })),
        usersApi.getWeeklySummary(uid).catch(() => ({ weekly_summary: null })),
        usersApi.getReadiness(uid).catch(() => ({ readiness: null })),
        usersApi.getReadinessHistory(uid, 28).catch(() => ({ history: [] })),
      ]);
      setUser(userResponse);
      setTrainingOverview(trainingResponse.training_overview);
      setWeeklyPlan(weeklyResponse.weekly_plan);
      setWeeklySummary(summaryResponse.weekly_summary);
      setReadiness(readinessResponse.readiness);
      setReadinessHistory(readinessHistoryResponse.history);
    } catch (err: any) {
      setError(err.message || '獲取用戶詳情失敗');
    } finally {
      setLoading(false);
    }
  };

  const handleViewWeeklyPlanMeta = async () => {
    if (!user?.active_weekly_plan_id) {
      alert('無法獲取週課表 ID');
      return;
    }

    try {
      const response = await llmMetaApi.getWeeklyPlanMeta(user.active_weekly_plan_id);
      if (response.success) {
        setLlmMetaModal({
          isOpen: true,
          type: 'weekly-plan',
          data: response.data,
        });
      } else {
        alert(`無法獲取 LLM 元數據: ${response.error}`);
      }
    } catch (error: any) {
      alert(`獲取失敗: ${error.message || '未知錯誤'}`);
    }
  };

  const handleViewWeeklySummaryMeta = async () => {
    if (!user?.active_weekly_plan_id) {
      alert('無法獲取週課表 ID');
      return;
    }

    // 計算 summary_id: {weekly_plan_id}_summary
    // 例如: "003bcz2NC4aLX0PgJARs_11" -> 從中提取week並減1 -> "003bcz2NC4aLX0PgJARs_10_summary"
    const parts = user.active_weekly_plan_id.split('_');
    if (parts.length < 2) {
      alert('無法解析週課表 ID');
      return;
    }

    const currentWeek = parseInt(parts[parts.length - 1]);
    const lastWeek = currentWeek - 1;
    const prefix = parts.slice(0, -1).join('_');
    const summaryId = `${prefix}_${lastWeek}_summary`;

    try {
      const response = await llmMetaApi.getWeeklySummaryMeta(summaryId);
      if (response.success) {
        setLlmMetaModal({
          isOpen: true,
          type: 'weekly-summary',
          data: response.data,
        });
      } else {
        alert(`無法獲取 LLM 元數據: ${response.error}`);
      }
    } catch (error: any) {
      alert(`獲取失敗: ${error.message || '未知錯誤'}`);
    }
  };

  const handleCloseLLMMetaModal = () => {
    setLlmMetaModal({
      isOpen: false,
      type: null,
      data: null,
    });
  };

  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return '-';
    try {
      if (typeof dateString === 'object' && '_seconds' in dateString) {
        return format(new Date((dateString as any)._seconds * 1000), 'yyyy-MM-dd HH:mm');
      }
      return format(new Date(dateString), 'yyyy-MM-dd HH:mm');
    } catch {
      return String(dateString);
    }
  };

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    if (hours > 0) {
      return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    }
    return `${minutes}:${String(secs).padStart(2, '0')}`;
  };

  const getWeekdayName = (day: number) => {
    const days = ['', '週一', '週二', '週三', '週四', '週五', '週六', '週日'];
    return days[day] || day;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">載入中...</div>
      </div>
    );
  }

  if (error || !user) {
    return (
      <div>
        <button
          onClick={() => navigate('/users')}
          className="mb-4 inline-flex items-center text-sm text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="w-4 h-4 mr-1" />
          返回用戶列表
        </button>
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
          {error || '用戶不存在'}
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/users')}
          className="mb-4 inline-flex items-center text-sm text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="w-4 h-4 mr-1" />
          返回用戶列表
        </button>

        <div className="flex items-center gap-4">
          {user.photo_url ? (
            <img src={user.photo_url} alt={user.display_name} className="w-16 h-16 rounded-full" />
          ) : (
            <div className="w-16 h-16 rounded-full bg-gray-200 flex items-center justify-center">
              <UserIcon className="w-8 h-8 text-gray-400" />
            </div>
          )}
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{user.display_name || '未設定名稱'}</h1>
            <p className="text-gray-600">{user.email}</p>
            <p className="text-xs text-gray-500">UID: {uid}</p>
          </div>
        </div>
      </div>

      {/* Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* 基本資訊 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <UserIcon className="w-5 h-5" />
            基本資訊
          </h2>
          <dl className="space-y-3">
            <div className="flex justify-between">
              <dt className="text-sm text-gray-600">Email</dt>
              <dd className="text-sm font-medium text-gray-900">{user.email || '-'}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-sm text-gray-600">顯示名稱</dt>
              <dd className="text-sm font-medium text-gray-900">{user.display_name || '-'}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-sm text-gray-600">登入方式</dt>
              <dd className="text-sm font-medium text-gray-900">{user.auth_provider || '-'}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-sm text-gray-600">語言偏好</dt>
              <dd className="text-sm font-medium text-gray-900">{user.preferred_language || 'zh-TW'}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-sm text-gray-600">註冊時間</dt>
              <dd className="text-sm font-medium text-gray-900">{formatDate(user.created_at)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-sm text-gray-600">最後登入</dt>
              <dd className="text-sm font-medium text-gray-900">{formatDate(user.last_login)}</dd>
            </div>
            {/* 心率數據 */}
            <div className="border-t border-gray-200 pt-3 mt-3">
              <div className="flex justify-between">
                <dt className="text-sm text-gray-600">最大心率</dt>
                <dd className="text-sm font-medium text-gray-900">{user.max_hr ? `${user.max_hr} bpm` : '-'}</dd>
              </div>
              <div className="flex justify-between mt-2">
                <dt className="text-sm text-gray-600">休息心率</dt>
                <dd className="text-sm font-medium text-gray-900">{user.relaxing_hr ? `${user.relaxing_hr} bpm` : '-'}</dd>
              </div>
            </div>

            {/* 調試信息 */}
            <div className="border-t border-gray-200 pt-3 mt-3">
              <div className="flex justify-between">
                <dt className="text-sm text-gray-600">Plan Overview ID</dt>
                <dd className="text-xs font-mono text-gray-700 break-all">{user.active_training_id || '-'}</dd>
              </div>
              <div className="flex justify-between mt-2">
                <dt className="text-sm text-gray-600">Weekly Plan ID</dt>
                <dd className="text-xs font-mono text-gray-700 break-all">{user.active_weekly_plan_id || '-'}</dd>
              </div>
            </div>
          </dl>
        </div>

        {/* 訓練總覽 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            訓練總覽
          </h2>
          {trainingOverview ? (
            <div className="space-y-4">
              <div className="border-b border-gray-200 pb-3">
                <div className="flex justify-between items-start mb-2">
                  <dt className="text-sm text-gray-600">訓練計劃</dt>
                  <dd className="text-sm font-medium text-gray-900">{trainingOverview.training_plan_name || '-'}</dd>
                </div>
                <div className="flex justify-between items-start mb-2">
                  <dt className="text-sm text-gray-600">總週數</dt>
                  <dd className="text-sm font-medium text-gray-900">{trainingOverview.total_weeks ? `${trainingOverview.total_weeks} 週` : '-'}</dd>
                </div>
                <div className="flex justify-between items-start mb-2">
                  <dt className="text-sm text-gray-600">目標評估</dt>
                  <dd className="text-sm font-medium text-gray-900">{trainingOverview.target_evaluate || '-'}</dd>
                </div>
              </div>

              {trainingOverview.training_hightlight && (
                <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
                  <dt className="text-xs text-blue-800 font-medium mb-1">訓練重點</dt>
                  <dd className="text-sm text-blue-900">{trainingOverview.training_hightlight}</dd>
                </div>
              )}

              {trainingOverview.training_stage_discription && trainingOverview.training_stage_discription.length > 0 && (
                <div>
                  <button
                    onClick={() => setStagesExpanded(!stagesExpanded)}
                    className="flex items-center justify-between w-full text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors"
                  >
                    <span className="flex items-center gap-2">
                      訓練階段
                      <span className="text-xs text-gray-500">({trainingOverview.training_stage_discription.length} 個階段)</span>
                    </span>
                    {stagesExpanded ? (
                      <ChevronDown className="w-4 h-4" />
                    ) : (
                      <ChevronRight className="w-4 h-4" />
                    )}
                  </button>

                  {stagesExpanded && (
                    <dd className="space-y-2 mt-2">
                      {trainingOverview.training_stage_discription.map((stage: any, index: number) => (
                        <div key={stage.stage_id || index} className="border border-gray-200 rounded-md p-3">
                          <div className="flex justify-between items-start mb-1">
                            <span className="text-sm font-medium text-gray-900">{stage.stage_name || '未命名階段'}</span>
                            <span className="text-xs text-gray-500">第 {stage.week_start}-{stage.week_end} 週</span>
                          </div>
                          {stage.training_focus && (
                            <div className="text-xs text-blue-600 mb-1">訓練重點: {stage.training_focus}</div>
                          )}
                          {stage.stage_description && (
                            <div className="text-xs text-gray-600">{stage.stage_description}</div>
                          )}
                        </div>
                      ))}
                    </dd>
                  )}
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-gray-400">尚無訓練總覽數據</p>
          )}
        </div>

        {/* 週課表 */}
        <div className="bg-white rounded-lg shadow p-6 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Calendar className="w-5 h-5" />
              週課表
            </h2>
            {user?.active_weekly_plan_id && (
              <button
                onClick={handleViewWeeklyPlanMeta}
                className="flex items-center gap-1 px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors"
              >
                <Eye className="w-4 h-4" />
                查看 Prompt
              </button>
            )}
          </div>
          {weeklyPlan && weeklyPlan.plan ? (
            <div className="space-y-4">
              {/* 週計劃概述 */}
              <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
                  <div>
                    <dt className="text-xs text-gray-600">第幾週</dt>
                    <dd className="text-sm font-medium text-gray-900">第 {weeklyPlan.plan.week_of_plan} / {weeklyPlan.plan.total_weeks} 週</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-gray-600">本週總距離</dt>
                    <dd className="text-sm font-medium text-gray-900">{weeklyPlan.plan.total_distance_km} km</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-gray-600">訓練目標</dt>
                    <dd className="text-sm font-medium text-gray-900">{weeklyPlan.plan.purpose}</dd>
                  </div>
                </div>
                {weeklyPlan.plan.total_distance_reason && (
                  <div className="pt-3 border-t border-gray-300">
                    <dt className="text-xs text-gray-600 mb-1">跑量說明</dt>
                    <dd className="text-xs text-gray-700">{weeklyPlan.plan.total_distance_reason}</dd>
                  </div>
                )}
              </div>

              {/* 每日訓練 */}
              {weeklyPlan.plan.days && weeklyPlan.plan.days.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {weeklyPlan.plan.days.map((day: any, index: number) => (
                    <div key={day.day_index || index} className="border border-gray-200 rounded-md p-3 hover:border-blue-300 transition-colors">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-medium text-gray-500">
                          {['週一', '週二', '週三', '週四', '週五', '週六', '週日'][day.day_index - 1] || `Day ${day.day_index}`}
                        </span>
                        <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-800 rounded">
                          {day.training_type === 'easy_run' && '輕鬆跑'}
                          {day.training_type === 'tempo_run' && '節奏跑'}
                          {day.training_type === 'interval_training' && '間歇訓練'}
                          {day.training_type === 'long_run' && '長距離跑'}
                          {day.training_type === 'recovery_run' && '恢復跑'}
                          {day.training_type === 'rest' && '休息'}
                          {day.training_type === 'combination' && '組合訓練'}
                          {!['easy_run', 'tempo_run', 'interval_training', 'long_run', 'recovery_run', 'rest', 'combination'].includes(day.training_type) && day.training_type}
                        </span>
                      </div>
                      <div className="text-sm font-medium text-gray-900 mb-1">{day.day_target || '-'}</div>

                      {/* 組合訓練 - 展開 segments */}
                      {day.training_type === 'combination' && day.training_details?.segments && (
                        <div className="mt-2 space-y-2">
                          {day.training_details.segments.map((segment: any, segIndex: number) => (
                            <div key={segIndex} className="pl-3 border-l-2 border-blue-200 bg-blue-50 rounded-r py-2 pr-2">
                              <div className="text-xs font-medium text-blue-900 mb-1">
                                {segment.type === 'easy_run' && '輕鬆跑'}
                                {segment.type === 'tempo_run' && '節奏跑'}
                                {segment.type === 'interval_training' && '間歇訓練'}
                                {segment.type === 'long_run' && '長距離跑'}
                                {segment.type === 'recovery_run' && '恢復跑'}
                                {!['easy_run', 'tempo_run', 'interval_training', 'long_run', 'recovery_run'].includes(segment.type) && segment.type}
                              </div>
                              {segment.description && (
                                <div className="text-xs text-blue-800 mb-1">{segment.description}</div>
                              )}
                              <div className="flex gap-3 text-xs text-blue-700">
                                {segment.distance_km && <span>距離: {segment.distance_km} km</span>}
                                {segment.duration_minutes && <span>時間: {segment.duration_minutes} 分鐘</span>}
                                {segment.pace && <span>配速: {segment.pace}</span>}
                              </div>
                              {segment.heart_rate_range && (
                                <div className="text-xs text-blue-700 mt-1">
                                  心率: {segment.heart_rate_range.min}-{segment.heart_rate_range.max} bpm
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}

                      {/* 非組合訓練 - 顯示原有的 training_details */}
                      {day.training_type !== 'combination' && day.training_details && (
                        <div className="space-y-1">
                          {day.training_details.distance_km && (
                            <div className="text-xs text-gray-600">距離: {day.training_details.distance_km} km</div>
                          )}
                          {day.training_details.heart_rate_range && (
                            <div className="text-xs text-gray-600">
                              心率: {day.training_details.heart_rate_range.min}-{day.training_details.heart_rate_range.max} bpm
                            </div>
                          )}
                          {day.training_details.description && (
                            <div className="text-xs text-gray-500 mt-1">{day.training_details.description}</div>
                          )}
                        </div>
                      )}

                      {day.reason && (
                        <div className="text-xs text-gray-400 mt-2 pt-2 border-t border-gray-100">{day.reason}</div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-gray-400">尚無週課表數據</p>
          )}
        </div>

        {/* 週回顧（上週） */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-purple-600" />
              週回顧（上週）
            </h2>
            {user?.active_weekly_plan_id && (
              <button
                onClick={handleViewWeeklySummaryMeta}
                className="flex items-center gap-1 px-3 py-1 text-sm bg-green-100 text-green-700 rounded-md hover:bg-green-200 transition-colors"
              >
                <Eye className="w-4 h-4" />
                查看 Prompt
              </button>
            )}
          </div>
          {weeklySummary ? (
            <div className="space-y-4">
              {/* 調試信息 */}
              {user?.active_weekly_plan_id && (() => {
                const parts = user.active_weekly_plan_id.split('_');
                const currentWeek = parts.length >= 2 ? parseInt(parts[parts.length - 1]) : null;
                const lastWeek = currentWeek ? currentWeek - 1 : null;
                const prefix = parts.slice(0, -1).join('_');
                const summaryId = lastWeek ? `${prefix}_${lastWeek}_summary` : null;

                return (
                  <div className="p-3 bg-gray-50 rounded-md text-xs font-mono">
                    <div className="text-gray-600">Summary ID: <span className="text-gray-800">{summaryId || '無法計算'}</span></div>
                    <div className="text-gray-600">Week Number: <span className="text-gray-800">{lastWeek || '無法計算'}</span></div>
                  </div>
                );
              })()}

              {/* 訓練完成度評估 */}
              {weeklySummary.training_completion?.evaluation && (
                <div className="p-4 bg-purple-50 rounded-md">
                  <h3 className="font-semibold text-purple-900 mb-2">
                    訓練完成度評估
                    {weeklySummary.training_completion?.percentage !== undefined && (
                      <span className="ml-2 px-2 py-0.5 text-xs rounded-full bg-purple-200 text-purple-800">
                        {weeklySummary.training_completion.percentage}%
                      </span>
                    )}
                  </h3>
                  <p className="text-sm text-purple-800 whitespace-pre-wrap">{weeklySummary.training_completion.evaluation}</p>
                </div>
              )}

              {/* 亮點與下週建議 */}
              <div className="grid md:grid-cols-2 gap-4">
                {weeklySummary.weekly_highlights?.highlights && (
                  <div className="p-4 bg-green-50 rounded-md">
                    <h3 className="font-semibold text-green-900 mb-2">本週亮點</h3>
                    <ul className="text-sm text-green-800 space-y-1">
                      {Array.isArray(weeklySummary.weekly_highlights.highlights) ? (
                        weeklySummary.weekly_highlights.highlights.map((highlight: string, index: number) => (
                          <li key={index} className="flex items-start gap-2">
                            <span className="text-green-600">✓</span>
                            <span>{highlight}</span>
                          </li>
                        ))
                      ) : (
                        <li className="whitespace-pre-wrap">{weeklySummary.weekly_highlights.highlights}</li>
                      )}
                    </ul>
                  </div>
                )}
                {weeklySummary.next_week_suggestions && (
                  <div className="p-4 bg-blue-50 rounded-md">
                    <h3 className="font-semibold text-blue-900 mb-2">下週建議</h3>
                    {weeklySummary.next_week_suggestions.focus && (
                      <p className="text-sm text-blue-900 mb-2 font-medium">{weeklySummary.next_week_suggestions.focus}</p>
                    )}
                    {weeklySummary.next_week_suggestions.recommendations && (
                      <ul className="text-sm text-blue-800 space-y-1">
                        {Array.isArray(weeklySummary.next_week_suggestions.recommendations) ? (
                          weeklySummary.next_week_suggestions.recommendations.map((suggestion: string, index: number) => (
                            <li key={index} className="flex items-start gap-2">
                              <span className="text-blue-600">→</span>
                              <span>{suggestion}</span>
                            </li>
                          ))
                        ) : (
                          <li className="whitespace-pre-wrap">{weeklySummary.next_week_suggestions.recommendations}</li>
                        )}
                      </ul>
                    )}
                  </div>
                )}
              </div>

              {/* 創建時間 */}
              {weeklySummary.created_at && (
                <div className="text-xs text-gray-500 text-right">
                  創建於 {formatDate(weeklySummary.created_at)}
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-sm text-gray-400">尚無週回顧數據</p>
              {/* 調試信息 - 顯示為什麼沒有數據 */}
              {user?.active_weekly_plan_id ? (() => {
                const parts = user.active_weekly_plan_id.split('_');
                const currentWeek = parts.length >= 2 ? parseInt(parts[parts.length - 1]) : null;
                const lastWeek = currentWeek ? currentWeek - 1 : null;
                const prefix = parts.slice(0, -1).join('_');
                const summaryId = lastWeek ? `${prefix}_${lastWeek}_summary` : null;

                return (
                  <div className="p-3 bg-yellow-50 rounded-md text-xs">
                    <div className="font-semibold text-yellow-800 mb-2">調試信息：</div>
                    <div className="space-y-1 text-yellow-700">
                      <div>當前週次: <span className="font-mono">{currentWeek || '無法解析'}</span></div>
                      <div>查詢週次: <span className="font-mono">{lastWeek || '無法計算'}</span></div>
                      <div>查詢 Summary ID: <span className="font-mono text-xs break-all">{summaryId || '無法計算'}</span></div>
                      {lastWeek && lastWeek < 1 && (
                        <div className="mt-2 text-red-600 font-semibold">⚠️ 第一週沒有上週回顧</div>
                      )}
                      {!user.active_weekly_plan_id && (
                        <div className="mt-2 text-red-600 font-semibold">⚠️ 沒有 active_weekly_plan_id</div>
                      )}
                    </div>
                  </div>
                );
              })() : (
                <div className="p-3 bg-red-50 rounded-md text-xs">
                  <div className="text-red-800 font-semibold">⚠️ 沒有 active_weekly_plan_id，無法查詢週回顧</div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* 連接狀態 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5" />
            第三方連接
          </h2>
          <div className="space-y-3">
            {/* 主要數據來源 */}
            {user.data_source && (
              <div className="mb-3 pb-3 border-b border-gray-200">
                <div className="text-xs text-gray-500 mb-2">主要數據來源</div>
                <div className="flex items-center gap-2">
                  {user.data_source === 'garmin' && (
                    <span className="px-3 py-1.5 text-sm font-medium rounded-full bg-green-100 text-green-800 border border-green-200">
                      Garmin
                    </span>
                  )}
                  {user.data_source === 'strava' && (
                    <span className="px-3 py-1.5 text-sm font-medium rounded-full bg-orange-100 text-orange-800 border border-orange-200">
                      Strava
                    </span>
                  )}
                  {user.data_source === 'apple_health' && (
                    <span className="px-3 py-1.5 text-sm font-medium rounded-full bg-gray-800 text-white border border-gray-700">
                      Apple Health
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* API 連接狀態 */}
            <div className="text-xs text-gray-500 mb-2">API 連接狀態</div>
            <div className="space-y-2">
              <div className="flex items-center justify-between py-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-700">Garmin</span>
                  {user.data_source === 'garmin' && (
                    <span className="text-xs text-gray-500">(主要來源)</span>
                  )}
                </div>
                <span className={`px-2 py-1 text-xs rounded-full ${user.garmin_tokens ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'}`}>
                  {user.garmin_tokens ? '已連接' : '未連接'}
                </span>
              </div>
              <div className="flex items-center justify-between py-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-700">Strava</span>
                  {user.data_source === 'strava' && (
                    <span className="text-xs text-gray-500">(主要來源)</span>
                  )}
                </div>
                <span className={`px-2 py-1 text-xs rounded-full ${user.strava_tokens ? 'bg-orange-100 text-orange-800' : 'bg-gray-100 text-gray-600'}`}>
                  {user.strava_tokens ? '已連接' : '未連接'}
                </span>
              </div>
              <div className="flex items-center justify-between py-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-700">Apple Health</span>
                  {user.data_source === 'apple_health' && (
                    <span className="text-xs text-gray-500">(主要來源)</span>
                  )}
                </div>
                <span className={`px-2 py-1 text-xs rounded-full ${user.apple_health_last_sync ? 'bg-gray-800 text-white' : 'bg-gray-100 text-gray-600'}`}>
                  {user.apple_health_last_sync ? '已連接' : '未連接'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* 訓練偏好 */}
        <div className="bg-white rounded-lg shadow p-6 lg:col-span-2">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            訓練偏好
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <dt className="text-sm text-gray-600 mb-2">訓練日偏好</dt>
              <dd className="flex flex-wrap gap-1">
                {user.prefer_week_days && user.prefer_week_days.length > 0 ? (
                  [...user.prefer_week_days].sort((a, b) => a - b).map((day: number) => (
                    <span key={day} className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                      {getWeekdayName(day)}
                    </span>
                  ))
                ) : (
                  <span className="text-sm text-gray-400">未設定</span>
                )}
              </dd>
            </div>
            <div>
              <dt className="text-sm text-gray-600 mb-2">長跑日偏好</dt>
              <dd className="flex flex-wrap gap-1">
                {user.prefer_week_days_longrun && user.prefer_week_days_longrun.length > 0 ? (
                  [...user.prefer_week_days_longrun].sort((a, b) => a - b).map((day: number) => (
                    <span key={day} className="px-2 py-1 text-xs bg-purple-100 text-purple-800 rounded">
                      {getWeekdayName(day)}
                    </span>
                  ))
                ) : (
                  <span className="text-sm text-gray-400">未設定</span>
                )}
              </dd>
            </div>
          </div>
        </div>

        {/* 個人最佳 */}
        <div className="bg-white rounded-lg shadow p-6 lg:col-span-2">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Trophy className="w-5 h-5 text-yellow-500" />
            個人最佳記錄
          </h2>
          {user.personal_best && user.personal_best.race_run && user.personal_best.race_run.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">距離</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">配速</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">完成時間</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">創建時間</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">更新時間</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {user.personal_best.race_run.map((race: any, index: number) => (
                    <tr key={race.id || index}>
                      <td className="px-4 py-3 text-sm text-gray-900">
                        {race.distance_km} km
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900">
                        {race.pace}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900">
                        <span className="inline-flex items-center gap-1">
                          <Clock className="w-4 h-4 text-gray-400" />
                          {formatTime(race.complete_time)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-500">
                        {formatDate(race.created_at)}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-500">
                        {formatDate(race.updated_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-sm text-gray-400">尚無個人最佳記錄</p>
          )}
        </div>
        {/* 訓練準備度 */}
        <div className="bg-white rounded-lg shadow p-6 lg:col-span-2">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Heart className="w-5 h-5 text-red-500" />
            訓練準備度
          </h2>
          {readiness ? (
            <div className="space-y-6">
              {/* 當前準備度指標 */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                {/* Speed */}
                {readiness.speed && (
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <div className="text-xs text-gray-600 mb-1">速度</div>
                    <div className="text-2xl font-bold text-blue-900">{readiness.speed.score}</div>
                    {readiness.speed.trend_data?.direction && (
                      <div className={`text-xs mt-1 ${
                        readiness.speed.trend_data.direction === 'up' ? 'text-green-600' :
                        readiness.speed.trend_data.direction === 'down' ? 'text-red-600' : 'text-gray-600'
                      }`}>
                        {readiness.speed.trend_data.direction === 'up' ? '↑' :
                         readiness.speed.trend_data.direction === 'down' ? '↓' : '→'}
                      </div>
                    )}
                  </div>
                )}
                {/* Endurance */}
                {readiness.endurance && (
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <div className="text-xs text-gray-600 mb-1">耐力</div>
                    <div className="text-2xl font-bold text-green-900">{readiness.endurance.score}</div>
                    {readiness.endurance.trend_data?.direction && (
                      <div className={`text-xs mt-1 ${
                        readiness.endurance.trend_data.direction === 'up' ? 'text-green-600' :
                        readiness.endurance.trend_data.direction === 'down' ? 'text-red-600' : 'text-gray-600'
                      }`}>
                        {readiness.endurance.trend_data.direction === 'up' ? '↑' :
                         readiness.endurance.trend_data.direction === 'down' ? '↓' : '→'}
                      </div>
                    )}
                  </div>
                )}
                {/* Race Fitness */}
                {readiness.race_fitness && (
                  <div className="text-center p-4 bg-purple-50 rounded-lg">
                    <div className="text-xs text-gray-600 mb-1">競賽狀態</div>
                    <div className="text-2xl font-bold text-purple-900">{readiness.race_fitness.score}</div>
                    {readiness.race_fitness.trend_data?.direction && (
                      <div className={`text-xs mt-1 ${
                        readiness.race_fitness.trend_data.direction === 'up' ? 'text-green-600' :
                        readiness.race_fitness.trend_data.direction === 'down' ? 'text-red-600' : 'text-gray-600'
                      }`}>
                        {readiness.race_fitness.trend_data.direction === 'up' ? '↑' :
                         readiness.race_fitness.trend_data.direction === 'down' ? '↓' : '→'}
                      </div>
                    )}
                  </div>
                )}
                {/* Training Load */}
                {readiness.training_load && (
                  <div className="text-center p-4 bg-orange-50 rounded-lg">
                    <div className="text-xs text-gray-600 mb-1">訓練負荷</div>
                    <div className="text-2xl font-bold text-orange-900">{readiness.training_load.score}</div>
                    {readiness.training_load.trend_data?.direction && (
                      <div className={`text-xs mt-1 ${
                        readiness.training_load.trend_data.direction === 'up' ? 'text-green-600' :
                        readiness.training_load.trend_data.direction === 'down' ? 'text-red-600' : 'text-gray-600'
                      }`}>
                        {readiness.training_load.trend_data.direction === 'up' ? '↑' :
                         readiness.training_load.trend_data.direction === 'down' ? '↓' : '→'}
                      </div>
                    )}
                  </div>
                )}
                {/* Recovery */}
                {readiness.recovery && (
                  <div className="text-center p-4 bg-pink-50 rounded-lg">
                    <div className="text-xs text-gray-600 mb-1">恢復狀態</div>
                    <div className="text-2xl font-bold text-pink-900">{readiness.recovery.score}</div>
                    {readiness.recovery.trend_data?.direction && (
                      <div className={`text-xs mt-1 ${
                        readiness.recovery.trend_data.direction === 'up' ? 'text-green-600' :
                        readiness.recovery.trend_data.direction === 'down' ? 'text-red-600' : 'text-gray-600'
                      }`}>
                        {readiness.recovery.trend_data.direction === 'up' ? '↑' :
                         readiness.recovery.trend_data.direction === 'down' ? '↓' : '→'}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* 28天趨勢圖表 */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-gray-700">趨勢圖表 (21天)</h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Speed Trend */}
                  {readiness.speed?.trend_data?.values && readiness.speed.trend_data.values.length > 0 && (
                    <div className="border border-gray-200 rounded-lg p-4 bg-white">
                      <div className="text-xs font-medium text-gray-700 mb-2">
                        速度趨勢 <span className="text-gray-400">({readiness.speed.trend_data.values.length}天)</span>
                      </div>
                      <div className="h-32 flex items-end gap-px bg-gray-50 rounded">
                        {readiness.speed.trend_data.values.map((value: number, index: number) => {
                          const allValues = readiness.speed.trend_data.values;
                          const maxValue = Math.max(...allValues);
                          const minValue = Math.min(...allValues);
                          const range = maxValue - minValue;
                          const height = range > 0 ? ((value - minValue) / range) * 100 : 50;
                          return (
                            <div key={index} className="flex-1 flex flex-col justify-end min-w-0">
                              <div
                                className="bg-blue-500 hover:bg-blue-600 transition-colors w-full"
                                style={{ height: `${Math.max(height, 10)}%` }}
                                title={`${readiness.speed.trend_data.dates?.[index]}: ${value.toFixed(1)}`}
                              />
                            </div>
                          );
                        })}
                      </div>
                      <div className="text-xs text-gray-500 mt-2 flex justify-between">
                        <span>{readiness.speed.trend_data.dates?.[0]}</span>
                        <span>{readiness.speed.trend_data.dates?.[readiness.speed.trend_data.dates.length - 1]}</span>
                      </div>
                    </div>
                  )}

                  {/* Endurance Trend */}
                  {readiness.endurance?.trend_data?.values && readiness.endurance.trend_data.values.length > 0 && (
                    <div className="border border-gray-200 rounded-lg p-4 bg-white">
                      <div className="text-xs font-medium text-gray-700 mb-2">
                        耐力趨勢 <span className="text-gray-400">({readiness.endurance.trend_data.values.length}天)</span>
                      </div>
                      <div className="h-32 flex items-end gap-px bg-gray-50 rounded">
                        {readiness.endurance.trend_data.values.map((value: number, index: number) => {
                          const allValues = readiness.endurance.trend_data.values;
                          const maxValue = Math.max(...allValues);
                          const minValue = Math.min(...allValues);
                          const range = maxValue - minValue;
                          const height = range > 0 ? ((value - minValue) / range) * 100 : 50;
                          return (
                            <div key={index} className="flex-1 flex flex-col justify-end min-w-0">
                              <div
                                className="bg-green-500 hover:bg-green-600 transition-colors w-full"
                                style={{ height: `${Math.max(height, 10)}%` }}
                                title={`${readiness.endurance.trend_data.dates?.[index]}: ${value.toFixed(1)}`}
                              />
                            </div>
                          );
                        })}
                      </div>
                      <div className="text-xs text-gray-500 mt-2 flex justify-between">
                        <span>{readiness.endurance.trend_data.dates?.[0]}</span>
                        <span>{readiness.endurance.trend_data.dates?.[readiness.endurance.trend_data.dates.length - 1]}</span>
                      </div>
                    </div>
                  )}

                  {/* Race Fitness Trend */}
                  {readiness.race_fitness?.trend_data?.values && readiness.race_fitness.trend_data.values.length > 0 && (
                    <div className="border border-gray-200 rounded-lg p-4 bg-white">
                      <div className="text-xs font-medium text-gray-700 mb-2">
                        競賽狀態趨勢 <span className="text-gray-400">({readiness.race_fitness.trend_data.values.length}天)</span>
                      </div>
                      <div className="h-32 flex items-end gap-px bg-gray-50 rounded">
                        {readiness.race_fitness.trend_data.values.map((value: number, index: number) => {
                          const allValues = readiness.race_fitness.trend_data.values;
                          const maxValue = Math.max(...allValues);
                          const minValue = Math.min(...allValues);
                          const range = maxValue - minValue;
                          const height = range > 0 ? ((value - minValue) / range) * 100 : 50;
                          return (
                            <div key={index} className="flex-1 flex flex-col justify-end min-w-0">
                              <div
                                className="bg-purple-500 hover:bg-purple-600 transition-colors w-full"
                                style={{ height: `${Math.max(height, 10)}%` }}
                                title={`${readiness.race_fitness.trend_data.dates?.[index]}: ${value.toFixed(1)}`}
                              />
                            </div>
                          );
                        })}
                      </div>
                      <div className="text-xs text-gray-500 mt-2 flex justify-between">
                        <span>{readiness.race_fitness.trend_data.dates?.[0]}</span>
                        <span>{readiness.race_fitness.trend_data.dates?.[readiness.race_fitness.trend_data.dates.length - 1]}</span>
                      </div>
                    </div>
                  )}

                  {/* Training Load Trend */}
                  {readiness.training_load?.trend_data?.values && readiness.training_load.trend_data.values.length > 0 && (
                    <div className="border border-gray-200 rounded-lg p-4 bg-white">
                      <div className="text-xs font-medium text-gray-700 mb-2">
                        訓練負荷趨勢 <span className="text-gray-400">({readiness.training_load.trend_data.values.length}天)</span>
                      </div>
                      <div className="h-32 flex items-end gap-px bg-gray-50 rounded">
                        {readiness.training_load.trend_data.values.map((value: number, index: number) => {
                          const allValues = readiness.training_load.trend_data.values;
                          const maxValue = Math.max(...allValues);
                          const minValue = Math.min(...allValues);
                          const range = maxValue - minValue;
                          const height = range > 0 ? ((value - minValue) / range) * 100 : 50;
                          return (
                            <div key={index} className="flex-1 flex flex-col justify-end min-w-0">
                              <div
                                className="bg-orange-500 hover:bg-orange-600 transition-colors w-full"
                                style={{ height: `${Math.max(height, 10)}%` }}
                                title={`${readiness.training_load.trend_data.dates?.[index]}: ${value.toFixed(1)}`}
                              />
                            </div>
                          );
                        })}
                      </div>
                      <div className="text-xs text-gray-500 mt-2 flex justify-between">
                        <span>{readiness.training_load.trend_data.dates?.[0]}</span>
                        <span>{readiness.training_load.trend_data.dates?.[readiness.training_load.trend_data.dates.length - 1]}</span>
                      </div>
                    </div>
                  )}

                  {/* Recovery Trend */}
                  {readiness.recovery?.trend_data?.values && readiness.recovery.trend_data.values.length > 0 && (
                    <div className="border border-gray-200 rounded-lg p-4 bg-white">
                      <div className="text-xs font-medium text-gray-700 mb-2">
                        恢復狀態趨勢 <span className="text-gray-400">({readiness.recovery.trend_data.values.length}天)</span>
                      </div>
                      <div className="h-32 flex items-end gap-px bg-gray-50 rounded">
                        {readiness.recovery.trend_data.values.map((value: number, index: number) => {
                          const allValues = readiness.recovery.trend_data.values;
                          const maxValue = Math.max(...allValues);
                          const minValue = Math.min(...allValues);
                          const range = maxValue - minValue;
                          const height = range > 0 ? ((value - minValue) / range) * 100 : 50;
                          return (
                            <div key={index} className="flex-1 flex flex-col justify-end min-w-0">
                              <div
                                className="bg-pink-500 hover:bg-pink-600 transition-colors w-full"
                                style={{ height: `${Math.max(height, 10)}%` }}
                                title={`${readiness.recovery.trend_data.dates?.[index]}: ${value.toFixed(1)}`}
                              />
                            </div>
                          );
                        })}
                      </div>
                      <div className="text-xs text-gray-500 mt-2 flex justify-between">
                        <span>{readiness.recovery.trend_data.dates?.[0]}</span>
                        <span>{readiness.recovery.trend_data.dates?.[readiness.recovery.trend_data.dates.length - 1]}</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-sm text-gray-400">尚無訓練準備度數據</div>
          )}
        </div>
        {/* 訂閱測試工具 */}
        <div className="mt-6">
          <SubscriptionTools uid={user.uid} onSuccess={fetchUser} />
        </div>

      </div>

      {/* LLM Meta Modal */}
      <LLMMetaModal
        isOpen={llmMetaModal.isOpen}
        onClose={handleCloseLLMMetaModal}
        type={llmMetaModal.type || 'weekly-plan'}
        data={llmMetaModal.data}
      />
    </div>
  );
}
