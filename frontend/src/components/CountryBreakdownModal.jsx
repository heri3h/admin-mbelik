import React, { useState, useEffect } from 'react';
import { X, Globe, TrendingUp, TrendingDown, Search, ArrowLeft, Loader2, Layers } from 'lucide-react';
import { dashboardService } from '../services/api';

export default function CountryBreakdownModal({ domain, startDate, endDate, onClose }) {
  const [countries, setCountries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Level 1: Country list | Level 2: Selected Country (Shows Ad Units inside that country)
  const [selectedCountry, setSelectedCountry] = useState(null);
  const [adUnits, setAdUnits] = useState([]);
  const [loadingAdUnits, setLoadingAdUnits] = useState(false);

  // Table Sort State
  const [sortColumn, setSortColumn] = useState('revenue');
  const [sortDirection, setSortDirection] = useState('desc');

  useEffect(() => {
    const fetchCountryData = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await dashboardService.getSiteCountries(domain, startDate, endDate);
        setCountries(data || []);
      } catch (err) {
        console.error('Failed fetching site country metrics', err);
        setError('Failed loading country data. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    if (domain) {
      fetchCountryData();
    }
  }, [domain, startDate, endDate]);

  useEffect(() => {
    const fetchAdUnits = async () => {
      if (!selectedCountry) {
        setAdUnits([]);
        return;
      }
      setLoadingAdUnits(true);
      try {
        const data = await dashboardService.getSiteCountryPlacements(domain, selectedCountry.country, startDate, endDate);
        setAdUnits(data || []);
      } catch (err) {
        console.error('Failed fetching ad unit placement data', err);
        setAdUnits([]);
      } finally {
        setLoadingAdUnits(false);
      }
    };

    fetchAdUnits();
  }, [selectedCountry, domain, startDate, endDate]);

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

  const handleCountryClick = (countryObj) => {
    setSelectedCountry(countryObj);
    setSearchTerm('');
    setSortColumn('revenue');
    setSortDirection('desc');
  };

  const handleBackToCountries = () => {
    setSelectedCountry(null);
    setSearchTerm('');
    setSortColumn('revenue');
    setSortDirection('desc');
  };

  // Calculations for Summary Cards
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
  const avgEcpm = countries.length > 0 ? (totalRev / (totalImps / 1000) || 0) : 0;
  const avgUpr = totalAdReqs > 0 ? (totalRev / (totalAdReqs / 1000)) : 0;

  // Level 1: Filter & Sort Country List
  const filteredCountries = countries.filter(c =>
    c.country.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (c.country_code && c.country_code.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const sortedCountries = [...filteredCountries].sort((a, b) => {
    let colKey = sortColumn === 'name' ? 'country' : sortColumn;
    let aVal = a[colKey] ?? 0;
    let bVal = b[colKey] ?? 0;
    if (typeof aVal === 'string') {
      return sortDirection === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    }
    return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
  });

  // Level 2: Filter & Sort Ad Units within Selected Country
  const level2TotalAdReqs = adUnits.reduce((sum, p) => sum + (p.ad_requests || 0), 0);
  const level2TotalMatchedReqs = adUnits.reduce((sum, p) => sum + (p.matched_requests || 0), 0);
  const level2AvgMatchRate = level2TotalAdReqs > 0 ? (level2TotalMatchedReqs / level2TotalAdReqs * 100) : 0;
  const level2TotalImps = adUnits.reduce((sum, p) => sum + (p.impressions || 0), 0);
  const level2TotalClicks = adUnits.reduce((sum, p) => sum + (p.clicks || 0), 0);
  const level2AvgCtr = level2TotalImps > 0 ? (level2TotalClicks / level2TotalImps * 100) : 0;

  const filteredAdUnits = adUnits.filter(p =>
    p.ad_unit.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const sortedAdUnits = [...filteredAdUnits].sort((a, b) => {
    let colKey = sortColumn === 'name' ? 'ad_unit' : sortColumn;
    let aVal = a[colKey] ?? 0;
    let bVal = b[colKey] ?? 0;
    if (typeof aVal === 'string') {
      return sortDirection === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    }
    return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
  });

  // Calculate active summary metrics based on Level 1 (All Countries) or Level 2 (Selected Country)
  const activeRev = selectedCountry ? selectedCountry.revenue : totalRev;
  const activeSpend = selectedCountry ? selectedCountry.spend : totalSpend;
  const activeProfit = activeRev - activeSpend;
  const activeEcpm = selectedCountry ? selectedCountry.ecpm : avgEcpm;
  const activeRoi = selectedCountry ? selectedCountry.roi : overallRoi;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl w-full max-w-6xl max-h-[90vh] flex flex-col overflow-hidden">
        
        {/* Modal Header */}
        <div className="p-5 border-b border-slate-700/70 bg-slate-900/90 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shrink-0">
          <div className="flex items-center space-x-3">
            {selectedCountry ? (
              <button
                onClick={handleBackToCountries}
                className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-all border border-slate-700 flex items-center space-x-1 shrink-0 cursor-pointer"
                title="Back to Country List"
              >
                <ArrowLeft className="w-5 h-5 text-emerald-400" />
              </button>
            ) : (
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center shrink-0">
                <Globe className="w-5 h-5 text-emerald-400" />
              </div>
            )}

            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                {selectedCountry ? (
                  <>
                    <span>Ad Unit Performance Report - {selectedCountry.flag_emoji} {selectedCountry.country}</span>
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      {domain}
                    </span>
                  </>
                ) : (
                  <>
                    <span>Domain Country Performance Breakdown</span>
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      {domain}
                    </span>
                  </>
                )}
              </h2>
              <p className="text-slate-400 text-xs mt-0.5">
                {selectedCountry ? (
                  <span>Ad Unit details for country <strong className="text-white">{selectedCountry.country}</strong> ({startDate} to {endDate})</span>
                ) : (
                  <span>Click on any country row to view ad unit breakdown for that country. ({startDate} to {endDate})</span>
                )}
              </p>
            </div>
          </div>

          {/* Top Actions Header */}
          <div className="flex items-center space-x-3">
            {selectedCountry && (
              <button
                onClick={handleBackToCountries}
                className="px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-emerald-600/20 hover:bg-emerald-600 text-emerald-300 hover:text-white transition-all border border-emerald-500/30 flex items-center space-x-1.5 cursor-pointer"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>← Back to Country List</span>
              </button>
            )}

            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-white bg-slate-800/80 hover:bg-slate-800 rounded-xl transition-all border border-slate-700/50 shrink-0 cursor-pointer"
              title="Close Modal"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-6 overflow-y-auto flex-1">
          {loading ? (
            <div className="min-h-[350px] flex flex-col items-center justify-center space-y-3 text-slate-400">
              <Loader2 className="w-8 h-8 animate-spin text-emerald-400" />
              <span className="text-sm font-medium">Loading country breakdown metrics...</span>
            </div>
          ) : error ? (
            <div className="min-h-[300px] flex flex-col items-center justify-center text-center p-6 bg-rose-500/10 border border-rose-500/30 rounded-2xl text-rose-400">
              <span className="text-sm font-semibold">{error}</span>
            </div>
          ) : (
            <>
              {/* Executive Summary Cards inside Modal */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
                <div className="bg-slate-800/80 border border-slate-700/60 p-4 rounded-xl">
                  <span className="text-slate-400 text-[11px] font-semibold uppercase">Total Revenue</span>
                  <p className="text-lg font-extrabold text-emerald-400 mt-1">{formatCurrency(activeRev)}</p>
                </div>
                <div className="bg-slate-800/80 border border-slate-700/60 p-4 rounded-xl">
                  <span className="text-slate-400 text-[11px] font-semibold uppercase">Total Spend</span>
                  <p className="text-lg font-extrabold text-rose-400 mt-1">{formatCurrency(activeSpend)}</p>
                </div>
                <div className="bg-slate-800/80 border border-slate-700/60 p-4 rounded-xl">
                  <span className="text-slate-400 text-[11px] font-semibold uppercase">Net Profit</span>
                  <p className={`text-lg font-extrabold mt-1 ${activeProfit >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {formatCurrency(activeProfit)}
                  </p>
                </div>
                <div className="bg-slate-800/80 border border-slate-700/60 p-4 rounded-xl">
                  <span className="text-slate-400 text-[11px] font-semibold uppercase">Avg eCPM</span>
                  <p className="text-lg font-extrabold text-sky-400 mt-1">{formatCurrency(activeEcpm)}</p>
                </div>
              </div>

              {/* Table Controls (Search & Counter) */}
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                <div className="relative w-full sm:w-64">
                  <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
                  <input
                    type="text"
                    placeholder={selectedCountry ? "Search ad unit placement..." : "Search country..."}
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="bg-slate-900 border border-slate-700 text-xs text-white pl-8 pr-3 py-1.5 rounded-lg focus:outline-none focus:border-emerald-500 w-full"
                  />
                </div>

                <div className="flex items-center space-x-2">
                  {selectedCountry ? (
                    <span className="text-xs font-semibold px-2.5 py-1 bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-lg">
                      {filteredAdUnits.length} Ad Units ({selectedCountry.country})
                    </span>
                  ) : (
                    <span className="text-xs font-semibold px-2.5 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-lg">
                      {filteredCountries.length} Countries (Click country for details)
                    </span>
                  )}
                </div>
              </div>

              {/* Data Table */}
              <div className="border border-slate-700/60 rounded-xl shadow-sm overflow-hidden">
                <div className="overflow-x-auto w-full max-w-full">
                  <table className="w-full text-left text-xs text-slate-300 border-separate border-spacing-0">
                    
                    {/* --- UNIFIED UNIFORM THEAD ACROSS LEVEL 1 & LEVEL 2 --- */}
                    <thead className="bg-slate-900 text-slate-400 uppercase font-semibold text-[10px] tracking-wider select-none shadow-md">
                      <tr>
                        <th onClick={() => handleSort('name')} className="sticky top-0 z-30 bg-slate-900 px-4 py-3 border-b border-slate-700/60 cursor-pointer hover:text-white transition-colors whitespace-nowrap">
                          {selectedCountry ? 'Ad Unit / Placement' : 'Country'} {renderSortIndicator('name')}
                        </th>
                        <th onClick={() => handleSort('spend')} className="sticky top-0 z-30 bg-slate-900 px-4 py-3 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors whitespace-nowrap">
                          Spend (Ads) {renderSortIndicator('spend')}
                        </th>
                        <th onClick={() => handleSort('revenue')} className="sticky top-0 z-30 bg-slate-900 px-4 py-3 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors whitespace-nowrap">
                          Revenue (AdX) {renderSortIndicator('revenue')}
                        </th>
                        <th onClick={() => handleSort('ecpm')} className="sticky top-0 z-30 bg-slate-900 px-4 py-3 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors whitespace-nowrap">
                          CPM AdX (eCPM) {renderSortIndicator('ecpm')}
                        </th>
                        <th onClick={() => handleSort('ad_requests')} className="sticky top-0 z-30 bg-slate-900 px-4 py-3 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors whitespace-nowrap">
                          Ad Requests {renderSortIndicator('ad_requests')}
                        </th>
                        <th onClick={() => handleSort('matched_requests')} className="sticky top-0 z-30 bg-slate-900 px-4 py-3 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors whitespace-nowrap">
                          Matched Requests {renderSortIndicator('matched_requests')}
                        </th>
                        <th onClick={() => handleSort('match_rate')} className="sticky top-0 z-30 bg-slate-900 px-4 py-3 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors whitespace-nowrap">
                          Match Rate {renderSortIndicator('match_rate')}
                        </th>
                        <th onClick={() => handleSort('ctr')} className="sticky top-0 z-30 bg-slate-900 px-4 py-3 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors whitespace-nowrap">
                          CTR {renderSortIndicator('ctr')}
                        </th>
                        <th onClick={() => handleSort('roi')} className="sticky top-0 z-30 bg-slate-900 px-4 py-3 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors whitespace-nowrap">
                          ROI {renderSortIndicator('roi')}
                        </th>
                        <th onClick={() => handleSort('net_profit')} className="sticky top-0 z-30 bg-slate-900 px-4 py-3 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors whitespace-nowrap">
                          Profit {renderSortIndicator('net_profit')}
                        </th>
                        <th onClick={() => handleSort('upr')} className="sticky top-0 z-30 bg-slate-900 px-4 py-3 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors whitespace-nowrap">
                          UPR & RPM {renderSortIndicator('upr')}
                        </th>
                      </tr>
                    </thead>

                    <tbody className="divide-y divide-slate-700/50">
                      {/* --- LEVEL 1: COUNTRY LIST --- */}
                      {!selectedCountry ? (
                        sortedCountries.length === 0 ? (
                          <tr>
                            <td colSpan="11" className="px-4 py-8 text-center text-slate-400 italic">
                              No country data found.
                            </td>
                          </tr>
                        ) : (
                          sortedCountries.map((c, idx) => {
                            const hasSpend = c.spend > 0;
                            const isProfitable = c.net_profit >= 0;

                            return (
                              <tr
                                key={idx}
                                onClick={() => handleCountryClick(c)}
                                className="hover:bg-emerald-500/10 cursor-pointer transition-colors group"
                                title="Click to view ad unit details for this country"
                              >
                                <td className="px-4 py-3.5 font-semibold text-white">
                                  <div className="flex items-center space-x-2">
                                    <span className="text-base group-hover:scale-125 transition-transform">{c.flag_emoji}</span>
                                    <span className="font-bold group-hover:text-emerald-400 group-hover:underline underline-offset-4 decoration-emerald-400 transition-colors">
                                      {c.country}
                                    </span>
                                    <span className="text-[10px] font-mono text-slate-400">({c.country_code})</span>
                                  </div>
                                </td>

                                <td className="px-4 py-3.5 text-right font-medium text-rose-400">
                                  {hasSpend ? formatCurrency(c.spend) : <span className="text-slate-500">-</span>}
                                </td>

                                <td className="px-4 py-3.5 text-right font-bold text-emerald-400">
                                  {formatCurrency(c.revenue)}
                                </td>

                                <td className="px-4 py-3.5 text-right font-mono font-semibold text-sky-400">
                                  {formatCurrency(c.ecpm)}
                                </td>

                                <td className="px-4 py-3.5 text-right font-mono text-slate-300">
                                  {(c.ad_requests || 0).toLocaleString()}
                                </td>

                                <td className="px-4 py-3.5 text-right font-mono text-slate-300">
                                  {(c.matched_requests || 0).toLocaleString()}
                                </td>

                                <td className="px-4 py-3.5 text-right font-mono font-semibold text-indigo-300">
                                  {(c.match_rate || 0).toFixed(1)}%
                                </td>

                                <td className="px-4 py-3.5 text-right font-mono text-slate-300">
                                  {(c.ctr || 0).toFixed(2)}%
                                </td>

                                <td className="px-4 py-3.5 text-right font-mono font-bold">
                                  {hasSpend ? (
                                    <span className={isProfitable ? 'text-emerald-400' : 'text-rose-400'}>
                                      {c.roi > 0 ? `+${c.roi.toFixed(1)}%` : `${c.roi.toFixed(1)}%`}
                                    </span>
                                  ) : (
                                    <span className="text-slate-500">N/A</span>
                                  )}
                                </td>

                                <td className="px-4 py-3.5 text-right">
                                  {hasSpend ? (
                                    <span className={`inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg text-xs font-bold border ${
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

                                <td className="px-4 py-3.5 text-right font-mono font-semibold text-amber-300">
                                  {formatCurrency(c.upr || 0)}
                                </td>
                              </tr>
                            );
                          })
                        )
                      ) : (
                        /* --- LEVEL 2: AD UNITS WITHIN SELECTED COUNTRY --- */
                        loadingAdUnits ? (
                          <tr>
                            <td colSpan="11" className="px-4 py-8 text-center text-slate-400">
                              <div className="flex items-center justify-center space-x-2">
                                <Loader2 className="w-5 h-5 animate-spin text-emerald-400" />
                                <span>Loading ad unit placements for {selectedCountry.country}...</span>
                              </div>
                            </td>
                          </tr>
                        ) : sortedAdUnits.length === 0 ? (
                          <tr>
                            <td colSpan="11" className="px-4 py-8 text-center text-slate-400 italic">
                              No ad unit placement data found for this country.
                            </td>
                          </tr>
                        ) : (
                          sortedAdUnits.map((p, idx) => {
                            const pRoi = p.roi || 0;
                            const pProfit = p.net_profit || 0;
                            const isPProfitable = pProfit >= 0;

                            return (
                              <tr key={idx} className="hover:bg-slate-700/40 transition-colors">
                                <td className="px-4 py-3.5 font-semibold text-white">
                                  <div className="flex flex-col space-y-0.5">
                                    <span className="font-bold text-slate-100">{p.ad_unit}</span>
                                    <span className="text-[10px] text-slate-400 font-mono">Domain: {p.domain}</span>
                                  </div>
                                </td>

                                <td className="px-4 py-3.5 text-right font-medium text-rose-400">
                                  {p.spend > 0 ? formatCurrency(p.spend) : <span className="text-slate-500">-</span>}
                                </td>

                                <td className="px-4 py-3.5 text-right font-bold text-emerald-400">
                                  {formatCurrency(p.revenue)}
                                </td>

                                <td className="px-4 py-3.5 text-right font-mono font-semibold text-sky-400">
                                  {formatCurrency(p.ecpm)}
                                </td>

                                <td className="px-4 py-3.5 text-right font-mono text-slate-300">
                                  {(p.ad_requests || 0).toLocaleString()}
                                </td>

                                <td className="px-4 py-3.5 text-right font-mono text-slate-300">
                                  {(p.matched_requests || 0).toLocaleString()}
                                </td>

                                <td className="px-4 py-3.5 text-right font-mono font-semibold text-indigo-300">
                                  {(p.match_rate || 0).toFixed(1)}%
                                </td>

                                <td className="px-4 py-3.5 text-right font-mono text-slate-300">
                                  {(p.ctr || 0).toFixed(2)}%
                                </td>

                                <td className="px-4 py-3.5 text-right font-mono font-bold">
                                  {p.spend > 0 ? (
                                    <span className={isPProfitable ? 'text-emerald-400' : 'text-rose-400'}>
                                      {pRoi > 0 ? `+${pRoi.toFixed(1)}%` : `${pRoi.toFixed(1)}%`}
                                    </span>
                                  ) : (
                                    <span className="text-slate-500">N/A</span>
                                  )}
                                </td>

                                <td className="px-4 py-3.5 text-right">
                                  {p.spend > 0 ? (
                                    <span className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-bold border ${
                                      isPProfitable
                                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                                        : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                                    }`}>
                                      {isPProfitable ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                                      <span>{formatCurrency(pProfit)}</span>
                                    </span>
                                  ) : (
                                    <span className="text-emerald-400 font-bold">{formatCurrency(p.revenue)}</span>
                                  )}
                                </td>

                                <td className="px-4 py-3.5 text-right font-mono font-semibold text-amber-300">
                                  {formatCurrency(p.upr || 0)}
                                </td>
                              </tr>
                            );
                          })
                        )
                      )}
                    </tbody>

                    {/* --- UNIFIED TFOOT ACROSS LEVEL 1 & LEVEL 2 --- */}
                    <tfoot className="bg-slate-950 text-slate-200 font-semibold border-t border-slate-700/80 text-[11px]">
                      <tr>
                        <td className="px-4 py-3 font-bold">
                          {selectedCountry ? `Total Ad Units (${selectedCountry.country})` : 'Total / Average All Countries'}
                        </td>
                        <td className="px-4 py-3 text-right font-bold text-rose-400">{formatCurrency(activeSpend)}</td>
                        <td className="px-4 py-3 text-right font-bold text-emerald-400">{formatCurrency(activeRev)}</td>
                        <td className="px-4 py-3 text-right font-mono text-sky-400">{formatCurrency(activeEcpm)}</td>
                        <td className="px-4 py-3 text-right font-mono">
                          {(selectedCountry ? level2TotalAdReqs : totalAdReqs).toLocaleString()}
                        </td>
                        <td className="px-4 py-3 text-right font-mono">
                          {(selectedCountry ? level2TotalMatchedReqs : totalMatchedReqs).toLocaleString()}
                        </td>
                        <td className="px-4 py-3 text-right font-mono text-indigo-300">
                          {(selectedCountry ? level2AvgMatchRate : avgMatchRate).toFixed(1)}%
                        </td>
                        <td className="px-4 py-3 text-right font-mono">
                          {(selectedCountry ? level2AvgCtr : avgCtr).toFixed(2)}%
                        </td>
                        <td className="px-4 py-3 text-right font-mono font-bold">
                          {activeSpend > 0 ? (
                            <span className={activeProfit >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                              {activeRoi > 0 ? `+${activeRoi.toFixed(1)}%` : `${activeRoi.toFixed(1)}%`}
                            </span>
                          ) : (
                            <span className="text-slate-500">N/A</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-right font-bold text-emerald-400">{formatCurrency(activeProfit)}</td>
                        <td className="px-4 py-3 text-right font-mono text-amber-300">
                          {formatCurrency(selectedCountry ? selectedCountry.upr || 0 : avgUpr)}
                        </td>
                      </tr>
                    </tfoot>

                  </table>

                </div>
              </div>
            </>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-700/70 bg-slate-900/90 flex justify-between items-center shrink-0">
          <div>
            {selectedCountry ? (
              <button
                onClick={handleBackToCountries}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-emerald-400 hover:text-white transition-all border border-slate-700 flex items-center space-x-1.5 cursor-pointer"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>← Back to Country List</span>
              </button>
            ) : (
              <span className="text-xs text-slate-400">
                💡 Tip: Click on any country row to view ad unit breakdown.
              </span>
            )}
          </div>

          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-white transition-all border border-slate-700 cursor-pointer"
          >
            Close
          </button>
        </div>

      </div>
    </div>
  );
}
