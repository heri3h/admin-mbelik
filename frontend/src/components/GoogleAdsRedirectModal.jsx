import React, { useState, useEffect } from 'react';
import { X, ExternalLink, ShieldCheck, Wallet, Globe, Check, Copy, UserCheck, Layers } from 'lucide-react';

export default function GoogleAdsRedirectModal({
  isOpen,
  onClose,
  customerId,
  domain,
  balance,
  mccId = '440-015-1880'
}) {
  const [authUser, setAuthUser] = useState(() => {
    try {
      return localStorage.getItem('gads_authuser_idx') || '0';
    } catch (e) {
      return '0';
    }
  });

  const [useMcc, setUseMcc] = useState(() => {
    try {
      const saved = localStorage.getItem('gads_use_mcc');
      return saved !== null ? saved === 'true' : true;
    } catch (e) {
      return true;
    }
  });

  const [copied, setCopied] = useState(false);

  const cleanCid = customerId ? String(customerId).replace(/\D/g, '') : '';
  const cleanMcc = mccId ? String(mccId).replace(/\D/g, '') : '4400151880';

  const targetUrl = useMcc && cleanMcc
    ? `https://ads.google.com/aw/campaigns?ocid=${cleanMcc}&__c=${cleanCid}&authuser=${authUser}`
    : `https://ads.google.com/aw/campaigns?ocid=${cleanCid}&authuser=${authUser}`;

  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === 'Enter') {
        handleProceed();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, targetUrl]);

  if (!isOpen || !customerId) return null;

  const hasBal = balance !== null && balance !== undefined && !isNaN(balance);
  const balNum = Number(balance);
  const isCritical = hasBal && balNum <= 0;
  const isLow = hasBal && balNum < 30000;

  const handleSelectAuthUser = (idx) => {
    setAuthUser(idx);
    try {
      localStorage.setItem('gads_authuser_idx', idx);
    } catch (e) {}
  };

  const handleToggleMcc = (val) => {
    setUseMcc(val);
    try {
      localStorage.setItem('gads_use_mcc', String(val));
    } catch (e) {}
  };

  const handleCopyUrl = () => {
    navigator.clipboard.writeText(targetUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleProceed = () => {
    window.open(targetUrl, '_blank', 'noopener,noreferrer');
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn">
      <div 
        className="bg-slate-900 border border-slate-700/80 rounded-2xl max-w-lg w-full shadow-2xl overflow-hidden flex flex-col transform transition-all"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 bg-sky-500/10 rounded-xl text-sky-400 border border-sky-500/20">
              <ExternalLink className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-white text-base">Buka Google Ads Campaigns</h3>
              <p className="text-xs text-slate-400">Direct deep-link ke daftar kampanye akun</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl transition-colors cursor-pointer"
            title="Tutup (Esc)"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-4">
          {/* Account Card Detail */}
          <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-3.5 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">Customer ID Target:</span>
              <span className="text-sm font-mono font-bold text-sky-300 bg-sky-500/10 px-2 py-0.5 rounded border border-sky-500/20">
                {customerId}
              </span>
            </div>

            {domain && (
              <div className="flex items-center justify-between border-t border-slate-800/80 pt-2">
                <span className="text-xs text-slate-400 flex items-center gap-1.5">
                  <Globe className="w-3.5 h-3.5 text-slate-400" />
                  Domain Terkait:
                </span>
                <span className="text-xs font-semibold text-slate-200">
                  {domain}
                </span>
              </div>
            )}

            {hasBal && (
              <div className="flex items-center justify-between border-t border-slate-800/80 pt-2">
                <span className="text-xs text-slate-400 flex items-center gap-1.5">
                  <Wallet className="w-3.5 h-3.5 text-slate-400" />
                  Sisa Saldo:
                </span>
                <span className={`text-xs font-semibold ${isCritical ? 'text-rose-400' : isLow ? 'text-amber-400' : 'text-emerald-400'}`}>
                  Rp {Math.round(balNum).toLocaleString('id-ID')}
                </span>
              </div>
            )}
          </div>

          {/* Setting 1: Bypass Google Account Chooser */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-medium text-slate-300 flex items-center gap-1.5">
                <UserCheck className="w-3.5 h-3.5 text-sky-400" />
                <span>Pilih Profil Login Google (Bypass Akun Google):</span>
              </label>
              <span className="text-[10px] text-slate-500">Tersimpan otomatis</span>
            </div>
            <div className="grid grid-cols-3 gap-2">
              {[
                { idx: '0', label: 'Akun 1 (Default)' },
                { idx: '1', label: 'Akun 2' },
                { idx: '2', label: 'Akun 3' }
              ].map((opt) => (
                <button
                  key={opt.idx}
                  type="button"
                  onClick={() => handleSelectAuthUser(opt.idx)}
                  className={`px-2.5 py-1.5 text-xs font-medium rounded-lg border transition-all text-center cursor-pointer ${
                    authUser === opt.idx
                      ? 'bg-sky-500/20 border-sky-500 text-sky-300 font-semibold shadow-sm'
                      : 'bg-slate-800/50 border-slate-700/60 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
            <p className="text-[11px] text-slate-400">
              Pilih profil Google yang aktif memiliki akses ke Google Ads ini agar tidak muncul layar <em>"Pilih Akun Google"</em>.
            </p>
          </div>

          {/* Setting 2: Hierarchy / Context Mode */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-slate-300 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-sky-400" />
              <span>Hierarki Akun Google Ads:</span>
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => handleToggleMcc(true)}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition-all text-left cursor-pointer ${
                  useMcc
                    ? 'bg-sky-500/20 border-sky-500 text-sky-300 font-semibold shadow-sm'
                    : 'bg-slate-800/50 border-slate-700/60 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                <div>Lewat MCC ({mccId})</div>
                <div className="text-[10px] font-normal opacity-75">Disarankan (Sub-akun)</div>
              </button>
              <button
                type="button"
                onClick={() => handleToggleMcc(false)}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition-all text-left cursor-pointer ${
                  !useMcc
                    ? 'bg-sky-500/20 border-sky-500 text-sky-300 font-semibold shadow-sm'
                    : 'bg-slate-800/50 border-slate-700/60 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                <div>Akses Langsung</div>
                <div className="text-[10px] font-normal opacity-75">Standalone Account</div>
              </button>
            </div>
          </div>

          {/* URL Live Preview & Copy */}
          <div className="space-y-1">
            <div className="flex items-center justify-between text-[11px] text-slate-400">
              <span>URL Target:</span>
              <button
                type="button"
                onClick={handleCopyUrl}
                className="text-sky-400 hover:text-sky-300 inline-flex items-center gap-1 cursor-pointer"
              >
                {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                <span>{copied ? 'Tersalin!' : 'Salin URL'}</span>
              </button>
            </div>
            <div className="bg-slate-950 border border-slate-800 rounded-lg p-2 text-[11px] font-mono text-slate-300 break-all select-all">
              {targetUrl}
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 bg-slate-950/50 border-t border-slate-800 flex items-center justify-between">
          <span className="text-[11px] text-slate-500 hidden sm:inline">
            Tekan <kbd className="px-1.5 py-0.5 bg-slate-800 border border-slate-700 rounded text-slate-300 text-[10px] font-mono">Enter</kbd> untuk buka, <kbd className="px-1.5 py-0.5 bg-slate-800 border border-slate-700 rounded text-slate-300 text-[10px] font-mono">Esc</kbd> untuk batal
          </span>
          <div className="flex items-center space-x-3 ml-auto">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl transition-colors cursor-pointer"
            >
              Batal
            </button>
            <button
              type="button"
              onClick={handleProceed}
              className="px-4 py-2 text-xs font-semibold text-white bg-sky-600 hover:bg-sky-500 rounded-xl transition-all shadow-lg shadow-sky-600/20 inline-flex items-center space-x-1.5 cursor-pointer"
            >
              <span>Buka Google Ads</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
