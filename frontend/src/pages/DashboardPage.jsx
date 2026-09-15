import React, { useState, useEffect } from 'react';
import DateFilter from '../components/DateFilter';
import SummaryCards from '../components/SummaryCards';
import TrendChart from '../components/TrendChart';
import AccountsTable from '../components/AccountsTable';
import SitesTable from '../components/SitesTable';
import PlacementsTable from '../components/PlacementsTable';
import SyncButton from '../components/SyncButton';
import { dashboardService } from '../services/api';
import { Loader2, Globe, LayoutGrid, Layers, Clock } from 'lucide-react';

const formatLocalDate = (d) => {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

export default function DashboardPage() {
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);
  const yesterdayStr = formatLocalDate(yesterday);

  const [startDate, setStartDate] = useState(yesterdayStr);
  const [endDate, setEndDate] = useState(yesterdayStr);

  const [summary, setSummary] = useState(null);
  const [trend, setTrend] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [sites, setSites] = useState([]);
  const [placements, setPlacements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Active breakdown view: 'sites' (default), 'placements', 'accounts'
  const [activeReportTab, setActiveReportTab] = useState('sites');

  const loadDashboardData = async () => {
    if (!summary) setLoading(true);
    setIsRefreshing(true);
    try {
      const [sumData, trendData, accData, siteData, placementData] = await Promise.all([
        dashboardService.getSummary(startDate, endDate),
        dashboardService.getTrend(startDate, endDate),
        dashboardService.getAccounts(startDate, endDate),
        dashboardService.getSites(startDate, endDate),
        dashboardService.getPlacements(startDate, endDate)
      ]);

      setSummary(sumData);
      setTrend(trendData);
      setAccounts(accData);
      setSites(siteData);
      setPlacements(placementData);
    } catch (err) {
      console.error('Failed loading dashboard data', err);
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, [startDate, endDate]);

  const handleFilterChange = (newStart, newEnd) => {
    setStartDate(newStart);
    setEndDate(newEnd);
  };

  return (
    <div className="space-y-6">
      {/* Top Header & Sync controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
            <span>Profitability Dashboard</span>
            {isRefreshing && <Loader2 className="w-4 h-4 animate-spin text-sky-400" title="Updating data..." />}
          </h1>
          <div className="flex flex-wrap items-center gap-2 text-slate-400 text-xs mt-1">
            <span>Google Ads Spend vs Ad Exchange (GAM) Revenue Analytics</span>
            {summary?.last_synced_at && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-slate-800 text-emerald-400 border border-emerald-500/30 shadow-sm">
                <Clock className="w-3 h-3 text-emerald-400" />
                <span>Last Synced: {summary.last_synced_at} (Auto 30m)</span>
              </span>
            )}
          </div>
        </div>
        <SyncButton startDate={startDate} endDate={endDate} onSyncSuccess={loadDashboardData} />
      </div>

      {/* Date Filter Bar */}
      <DateFilter startDate={startDate} endDate={endDate} onFilterChange={handleFilterChange} />

      {loading && !summary ? (
        <div className="min-h-[400px] flex flex-col items-center justify-center space-y-3 text-slate-400">
          <Loader2 className="w-8 h-8 animate-spin text-sky-400" />
          <span className="text-sm font-medium">Loading analytics data...</span>
        </div>
      ) : (
        <div className={`transition-opacity duration-200 ${isRefreshing ? 'opacity-85 pointer-events-none' : 'opacity-100'}`}>
          {/* Executive Summary Metric Cards */}
          <SummaryCards data={summary} />

          {/* Daily Trend Chart */}
          <TrendChart data={trend} startDate={startDate} endDate={endDate} />

          {/* Breakdown Reports Section */}
          <div className="space-y-4 mt-6">
            {/* Report Selector Tabs */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-slate-700/60 pb-3 max-w-full">
              <h2 className="text-lg font-bold text-white tracking-tight">Detailed Breakdown Reports</h2>
              <div className="flex items-center bg-slate-900/80 p-1 rounded-xl border border-slate-700/60 space-x-1 overflow-x-auto max-w-full w-full sm:w-auto shrink-0">
                <button
                  onClick={() => setActiveReportTab('sites')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all whitespace-nowrap ${
                    activeReportTab === 'sites'
                      ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/20'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`}
                >
                  <Globe className="w-3.5 h-3.5" />
                  <span>By Site (Domain) [Default]</span>
                </button>

                <button
                  onClick={() => setActiveReportTab('placements')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all whitespace-nowrap ${
                    activeReportTab === 'placements'
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`}
                >
                  <LayoutGrid className="w-3.5 h-3.5" />
                  <span>By Placement (Ad Unit)</span>
                </button>

                <button
                  onClick={() => setActiveReportTab('accounts')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all whitespace-nowrap ${
                    activeReportTab === 'accounts'
                      ? 'bg-sky-600 text-white shadow-md shadow-sky-600/20'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`}
                >
                  <Layers className="w-3.5 h-3.5" />
                  <span>Google Ads Accounts</span>
                </button>
              </div>
            </div>

            {/* Active Report Table Display */}
            {activeReportTab === 'sites' && <SitesTable sites={sites} startDate={startDate} endDate={endDate} />}
            {activeReportTab === 'placements' && <PlacementsTable placements={placements} />}
            {activeReportTab === 'accounts' && <AccountsTable accounts={accounts} />}
          </div>
        </div>
      )}
    </div>
  );
}
