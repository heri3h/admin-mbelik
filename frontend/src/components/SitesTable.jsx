import React, { useState } from 'react';
import { Globe, Search, Link as LinkIcon, TrendingUp, TrendingDown, ChevronRight } from 'lucide-react';
import CountryBreakdownModal from './CountryBreakdownModal';

export default function SitesTable({ sites, startDate, endDate }) {
  const isSingleDay = Boolean(startDate && endDate && startDate === endDate);

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDomain, setSelectedDomain] = useState(null);
  const [sortColumn, setSortColumn] = useState('total_revenue');
  const [sortDirection, setSortDirection] = useState('desc');

  if (!sites || sites.length === 0) {
    return (
      <div className="bg-slate-800 border border-slate-700/60 p-6 rounded-2xl text-center text-slate-400 text-sm">
        No website domain performance data available.
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

  const filteredSites = sites.filter(s =>
    s.domain.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const sortedSites = [...filteredSites].sort((a, b) => {
    let aVal = a[sortColumn] ?? 0;
    let bVal = b[sortColumn] ?? 0;
    if (typeof aVal === 'string') {
      return sortDirection === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    }
    return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
  });

  const renderDeltaBadge = (pct, invertColors = false, subtitle = '') => {
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
      {/* Country breakdown modal window */}
      {selectedDomain && (
        <CountryBreakdownModal
          domain={selectedDomain}
          startDate={startDate}
          endDate={endDate}
          onClose={() => setSelectedDomain(null)}
        />
      )}

      <div className="p-5 border-b border-slate-700/60 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Globe className="w-5 h-5 text-emerald-400" />
            <span>Performance & Profitability Report by Site (Domain)</span>
          </h3>
          <p className="text-slate-400 text-xs mt-0.5">
            Spend, Revenue, Ad Requests, Matched Requests, MR AdX, Net Profit, ROI, dan eCPM per domain. <span className="text-emerald-400 font-semibold">(Klik nama domain untuk melihat rincian negara)</span>
          </p>
        </div>

        <div className="flex items-center space-x-3 w-full sm:w-auto">
          <div className="relative flex-1 sm:flex-initial">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search site domain..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-xs text-white pl-8 pr-3 py-1.5 rounded-lg focus:outline-none focus:border-sky-500 w-full sm:w-48"
            />
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-lg shrink-0">
            {filteredSites.length} Active Sites
          </span>
        </div>
      </div>

      <div className="overflow-x-auto sm:overflow-x-visible rounded-b-2xl">
        <table className="w-full text-left text-xs text-slate-300 border-collapse">
          <thead className="sm:sticky sm:top-16 z-30 bg-slate-900 text-slate-400 uppercase font-semibold text-[11px] tracking-wider border-b border-slate-700/60 select-none shadow-md">
            <tr>
              <th onClick={() => handleSort('domain')} className="px-5 py-3.5 cursor-pointer hover:text-white transition-colors">
                Site / Domain Name {renderSortIndicator('domain')}
              </th>
              <th onClick={() => handleSort('total_spend')} className="px-5 py-3.5 text-right cursor-pointer hover:text-white transition-colors">
                Spend (Ads) {renderSortIndicator('total_spend')}
              </th>
              <th onClick={() => handleSort('total_revenue')} className="px-5 py-3.5 text-right cursor-pointer hover:text-white transition-colors">
                Revenue (AdX) {renderSortIndicator('total_revenue')}
              </th>
              <th onClick={() => handleSort('net_profit')} className="px-5 py-3.5 text-right cursor-pointer hover:text-white transition-colors">
                Net Profit {renderSortIndicator('net_profit')}
              </th>
              {!isSingleDay && (
                <th onClick={() => handleSort('roi')} className="px-5 py-3.5 text-right cursor-pointer hover:text-white transition-colors">
                  ROI {renderSortIndicator('roi')}
                </th>
              )}
              <th onClick={() => handleSort('ad_requests')} className="px-5 py-3.5 text-right cursor-pointer hover:text-white transition-colors">
                Ad Requests {renderSortIndicator('ad_requests')}
              </th>
              <th onClick={() => handleSort('matched_requests')} className="px-5 py-3.5 text-right cursor-pointer hover:text-white transition-colors">
                Matched Requests {renderSortIndicator('matched_requests')}
              </th>
              <th onClick={() => handleSort('match_rate')} className="px-5 py-3.5 text-right cursor-pointer hover:text-white transition-colors">
                MR AdX {renderSortIndicator('match_rate')}
              </th>
              <th onClick={() => handleSort('ecpm')} className="px-5 py-3.5 text-right cursor-pointer hover:text-white transition-colors">
                eCPM {renderSortIndicator('ecpm')}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/50">
            {sortedSites.map((site, idx) => {
              const hasSpend = site.total_spend > 0;
              const isProfitable = site.net_profit >= 0;
              const compLabel = site.comparison_period_label || 'vs periode sebelumnya';

              return (
                <tr key={idx} className="hover:bg-slate-700/40 transition-colors group">
                  <td className="px-5 py-4 font-semibold text-white">
                    <div className="flex flex-col space-y-1">
                      <button
                        onClick={() => setSelectedDomain(site.domain)}
                        className="flex items-center space-x-2 text-left hover:text-emerald-400 transition-colors focus:outline-none cursor-pointer"
                        title="Klik untuk melihat detail per negara"
                      >
                        <span className="w-2 h-2 rounded-full bg-emerald-400 group-hover:scale-125 transition-transform"></span>
                        <span className="text-sm font-bold hover:underline decoration-emerald-400 underline-offset-4">
                          {site.domain}
                        </span>
                      </button>

                      {site.assigned_customer_ids && site.assigned_customer_ids.length > 0 ? (
                        <div className="flex items-center space-x-1 pl-4">
                          <LinkIcon className="w-3 h-3 text-sky-400 shrink-0" />
                          <span className="text-[10px] font-mono text-sky-300">
                            Ads ID: {site.assigned_customer_ids.join(', ')}
                          </span>
                        </div>
                      ) : (
                        <span className="text-[10px] text-slate-500 pl-4 italic">
                          Belum dipasang Ads ID
                        </span>
                      )}
                    </div>
                  </td>

                  <td className="px-5 py-4 text-right">
                    <div className="flex flex-col items-end">
                      <span className={`font-medium ${hasSpend ? 'text-rose-400' : 'text-slate-500'}`}>
                        {hasSpend ? formatCurrency(site.total_spend) : '-'}
                      </span>
                      {hasSpend && renderDeltaBadge(site.spend_change_pct, true, compLabel)}
                    </div>
                  </td>

                  <td className="px-5 py-4 text-right">
                    <div className="flex flex-col items-end">
                      <span className="font-bold text-emerald-400">{formatCurrency(site.total_revenue)}</span>
                      {renderDeltaBadge(site.revenue_change_pct, false, compLabel)}
                    </div>
                  </td>

                  <td className="px-5 py-4 text-right">
                    <div className="flex flex-col items-end">
                      {hasSpend ? (
                        <span className={`inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg text-xs font-bold border ${
                          isProfitable
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                            : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                        }`}>
                          {isProfitable ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                          <span>{formatCurrency(site.net_profit)}</span>
                        </span>
                      ) : (
                        <span className="text-emerald-400 font-bold">{formatCurrency(site.total_revenue)}</span>
                      )}
                      {renderDeltaBadge(site.profit_change_pct, false, compLabel)}
                    </div>
                  </td>

                  {!isSingleDay && (
                    <td className="px-5 py-4 text-right">
                      <div className="flex flex-col items-end font-mono font-bold">
                        {hasSpend ? (
                          <span className={isProfitable ? 'text-emerald-400' : 'text-rose-400'}>
                            {site.roi > 0 ? `+${site.roi}%` : `${site.roi}%`}
                          </span>
                        ) : (
                          <span className="text-slate-500">N/A</span>
                        )}
                        {hasSpend && renderDeltaBadge(site.roi_change_pct, false, compLabel)}
                      </div>
                    </td>
                  )}

                  <td className="px-5 py-4 text-right font-mono text-slate-300">
                    {(site.ad_requests || 0).toLocaleString()}
                  </td>

                  <td className="px-5 py-4 text-right font-mono text-slate-300">
                    {(site.matched_requests || 0).toLocaleString()}
                  </td>

                  <td className="px-5 py-4 text-right font-mono font-semibold text-indigo-300">
                    {(site.match_rate || 0).toFixed(1)}%
                  </td>

                  <td className="px-5 py-4 text-right font-mono font-semibold text-sky-400">{formatCurrency(site.ecpm)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

