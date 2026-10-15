import React, { useState, useEffect } from 'react';
import { X, ExternalLink, Wallet, Globe, Check, Copy, UserCheck, Layers, Link as LinkIcon, Sparkles } from 'lucide-react';

const DEFAULT_OCID = '1353856964';
const DEFAULT_USER_ID = '3429262417';
const DEFAULT_AUTHUSER = '0';

// Known initial account mappings
const BUILTIN_C_MAPPINGS = {
  '255-105-1790': '5549233089',
  '2551051790': '5549233089'
};

export default function GoogleAdsRedirectModal({
  isOpen,
  onClose,
  customerId,
  domain,
  balance,
  mccId = '440-015-1880'
}) {
  const cleanCid = customerId ? String(customerId).replace(/\D/g, '') : '';
  const formattedCid = customerId ? String(customerId).trim() : '';

  // Load persistent configurations
  const [ocid, setOcid] = useState(() => {
    try {
      return localStorage.getItem('gads_mcc_ocid') || DEFAULT_OCID;
    } catch (e) {
      return DEFAULT_OCID;
    }
  });

  const [userId, setUserId] = useState(() => {
    try {
      return localStorage.getItem('gads_mcc_userid') || DEFAULT_USER_ID;
    } catch (e) {
      return DEFAULT_USER_ID;
    }
  });

  const [authUser, setAuthUser] = useState(() => {
    try {
      return localStorage.getItem('gads_authuser_idx') || DEFAULT_AUTHUSER;
    } catch (e) {
      return DEFAULT_AUTHUSER;
    }
  });

  // Local storage mapping for customer_id -> internal __c
  const [internalC, setInternalC] = useState('');
  const [pasteInput, setPasteInput] = useState('');
  const [pasteSuccess, setPasteSuccess] = useState(false);
  const [copied, setCopied] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Sync internal __c when modal opens with a customerId
  useEffect(() => {
    if (!customerId) return;
    try {
      const savedMappings = JSON.parse(localStorage.getItem('gads_c_mappings') || '{}');
      const found = savedMappings[formattedCid] || savedMappings[cleanCid] || BUILTIN_C_MAPPINGS[formattedCid] || BUILTIN_C_MAPPINGS[cleanCid] || '';
      setInternalC(found);
    } catch (e) {
      const found = BUILTIN_C_MAPPINGS[formattedCid] || BUILTIN_C_MAPPINGS[cleanCid] || '';
      setInternalC(found);
    }
    setPasteInput('');
    setPasteSuccess(false);
  }, [customerId, isOpen]);

  // Target URL computation
  // If internal __c is available, deep-link straight to campaigns!
  // If not, open the MCC overview page with the verified session tokens so it skips Google login.
  const targetUrl = internalC
    ? `https://ads.google.com/aw/campaigns?ocid=${ocid}&ascid=${ocid}&authuser=${authUser}&__u=${userId}&__c=${internalC}`
    : `https://ads.google.com/aw/overview?ocid=${ocid}&ascid=${ocid}&authuser=${authUser}&__u=${userId}`;

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

  const handleCopyUrl = () => {
    navigator.clipboard.writeText(targetUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleInternalCChange = (newVal) => {
    const val = String(newVal).trim();
    setInternalC(val);
    try {
      const saved = JSON.parse(localStorage.getItem('gads_c_mappings') || '{}');
      saved[formattedCid] = val;
      saved[cleanCid] = val;
      localStorage.setItem('gads_c_mappings', JSON.stringify(saved));
    } catch (e) {}
  };

  const handlePasteAnalyze = (e) => {
    const raw = e.target.value;
    setPasteInput(raw);
    if (!raw || !raw.includes('ads.google.com')) return;

    try {
      const urlObj = new URL(raw.trim());
      const p = urlObj.searchParams;

      let extractedC = p.get('__c');
      let extractedOcid = p.get('ocid');
      let extractedU = p.get('__u');
      let extractedAuth = p.get('authuser');

      if (extractedOcid) {
        setOcid(extractedOcid);
        localStorage.setItem('gads_mcc_ocid', extractedOcid);
      }
      if (extractedU) {
        setUserId(extractedU);
        localStorage.setItem('gads_mcc_userid', extractedU);
      }
      if (extractedAuth) {
        setAuthUser(extractedAuth);
        localStorage.setItem('gads_authuser_idx', extractedAuth);
      }
      if (extractedC) {
        handleInternalCChange(extractedC);
      }

      setPasteSuccess(true);
      setTimeout(() => setPasteSuccess(false), 3500);
    } catch (err) {
      console.warn('Could not parse Google Ads URL', err);
    }
  };

  const handleProceed = () => {
    window.open(targetUrl, '_blank');
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn">
      <div 
        className="bg-slate-900 border border-slate-700/80 rounded-2xl max-w-lg w-full shadow-2xl overflow-hidden flex flex-col transform transition-all max-h-[90vh]"
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
              <p className="text-xs text-slate-400">Direct Link bypass login & account chooser</p>
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
        <div className="p-6 space-y-4 overflow-y-auto">
          {/* Account Card Detail */}
          <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-3.5 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">Customer ID:</span>
              <div className="flex items-center gap-2">
                <span className="text-sm font-mono font-bold text-sky-300 bg-sky-500/10 px-2 py-0.5 rounded border border-sky-500/20">
                  {customerId}
                </span>
                {internalC ? (
                  <span
                    title={`Internal Child ID Google: ${internalC}`}
                    className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.5 rounded flex items-center gap-1"
                  >
                    <Check className="w-2.5 h-2.5" />
                    <span>Direct Camp. Ready</span>
                  </span>
                ) : (
                  <span
                    title="Akan membuka halaman MCC tanpa layar login"
                    className="text-[10px] text-amber-400 bg-amber-500/10 border border-amber-500/20 px-1.5 py-0.5 rounded"
                  >
                    Via MCC
                  </span>
                )}
              </div>
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

          {/* Quick Notice */}
          <div className="p-3 bg-sky-500/10 border border-sky-500/20 rounded-xl text-xs text-sky-200 leading-relaxed flex items-start gap-2.5">
            <Sparkles className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />
            <div>
              {internalC ? (
                <span>
                  Tautan ini otomatis menggunakan parameter sesi internal MCC (<code className="font-mono text-white bg-slate-800 px-1 py-0.5 rounded">ocid={ocid}</code> dan <code className="font-mono text-white bg-slate-800 px-1 py-0.5 rounded">__c={internalC}</code>) agar <strong>langsung membuka halaman kampanye akun ini</strong> tanpa meminta pilih akun.
                </span>
              ) : (
                <span>
                  Akun ini akan dibuka langsung via sesi MCC Anda tanpa meminta login Google. Anda juga dapat menempelkan link akun ini dari MCC di bawah agar klik berikutnya langsung menuju kampanyenya.
                </span>
              )}
            </div>
          </div>

          {/* Setting: Profil Akun Google (authuser) */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-medium text-slate-300 flex items-center gap-1.5">
                <UserCheck className="w-3.5 h-3.5 text-sky-400" />
                <span>Profil Akun Google:</span>
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
          </div>

          {/* Quick Paste / Auto-configure Helper */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-medium text-slate-300 flex items-center gap-1.5">
                <LinkIcon className="w-3.5 h-3.5 text-sky-400" />
                <span>Tempel Link dari MCC (Otomatis Deteksi):</span>
              </label>
              {pasteSuccess && (
                <span className="text-[11px] font-semibold text-emerald-400 flex items-center gap-1">
                  <Check className="w-3 h-3" /> Berhasil disimpan!
                </span>
              )}
            </div>
            <input
              type="text"
              placeholder="Tempel link URL dari Google Ads MCC browser di sini..."
              value={pasteInput}
              onChange={handlePasteAnalyze}
              className="w-full bg-slate-950 border border-slate-800 focus:border-sky-500 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-600 focus:outline-none font-mono"
            />
          </div>

          {/* Advanced Details Toggle */}
          <div className="pt-1">
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="text-[11px] text-slate-400 hover:text-sky-300 underline underline-offset-2 transition-colors cursor-pointer"
            >
              {showAdvanced ? 'Sembunyikan Pengaturan Parameter' : 'Tampilkan Pengaturan Parameter Internal (__c, ocid, __u)'}
            </button>

            {showAdvanced && (
              <div className="mt-2.5 p-3 bg-slate-950/70 border border-slate-800 rounded-xl space-y-2.5 text-xs animate-fadeIn">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-[10px] text-slate-400 block mb-1">Internal Child ID (__c):</label>
                    <input
                      type="text"
                      value={internalC}
                      onChange={(e) => handleInternalCChange(e.target.value)}
                      placeholder="e.g. 5549233089"
                      className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-sky-300 font-mono focus:outline-none focus:border-sky-500"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-slate-400 block mb-1">User Session (__u):</label>
                    <input
                      type="text"
                      value={userId}
                      onChange={(e) => {
                        setUserId(e.target.value);
                        localStorage.setItem('gads_mcc_userid', e.target.value);
                      }}
                      className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200 font-mono focus:outline-none focus:border-sky-500"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-[10px] text-slate-400 block mb-1">MCC Organization ID (ocid):</label>
                  <input
                    type="text"
                    value={ocid}
                    onChange={(e) => {
                      setOcid(e.target.value);
                      localStorage.setItem('gads_mcc_ocid', e.target.value);
                    }}
                    className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200 font-mono focus:outline-none focus:border-sky-500"
                  />
                </div>
              </div>
            )}
          </div>

          {/* URL Live Preview & Copy */}
          <div className="space-y-1">
            <div className="flex items-center justify-between text-[11px] text-slate-400">
              <span>URL Target yang akan dibuka:</span>
              <button
                type="button"
                onClick={handleCopyUrl}
                className="text-sky-400 hover:text-sky-300 inline-flex items-center gap-1 cursor-pointer"
              >
                {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                <span>{copied ? 'Tersalin!' : 'Salin URL'}</span>
              </button>
            </div>
            <div className="bg-slate-950 border border-slate-800 rounded-lg p-2 text-[11px] font-mono text-slate-300 break-all select-all leading-normal">
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
