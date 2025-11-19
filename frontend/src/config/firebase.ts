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

console.log(`🔥 Initializing Firebase for environment: ${currentConfig.name}`);
console.log(`📦 Project ID: ${firebaseConfig.projectId}`);

// 初始化 Firebase
const app = initializeApp(firebaseConfig);

// 初始化 Auth
export const auth = getAuth(app);

export default app;
