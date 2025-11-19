/**
 * 訂閱測試工具組件
 *
 * 提供開發環境下的訂閱管理功能
 */
import { useState } from 'react';
import { subscriptionToolsApi } from '../services/api';
import {
  PlayCircle, Shield, ShieldOff, Clock, CheckCircle,
  AlertTriangle, Info, Loader2
} from 'lucide-react';

interface SubscriptionToolsProps {
  uid: string;
  onSuccess?: () => void;
}

export default function SubscriptionTools({ uid, onSuccess }: SubscriptionToolsProps) {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);
  const [subscriptionStatus, setSubscriptionStatus] = useState<any>(null);

  // 表單狀態
  const [trialDays, setTrialDays] = useState(14);
  const [extendDays, setExtendDays] = useState(7);
  const [extendReason, setExtendReason] = useState('admin');
  const [whitelistReason, setWhitelistReason] = useState('test_account');
  const [notes, setNotes] = useState('');

  const showMessage = (type: 'success' | 'error' | 'info', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 5000);
  };

  const handleStartTrial = async () => {
    setLoading(true);
    try {
      const result = await subscriptionToolsApi.startTrial({ uid, trial_days: trialDays });
      showMessage('success', result.message);
      onSuccess?.();
    } catch (error: any) {
      showMessage('error', error.response?.data?.error || '操作失敗');
    } finally {
      setLoading(false);
    }
  };

  const handleAddWhitelist = async () => {
    setLoading(true);
    try {
      const result = await subscriptionToolsApi.addWhitelist({
        uid,
        reason: whitelistReason,
        granted_by: 'admin'
      });
      showMessage('success', result.message);
      onSuccess?.();
    } catch (error: any) {
      showMessage('error', error.response?.data?.error || '操作失敗');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveWhitelist = async () => {
    if (!confirm('確定要將用戶移出白名單嗎？')) return;

    setLoading(true);
    try {
      const result = await subscriptionToolsApi.removeWhitelist({ uid });
      showMessage('success', result.message);
      onSuccess?.();
    } catch (error: any) {
      showMessage('error', error.response?.data?.error || '操作失敗');
    } finally {
      setLoading(false);
    }
  };

  const handleExtend = async () => {
    setLoading(true);
    try {
      const result = await subscriptionToolsApi.extend({
        uid,
        days: extendDays,
        reason: extendReason,
        granted_by: 'admin',
        notes: notes || undefined
      });
      showMessage('success', result.message);
      setNotes('');
      onSuccess?.();
    } catch (error: any) {
      showMessage('error', error.response?.data?.error || '操作失敗');
    } finally {
      setLoading(false);
    }
  };

  const handleCheckStatus = async () => {
    setLoading(true);
    try {
      const result = await subscriptionToolsApi.check(uid);
      setSubscriptionStatus(result.data);
      showMessage('info', '訂閱狀態已更新');
    } catch (error: any) {
      showMessage('error', error.response?.data?.error || '獲取狀態失敗');
    } finally {
      setLoading(false);
    }
  };

  const handleTestAutoTrial = async () => {
    if (!confirm('確定要測試自動試用功能嗎？此操作僅對沒有訂閱記錄的用戶有效。')) return;

    setLoading(true);
    try {
      const result = await subscriptionToolsApi.testAutoTrial({ uid });
      showMessage('success', result.message);
      onSuccess?.();
    } catch (error: any) {
      showMessage('error', error.response?.data?.error || '操作失敗');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-gray-900">訂閱測試工具</h2>
        <button
          onClick={handleCheckStatus}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Info className="w-4 h-4" />}
          檢查狀態
        </button>
      </div>

      {/* 消息提示 */}
      {message && (
        <div className={`mb-4 p-4 rounded-md flex items-center gap-2 ${
          message.type === 'success' ? 'bg-green-50 text-green-800' :
          message.type === 'error' ? 'bg-red-50 text-red-800' :
          'bg-blue-50 text-blue-800'
        }`}>
          {message.type === 'success' && <CheckCircle className="w-5 h-5" />}
          {message.type === 'error' && <AlertTriangle className="w-5 h-5" />}
          {message.type === 'info' && <Info className="w-5 h-5" />}
          <span>{message.text}</span>
        </div>
      )}

      {/* 訂閱狀態顯示 */}
      {subscriptionStatus && (
        <div className="mb-6 p-4 bg-gray-50 rounded-md">
          <h3 className="font-semibold mb-3">當前訂閱狀態</h3>
          <dl className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="text-gray-600">狀態</dt>
              <dd className="font-semibold">{subscriptionStatus.summary?.status || 'N/A'}</dd>
            </div>
            <div>
              <dt className="text-gray-600">付費功能訪問</dt>
              <dd className={subscriptionStatus.has_premium_access ? 'text-green-600 font-semibold' : 'text-red-600 font-semibold'}>
                {subscriptionStatus.has_premium_access ? '✅ 有權限' : '❌ 無權限'}
              </dd>
            </div>
            <div>
              <dt className="text-gray-600">白名單</dt>
              <dd className={subscriptionStatus.is_whitelisted ? 'text-green-600 font-semibold' : 'text-gray-600'}>
                {subscriptionStatus.is_whitelisted ? '✅ 是' : '❌ 否'}
              </dd>
            </div>
            {subscriptionStatus.summary?.trial_end && (
              <div>
                <dt className="text-gray-600">試用結束</dt>
                <dd className="font-semibold">{subscriptionStatus.summary.trial_end}</dd>
              </div>
            )}
          </dl>
        </div>
      )}

      {/* 操作按鈕區 */}
      <div className="space-y-6">
        {/* 開始試用 */}
        <div className="border border-gray-200 rounded-md p-4">
          <div className="flex items-center gap-2 mb-3">
            <PlayCircle className="w-5 h-5 text-blue-600" />
            <h3 className="font-semibold">開始試用期</h3>
          </div>
          <div className="flex items-center gap-3">
            <input
              type="number"
              value={trialDays}
              onChange={(e) => setTrialDays(Number(e.target.value))}
              min="1"
              max="365"
              className="w-24 px-3 py-2 border border-gray-300 rounded-md"
            />
            <span className="text-gray-600">天</span>
            <button
              onClick={handleStartTrial}
              disabled={loading}
              className="ml-auto px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400"
            >
              開始試用
            </button>
          </div>
        </div>

        {/* 白名單管理 */}
        <div className="border border-gray-200 rounded-md p-4">
          <div className="flex items-center gap-2 mb-3">
            <Shield className="w-5 h-5 text-green-600" />
            <h3 className="font-semibold">白名單管理</h3>
          </div>
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <select
                value={whitelistReason}
                onChange={(e) => setWhitelistReason(e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="test_account">測試帳號</option>
                <option value="internal_employee">內部員工</option>
                <option value="vip_user">VIP 用戶</option>
                <option value="beta_tester">Beta 測試者</option>
                <option value="compensation">補償</option>
              </select>
              <button
                onClick={handleAddWhitelist}
                disabled={loading}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400"
              >
                加入白名單
              </button>
            </div>
            <button
              onClick={handleRemoveWhitelist}
              disabled={loading}
              className="w-full px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:bg-gray-400 flex items-center justify-center gap-2"
            >
              <ShieldOff className="w-4 h-4" />
              移出白名單
            </button>
          </div>
        </div>

        {/* 延長訂閱 */}
        <div className="border border-gray-200 rounded-md p-4">
          <div className="flex items-center gap-2 mb-3">
            <Clock className="w-5 h-5 text-purple-600" />
            <h3 className="font-semibold">延長訂閱</h3>
          </div>
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <input
                type="number"
                value={extendDays}
                onChange={(e) => setExtendDays(Number(e.target.value))}
                min="1"
                max="365"
                className="w-24 px-3 py-2 border border-gray-300 rounded-md"
              />
              <span className="text-gray-600">天</span>
              <select
                value={extendReason}
                onChange={(e) => setExtendReason(e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="admin">管理員贈送</option>
                <option value="referral">推薦獎勵</option>
                <option value="promotion">促銷活動</option>
                <option value="compensation">補償</option>
                <option value="other">其他</option>
              </select>
            </div>
            <input
              type="text"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="備註（可選）"
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
            <button
              onClick={handleExtend}
              disabled={loading}
              className="w-full px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:bg-gray-400"
            >
              延長訂閱
            </button>
          </div>
        </div>

        {/* 測試自動試用 */}
        <div className="border border-gray-200 rounded-md p-4">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="w-5 h-5 text-orange-600" />
            <h3 className="font-semibold">測試自動試用</h3>
          </div>
          <p className="text-sm text-gray-600 mb-3">
            僅對沒有訂閱記錄的新用戶有效
          </p>
          <button
            onClick={handleTestAutoTrial}
            disabled={loading}
            className="w-full px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 disabled:bg-gray-400"
          >
            測試自動試用
          </button>
        </div>
      </div>
    </div>
  );
}
