import React, { useState, useEffect } from 'react';
import { X, Save, Plus, Trash2, RotateCcw, AlertCircle, CheckCircle2, RefreshCw, Sliders } from 'lucide-react';
import { dashboardService } from '../services/api';

const DEFAULT_RULES = [
  { cpm: 5000,   target_key: '5000',   floor_key: 'f4000' },
  { cpm: 7500,   target_key: '7500',   floor_key: 'f7000' },
  { cpm: 10000,  target_key: '10000',  floor_key: 'f9000' },
  { cpm: 12500,  target_key: '12500',  floor_key: 'f12000' },
  { cpm: 15000,  target_key: '15000',  floor_key: 'f15000' },
  { cpm: 17500,  target_key: '17500',  floor_key: 'f17000' },
  { cpm: 20000,  target_key: '20000',  floor_key: 'f20000' },
  { cpm: 22500,  target_key: '22500',  floor_key: 'f23000' },
  { cpm: 25000,  target_key: '25000',  floor_key: 'f25000' },
  { cpm: 30000,  target_key: '30000',  floor_key: 'f27000' },
  { cpm: 35000,  target_key: '35000',  floor_key: 'f30000' },
  { cpm: 40000,  target_key: '40000',  floor_key: 'f35000' },
  { cpm: 45000,  target_key: '45000',  floor_key: 'f40000' },
  { cpm: 50000,  target_key: '50000',  floor_key: 'f45000' },
  { cpm: 55000,  target_key: '55000',  floor_key: 'f50000' },
  { cpm: 60000,  target_key: '60000',  floor_key: 'f55000' },
  { cpm: 65000,  target_key: '65000',  floor_key: 'f60000' },
  { cpm: 70000,  target_key: '70000',  floor_key: 'f60000' },
  { cpm: 75000,  target_key: '75000',  floor_key: 'f60000' },
  { cpm: 80000,  target_key: '80000',  floor_key: 'f60000' },
  { cpm: 100000, target_key: '100000', floor_key: 'f60000' },
  { cpm: 130000, target_key: '130000', floor_key: 'f60000' },
  { cpm: 155000, target_key: '155000', floor_key: 'f60000' }
];

