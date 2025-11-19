/**
 * App 主組件
 *
 * 處理路由和認證邏輯
 */
import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { setAuthToken } from './services/api';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import UsersPage from './pages/UsersPage';
import UserDetailPage from './pages/UserDetailPage';
import SubscriptionsPage from './pages/SubscriptionsPage';
import SubscriptionDetailPage from './pages/SubscriptionDetailPage';
import InviteCodesPage from './pages/InviteCodesPage';
import InviteCodeDetailPage from './pages/InviteCodeDetailPage';
import DashboardPage from './pages/DashboardPage';
import SettingsPage from './pages/SettingsPage';
import IAPTestPage from './pages/IAPTestPage';

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
  );
}

export default AppRoutes;
