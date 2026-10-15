import React, { useEffect } from 'react';
import { X, ExternalLink, ShieldCheck, Wallet, Globe } from 'lucide-react';

export default function GoogleAdsRedirectModal({
  isOpen,
  onClose,
  customerId,
  domain,
  balance
}) {
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
  }, [isOpen, customerId]);

  if (!isOpen || !customerId) return null;

  const cleanCid = String(customerId).replace(/\D/g, '');
  const targetUrl = `https://ads.google.com/aw/campaigns?__c=${cleanCid}`;

  const hasBal = balance !== null && balance !== undefined && !isNaN(balance);
  const balNum = Number(balance);
  const isCritical = hasBal && balNum <= 0;
  const isLow = hasBal && balNum < 30000;

  const handleProceed = () => {
    window.open(targetUrl, '_blank', 'noopener,noreferrer');
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn">
      <div 
        className="bg-slate-900 border border-slate-700/80 rounded-2xl max-w-md w-full shadow-2xl overflow-hidden flex flex-col transform transition-all"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 bg-sky-500/10 rounded-xl text-sky-400 border border-sky-500/20">
              <ExternalLink className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-white text-base">Buka Google Ads</h3>
              <p className="text-xs text-slate-400">Konfirmasi pengalihan ke tab baru</p>
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
          <p className="text-xs text-slate-300 leading-relaxed">
            Anda akan dialihkan ke halaman <span className="font-semibold text-sky-400">Daftar Kampanye</span> pada akun Google Ads berikut:
          </p>

          {/* Account Card Detail */}
          <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">Customer ID:</span>
              <span className="text-sm font-mono font-bold text-sky-300 bg-sky-500/10 px-2 py-0.5 rounded border border-sky-500/20">
                {customerId}
              </span>
            </div>

            {domain && (
              <div className="flex items-center justify-between border-t border-slate-800/80 pt-2.5">
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
              <div className="flex items-center justify-between border-t border-slate-800/80 pt-2.5">
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

          {/* Informational Tip */}
          <div className="flex items-start space-x-2.5 p-3 rounded-xl bg-slate-800/40 border border-slate-700/50 text-[11px] text-slate-400">
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <span className="leading-normal">
              Pastikan browser Anda sudah login ke akun Google yang memiliki hak akses (atau akun MCC Pengelola) ke ID ini.
            </span>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 bg-slate-950/50 border-t border-slate-800 flex items-center justify-end space-x-3">
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
  );
}
