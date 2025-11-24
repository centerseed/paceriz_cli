/**
 * API Service
 *
 * 與 Admin Backend API 通信
 * 支援運行時環境切換
 */
import axios, { AxiosInstance } from 'axios';
import { auth } from '../config/firebase';
import { getCurrentConfig } from '../config/environments';

// 獲取當前環境的 API Base URL
const currentConfig = getCurrentConfig();
const API_BASE_URL = currentConfig.apiBaseUrl;

console.log(`🌐 API Base URL: ${API_BASE_URL}`);

// 創建 axios 實例
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - 自動添加 Firebase token
apiClient.interceptors.request.use(
  async (config) => {
    const user = auth.currentUser;
    if (user) {
      try {
        const token = await user.getIdToken();
        config.headers['Authorization'] = `Bearer ${token}`;
      } catch (error) {
        console.error('Failed to get ID token:', error);
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - 處理錯誤
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.error('Unauthorized - redirecting to login');
      // 可以在這裡添加自動跳轉到登入頁的邏輯
    }
    return Promise.reject(error);
  }
);

// 設置認證 token（保留向後兼容，但現在使用 interceptor 自動處理）
export function setAuthToken(token: string | null) {
  if (token) {
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete apiClient.defaults.headers.common['Authorization'];
  }
}

// 訂閱相關 API
export const subscriptionApi = {
  // 獲取訂閱列表
  list: async (params?: { page?: number; limit?: number; status?: string }) => {
    const response = await apiClient.get('/api/v1/admin/subscriptions', { params });
    return response.data;
  },

  // 獲取訂閱詳情
  get: async (uid: string) => {
    const response = await apiClient.get(`/api/v1/admin/subscriptions/${uid}`);
    return response.data;
  },

  // 延長訂閱
  extend: async (uid: string, days: number, reason: string) => {
    const response = await apiClient.post(`/api/v1/admin/subscriptions/${uid}/extend`, {
      days,
      reason,
    });
    return response.data;
  },

  // 取消訂閱
  cancel: async (uid: string, reason: string) => {
    const response = await apiClient.post(`/api/v1/admin/subscriptions/${uid}/cancel`, {
      reason,
    });
    return response.data;
  },
};

// 邀請碼相關 API
export const inviteCodeApi = {
  // 獲取邀請碼列表
  list: async (params?: { page?: number; limit?: number; status?: string; search?: string }) => {
    const response = await apiClient.get('/api/v1/admin/invite-codes', { params });
    return response.data;
  },

  // 獲取邀請碼詳情
  get: async (code: string) => {
    const response = await apiClient.get(`/api/v1/admin/invite-codes/${code}`);
    return response.data;
  },

  // 獲取邀請碼使用記錄
  getUsages: async (code: string, params?: { page?: number; limit?: number }) => {
    const response = await apiClient.get(`/api/v1/admin/invite-codes/${code}/usages`, { params });
    return response.data;
  },

  // 禁用邀請碼
  disable: async (code: string) => {
    const response = await apiClient.post(`/api/v1/admin/invite-codes/${code}/disable`);
    return response.data;
  },

  // 獲取邀請碼統計
  getStats: async () => {
    const response = await apiClient.get('/api/v1/admin/invite-codes/stats');
    return response.data;
  },
};

// 數據分析相關 API
export const analyticsApi = {
  // 獲取總覽統計
  getOverview: async () => {
    const response = await apiClient.get('/api/v1/admin/analytics/overview');
    return response.data;
  },

  // 獲取收入統計
  getRevenue: async () => {
    const response = await apiClient.get('/api/v1/admin/analytics/revenue');
    return response.data;
  },

  // 獲取留存分析
  getRetention: async () => {
    const response = await apiClient.get('/api/v1/admin/analytics/retention');
    return response.data;
  },

  // 獲取趨勢數據
  getTrends: async (days: number = 30) => {
    const response = await apiClient.get('/api/v1/admin/analytics/trends', {
      params: { days },
    });
    return response.data;
  },
};

// 管理員管理相關 API
export const adminsApi = {
  // 獲取管理員列表
  list: async (params?: { page?: number; limit?: number; role?: string }) => {
    const response = await apiClient.get('/api/v1/admin/admins', { params });
    return response.data;
  },

  // 授予管理員權限
  grant: async (uid: string, reason?: string) => {
    const response = await apiClient.post(`/api/v1/admin/admins/${uid}/grant`, { reason });
    return response.data;
  },

  // 撤銷管理員權限
  revoke: async (uid: string, reason?: string) => {
    const response = await apiClient.post(`/api/v1/admin/admins/${uid}/revoke`, { reason });
    return response.data;
  },

  // 獲取審計日誌
  getAuditLogs: async (params?: { limit?: number; action?: string }) => {
    const response = await apiClient.get('/api/v1/admin/admins/audit-logs', { params });
    return response.data;
  },
};

// 用戶管理相關 API
export const usersApi = {
  // 獲取用戶列表
  list: async (params?: { page?: number; limit?: number; search?: string }) => {
    const response = await apiClient.get('/api/v1/admin/users', { params });
    return response.data;
  },

  // 獲取用戶詳情
  get: async (uid: string) => {
    const response = await apiClient.get(`/api/v1/admin/users/${uid}`);
    return response.data;
  },

  // 獲取用戶訓練總覽
  getTrainingOverview: async (uid: string) => {
    const response = await apiClient.get(`/api/v1/admin/users/${uid}/training-overview`);
    return response.data;
  },

  // 獲取用戶週課表
  getWeeklyPlan: async (uid: string) => {
    const response = await apiClient.get(`/api/v1/admin/users/${uid}/weekly-plan`);
    return response.data;
  },

  // 獲取用戶週回顧（上週）
  getWeeklySummary: async (uid: string) => {
    const response = await apiClient.get(`/api/v1/admin/users/${uid}/weekly-summary`);
    return response.data;
  },
};

// 訂閱測試工具相關 API
export const subscriptionToolsApi = {
  // 開始試用期
  startTrial: async (data: { uid: string; trial_days?: number }) => {
    const response = await apiClient.post('/api/v1/admin/subscription-tools/start-trial', data);
    return response.data;
  },

  // 加入白名單
  addWhitelist: async (data: { uid: string; reason?: string; granted_by?: string }) => {
    const response = await apiClient.post('/api/v1/admin/subscription-tools/add-whitelist', data);
    return response.data;
  },

  // 移出白名單
  removeWhitelist: async (data: { uid: string }) => {
    const response = await apiClient.post('/api/v1/admin/subscription-tools/remove-whitelist', data);
    return response.data;
  },

  // 延長訂閱
  extend: async (data: {
    uid: string;
    days: number;
    reason?: string;
    granted_by?: string;
    notes?: string;
  }) => {
    const response = await apiClient.post('/api/v1/admin/subscription-tools/extend', data);
    return response.data;
  },

  // 檢查訂閱狀態
  check: async (uid: string) => {
    const response = await apiClient.get(`/api/v1/admin/subscription-tools/check/${uid}`);
    return response.data;
  },

  // 測試自動試用
  testAutoTrial: async (data: { uid: string }) => {
    const response = await apiClient.post('/api/v1/admin/subscription-tools/test-auto-trial', data);
    return response.data;
  },
};

// LLM 元數據相關 API
export const llmMetaApi = {
  // 獲取週課表的 LLM 元數據
  getWeeklyPlanMeta: async (weeklyPlanId: string) => {
    const response = await apiClient.get(`/api/v1/admin/llm-meta/weekly-plans/${weeklyPlanId}/llm-meta`);
    return response.data;
  },

  // 獲取週回顧的 LLM 元數據
  getWeeklySummaryMeta: async (summaryId: string) => {
    const response = await apiClient.get(`/api/v1/admin/llm-meta/weekly-summaries/${summaryId}/llm-meta`);
    return response.data;
  },
};

// Workout 訓練記錄相關 API
export const workoutApi = {
  // 獲取用戶的訓練記錄索引列表
  getWorkoutIndex: async (uid: string, params?: {
    limit?: number;
    startDate?: string;
    endDate?: string;
    provider?: string;
  }) => {
    const response = await apiClient.get(`/api/v1/admin/users/${uid}/workouts/index`, { params });
    return response.data;
  },

  // 獲取特定訓練的詳細數據
  getWorkoutDetail: async (uid: string, provider: string, activityId: string) => {
    const response = await apiClient.get(`/api/v1/admin/users/${uid}/workouts/${provider}/${activityId}`);
    return response.data;
  },
};

// Apple IAP 測試相關 API
export const iapTestApi = {
  // 設置 Mock 模式
  setMockMode: async (mode: 'success' | 'expired' | 'invalid' | 'malformed' | 'server_error') => {
    const response = await apiClient.post('/api/v1/admin/subscription-tools/iap/set-mock-mode', { mode });
    return response.data;
  },

  // 測試驗證購買
  testVerify: async (data: { uid: string; platform?: string; purchase_token?: string }) => {
    const response = await apiClient.post('/api/v1/admin/subscription-tools/iap/test-verify', data);
    return response.data;
  },

  // 測試恢復購買
  testRestore: async (data: { uid: string; platform?: string; purchase_token?: string }) => {
    const response = await apiClient.post('/api/v1/admin/subscription-tools/iap/test-restore', data);
    return response.data;
  },

  // 測試 Webhook
  testWebhook: async (webhookType: 'refund' | 'renew' | 'fail_to_renew') => {
    const response = await apiClient.post('/api/v1/admin/subscription-tools/iap/test-webhook', {
      webhook_type: webhookType,
    });
    return response.data;
  },

  // 獲取審計日誌
  getAuditLog: async () => {
    const response = await apiClient.get('/api/v1/admin/subscription-tools/iap/audit-log');
    return response.data;
  },

  // 清除審計日誌
  clearAuditLog: async () => {
    const response = await apiClient.post('/api/v1/admin/subscription-tools/iap/clear-audit-log');
    return response.data;
  },
};

export default apiClient;
