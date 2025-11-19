import React, { useState, useEffect } from 'react';
import { adminsApi } from '../services/api';
import { Shield, UserPlus, UserMinus, History, AlertCircle, Crown, User } from 'lucide-react';

interface Admin {
  uid: string;
  email: string;
  role: string;
  is_super_admin: boolean;
  display_name: string;
  created_at: string | null;
  last_login: string | null;
}

interface AuditLog {
  id: string;
  action: string;
  admin_uid: string;
  admin_email: string;
  target_uid: string;
  details: any;
  created_at: string;
}

export default function SettingsPage() {
  const [admins, setAdmins] = useState<Admin[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'admins' | 'audit'>('admins');

  // Add admin modal state
  const [showAddModal, setShowAddModal] = useState(false);
  const [newAdminUid, setNewAdminUid] = useState('');
  const [addReason, setAddReason] = useState('');

  useEffect(() => {
    if (activeTab === 'admins') {
      fetchAdmins();
    } else {
      fetchAuditLogs();
    }
  }, [activeTab]);

  const fetchAdmins = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await adminsApi.list({ page: 1, limit: 100 });
      setAdmins(data.data);
    } catch (err: any) {
      console.error('Error fetching admins:', err);
      setError(err.response?.data?.error || '載入管理員列表失敗');
    } finally {
      setLoading(false);
    }
  };

  const fetchAuditLogs = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await adminsApi.getAuditLogs({ limit: 100 });
      setAuditLogs(data.data);
    } catch (err: any) {
      console.error('Error fetching audit logs:', err);
      setError(err.response?.data?.error || '載入審計日誌失敗');
    } finally {
      setLoading(false);
    }
  };

  const handleGrantAdmin = async () => {
    if (!newAdminUid.trim()) {
      alert('請輸入用戶 UID');
      return;
    }

    try {
      await adminsApi.grant(newAdminUid.trim(), addReason || undefined);
      alert('管理員權限已授予');
      setShowAddModal(false);
      setNewAdminUid('');
      setAddReason('');
      fetchAdmins();
    } catch (err: any) {
      alert(err.response?.data?.error || '授予權限失敗');
    }
  };

  const handleRevokeAdmin = async (uid: string, email: string) => {
    const reason = prompt(`確定要撤銷 ${email} 的管理員權限嗎？\n\n請輸入原因（可選）:`);

    if (reason === null) return; // 用戶取消

    try {
      await adminsApi.revoke(uid, reason || undefined);
      alert('管理員權限已撤銷');
      fetchAdmins();
    } catch (err: any) {
      alert(err.response?.data?.error || '撤銷權限失敗');
    }
  };

  const getRoleBadge = (admin: Admin) => {
    if (admin.is_super_admin) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-purple-100 text-purple-700">
          <Crown className="w-3 h-3" />
          超級管理員
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-700">
        <Shield className="w-3 h-3" />
        管理員
      </span>
    );
  };

  const getActionBadge = (action: string) => {
    const badges: { [key: string]: { label: string; color: string } } = {
      grant_admin: { label: '授予權限', color: 'green' },
      revoke_admin: { label: '撤銷權限', color: 'red' },
      extend_subscription: { label: '延長訂閱', color: 'blue' },
      cancel_subscription: { label: '取消訂閱', color: 'orange' },
      disable_invite_code: { label: '禁用邀請碼', color: 'gray' },
    };

    const badge = badges[action] || { label: action, color: 'gray' };
    return (
      <span className={`px-2 py-1 text-xs rounded-full bg-${badge.color}-100 text-${badge.color}-700`}>
        {badge.label}
      </span>
    );
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">系統設定</h1>
        <p className="text-gray-600">管理員權限與系統審計日誌</p>
      </div>

      {/* Tabs */}
      <div className="mb-6 border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('admins')}
            className={`${
              activeTab === 'admins'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2`}
          >
            <Shield className="w-4 h-4" />
            管理員管理
          </button>
          <button
            onClick={() => setActiveTab('audit')}
            className={`${
              activeTab === 'audit'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2`}
          >
            <History className="w-4 h-4" />
            審計日誌
          </button>
        </nav>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-medium text-red-900 mb-1">錯誤</h3>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      )}

      {/* Admins Tab */}
      {!loading && activeTab === 'admins' && (
        <div>
          {/* Add Admin Button */}
          <div className="mb-4 flex justify-end">
            <button
              onClick={() => setShowAddModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              <UserPlus className="w-4 h-4" />
              添加管理員
            </button>
          </div>

          {/* Admins Table */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">管理員</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">角色</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">創建時間</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">最後登入</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">操作</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {admins.map((admin) => (
                  <tr key={admin.uid || admin.email} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div>
                        <div className="font-medium text-gray-900">{admin.display_name}</div>
                        <div className="text-sm text-gray-500">{admin.email}</div>
                        {admin.uid && <div className="text-xs text-gray-400 font-mono">{admin.uid}</div>}
                      </div>
                    </td>
                    <td className="px-6 py-4">{getRoleBadge(admin)}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {admin.created_at ? new Date(admin.created_at).toLocaleDateString('zh-TW') : '-'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {admin.last_login ? new Date(admin.last_login).toLocaleDateString('zh-TW') : '-'}
                    </td>
                    <td className="px-6 py-4 text-right">
                      {!admin.is_super_admin && admin.uid && (
                        <button
                          onClick={() => handleRevokeAdmin(admin.uid, admin.email)}
                          className="text-red-600 hover:text-red-900 text-sm font-medium flex items-center gap-1 ml-auto"
                        >
                          <UserMinus className="w-4 h-4" />
                          撤銷權限
                        </button>
                      )}
                      {admin.is_super_admin && (
                        <span className="text-gray-400 text-sm">不可修改</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Audit Logs Tab */}
      {!loading && activeTab === 'audit' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">時間</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">管理員</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">目標</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">詳情</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {auditLogs.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                      暫無審計日誌
                    </td>
                  </tr>
                ) : (
                  auditLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {new Date(log.created_at).toLocaleString('zh-TW')}
                      </td>
                      <td className="px-6 py-4">{getActionBadge(log.action)}</td>
                      <td className="px-6 py-4 text-sm text-gray-900">{log.admin_email}</td>
                      <td className="px-6 py-4 text-sm text-gray-600 font-mono">
                        {log.target_uid || '-'}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {log.details?.reason || log.details?.target_email || '-'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Add Admin Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold text-gray-900 mb-4">添加管理員</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  用戶 UID *
                </label>
                <input
                  type="text"
                  value={newAdminUid}
                  onChange={(e) => setNewAdminUid(e.target.value)}
                  placeholder="輸入用戶的 Firebase UID"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  原因（可選）
                </label>
                <textarea
                  value={addReason}
                  onChange={(e) => setAddReason(e.target.value)}
                  placeholder="授予管理員權限的原因"
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="mt-6 flex gap-3 justify-end">
              <button
                onClick={() => {
                  setShowAddModal(false);
                  setNewAdminUid('');
                  setAddReason('');
                }}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
              >
                取消
              </button>
              <button
                onClick={handleGrantAdmin}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                授予權限
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
