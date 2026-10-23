import React, { useState, useEffect } from 'react';
import { X, Globe, TrendingUp, TrendingDown, Search, ArrowLeft, Loader2, Layers, FileText, ChevronLeft, ChevronRight, Calendar, ExternalLink } from 'lucide-react';
import api, { dashboardService } from '../services/api';
import ColumnToggleDropdown from './ColumnToggleDropdown';
import SiteNoteModal from './SiteNoteModal';
import GoogleAdsRedirectModal, { BUILTIN_OCID_MAPPINGS } from './GoogleAdsRedirectModal';
import AdUnitPricingOverrideModal from './AdUnitPricingOverrideModal';

const LEVEL1_COLUMNS = [
  { key: 'name', label: 'Country' },
  { key: 'spend', label: 'Spend (Ads)' },
  { key: 'cpc', label: 'CPC (Ads)' },
  { key: 'revenue', label: 'Revenue (AdX)' },
  { key: 'net_profit', label: 'Profit' },
  { key: 'ecpm', label: 'CPM AdX (eCPM)' },
  { key: 'match_rate', label: 'Match Rate' },
  { key: 'ctr', label: 'CTR' },
  { key: 'ad_requests', label: 'Ad Requests' },
  { key: 'matched_requests', label: 'Matched Requests' },
  { key: 'roi', label: 'ROI' },
  { key: 'pricing_rule_name', label: 'PRICING_RULE_NAME' },
];

const LEVEL2_COLUMNS = [
  { key: 'name', label: 'Ad Unit' },
  { key: 'revenue', label: 'Revenue (AdX)' },
  { key: 'ecpm', label: 'CPM AdX (eCPM)' },
  { key: 'match_rate', label: 'Match Rate' },
  { key: 'ctr', label: 'CTR' },
  { key: 'ad_requests', label: 'Ad Requests' },
  { key: 'matched_requests', label: 'Matched Requests' },
  { key: 'pricing_rule_name', label: 'PRICING_RULE_NAME' },
  { key: 'placement_format', label: 'Format Iklan (Placement)' },
  { key: 'pricing_override', label: 'Override Pricing' },
];

const formatPricingRuleName = (rule) => {
  if (!rule || rule === 'All Rules') return 'All Rules';
  if (rule === '(No pricing rule applied)' || rule === 'No pricing rule applied' || rule === '(No Rule)') return 'No Rule';
  return rule;
};

const parseYMD = (str) => {
  if (!str) return new Date();
  const parts = str.split('-').map(Number);
  return new Date(parts[0], parts[1] - 1, parts[2]);
};

