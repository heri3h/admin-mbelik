import React, { useState } from 'react';
import { Layers, TrendingUp, TrendingDown } from 'lucide-react';

export default function AccountsTable({ accounts }) {
  const [sortColumn, setSortColumn] = useState('total_spend');
  const [sortDirection, setSortDirection] = useState('desc');

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
    <div className="bg-slate-800 border border-slate-700/60 rounded-2xl shadow-sm overflow-hidden">
      <div className="p-5 border-b border-slate-700/60 flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Layers className="w-5 h-5 text-sky-400" />
            <span>Google Ads Account Performance Breakdown</span>
          </h3>
          <p className="text-slate-400 text-xs mt-0.5">Ad spend, impressions, clicks, CPC, and CTR per account</p>
        </div>
        <span className="text-xs font-semibold px-2.5 py-1 bg-slate-700 text-slate-300 rounded-lg">
          {accounts.length} Accounts
        </span>
      </div>

      <div className="overflow-x-auto w-full max-w-full">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="sticky top-16 z-30 bg-slate-900/95 backdrop-blur text-slate-400 uppercase font-semibold text-[11px] tracking-wider border-b border-slate-700/60 select-none shadow-md">
            <tr>
              <th onClick={() => handleSort('account_name')} className="px-5 py-3.5 cursor-pointer hover:text-white transition-colors">
                Google Ads Account {renderSortIndicator('account_name')}
              </th>
              <th onClick={() => handleSort('customer_id')} className="px-5 py-3.5 cursor-pointer hover:text-white transition-colors">
                Customer ID {renderSortIndicator('customer_id')}
              </th>
              <th onClick={() => handleSort('total_spend')} className="px-5 py-3.5 text-right cursor-pointer hover:text-white transition-colors">
                Total Spend {renderSortIndicator('total_spend')}
              </th>
              <th onClick={() => handleSort('impressions')} className="px-5 py-3.5 text-right cursor-pointer hover:text-white transition-colors">
                Impressions {renderSortIndicator('impressions')}
              </th>
              <th onClick={() => handleSort('clicks')} className="px-5 py-3.5 text-right cursor-pointer hover:text-white transition-colors">
                Clicks {renderSortIndicator('clicks')}
              </th>
              <th onClick={() => handleSort('cpc')} className="px-5 py-3.5 text-right cursor-pointer hover:text-white transition-colors">
                Avg CPC {renderSortIndicator('cpc')}
              </th>
              <th onClick={() => handleSort('ctr')} className="px-5 py-3.5 text-right cursor-pointer hover:text-white transition-colors">
                CTR (%) {renderSortIndicator('ctr')}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/50">
            {sortedAccounts.map((acc, idx) => {
              const compLabel = acc.comparison_period_label || 'vs previous period';

              return (
                <tr key={idx} className="hover:bg-slate-700/30 transition-colors">
                  <td className="px-5 py-4 font-semibold text-white">
                    <div className="flex items-center space-x-2">
                      <span className="w-2 h-2 rounded-full bg-sky-400"></span>
                      <span>{acc.account_name}</span>
                    </div>
                  </td>
                  <td className="px-5 py-4 font-mono text-slate-400">{acc.customer_id}</td>

                  <td className="px-5 py-4 text-right font-bold text-sky-400">
                    <div className="flex flex-col items-end">
                      <span>{formatCurrency(acc.total_spend)}</span>
                      {renderDeltaBadge(acc.spend_change_pct, true, compLabel)}
                    </div>
                  </td>

                  <td className="px-5 py-4 text-right">{acc.impressions.toLocaleString()}</td>
                  <td className="px-5 py-4 text-right">{acc.clicks.toLocaleString()}</td>
                  <td className="px-5 py-4 text-right font-mono">{formatCurrency(acc.cpc)}</td>
                  <td className="px-5 py-4 text-right font-mono font-semibold text-emerald-400">{acc.ctr}%</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
