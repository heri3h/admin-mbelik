import React from 'react';
import { DollarSign, TrendingUp, TrendingDown, Award, CreditCard, ArrowUpRight, ArrowDownRight } from 'lucide-react';

export default function SummaryCards({ data }) {
  if (!data) return null;

  const formatCurrency = (val) => {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR',
      maximumFractionDigits: 0
    }).format(val || 0);
  };

  const isProfitable = data.net_profit >= 0;
  const compLabel = data.comparison_period_label || 'vs kemarin';

  const renderDeltaBadge = (pct, label, invertColors = false) => {
    if (pct === undefined || pct === null) return null;
    const isUp = pct > 0;
    const isDown = pct < 0;

    let colorClass = 'text-slate-400 bg-slate-700/40 border-slate-600';
    if (isUp) {
      colorClass = invertColors
        ? 'text-rose-400 bg-rose-500/10 border-rose-500/30'
        : 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
    } else if (isDown) {
      colorClass = invertColors
        ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30'
        : 'text-rose-400 bg-rose-500/10 border-rose-500/30';
    }

    return (
      <span className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded-md text-[11px] font-semibold border ${colorClass}`} title={`${label}`}>
        {isUp && <ArrowUpRight className="w-3 h-3 shrink-0" />}
        {isDown && <ArrowDownRight className="w-3 h-3 shrink-0" />}
        <span>{isUp ? `+${pct}%` : `${pct}%`}</span>
      </span>
    );
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
      {/* Total Spend */}
      <div className="bg-slate-800 border border-slate-700/60 p-5 rounded-2xl shadow-sm hover:border-slate-600 transition-colors">
        <div className="flex items-center justify-between">
          <span className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Total Spend (Google Ads)</span>
          <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-xl border border-indigo-500/20">
            <CreditCard className="w-5 h-5" />
          </div>
        </div>
        <div className="mt-3">
          <div className="flex items-baseline justify-between gap-2">
            <h3 className="text-2xl font-extrabold text-white tracking-tight">{formatCurrency(data.total_spend)}</h3>
            {renderDeltaBadge(data.spend_change_pct, compLabel, true)}
          </div>
          <p className="text-slate-400 text-[11px] mt-1 flex items-center justify-between">
            <span>Google Ads Total Cost</span>
            <span className="text-slate-500 text-[10px] italic">{compLabel}</span>
          </p>
        </div>
      </div>

      {/* Total Revenue */}
      <div className="bg-slate-800 border border-slate-700/60 p-5 rounded-2xl shadow-sm hover:border-slate-600 transition-colors">
        <div className="flex items-center justify-between">
          <span className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Total Revenue (AdX)</span>
          <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-xl border border-emerald-500/20">
            <DollarSign className="w-5 h-5" />
          </div>
        </div>
        <div className="mt-3">
          <div className="flex items-baseline justify-between gap-2">
            <h3 className="text-2xl font-extrabold text-white tracking-tight">{formatCurrency(data.total_revenue)}</h3>
            {renderDeltaBadge(data.revenue_change_pct, compLabel, false)}
          </div>
          <p className="text-slate-400 text-[11px] mt-1 flex items-center justify-between">
            <span>Google Ad Manager Earnings</span>
            <span className="text-slate-500 text-[10px] italic">{compLabel}</span>
          </p>
        </div>
      </div>

      {/* Net Profit */}
      <div className={`bg-slate-800 border p-5 rounded-2xl shadow-sm transition-colors ${
        isProfitable
          ? 'border-emerald-500/40 bg-gradient-to-b from-slate-800 to-emerald-950/20'
          : 'border-rose-500/40 bg-gradient-to-b from-slate-800 to-rose-950/20'
      }`}>
        <div className="flex items-center justify-between">
          <span className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Net Profit</span>
          <div className={`p-2 rounded-xl border ${
            isProfitable
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
              : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
          }`}>
            {isProfitable ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
          </div>
        </div>
        <div className="mt-3">
          <div className="flex items-baseline justify-between gap-2">
            <h3 className={`text-2xl font-extrabold tracking-tight ${
              isProfitable ? 'text-emerald-400' : 'text-rose-400'
            }`}>
              {formatCurrency(data.net_profit)}
            </h3>
            {renderDeltaBadge(data.profit_change_pct, compLabel, false)}
          </div>
          <p className="text-slate-400 text-[11px] mt-1 flex items-center justify-between">
            <span>Revenue - Spend</span>
            <span className="text-slate-500 text-[10px] italic">{compLabel}</span>
          </p>
        </div>
      </div>

      {/* ROI & Margin */}
      <div className="bg-slate-800 border border-slate-700/60 p-5 rounded-2xl shadow-sm hover:border-slate-600 transition-colors">
        <div className="flex items-center justify-between">
          <span className="text-slate-400 text-xs font-semibold uppercase tracking-wider">ROAS / ROI & Margin</span>
          <div className="p-2 bg-sky-500/10 text-sky-400 rounded-xl border border-sky-500/20">
            <Award className="w-5 h-5" />
          </div>
        </div>
        <div className="mt-3 grid grid-cols-2 gap-2">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400 font-medium">ROAS / ROI</span>
              {renderDeltaBadge(data.roi_change_pct, compLabel, false)}
            </div>
            <p className="text-lg font-bold text-sky-400 mt-0.5">{data.roi}%</p>
          </div>
          <div>
            <span className="text-xs text-slate-400 font-medium">Profit Margin</span>
            <p className={`text-lg font-bold mt-0.5 ${isProfitable ? 'text-emerald-400' : 'text-rose-400'}`}>
              {data.profit_margin}%
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

