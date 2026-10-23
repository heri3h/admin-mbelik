import React, { useState, useEffect, useMemo } from 'react';
import { X, Check, Loader2, Smartphone, Monitor, Shield, Target, Zap, Percent, AlertCircle, Sparkles } from 'lucide-react';
import { dashboardService } from '../services/api';

const domainRulesCache = {};

export const PRICING_FLOOR_OPTIONS = [
  { key: 'f4000', label: 'Rp 4.000', code: 'f4000' },
  { key: 'f7000', label: 'Rp 7.000', code: 'f7000' },
  { key: 'f9000', label: 'Rp 9.000', code: 'f9000' },
  { key: 'f12000', label: 'Rp 12.000', code: 'f12000' },
  { key: 'f15000', label: 'Rp 15.000', code: 'f15000' },
  { key: 'f17000', label: 'Rp 17.000', code: 'f17000' },
  { key: 'f20000', label: 'Rp 20.000', code: 'f20000' },
  { key: 'f23000', label: 'Rp 23.000', code: 'f23000' },
  { key: 'f25000', label: 'Rp 25.000', code: 'f25000' },
  { key: 'f27000', label: 'Rp 27.000', code: 'f27000' },
  { key: 'f30000', label: 'Rp 30.000', code: 'f30000' },
  { key: 'f35000', label: 'Rp 35.000', code: 'f35000' },
  { key: 'f40000', label: 'Rp 40.000', code: 'f40000' },
  { key: 'f45000', label: 'Rp 45.000', code: 'f45000' },
  { key: 'f50000', label: 'Rp 50.000', code: 'f50000' },
  { key: 'f55000', label: 'Rp 55.000', code: 'f55000' },
  { key: 'f60000', label: 'Rp 60.000', code: 'f60000' },
  { key: 'f65000', label: 'Rp 65.000', code: 'f65000' },
  { key: 'f70000', label: 'Rp 70.000', code: 'f70000' },
  { key: 'f75000', label: 'Rp 75.000', code: 'f75000' },
  { key: 'f80000', label: 'Rp 80.000', code: 'f80000' },
  { key: 'f100000', label: 'Rp 100.000', code: 'f100000' },
  { key: 'f125000', label: 'Rp 125.000', code: 'f125000' },
  { key: 'f140000', label: 'Rp 140.000', code: 'f140000' },
  { key: 'f160000', label: 'Rp 160.000', code: 'f160000' },
  { key: 'f190000', label: 'Rp 190.000', code: 'f190000' },
  { key: 'f230000', label: 'Rp 230.000', code: 'f230000' },
  { key: 'f280000', label: 'Rp 280.000', code: 'f280000' },
  { key: 'f340000', label: 'Rp 340.000', code: 'f340000' },
  { key: 'f420000', label: 'Rp 420.000', code: 'f420000' },
  { key: 'f480000', label: 'Rp 480.000', code: 'f480000' },
  { key: 'f560000', label: 'Rp 560.000', code: 'f560000' },
  { key: 'f680000', label: 'Rp 680.000', code: 'f680000' },
  { key: 'f800000', label: 'Rp 800.000', code: 'f800000' },
];

