import React, { useState } from 'react';
import { Globe } from 'lucide-react';
import ColumnToggleDropdown from './ColumnToggleDropdown';

const ALL_COLUMNS = [
  { key: 'domain', label: 'Domain' },
  { key: 'total_revenue', label: 'AdX Revenue' },
  { key: 'impressions', label: 'AdX Impressions' },
  { key: 'clicks', label: 'Clicks' },
  { key: 'ecpm', label: 'eCPM' },
];

export default function DomainsTable({ domains }) {
  const [visibleColumns, setVisibleColumns] = useState(
    ALL_COLUMNS.reduce((acc, col) => ({ ...acc, [col.key]: true }), {})
  );

  const handleToggleColumn = (key) => {
    setVisibleColumns(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleResetColumns = () => {
    setVisibleColumns(ALL_COLUMNS.reduce((acc, col) => ({ ...acc, [col.key]: true }), {}));
  };

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
      <div className="p-5 border-b border-slate-700/60 flex items-center justify-between gap-4">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Globe className="w-5 h-5 text-emerald-400" />
            <span>GAM / AdX Domain Performance Breakdown</span>
          </h3>
          <p className="text-slate-400 text-xs mt-0.5">Ad Exchange earnings, eCPM, and ad impression breakdown per website</p>
        </div>

        <div className="flex items-center space-x-3">
          <ColumnToggleDropdown
            columns={ALL_COLUMNS}
            visibleColumns={visibleColumns}
            onToggleColumn={handleToggleColumn}
            onResetColumns={handleResetColumns}
          />

          <span className="text-xs font-semibold px-2.5 py-1 bg-slate-700 text-slate-300 rounded-lg">
            {domains.length} Active Domains
          </span>
        </div>
      </div>

      <div className="overflow-auto max-h-[calc(100vh-220px)] min-h-[350px] w-full max-w-full rounded-b-2xl border-t border-slate-700/60">
        <table className="w-full text-left text-xs text-slate-300 border-separate border-spacing-0">
          <thead className="bg-slate-900 text-slate-400 uppercase font-semibold text-[10px] tracking-wider select-none shadow-md">
            <tr>
              {visibleColumns.domain && <th className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 leading-tight">Domain</th>}
              {visibleColumns.total_revenue && <th className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 text-right leading-tight">AdX<br/>Revenue</th>}
              {visibleColumns.impressions && <th className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 text-right leading-tight">AdX<br/>Impressions</th>}
              {visibleColumns.clicks && <th className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 text-right leading-tight">Clicks</th>}
              {visibleColumns.ecpm && <th className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 text-right leading-tight">eCPM</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/50">
            {domains.map((dom, idx) => (
              <tr key={idx} className="hover:bg-slate-700/30 transition-colors">
                {visibleColumns.domain && (
                  <td className="px-3 py-2.5 font-semibold text-white whitespace-nowrap">
                    <div className="flex items-center space-x-2">
                      <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                      <span>{dom.domain}</span>
                    </div>
                  </td>
                )}
                {visibleColumns.total_revenue && (
                  <td className="px-3 py-2.5 text-right font-bold text-emerald-400 whitespace-nowrap">
                    {formatCurrency(dom.total_revenue)}
                  </td>
                )}
                {visibleColumns.impressions && (
                  <td className="px-3 py-2.5 text-right whitespace-nowrap">{dom.impressions.toLocaleString()}</td>
                )}
                {visibleColumns.clicks && (
                  <td className="px-3 py-2.5 text-right whitespace-nowrap">{dom.clicks.toLocaleString()}</td>
                )}
                {visibleColumns.ecpm && (
                  <td className="px-3 py-2.5 text-right font-mono font-semibold text-sky-400 whitespace-nowrap">{formatCurrency(dom.ecpm)}</td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
