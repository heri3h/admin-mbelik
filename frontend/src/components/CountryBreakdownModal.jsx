import React, { useState, useEffect } from 'react';
import { X, Search, Loader2, Globe, TrendingUp, TrendingDown, LayoutGrid, ArrowLeft } from 'lucide-react';
import { dashboardService } from '../services/api';

export default function CountryBreakdownModal({ domain, startDate, endDate, onClose }) {
  const [countries, setCountries] = useState([]);
  const [placements, setPlacements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortColumn, setSortColumn] = useState('revenue');
  const [sortDirection, setSortDirection] = useState('desc');

  // Selected country for Level 2 drill-down (null = Level 1 Country List)
  const [selectedCountry, setSelectedCountry] = useState(null);
  const [countryPlacements, setCountryPlacements] = useState([]);
  const [loadingCountryPlacements, setLoadingCountryPlacements] = useState(false);

  useEffect(() => {
    let isMounted = true;
    const fetchDomainDetails = async () => {
      setLoading(true);
      try {
        const countryData = await dashboardService.getSiteCountries(domain, startDate, endDate);

        if (isMounted) {
          setCountries(countryData || []);
        }
      } catch (err) {
        console.error('Failed fetching site breakdown details:', err);
        if (isMounted) setCountries([]);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    if (domain) {
      fetchDomainDetails();
    }

    return () => {
      isMounted = false;
    };
  }, [domain, startDate, endDate]);

  const handleCountryClick = async (countryObj) => {
    setSelectedCountry(countryObj);
    setCountryPlacements([]);
    setSearchTerm('');
    setSortColumn('revenue');
    setLoadingCountryPlacements(true);

    try {
      const realPlacements = await dashboardService.getSiteCountryPlacements(domain, countryObj.country, startDate, endDate);
      setCountryPlacements(realPlacements || []);
    } catch (err) {
      console.error('Failed fetching country placements:', err);
      setCountryPlacements([]);
    } finally {
      setLoadingCountryPlacements(false);
    }
  };

  const handleBackToCountries = () => {
    setSelectedCountry(null);
    setCountryPlacements([]);
    setSearchTerm('');
    setSortColumn('revenue');
  };

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

  // Base Summary Calculations across the entire domain dataset (Level 1)
  const totalRev = countries.reduce((sum, item) => sum + (item.revenue || 0), 0);
  const totalSpend = countries.reduce((sum, item) => sum + (item.spend || 0), 0);
  const totalProfit = totalRev - totalSpend;
  const totalImps = countries.reduce((sum, item) => sum + (item.impressions || 0), 0);
  const totalClicks = countries.reduce((sum, item) => sum + (item.clicks || 0), 0);
  const totalAdReqs = countries.reduce((sum, item) => sum + (item.ad_requests || 0), 0);
  const totalMatchedReqs = countries.reduce((sum, item) => sum + (item.matched_requests || 0), 0);

  const avgEcpm = totalImps > 0 ? (totalRev / totalImps * 1000) : 0;
  const overallRoi = totalSpend > 0 ? (totalRev / totalSpend * 100) : 0;
  const avgMatchRate = totalAdReqs > 0 
    ? ((totalMatchedReqs / totalAdReqs) * 100) 
    : (countries.length > 0 ? (countries.reduce((sum, item) => sum + (item.match_rate || 0), 0) / countries.length) : 0);
  const avgUpr = countries.length > 0 
    ? (countries.reduce((sum, item) => sum + (item.upr || 0), 0) / countries.length) 
    : 0;
  const avgCtr = totalImps > 0 ? (totalClicks / totalImps * 100) : 0;

  // --- Level 1: Country View Dataset ---
  const filteredCountries = (countries || []).filter(c => {
    if (!c) return false;
    const countryName = (c.country || '').toString().toLowerCase();
    const countryCode = (c.country_code || '').toString().toLowerCase();
    const search = (searchTerm || '').toString().toLowerCase();
    return countryName.includes(search) || countryCode.includes(search);
  });

  const sortedCountries = [...filteredCountries].sort((a, b) => {
    let colKey = sortColumn === 'name' ? 'country' : sortColumn;
    let aVal = a[colKey] ?? 0;
    let bVal = b[colKey] ?? 0;
    if (typeof aVal === 'string') {
      return sortDirection === 'asc' ? aVal.localeCompare(String(bVal)) : String(bVal).localeCompare(String(aVal));
    }
    return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
  });

  // --- Level 2: Ad Unit View Dataset (Filtered for Selected Country) ---
  const getCountryAdUnits = () => {
    if (!selectedCountry) return [];

    const cSpend = selectedCountry.spend || 0;
    const cRev = selectedCountry.revenue || 0;
    const cImps = selectedCountry.impressions || 0;
    const cClicks = selectedCountry.clicks || 0;
    const cAdReqs = selectedCountry.ad_requests || 0;
    const cMatchedReqs = selectedCountry.matched_requests || 0;
    const cMatchRate = selectedCountry.match_rate || avgMatchRate || 34.8;
    const cUpr = selectedCountry.upr || 0;

    // Use real country placement records from API if available
    if (countryPlacements && countryPlacements.length > 0) {
      const totPlacRev = countryPlacements.reduce((sum, p) => sum + (p.total_revenue || 0), 0);
      return countryPlacements.map((p) => {
        const pRev = p.total_revenue || 0;
        const pImps = p.impressions || 0;
        const pClicks = p.clicks || 0;
        const pShare = totPlacRev > 0 ? (pRev / totPlacRev) : (1 / countryPlacements.length);
        const pSpend = cSpend * pShare;
        const pProfit = pRev - pSpend;
        const pRoi = pSpend > 0 ? (pRev / pSpend * 100) : 0;
        const pEcpm = p.ecpm || (pImps > 0 ? pRev / pImps * 1000 : 0);
        const pCtr = pImps > 0 ? (pClicks / pImps * 100) : 0;
        const pAdR = (p.ad_requests !== undefined && p.ad_requests !== null) ? p.ad_requests : 0;
        const pMatchedR = (p.matched_requests !== undefined && p.matched_requests !== null) ? p.matched_requests : 0;
        const pMr = (p.match_rate !== undefined && p.match_rate !== null) ? p.match_rate : (pAdR > 0 ? ((pMatchedR / pAdR) * 100) : 0);

        return {
          ad_unit: p.ad_unit || 'Standard Ad Unit',
          spend: pSpend,
          revenue: pRev,
          ecpm: pEcpm,
          ad_requests: pAdR,
          matched_requests: pMatchedR,
          match_rate: pMr,
          ctr: pCtr,
          roi: pRoi,
          net_profit: pProfit,
          upr: cUpr,
          rpm: pEcpm
        };
      });
    }

    return [];
  };

  const countryAdUnits = getCountryAdUnits();

  // Dynamic totals for Level 2 Ad Unit drill-down footer
  const level2TotalAdReqs = countryAdUnits.reduce((sum, p) => sum + (p.ad_requests || 0), 0);
  const level2TotalMatchedReqs = countryAdUnits.reduce((sum, p) => sum + (p.matched_requests || 0), 0);
  const level2AvgMatchRate = level2TotalAdReqs > 0
    ? ((level2TotalMatchedReqs / level2TotalAdReqs) * 100)
    : (selectedCountry ? (selectedCountry.match_rate || 0) : 0);

  const level2TotalImps = countryPlacements.reduce((sum, p) => sum + (p.impressions || 0), 0);
  const level2TotalClicks = countryPlacements.reduce((sum, p) => sum + (p.clicks || 0), 0);
  const level2AvgCtr = level2TotalImps > 0 ? ((level2TotalClicks / level2TotalImps) * 100) : (selectedCountry ? (selectedCountry.ctr || 0) : 0);

  const filteredAdUnits = (countryAdUnits || []).filter(p => {
    if (!p) return false;
    const adUnitName = (p.ad_unit || '').toString().toLowerCase();
    const search = (searchTerm || '').toString().toLowerCase();
    return adUnitName.includes(search);
  });

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
                title="Kembali ke Daftar Negara"
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
                    <span>Report Unit Iklan (Ad Unit) - {selectedCountry.flag_emoji} {selectedCountry.country}</span>
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      {domain}
                    </span>
                  </>
                ) : (
                  <>
                    <span>Breakdown Kinerja Domain Per Negara</span>
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      {domain}
                    </span>
                  </>
                )}
              </h2>
              <p className="text-slate-400 text-xs mt-0.5">
                {selectedCountry ? (
                  <span>Rincian unit iklan (Ad Unit) untuk negara <strong className="text-white">{selectedCountry.country}</strong> ({startDate} s.d {endDate})</span>
                ) : (
                  <span>Klik salah satu baris negara untuk melihat report rincian Ad Unit di negara tersebut. ({startDate} s.d {endDate})</span>
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
                <span>← Kembali ke Daftar Negara</span>
              </button>
            )}

            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-white bg-slate-800/80 hover:bg-slate-800 rounded-xl transition-all border border-slate-700/50 shrink-0 cursor-pointer"
              title="Tutup Modal"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-5 overflow-y-auto space-y-5 flex-1">
          {loading || loadingCountryPlacements ? (
            <div className="min-h-[300px] flex flex-col items-center justify-center space-y-3 text-slate-400">
              <Loader2 className="w-8 h-8 animate-spin text-emerald-400" />
              <span className="text-xs font-medium">
                {loadingCountryPlacements
                  ? `Memuat data unit iklan GAM untuk negara ${selectedCountry?.country}...`
                  : `Memuat data rincian untuk domain ${domain}...`}
              </span>
            </div>
          ) : (
            <>
              {/* Metric Summary Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                <div className="bg-slate-800/80 border border-slate-700/60 p-3.5 rounded-xl">
                  <span className="text-[11px] font-semibold text-slate-400 block">Total Revenue</span>
                  <span className="text-base font-extrabold text-emerald-400 block mt-0.5">{formatCurrency(activeRev)}</span>
                </div>
                <div className="bg-slate-800/80 border border-slate-700/60 p-3.5 rounded-xl">
                  <span className="text-[11px] font-semibold text-slate-400 block">Total Spend</span>
                  <span className="text-base font-extrabold text-rose-400 block mt-0.5">{formatCurrency(activeSpend)}</span>
                </div>
                <div className="bg-slate-800/80 border border-slate-700/60 p-3.5 rounded-xl">
                  <span className="text-[11px] font-semibold text-slate-400 block">Net Profit</span>
                  <span className={`text-base font-extrabold block mt-0.5 ${activeProfit >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {formatCurrency(activeProfit)}
                  </span>
                </div>
                <div className="bg-slate-800/80 border border-slate-700/60 p-3.5 rounded-xl">
                  <span className="text-[11px] font-semibold text-slate-400 block">Rata-rata eCPM</span>
                  <span className="text-base font-extrabold text-sky-400 block mt-0.5">{formatCurrency(activeEcpm)}</span>
                </div>
                <div className="bg-slate-800/80 border border-slate-700/60 p-3.5 rounded-xl">
                  <span className="text-[11px] font-semibold text-slate-400 block">Overall ROI</span>
                  <span className={`text-base font-extrabold block mt-0.5 ${activeRoi >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {activeSpend > 0 ? `${activeRoi.toFixed(1)}%` : 'N/A'}
                  </span>
                </div>
              </div>

              {/* Toolbar & Search */}
              <div className="flex items-center justify-between gap-4">
                <div className="relative flex-1 sm:flex-initial">
                  <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
                  <input
                    type="text"
                    placeholder={selectedCountry ? `Cari unit iklan di ${selectedCountry.country}...` : "Cari nama atau kode negara..."}
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="bg-slate-950 border border-slate-700 text-xs text-white pl-8 pr-3 py-1.5 rounded-lg focus:outline-none focus:border-emerald-500 w-full sm:w-64"
                  />
                </div>

                <div className="flex items-center space-x-2">
                  {selectedCountry ? (
                    <span className="text-xs font-semibold px-2.5 py-1 bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-lg">
                      {filteredAdUnits.length} Unit Iklan ({selectedCountry.country})
                    </span>
                  ) : (
                    <span className="text-xs font-semibold px-2.5 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-lg">
                      {filteredCountries.length} Negara (Klik negara untuk detail)
                    </span>
                  )}
                </div>
              </div>

              {/* Data Table */}
              <div className="border border-slate-700/60 rounded-xl overflow-hidden shadow-sm">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs text-slate-300 border-collapse">
                    
                    {/* --- UNIFIED UNIFORM THEAD ACROSS LEVEL 1 & LEVEL 2 --- */}
                    <thead className="sticky top-0 z-20 bg-slate-900/95 backdrop-blur text-slate-400 uppercase font-semibold text-[10px] tracking-wider border-b border-slate-700/60 select-none shadow-md">
                      <tr>
                        <th onClick={() => handleSort('name')} className="px-4 py-3 cursor-pointer hover:text-white transition-colors">
                          {selectedCountry ? 'Unit Iklan / Placement' : 'Negara'} {renderSortIndicator('name')}
                        </th>
                        <th onClick={() => handleSort('spend')} className="px-4 py-3 text-right cursor-pointer hover:text-white transition-colors">
                          Spend (Ads) {renderSortIndicator('spend')}
                        </th>
                        <th onClick={() => handleSort('revenue')} className="px-4 py-3 text-right cursor-pointer hover:text-white transition-colors">
                          Revenue (AdX) {renderSortIndicator('revenue')}
                        </th>
                        <th onClick={() => handleSort('ecpm')} className="px-4 py-3 text-right cursor-pointer hover:text-white transition-colors">
                          CPM AdX (eCPM) {renderSortIndicator('ecpm')}
                        </th>
                        <th onClick={() => handleSort('ad_requests')} className="px-4 py-3 text-right cursor-pointer hover:text-white transition-colors">
                          Ad Requests {renderSortIndicator('ad_requests')}
                        </th>
                        <th onClick={() => handleSort('matched_requests')} className="px-4 py-3 text-right cursor-pointer hover:text-white transition-colors">
                          Matched Requests {renderSortIndicator('matched_requests')}
                        </th>
                        <th onClick={() => handleSort('match_rate')} className="px-4 py-3 text-right cursor-pointer hover:text-white transition-colors">
                          Match Rate {renderSortIndicator('match_rate')}
                        </th>
                        <th onClick={() => handleSort('ctr')} className="px-4 py-3 text-right cursor-pointer hover:text-white transition-colors">
                          CTR {renderSortIndicator('ctr')}
                        </th>
                        <th onClick={() => handleSort('roi')} className="px-4 py-3 text-right cursor-pointer hover:text-white transition-colors">
                          ROI {renderSortIndicator('roi')}
                        </th>
                        <th onClick={() => handleSort('net_profit')} className="px-4 py-3 text-right cursor-pointer hover:text-white transition-colors">
                          Profit {renderSortIndicator('net_profit')}
                        </th>
                        <th onClick={() => handleSort('upr')} className="px-4 py-3 text-right cursor-pointer hover:text-white transition-colors">
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
                              Tidak ada data negara ditemukan.
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
                                title="Klik untuk melihat detail unit iklan (Ad Unit) di negara ini"
                              >
                                <td className="px-4 py-3.5 font-semibold text-white">
                                  <div className="flex items-center space-x-2">
                                    <span className="text-base group-hover:scale-125 transition-transform">{c.flag_emoji}</span>
                                    <span className="font-bold group-hover:text-emerald-400 group-hover:underline underline-offset-4 decoration-emerald-400 transition-colors">
                                      {c.country}
                                    </span>
                                    <span className="text-[10px] font-mono text-slate-400">({c.country_code})</span>
                                    <span className="text-[10px] bg-slate-800 text-emerald-400 border border-emerald-500/30 px-1.5 py-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity ml-1">
                                      Lihat Ad Unit →
                                    </span>
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

                                <td className="px-4 py-3.5 text-right font-mono text-indigo-300">
                                  {c.match_rate.toFixed(1)}%
                                </td>

                                <td className="px-4 py-3.5 text-right font-mono text-slate-300">
                                  {c.ctr.toFixed(2)}%
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
                                    <span className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-bold border ${
                                      isProfitable
                                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                                        : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                                    }`}>
                                      {isProfitable ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                                      <span>{formatCurrency(c.net_profit)}</span>
                                    </span>
                                  ) : (
                                    <span className="text-emerald-400 font-bold">{formatCurrency(c.revenue)}</span>
                                  )}
                                </td>

                                <td className="px-4 py-3.5 text-right font-mono">
                                  <div className="flex flex-col items-end">
                                    <span className="text-amber-300 font-semibold text-[11px]">
                                      {c.upr > 0 ? formatCurrency(c.upr) : '-'}
                                    </span>
                                    <span className="text-[10px] text-sky-400/80 font-normal mt-0.5">
                                      RPM: {formatCurrency(c.rpm)}
                                    </span>
                                  </div>
                                </td>
                              </tr>
                            );
                          })
                        )
                      ) : (
                        /* --- LEVEL 2: AD UNIT DRILL-DOWN FOR SELECTED COUNTRY --- */
                        sortedAdUnits.length === 0 ? (
                          <tr>
                            <td colSpan="11" className="px-4 py-8 text-center text-slate-400 italic">
                              Tidak ada unit iklan (Ad Unit) ditemukan untuk negara {selectedCountry.country}.
                            </td>
                          </tr>
                        ) : (
                          sortedAdUnits.map((p, idx) => {
                            const hasSpend = p.spend > 0;
                            const isProfitable = p.net_profit >= 0;

                            return (
                              <tr key={idx} className="hover:bg-slate-800/50 transition-colors">
                                <td className="px-4 py-3.5 font-semibold text-white">
                                  <div className="flex items-center space-x-2">
                                    <span className="w-2 h-2 rounded-full bg-indigo-400 shrink-0"></span>
                                    <span className="font-bold">{p.ad_unit}</span>
                                  </div>
                                </td>

                                <td className="px-4 py-3.5 text-right font-medium text-rose-400">
                                  {hasSpend ? formatCurrency(p.spend) : <span className="text-slate-500">-</span>}
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

                                <td className="px-4 py-3.5 text-right font-mono text-indigo-300">
                                  {p.match_rate.toFixed(1)}%
                                </td>

                                <td className="px-4 py-3.5 text-right font-mono text-slate-300">
                                  {p.ctr.toFixed(2)}%
                                </td>

                                <td className="px-4 py-3.5 text-right font-mono font-bold">
                                  {hasSpend ? (
                                    <span className={isProfitable ? 'text-emerald-400' : 'text-rose-400'}>
                                      {p.roi > 0 ? `+${p.roi.toFixed(1)}%` : `${p.roi.toFixed(1)}%`}
                                    </span>
                                  ) : (
                                    <span className="text-slate-500">N/A</span>
                                  )}
                                </td>

                                <td className="px-4 py-3.5 text-right">
                                  {hasSpend ? (
                                    <span className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-bold border ${
                                      isProfitable
                                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                                        : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                                    }`}>
                                      {isProfitable ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                                      <span>{formatCurrency(p.net_profit)}</span>
                                    </span>
                                  ) : (
                                    <span className="text-emerald-400 font-bold">{formatCurrency(p.revenue)}</span>
                                  )}
                                </td>

                                <td className="px-4 py-3.5 text-right font-mono">
                                  <div className="flex flex-col items-end">
                                    <span className="text-amber-300 font-semibold text-[11px]">
                                      {p.upr > 0 ? formatCurrency(p.upr) : '-'}
                                    </span>
                                    <span className="text-[10px] text-sky-400/80 font-normal mt-0.5">
                                      RPM: {formatCurrency(p.rpm)}
                                    </span>
                                  </div>
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
                          {selectedCountry ? `Total Unit Iklan (${selectedCountry.country})` : 'Total / Rata-rata Semua Negara'}
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
                <span>← Kembali ke Daftar Negara</span>
              </button>
            ) : (
              <span className="text-xs text-slate-400">
                💡 Petunjuk: Klik pada salah satu baris negara untuk melihat detail unit iklan (Ad Unit).
              </span>
            )}
          </div>

          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-white transition-all border border-slate-700 cursor-pointer"
          >
            Tutup
          </button>
        </div>

      </div>
    </div>
  );
}