const formatYMD = (date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const formatDisplayDate = (startStr, endStr) => {
  if (!startStr) return '';
  const todayStr = formatYMD(new Date());
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  const yesterdayStr = formatYMD(yesterday);

  const formatSingle = (s) => {
    const [y, m, d] = s.split('-').map(Number);
    const dt = new Date(y, m - 1, d);
    return dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  if (startStr === endStr) {
    const formatted = formatSingle(startStr);
    if (startStr === todayStr) return `${formatted} (Today)`;
    if (startStr === yesterdayStr) return `${formatted} (Yesterday)`;
    return formatted;
  }

  return `${formatSingle(startStr)} - ${formatSingle(endStr)}`;
};

export default function CountryBreakdownModal({ domain, startDate, endDate, onClose, onNoteUpdate, mccId, siteData }) {
  const [countries, setCountries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentStartDate, setCurrentStartDate] = useState(startDate);
  const [currentEndDate, setCurrentEndDate] = useState(endDate);
  const [showNoteModal, setShowNoteModal] = useState(false);
  const [siteNote, setSiteNote] = useState(siteData?.note || '');
  const [siteObj, setSiteObj] = useState(siteData || null);
  const [redirectModalData, setRedirectModalData] = useState(null);
  const [selectedOverrideAdUnit, setSelectedOverrideAdUnit] = useState(null);

  useEffect(() => {
    setCurrentStartDate(startDate);
    setCurrentEndDate(endDate);
  }, [startDate, endDate]);

  useEffect(() => {
    if (siteData) {
      setSiteObj(siteData);
      if (siteData.note) setSiteNote(siteData.note);
    }
  }, [siteData]);

  useEffect(() => {
    const fetchSiteInfo = async () => {
      try {
        const res = await api.get('/api/dashboard/sites', {
          params: { start_date: currentStartDate, end_date: currentEndDate }
        });
        if (res.data && Array.isArray(res.data)) {
          const matched = res.data.find(s => s.domain === domain);
          if (matched) {
            setSiteObj(matched);
            if (matched.note) {
              setSiteNote(matched.note);
            }
          }
        }
      } catch (e) {}
    };
    if (domain) {
      fetchSiteInfo();
    }
  }, [domain, currentStartDate, currentEndDate]);

  const getGAdsUrl = (account) => {
    if (!account || !account.customer_id) {
      return 'https://ads.google.com/aw/campaigns';
    }
    const cid = account.customer_id;
    const cleanCid = cid.replace(/-/g, '');
    let ocid = account.ocid;
    if (!ocid) {
      try {
        const savedMappings = JSON.parse(localStorage.getItem('gads_ocid_mappings') || '{}');
        ocid = savedMappings[cid] || savedMappings[cleanCid] || BUILTIN_OCID_MAPPINGS[cid] || BUILTIN_OCID_MAPPINGS[cleanCid] || '';
      } catch (e) {
        ocid = BUILTIN_OCID_MAPPINGS[cid] || BUILTIN_OCID_MAPPINGS[cleanCid] || '';
      }
    }

    const authUser = localStorage.getItem('gads_authuser_idx') || '0';
    const userId = localStorage.getItem('gads_u_id') || '3429262417';
    const mccC = localStorage.getItem('gads_mcc_c') || '5549233089';

    if (ocid) {
      return `https://ads.google.com/aw/campaigns?ocid=${ocid}&ascid=${ocid}&authuser=${authUser}&__u=${userId}&__c=${mccC}`;
    }
    return `https://ads.google.com/aw/campaigns?ocid=${cleanCid}&authuser=${authUser}`;
  };

  const primaryAccount = siteObj?.assigned_accounts?.[0] || (siteObj?.assigned_customer_ids?.[0] ? { customer_id: siteObj.assigned_customer_ids[0] } : null);

  const handleOpenGAds = () => {
    const accounts = siteObj?.assigned_accounts || [];
    if (accounts.length === 1) {
      const url = getGAdsUrl(accounts[0]);
      window.open(url, '_blank', 'noopener,noreferrer');
    } else if (accounts.length > 1) {
      setRedirectModalData({
        customerId: accounts[0].customer_id,
        domain: domain,
        balance: accounts[0].balance,
        ocid: accounts[0].ocid
      });
    } else if (siteObj?.assigned_customer_ids?.length > 0) {
      const cid = siteObj.assigned_customer_ids[0];
      const url = getGAdsUrl({ customer_id: cid });
      window.open(url, '_blank', 'noopener,noreferrer');
    } else {
      window.open('https://ads.google.com/aw/campaigns', '_blank', 'noopener,noreferrer');
    }
  };
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [deviceFilter, setDeviceFilter] = useState('all');
  
  // Level 1: Country list | Level 2: Selected Country (Shows Ad Units inside that country)
  const [selectedCountry, setSelectedCountry] = useState(null);
  const [adUnits, setAdUnits] = useState([]);
  const [loadingAdUnits, setLoadingAdUnits] = useState(false);

  // Table Sort State for Level 1 (Country) - Persisted in localStorage
  const [countrySortColumn, setCountrySortColumn] = useState(() => {
    try {
      return localStorage.getItem('country_sort_column') || 'revenue';
    } catch (e) {
      return 'revenue';
    }
  });
  const [countrySortDirection, setCountrySortDirection] = useState(() => {
    try {
      return localStorage.getItem('country_sort_direction') || 'desc';
    } catch (e) {
      return 'desc';
    }
  });

  // Table Sort State for Level 2 (Ad Unit) - Persisted in localStorage
  const [adUnitSortColumn, setAdUnitSortColumn] = useState(() => {
    try {
      return localStorage.getItem('adunit_sort_column') || 'revenue';
    } catch (e) {
      return 'revenue';
    }
  });
  const [adUnitSortDirection, setAdUnitSortDirection] = useState(() => {
    try {
      return localStorage.getItem('adunit_sort_direction') || 'desc';
    } catch (e) {
      return 'desc';
    }
  });

  const activeSortColumn = selectedCountry ? adUnitSortColumn : countrySortColumn;
  const activeSortDirection = selectedCountry ? adUnitSortDirection : countrySortDirection;

  // Column Visibility State (Persisted in localStorage)
  const [level1VisibleCols, setLevel1VisibleCols] = useState(() => {
    try {
      const saved = localStorage.getItem('col_vis_country_level1');
      if (saved) {
        const parsed = JSON.parse(saved);
        return LEVEL1_COLUMNS.reduce((acc, col) => ({
          ...acc,
          [col.key]: parsed[col.key] !== undefined ? parsed[col.key] : true
        }), {});
      }
    } catch (e) {}
    return LEVEL1_COLUMNS.reduce((acc, col) => ({ ...acc, [col.key]: true }), {});
  });

  const [level2VisibleCols, setLevel2VisibleCols] = useState(() => {
    try {
      const saved = localStorage.getItem('col_vis_country_level2');
      if (saved) {
        const parsed = JSON.parse(saved);
        return LEVEL2_COLUMNS.reduce((acc, col) => ({
          ...acc,
          [col.key]: parsed[col.key] !== undefined ? parsed[col.key] : true
        }), {});
      }
    } catch (e) {}
    return LEVEL2_COLUMNS.reduce((acc, col) => ({ ...acc, [col.key]: true }), {});
  });

  const isOverrideSupported = Boolean(domain);
  const effectiveLevel2Columns = isOverrideSupported ? LEVEL2_COLUMNS : LEVEL2_COLUMNS.filter(c => c.key !== 'pricing_override');
  const activeColumns = selectedCountry ? effectiveLevel2Columns : LEVEL1_COLUMNS;
  const activeVisibleCols = selectedCountry ? level2VisibleCols : level1VisibleCols;

  const handleToggleColumn = (key) => {
    if (selectedCountry) {
      setLevel2VisibleCols(prev => {
        const updated = { ...prev, [key]: !prev[key] };
        try { localStorage.setItem('col_vis_country_level2', JSON.stringify(updated)); } catch (e) {}
        return updated;
      });
    } else {
      setLevel1VisibleCols(prev => {
        const updated = { ...prev, [key]: !prev[key] };
        try { localStorage.setItem('col_vis_country_level1', JSON.stringify(updated)); } catch (e) {}
        return updated;
      });
    }
  };

  const handleResetColumns = () => {
    if (selectedCountry) {
      const initial = LEVEL2_COLUMNS.reduce((acc, col) => ({ ...acc, [col.key]: true }), {});
      setLevel2VisibleCols(initial);
      try { localStorage.setItem('col_vis_country_level2', JSON.stringify(initial)); } catch (e) {}
    } else {
      const initial = LEVEL1_COLUMNS.reduce((acc, col) => ({ ...acc, [col.key]: true }), {});
      setLevel1VisibleCols(initial);
      try { localStorage.setItem('col_vis_country_level1', JSON.stringify(initial)); } catch (e) {}
    }
  };

  const todayStr = formatYMD(new Date());
  const isAtToday = currentEndDate >= todayStr;
  const isNextDisabled = isAtToday || loading || loadingAdUnits;
  const isPrevDisabled = loading || loadingAdUnits;

  const handlePrevDay = () => {
    const d = parseYMD(currentStartDate);
    d.setDate(d.getDate() - 1);
    const newStr = formatYMD(d);
    setCurrentStartDate(newStr);
    setCurrentEndDate(newStr);
  };

  const handleNextDay = () => {
    if (isAtToday) return;
    const d = parseYMD(currentEndDate);
    d.setDate(d.getDate() + 1);
    const newStr = formatYMD(d);
    setCurrentStartDate(newStr);
    setCurrentEndDate(newStr);
  };

  useEffect(() => {
    const fetchCountryData = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await dashboardService.getSiteCountries(domain, currentStartDate, currentEndDate, deviceFilter);
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
  }, [domain, currentStartDate, currentEndDate, deviceFilter]);

  useEffect(() => {
    const fetchAdUnits = async () => {
      if (!selectedCountry) {
        setAdUnits([]);
        return;
      }
      setLoadingAdUnits(true);
      try {
        const data = await dashboardService.getSiteCountryPlacements(domain, selectedCountry.country, currentStartDate, currentEndDate, deviceFilter);
        setAdUnits(data || []);
      } catch (err) {
        console.error('Failed fetching ad unit placement data', err);
        setAdUnits([]);
      } finally {
        setLoadingAdUnits(false);
      }
    };

    fetchAdUnits();
  }, [selectedCountry, domain, currentStartDate, currentEndDate, deviceFilter]);

  const formatCurrency = (val) => {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR',
      maximumFractionDigits: 0
    }).format(val || 0);
  };

  const handleSort = (col) => {
    if (selectedCountry) {
      const isSame = adUnitSortColumn === col;
      const nextDir = isSame ? (adUnitSortDirection === 'asc' ? 'desc' : 'asc') : 'desc';
      setAdUnitSortColumn(col);
      setAdUnitSortDirection(nextDir);
      try {
        localStorage.setItem('adunit_sort_column', col);
        localStorage.setItem('adunit_sort_direction', nextDir);
      } catch (e) {}
    } else {
      const isSame = countrySortColumn === col;
      const nextDir = isSame ? (countrySortDirection === 'asc' ? 'desc' : 'asc') : 'desc';
      setCountrySortColumn(col);
      setCountrySortDirection(nextDir);
      try {
        localStorage.setItem('country_sort_column', col);
        localStorage.setItem('country_sort_direction', nextDir);
      } catch (e) {}
    }
  };

  const renderSortIndicator = (col) => {
    if (activeSortColumn !== col) return <span className="text-slate-600 ml-1 font-normal opacity-50">↕</span>;
    return activeSortDirection === 'asc' ? <span className="text-emerald-400 ml-1 font-bold">↑</span> : <span className="text-emerald-400 ml-1 font-bold">↓</span>;
  };

  const handleCountryClick = (countryObj) => {
    setSelectedCountry(countryObj);
    setSearchTerm('');
  };

  const handleBackToCountries = () => {
    setSelectedCountry(null);
    setSearchTerm('');
  };

  // Calculations for Summary Cards
  const totalRev = countries.reduce((sum, c) => sum + (c.revenue || 0), 0);
  const totalSpend = countries.reduce((sum, c) => sum + (c.spend || 0), 0);
  const totalGAdsClicks = countries.reduce((sum, c) => sum + (c.clicks_ads || 0), 0);
  const avgOverallCpc = totalGAdsClicks > 0 ? (totalSpend / totalGAdsClicks) : (countries.filter(c => c.cpc > 0).length > 0 ? countries.reduce((sum, c) => sum + (c.cpc || 0), 0) / countries.filter(c => c.cpc > 0).length : 0);
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
    let colKey = countrySortColumn === 'name' ? 'country' : countrySortColumn;
    let aVal = a[colKey] ?? 0;
    let bVal = b[colKey] ?? 0;
    if (typeof aVal === 'string') {
      return countrySortDirection === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    }
    return countrySortDirection === 'asc' ? aVal - bVal : bVal - aVal;
  });

  // Level 2: Filter & Sort Ad Units within Selected Country
  const level2TotalRev = adUnits.reduce((sum, p) => sum + (p.total_revenue || 0), 0);
  const level2TotalAdReqs = adUnits.reduce((sum, p) => sum + (p.ad_requests || 0), 0);
  const level2TotalMatchedReqs = adUnits.reduce((sum, p) => sum + (p.matched_requests || 0), 0);
  const level2AvgMatchRate = level2TotalAdReqs > 0 ? (level2TotalMatchedReqs / level2TotalAdReqs * 100) : 0;
  const level2TotalImps = adUnits.reduce((sum, p) => sum + (p.impressions || 0), 0);
  const level2TotalClicks = adUnits.reduce((sum, p) => sum + (p.clicks || 0), 0);
  const level2AvgCtr = level2TotalImps > 0 ? (level2TotalClicks / level2TotalImps * 100) : 0;
  const level2AvgEcpm = level2TotalImps > 0 ? (level2TotalRev / (level2TotalImps / 1000)) : 0;

  const filteredAdUnits = adUnits.filter(p =>
    p.ad_unit.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const sortedAdUnits = [...filteredAdUnits].sort((a, b) => {
    let colKey = adUnitSortColumn === 'name' ? 'ad_unit' : adUnitSortColumn;
    let aVal = a[colKey] ?? 0;
    let bVal = b[colKey] ?? 0;
    if (typeof aVal === 'string') {
      return adUnitSortDirection === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    }
    return adUnitSortDirection === 'asc' ? aVal - bVal : bVal - aVal;
  });

  // Find updated country metadata matching the active deviceFilter
  const currentCountryData = selectedCountry
    ? (countries.find(c =>
        (c.country && selectedCountry.country && c.country.toLowerCase() === selectedCountry.country.toLowerCase()) ||
        (c.country_code && selectedCountry.country_code && c.country_code.toUpperCase() === selectedCountry.country_code.toUpperCase())
      ) || selectedCountry)
    : null;

  // Level 2 Metrics:
  // When adUnits are loaded, total revenue and ecpm come directly from the ad units list.
  // If adUnits are still fetching (or empty), fallback to the currentCountryData revenue/ecpm.
  const level2ActiveRev = (adUnits.length > 0 || !loadingAdUnits)
    ? level2TotalRev
    : (currentCountryData?.revenue || 0);

  const level2ActiveImps = (adUnits.length > 0 || !loadingAdUnits)
    ? level2TotalImps
    : (currentCountryData?.impressions || 0);

  const level2ActiveEcpm = level2ActiveImps > 0
    ? (level2ActiveRev / (level2ActiveImps / 1000))
    : (currentCountryData?.ecpm || 0);

  const level2Spend = currentCountryData ? (currentCountryData.spend || 0) : 0;
  const level2Profit = level2ActiveRev - level2Spend;
  const level2Roi = level2Spend > 0 ? (level2ActiveRev / level2Spend * 100) : 0;

  // Calculate active summary metrics based on Level 1 (All Countries) or Level 2 (Selected Country)
  const activeRev = selectedCountry ? level2ActiveRev : totalRev;
  const activeSpend = selectedCountry ? level2Spend : totalSpend;
  const activeProfit = selectedCountry ? level2Profit : netProfit;
  const activeEcpm = selectedCountry ? level2ActiveEcpm : avgEcpm;
  const activeRoi = selectedCountry ? level2Roi : overallRoi;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-1 sm:p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
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
                  <span className="flex flex-wrap items-center gap-2">
                    <span>Ad Unit Performance Report</span>
                    <span className="text-xs px-2.5 py-0.5 font-medium rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                      {selectedCountry.flag_emoji} {selectedCountry.country}
                    </span>
                  </span>
                ) : (
                  <span>Domain Country Performance Breakdown</span>
                )}
              </h2>
              <div className="flex items-center gap-2 mt-1">
                <button
                  type="button"
                  onClick={() => setShowNoteModal(true)}
                  title={`View or edit optimization notes for ${domain}`}
                  className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-xs font-mono bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/20 transition-all cursor-pointer"
                >
                  <Globe className="w-3 h-3 text-emerald-400" />
                  <span className="font-semibold">{domain}</span>
                  <FileText className="w-3 h-3 text-emerald-400" />
                </button>
              </div>
            </div>
          </div>

          {/* Top Actions Header */}
          <div className="flex flex-wrap items-center gap-2.5">
            {/* Daily Date Navigation Stepper with icons */}
            <div className="flex items-center bg-slate-900/90 border border-slate-700/70 rounded-xl p-0.5 text-xs shadow-sm">
              <button
                type="button"
                onClick={handlePrevDay}
                disabled={isPrevDisabled}
                title="Previous Day"
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 disabled:opacity-30 disabled:hover:bg-transparent disabled:cursor-not-allowed transition-all cursor-pointer"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>

              <div className="flex items-center space-x-1.5 px-2.5 py-0.5 font-mono text-xs font-semibold text-slate-200">
                <Calendar className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                <span className="whitespace-nowrap">{formatDisplayDate(currentStartDate, currentEndDate)}</span>
              </div>

              <button
                type="button"
                onClick={handleNextDay}
                disabled={isNextDisabled}
                title={isAtToday ? "Already on today" : "Next Day"}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 disabled:opacity-30 disabled:hover:bg-transparent disabled:cursor-not-allowed transition-all cursor-pointer"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>

            <div className="flex items-center space-x-1 bg-slate-900/80 p-1 rounded-xl border border-slate-700/60 text-xs">
              <button
                onClick={() => setDeviceFilter('all')}
                className={`px-2.5 py-1 rounded-lg font-semibold transition-all flex items-center space-x-1 cursor-pointer ${
                  deviceFilter === 'all'
                    ? 'bg-sky-500 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`}
              >
                <Globe className="w-3 h-3" />
                <span>All</span>
              </button>
              <button
                onClick={() => setDeviceFilter('mobile')}
                className={`px-2.5 py-1 rounded-lg font-semibold transition-all flex items-center space-x-1 cursor-pointer ${
                  deviceFilter === 'mobile'
                    ? 'bg-sky-500 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`}
              >
                <span>📱 Mobile</span>
              </button>
              <button
                onClick={() => setDeviceFilter('desktop')}
                className={`px-2.5 py-1 rounded-lg font-semibold transition-all flex items-center space-x-1 cursor-pointer ${
                  deviceFilter === 'desktop'
                    ? 'bg-sky-500 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`}
              >
                <span>💻 Desktop</span>
              </button>
            </div>
            {selectedCountry && (
              <button
                onClick={handleBackToCountries}
                className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-all border border-slate-700 flex items-center space-x-1.5 cursor-pointer shadow-sm"
                title="Back to Country Breakdown"
              >
                <ArrowLeft className="w-3.5 h-3.5 text-emerald-400" />
                <span>Back to Countries</span>
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
                <div
                  onClick={handleOpenGAds}
                  title={primaryAccount ? `Open Google Ads Campaigns (${primaryAccount.customer_id}${primaryAccount.ocid ? ` • OCID: ${primaryAccount.ocid}` : ''}) in new tab` : "Open Google Ads Campaigns in new tab"}
                  className="bg-slate-800/80 hover:bg-slate-800 border border-slate-700/60 hover:border-rose-500/50 p-4 rounded-xl transition-all cursor-pointer group shadow-sm hover:shadow-md hover:shadow-rose-500/10 flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400 text-[11px] font-semibold uppercase flex items-center gap-1">
                        <span>Total Spend</span>
                        <span className="text-[10px] text-rose-400/80 font-normal lowercase">(Google Ads)</span>
                      </span>
                      <ExternalLink className="w-3.5 h-3.5 text-slate-500 group-hover:text-rose-400 transition-colors shrink-0" />
                    </div>
                    <p className="text-lg font-extrabold text-rose-400 mt-1">{formatCurrency(activeSpend)}</p>
                  </div>
                  {primaryAccount && (
                    <div className="flex items-center gap-1.5 mt-2 pt-1.5 border-t border-slate-700/40 text-[10px] text-slate-400 font-mono">
                      <span className="group-hover:text-sky-300 transition-colors underline decoration-dotted">
                        {primaryAccount.customer_id}
                      </span>
                      {primaryAccount.ocid ? (
                        <span className="px-1.5 py-0.5 rounded bg-sky-950/80 text-sky-300 border border-sky-800/50 text-[9px] font-bold">
                          OCID: {primaryAccount.ocid}
                        </span>
                      ) : (
                        <span className="text-[9px] text-slate-500">
                          (Click to open)
                        </span>
                      )}
                    </div>
                  )}
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

                <div className="flex items-center space-x-3">
                  <ColumnToggleDropdown
                    columns={activeColumns}
                    visibleColumns={activeVisibleCols}
                    onToggleColumn={handleToggleColumn}
                    onResetColumns={handleResetColumns}
                  />

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
                    
                    {/* --- DYNAMIC THEAD ACROSS LEVEL 1 (COUNTRY) & LEVEL 2 (AD UNIT) --- */}
                    <thead className="bg-slate-900 text-slate-400 uppercase font-semibold text-[10px] tracking-wider select-none shadow-md">
                      <tr>
                        {activeVisibleCols.name && (
                          <th onClick={() => handleSort('name')} className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 cursor-pointer hover:text-white transition-colors">
                            <div className="flex items-center space-x-1 leading-tight">
                              <span>{selectedCountry ? 'Ad Unit' : 'Country'}</span>
                              {renderSortIndicator('name')}
                            </div>
                          </th>
                        )}
                        {!selectedCountry && activeVisibleCols.spend && (
                          <th onClick={() => handleSort('spend')} className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                            <div className="flex items-center justify-end space-x-1 leading-tight">
                              <span>Spend<br/>(Ads)</span>
                              {renderSortIndicator('spend')}
                            </div>
                          </th>
                        )}
                        {!selectedCountry && activeVisibleCols.cpc && (
                          <th onClick={() => handleSort('cpc')} className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                            <div className="flex items-center justify-end space-x-1 leading-tight">
                              <span>CPC<br/>(Ads)</span>
                              {renderSortIndicator('cpc')}
                            </div>
                          </th>
                        )}
                        {activeVisibleCols.revenue && (
                          <th onClick={() => handleSort('revenue')} className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                            <div className="flex items-center justify-end space-x-1 leading-tight">
                              <span>Revenue<br/>(AdX)</span>
                              {renderSortIndicator('revenue')}
                            </div>
                          </th>
                        )}
                        {!selectedCountry && activeVisibleCols.net_profit && (
                          <th onClick={() => handleSort('net_profit')} className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                            <div className="flex items-center justify-end space-x-1 leading-tight">
                              <span>Profit</span>
                              {renderSortIndicator('net_profit')}
                            </div>
                          </th>
                        )}
                        {activeVisibleCols.ecpm && (
                          <th onClick={() => handleSort('ecpm')} className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                            <div className="flex items-center justify-end space-x-1 leading-tight">
                              <span>CPM AdX<br/>(eCPM)</span>
                              {renderSortIndicator('ecpm')}
                            </div>
                          </th>
                        )}
                        {activeVisibleCols.match_rate && (
                          <th onClick={() => handleSort('match_rate')} className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                            <div className="flex items-center justify-end space-x-1 leading-tight">
                              <span>Match<br/>Rate</span>
                              {renderSortIndicator('match_rate')}
                            </div>
                          </th>
                        )}
                        {activeVisibleCols.ctr && (
                          <th onClick={() => handleSort('ctr')} className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                            <div className="flex items-center justify-end space-x-1 leading-tight">
                              <span>CTR</span>
                              {renderSortIndicator('ctr')}
                            </div>
                          </th>
                        )}
                        {activeVisibleCols.ad_requests && (
                          <th onClick={() => handleSort('ad_requests')} className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                            <div className="flex items-center justify-end space-x-1 leading-tight">
                              <span>Ad<br/>Requests</span>
                              {renderSortIndicator('ad_requests')}
                            </div>
                          </th>
                        )}
                        {activeVisibleCols.matched_requests && (
                          <th onClick={() => handleSort('matched_requests')} className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                            <div className="flex items-center justify-end space-x-1 leading-tight">
                              <span>Matched<br/>Requests</span>
                              {renderSortIndicator('matched_requests')}
                            </div>
                          </th>
                        )}
                        {!selectedCountry && activeVisibleCols.roi && (
                          <th onClick={() => handleSort('roi')} className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                            <div className="flex items-center justify-end space-x-1 leading-tight">
                              <span>ROI</span>
                              {renderSortIndicator('roi')}
                            </div>
                          </th>
                        )}
                        {activeVisibleCols.pricing_rule_name && (
                          <th onClick={() => handleSort('pricing_rule_name')} className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                            <div className="flex items-center justify-end space-x-1 leading-tight">
                              <span>PRICING_<br/>RULE_NAME</span>
                              {renderSortIndicator('pricing_rule_name')}
                            </div>
                          </th>
                        )}
                        {selectedCountry && activeVisibleCols.placement_format && (
                          <th onClick={() => handleSort('placement_format')} className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 text-right cursor-pointer hover:text-white transition-colors">
                            <div className="flex items-center justify-end space-x-1 leading-tight">
                              <span>Format Iklan<br/>(Placement)</span>
                              {renderSortIndicator('placement_format')}
                            </div>
                          </th>
                        )}
                        {selectedCountry && isOverrideSupported && activeVisibleCols.pricing_override && (
                          <th
                            className="sticky top-0 z-30 bg-slate-900 px-3 py-2.5 border-b border-slate-700/60 text-right cursor-help"
                            title="Status Badge: 🟢 Auto (Hijau) | 🟣 Target Floor (Ungu) | 🔵 Target CPM (Biru) | 🟠 Target MR (Amber)"
                          >
                            <div className="flex items-center justify-end space-x-1 leading-tight">
                              <span>Override<br/>Pricing</span>
                            </div>
                          </th>
                        )}
                      </tr>
                    </thead>

                    <tbody className="divide-y divide-slate-700/50">
                      {/* --- LEVEL 1: COUNTRY LIST --- */}
                      {!selectedCountry ? (
                        sortedCountries.length === 0 ? (
                          <tr>
                            <td colSpan="11" className="px-3 py-6 text-center text-slate-400 italic">
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
                                {activeVisibleCols.name && (
                                  <td
                                    className="px-3 py-2.5 font-semibold text-white whitespace-nowrap"
                                    title={`Country: ${c.country} (${c.country_code})`}
                                  >
                                    <div className="flex items-center space-x-1.5">
                                      <span className="text-base group-hover:scale-125 transition-transform">{c.flag_emoji}</span>
                                      <span className="font-bold font-mono text-slate-100 group-hover:text-emerald-400 group-hover:underline underline-offset-4 decoration-emerald-400 transition-colors">
                                        {c.country_code}
                                      </span>
                                    </div>
                                  </td>
                                )}

                                {activeVisibleCols.spend && (
                                  <td className="px-3 py-2.5 text-right font-medium text-rose-400 whitespace-nowrap">
                                    {hasSpend ? formatCurrency(c.spend) : <span className="text-slate-500">-</span>}
                                  </td>
                                )}

                                {activeVisibleCols.cpc && (
                                  <td className="px-3 py-2.5 text-right font-mono text-slate-300 whitespace-nowrap">
                                    {c.cpc > 0 ? formatCurrency(c.cpc) : <span className="text-slate-500">-</span>}
                                  </td>
                                )}

                                {activeVisibleCols.revenue && (
                                  <td className="px-3 py-2.5 text-right font-bold text-emerald-400 whitespace-nowrap">
                                    {formatCurrency(c.revenue)}
                                  </td>
                                )}

                                {activeVisibleCols.net_profit && (
                                  <td className="px-3 py-2.5 text-right whitespace-nowrap">
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

                                {activeVisibleCols.ecpm && (
                                  <td className="px-3 py-2.5 text-right font-mono font-semibold text-sky-400 whitespace-nowrap">
                                    {formatCurrency(c.ecpm)}
                                  </td>
                                )}

                                {activeVisibleCols.match_rate && (
                                  <td className="px-3 py-2.5 text-right font-mono font-semibold text-indigo-300 whitespace-nowrap">
                                    {(c.match_rate || 0).toFixed(1)}%
                                  </td>
                                )}

                                {activeVisibleCols.ctr && (
                                  <td className="px-3 py-2.5 text-right font-mono text-slate-300 whitespace-nowrap">
                                    {(c.ctr || 0).toFixed(2)}%
                                  </td>
                                )}

                                {activeVisibleCols.ad_requests && (
                                  <td className="px-3 py-2.5 text-right font-mono text-slate-300 whitespace-nowrap">
                                    {(c.ad_requests || 0).toLocaleString()}
                                  </td>
                                )}

                                {activeVisibleCols.matched_requests && (
                                  <td className="px-3 py-2.5 text-right font-mono text-slate-300 whitespace-nowrap">
                                    {(c.matched_requests || 0).toLocaleString()}
                                  </td>
                                )}

                                {activeVisibleCols.roi && (
                                  <td className="px-3 py-2.5 text-right font-mono font-bold whitespace-nowrap">
                                    {hasSpend ? (
                                      <span className={isProfitable ? 'text-emerald-400' : 'text-rose-400'}>
                                        {c.roi > 0 ? `+${c.roi.toFixed(1)}%` : `${c.roi.toFixed(1)}%`}
                                      </span>
                                    ) : (
                                      <span className="text-slate-500">N/A</span>
                                    )}
                                  </td>
                                )}

                                {activeVisibleCols.pricing_rule_name && (
                                  <td className="px-3 py-2.5 text-right font-medium text-amber-300 whitespace-nowrap">
                                    {formatPricingRuleName(c.pricing_rule_name)}
                                  </td>
                                )}
                              </tr>
                            );
                          })
                        )
                      ) : (
                        /* --- LEVEL 2: AD UNITS WITHIN SELECTED COUNTRY --- */
                        loadingAdUnits ? (
                          <tr>
                            <td colSpan={Object.values(activeVisibleCols).filter(Boolean).length || 10} className="px-3 py-6 text-center text-slate-400">
                              <div className="flex items-center justify-center space-x-2">
                                <Loader2 className="w-5 h-5 animate-spin text-emerald-400" />
                                <span>Loading ad unit placements for {selectedCountry.country}...</span>
                              </div>
                            </td>
                          </tr>
                        ) : sortedAdUnits.length === 0 ? (
                          <tr>
                            <td colSpan={Object.values(activeVisibleCols).filter(Boolean).length || 10} className="px-3 py-6 text-center text-slate-400 italic">
                              No ad unit placement data found for this country.
                            </td>
                          </tr>
                        ) : (
                          sortedAdUnits.map((p, idx) => {
                            const revVal = p.total_revenue ?? p.revenue ?? 0;
                            return (
                              <tr key={idx} className="hover:bg-slate-700/40 transition-colors">
                                {activeVisibleCols.name && (
                                  <td className="px-3 py-2.5 font-semibold text-white whitespace-nowrap">
                                    <div className="flex flex-col space-y-0.5">
                                      <span className="font-bold text-slate-100">{p.ad_unit}</span>
                                      <span className="text-[10px] text-slate-400 font-mono">Domain: {p.domain}</span>
                                    </div>
                                  </td>
                                )}

                                {activeVisibleCols.revenue && (
                                  <td className="px-3 py-2.5 text-right font-bold text-emerald-400 whitespace-nowrap">
                                    {formatCurrency(revVal)}
                                  </td>
                                )}

                                {activeVisibleCols.ecpm && (
                                  <td className="px-3 py-2.5 text-right font-mono font-semibold text-sky-400 whitespace-nowrap">
                                    {formatCurrency(p.ecpm)}
                                  </td>
                                )}

                                {activeVisibleCols.match_rate && (
                                  <td className="px-3 py-2.5 text-right font-mono font-semibold text-indigo-300 whitespace-nowrap">
                                    {(p.match_rate || 0).toFixed(1)}%
                                  </td>
                                )}

                                {activeVisibleCols.ctr && (
                                  <td className="px-3 py-2.5 text-right font-mono text-slate-300 whitespace-nowrap">
                                    {(p.ctr || 0).toFixed(2)}%
                                  </td>
                                )}

                                {activeVisibleCols.ad_requests && (
                                  <td className="px-3 py-2.5 text-right font-mono text-slate-300 whitespace-nowrap">
                                    {(p.ad_requests || 0).toLocaleString()}
                                  </td>
                                )}

                                {activeVisibleCols.matched_requests && (
                                  <td className="px-3 py-2.5 text-right font-mono text-slate-300 whitespace-nowrap">
                                    {(p.matched_requests || 0).toLocaleString()}
                                  </td>
                                )}

                                {activeVisibleCols.pricing_rule_name && (
                                  <td className="px-3 py-2.5 text-right font-medium text-amber-300 whitespace-nowrap">
                                    {formatPricingRuleName(p.pricing_rule_name)}
                                  </td>
                                )}

                                {activeVisibleCols.placement_format && (
                                  <td className="px-3 py-2.5 text-right whitespace-nowrap">
                                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold border ${
                                      p.placement_format === 'Interstitial' ? 'bg-amber-500/10 text-amber-300 border-amber-500/30' :
                                      p.placement_format === 'Anchor / Sticky' ? 'bg-purple-500/10 text-purple-300 border-purple-500/30' :
                                      p.placement_format === 'Vignette' ? 'bg-rose-500/10 text-rose-300 border-rose-500/30' :
                                      p.placement_format === 'In-Feed' ? 'bg-teal-500/10 text-teal-300 border-teal-500/30' :
                                      p.placement_format === 'Header' ? 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30' :
                                      p.placement_format === 'Sidebar 1' || p.placement_format === 'Sidebar 2' ? 'bg-blue-500/10 text-blue-300 border-blue-500/30' :
                                      'bg-slate-700/50 text-slate-300 border-slate-600/50'
                                    }`}>
                                      {p.placement_format || 'Banner'}
                                    </span>
                                  </td>
                                )}

                                {isOverrideSupported && activeVisibleCols.pricing_override && (
                                  <td className="px-3 py-2 text-right whitespace-nowrap">
                                    <button
                                      type="button"
                                      onClick={() => setSelectedOverrideAdUnit(p)}
                                      className="group inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-lg border text-xs font-mono transition-all cursor-pointer shadow-sm bg-slate-800/90 hover:bg-slate-800 border-slate-700/80 hover:border-purple-500/60"
                                      title="Klik untuk membuka modal pengaturan CPM Override Ad Unit"
                                    >
                                      {(() => {
                                        const renderPricingBadge = (ov, deviceIcon) => {
                                          const mode = ov?.pricing_mode || 'auto';
                                          let badgeCls = "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
                                          let icon = "🟢";
                                          let text = "Auto";

                                          if (mode === 'target_floor') {
                                            badgeCls = "bg-purple-500/15 text-purple-300 border-purple-500/35";
                                            icon = "🟣";
                                            text = ov.target_floor_key || 'Floor';
                                          } else if (mode === 'target_cpm') {
                                            badgeCls = "bg-sky-500/15 text-sky-300 border-sky-500/35";
                                            icon = "🔵";
                                            const rawVal = ov.target_key || ov.target_cpm;
                                            if (rawVal && !isNaN(Number(rawVal))) {
                                              text = `CPM ${Number(rawVal).toLocaleString('id-ID')}`;
                                            } else {
                                              text = rawVal ? `CPM ${rawVal}` : "Target CPM";
                                            }
                                          } else if (mode === 'target_mr') {
                                            badgeCls = "bg-amber-500/15 text-amber-300 border-amber-500/35";
                                            icon = "🟠";
                                            text = `MR ${ov.target_mr || 65}%`;
                                          }

                                          return (
                                            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border text-[11px] font-mono shadow-xs transition-colors ${badgeCls}`}>
                                              {deviceIcon && <span className="text-[10px] opacity-80 mr-0.5">{deviceIcon}</span>}
                                              <span className="text-[9px] leading-none">{icon}</span>
                                              <span className="font-semibold tracking-tight">{text}</span>
                                            </span>
                                          );
                                        };

                                        if (deviceFilter === 'mobile') {
                                          return renderPricingBadge(p.mobile_override, '📱');
                                        }
                                        if (deviceFilter === 'desktop') {
                                          return renderPricingBadge(p.desktop_override, '💻');
                                        }
                                        return (
                                          <div className="flex items-center space-x-1.5 text-[11px] font-mono">
                                            {renderPricingBadge(p.mobile_override, '📱')}
                                            <span className="text-slate-600">|</span>
                                            {renderPricingBadge(p.desktop_override, '💻')}
                                          </div>
                                        );
                                      })()}
                                      <span className="text-[10px] text-slate-500 group-hover:text-purple-400 transition-colors ml-0.5">⚙️</span>
                                    </button>
                                  </td>
                                )}
                              </tr>
                            );
                          })
                        )
                      )}
                    </tbody>

                    {/* --- DYNAMIC TFOOT ACROSS LEVEL 1 (COUNTRY) & LEVEL 2 (AD UNIT) --- */}
                    <tfoot className="bg-slate-950 text-slate-200 font-semibold border-t border-slate-700/80 text-[11px]">
                      {selectedCountry ? (
                        <tr>
                          {activeVisibleCols.name && (
                            <td className="px-3 py-2.5 font-bold whitespace-nowrap">
                              Total Ad Units ({selectedCountry.country})
                            </td>
                          )}
                          {activeVisibleCols.revenue && (
                            <td className="px-3 py-2.5 text-right font-bold text-emerald-400 whitespace-nowrap">{formatCurrency(activeRev)}</td>
                          )}
                          {activeVisibleCols.ecpm && (
                            <td className="px-3 py-2.5 text-right font-mono text-sky-400 whitespace-nowrap">{formatCurrency(activeEcpm)}</td>
                          )}
                          {activeVisibleCols.match_rate && (
                            <td className="px-3 py-2.5 text-right font-mono text-indigo-300 whitespace-nowrap">
                              {level2AvgMatchRate.toFixed(1)}%
                            </td>
                          )}
                          {activeVisibleCols.ctr && (
                            <td className="px-3 py-2.5 text-right font-mono whitespace-nowrap">
                              {level2AvgCtr.toFixed(2)}%
                            </td>
                          )}
                          {activeVisibleCols.ad_requests && (
                            <td className="px-3 py-2.5 text-right font-mono whitespace-nowrap">
                              {level2TotalAdReqs.toLocaleString()}
                            </td>
                          )}
                          {activeVisibleCols.matched_requests && (
                            <td className="px-3 py-2.5 text-right font-mono whitespace-nowrap">
                              {level2TotalMatchedReqs.toLocaleString()}
                            </td>
                          )}
                          {activeVisibleCols.pricing_rule_name && (
                            <td className="px-3 py-2.5 text-right font-medium text-amber-300 whitespace-nowrap">
                              All Rules
                            </td>
                          )}
                          {activeVisibleCols.placement_format && (
                            <td className="px-3 py-2.5 text-right text-slate-500 font-mono">-</td>
                          )}
                          {isOverrideSupported && activeVisibleCols.pricing_override && (
                            <td className="px-3 py-2.5 text-right text-slate-500 font-mono">-</td>
                          )}
                        </tr>
                      ) : (
                        <tr>
                          {activeVisibleCols.name && (
                            <td className="px-3 py-2 font-bold text-xs leading-tight">
                              <div>Total / Average</div>
                              <div className="text-[10px] text-slate-400 font-normal">All Countries</div>
                            </td>
                          )}

                          {activeVisibleCols.spend && (
                            <td className="px-3 py-2.5 text-right font-bold text-rose-400 whitespace-nowrap">{formatCurrency(activeSpend)}</td>
                          )}
                          {activeVisibleCols.cpc && (
                            <td className="px-3 py-2.5 text-right font-mono font-bold text-slate-300 whitespace-nowrap">
                              {avgOverallCpc > 0 ? formatCurrency(avgOverallCpc) : '-'}
                            </td>
                          )}
                          {activeVisibleCols.revenue && (
                            <td className="px-3 py-2.5 text-right font-bold text-emerald-400 whitespace-nowrap">{formatCurrency(activeRev)}</td>
                          )}
                          {activeVisibleCols.net_profit && (
                            <td className={`px-3 py-2.5 text-right font-bold whitespace-nowrap ${activeProfit >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>{formatCurrency(activeProfit)}</td>
                          )}
                          {activeVisibleCols.ecpm && (
                            <td className="px-3 py-2.5 text-right font-mono text-sky-400 whitespace-nowrap">{formatCurrency(activeEcpm)}</td>
                          )}
                          {activeVisibleCols.match_rate && (
                            <td className="px-3 py-2.5 text-right font-mono text-indigo-300 whitespace-nowrap">
                              {avgMatchRate.toFixed(1)}%
                            </td>
                          )}
                          {activeVisibleCols.ctr && (
                            <td className="px-3 py-2.5 text-right font-mono whitespace-nowrap">
                              {avgCtr.toFixed(2)}%
                            </td>
                          )}
                          {activeVisibleCols.ad_requests && (
                            <td className="px-3 py-2.5 text-right font-mono whitespace-nowrap">
                              {totalAdReqs.toLocaleString()}
                            </td>
                          )}
                          {activeVisibleCols.matched_requests && (
                            <td className="px-3 py-2.5 text-right font-mono whitespace-nowrap">
                              {totalMatchedReqs.toLocaleString()}
                            </td>
                          )}
                          {activeVisibleCols.roi && (
                            <td className="px-3 py-2.5 text-right font-mono font-bold whitespace-nowrap">
                              {activeSpend > 0 ? (
                                <span className={activeProfit >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                                  {activeRoi > 0 ? `+${activeRoi.toFixed(1)}%` : `${activeRoi.toFixed(1)}%`}
                                </span>
                              ) : (
                                <span className="text-slate-500">N/A</span>
                              )}
                            </td>
                          )}
                          {activeVisibleCols.pricing_rule_name && (
                            <td className="px-3 py-2.5 text-right font-medium text-amber-300 whitespace-nowrap">
                              All Rules
                            </td>
                          )}
                        </tr>
                      )}
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

      {showNoteModal && (
        <SiteNoteModal
          domain={domain}
          initialNote={siteNote}
          onClose={() => setShowNoteModal(false)}
          onSaveSuccess={(dom, newNote) => {
            setSiteNote(newNote);
            if (onNoteUpdate) {
              onNoteUpdate(dom, newNote);
            }
          }}
        />
      )}

      {redirectModalData && (
        <GoogleAdsRedirectModal
          isOpen={Boolean(redirectModalData)}
          onClose={() => setRedirectModalData(null)}
          customerId={redirectModalData.customerId}
          domain={redirectModalData.domain}
          balance={redirectModalData.balance}
          ocid={redirectModalData.ocid}
          mccId={mccId}
        />
      )}

      {selectedOverrideAdUnit && selectedCountry && (
        <AdUnitPricingOverrideModal
          isOpen={Boolean(selectedOverrideAdUnit)}
          onClose={() => setSelectedOverrideAdUnit(null)}
          domain={domain}
          country={selectedCountry}
          adUnitItem={selectedOverrideAdUnit}
          onSaved={({ adUnit, mobileOverride, desktopOverride }) => {
            setAdUnits((prev) =>
              prev.map((item) => {
                if (item.ad_unit === adUnit) {
                  return {
                    ...item,
                    mobile_override: mobileOverride,
                    desktop_override: desktopOverride,
                    pricing_override: deviceFilter === 'mobile' ? mobileOverride : (deviceFilter === 'desktop' ? desktopOverride : null),
                  };
                }
                return item;
              })
            );
          }}
        />
      )}
    </div>
  );
}
