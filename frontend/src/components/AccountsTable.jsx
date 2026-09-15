import React, { useState } from 'react';
import { Layers, TrendingUp, TrendingDown } from 'lucide-react';
import ColumnToggleDropdown from './ColumnToggleDropdown';

const ALL_COLUMNS = [
  { key: 'account_name', label: 'Google Ads Account' },
  { key: 'customer_id', label: 'Customer ID' },
  { key: 'total_spend', label: 'Total Spend' },
  { key: 'impressions', label: 'Impressions' },
  { key: 'clicks', label: 'Clicks' },
  { key: 'cpc', label: 'Avg CPC' },
  { key: 'ctr', label: 'CTR (%)' },
];

export default function AccountsTable({ accounts }) {
  const [sortColumn, setSortColumn] = useState('total_spend');
  const [sortDirection, setSortDirection] = useState('desc');
  const [visibleColumns, setVisibleColumns] = useState(
    ALL_COLUMNS.reduce((acc, col) => ({ ...acc, [col.key]: true }), {})
  );

  const handleToggleColumn = (key) => {
    setVisibleColumns(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleResetColumns = () => {
    setVisibleColumns(ALL_COLUMNS.reduce((acc, col) => ({ ...acc, [col.key]: true }), {}));
  };

  if (!accounts || accounts.length === 0) {
    return (
      <div className="bg-slate-800 border border-slate-700/60 p-6 rounded-2xl text-center text-slate-400 text-sm">
        No Google Ads account performance data available.
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

  const handleSort = (col) => {
    if (sortColumn === col) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(col);
      setSortDirection('desc');
    }
  };

  const renderSortIndicator = (col) => {
    if (sortColumn !== col) return <span className="text-slate-600 ml-1 font-normal opacity-50">↕</span>;
    return sortDirection === 'asc' ? <span className="text-sky-400 ml-1 font-bold">↑</span> : <span className="text-sky-400 ml-1 font-bold">↓</span>;
  };

  const sortedAccounts = [...accounts].sort((a, b) => {
    let aVal = a[sortColumn] ?? 0;
    let bVal = b[sortColumn] ?? 0;
    if (typeof aVal === 'string') {
      return sortDirection === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    }
    return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
  });

  const renderDeltaBadge = (pct, invertColors = true, subtitle = '') => {
    if (pct === null || pct === undefined) return null;
    const isPositive = pct > 0;
    const isZero = pct === 0;

    let isGood = isPositive;
    if (invertColors) {
      isGood = !isPositive;
    }

    let badgeColor = 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
    if (!isZero) {
      if (!isGood) {
        badgeColor = 'text-rose-400 bg-rose-500/10 border-rose-500/20';
      }
    } else {
      badgeColor = 'text-slate-400 bg-slate-800 border-slate-700';
    }

    const Icon = isPositive ? TrendingUp : (isZero ? null : TrendingDown);

    return (
      <span
        title={subtitle}
        className={`inline-flex items-center gap-0.5 text-[10px] font-semibold px-1.5 py-0.5 rounded border ${badgeColor} mt-0.5`}
      >
        {Icon && <Icon className="w-2.5 h-2.5" />}
        <span>{isPositive ? `+${pct}%` : `${pct}%`}</span>
      </span>
    );
  };

  return (
    <div className="bg-slate-800 border border-slate-700/60 rounded-2xl shadow-sm">
      <div className="p-3.5 sm:p-5 border-b border-slate-700/60 flex items-center justify-between gap-4">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Layers className="w-5 h-5 text-sky-400" />
            <span>Google Ads Account Performance Breakdown</span>
          </h3>
          <p className="text-slate-400 text-xs mt-0.5">Ad spend, impressions, clicks, CPC, and CTR per account</p>
        </div>

        <div className="flex items-center space-x-3">
          <ColumnToggleDropdown
            columns={ALL_COLUMNS}
            visibleColumns={visibleColumns}
            onToggleColumn={handleToggleColumn}
            onResetColumns={handleResetColumns}
          />

          <span className="text-xs font-semibold px-2.5 py-1 bg-slate-700 text-slate-300 rounded-lg">
            {accounts.length} Accounts
          </span>
        </div>
      </div>

      <div className="overflow-auto max-h-[calc(100vh-220px)] min-h-[350px] w-full max-w-full rounded-b-2xl border-t border-slate-700/60">
        <table className="w-full text-left text-xs text-slate-300 border-separate border-spacing-0">
          <thead className="bg-slate-900 text-slate-400 uppercase font-semibold text-[10px] tracking-wider select-none shadow-md">
            <tr>
              {visibleColumns.account_name && (
                <th onClick={() => handleSort('account_name')} className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 cursor-pointer hover:text-white transition-colors">
                  <div className="flex items-center space-x-1 leading-tight">
                    <span>Google Ads<br/>Account</span>
                    {renderSortIndicator('account_name')}
                  </div>
                </th>
              )}
              {visibleColumns.customer_id && (
                <th onClick={() => handleSort('customer_id')} className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 cursor-pointer hover:text-white transition-colors">
                  <div className="flex items-center space-x-1 leading-tight">
                    <span>Customer<br/>ID</span>
                    {renderSortIndicator('customer_id')}
                  </div>
                </th>
              )}
              {visibleColumns.total_spend && (
                <th onClick={() => handleSort('total_spend')} className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                  <div className="flex items-center justify-end space-x-1 leading-tight">
                    <span>Total<br/>Spend</span>
                    {renderSortIndicator('total_spend')}
                  </div>
                </th>
              )}
              {visibleColumns.impressions && (
                <th onClick={() => handleSort('impressions')} className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                  <div className="flex items-center justify-end space-x-1 leading-tight">
                    <span>Impressions</span>
                    {renderSortIndicator('impressions')}
                  </div>
                </th>
              )}
              {visibleColumns.clicks && (
                <th onClick={() => handleSort('clicks')} className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                  <div className="flex items-center justify-end space-x-1 leading-tight">
                    <span>Clicks</span>
                    {renderSortIndicator('clicks')}
                  </div>
                </th>
              )}
              {visibleColumns.cpc && (
                <th onClick={() => handleSort('cpc')} className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                  <div className="flex items-center justify-end space-x-1 leading-tight">
                    <span>Avg<br/>CPC</span>
                    {renderSortIndicator('cpc')}
                  </div>
                </th>
              )}
              {visibleColumns.ctr && (
                <th onClick={() => handleSort('ctr')} className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                  <div className="flex items-center justify-end space-x-1 leading-tight">
                    <span>CTR (%)</span>
                    {renderSortIndicator('ctr')}
                  </div>
                </th>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/50">
            {sortedAccounts.map((acc, idx) => {
              const compLabel = acc.comparison_period_label || 'vs previous period';

              return (
                <tr key={idx} className="hover:bg-slate-700/30 transition-colors">
                  {visibleColumns.account_name && (
                    <td className="px-3 py-2.5 font-semibold text-white whitespace-nowrap">
                      <div className="flex items-center space-x-2">
                        <span className="w-2 h-2 rounded-full bg-sky-400"></span>
                        <span>{acc.account_name}</span>
                      </div>
                    </td>
                  )}
                  {visibleColumns.customer_id && (
                    <td className="px-3 py-2.5 font-mono text-slate-400 whitespace-nowrap">{acc.customer_id}</td>
                  )}

                  {visibleColumns.total_spend && (
                    <td className="px-3 py-2.5 text-right font-bold text-sky-400 whitespace-nowrap">
                      <div className="flex flex-col items-end">
                        <span>{formatCurrency(acc.total_spend)}</span>
                        {renderDeltaBadge(acc.spend_change_pct, true, compLabel)}
                      </div>
                    </td>
                  )}

                  {visibleColumns.impressions && (
                    <td className="px-3 py-2.5 text-right whitespace-nowrap">{acc.impressions.toLocaleString()}</td>
                  )}
                  {visibleColumns.clicks && (
                    <td className="px-3 py-2.5 text-right whitespace-nowrap">{acc.clicks.toLocaleString()}</td>
                  )}
                  {visibleColumns.cpc && (
                    <td className="px-3 py-2.5 text-right font-mono whitespace-nowrap">{formatCurrency(acc.cpc)}</td>
                  )}
                  {visibleColumns.ctr && (
                    <td className="px-3 py-2.5 text-right font-mono font-semibold text-emerald-400 whitespace-nowrap">{acc.ctr}%</td>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
