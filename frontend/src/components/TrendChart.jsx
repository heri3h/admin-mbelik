import React, { useState, useEffect } from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';

export default function TrendChart({ data, startDate, endDate }) {
  const isSingleDay = Boolean(startDate && endDate && startDate === endDate);

  const [showRevenue, setShowRevenue] = useState(true);
  const [showSpend, setShowSpend] = useState(true);
  const [showProfit, setShowProfit] = useState(true);
  const [showRoi, setShowRoi] = useState(!isSingleDay);

  useEffect(() => {
    if (isSingleDay) {
      setShowRoi(false);
    } else {
      setShowRoi(true);
    }
  }, [startDate, endDate, isSingleDay]);

  if (!data || data.length === 0) {
    return (
      <div className="bg-slate-800 border border-slate-700/60 p-6 rounded-2xl h-80 flex items-center justify-center text-slate-400">
        No performance chart data available for this date range.
      </div>
    );
  }

  const formatYAxisLeft = (val) => {
    if (val >= 1000000000) return `Rp ${(val / 1000000000).toFixed(1)}B`;
    if (val >= 1000000) return `Rp ${(val / 1000000).toFixed(1)}M`;
    if (val >= 1000) return `Rp ${(val / 1000).toFixed(0)}k`;
    return `Rp ${val}`;
  };

  const formatYAxisRight = (val) => {
    return `${val.toFixed(0)}%`;
  };

  const formatCurrency = (val) => {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR',
      maximumFractionDigits: 0
    }).format(val || 0);
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-slate-900 border border-slate-700 p-3 rounded-xl shadow-xl text-xs space-y-1.5 min-w-[180px]">
          <p className="font-semibold text-slate-200 border-b border-slate-700 pb-1">{label}</p>
          {payload.map((entry, index) => {
            const isRoi = entry.dataKey === 'roi' || entry.name.includes('ROI');
            return (
              <div key={`item-${index}`} className="flex items-center justify-between space-x-4">
                <span style={{ color: entry.color }} className="font-medium flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full inline-block" style={{ backgroundColor: entry.color }}></span>
                  {entry.name}:
                </span>
                <span className="font-bold text-white">
                  {isRoi ? `${(entry.value || 0).toFixed(1)}%` : formatCurrency(entry.value)}
                </span>
              </div>
            );
          })}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-slate-800 border border-slate-700/60 p-6 rounded-2xl shadow-sm space-y-4">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <span>{isSingleDay ? 'Intraday Hourly Performance Trend' : 'Daily Performance & ROI Trend'}</span>
          </h3>
          <p className="text-slate-400 text-xs mt-0.5">
            {isSingleDay
              ? 'Trend jam demi jam Spend (Google Ads), Revenue (AdX), dan Net Profit'
              : 'Perbandingan Daily Spend (Google Ads), Revenue (AdX), Net Profit, dan ROI (%)'}
          </p>
        </div>

        {/* Metric Visibility Toggles */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <button
            type="button"
            onClick={() => setShowRevenue(!showRevenue)}
            className={`px-2.5 py-1 rounded-lg font-medium border transition-all ${
              showRevenue
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                : 'bg-slate-900/50 text-slate-500 border-slate-700/50 line-through'
            }`}
          >
            ● Revenue
          </button>
          <button
            type="button"
            onClick={() => setShowSpend(!showSpend)}
            className={`px-2.5 py-1 rounded-lg font-medium border transition-all ${
              showSpend
                ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30'
                : 'bg-slate-900/50 text-slate-500 border-slate-700/50 line-through'
            }`}
          >
            ● Spend
          </button>
          <button
            type="button"
            onClick={() => setShowProfit(!showProfit)}
            className={`px-2.5 py-1 rounded-lg font-medium border transition-all ${
              showProfit
                ? 'bg-sky-500/10 text-sky-400 border-sky-500/30'
                : 'bg-slate-900/50 text-slate-500 border-slate-700/50 line-through'
            }`}
          >
            ● Net Profit
          </button>
          {!isSingleDay && (
            <button
              type="button"
              onClick={() => setShowRoi(!showRoi)}
              className={`px-2.5 py-1 rounded-lg font-medium border transition-all ${
                showRoi
                  ? 'bg-amber-500/10 text-amber-400 border-amber-500/30 shadow-sm'
                  : 'bg-slate-900/50 text-slate-500 border-slate-700/50 line-through'
              }`}
            >
              📈 ROI (%)
            </button>
          )}
        </div>
      </div>

      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 10, right: (showRoi && !isSingleDay) ? 15 : -10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.4}/>
                <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorSpend" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4}/>
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorProfit" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#0284c7" stopOpacity={0.4}/>
                <stop offset="95%" stopColor="#0284c7" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
            <XAxis
              dataKey="date"
              stroke="#64748b"
              fontSize={12}
              tickLine={false}
            />
            {/* Left Y Axis for Monetary Values */}
            <YAxis
              yAxisId="left"
              stroke="#64748b"
              fontSize={12}
              tickFormatter={formatYAxisLeft}
              tickLine={false}
            />
            {/* Right Y Axis for ROI % */}
            {showRoi && !isSingleDay && (
              <YAxis
                yAxisId="right"
                orientation="right"
                stroke="#f59e0b"
                fontSize={12}
                tickFormatter={formatYAxisRight}
                tickLine={false}
              />
            )}
            <Tooltip content={<CustomTooltip />} />
            <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '12px' }} />

            {showRevenue && (
              <Area
                yAxisId="left"
                type="monotone"
                dataKey="revenue"
                name="Revenue (AdX)"
                stroke="#10b981"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#colorRevenue)"
              />
            )}
            {showSpend && (
              <Area
                yAxisId="left"
                type="monotone"
                dataKey="spend"
                name="Spend (Google Ads)"
                stroke="#6366f1"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#colorSpend)"
              />
            )}
            {showProfit && (
              <Area
                yAxisId="left"
                type="monotone"
                dataKey="profit"
                name="Net Profit"
                stroke="#0284c7"
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#colorProfit)"
              />
            )}
            {showRoi && !isSingleDay && (
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="roi"
                name="ROI (%)"
                stroke="#f59e0b"
                strokeWidth={2.5}
                dot={{ r: 3, fill: '#f59e0b' }}
                activeDot={{ r: 6 }}
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
