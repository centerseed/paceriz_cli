/**
 * App 主組件
 *
 * 處理路由和認證邏輯
 */
import React, { useEffect, ReactNode } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { setAuthToken } from './services/api';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import UsersPage from './pages/UsersPage';
import UserDetailPage from './pages/UserDetailPage';
import WorkoutListPage from './pages/WorkoutListPage';
import WorkoutDetailPage from './pages/WorkoutDetailPage';
import SubscriptionsPage from './pages/SubscriptionsPage';
import SubscriptionDetailPage from './pages/SubscriptionDetailPage';
import InviteCodesPage from './pages/InviteCodesPage';
import InviteCodeDetailPage from './pages/InviteCodeDetailPage';
import DashboardPage from './pages/DashboardPage';
import SettingsPage from './pages/SettingsPage';
import IAPTestPage from './pages/IAPTestPage';

// Error Boundary Component
interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error) {
    console.error('❌ Application Error:', error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-red-50 flex items-center justify-center p-4">
          <div className="bg-white p-8 rounded-lg shadow-lg max-w-md">
            <h1 className="text-xl font-bold text-red-600 mb-4">⚠️ 應用程序錯誤</h1>
            <div className="bg-red-100 border border-red-300 rounded p-4 mb-4">
              <p className="text-sm text-red-800 font-mono break-words">
                {this.state.error?.message || '發生未知錯誤'}
              </p>
            </div>
            <details className="text-sm text-gray-600 mb-4">
              <summary className="cursor-pointer font-semibold">詳細資訊</summary>
              <pre className="mt-2 text-xs bg-gray-100 p-2 rounded overflow-auto max-h-40">
                {this.state.error?.stack}
              </pre>
            </details>
            <div className="bg-blue-50 border border-blue-300 rounded p-4">
              <p className="text-sm text-blue-800 mb-2">
                <strong>可能的原因：</strong>
              </p>
              <ul className="text-sm text-blue-700 list-disc list-inside space-y-1">
                <li>Firebase 環境變數未設置</li>
                <li>環境變數值不正確</li>
                <li>網路連線問題</li>
              </ul>
              <p className="text-sm text-blue-800 mt-2">
                請檢查瀏覽器控制台 (F12) 的完整錯誤訊息。
              </p>
              <p className="text-sm text-blue-800 mt-2">
                參考 <code className="bg-white px-1">frontend/ENV_SETUP.md</code> 進行設定。
              </p>
            </div>
            <button
              onClick={() => window.location.reload()}
              className="mt-4 w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
            >
              重新載入
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Protected Route Component
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-500">載入中...</div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

// Auth Token Updater
function AuthTokenUpdater() {
  const { getIdToken, user } = useAuth();

  useEffect(() => {
    const updateToken = async () => {
      if (user) {
        const token = await getIdToken();
        setAuthToken(token);
      } else {
        setAuthToken(null);
      }
    };

    updateToken();
  }, [user, getIdToken]);

  return null;
}

function AppRoutes() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <AuthTokenUpdater />
          <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<LoginPage />} />

          {/* Protected Routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout>
                  <Navigate to="/users" replace />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/users"
            element={
              <ProtectedRoute>
                <Layout>
                  <UsersPage />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/users/:uid"
            element={
              <ProtectedRoute>
                <Layout>
                  <UserDetailPage />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/users/:uid/workouts"
            element={
              <ProtectedRoute>
                <Layout>
                  <WorkoutListPage />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/users/:uid/workouts/:provider/:activityId"
            element={
              <ProtectedRoute>
                <Layout>
                  <WorkoutDetailPage />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/subscriptions"
            element={
              <ProtectedRoute>
                <Layout>
                  <SubscriptionsPage />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/subscriptions/:uid"
            element={
              <ProtectedRoute>
                <Layout>
                  <SubscriptionDetailPage />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/invite-codes"
            element={
              <ProtectedRoute>
                <Layout>
                  <InviteCodesPage />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/invite-codes/:code"
            element={
              <ProtectedRoute>
                <Layout>
                  <InviteCodeDetailPage />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Layout>
                  <DashboardPage />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <Layout>
                  <SettingsPage />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/iap-test"
            element={
              <ProtectedRoute>
                <Layout>
                  <IAPTestPage />
                </Layout>
              </ProtectedRoute>
            }
          />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default AppRoutes;
