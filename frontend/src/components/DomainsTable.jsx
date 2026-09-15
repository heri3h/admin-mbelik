import React from 'react';
import { Globe } from 'lucide-react';

export default function DomainsTable({ domains }) {
  if (!domains || domains.length === 0) {
    return (
      <div className="bg-slate-800 border border-slate-700/60 p-6 rounded-2xl text-center text-slate-400 text-sm">
        No Ad Manager domain performance data available.
      </div>
    );
  }

  const formatCurrency = (val) => {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR',
      maximumFractionDigits: 0
    }).format(val || 0);
  };

  return (
    <div className="bg-slate-800 border border-slate-700/60 rounded-2xl shadow-sm">
      <div className="p-5 border-b border-slate-700/60 flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Globe className="w-5 h-5 text-emerald-400" />
            <span>GAM / AdX Domain Performance Breakdown</span>
          </h3>
          <p className="text-slate-400 text-xs mt-0.5">Ad Exchange earnings, eCPM, and ad impression breakdown per website</p>
        </div>
        <span className="text-xs font-semibold px-2.5 py-1 bg-slate-700 text-slate-300 rounded-lg">
          {domains.length} Active Domains
        </span>
      </div>

      <div className="overflow-x-auto w-full max-w-full rounded-b-2xl">
        <table className="w-full text-left text-xs text-slate-300 border-separate border-spacing-0">
          <thead className="bg-slate-900 text-slate-400 uppercase font-semibold text-[11px] tracking-wider select-none shadow-md">
            <tr>
              <th className="sticky top-16 z-30 bg-slate-900 px-5 py-3.5 border-b border-slate-700/60 whitespace-nowrap">Domain</th>
              <th className="sticky top-16 z-30 bg-slate-900 px-5 py-3.5 border-b border-slate-700/60 text-right whitespace-nowrap">AdX Revenue</th>
              <th className="sticky top-16 z-30 bg-slate-900 px-5 py-3.5 border-b border-slate-700/60 text-right whitespace-nowrap">AdX Impressions</th>
              <th className="sticky top-16 z-30 bg-slate-900 px-5 py-3.5 border-b border-slate-700/60 text-right whitespace-nowrap">Clicks</th>
              <th className="sticky top-16 z-30 bg-slate-900 px-5 py-3.5 border-b border-slate-700/60 text-right whitespace-nowrap">eCPM</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/50">
            {domains.map((dom, idx) => (
              <tr key={idx} className="hover:bg-slate-700/30 transition-colors">
                <td className="px-5 py-4 font-semibold text-white">
                  <div className="flex items-center space-x-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                    <span>{dom.domain}</span>
                  </div>
                </td>
                <td className="px-5 py-4 text-right font-bold text-emerald-400">
                  {formatCurrency(dom.total_revenue)}
                </td>
                <td className="px-5 py-4 text-right">{dom.impressions.toLocaleString()}</td>
                <td className="px-5 py-4 text-right">{dom.clicks.toLocaleString()}</td>
                <td className="px-5 py-4 text-right font-mono font-semibold text-sky-400">{formatCurrency(dom.ecpm)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
