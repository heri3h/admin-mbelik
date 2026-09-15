import React, { useState } from 'react';
import { LayoutGrid, Search, TrendingUp, TrendingDown } from 'lucide-react';

export default function PlacementsTable({ placements }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortColumn, setSortColumn] = useState('total_revenue');
  const [sortDirection, setSortDirection] = useState('desc');

  if (!placements || placements.length === 0) {
    return (
      <div className="bg-slate-800 border border-slate-700/60 p-6 rounded-2xl text-center text-slate-400 text-sm">
        No ad unit placement performance data available.
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
    return sortDirection === 'asc' ? <span className="text-indigo-400 ml-1 font-bold">↑</span> : <span className="text-indigo-400 ml-1 font-bold">↓</span>;
  };

  const filteredPlacements = placements.filter(p =>
    p.ad_unit.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.domain.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const sortedPlacements = [...filteredPlacements].sort((a, b) => {
    let aVal = a[sortColumn] ?? 0;
    let bVal = b[sortColumn] ?? 0;
    if (typeof aVal === 'string') {
      return sortDirection === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    }
    return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
  });

  const renderDeltaBadge = (pct, subtitle = '') => {
    if (pct === null || pct === undefined) return null;
    const isPositive = pct > 0;
    const isZero = pct === 0;

    let badgeColor = 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
    if (!isZero) {
      if (!isPositive) {
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
      <div className="p-5 border-b border-slate-700/60 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <LayoutGrid className="w-5 h-5 text-indigo-400" />
            <span>Performance Report by Placement (Ad Unit)</span>
          </h3>
          <p className="text-slate-400 text-xs mt-0.5">Ad Exchange earnings, eCPM, and impressions per specific ad placement</p>
        </div>

        <div className="flex items-center space-x-3 w-full sm:w-auto">
          <div className="relative flex-1 sm:flex-initial">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search placement..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-xs text-white pl-8 pr-3 py-1.5 rounded-lg focus:outline-none focus:border-sky-500 w-full sm:w-48"
            />
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 bg-slate-700 text-slate-300 rounded-lg shrink-0">
            {filteredPlacements.length} Placements
          </span>
        </div>
      </div>

      <div className="overflow-auto max-h-[calc(100vh-220px)] min-h-[350px] w-full max-w-full rounded-b-2xl border-t border-slate-700/60">
        <table className="w-full text-left text-xs text-slate-300 border-separate border-spacing-0">
          <thead className="bg-slate-900 text-slate-400 uppercase font-semibold text-[11px] tracking-wider select-none shadow-md">
            <tr>
              <th onClick={() => handleSort('ad_unit')} className="sticky top-0 z-30 bg-slate-900 px-5 py-3.5 border-b border-slate-700/60 cursor-pointer hover:text-white transition-colors whitespace-nowrap">
                Ad Unit / Placement Name {renderSortIndicator('ad_unit')}
              </th>
              <th onClick={() => handleSort('domain')} className="sticky top-0 z-30 bg-slate-900 px-5 py-3.5 border-b border-slate-700/60 cursor-pointer hover:text-white transition-colors whitespace-nowrap">
                Site / Domain {renderSortIndicator('domain')}
              </th>
              <th onClick={() => handleSort('total_revenue')} className="sticky top-0 z-30 bg-slate-900 px-5 py-3.5 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors whitespace-nowrap">
                AdX Revenue {renderSortIndicator('total_revenue')}
              </th>
              <th onClick={() => handleSort('impressions')} className="sticky top-0 z-30 bg-slate-900 px-5 py-3.5 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors whitespace-nowrap">
                AdX Impressions {renderSortIndicator('impressions')}
              </th>
              <th onClick={() => handleSort('clicks')} className="sticky top-0 z-30 bg-slate-900 px-5 py-3.5 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors whitespace-nowrap">
                Clicks {renderSortIndicator('clicks')}
              </th>
              <th onClick={() => handleSort('ctr')} className="sticky top-0 z-30 bg-slate-900 px-5 py-3.5 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors whitespace-nowrap">
                CTR {renderSortIndicator('ctr')}
              </th>
              <th onClick={() => handleSort('ad_requests')} className="sticky top-0 z-30 bg-slate-900 px-5 py-3.5 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors whitespace-nowrap">
                Ad Requests {renderSortIndicator('ad_requests')}
              </th>
              <th onClick={() => handleSort('matched_requests')} className="sticky top-0 z-30 bg-slate-900 px-5 py-3.5 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors whitespace-nowrap">
                Matched Requests {renderSortIndicator('matched_requests')}
              </th>
              <th onClick={() => handleSort('match_rate')} className="sticky top-0 z-30 bg-slate-900 px-5 py-3.5 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors whitespace-nowrap">
                Match Rate {renderSortIndicator('match_rate')}
              </th>
              <th onClick={() => handleSort('ecpm')} className="sticky top-0 z-30 bg-slate-900 px-5 py-3.5 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors whitespace-nowrap">
                eCPM {renderSortIndicator('ecpm')}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/50">
            {sortedPlacements.map((item, idx) => {
              const compLabel = item.comparison_period_label || 'vs previous period';

              return (
                <tr key={idx} className="hover:bg-slate-700/30 transition-colors">
                  <td className="px-5 py-4 font-semibold text-white whitespace-nowrap">
                    <div className="flex items-center space-x-2">
                      <span className="w-2 h-2 rounded-full bg-indigo-400"></span>
                      <span>{item.ad_unit}</span>
                    </div>
                  </td>
                  <td className="px-5 py-4 font-mono text-slate-400 whitespace-nowrap">{item.domain}</td>

                  <td className="px-5 py-4 text-right whitespace-nowrap">
                    <div className="flex flex-col items-end font-bold text-emerald-400">
                      <span>{formatCurrency(item.total_revenue)}</span>
                      {renderDeltaBadge(item.revenue_change_pct, compLabel)}
                    </div>
                  </td>

                  <td className="px-5 py-4 text-right font-mono text-slate-300 whitespace-nowrap">{(item.impressions || 0).toLocaleString()}</td>
                  <td className="px-5 py-4 text-right font-mono text-slate-300 whitespace-nowrap">{(item.clicks || 0).toLocaleString()}</td>
                  <td className="px-5 py-4 text-right font-mono text-slate-300 whitespace-nowrap">{(item.ctr || 0).toFixed(2)}%</td>

                  <td className="px-5 py-4 text-right font-mono text-slate-300 whitespace-nowrap">{(item.ad_requests || 0).toLocaleString()}</td>
                  <td className="px-5 py-4 text-right font-mono text-slate-300 whitespace-nowrap">{(item.matched_requests || 0).toLocaleString()}</td>
                  <td className="px-5 py-4 text-right font-mono font-semibold text-indigo-300 whitespace-nowrap">{(item.match_rate || 0).toFixed(1)}%</td>

                  <td className="px-5 py-4 text-right whitespace-nowrap">
                    <div className="flex flex-col items-end font-mono font-semibold text-sky-400">
                      <span>{formatCurrency(item.ecpm)}</span>
                      {renderDeltaBadge(item.ecpm_change_pct, compLabel)}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
