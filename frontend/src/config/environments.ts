/**
 * 環境配置
 * 支援運行時動態切換環境
 *
 * ⚠️ Firebase 配置來自環境變數，不應硬編碼
 * 詳見 .env.example
 */

export interface EnvironmentConfig {
  name: string;
  apiBaseUrl: string;
  firebase: {
    apiKey: string;
    authDomain: string;
    projectId: string;
    storageBucket: string;
    messagingSenderId: string;
    appId: string;
    measurementId: string;
  };
}

// 從環境變數讀取 Firebase 配置
const loadFirebaseConfig = (prefix: string) => {
  const getEnv = (key: string): string => {
    const value = import.meta.env[`VITE_FIREBASE_${prefix}_${key}`];
    if (!value) {
      console.warn(`⚠️  Missing environment variable: VITE_FIREBASE_${prefix}_${key}`);
    }
    return value || '';
  };

  return {
    apiKey: getEnv('API_KEY'),
    authDomain: getEnv('AUTH_DOMAIN'),
    projectId: getEnv('PROJECT_ID'),
    storageBucket: getEnv('STORAGE_BUCKET'),
    messagingSenderId: getEnv('MESSAGING_SENDER_ID'),
    appId: getEnv('APP_ID'),
    measurementId: getEnv('MEASUREMENT_ID'),
  };
};

export const environments: Record<string, EnvironmentConfig> = {
  dev: {
    name: 'Development',
    apiBaseUrl: import.meta.env.VITE_API_BASE_URL_DEV || 'http://localhost:8080',
    firebase: loadFirebaseConfig('DEV'),
  },
  prod: {
    name: 'Production',
    apiBaseUrl: import.meta.env.VITE_API_BASE_URL_PROD || 'http://localhost:8081',
    firebase: loadFirebaseConfig('PROD'),
  },
};

// 從 localStorage 獲取當前環境，默認為 dev
export const getCurrentEnvironment = (): string => {
  return localStorage.getItem('currentEnvironment') || 'dev';
};

// 設置當前環境
export const setCurrentEnvironment = (env: string): void => {
  localStorage.setItem('currentEnvironment', env);
  // 重新加載頁面以應用新環境
  window.location.reload();
};

// 獲取當前環境配置
export const getCurrentConfig = (): EnvironmentConfig => {
  const env = getCurrentEnvironment();
  return environments[env] || environments.dev;
};
