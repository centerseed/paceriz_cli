/**
 * Firebase 配置
 *
 * 用於 Admin Frontend 的 Firebase Auth
 * 支援運行時環境切換
 */
import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getCurrentConfig } from './environments';

// 獲取當前環境的 Firebase 配置
const currentConfig = getCurrentConfig();
const firebaseConfig = currentConfig.firebase;

// 驗證 Firebase 配置
const requiredFields = ['apiKey', 'authDomain', 'projectId', 'appId'];
const missingFields = requiredFields.filter(field => !firebaseConfig[field as keyof typeof firebaseConfig]);

if (missingFields.length > 0) {
  console.error('❌ Firebase Configuration Error');
  console.error('Missing environment variables:');
  const envPrefix = currentConfig.name === 'Production' ? 'PROD' : 'DEV';
  missingFields.forEach(field => {
    // Convert camelCase to SNAKE_CASE
    const snakeCase = field.replace(/([A-Z])/g, '_$1').toUpperCase();
    console.error(`  - VITE_FIREBASE_${envPrefix}${snakeCase}`);
  });
  console.error('');
  console.error('Please configure environment variables in frontend/.env.development or frontend/.env.production');
  console.error('See frontend/ENV_SETUP.md for instructions');
  console.error('');
}

console.log(`🔥 Initializing Firebase for environment: ${currentConfig.name}`);
console.log(`📦 Project ID: ${firebaseConfig.projectId || '(missing)'}`);

// 初始化 Firebase
let app;
let auth;

try {
  app = initializeApp(firebaseConfig);
  auth = getAuth(app);
  console.log('✅ Firebase initialized successfully');
} catch (error) {
  console.error('❌ Firebase initialization failed:', error);
  throw error;
}

export { auth };
export default app;
