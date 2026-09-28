import React, { useState } from 'react';
import { Globe, Search, TrendingUp, TrendingDown } from 'lucide-react';
import ColumnToggleDropdown from './ColumnToggleDropdown';
import CountryBreakdownModal from './CountryBreakdownModal';

const ALL_COLUMNS = [
  { key: 'country', label: 'Country' },
  { key: 'spend', label: 'Spend (Ads)' },
  { key: 'revenue', label: 'Revenue (AdX)' },
  { key: 'net_profit', label: 'Net Profit' },
  { key: 'roi', label: 'ROI' },
  { key: 'ecpm', label: 'CPM AdX (eCPM)' },
  { key: 'match_rate', label: 'Match Rate' },
  { key: 'ctr', label: 'CTR' },
  { key: 'ad_requests', label: 'Ad Requests' },
  { key: 'matched_requests', label: 'Matched Requests' },
  { key: 'pricing_rule_name', label: 'PRICING_RULE_NAME' }
];

const formatPricingRuleName = (rule) => {
  if (!rule || rule === 'All Rules') return 'All Rules';
  if (rule === '(No pricing rule applied)' || rule === 'No pricing rule applied' || rule === '(No Rule)') return 'No Rule';
  return rule;
};

export default function CountriesTable({ countries, startDate, endDate }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCountryObj, setSelectedCountryObj] = useState(null);
  const [sortColumn, setSortColumn] = useState('revenue');
  const [sortDirection, setSortDirection] = useState('desc');
  const [visibleColumns, setVisibleColumns] = useState(() => {
    try {
      const saved = localStorage.getItem('col_vis_countries');
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
      try { localStorage.setItem('col_vis_countries', JSON.stringify(updated)); } catch (e) {}
      return updated;
    });
  };

  const handleResetColumns = () => {
    const initial = ALL_COLUMNS.reduce((acc, col) => ({ ...acc, [col.key]: true }), {});
    setVisibleColumns(initial);
    try { localStorage.setItem('col_vis_countries', JSON.stringify(initial)); } catch (e) {}
  };

  if (!countries || countries.length === 0) {
    return (
      <div className="bg-slate-800 border border-slate-700/60 p-6 rounded-2xl text-center text-slate-400 text-sm">
        No country breakdown data available for the selected period.
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
    return sortDirection === 'asc' ? <span className="text-emerald-400 ml-1 font-bold">↑</span> : <span className="text-emerald-400 ml-1 font-bold">↓</span>;
  };

  const filteredCountries = countries.filter(c =>
    (c.country || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (c.country_code || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  const sortedCountries = [...filteredCountries].sort((a, b) => {
    let colKey = sortColumn === 'country' ? 'country' : sortColumn;
    let aVal = a[colKey] ?? 0;
    let bVal = b[colKey] ?? 0;
    if (typeof aVal === 'string') {
      return sortDirection === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    }
    return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
  });

  // Calculate totals for footer
  const totalRev = countries.reduce((sum, c) => sum + (c.revenue || 0), 0);
  const totalSpend = countries.reduce((sum, c) => sum + (c.spend || 0), 0);
  const netProfit = totalRev - totalSpend;
  const overallRoi = totalSpend > 0 ? (totalRev / totalSpend * 100) : 0;
  const totalAdReqs = countries.reduce((sum, c) => sum + (c.ad_requests || 0), 0);
  const totalMatchedReqs = countries.reduce((sum, c) => sum + (c.matched_requests || 0), 0);
  const avgMatchRate = totalAdReqs > 0 ? (totalMatchedReqs / totalAdReqs * 100) : 0;
  const totalImps = countries.reduce((sum, c) => sum + (c.impressions || 0), 0);
  const totalClicks = countries.reduce((sum, c) => sum + (c.clicks || 0), 0);
  const avgCtr = totalImps > 0 ? (totalClicks / totalImps * 100) : 0;
  const avgEcpm = totalImps > 0 ? (totalRev / (totalImps / 1000)) : 0;

  return (
    <div className="bg-slate-800 border border-slate-700/60 rounded-2xl shadow-xl overflow-hidden space-y-4">
      {/* Header controls bar */}
      <div className="p-4 border-b border-slate-700/60 bg-slate-900/60 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="flex items-center space-x-2">
          <Globe className="w-5 h-5 text-emerald-400" />
          <h3 className="font-bold text-white text-sm sm:text-base">Earning & Spend Breakdown by Country</h3>
          <span className="text-xs text-slate-400 font-mono">({sortedCountries.length} countries)</span>
        </div>

        <div className="flex items-center space-x-3 w-full sm:w-auto">
          <div className="relative flex-1 sm:w-64">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search country or code..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-xs text-white pl-8 pr-3 py-1.5 rounded-lg focus:outline-none focus:border-emerald-500 w-full"
            />
          </div>

          <ColumnToggleDropdown
            columns={ALL_COLUMNS}
            visibleColumns={visibleColumns}
            onToggleColumn={handleToggleColumn}
            onResetColumns={handleResetColumns}
          />
        </div>
      </div>

      {/* Table Display */}
      <div className="overflow-x-auto w-full max-w-full">
        <table className="w-full text-left text-xs text-slate-300 border-separate border-spacing-0">
          <thead className="bg-slate-900/90 text-slate-400 uppercase font-semibold text-[10px] tracking-wider select-none shadow-md">
            <tr>
              {visibleColumns.country && (
                <th onClick={() => handleSort('country')} className="sticky top-0 z-10 bg-slate-900 px-4 py-3 border-b border-slate-700/60 cursor-pointer hover:text-white transition-colors">
                  <div className="flex items-center space-x-1 leading-tight">
                    <span>Country</span>
                    {renderSortIndicator('country')}
                  </div>
                </th>
              )}
              {visibleColumns.spend && (
                <th onClick={() => handleSort('spend')} className="sticky top-0 z-10 bg-slate-900 px-4 py-3 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                  <div className="flex items-center justify-end space-x-1 leading-tight">
                    <span>Spend<br/>(Ads)</span>
                    {renderSortIndicator('spend')}
                  </div>
                </th>
              )}
              {visibleColumns.revenue && (
                <th onClick={() => handleSort('revenue')} className="sticky top-0 z-10 bg-slate-900 px-4 py-3 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                  <div className="flex items-center justify-end space-x-1 leading-tight">
                    <span>Revenue<br/>(AdX)</span>
                    {renderSortIndicator('revenue')}
                  </div>
                </th>
              )}
              {visibleColumns.net_profit && (
                <th onClick={() => handleSort('net_profit')} className="sticky top-0 z-10 bg-slate-900 px-4 py-3 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                  <div className="flex items-center justify-end space-x-1 leading-tight">
                    <span>Net Profit</span>
                    {renderSortIndicator('net_profit')}
                  </div>
                </th>
              )}
              {visibleColumns.roi && (
                <th onClick={() => handleSort('roi')} className="sticky top-0 z-10 bg-slate-900 px-4 py-3 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                  <div className="flex items-center justify-end space-x-1 leading-tight">
                    <span>ROI</span>
                    {renderSortIndicator('roi')}
                  </div>
                </th>
              )}
              {visibleColumns.ecpm && (
                <th onClick={() => handleSort('ecpm')} className="sticky top-0 z-10 bg-slate-900 px-4 py-3 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                  <div className="flex items-center justify-end space-x-1 leading-tight">
                    <span>CPM AdX<br/>(eCPM)</span>
                    {renderSortIndicator('ecpm')}
                  </div>
                </th>
              )}
              {visibleColumns.match_rate && (
                <th onClick={() => handleSort('match_rate')} className="sticky top-0 z-10 bg-slate-900 px-4 py-3 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                  <div className="flex items-center justify-end space-x-1 leading-tight">
                    <span>Match<br/>Rate</span>
                    {renderSortIndicator('match_rate')}
                  </div>
                </th>
              )}
              {visibleColumns.ctr && (
                <th onClick={() => handleSort('ctr')} className="sticky top-0 z-10 bg-slate-900 px-4 py-3 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                  <div className="flex items-center justify-end space-x-1 leading-tight">
                    <span>CTR</span>
                    {renderSortIndicator('ctr')}
                  </div>
                </th>
              )}
              {visibleColumns.ad_requests && (
                <th onClick={() => handleSort('ad_requests')} className="sticky top-0 z-10 bg-slate-900 px-4 py-3 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                  <div className="flex items-center justify-end space-x-1 leading-tight">
                    <span>Ad<br/>Requests</span>
                    {renderSortIndicator('ad_requests')}
                  </div>
                </th>
              )}
              {visibleColumns.matched_requests && (
                <th onClick={() => handleSort('matched_requests')} className="sticky top-0 z-10 bg-slate-900 px-4 py-3 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                  <div className="flex items-center justify-end space-x-1 leading-tight">
                    <span>Matched<br/>Requests</span>
                    {renderSortIndicator('matched_requests')}
                  </div>
                </th>
              )}
              {visibleColumns.pricing_rule_name && (
                <th onClick={() => handleSort('pricing_rule_name')} className="sticky top-0 z-10 bg-slate-900 px-4 py-3 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                  <div className="flex items-center justify-end space-x-1 leading-tight">
                    <span>PRICING_<br/>RULE_NAME</span>
                    {renderSortIndicator('pricing_rule_name')}
                  </div>
                </th>
              )}
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-700/50">
            {sortedCountries.map((c, idx) => {
              const hasSpend = c.spend > 0;
              const isProfitable = c.net_profit >= 0;

              return (
                <tr
                  key={idx}
                  onClick={() => setSelectedCountryObj(c)}
                  className="hover:bg-slate-700/50 cursor-pointer transition-colors group"
                  title="Click to view details for this country"
                >
                  {visibleColumns.country && (
                    <td className="px-4 py-3 font-semibold text-white whitespace-nowrap">
                      <div className="flex items-center space-x-2">
                        <span className="text-base group-hover:scale-125 transition-transform">{c.flag_emoji || '🌐'}</span>
                        <span className="font-bold text-slate-100 group-hover:text-emerald-400 transition-colors">
                          {c.country}
                        </span>
                        <span className="font-mono text-[10px] text-slate-400 bg-slate-900/80 px-1.5 py-0.5 rounded border border-slate-700/50">
                          {c.country_code}
                        </span>
                      </div>
                    </td>
                  )}

                  {visibleColumns.spend && (
                    <td className="px-4 py-3 text-right font-medium text-rose-400 whitespace-nowrap">
                      {hasSpend ? formatCurrency(c.spend) : <span className="text-slate-500">-</span>}
                    </td>
                  )}

                  {visibleColumns.revenue && (
                    <td className="px-4 py-3 text-right font-bold text-emerald-400 whitespace-nowrap">
                      {formatCurrency(c.revenue)}
                    </td>
                  )}

                  {visibleColumns.net_profit && (
                    <td className="px-4 py-3 text-right whitespace-nowrap">
                      {hasSpend ? (
                        <span className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded-lg text-xs font-bold border ${
                          isProfitable
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                            : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                        }`}>
                          {isProfitable ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                          <span>{formatCurrency(c.net_profit)}</span>
                        </span>
                      ) : (
                        <span className="text-emerald-400 font-bold">{formatCurrency(c.revenue)}</span>
                      )}
                    </td>
                  )}

                  {visibleColumns.roi && (
                    <td className="px-4 py-3 text-right font-mono font-bold whitespace-nowrap">
                      {hasSpend ? (
                        <span className={isProfitable ? 'text-emerald-400' : 'text-rose-400'}>
                          {c.roi > 0 ? `+${c.roi.toFixed(1)}%` : `${c.roi.toFixed(1)}%`}
                        </span>
                      ) : (
                        <span className="text-slate-500">N/A</span>
                      )}
                    </td>
                  )}

                  {visibleColumns.ecpm && (
                    <td className="px-4 py-3 text-right font-mono font-semibold text-sky-400 whitespace-nowrap">
                      {formatCurrency(c.ecpm)}
                    </td>
                  )}

                  {visibleColumns.match_rate && (
                    <td className="px-4 py-3 text-right font-mono font-semibold text-indigo-300 whitespace-nowrap">
                      {(c.match_rate || 0).toFixed(1)}%
                    </td>
                  )}

                  {visibleColumns.ctr && (
                    <td className="px-4 py-3 text-right font-mono text-slate-300 whitespace-nowrap">
                      {(c.ctr || 0).toFixed(2)}%
                    </td>
                  )}

                  {visibleColumns.ad_requests && (
                    <td className="px-4 py-3 text-right font-mono text-slate-300 whitespace-nowrap">
                      {(c.ad_requests || 0).toLocaleString()}
                    </td>
                  )}

                  {visibleColumns.matched_requests && (
                    <td className="px-4 py-3 text-right font-mono text-slate-300 whitespace-nowrap">
                      {(c.matched_requests || 0).toLocaleString()}
                    </td>
                  )}

                  {visibleColumns.pricing_rule_name && (
                    <td className="px-4 py-3 text-right font-medium text-amber-300 whitespace-nowrap">
                      {formatPricingRuleName(c.pricing_rule_name)}
                    </td>
                  )}
                </tr>
              );
            })}
          </tbody>

          <tfoot className="bg-slate-950 text-slate-200 font-semibold border-t border-slate-700/80 text-[11px]">
            <tr>
              {visibleColumns.country && (
                <td className="px-4 py-3 font-bold text-xs leading-tight">
                  <div>Total / Average</div>
                  <div className="text-[10px] text-slate-400 font-normal">All Countries ({countries.length})</div>
                </td>
              )}
              {visibleColumns.spend && (
                <td className="px-4 py-3 text-right font-bold text-rose-400 whitespace-nowrap">{formatCurrency(totalSpend)}</td>
              )}
              {visibleColumns.revenue && (
                <td className="px-4 py-3 text-right font-bold text-emerald-400 whitespace-nowrap">{formatCurrency(totalRev)}</td>
              )}
              {visibleColumns.net_profit && (
                <td className={`px-4 py-3 text-right font-bold whitespace-nowrap ${netProfit >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {formatCurrency(netProfit)}
                </td>
              )}
              {visibleColumns.roi && (
                <td className={`px-4 py-3 text-right font-mono font-bold whitespace-nowrap ${overallRoi >= 100 ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {totalSpend > 0 ? `${overallRoi.toFixed(1)}%` : 'N/A'}
                </td>
              )}
              {visibleColumns.ecpm && (
                <td className="px-4 py-3 text-right font-mono text-sky-400 whitespace-nowrap">{formatCurrency(avgEcpm)}</td>
              )}
              {visibleColumns.match_rate && (
                <td className="px-4 py-3 text-right font-mono text-indigo-300 whitespace-nowrap">{avgMatchRate.toFixed(1)}%</td>
              )}
              {visibleColumns.ctr && (
                <td className="px-4 py-3 text-right font-mono whitespace-nowrap">{avgCtr.toFixed(2)}%</td>
              )}
              {visibleColumns.ad_requests && (
                <td className="px-4 py-3 text-right font-mono whitespace-nowrap">{totalAdReqs.toLocaleString()}</td>
              )}
              {visibleColumns.matched_requests && (
                <td className="px-4 py-3 text-right font-mono whitespace-nowrap">{totalMatchedReqs.toLocaleString()}</td>
              )}
              {visibleColumns.pricing_rule_name && (
                <td className="px-4 py-3 text-right font-medium text-amber-300 whitespace-nowrap">All Rules</td>
              )}
            </tr>
          </tfoot>
        </table>
      </div>

      {/* Country Breakdown Detail Modal when clicking a country row */}
      {selectedCountryObj && (
        <CountryBreakdownModal
          domain="all"
          startDate={startDate}
          endDate={endDate}
          onClose={() => setSelectedCountryObj(null)}
        />
      )}
    </div>
  );
}
