/**
 * Layout 組件
 *
 * 包含 Header 和 Sidebar 的主佈局
 */
import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { LogOut, Users, BarChart3, Settings, Gift, User, Server, RefreshCw, AlertTriangle, Smartphone } from 'lucide-react';
import apiClient from '../services/api';
import { getCurrentEnvironment, setCurrentEnvironment, getCurrentConfig } from '../config/environments';

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [environment, setEnvironment] = useState<string>(getCurrentEnvironment());
  const [showEnvMenu, setShowEnvMenu] = useState(false);
  const [backendEnvironment, setBackendEnvironment] = useState<string | null>(null);
  const [envMismatch, setEnvMismatch] = useState(false);

  useEffect(() => {
    // 從 localStorage 獲取當前環境
    setEnvironment(getCurrentEnvironment());
  }, []);

  // 檢查後端環境
  useEffect(() => {
    const checkBackendEnvironment = async () => {
      try {
        const currentConfig = getCurrentConfig();
        const response = await fetch(`${currentConfig.apiBaseUrl}/health`);
        const data = await response.json();
        const backendEnv = data.environment;
        setBackendEnvironment(backendEnv);

        // 檢查前後端環境是否一致
        const frontendEnv = getCurrentEnvironment();
        setEnvMismatch(frontendEnv !== backendEnv);
      } catch (error) {
        console.error('Failed to check backend environment:', error);
      }
    };

    checkBackendEnvironment();
    // 每 10 秒檢查一次
    const interval = setInterval(checkBackendEnvironment, 10000);
    return () => clearInterval(interval);
  }, [environment]);

  // 點擊外部關閉環境菜單
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (showEnvMenu) {
        const target = event.target as HTMLElement;
        if (!target.closest('.env-menu-container')) {
          setShowEnvMenu(false);
        }
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showEnvMenu]);

  const handleEnvironmentChange = (env: string) => {
    // 直接切換環境，前端會重新加載並連接到對應的後端 port
    // Dev: port 8080, Prod: port 8081
    setCurrentEnvironment(env);
    setShowEnvMenu(false);
  };

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const navigation = [
    { name: '用戶資訊', href: '/users', icon: User },
    { name: '訂閱管理', href: '/subscriptions', icon: Users },
    { name: '邀請碼管理', href: '/invite-codes', icon: Gift },
    { name: '數據儀表板', href: '/dashboard', icon: BarChart3 },
    { name: '設定', href: '/settings', icon: Settings },
    { name: 'IAP 測試', href: '/iap-test', icon: Smartphone },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center space-x-4">
              <Link to="/" className="flex items-center space-x-3">
                <img src="/paceriz_logo.png" alt="Paceriz" className="h-8 w-8" />
                <span className="text-xl font-bold text-gray-900">Paceriz Admin</span>
              </Link>

              {/* Environment Switcher */}
              <div className="relative env-menu-container">
                <button
                  onClick={() => setShowEnvMenu(!showEnvMenu)}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <Server className="w-4 h-4 text-gray-500" />
                  <span className={`px-2.5 py-1 text-xs font-semibold rounded-full ${
                    environment === 'prod'
                      ? 'bg-red-100 text-red-800 border border-red-300'
                      : 'bg-green-100 text-green-800 border border-green-300'
                  }`}>
                    {environment === 'prod' ? 'PRODUCTION' : 'DEVELOPMENT'}
                  </span>
                  <RefreshCw className="w-3 h-3 text-gray-400" />
                </button>

                {/* Dropdown Menu */}
                {showEnvMenu && (
                  <div className="absolute left-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
                    <div className="p-2">
                      <button
                        onClick={() => handleEnvironmentChange('dev')}
                        className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                          environment === 'dev'
                            ? 'bg-green-50 text-green-900'
                            : 'hover:bg-gray-50 text-gray-700'
                        }`}
                      >
                        <div className="w-2 h-2 rounded-full bg-green-500"></div>
                        <div className="flex-1 text-left">
                          <div className="font-medium">Development</div>
                          <div className="text-xs text-gray-500">havital-dev</div>
                        </div>
                        {environment === 'dev' && (
                          <span className="text-green-600">✓</span>
                        )}
                      </button>
                      <button
                        onClick={() => handleEnvironmentChange('prod')}
                        className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                          environment === 'prod'
                            ? 'bg-red-50 text-red-900'
                            : 'hover:bg-gray-50 text-gray-700'
                        }`}
                      >
                        <div className="w-2 h-2 rounded-full bg-red-500"></div>
                        <div className="flex-1 text-left">
                          <div className="font-medium">Production</div>
                          <div className="text-xs text-gray-500">paceriz-prod</div>
                        </div>
                        {environment === 'prod' && (
                          <span className="text-red-600">✓</span>
                        )}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* User Menu */}
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                {user?.email}
              </span>
              <button
                onClick={handleLogout}
                className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <LogOut className="w-4 h-4 mr-2" />
                登出
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Environment Mismatch Warning Banner */}
      {envMismatch && backendEnvironment && (
        <div className="bg-red-50 border-b border-red-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="py-3 flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-semibold text-red-900">
                  ⚠️ 環境不一致警告
                </p>
                <p className="text-sm text-red-700 mt-1">
                  前端環境: <span className="font-mono font-semibold">{environment}</span>
                  {' '} | {' '}
                  後端環境: <span className="font-mono font-semibold">{backendEnvironment}</span>
                  {' '} - {' '}
                  請執行 <code className="bg-red-100 px-2 py-0.5 rounded font-mono text-xs">
                    ./restart_{environment}.sh
                  </code> 來重啟後端服務
                </p>
              </div>
              <button
                onClick={() => {
                  const scriptName = environment === 'prod' ? 'restart_prod.sh' : 'restart_dev.sh';
                  navigator.clipboard.writeText(`./${scriptName}`);
                  alert('已複製指令到剪貼簿！');
                }}
                className="px-3 py-1.5 bg-red-600 text-white text-sm rounded-md hover:bg-red-700 transition-colors"
              >
                複製指令
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 bg-white shadow-sm min-h-[calc(100vh-4rem)]">
          <nav className="mt-5 px-2 space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href || location.pathname.startsWith(item.href + '/');
              const Icon = item.icon;

              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`
                    group flex items-center px-3 py-2 text-sm font-medium rounded-md
                    ${isActive
                      ? 'bg-blue-100 text-blue-900'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    }
                  `}
                >
                  <Icon
                    className={`
                      mr-3 h-5 w-5
                      ${isActive ? 'text-blue-900' : 'text-gray-400 group-hover:text-gray-500'}
                    `}
                  />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