export default function PricingConfigModal({ isOpen, onClose }) {
  const [targetMr, setTargetMr] = useState(65.0);
  const [defaultPricing, setDefaultPricing] = useState('google_optimize');
  const [rules, setRules] = useState(DEFAULT_RULES);

  // Dynamic adjustments state
  const [adjustments, setAdjustments] = useState({
    high_mr_threshold: 85.0,
    high_mr_boost_pct: 25.0,
    med_mr_threshold: 70.0,
    med_mr_boost_pct: 10.0,
    low_mr_threshold: 50.0,
    low_mr_penalty_pct: -15.0
  });

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [syncedPaths, setSyncedPaths] = useState([]);

  // New rule input state
  const [newCpm, setNewCpm] = useState('');
  const [newTargetKey, setNewTargetKey] = useState('');
  const [newFloorKey, setNewFloorKey] = useState('');

  useEffect(() => {
    if (isOpen) {
      fetchConfig();
    }
  }, [isOpen]);

  const fetchConfig = async () => {
    setLoading(true);
    setError('');
    setSuccessMsg('');
    try {
      const data = await dashboardService.getPricingConfig();
      if (data) {
        if (data.target_mr !== undefined) setTargetMr(data.target_mr);
        if (data.default_pricing !== undefined) setDefaultPricing(data.default_pricing);
        if (data.adjustments) {
          setAdjustments({
            high_mr_threshold: data.adjustments.high_mr_threshold ?? 85.0,
            high_mr_boost_pct: data.adjustments.high_mr_boost_pct ?? 25.0,
            med_mr_threshold: data.adjustments.med_mr_threshold ?? 70.0,
            med_mr_boost_pct: data.adjustments.med_mr_boost_pct ?? 10.0,
            low_mr_threshold: data.adjustments.low_mr_threshold ?? 50.0,
            low_mr_penalty_pct: data.adjustments.low_mr_penalty_pct ?? -15.0
          });
        }
        if (Array.isArray(data.rules) && data.rules.length > 0) {
          const sorted = [...data.rules].sort((a, b) => a.cpm - b.cpm);
          setRules(sorted);
        }
      }
    } catch (err) {
      console.error('Failed to load pricing config:', err);
      setError('Failed to load current pricing configuration.');
    } finally {
      setLoading(false);
    }
  };

  const handleCpmChangeForNew = (val) => {
    setNewCpm(val);
    const num = parseInt(val, 10);
    if (!isNaN(num) && num > 0) {
      if (!newTargetKey || newTargetKey === '' || newTargetKey === String(num)) {
        setNewTargetKey(String(num));
      }
      if (!newFloorKey || newFloorKey === '' || newFloorKey.startsWith('f')) {
        const floorEst = Math.max(1000, Math.floor(num * 0.8 / 1000) * 1000);
        setNewFloorKey(`f${floorEst}`);
      }
    }
  };

  const handleAddRule = (e) => {
    e.preventDefault();
    const cpmNum = parseInt(newCpm, 10);
    if (isNaN(cpmNum) || cpmNum <= 0) {
      setError('Valid CPM number is required.');
      return;
    }
    const tKey = newTargetKey.trim() || String(cpmNum);
    const fKey = newFloorKey.trim() || `f${cpmNum}`;

    const exists = rules.some(r => r.cpm === cpmNum);
    if (exists) {
      setError(`Rule for CPM ${cpmNum} already exists.`);
      return;
    }

    const updated = [...rules, { cpm: cpmNum, target_key: tKey, floor_key: fKey }].sort((a, b) => a.cpm - b.cpm);
    setRules(updated);
    setNewCpm('');
    setNewTargetKey('');
    setNewFloorKey('');
    setError('');
  };

  const handleDeleteRule = (cpmToDelete) => {
    setRules(rules.filter(r => r.cpm !== cpmToDelete));
  };

  const handleRuleChange = (index, field, value) => {
    const updated = [...rules];
    if (field === 'cpm') {
      const val = parseInt(value, 10);
      updated[index].cpm = isNaN(val) ? 0 : val;
    } else {
      updated[index][field] = value;
    }
    setRules(updated);
  };

  const handleResetDefaults = () => {
    if (window.confirm('Reset pricing rules to system defaults?')) {
      setTargetMr(65.0);
      setDefaultPricing('google_optimize');
      setRules(DEFAULT_RULES);
      setError('');
      setSuccessMsg('');
    }
  };

  const handleSaveConfig = async () => {
    setSaving(true);
    setError('');
    setSuccessMsg('');
    setSyncedPaths([]);

    const payload = {
      target_mr: parseFloat(targetMr) || 65.0,
      default_pricing: defaultPricing.trim() || 'google_optimize',
      adjustments: {
        high_mr_threshold: parseFloat(adjustments.high_mr_threshold) || 85.0,
        high_mr_boost_pct: parseFloat(adjustments.high_mr_boost_pct) || 25.0,
        med_mr_threshold: parseFloat(adjustments.med_mr_threshold) || 70.0,
        med_mr_boost_pct: parseFloat(adjustments.med_mr_boost_pct) || 10.0,
        low_mr_threshold: parseFloat(adjustments.low_mr_threshold) || 50.0,
        low_mr_penalty_pct: parseFloat(adjustments.low_mr_penalty_pct) || -15.0
      },
      rules: rules.map(r => ({
        cpm: parseInt(r.cpm, 10),
        target_key: String(r.target_key).trim(),
        floor_key: String(r.floor_key).trim()
      })).sort((a, b) => a.cpm - b.cpm)
    };

    try {
      const res = await dashboardService.savePricingConfig(payload);
      setSuccessMsg(res.message || 'Pricing configuration saved successfully!');
      if (res.synced_paths) {
        setSyncedPaths(res.synced_paths);
      }
    } catch (err) {
      console.error('Failed saving pricing config:', err);
      setError(err.response?.data?.detail || 'Failed to save and sync pricing config.');
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm overflow-y-auto animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl max-w-3xl w-full p-6 shadow-2xl space-y-6 my-8 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-700/60 shrink-0">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-sky-500/10 text-sky-400 rounded-xl border border-sky-500/20">
              <Sliders className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-extrabold text-white tracking-tight">GAM Auto Pricing Rules & Central Config</h2>
              <p className="text-slate-400 text-xs mt-0.5">Edit CPM threshold rules, target match rate, and default fallback pricing across all sites</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto pr-1 space-y-6">
          {loading ? (
            <div className="py-12 text-center text-slate-400">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-sky-400" />
              <span>Loading pricing rules configuration...</span>
            </div>
          ) : (
            <>
              {error && (
                <div className="p-3.5 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-400 text-xs flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              {successMsg && (
                <div className="p-3.5 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 text-xs space-y-2">
                  <div className="flex items-center space-x-2 font-semibold">
                    <CheckCircle2 className="w-4 h-4 shrink-0" />
                    <span>{successMsg}</span>
                  </div>
                  {syncedPaths.length > 0 && (
                    <div className="pt-2 border-t border-emerald-500/20 text-[11px] text-emerald-300">
                      <span className="font-semibold">Synced Files ({syncedPaths.length}):</span>
                      <ul className="mt-1 space-y-0.5 font-mono text-[10px] text-emerald-200">
                        {syncedPaths.map((p, i) => (
                          <li key={i}>✓ {p}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Central Settings */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-slate-800/60 p-4 rounded-xl border border-slate-700/60">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                    Target Match Rate (Target MR %)
                  </label>
                  <div className="relative">
                    <input
                      type="number"
                      step="0.1"
                      min="1"
                      max="100"
                      value={targetMr}
                      onChange={(e) => setTargetMr(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white font-mono font-bold focus:outline-none focus:border-sky-500"
                    />
                    <span className="absolute right-3 top-2.5 text-xs text-slate-400 font-bold">%</span>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1">Default target match rate used for pricing rule calculations</p>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                    Default Fallback Pricing
                  </label>
                  <input
                    type="text"
                    value={defaultPricing}
                    onChange={(e) => setDefaultPricing(e.target.value)}
                    placeholder="e.g. google_optimize"
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white font-mono font-semibold focus:outline-none focus:border-sky-500"
                  />
                  <p className="text-[11px] text-slate-500 mt-1">Fallback rule name when pricing match fails or falls back to Google GAM default</p>
                </div>
              </div>

              {/* Dynamic CPM Adjustments Section */}
              <div className="bg-slate-800/60 p-4 rounded-xl border border-slate-700/60 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-sky-400 uppercase tracking-wider flex items-center gap-1.5">
                    <Sliders className="w-4 h-4" />
                    <span>Dynamic CPM Auto-Adjustments (%)</span>
                  </h3>
                  <span className="text-[11px] text-slate-400">Read by Client Adsheader Engine</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-700/50 space-y-2">
                    <span className="text-[11px] font-bold text-emerald-400 block">High Demand Tier</span>
                    <div>
                      <label className="block text-[10px] text-slate-400 mb-0.5">MR Threshold (≥ %)</label>
                      <input
                        type="number"
                        step="0.5"
                        value={adjustments.high_mr_threshold}
                        onChange={(e) => setAdjustments({ ...adjustments, high_mr_threshold: parseFloat(e.target.value) || 0 })}
                        className="w-full px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-white font-mono font-bold focus:outline-none focus:border-emerald-500"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] text-slate-400 mb-0.5">CPM Boost (+ %)</label>
                      <input
                        type="number"
                        step="0.5"
                        value={adjustments.high_mr_boost_pct}
                        onChange={(e) => setAdjustments({ ...adjustments, high_mr_boost_pct: parseFloat(e.target.value) || 0 })}
                        className="w-full px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-emerald-400 font-mono font-bold focus:outline-none focus:border-emerald-500"
                      />
                    </div>
                  </div>

                  <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-700/50 space-y-2">
                    <span className="text-[11px] font-bold text-sky-400 block">Medium Demand Tier</span>
                    <div>
                      <label className="block text-[10px] text-slate-400 mb-0.5">MR Threshold (≥ %)</label>
                      <input
                        type="number"
                        step="0.5"
                        value={adjustments.med_mr_threshold}
                        onChange={(e) => setAdjustments({ ...adjustments, med_mr_threshold: parseFloat(e.target.value) || 0 })}
                        className="w-full px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-white font-mono font-bold focus:outline-none focus:border-sky-500"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] text-slate-400 mb-0.5">CPM Boost (+ %)</label>
                      <input
                        type="number"
                        step="0.5"
                        value={adjustments.med_mr_boost_pct}
                        onChange={(e) => setAdjustments({ ...adjustments, med_mr_boost_pct: parseFloat(e.target.value) || 0 })}
                        className="w-full px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-sky-400 font-mono font-bold focus:outline-none focus:border-sky-500"
                      />
                    </div>
                  </div>

                  <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-700/50 space-y-2">
                    <span className="text-[11px] font-bold text-amber-400 block">Low Demand Tier</span>
                    <div>
                      <label className="block text-[10px] text-slate-400 mb-0.5">MR Threshold (&lt; %)</label>
                      <input
                        type="number"
                        step="0.5"
                        value={adjustments.low_mr_threshold}
                        onChange={(e) => setAdjustments({ ...adjustments, low_mr_threshold: parseFloat(e.target.value) || 0 })}
                        className="w-full px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-white font-mono font-bold focus:outline-none focus:border-amber-500"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] text-slate-400 mb-0.5">CPM Penalty (- %)</label>
                      <input
                        type="number"
                        step="0.5"
                        value={adjustments.low_mr_penalty_pct}
                        onChange={(e) => setAdjustments({ ...adjustments, low_mr_penalty_pct: parseFloat(e.target.value) || 0 })}
                        className="w-full px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-amber-400 font-mono font-bold focus:outline-none focus:border-amber-500"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Add New Rule Form */}
              <form onSubmit={handleAddRule} className="bg-slate-800/40 p-4 rounded-xl border border-slate-700/50 space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-sky-400 uppercase tracking-wider flex items-center gap-1.5">
                    <Plus className="w-4 h-4" />
                    <span>Add New Pricing Threshold Rule</span>
                  </h4>
                  <span className="text-[11px] text-slate-400">{rules.length} Active Rules</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <label className="block text-[11px] font-medium text-slate-400 mb-1">Target CPM (IDR)</label>
                    <input
                      type="number"
                      placeholder="e.g. 90000"
                      value={newCpm}
                      onChange={(e) => handleCpmChangeForNew(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white font-mono focus:outline-none focus:border-sky-500"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-medium text-slate-400 mb-1">Target Key</label>
                    <input
                      type="text"
                      placeholder="e.g. 90000"
                      value={newTargetKey}
                      onChange={(e) => setNewTargetKey(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white font-mono focus:outline-none focus:border-sky-500"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-medium text-slate-400 mb-1">Floor Key</label>
                    <input
                      type="text"
                      placeholder="e.g. f60000"
                      value={newFloorKey}
                      onChange={(e) => setNewFloorKey(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white font-mono focus:outline-none focus:border-sky-500"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs rounded-lg shadow transition-all flex items-center gap-1.5"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add Rule</span>
                </button>
              </form>

              {/* Rules Table */}
              <div className="border border-slate-700/60 rounded-xl overflow-hidden shadow-sm">
                <div className="overflow-x-auto max-h-72">
                  <table className="w-full text-left text-xs text-slate-300">
                    <thead className="bg-slate-900/90 sticky top-0 z-10 text-[10px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-700/60">
                      <tr>
                        <th className="px-4 py-3 text-center">#</th>
                        <th className="px-4 py-3">CPM Threshold (IDR)</th>
                        <th className="px-4 py-3">Target Key</th>
                        <th className="px-4 py-3">Floor Key</th>
                        <th className="px-4 py-3 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-700/40 bg-slate-900/40">
                      {rules.length > 0 ? (
                        rules.map((rule, idx) => (
                          <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                            <td className="px-4 py-2 text-center text-slate-500 font-mono text-[11px]">{idx + 1}</td>
                            <td className="px-4 py-2">
                              <input
                                type="number"
                                value={rule.cpm}
                                onChange={(e) => handleRuleChange(idx, 'cpm', e.target.value)}
                                className="w-28 px-2 py-1 bg-slate-900 border border-slate-700 rounded text-xs text-white font-mono font-semibold focus:outline-none focus:border-sky-500"
                              />
                            </td>
                            <td className="px-4 py-2">
                              <input
                                type="text"
                                value={rule.target_key}
                                onChange={(e) => handleRuleChange(idx, 'target_key', e.target.value)}
                                className="w-28 px-2 py-1 bg-slate-900 border border-slate-700 rounded text-xs text-sky-400 font-mono focus:outline-none focus:border-sky-500"
                              />
                            </td>
                            <td className="px-4 py-2">
                              <input
                                type="text"
                                value={rule.floor_key}
                                onChange={(e) => handleRuleChange(idx, 'floor_key', e.target.value)}
                                className="w-28 px-2 py-1 bg-slate-900 border border-slate-700 rounded text-xs text-amber-400 font-mono focus:outline-none focus:border-sky-500"
                              />
                            </td>
                            <td className="px-4 py-2 text-right">
                              <button
                                onClick={() => handleDeleteRule(rule.cpm)}
                                className="p-1.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 rounded-lg transition-all border border-rose-500/30"
                                title="Delete Rule"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan="5" className="px-4 py-6 text-center text-slate-500 italic">
                            No rules defined. Click 'Reset Defaults' or add a rule above.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-slate-700/60 shrink-0">
          <button
            onClick={handleResetDefaults}
            disabled={saving}
            className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs rounded-xl border border-slate-700 transition-all flex items-center space-x-1.5 disabled:opacity-50"
          >
            <RotateCcw className="w-3.5 h-3.5 text-amber-400" />
            <span>Reset Defaults</span>
          </button>

          <div className="flex items-center space-x-3">
            <button
              onClick={onClose}
              disabled={saving}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs rounded-xl transition-all disabled:opacity-50"
            >
              Cancel
            </button>

            <button
              onClick={handleSaveConfig}
              disabled={saving || loading}
              className="px-5 py-2 bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-sky-600/20 transition-all flex items-center space-x-2 disabled:opacity-50"
            >
              {saving ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin text-white" />
                  <span>Saving & Syncing All Sites...</span>
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 text-white" />
                  <span>Save & Overwrite All Sites</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
