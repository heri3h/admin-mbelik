import React, { useEffect, useState } from 'react';
import { Settings, ShieldCheck, AlertCircle, Key, Layers, Globe, RefreshCw, XCircle, KeyRound, CheckCircle2, Lock, Trash2, Database, Plus, Edit2, Save, Link as LinkIcon, Building2, Sliders } from 'lucide-react';
import { dashboardService, authService } from '../services/api';

export default function SettingsPage({ onOpenPricingModal }) {

  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  // Change password form state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [pwdLoading, setPwdLoading] = useState(false);
  const [pwdError, setPwdError] = useState('');
  const [pwdSuccess, setPwdSuccess] = useState('');

  // Clear cache state
  const [cacheLoading, setCacheLoading] = useState(false);
  const [cacheError, setCacheError] = useState('');
  const [cacheSuccess, setCacheSuccess] = useState('');

  // Google Ads Accounts Management State
  const [gadsAccounts, setGadsAccounts] = useState([]);
  const [domainsList, setDomainsList] = useState([]);
  const [gadsLoading, setGadsLoading] = useState(false);
  const [gadsError, setGadsError] = useState('');
  const [gadsSuccess, setGadsSuccess] = useState('');

  // Add Account Form State
  const [newCid, setNewCid] = useState('');
  const [newAccName, setNewAccName] = useState('');
  const [newDomain, setNewDomain] = useState('All / Unassigned');

  // Edit Account State
  const [editingId, setEditingId] = useState(null);
  const [editAccName, setEditAccName] = useState('');
  const [editDomain, setEditDomain] = useState('');

  // JSON Export Targets State
  const [exportTargets, setExportTargets] = useState([]);
  const [exportLoading, setExportLoading] = useState(false);
  const [exportError, setExportError] = useState('');
  const [exportSuccess, setExportSuccess] = useState('');

  // Add Target Form State
  const [targetDomain, setTargetDomain] = useState('');
  const [targetFilepath, setTargetFilepath] = useState('');
  const [targetStartHour, setTargetStartHour] = useState(10);
  const [targetEndHour, setTargetEndHour] = useState(23);

  useEffect(() => {
    fetchStatus();
    fetchGadsAccounts();
    fetchDomains();
    fetchExportTargets();
  }, []);

  const fetchExportTargets = async () => {
    setExportLoading(true);
    try {
      const data = await dashboardService.getExportTargets();
      setExportTargets(data);
    } catch (err) {
      console.error('Failed fetching export targets', err);
    } finally {
      setExportLoading(false);
    }
  };

  const handleAddExportTarget = async (e) => {
    e.preventDefault();
    setExportError('');
    setExportSuccess('');

    if (!targetDomain.trim() || !targetFilepath.trim()) {
      setExportError('Domain and Target Filepath are required.');
      return;
    }

    try {
      await dashboardService.addExportTarget({
        domain: targetDomain.trim(),
        target_filepath: targetFilepath.trim(),
        start_hour: parseInt(targetStartHour),
        end_hour: parseInt(targetEndHour),
        is_active: true
      });
      setExportSuccess(`Export target for ${targetDomain.trim()} added successfully!`);
      setTargetDomain('');
      setTargetFilepath('');
      setTargetStartHour(10);
      setTargetEndHour(23);
      fetchExportTargets();
    } catch (err) {
      setExportError(err.response?.data?.detail || 'Failed to add export target.');
    }
  };

  const handleToggleTargetActive = async (target) => {
    setExportError('');
    setExportSuccess('');
    try {
      await dashboardService.updateExportTarget(target.id, {
        is_active: !target.is_active
      });
      setExportSuccess(`Target status for ${target.domain} updated successfully.`);
      fetchExportTargets();
    } catch (err) {
      setExportError('Failed to update target status.');
    }
  };

  const handleDeleteTarget = async (id, domain) => {
    if (!window.confirm(`Delete export target for ${domain}?`)) return;
    setExportError('');
    setExportSuccess('');
    try {
      await dashboardService.deleteExportTarget(id);
      setExportSuccess(`Export target for ${domain} deleted successfully.`);
      fetchExportTargets();
    } catch (err) {
      setExportError('Failed to delete export target.');
    }
  };

  const handleTestExport = async (id, domain) => {
    setExportError('');
    setExportSuccess('');
    try {
      const res = await dashboardService.testExportTarget(id);
      setExportSuccess(res.message || `JSON export for ${domain} simulated successfully!`);
    } catch (err) {
      setExportError(err.response?.data?.detail || `Failed to export JSON for ${domain}.`);
    }
  };

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const data = await dashboardService.getSettingsStatus();
      setStatus(data);
    } catch (err) {
      console.error('Failed fetching settings status', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchGadsAccounts = async () => {
    setGadsLoading(true);
    try {
      const accs = await dashboardService.getGoogleAdsAccounts();
      setGadsAccounts(accs);
    } catch (err) {
      console.error('Failed fetching Google Ads accounts', err);
    } finally {
      setGadsLoading(false);
    }
  };

  const [isCustomDomain, setIsCustomDomain] = useState(false);

  const fetchDomains = async () => {
    try {
      const domains = await dashboardService.getAvailableDomains();
      const defaultList = ['2b.nubmaster.com', 'baleq.me', 'dpr.skuy.me', 'mbelik.com', 'news.mbelik.com', 'portal.mbelik.com', 'sub.mbelik.com'];
      const combined = Array.from(new Set([...(domains || []), ...defaultList])).sort();
      setDomainsList(['All / Unassigned', ...combined]);
    } catch (err) {
      console.error('Failed fetching domains for mapping', err);
      setDomainsList(['All / Unassigned', '2b.nubmaster.com', 'baleq.me', 'dpr.skuy.me', 'mbelik.com']);
    }
  };

  const handleAddAccount = async (e) => {
    e.preventDefault();
    setGadsError('');
    setGadsSuccess('');

    if (!newCid.trim()) {
      setGadsError('Google Ads Customer ID is required.');
      return;
    }

    try {
      await dashboardService.addGoogleAdsAccount({
        customer_id: newCid.trim(),
        account_name: newAccName.trim() || `Google Ads (${newCid.trim()})`,
        assigned_domain: newDomain
      });
      setGadsSuccess(`Google Ads Account ${newCid.trim()} added successfully!`);
      setNewCid('');
      setNewAccName('');
      setNewDomain('All / Unassigned');
      fetchGadsAccounts();
      fetchStatus();
    } catch (err) {
      setGadsError(err.response?.data?.detail || 'Failed to add Google Ads Account.');
    }
  };

  const handleStartEdit = (acc) => {
    setEditingId(acc.id);
    setEditAccName(acc.account_name || '');
    setEditDomain(acc.assigned_domain || 'All / Unassigned');
  };

  const handleSaveEdit = async (id) => {
    setGadsError('');
    setGadsSuccess('');
    try {
      await dashboardService.updateGoogleAdsAccount(id, {
        account_name: editAccName,
        assigned_domain: editDomain
      });
      setGadsSuccess('Account mapping updated successfully!');
      setEditingId(null);
      fetchGadsAccounts();
    } catch (err) {
      setGadsError(err.response?.data?.detail || 'Failed to update account.');
    }
  };

  const handleDeleteAccount = async (id, cid) => {
    if (!window.confirm(`Delete Google Ads ID ${cid}?`)) return;
    setGadsError('');
    setGadsSuccess('');
    try {
      await dashboardService.deleteGoogleAdsAccount(id);
      setGadsSuccess(`Google Ads ID ${cid} deleted successfully.`);
      fetchGadsAccounts();
      fetchStatus();
    } catch (err) {
      setGadsError(err.response?.data?.detail || 'Failed to delete account.');
    }
  };

  const handleClearCache = async () => {
    if (!window.confirm('Are you sure you want to clear analytics data cache and re-sync? Your admin password & account REMAIN SAFE.')) {
      return;
    }

    setCacheError('');
    setCacheSuccess('');
    setCacheLoading(true);

    try {
      const res = await dashboardService.clearCache();
      if (res && res.status === 'error') {
        setCacheError(res.message || 'Failed to clear cache.');
      } else {
        setCacheSuccess(res?.message || 'Analytics data cache cleared and re-synced successfully!');
      }
    } catch (err) {
      setCacheError(err.response?.data?.detail || err.message || 'Failed to clear cache.');
    } finally {
      setCacheLoading(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setPwdError('');
    setPwdSuccess('');

    if (newPassword !== confirmPassword) {
      setPwdError('New password confirmation does not match.');
      return;
    }

    if (newPassword.length < 6) {
      setPwdError('New password must be at least 6 characters.');
      return;
    }

    setPwdLoading(true);
    try {
      const res = await authService.changePassword(currentPassword, newPassword);
      setPwdSuccess(res.message || 'Password updated successfully.');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      setPwdError(err.response?.data?.detail || 'Failed to change password. Make sure current password is correct.');
    } finally {
      setPwdLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 text-center text-slate-400">
        <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-sky-400" />
        <span>Loading integration status...</span>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
          <Settings className="w-6 h-6 text-sky-400" />
          <span>System Settings & API Integration</span>
        </h1>
        <p className="text-slate-400 text-xs mt-1">
          Manage admin account security and Google Ads API / Google Ad Manager connection status
        </p>
      </div>

      {/* Data Mode Banner */}
      <div className={`p-5 rounded-2xl border ${
        status.use_mock_data
          ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
          : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
      }`}>
        <div className="flex items-start space-x-3">
          {status.use_mock_data ? (
            <AlertCircle className="w-6 h-6 shrink-0 text-amber-400 mt-0.5" />
          ) : (
            <ShieldCheck className="w-6 h-6 shrink-0 text-emerald-400 mt-0.5" />
          )}
          <div className="w-full">
            <h3 className="font-bold text-sm">
              {status.use_mock_data ? 'Simulation Mode (Mock Data) Active' : 'Live API Mode Active'}
            </h3>
            <p className="text-xs opacity-90 mt-1 leading-relaxed">
              {status.use_mock_data
                ? 'The application is currently displaying realistic simulation data because some API credentials are not set or set to false in the .env file.'
                : 'The application connects directly to Google Ads API & Google Ad Manager API to present real-time daily data.'}
            </p>

            {status.use_mock_data && status.missing_fields && status.missing_fields.length > 0 && (
              <div className="mt-4 pt-3 border-t border-amber-500/20">
                <span className="text-xs font-semibold block mb-2 text-amber-200">
                  Reasons Mock Mode Is Still Active:
                </span>
                <ul className="space-y-1">
                  {status.missing_fields.map((msg, idx) => (
                    <li key={idx} className="flex items-center space-x-1.5 text-xs text-amber-300">
                      <XCircle className="w-3.5 h-3.5 shrink-0 text-amber-400" />
                      <span>{msg}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Change Password Card */}
      <div className="bg-slate-800 border border-slate-700/60 p-6 rounded-2xl shadow-sm">
        <div className="flex items-center space-x-3 pb-4 border-b border-slate-700/60 mb-5">
          <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-xl border border-indigo-500/20">
            <Lock className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-white text-base">Change Admin Password</h3>
            <p className="text-slate-400 text-xs mt-0.5">Update application administrator account password</p>
          </div>
        </div>

        {pwdError && (
          <div className="mb-4 p-3.5 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-400 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{pwdError}</span>
          </div>
        )}

        {pwdSuccess && (
          <div className="mb-4 p-3.5 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 text-xs flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{pwdSuccess}</span>
          </div>
        )}

        <form onSubmit={handleChangePassword} className="space-y-4 max-w-lg">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Current Password
            </label>
            <div className="relative">
              <KeyRound className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
              <input
                type="password"
                required
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                placeholder="Enter current password"
                className="w-full pl-9 pr-4 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-sky-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              New Password
            </label>
            <div className="relative">
              <Key className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
              <input
                type="password"
                required
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Enter new password (min 6 characters)"
                className="w-full pl-9 pr-4 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-sky-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Confirm New Password
            </label>
            <div className="relative">
              <Key className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
              <input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Repeat new password"
                className="w-full pl-9 pr-4 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-sky-500"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={pwdLoading}
            className="px-5 py-2.5 bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs rounded-xl shadow-md transition-all disabled:opacity-50 mt-2"
          >
            {pwdLoading ? 'Saving...' : 'Save New Password'}
          </button>
        </form>
      </div>

      {/* Google Ads Accounts & Domain Mapping Card */}
      <div className="bg-slate-800 border border-slate-700/60 p-6 rounded-2xl shadow-sm space-y-6">
        <div className="flex items-center space-x-3 pb-4 border-b border-slate-700/60">
          <div className="p-2 bg-sky-500/10 text-sky-400 rounded-xl border border-sky-500/20">
            <Building2 className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-white text-base">Manage Google Ads Accounts & Site Mapping</h3>
            <p className="text-slate-400 text-xs mt-0.5">Add new Google Ads Customer IDs and link them to specific sites/domains to calculate profit per site</p>
          </div>
        </div>

        {gadsError && (
          <div className="p-3.5 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-400 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{gadsError}</span>
          </div>
        )}

        {gadsSuccess && (
          <div className="p-3.5 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 text-xs flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{gadsSuccess}</span>
          </div>
        )}

        {/* Form Add New Account */}
        <form onSubmit={handleAddAccount} className="bg-slate-900/60 p-4 rounded-xl border border-slate-700/60 space-y-4">
          <h4 className="text-xs font-bold text-sky-400 uppercase tracking-wider flex items-center gap-1.5">
            <Plus className="w-4 h-4" />
            <span>Add New Google Ads ID</span>
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label className="block text-[11px] font-medium text-slate-400 mb-1">Google Ads Customer ID *</label>
              <input
                type="text"
                required
                placeholder="e.g. 123-456-7890"
                value={newCid}
                onChange={(e) => setNewCid(e.target.value)}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500 font-mono"
              />
            </div>
            <div>
              <label className="block text-[11px] font-medium text-slate-400 mb-1">Account Name (Optional)</label>
              <input
                type="text"
                placeholder="e.g. Google Ads - Domain A"
                value={newAccName}
                onChange={(e) => setNewAccName(e.target.value)}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
              />
            </div>
            <div>
              <label className="block text-[11px] font-medium text-slate-400 mb-1">Site Mapping (Domain)</label>
              <select
                value={isCustomDomain ? '__custom__' : newDomain}
                onChange={(e) => {
                  if (e.target.value === '__custom__') {
                    setIsCustomDomain(true);
                    setNewDomain('');
                  } else {
                    setIsCustomDomain(false);
                    setNewDomain(e.target.value);
                  }
                }}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-sky-500 font-medium"
              >
                {domainsList.map((domain, idx) => (
                  <option key={idx} value={domain}>
                    {domain}
                  </option>
                ))}
                <option value="__custom__">+ Enter Custom / Manual Domain...</option>
              </select>

              {isCustomDomain && (
                <input
                  type="text"
                  placeholder="Enter domain name (e.g. sub.mbelik.com)"
                  value={newDomain}
                  onChange={(e) => setNewDomain(e.target.value)}
                  className="w-full mt-2 px-3 py-2 bg-slate-900 border border-sky-500/80 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none"
                />
              )}
            </div>
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs rounded-lg shadow transition-all flex items-center gap-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Save Google Ads ID</span>
          </button>
        </form>

        {/* Account & Mapping List Table */}
        <div className="overflow-x-auto border border-slate-700/60 rounded-xl">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/80 uppercase text-[10px] tracking-wider text-slate-400 border-b border-slate-700/60">
              <tr>
                <th className="px-4 py-3">Customer ID</th>
                <th className="px-4 py-3">Account Name</th>
                <th className="px-4 py-3">Connected Domain</th>
                <th className="px-4 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/40">
              {gadsAccounts.length > 0 ? (
                gadsAccounts.map((acc) => (
                  <tr key={acc.id} className="hover:bg-slate-700/20 transition-colors">
                    <td className="px-4 py-3 font-mono text-sky-400 font-semibold">{acc.customer_id}</td>
                    <td className="px-4 py-3">
                      {editingId === acc.id ? (
                        <input
                          type="text"
                          value={editAccName}
                          onChange={(e) => setEditAccName(e.target.value)}
                          className="px-2 py-1 bg-slate-900 border border-slate-600 rounded text-xs text-white"
                        />
                      ) : (
                        <span>{acc.account_name || '-'}</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {editingId === acc.id ? (
                        <select
                          value={editDomain}
                          onChange={(e) => setEditDomain(e.target.value)}
                          className="px-2 py-1 bg-slate-900 border border-slate-600 rounded text-xs text-white font-medium"
                        >
                          {domainsList.map((d, idx) => (
                            <option key={idx} value={d}>{d}</option>
                          ))}
                        </select>
                      ) : (
                        <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium border ${
                          acc.assigned_domain && acc.assigned_domain !== 'All / Unassigned'
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                            : 'bg-slate-700/40 text-slate-400 border-slate-600'
                        }`}>
                          <LinkIcon className="w-3 h-3" />
                          <span>{acc.assigned_domain || 'All / Unassigned'}</span>
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right space-x-2">
                      {editingId === acc.id ? (
                        <button
                          onClick={() => handleSaveEdit(acc.id)}
                          className="p-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg transition-all"
                          title="Save"
                        >
                          <Save className="w-3.5 h-3.5" />
                        </button>
                      ) : (
                        <button
                          onClick={() => handleStartEdit(acc)}
                          className="p-1.5 bg-slate-700 hover:bg-slate-600 text-sky-300 rounded-lg transition-all"
                          title="Edit Mapping"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                      <button
                        onClick={() => handleDeleteAccount(acc.id, acc.customer_id)}
                        className="p-1.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 rounded-lg transition-all border border-rose-500/30"
                        title="Delete"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="4" className="px-4 py-6 text-center text-slate-500 italic">
                    No Google Ads Accounts registered yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* JSON Auto-Export Targets Card */}
      <div className="bg-slate-800 border border-slate-700/60 p-6 rounded-2xl shadow-sm">
        <div className="flex flex-wrap items-center justify-between pb-4 border-b border-slate-700/60 mb-4 gap-3">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-purple-500/10 text-purple-400 rounded-xl border border-purple-500/20">
              <Globe className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-white text-base">Site Auto-Export JSON Settings</h3>
              <p className="text-slate-400 text-xs mt-0.5">Manage domains and VPS folder paths where current_pricing.json is generated during sync</p>
            </div>
          </div>

          {onOpenPricingModal && (
            <button
              onClick={onOpenPricingModal}
              className="px-3.5 py-2 bg-sky-600/20 hover:bg-sky-600/30 text-sky-300 border border-sky-500/40 rounded-xl font-bold text-xs transition-all flex items-center space-x-1.5 shadow-sm"
            >
              <Sliders className="w-4 h-4 text-sky-400" />
              <span>Manage GAM Auto Pricing Rules</span>
            </button>
          )}
        </div>


        {exportError && (
          <div className="mb-4 p-3.5 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-400 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{exportError}</span>
          </div>
        )}

        {exportSuccess && (
          <div className="mb-4 p-3.5 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 text-xs flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{exportSuccess}</span>
          </div>
        )}

        {/* Add Target Form */}
        <form onSubmit={handleAddExportTarget} className="mb-6 p-4 bg-slate-900/60 border border-slate-700/50 rounded-xl space-y-4">
          <div className="text-xs font-semibold text-slate-300 flex items-center space-x-1.5">
            <Plus className="w-4 h-4 text-purple-400" />
            <span>Add New JSON Export Target</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-medium text-slate-400 mb-1">Target Domain</label>
              <input
                type="text"
                value={targetDomain}
                onChange={(e) => setTargetDomain(e.target.value)}
                placeholder="e.g. spotgames.top or zse.ugames.top"
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-purple-500"
              />
            </div>
            <div>
              <label className="block text-[11px] font-medium text-slate-400 mb-1">JSON File Path on VPS</label>
              <input
                type="text"
                value={targetFilepath}
                onChange={(e) => setTargetFilepath(e.target.value)}
                placeholder="/home/mbummm/web/spotgames.top/public_html/current_pricing.json"
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white font-mono placeholder-slate-500 focus:outline-none focus:border-purple-500"
              />
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
            <div className="flex items-center space-x-3 text-xs">
              <span className="text-slate-400">Operating Hours:</span>
              <div className="flex items-center space-x-1.5">
                <input
                  type="number"
                  min="0"
                  max="23"
                  value={targetStartHour}
                  onChange={(e) => setTargetStartHour(e.target.value)}
                  className="w-14 bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-white text-center"
                />
                <span className="text-slate-500">to</span>
                <input
                  type="number"
                  min="0"
                  max="23"
                  value={targetEndHour}
                  onChange={(e) => setTargetEndHour(e.target.value)}
                  className="w-14 bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-white text-center"
                />
                <span className="text-slate-400">UTC+7</span>
              </div>
            </div>

            <button
              type="submit"
              className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs rounded-lg transition-all flex items-center space-x-1.5"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Save Export Target</span>
            </button>
          </div>
        </form>

        {/* Target List Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 text-slate-400 font-semibold border-b border-slate-700">
              <tr>
                <th className="px-4 py-3">Domain</th>
                <th className="px-4 py-3">Target File Path</th>
                <th className="px-4 py-3 text-center">Operating Hours</th>
                <th className="px-4 py-3 text-center">Status</th>
                <th className="px-4 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50 text-slate-300">
              {exportTargets.length > 0 ? (
                exportTargets.map((target) => (
                  <tr key={target.id} className="hover:bg-slate-700/30 transition-colors">
                    <td className="px-4 py-3 font-semibold text-white">{target.domain}</td>
                    <td className="px-4 py-3 font-mono text-[11px] text-purple-300 max-w-xs truncate" title={target.target_filepath}>
                      {target.target_filepath}
                    </td>
                    <td className="px-4 py-3 text-center font-mono text-xs text-slate-300">
                      {target.start_hour}:00 - {target.end_hour}:00 UTC+7
                    </td>
                    <td className="px-4 py-3 text-center">
                      <button
                        onClick={() => handleToggleTargetActive(target)}
                        className={`px-2.5 py-0.5 rounded-full text-[11px] font-semibold border transition-all ${
                          target.is_active
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                            : 'bg-slate-700/50 text-slate-400 border-slate-600'
                        }`}
                      >
                        {target.is_active ? 'Active' : 'Inactive'}
                      </button>
                    </td>
                    <td className="px-4 py-3 text-right space-x-1.5">
                      <button
                        onClick={() => handleTestExport(target.id, target.domain)}
                        className="px-2.5 py-1 bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/30 rounded-lg font-medium text-[11px] transition-all"
                        title="Test export now"
                      >
                        Test Export
                      </button>
                      <button
                        onClick={() => handleDeleteTarget(target.id, target.domain)}
                        className="p-1.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 rounded-lg transition-all border border-rose-500/30"
                        title="Delete Target"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="5" className="px-4 py-6 text-center text-slate-500 italic">
                    No auto-export JSON targets registered yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Clear Cache Card */}
      <div className="bg-slate-800 border border-slate-700/60 p-6 rounded-2xl shadow-sm">
        <div className="flex items-center space-x-3 pb-4 border-b border-slate-700/60 mb-4">
          <div className="p-2 bg-amber-500/10 text-amber-400 rounded-xl border border-amber-500/20">
            <Database className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-white text-base">Data Cache Cleanup (Safe Reset)</h3>
            <p className="text-slate-400 text-xs mt-0.5">Clear analytics cache & re-sync from API without resetting admin password</p>
          </div>
        </div>

        <p className="text-xs text-slate-300 mb-4 leading-relaxed">
          Use this button to refresh all historical data from Google Ads & GAM. Your admin account and password <strong className="text-emerald-400 font-semibold">REMAIN SAFE</strong> and will not reset to default.
        </p>

        {cacheError && (
          <div className="mb-4 p-3.5 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-400 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{cacheError}</span>
          </div>
        )}

        {cacheSuccess && (
          <div className="mb-4 p-3.5 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 text-xs flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{cacheSuccess}</span>
          </div>
        )}

        <button
          onClick={handleClearCache}
          disabled={cacheLoading}
          className="px-5 py-2.5 bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs rounded-xl shadow-md transition-all disabled:opacity-50 flex items-center space-x-2"
        >
          {cacheLoading ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Clearing & Re-syncing Data...</span>
            </>
          ) : (
            <>
              <Trash2 className="w-4 h-4" />
              <span>Clear Data Cache & Re-sync</span>
            </>
          )}
        </button>
      </div>

      {/* Integration Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Google Ads Status */}
        <div className="bg-slate-800 border border-slate-700/60 p-6 rounded-2xl">
          <div className="flex items-center justify-between pb-4 border-b border-slate-700">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-sky-500/10 text-sky-400 rounded-xl border border-sky-500/20">
                <Layers className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-white text-base">Google Ads API</h3>
            </div>
            <span className={`text-xs px-2.5 py-1 rounded-full font-semibold border ${
              status.google_ads_configured
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                : 'bg-slate-700 text-slate-400 border-slate-600'
            }`}>
              {status.google_ads_configured ? 'Connected' : 'Not Configured'}
            </span>
          </div>

          <div className="mt-4 space-y-3 text-xs">
            <div>
              <span className="text-slate-400 block font-medium">Registered Accounts / Customer IDs:</span>
              <div className="mt-1 flex flex-wrap gap-1.5">
                {status.configured_customer_ids.length > 0 ? (
                  status.configured_customer_ids.map((cid, idx) => (
                    <span key={idx} className="font-mono bg-slate-900 px-2 py-1 rounded text-sky-400 border border-slate-700">
                      {cid}
                    </span>
                  ))
                ) : (
                  <span className="text-slate-500 italic">No Customer IDs in .env yet</span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* GAM Status */}
        <div className="bg-slate-800 border border-slate-700/60 p-6 rounded-2xl">
          <div className="flex items-center justify-between pb-4 border-b border-slate-700">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-xl border border-emerald-500/20">
                <Globe className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-white text-base">Google Ad Manager (GAM)</h3>
            </div>
            <span className={`text-xs px-2.5 py-1 rounded-full font-semibold border ${
              status.gam_configured
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                : 'bg-slate-700 text-slate-400 border-slate-600'
            }`}>
              {status.gam_configured ? 'Connected' : 'Not Configured'}
            </span>
          </div>

          <div className="mt-4 space-y-3 text-xs">
            <div>
              <span className="text-slate-400 block font-medium">GAM Network Code:</span>
              <span className="font-mono bg-slate-900 px-2.5 py-1 rounded text-emerald-400 border border-slate-700 mt-1 inline-block">
                {status.gam_network_code || 'Not set'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
