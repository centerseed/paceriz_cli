/**
 * Apple IAP Mock 測試頁面
 *
 * 提供開發環境下的 IAP 購買流程測試功能：
 * - 設置不同的 Mock 模式（成功/過期/無效等）
 * - 測試驗證購買
 * - 測試恢復購買
 * - 測試 Webhook 通知
 * - 查看審計日誌
 */

import { useState, useEffect } from 'react';
import { iapTestApi, subscriptionToolsApi } from '../services/api';
import {
  Smartphone,
  CheckCircle,
  XCircle,
  RefreshCw,
  Webhook,
  FileText,
  Trash2,
  AlertCircle,
  Settings,
  PlayCircle,
} from 'lucide-react';

type MockMode = 'success' | 'expired' | 'invalid' | 'malformed' | 'server_error';
type WebhookType = 'refund' | 'renew' | 'fail_to_renew';

interface AuditLog {
  operation: string;
  success: boolean;
  timestamp: string;
  details?: any;
}

export default function IAPTestPage() {
  // State
  const [currentMode, setCurrentMode] = useState<MockMode>('success');
  const [testUid, setTestUid] = useState('test_user_001');
  const [platform, setPlatform] = useState('apple');
  const [purchaseToken, setPurchaseToken] = useState('test_receipt');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [subscriptionStatus, setSubscriptionStatus] = useState<any>(null);

  // 自動加載審計日誌
  useEffect(() => {
    loadAuditLogs();
  }, []);

  // 加載審計日誌
  const loadAuditLogs = async () => {
    try {
      const response = await iapTestApi.getAuditLog();
      if (response.success) {
        setAuditLogs(response.data.logs || []);
      }
    } catch (err: any) {
      console.error('Failed to load audit logs:', err);
    }
  };

  // 設置 Mock 模式
  const handleSetMode = async (mode: MockMode) => {
    try {
      setLoading(true);
      setError(null);
      const response = await iapTestApi.setMockMode(mode);
      if (response.success) {
        setCurrentMode(mode);
        setResult({ message: response.message, mode: response.data.mode });
      } else {
        setError(response.error || 'Failed to set mode');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || err.message);
    } finally {
      setLoading(false);
    }
  };

  // 測試驗證購買
  const handleTestVerify = async () => {
    try {
      setLoading(true);
      setError(null);
      setResult(null);

      const response = await iapTestApi.testVerify({
        uid: testUid,
        platform,
        purchase_token: purchaseToken,
      });

      if (response.success) {
        setResult(response.data);
        setSubscriptionStatus(response.data.subscription_status);
        await loadAuditLogs();
      } else {
        setError(response.error || 'Verification failed');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || err.message);
    } finally {
      setLoading(false);
    }
  };

  // 測試恢復購買
  const handleTestRestore = async () => {
    try {
      setLoading(true);
      setError(null);
      setResult(null);

      const response = await iapTestApi.testRestore({
        uid: testUid,
        platform,
        purchase_token: 'restore_receipt',
      });

      if (response.success) {
        setResult(response.data);
        setSubscriptionStatus(response.data.subscription_status);
        await loadAuditLogs();
      } else {
        setError(response.error || 'Restore failed');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || err.message);
    } finally {
      setLoading(false);
    }
  };

  // 測試 Webhook
  const handleTestWebhook = async (webhookType: WebhookType) => {
    try {
      setLoading(true);
      setError(null);
      setResult(null);

      const response = await iapTestApi.testWebhook(webhookType);

      if (response.success) {
        setResult(response.data);
        await loadAuditLogs();
      } else {
        setError(response.error || 'Webhook test failed');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || err.message);
    } finally {
      setLoading(false);
    }
  };

  // 清除審計日誌
  const handleClearLogs = async () => {
    try {
      setLoading(true);
      const response = await iapTestApi.clearAuditLog();
      if (response.success) {
        setAuditLogs([]);
        setResult({ message: 'Audit log cleared' });
      }
    } catch (err: any) {
      setError(err.response?.data?.error || err.message);
    } finally {
      setLoading(false);
    }
  };

  // 查詢訂閱狀態
  const handleCheckSubscription = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await subscriptionToolsApi.check(testUid);
      if (response.success) {
        setSubscriptionStatus(response.data.summary);
        setResult({ message: 'Subscription status loaded', summary: response.data.summary });
      } else {
        setError(response.error || 'Failed to check subscription');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || err.message);
    } finally {
      setLoading(false);
    }
  };

  // 渲染 Mock 模式選擇
  const renderModeSelector = () => {
    const modes: { value: MockMode; label: string; description: string; color: string }[] = [
      { value: 'success', label: '成功', description: '驗證成功，返回有效訂閱', color: 'green' },
      { value: 'expired', label: '過期', description: '收據已過期', color: 'yellow' },
      { value: 'invalid', label: '無效', description: '無效收據', color: 'red' },
      { value: 'malformed', label: '格式錯誤', description: '格式錯誤的收據', color: 'orange' },
      { value: 'server_error', label: '服務器錯誤', description: '模擬 Apple 服務器錯誤', color: 'purple' },
    ];

    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center gap-2 mb-4">
          <Settings className="w-5 h-5 text-blue-600" />
          <h2 className="text-lg font-semibold">Mock 模式設置</h2>
        </div>
        <p className="text-sm text-gray-600 mb-4">選擇不同的模式來測試各種購買場景</p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {modes.map((mode) => (
            <button
              key={mode.value}
              onClick={() => handleSetMode(mode.value)}
              disabled={loading}
              className={`p-4 rounded-lg border-2 transition-all ${
                currentMode === mode.value
                  ? `border-${mode.color}-500 bg-${mode.color}-50`
                  : 'border-gray-200 hover:border-gray-300'
              } disabled:opacity-50`}
            >
              <div className="font-semibold text-sm mb-1">{mode.label}</div>
              <div className="text-xs text-gray-600">{mode.description}</div>
            </button>
          ))}
        </div>

        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-blue-600 mt-0.5" />
          <div className="text-sm text-blue-800">
            當前模式: <span className="font-semibold">{currentMode}</span>
          </div>
        </div>
      </div>
    );
  };

  // 渲染測試操作
  const renderTestActions = () => {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center gap-2 mb-4">
          <PlayCircle className="w-5 h-5 text-green-600" />
          <h2 className="text-lg font-semibold">測試操作</h2>
        </div>

        {/* 測試參數 */}
        <div className="space-y-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">用戶 UID</label>
            <input
              type="text"
              value={testUid}
              onChange={(e) => setTestUid(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="test_user_001"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">平台</label>
            <select
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="apple">Apple</option>
              <option value="ios">iOS</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">購買憑證</label>
            <input
              type="text"
              value={purchaseToken}
              onChange={(e) => setPurchaseToken(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="test_receipt"
            />
          </div>
        </div>

        {/* 測試按鈕 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <button
            onClick={handleTestVerify}
            disabled={loading}
            className="flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            <Smartphone className="w-4 h-4" />
            驗證購買
          </button>

          <button
            onClick={handleTestRestore}
            disabled={loading}
            className="flex items-center justify-center gap-2 px-4 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors disabled:opacity-50"
          >
            <RefreshCw className="w-4 h-4" />
            恢復購買
          </button>

          <button
            onClick={() => handleTestWebhook('refund')}
            disabled={loading}
            className="flex items-center justify-center gap-2 px-4 py-3 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors disabled:opacity-50"
          >
            <Webhook className="w-4 h-4" />
            退款 Webhook
          </button>

          <button
            onClick={() => handleTestWebhook('renew')}
            disabled={loading}
            className="flex items-center justify-center gap-2 px-4 py-3 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors disabled:opacity-50"
          >
            <Webhook className="w-4 h-4" />
            續訂 Webhook
          </button>

          <button
            onClick={() => handleTestWebhook('fail_to_renew')}
            disabled={loading}
            className="flex items-center justify-center gap-2 px-4 py-3 bg-orange-600 text-white rounded-md hover:bg-orange-700 transition-colors disabled:opacity-50"
          >
            <Webhook className="w-4 h-4" />
            續訂失敗 Webhook
          </button>

          <button
            onClick={handleCheckSubscription}
            disabled={loading}
            className="flex items-center justify-center gap-2 px-4 py-3 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors disabled:opacity-50"
          >
            <FileText className="w-4 h-4" />
            查詢訂閱狀態
          </button>
        </div>
      </div>
    );
  };

  // 渲染結果顯示
  const renderResult = () => {
    if (!result && !error) return null;

    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">測試結果</h2>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md flex items-start gap-2">
            <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <div className="font-semibold text-red-800">錯誤</div>
              <div className="text-sm text-red-700">{error}</div>
            </div>
          </div>
        )}

        {result && (
          <div className="space-y-4">
            {result.verification && (
              <div className={`p-4 rounded-md border ${result.verification.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                <div className="flex items-start gap-2 mb-2">
                  {result.verification.success ? (
                    <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
                  )}
                  <div className="font-semibold">
                    {result.verification.success ? '驗證成功' : '驗證失敗'}
                  </div>
                </div>
                {result.verification.error && (
                  <div className="text-sm text-red-700 ml-7">{result.verification.error}</div>
                )}
                {result.verification.subscription_info && (
                  <pre className="mt-2 text-xs bg-white p-2 rounded border overflow-auto">
                    {JSON.stringify(result.verification.subscription_info, null, 2)}
                  </pre>
                )}
              </div>
            )}

            {result.restore && (
              <div className={`p-4 rounded-md border ${result.restore.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                <div className="flex items-start gap-2 mb-2">
                  {result.restore.success ? (
                    <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
                  )}
                  <div className="font-semibold">
                    {result.restore.success ? '恢復成功' : '恢復失敗'}
                  </div>
                </div>
                {result.restore.error && (
                  <div className="text-sm text-red-700 ml-7">{result.restore.error}</div>
                )}
              </div>
            )}

            {result.message && !result.verification && !result.restore && (
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-md">
                <div className="text-sm text-blue-800">{result.message}</div>
              </div>
            )}

            {result.webhook_processed !== undefined && (
              <div className="p-4 bg-purple-50 border border-purple-200 rounded-md">
                <div className="font-semibold text-purple-800 mb-2">
                  Webhook 處理: {result.webhook_processed ? '成功' : '失敗'}
                </div>
                <div className="text-xs text-purple-700">類型: {result.webhook_type}</div>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  // 渲染訂閱狀態
  const renderSubscriptionStatus = () => {
    if (!subscriptionStatus) return null;

    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">當前訂閱狀態</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div>
            <div className="text-xs text-gray-600 mb-1">狀態</div>
            <div className="font-semibold">{subscriptionStatus.status || 'N/A'}</div>
          </div>
          <div>
            <div className="text-xs text-gray-600 mb-1">商品 ID</div>
            <div className="text-sm">{subscriptionStatus.product_id || 'N/A'}</div>
          </div>
          <div>
            <div className="text-xs text-gray-600 mb-1">平台</div>
            <div className="text-sm">{subscriptionStatus.payment_method || 'N/A'}</div>
          </div>
          <div>
            <div className="text-xs text-gray-600 mb-1">到期時間</div>
            <div className="text-sm">{subscriptionStatus.premium_end_at || 'N/A'}</div>
          </div>
          <div>
            <div className="text-xs text-gray-600 mb-1">自動續訂</div>
            <div className="text-sm">{subscriptionStatus.auto_renew ? '是' : '否'}</div>
          </div>
          <div>
            <div className="text-xs text-gray-600 mb-1">試用期</div>
            <div className="text-sm">{subscriptionStatus.is_trial_period ? '是' : '否'}</div>
          </div>
        </div>
      </div>
    );
  };

  // 渲染審計日誌
  const renderAuditLogs = () => {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-gray-600" />
            <h2 className="text-lg font-semibold">審計日誌</h2>
            <span className="px-2 py-1 bg-gray-100 rounded text-xs">{auditLogs.length} 條記錄</span>
          </div>
          <button
            onClick={handleClearLogs}
            disabled={loading || auditLogs.length === 0}
            className="flex items-center gap-1 px-3 py-1.5 text-sm bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors disabled:opacity-50"
          >
            <Trash2 className="w-4 h-4" />
            清除日誌
          </button>
        </div>

        {auditLogs.length === 0 ? (
          <div className="text-center py-8 text-gray-500">暫無日誌記錄</div>
        ) : (
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {auditLogs.map((log, index) => (
              <div key={index} className="p-3 bg-gray-50 rounded-md border border-gray-200">
                <div className="flex items-start justify-between mb-1">
                  <div className="flex items-center gap-2">
                    {log.success ? (
                      <CheckCircle className="w-4 h-4 text-green-600" />
                    ) : (
                      <XCircle className="w-4 h-4 text-red-600" />
                    )}
                    <span className="font-semibold text-sm">{log.operation}</span>
                  </div>
                  <span className="text-xs text-gray-500">{log.timestamp}</span>
                </div>
                {log.details && (
                  <pre className="text-xs bg-white p-2 rounded border border-gray-200 mt-2 overflow-auto">
                    {JSON.stringify(log.details, null, 2)}
                  </pre>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg shadow-lg p-6 text-white">
        <div className="flex items-center gap-3 mb-2">
          <Smartphone className="w-8 h-8" />
          <h1 className="text-2xl font-bold">Apple IAP Mock 測試</h1>
        </div>
        <p className="text-blue-100">測試 Apple In-App Purchase 購買流程（開發環境）</p>
      </div>

      {/* 環境提示 */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 flex items-start gap-2">
        <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-yellow-800">
          <div className="font-semibold mb-1">僅開發環境可用</div>
          <div>此功能僅在開發環境下啟用，用於測試 IAP 購買流程。生產環境將使用真實的 Apple 驗證。</div>
        </div>
      </div>

      {/* Mock 模式選擇器 */}
      {renderModeSelector()}

      {/* 測試操作 */}
      {renderTestActions()}

      {/* 測試結果 */}
      {renderResult()}

      {/* 訂閱狀態 */}
      {renderSubscriptionStatus()}

      {/* 審計日誌 */}
      {renderAuditLogs()}
    </div>
  );
}
