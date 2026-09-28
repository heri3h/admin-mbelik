import React, { useState, useRef, useEffect } from 'react';
import { RefreshCw, CheckCircle2, AlertCircle, Trash2, ChevronDown, Zap } from 'lucide-react';
import { dashboardService } from '../services/api';

export default function SyncButton({ startDate, endDate, onSyncSuccess }) {
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [clearingCache, setClearingCache] = useState(false);
  const [statusMsg, setStatusMsg] = useState(null);
  const dropdownRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSync = async () => {
    setIsOpen(false);
    setLoading(true);
    setStatusMsg(null);
    try {
      const res = await dashboardService.triggerSync(startDate, endDate);
      setStatusMsg({ type: res.status === 'error' ? 'error' : 'success', text: res.message });
      if (onSyncSuccess) {
        onSyncSuccess();
      }
    } catch (err) {
      setStatusMsg({ type: 'error', text: 'Failed to sync API data.' });
    } finally {
      setLoading(false);
      setTimeout(() => setStatusMsg(null), 5000);
    }
  };

  const handleClearCache = async () => {
    setIsOpen(false);
    setClearingCache(true);
    setStatusMsg({ type: 'warning', text: 'Sedang menghapus cache & menarik data baru...' });
    try {
      const res = await dashboardService.clearCache();
      setStatusMsg({ type: res.status === 'error' ? 'error' : 'success', text: res.message || 'Cache Berhasil Dihapus & Re-synced' });
      if (onSyncSuccess) {
        await onSyncSuccess();
      }
    } catch (err) {
      setStatusMsg({ type: 'error', text: 'Gagal menghapus cache & re-sync.' });
    } finally {
      setClearingCache(false);
      setTimeout(() => setStatusMsg(null), 6000);
    }
  };

  const isBusy = loading || clearingCache;

  return (
    <div className="relative inline-flex items-center space-x-2" ref={dropdownRef}>
      {statusMsg && (
        <div className={`flex items-center space-x-1.5 text-xs px-3 py-1.5 rounded-lg border font-medium shadow-sm ${
          statusMsg.type === 'success'
            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
            : statusMsg.type === 'warning'
            ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
            : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
        }`}>
          {statusMsg.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : statusMsg.type === 'warning' ? <RefreshCw className="w-4 h-4 animate-spin text-amber-400" /> : <AlertCircle className="w-4 h-4" />}
          <span>{statusMsg.text}</span>
        </div>
      )}

      {/* Main Dropdown Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isBusy}
        className="flex items-center space-x-1.5 bg-gradient-to-r from-slate-800 to-slate-900 hover:from-slate-700 hover:to-slate-800 text-slate-200 border border-slate-700/80 hover:border-sky-500/50 font-semibold text-xs px-3 py-1.5 rounded-xl shadow-md transition-all cursor-pointer disabled:opacity-50 shrink-0"
      >
        <Zap className={`w-3.5 h-3.5 ${isBusy ? 'text-amber-400 animate-pulse' : 'text-sky-400'}`} />
        <span>{loading ? 'Syncing...' : clearingCache ? 'Clearing...' : 'Actions'}</span>
        <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform duration-200 ${isOpen ? 'rotate-180 text-sky-400' : ''}`} />
      </button>

      {/* Dropdown Menu Overlay */}
      {isOpen && (
        <div className="absolute right-0 top-full mt-2 w-64 max-w-[calc(100vw-32px)] bg-slate-900/95 backdrop-blur-md border border-slate-700/80 rounded-2xl shadow-2xl z-50 p-2 space-y-1 animate-in fade-in slide-in-from-top-2 duration-150">
          <div className="px-3 py-1.5 text-[10px] font-bold tracking-wider uppercase text-slate-400 border-b border-slate-800/80 mb-1">
            Data Maintenance
          </div>

          <button
            onClick={handleSync}
            disabled={isBusy}
            className="w-full flex items-start space-x-3 px-3 py-2.5 rounded-xl hover:bg-sky-500/10 hover:border-sky-500/30 border border-transparent text-left transition-all group cursor-pointer"
          >
            <div className="p-1.5 rounded-lg bg-sky-500/10 text-sky-400 group-hover:bg-sky-500/20 group-hover:scale-110 transition-all mt-0.5">
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </div>
            <div>
              <div className="text-xs font-bold text-slate-200 group-hover:text-sky-300">Sync Data</div>
              <div className="text-[10px] text-slate-400">Tarik data API terbaru GAM & Google Ads</div>
            </div>
          </button>

          <button
            onClick={handleClearCache}
            disabled={isBusy}
            className="w-full flex items-start space-x-3 px-3 py-2.5 rounded-xl hover:bg-rose-500/10 hover:border-rose-500/30 border border-transparent text-left transition-all group cursor-pointer"
          >
            <div className="p-1.5 rounded-lg bg-rose-500/10 text-rose-400 group-hover:bg-rose-500/20 group-hover:scale-110 transition-all mt-0.5">
              <Trash2 className={`w-4 h-4 ${clearingCache ? 'animate-spin' : ''}`} />
            </div>
            <div>
              <div className="text-xs font-bold text-slate-200 group-hover:text-rose-300">Clear Cache & Re-sync</div>
              <div className="text-[10px] text-slate-400">Hapus cache database & muat ulang data</div>
            </div>
          </button>
        </div>
      )}
    </div>
  );
}
