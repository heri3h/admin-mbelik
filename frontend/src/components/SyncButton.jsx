import React, { useState } from 'react';
import { RefreshCw, CheckCircle2, AlertCircle, Trash2 } from 'lucide-react';
import { dashboardService } from '../services/api';

export default function SyncButton({ startDate, endDate, onSyncSuccess }) {
  const [loading, setLoading] = useState(false);
  const [clearingCache, setClearingCache] = useState(false);
  const [statusMsg, setStatusMsg] = useState(null);

  const handleSync = async () => {
    setLoading(true);
    setStatusMsg(null);
    try {
      const res = await dashboardService.triggerSync(startDate, endDate);
      setStatusMsg({ type: res.status === 'error' ? 'error' : 'success', text: res.message });
      if (onSyncSuccess) {
        onSyncSuccess();
      }
    } catch (err) {
      setStatusMsg({ type: 'error', text: 'Gagal menyinkronkan data API.' });
    } finally {
      setLoading(false);
      setTimeout(() => setStatusMsg(null), 5000);
    }
  };

  const handleClearCache = async () => {
    setClearingCache(true);
    setStatusMsg(null);
    try {
      const res = await dashboardService.clearCache();
      setStatusMsg({ type: res.status === 'error' ? 'error' : 'success', text: res.message || 'Cache Berhasil Dibersihkan' });
      if (onSyncSuccess) {
        onSyncSuccess();
      }
    } catch (err) {
      setStatusMsg({ type: 'error', text: 'Gagal membersihkan cache.' });
    } finally {
      setClearingCache(false);
      setTimeout(() => setStatusMsg(null), 5000);
    }
  };

  return (
    <div className="flex items-center space-x-3">
      {statusMsg && (
        <div className={`flex items-center space-x-1.5 text-xs px-3 py-1.5 rounded-lg border font-medium ${
          statusMsg.type === 'success'
            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
            : statusMsg.type === 'warning'
            ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
            : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
        }`}>
          {statusMsg.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
          <span>{statusMsg.text}</span>
        </div>
      )}

      <button
        onClick={handleSync}
        disabled={loading || clearingCache}
        className="flex items-center space-x-2 bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-600 hover:to-indigo-700 text-white font-semibold text-xs px-4 py-2 rounded-lg shadow-lg shadow-sky-500/20 transition-all disabled:opacity-50"
      >
        <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        <span>{loading ? 'Syncing...' : 'Sync Data'}</span>
      </button>

      <button
        onClick={handleClearCache}
        disabled={loading || clearingCache}
        title="Hapus seluruh cache database dan tarik ulang data segar dari API"
        className="flex items-center space-x-2 bg-slate-800 hover:bg-rose-950/40 text-slate-300 hover:text-rose-400 font-medium text-xs px-3 py-2 rounded-lg border border-slate-700 hover:border-rose-500/50 transition-all disabled:opacity-50"
      >
        <Trash2 className={`w-4 h-4 ${clearingCache ? 'animate-spin' : ''}`} />
        <span>{clearingCache ? 'Clearing...' : 'Clear Cache'}</span>
      </button>
    </div>
  );
}