export const PRICING_TARGET_OPTIONS = [
  { key: '5000', label: 'Rp 5.000', code: '5000' },
  { key: '7500', label: 'Rp 7.500', code: '7500' },
  { key: '10000', label: 'Rp 10.000', code: '10000' },
  { key: '12500', label: 'Rp 12.500', code: '12500' },
  { key: '15000', label: 'Rp 15.000', code: '15000' },
  { key: '17500', label: 'Rp 17.500', code: '17500' },
  { key: '20000', label: 'Rp 20.000', code: '20000' },
  { key: '22500', label: 'Rp 22.500', code: '22500' },
  { key: '25000', label: 'Rp 25.000', code: '25000' },
  { key: '30000', label: 'Rp 30.000', code: '30000' },
  { key: '35000', label: 'Rp 35.000', code: '35000' },
  { key: '40000', label: 'Rp 40.000', code: '40000' },
  { key: '45000', label: 'Rp 45.000', code: '45000' },
  { key: '50000', label: 'Rp 50.000', code: '50000' },
  { key: '55000', label: 'Rp 55.000', code: '55000' },
  { key: '60000', label: 'Rp 60.000', code: '60000' },
  { key: '65000', label: 'Rp 65.000', code: '65000' },
  { key: '70000', label: 'Rp 70.000', code: '70000' },
  { key: '75000', label: 'Rp 75.000', code: '75000' },
  { key: '80000', label: 'Rp 80.000', code: '80000' },
  { key: '100000', label: 'Rp 100.000', code: '100000' },
  { key: '130000', label: 'Rp 130.000', code: '130000' },
  { key: '155000', label: 'Rp 155.000', code: '155000' },
  { key: '175000', label: 'Rp 175.000', code: '175000' },
  { key: '200000', label: 'Rp 200.000', code: '200000' },
  { key: '240000', label: 'Rp 240.000', code: '240000' },
  { key: '290000', label: 'Rp 290.000', code: '290000' },
  { key: '350000', label: 'Rp 350.000', code: '350000' },
  { key: '430000', label: 'Rp 430.000', code: '430000' },
  { key: '525000', label: 'Rp 525.000', code: '525000' },
  { key: '600000', label: 'Rp 600.000', code: '600000' },
  { key: '700000', label: 'Rp 700.000', code: '700000' },
  { key: '850000', label: 'Rp 850.000', code: '850000' },
  { key: '1000000', label: 'Rp 1.000.000', code: '1000000' },
];

export const PRICING_MR_OPTIONS = [
  { value: 50.0, label: '50% (Match Rate Rendah - Aggressive Floor)' },
  { value: 55.0, label: '55% (Match Rate Sedang-Rendah)' },
  { value: 60.0, label: '60% (Match Rate Sedang)' },
  { value: 65.0, label: '65% (Standar Target MR)' },
  { value: 70.0, label: '70% (Match Rate Cukup Tinggi)' },
  { value: 75.0, label: '75% (Match Rate Tinggi - Safe Fill)' },
  { value: 80.0, label: '80% (Match Rate Sangat Tinggi)' },
  { value: 85.0, label: '85% (Maksimal Fill Rate)' },
];

