import React, { useState, useEffect } from 'react';
import { X, ExternalLink, ShieldCheck, Wallet, Globe, Check, Link as LinkIcon } from 'lucide-react';

const SHARED_MCC_C = '5549233089';
const SHARED_USER_ID = '3429262417';
const DEFAULT_AUTHUSER = '0';

// Known account OCID mappings
const BUILTIN_OCID_MAPPINGS = {
  // 'enew' (324-608-5080)
  '324-608-5080': '1353856964',
  '3246085080': '1353856964',

  // 'glee' (808-296-3952)
  '808-296-3952': '1295632265',
  '8082963952': '1295632265',
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

  const [mccC, setMccC] = useState(() => {
    try {
      return localStorage.getItem('gads_mcc_c') || SHARED_MCC_C;
    } catch (e) {
      return SHARED_MCC_C;
    }
  });

  const [userId, setUserId] = useState(() => {
    try {
      return localStorage.getItem('gads_mcc_userid') || SHARED_USER_ID;
    } catch (e) {
      return SHARED_USER_ID;
    }
  });

  const [authUser, setAuthUser] = useState(() => {
    try {
      return localStorage.getItem('gads_authuser_idx') || DEFAULT_AUTHUSER;
    } catch (e) {
      return DEFAULT_AUTHUSER;
    }
  });

  const [accountOcid, setAccountOcid] = useState('');
  const [showConfig, setShowConfig] = useState(false);
  const [pasteInput, setPasteInput] = useState('');
  const [pasteSuccess, setPasteSuccess] = useState(false);

  useEffect(() => {
    if (!customerId) return;
    try {
      const savedMappings = JSON.parse(localStorage.getItem('gads_ocid_mappings') || '{}');
      const found = savedMappings[formattedCid] || savedMappings[cleanCid] || BUILTIN_OCID_MAPPINGS[formattedCid] || BUILTIN_OCID_MAPPINGS[cleanCid] || '';
      setAccountOcid(found);
    } catch (e) {
      const found = BUILTIN_OCID_MAPPINGS[formattedCid] || BUILTIN_OCID_MAPPINGS[cleanCid] || '';
      setAccountOcid(found);
    }
    setPasteInput('');
    setPasteSuccess(false);
    setShowConfig(false);
  }, [customerId, isOpen]);

  // If specific OCID is known for this account, deep link with MCC context and account OCID
  // Otherwise, fallback directly to Customer ID ocid
  const targetUrl = accountOcid
    ? `https://ads.google.com/aw/campaigns?ocid=${accountOcid}&ascid=${accountOcid}&authuser=${authUser}&__u=${userId}&__c=${mccC}`
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

  const handlePasteAnalyze = (e) => {
    const raw = e.target.value;
    setPasteInput(raw);
    if (!raw || !raw.includes('ads.google.com')) return;

    try {
      const urlObj = new URL(raw.trim());
      const p = urlObj.searchParams;

      const extractedOcid = p.get('ocid');
      const extractedU = p.get('__u');
      const extractedAuth = p.get('authuser');
      const extractedC = p.get('__c');

      if (extractedOcid) {
        setAccountOcid(extractedOcid);
        const saved = JSON.parse(localStorage.getItem('gads_ocid_mappings') || '{}');
        saved[formattedCid] = extractedOcid;
        saved[cleanCid] = extractedOcid;
        localStorage.setItem('gads_ocid_mappings', JSON.stringify(saved));
      }
      if (extractedU) {
        setUserId(extractedU);
        localStorage.setItem('gads_mcc_userid', extractedU);
      }
      if (extractedC) {
        setMccC(extractedC);
        localStorage.setItem('gads_mcc_c', extractedC);
      }
      if (extractedAuth) {
        setAuthUser(extractedAuth);
        localStorage.setItem('gads_authuser_idx', extractedAuth);
      }

      setPasteSuccess(true);
      setTimeout(() => setPasteSuccess(false), 3000);
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
              <h3 className="font-bold text-white text-base">Open Google Ads</h3>
              <p className="text-xs text-slate-400">Confirm redirect to account campaigns</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl transition-colors cursor-pointer"
            title="Close (Esc)"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-4">
          <p className="text-xs text-slate-300 leading-relaxed">
            You will be redirected to the <span className="font-semibold text-sky-400">Campaigns</span> page for the following Google Ads account:
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
                  Associated Domain:
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
                  Remaining Balance:
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
              Direct deep-link is active. Ensure your browser is logged into your Google Ads Manager account.
            </span>
          </div>

          {/* Optional Quick Link Setup Helper */}
          <div>
            <button
              type="button"
              onClick={() => setShowConfig(!showConfig)}
              className="text-[11px] text-slate-500 hover:text-slate-300 underline underline-offset-2 transition-colors cursor-pointer"
            >
              {showConfig ? 'Hide link settings' : 'Custom link settings'}
            </button>

            {showConfig && (
              <div className="mt-2 p-3 bg-slate-950/70 border border-slate-800 rounded-xl space-y-2 text-xs animate-fadeIn">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-slate-400 flex items-center gap-1">
                    <LinkIcon className="w-3 h-3 text-sky-400" />
                    Paste URL from MCC (auto-saves for this account):
                  </span>
                  {pasteSuccess && (
                    <span className="text-[10px] text-emerald-400 font-semibold flex items-center gap-0.5">
                      <Check className="w-3 h-3" /> Saved!
                    </span>
                  )}
                </div>
                <input
                  type="text"
                  placeholder="Paste URL from Google Ads MCC browser..."
                  value={pasteInput}
                  onChange={handlePasteAnalyze}
                  className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1 text-xs text-slate-200 font-mono focus:outline-none focus:border-sky-500"
                />
              </div>
            )}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 bg-slate-950/50 border-t border-slate-800 flex items-center justify-between">
          <span className="text-[11px] text-slate-500 hidden sm:inline">
            Press <kbd className="px-1.5 py-0.5 bg-slate-800 border border-slate-700 rounded text-slate-300 text-[10px] font-mono">Enter</kbd> to open, <kbd className="px-1.5 py-0.5 bg-slate-800 border border-slate-700 rounded text-slate-300 text-[10px] font-mono">Esc</kbd> to cancel
          </span>
          <div className="flex items-center space-x-3 ml-auto">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-xl transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleProceed}
              className="px-4 py-2 text-xs font-semibold text-white bg-sky-600 hover:bg-sky-500 rounded-xl transition-all shadow-lg shadow-sky-600/20 inline-flex items-center space-x-1.5 cursor-pointer"
            >
              <span>Open Google Ads</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
