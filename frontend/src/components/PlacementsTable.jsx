import React, { useState } from 'react';
import { LayoutGrid, Search, TrendingUp, TrendingDown } from 'lucide-react';
import ColumnToggleDropdown from './ColumnToggleDropdown';

const ALL_COLUMNS = [
  { key: 'ad_unit', label: 'Ad Unit / Placement' },
  { key: 'domain', label: 'Site / Domain' },
  { key: 'total_revenue', label: 'AdX Revenue' },
  { key: 'impressions', label: 'AdX Impressions' },
  { key: 'clicks', label: 'Clicks' },
  { key: 'ctr', label: 'CTR' },
  { key: 'ad_requests', label: 'Ad Requests' },
  { key: 'matched_requests', label: 'Matched Requests' },
  { key: 'match_rate', label: 'Match Rate' },
  { key: 'ecpm', label: 'eCPM' },
  { key: 'pricing_rule_name', label: 'PRICING_RULE_NAME' },
];

const formatPricingRuleName = (rule) => {
  if (!rule || rule === 'All Rules') return 'All Rules';
  if (rule === '(No pricing rule applied)' || rule === 'No pricing rule applied' || rule === '(No Rule)') return 'No Rule';
  return rule;
};

export default function PlacementsTable({ placements }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortColumn, setSortColumn] = useState('total_revenue');
  const [sortDirection, setSortDirection] = useState('desc');
  const [visibleColumns, setVisibleColumns] = useState(() => {
    try {
      const saved = localStorage.getItem('col_vis_placements');
      if (saved) {
        const parsed = JSON.parse(saved);
        return ALL_COLUMNS.reduce((acc, col) => ({
          ...acc,
          [col.key]: parsed[col.key] !== undefined ? parsed[col.key] : true
        }), {});
      }
    } catch (e) {}
    return ALL_COLUMNS.reduce((acc, col) => ({ ...acc, [col.key]: true }), {});
  });

  const handleToggleColumn = (key) => {
    setVisibleColumns(prev => {
      const updated = { ...prev, [key]: !prev[key] };
      try { localStorage.setItem('col_vis_placements', JSON.stringify(updated)); } catch (e) {}
      return updated;
    });
  };

  const handleResetColumns = () => {
    const initial = ALL_COLUMNS.reduce((acc, col) => ({ ...acc, [col.key]: true }), {});
    setVisibleColumns(initial);
    try { localStorage.setItem('col_vis_placements', JSON.stringify(initial)); } catch (e) {}
  };

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

  const visibleCount = Object.values(visibleColumns).filter(Boolean).length;

  return (
    <div className="-mx-1.5 sm:mx-0 bg-slate-800 border-x-0 sm:border-x border-y border-slate-700/60 rounded-none sm:rounded-2xl shadow-sm">
      <div className="px-3 py-3.5 sm:p-5 border-b border-slate-700/60 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
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

          <ColumnToggleDropdown
            columns={ALL_COLUMNS}
            visibleColumns={visibleColumns}
            onToggleColumn={handleToggleColumn}
            onResetColumns={handleResetColumns}
          />

          <span className="text-xs font-semibold px-2.5 py-1 bg-slate-700 text-slate-300 rounded-lg shrink-0">
            {filteredPlacements.length} Placements
          </span>
        </div>
      </div>

      <div className="overflow-auto max-h-[calc(100vh-220px)] min-h-[350px] w-full max-w-full rounded-b-2xl border-t border-slate-700/60">
        <table className="w-full text-left text-xs text-slate-300 border-separate border-spacing-0">
          <thead className="bg-slate-900 text-slate-400 uppercase font-semibold text-[10px] tracking-wider select-none shadow-md">
            <tr>
              {visibleColumns.ad_unit && (
                <th onClick={() => handleSort('ad_unit')} className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 cursor-pointer hover:text-white transition-colors">
                  <div className="flex items-center space-x-1 leading-tight">
                    <span>Ad Unit /<br/>Placement</span>
                    {renderSortIndicator('ad_unit')}
                  </div>
                </th>
              )}
              {visibleColumns.domain && (
                <th onClick={() => handleSort('domain')} className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 cursor-pointer hover:text-white transition-colors">
                  <div className="flex items-center space-x-1 leading-tight">
                    <span>Site /<br/>Domain</span>
                    {renderSortIndicator('domain')}
                  </div>
                </th>
              )}
              {visibleColumns.total_revenue && (
                <th onClick={() => handleSort('total_revenue')} className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                  <div className="flex items-center justify-end space-x-1 leading-tight">
                    <span>AdX Revenue</span>
                    {renderSortIndicator('total_revenue')}
                  </div>
                </th>
              )}
              {visibleColumns.impressions && (
                <th onClick={() => handleSort('impressions')} className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                  <div className="flex items-center justify-end space-x-1 leading-tight">
                    <span>AdX<br/>Impressions</span>
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
              {visibleColumns.ctr && (
                <th onClick={() => handleSort('ctr')} className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                  <div className="flex items-center justify-end space-x-1 leading-tight">
                    <span>CTR</span>
                    {renderSortIndicator('ctr')}
                  </div>
                </th>
              )}
              {visibleColumns.ad_requests && (
                <th onClick={() => handleSort('ad_requests')} className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                  <div className="flex items-center justify-end space-x-1 leading-tight">
                    <span>Ad<br/>Requests</span>
                    {renderSortIndicator('ad_requests')}
                  </div>
                </th>
              )}
              {visibleColumns.matched_requests && (
                <th onClick={() => handleSort('matched_requests')} className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                  <div className="flex items-center justify-end space-x-1 leading-tight">
                    <span>Matched<br/>Requests</span>
                    {renderSortIndicator('matched_requests')}
                  </div>
                </th>
              )}
              {visibleColumns.match_rate && (
                <th onClick={() => handleSort('match_rate')} className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                  <div className="flex items-center justify-end space-x-1 leading-tight">
                    <span>Match<br/>Rate</span>
                    {renderSortIndicator('match_rate')}
                  </div>
                </th>
              )}
              {visibleColumns.ecpm && (
                <th onClick={() => handleSort('ecpm')} className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                  <div className="flex items-center justify-end space-x-1 leading-tight">
                    <span>eCPM</span>
                    {renderSortIndicator('ecpm')}
                  </div>
                </th>
              )}
              {visibleColumns.pricing_rule_name && (
                <th onClick={() => handleSort('pricing_rule_name')} className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                  <div className="flex items-center justify-end space-x-1 leading-tight">
                    <span>PRICING_<br/>RULE_NAME</span>
                    {renderSortIndicator('pricing_rule_name')}
                  </div>
                </th>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/50">
            {sortedPlacements.map((item, idx) => {
              const compLabel = item.comparison_period_label || 'vs previous period';

              return (
                <tr key={idx} className="hover:bg-slate-700/30 transition-colors">
                  {visibleColumns.ad_unit && (
                    <td className="px-3 py-2.5 font-semibold text-white whitespace-nowrap">
                      <div className="flex items-center space-x-2">
                        <span className="w-2 h-2 rounded-full bg-indigo-400"></span>
                        <span>{item.ad_unit}</span>
                      </div>
                    </td>
                  )}
                  {visibleColumns.domain && (
                    <td className="px-3 py-2.5 font-mono text-slate-400 whitespace-nowrap">{item.domain}</td>
                  )}

                  {visibleColumns.total_revenue && (
                    <td className="px-3 py-2.5 text-right whitespace-nowrap">
                      <div className="flex flex-col items-end font-bold text-emerald-400">
                        <span>{formatCurrency(item.total_revenue)}</span>
                        {renderDeltaBadge(item.revenue_change_pct, compLabel)}
                      </div>
                    </td>
                  )}

                  {visibleColumns.impressions && (
                    <td className="px-3 py-2.5 text-right font-mono text-slate-300 whitespace-nowrap">{(item.impressions || 0).toLocaleString()}</td>
                  )}
                  {visibleColumns.clicks && (
                    <td className="px-3 py-2.5 text-right font-mono text-slate-300 whitespace-nowrap">{(item.clicks || 0).toLocaleString()}</td>
                  )}
                  {visibleColumns.ctr && (
                    <td className="px-3 py-2.5 text-right font-mono text-slate-300 whitespace-nowrap">{(item.ctr || 0).toFixed(2)}%</td>
                  )}

                  {visibleColumns.ad_requests && (
                    <td className="px-3 py-2.5 text-right font-mono text-slate-300 whitespace-nowrap">{(item.ad_requests || 0).toLocaleString()}</td>
                  )}
                  {visibleColumns.matched_requests && (
                    <td className="px-3 py-2.5 text-right font-mono text-slate-300 whitespace-nowrap">{(item.matched_requests || 0).toLocaleString()}</td>
                  )}
                  {visibleColumns.match_rate && (
                    <td className="px-3 py-2.5 text-right font-mono font-semibold text-indigo-300 whitespace-nowrap">{(item.match_rate || 0).toFixed(1)}%</td>
                  )}

                  {visibleColumns.ecpm && (
                    <td className="px-3 py-2.5 text-right whitespace-nowrap">
                      <div className="flex flex-col items-end font-mono font-semibold text-sky-400">
                        <span>{formatCurrency(item.ecpm)}</span>
                        {renderDeltaBadge(item.ecpm_change_pct, compLabel)}
                      </div>
                    </td>
                  )}

                  {visibleColumns.pricing_rule_name && (
                    <td className="px-3 py-2.5 text-right font-medium text-amber-300 whitespace-nowrap">
                      {formatPricingRuleName(item.pricing_rule_name)}
                    </td>
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