export default function AdUnitPricingOverrideModal({
  isOpen,
  onClose,
  domain,
  country,
  adUnitItem,
  onSaved,
}) {
  const [mobileMode, setMobileMode] = useState('auto');
  const [mobileFloorKey, setMobileFloorKey] = useState('f15000');
  const [mobileTargetKey, setMobileTargetKey] = useState('15000');
  const [mobileMr, setMobileMr] = useState(65.0);

  const [desktopMode, setDesktopMode] = useState('auto');
  const [desktopFloorKey, setDesktopFloorKey] = useState('f20000');
  const [desktopTargetKey, setDesktopTargetKey] = useState('20000');
  const [desktopMr, setDesktopMr] = useState(65.0);

  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  // Dynamic pricing rules state
  const [rules, setRules] = useState(() => (domain && domainRulesCache[domain]) || []);
  const [loadingRules, setLoadingRules] = useState(false);

  useEffect(() => {
    if (!isOpen || !domain) return;
    if (domainRulesCache[domain] && domainRulesCache[domain].length > 0) {
      setRules(domainRulesCache[domain]);
      return;
    }
    let isMounted = true;
    setLoadingRules(true);
    dashboardService.getSitePricingRules(domain)
      .then((res) => {
        if (!isMounted) return;
        if (res && Array.isArray(res.rules) && res.rules.length > 0) {
          domainRulesCache[domain] = res.rules;
          setRules(res.rules);
        }
      })
      .catch((err) => {
        console.warn('Failed fetching dynamic pricing rules for', domain, err);
      })
      .finally(() => {
        if (isMounted) setLoadingRules(false);
      });
    return () => {
      isMounted = false;
    };
  }, [isOpen, domain]);

  // Dynamically resolve Target CPM options
  const targetOptions = useMemo(() => {
    let list = [];
    if (rules && rules.length > 0) {
      list = rules.map((r) => {
        const cpmNum = Number(r.cpm) || parseInt(String(r.target_key).replace(/\D/g, ''), 10) || 0;
        return {
          key: String(r.target_key),
          label: `Rp ${cpmNum.toLocaleString('id-ID')}`,
          code: String(r.target_key),
        };
      });
    } else {
      list = [...PRICING_TARGET_OPTIONS];
    }

    // Ensure selected keys are included even if not in rules
    const ensureKey = (k) => {
      if (k && !list.some((o) => o.key === String(k))) {
        const numMatch = String(k).match(/\d+/);
        const val = numMatch ? parseInt(numMatch[0], 10) : k;
        list.push({
          key: String(k),
          label: `Rp ${Number(val).toLocaleString('id-ID')}`,
          code: String(k),
        });
      }
    };
    ensureKey(mobileTargetKey);
    ensureKey(desktopTargetKey);
    return list;
  }, [rules, mobileTargetKey, desktopTargetKey]);

  // Dynamically resolve Floor options
  const floorOptions = useMemo(() => {
    let list = [];
    if (rules && rules.length > 0) {
      list = rules
        .filter((r) => r.floor_key)
        .map((r) => {
          const numMatch = String(r.floor_key).match(/\d+/);
          const floorNum = numMatch ? parseInt(numMatch[0], 10) : (Number(r.cpm) || 0);
          return {
            key: String(r.floor_key),
            label: `Rp ${floorNum.toLocaleString('id-ID')}`,
            code: String(r.floor_key),
          };
        });
    } else {
      list = [...PRICING_FLOOR_OPTIONS];
    }

    // Ensure selected keys are included even if not in rules
    const ensureKey = (k) => {
      if (k && !list.some((o) => o.key === String(k))) {
        const numMatch = String(k).match(/\d+/);
        const val = numMatch ? parseInt(numMatch[0], 10) : k;
        list.push({
          key: String(k),
          label: `Rp ${Number(val).toLocaleString('id-ID')}`,
          code: String(k),
        });
      }
    };
    ensureKey(mobileFloorKey);
    ensureKey(desktopFloorKey);
    return list;
  }, [rules, mobileFloorKey, desktopFloorKey]);

  useEffect(() => {
    if (!isOpen || !adUnitItem) return;

    // Initialize Mobile state
    const mob = adUnitItem.mobile_override;
    if (mob && mob.pricing_mode) {
      setMobileMode(mob.pricing_mode);
      if (mob.pricing_mode === 'target_floor') {
        setMobileFloorKey(mob.target_floor_key || 'f15000');
      } else if (mob.pricing_mode === 'target_cpm') {
        setMobileTargetKey(mob.target_key || (mob.target_cpm ? String(mob.target_cpm) : '15000'));
      } else if (mob.pricing_mode === 'target_mr') {
        setMobileMr(mob.target_mr || 65.0);
      }
    } else {
      setMobileMode('auto');
      setMobileFloorKey('f15000');
      setMobileTargetKey('15000');
      setMobileMr(65.0);
    }

    // Initialize Desktop state
    const desk = adUnitItem.desktop_override;
    if (desk && desk.pricing_mode) {
      setDesktopMode(desk.pricing_mode);
      if (desk.pricing_mode === 'target_floor') {
        setDesktopFloorKey(desk.target_floor_key || 'f20000');
      } else if (desk.pricing_mode === 'target_cpm') {
        setDesktopTargetKey(desk.target_key || (desk.target_cpm ? String(desk.target_cpm) : '20000'));
      } else if (desk.pricing_mode === 'target_mr') {
        setDesktopMr(desk.target_mr || 65.0);
      }
    } else {
      setDesktopMode('auto');
      setDesktopFloorKey('f20000');
      setDesktopTargetKey('20000');
      setDesktopMr(65.0);
    }

    setSavedSuccess(false);
    setErrorMsg(null);
  }, [isOpen, adUnitItem]);

  if (!isOpen || !adUnitItem) return null;

  const handleSave = async () => {
    setSaving(true);
    setErrorMsg(null);
    try {
      const cc = country?.country_code || 'ALL';
      const unit = adUnitItem.ad_unit;

      // Prepare Mobile Payload
      const mobFloor = mobileMode === 'target_floor' ? mobileFloorKey : null;
      const mobTarget = mobileMode === 'target_cpm' ? mobileTargetKey : null;
      const mobCpm = mobileMode === 'target_cpm' && mobTarget ? parseInt(mobTarget, 10) : null;
      const mobMrVal = mobileMode === 'target_mr' ? mobileMr : null;

      // Prepare Desktop Payload
      const deskFloor = desktopMode === 'target_floor' ? desktopFloorKey : null;
      const deskTarget = desktopMode === 'target_cpm' ? desktopTargetKey : null;
      const deskCpm = desktopMode === 'target_cpm' && deskTarget ? parseInt(deskTarget, 10) : null;
      const deskMrVal = desktopMode === 'target_mr' ? desktopMr : null;

      const [mobRes, deskRes] = await Promise.all([
        dashboardService.setPricingOverride({
          domain,
          country_code: cc,
          device_category: 'mobile',
          ad_unit: unit,
          pricing_mode: mobileMode,
          target_floor_key: mobFloor,
          target_key: mobTarget,
          target_cpm: mobCpm,
          target_mr: mobMrVal,
        }),
        dashboardService.setPricingOverride({
          domain,
          country_code: cc,
          device_category: 'desktop',
          ad_unit: unit,
          pricing_mode: desktopMode,
          target_floor_key: deskFloor,
          target_key: deskTarget,
          target_cpm: deskCpm,
          target_mr: deskMrVal,
        }),
      ]);

      setSavedSuccess(true);
      if (onSaved) {
        onSaved({
          adUnit: unit,
          mobileOverride: mobRes.override,
          desktopOverride: deskRes.override,
        });
      }
      setTimeout(() => {
        onClose();
      }, 700);
    } catch (err) {
      console.error('Failed to save override config', err);
      setErrorMsg('Gagal menyimpan perubahan. Pastikan koneksi aman dan coba lagi.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-3 sm:p-6 bg-slate-950/85 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl w-full max-w-3xl overflow-hidden flex flex-col max-h-[95vh]">
        {/* Header */}
        <div className="p-4 sm:p-5 border-b border-slate-700/70 bg-slate-900/90 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <span>Atur CPM Override Ad Unit</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                  {domain}
                </span>
              </h3>
              <p className="text-xs text-slate-400 mt-0.5 flex items-center gap-1.5">
                <span>Negara:</span>
                <span className="text-sm">{country?.flag_emoji}</span>
                <span className="font-semibold text-slate-200">{country?.country} ({country?.country_code})</span>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-4 sm:p-6 space-y-5 overflow-y-auto">
          {/* Ad Unit Info Box */}
          <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <span className="text-[10px] text-slate-400 uppercase font-semibold tracking-wider">Ad Unit Placement</span>
              <p className="font-mono text-sm font-bold text-slate-100">{adUnitItem.ad_unit}</p>
            </div>
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <div className="bg-slate-800/80 px-2.5 py-1 rounded-lg border border-slate-700/60">
                <span className="text-slate-400 text-[10px] block">Format</span>
                <span className="font-semibold text-cyan-300">{adUnitItem.placement_format || 'Banner'}</span>
              </div>
              <div className="bg-slate-800/80 px-2.5 py-1 rounded-lg border border-slate-700/60">
                <span className="text-slate-400 text-[10px] block">eCPM Saat Ini</span>
                <span className="font-semibold text-sky-400">
                  {new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(adUnitItem.ecpm || 0)}
                </span>
              </div>
              <div className="bg-slate-800/80 px-2.5 py-1 rounded-lg border border-slate-700/60 flex items-center gap-1.5">
                {loadingRules ? (
                  <Loader2 className="w-3.5 h-3.5 text-indigo-400 animate-spin shrink-0" />
                ) : (
                  <Sparkles className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                )}
                <div>
                  <span className="text-slate-400 text-[10px] block">Tier Rules</span>
                  <span className="font-semibold text-indigo-300">
                    {loadingRules ? 'Memuat...' : `${targetOptions.length} Tiers (${domain})`}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {errorMsg && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl flex items-center space-x-2 text-rose-400 text-xs">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Two Columns: Mobile & Desktop */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* --- MOBILE COLUMN --- */}
            <div className="bg-slate-800/50 border border-slate-700/70 rounded-xl p-4 flex flex-col justify-between space-y-4">
              <div>
                <div className="flex items-center space-x-2 pb-2.5 border-b border-slate-700/50">
                  <Smartphone className="w-4 h-4 text-amber-400" />
                  <span className="font-bold text-sm text-slate-100">📱 Mobile Override</span>
                </div>

                <div className="space-y-3 mt-3">
                  {/* Option 1: Auto */}
                  <label
                    onClick={() => setMobileMode('auto')}
                    className={`flex items-start space-x-2.5 p-2.5 rounded-lg border cursor-pointer transition-all ${
                      mobileMode === 'auto'
                        ? 'bg-emerald-500/10 border-emerald-500/50 text-white'
                        : 'bg-slate-900/60 border-slate-700/60 text-slate-300 hover:border-slate-600'
                    }`}
                  >
                    <input
                      type="radio"
                      name="mobile_mode"
                      checked={mobileMode === 'auto'}
                      onChange={() => setMobileMode('auto')}
                      className="mt-0.5 text-emerald-500 focus:ring-0"
                    />
                    <div>
                      <div className="text-xs font-bold flex items-center gap-1.5">
                        <Zap className="w-3.5 h-3.5 text-emerald-400" />
                        <span>🟢 Auto (Cascade Bawaan)</span>
                      </div>
                      <p className="text-[10px] text-slate-400 mt-0.5">Mengikuti kalkulasi dinamis harian bawaan.</p>
                    </div>
                  </label>

                  {/* Option 2: Target CPM */}
                  <label
                    onClick={() => setMobileMode('target_cpm')}
                    className={`flex flex-col space-y-2 p-2.5 rounded-lg border cursor-pointer transition-all ${
                      mobileMode === 'target_cpm'
                        ? 'bg-sky-500/10 border-sky-500/50 text-white'
                        : 'bg-slate-900/60 border-slate-700/60 text-slate-300 hover:border-slate-600'
                    }`}
                  >
                    <div className="flex items-start space-x-2.5">
                      <input
                        type="radio"
                        name="mobile_mode"
                        checked={mobileMode === 'target_cpm'}
                        onChange={() => setMobileMode('target_cpm')}
                        className="mt-0.5 text-sky-500 focus:ring-0"
                      />
                      <div>
                        <div className="text-xs font-bold flex items-center gap-1.5">
                          <Target className="w-3.5 h-3.5 text-sky-400" />
                          <span>🔵 Target CPM</span>
                        </div>
                        <p className="text-[10px] text-slate-400 mt-0.5">Optimasi lelang di sekitar target CPM.</p>
                      </div>
                    </div>

                    {mobileMode === 'target_cpm' && (
                      <div className="pl-6 pt-1">
                        <span className="text-[10px] font-semibold text-sky-300 block mb-1">Pilih Nilai Target CPM:</span>
                        <select
                          value={mobileTargetKey}
                          onChange={(e) => setMobileTargetKey(e.target.value)}
                          className="w-full bg-slate-900 border border-sky-500/50 text-slate-100 text-xs font-mono rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-sky-400"
                        >
                          {targetOptions.map((opt) => (
                            <option key={opt.key} value={opt.key}>
                              {opt.label} ({opt.code})
                            </option>
                          ))}
                        </select>
                      </div>
                    )}
                  </label>

                  {/* Option 3: Target Floor */}
                  <label
                    onClick={() => setMobileMode('target_floor')}
                    className={`flex flex-col space-y-2 p-2.5 rounded-lg border cursor-pointer transition-all ${
                      mobileMode === 'target_floor'
                        ? 'bg-purple-500/10 border-purple-500/50 text-white'
                        : 'bg-slate-900/60 border-slate-700/60 text-slate-300 hover:border-slate-600'
                    }`}
                  >
                    <div className="flex items-start space-x-2.5">
                      <input
                        type="radio"
                        name="mobile_mode"
                        checked={mobileMode === 'target_floor'}
                        onChange={() => setMobileMode('target_floor')}
                        className="mt-0.5 text-purple-500 focus:ring-0"
                      />
                      <div>
                        <div className="text-xs font-bold flex items-center gap-1.5">
                          <Shield className="w-3.5 h-3.5 text-purple-400" />
                          <span>🟣 Target Floor (Hard Floor)</span>
                        </div>
                        <p className="text-[10px] text-slate-400 mt-0.5">Tolak lelang di bawah batas harga minimum.</p>
                      </div>
                    </div>

                    {mobileMode === 'target_floor' && (
                      <div className="pl-6 pt-1">
                        <span className="text-[10px] font-semibold text-purple-300 block mb-1">Pilih Nilai Hard Floor:</span>
                        <select
                          value={mobileFloorKey}
                          onChange={(e) => setMobileFloorKey(e.target.value)}
                          className="w-full bg-slate-900 border border-purple-500/50 text-slate-100 text-xs font-mono rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-purple-400"
                        >
                          {floorOptions.map((opt) => (
                            <option key={opt.key} value={opt.key}>
                              {opt.label} ({opt.code})
                            </option>
                          ))}
                        </select>
                      </div>
                    )}
                  </label>

                  {/* Option 4: Target MR */}
                  <label
                    onClick={() => setMobileMode('target_mr')}
                    className={`flex flex-col space-y-2 p-2.5 rounded-lg border cursor-pointer transition-all ${
                      mobileMode === 'target_mr'
                        ? 'bg-amber-500/10 border-amber-500/50 text-white'
                        : 'bg-slate-900/60 border-slate-700/60 text-slate-300 hover:border-slate-600'
                    }`}
                  >
                    <div className="flex items-start space-x-2.5">
                      <input
                        type="radio"
                        name="mobile_mode"
                        checked={mobileMode === 'target_mr'}
                        onChange={() => setMobileMode('target_mr')}
                        className="mt-0.5 text-amber-500 focus:ring-0"
                      />
                      <div>
                        <div className="text-xs font-bold flex items-center gap-1.5">
                          <Percent className="w-3.5 h-3.5 text-amber-400" />
                          <span>🟠 Target MR (Match Rate)</span>
                        </div>
                        <p className="text-[10px] text-slate-400 mt-0.5">Otomatis tentukan floor agar keterisian mencapai target MR.</p>
                      </div>
                    </div>

                    {mobileMode === 'target_mr' && (
                      <div className="pl-6 pt-1">
                        <span className="text-[10px] font-semibold text-amber-300 block mb-1">Pilih Target Match Rate:</span>
                        <select
                          value={mobileMr}
                          onChange={(e) => setMobileMr(parseFloat(e.target.value))}
                          className="w-full bg-slate-900 border border-amber-500/50 text-slate-100 text-xs font-mono rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-amber-400"
                        >
                          {PRICING_MR_OPTIONS.map((opt) => (
                            <option key={opt.value} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </select>
                      </div>
                    )}
                  </label>
                </div>
              </div>
            </div>

            {/* --- DESKTOP COLUMN --- */}
            <div className="bg-slate-800/50 border border-slate-700/70 rounded-xl p-4 flex flex-col justify-between space-y-4">
              <div>
                <div className="flex items-center space-x-2 pb-2.5 border-b border-slate-700/50">
                  <Monitor className="w-4 h-4 text-indigo-400" />
                  <span className="font-bold text-sm text-slate-100">💻 Desktop Override</span>
                </div>

                <div className="space-y-3 mt-3">
                  {/* Option 1: Auto */}
                  <label
                    onClick={() => setDesktopMode('auto')}
                    className={`flex items-start space-x-2.5 p-2.5 rounded-lg border cursor-pointer transition-all ${
                      desktopMode === 'auto'
                        ? 'bg-emerald-500/10 border-emerald-500/50 text-white'
                        : 'bg-slate-900/60 border-slate-700/60 text-slate-300 hover:border-slate-600'
                    }`}
                  >
                    <input
                      type="radio"
                      name="desktop_mode"
                      checked={desktopMode === 'auto'}
                      onChange={() => setDesktopMode('auto')}
                      className="mt-0.5 text-emerald-500 focus:ring-0"
                    />
                    <div>
                      <div className="text-xs font-bold flex items-center gap-1.5">
                        <Zap className="w-3.5 h-3.5 text-emerald-400" />
                        <span>🟢 Auto (Cascade Bawaan)</span>
                      </div>
                      <p className="text-[10px] text-slate-400 mt-0.5">Mengikuti kalkulasi dinamis harian bawaan.</p>
                    </div>
                  </label>

                  {/* Option 2: Target CPM */}
                  <label
                    onClick={() => setDesktopMode('target_cpm')}
                    className={`flex flex-col space-y-2 p-2.5 rounded-lg border cursor-pointer transition-all ${
                      desktopMode === 'target_cpm'
                        ? 'bg-sky-500/10 border-sky-500/50 text-white'
                        : 'bg-slate-900/60 border-slate-700/60 text-slate-300 hover:border-slate-600'
                    }`}
                  >
                    <div className="flex items-start space-x-2.5">
                      <input
                        type="radio"
                        name="desktop_mode"
                        checked={desktopMode === 'target_cpm'}
                        onChange={() => setDesktopMode('target_cpm')}
                        className="mt-0.5 text-sky-500 focus:ring-0"
                      />
                      <div>
                        <div className="text-xs font-bold flex items-center gap-1.5">
                          <Target className="w-3.5 h-3.5 text-sky-400" />
                          <span>🔵 Target CPM</span>
                        </div>
                        <p className="text-[10px] text-slate-400 mt-0.5">Optimasi lelang di sekitar target CPM.</p>
                      </div>
                    </div>

                    {desktopMode === 'target_cpm' && (
                      <div className="pl-6 pt-1">
                        <span className="text-[10px] font-semibold text-sky-300 block mb-1">Pilih Nilai Target CPM:</span>
                        <select
                          value={desktopTargetKey}
                          onChange={(e) => setDesktopTargetKey(e.target.value)}
                          className="w-full bg-slate-900 border border-sky-500/50 text-slate-100 text-xs font-mono rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-sky-400"
                        >
                          {targetOptions.map((opt) => (
                            <option key={opt.key} value={opt.key}>
                              {opt.label} ({opt.code})
                            </option>
                          ))}
                        </select>
                      </div>
                    )}
                  </label>

                  {/* Option 3: Target Floor */}
                  <label
                    onClick={() => setDesktopMode('target_floor')}
                    className={`flex flex-col space-y-2 p-2.5 rounded-lg border cursor-pointer transition-all ${
                      desktopMode === 'target_floor'
                        ? 'bg-purple-500/10 border-purple-500/50 text-white'
                        : 'bg-slate-900/60 border-slate-700/60 text-slate-300 hover:border-slate-600'
                    }`}
                  >
                    <div className="flex items-start space-x-2.5">
                      <input
                        type="radio"
                        name="desktop_mode"
                        checked={desktopMode === 'target_floor'}
                        onChange={() => setDesktopMode('target_floor')}
                        className="mt-0.5 text-purple-500 focus:ring-0"
                      />
                      <div>
                        <div className="text-xs font-bold flex items-center gap-1.5">
                          <Shield className="w-3.5 h-3.5 text-purple-400" />
                          <span>🟣 Target Floor (Hard Floor)</span>
                        </div>
                        <p className="text-[10px] text-slate-400 mt-0.5">Tolak lelang di bawah batas harga minimum.</p>
                      </div>
                    </div>

                    {desktopMode === 'target_floor' && (
                      <div className="pl-6 pt-1">
                        <span className="text-[10px] font-semibold text-purple-300 block mb-1">Pilih Nilai Hard Floor:</span>
                        <select
                          value={desktopFloorKey}
                          onChange={(e) => setDesktopFloorKey(e.target.value)}
                          className="w-full bg-slate-900 border border-purple-500/50 text-slate-100 text-xs font-mono rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-purple-400"
                        >
                          {floorOptions.map((opt) => (
                            <option key={opt.key} value={opt.key}>
                              {opt.label} ({opt.code})
                            </option>
                          ))}
                        </select>
                      </div>
                    )}
                  </label>

                  {/* Option 4: Target MR */}
                  <label
                    onClick={() => setDesktopMode('target_mr')}
                    className={`flex flex-col space-y-2 p-2.5 rounded-lg border cursor-pointer transition-all ${
                      desktopMode === 'target_mr'
                        ? 'bg-amber-500/10 border-amber-500/50 text-white'
                        : 'bg-slate-900/60 border-slate-700/60 text-slate-300 hover:border-slate-600'
                    }`}
                  >
                    <div className="flex items-start space-x-2.5">
                      <input
                        type="radio"
                        name="desktop_mode"
                        checked={desktopMode === 'target_mr'}
                        onChange={() => setDesktopMode('target_mr')}
                        className="mt-0.5 text-amber-500 focus:ring-0"
                      />
                      <div>
                        <div className="text-xs font-bold flex items-center gap-1.5">
                          <Percent className="w-3.5 h-3.5 text-amber-400" />
                          <span>🟠 Target MR (Match Rate)</span>
                        </div>
                        <p className="text-[10px] text-slate-400 mt-0.5">Otomatis tentukan floor agar keterisian mencapai target MR.</p>
                      </div>
                    </div>

                    {desktopMode === 'target_mr' && (
                      <div className="pl-6 pt-1">
                        <span className="text-[10px] font-semibold text-amber-300 block mb-1">Pilih Target Match Rate:</span>
                        <select
                          value={desktopMr}
                          onChange={(e) => setDesktopMr(parseFloat(e.target.value))}
                          className="w-full bg-slate-900 border border-amber-500/50 text-slate-100 text-xs font-mono rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-amber-400"
                        >
                          {PRICING_MR_OPTIONS.map((opt) => (
                            <option key={opt.value} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </select>
                      </div>
                    )}
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 sm:p-5 border-t border-slate-800 bg-slate-900 flex items-center justify-between gap-3">
          <span className="text-[11px] text-slate-400 hidden sm:inline">
            Sinkronisasi instan ke server <span className="font-mono text-emerald-400">current_pricing.json</span>
          </span>
          <div className="flex items-center space-x-2 ml-auto">
            <button
              type="button"
              onClick={onClose}
              disabled={saving}
              className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-all cursor-pointer"
            >
              Batal
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={saving}
              className="px-5 py-2 rounded-xl text-xs font-bold bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-950 shadow-md shadow-emerald-500/20 transition-all flex items-center space-x-1.5 cursor-pointer disabled:opacity-50"
            >
              {saving ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Menyimpan...</span>
                </>
              ) : savedSuccess ? (
                <>
                  <Check className="w-3.5 h-3.5" />
                  <span>Tersimpan!</span>
                </>
              ) : (
                <span>Simpan Pengaturan</span>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
