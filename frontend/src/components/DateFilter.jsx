import React, { useState } from 'react';
import { Calendar, Filter, ChevronLeft, ChevronRight } from 'lucide-react';

export default function DateFilter({ startDate, endDate, onFilterChange }) {
  const [preset, setPreset] = useState('yesterday'); // 'today', 'yesterday', '7d', '30d', 'month', 'custom'
  const [customStart, setCustomStart] = useState(startDate || '');
  const [customEnd, setCustomEnd] = useState(endDate || '');

  const formatLocalDate = (d) => {
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const todayStr = formatLocalDate(new Date());
  const isAtToday = endDate >= todayStr;

  const handlePrevDay = () => {
    const parts = (startDate || todayStr).split('-').map(Number);
    const baseDate = new Date(parts[0], parts[1] - 1, parts[2]);
    baseDate.setDate(baseDate.getDate() - 1);
    const dStr = formatLocalDate(baseDate);
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const yStr = formatLocalDate(yesterday);
    setPreset(dStr === yStr ? 'yesterday' : 'custom');
    setCustomStart(dStr);
    setCustomEnd(dStr);
    onFilterChange(dStr, dStr);
  };

  const handleNextDay = () => {
    if (isAtToday) return;
    const parts = (endDate || todayStr).split('-').map(Number);
    const baseDate = new Date(parts[0], parts[1] - 1, parts[2]);
    baseDate.setDate(baseDate.getDate() + 1);
    const dStr = formatLocalDate(baseDate);
    setPreset(dStr === todayStr ? 'today' : 'custom');
    setCustomStart(dStr);
    setCustomEnd(dStr);
    onFilterChange(dStr, dStr);
  };

  const handlePresetSelect = (selectedPreset) => {
    setPreset(selectedPreset);
    const today = new Date();

    if (selectedPreset === 'today') {
      const dateStr = formatLocalDate(today);
      onFilterChange(dateStr, dateStr);
    } else if (selectedPreset === 'yesterday') {
      const yesterday = new Date(today);
      yesterday.setDate(today.getDate() - 1);
      const dateStr = formatLocalDate(yesterday);
      onFilterChange(dateStr, dateStr);
    } else if (selectedPreset === '7d') {
      const end = new Date(today);
      end.setDate(today.getDate() - 1);
      const start = new Date(end);
      start.setDate(end.getDate() - 6);
      onFilterChange(formatLocalDate(start), formatLocalDate(end));
    } else if (selectedPreset === '30d') {
      const end = new Date(today);
      end.setDate(today.getDate() - 1);
      const start = new Date(end);
      start.setDate(end.getDate() - 29);
      onFilterChange(formatLocalDate(start), formatLocalDate(end));
    } else if (selectedPreset === 'month') {
      const start = new Date(today.getFullYear(), today.getMonth(), 1);
      onFilterChange(formatLocalDate(start), formatLocalDate(today));
    }
  };

  const handleCustomSubmit = (e) => {
    e.preventDefault();
    if (customStart && customEnd) {
      setPreset('custom');
      onFilterChange(customStart, customEnd);
    }
  };

  return (
    <div className="bg-slate-800 border border-slate-700/60 p-4 rounded-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
      <div className="flex items-center space-x-2 text-slate-300 font-medium text-sm">
        <Filter className="w-4 h-4 text-sky-400" />
        <span>Date Range Filter:</span>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {/* Daily Navigation Stepper */}
        <div className="flex items-center bg-slate-900/90 border border-slate-700/80 rounded-xl p-0.5 text-xs shadow-sm">
          <button
            type="button"
            onClick={handlePrevDay}
            title="Previous Day"
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-all cursor-pointer"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
          </button>
          <button
            type="button"
            onClick={handleNextDay}
            disabled={isAtToday}
            title={isAtToday ? "Already on today" : "Next Day"}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 disabled:opacity-30 disabled:hover:bg-transparent disabled:cursor-not-allowed transition-all cursor-pointer"
          >
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <button
          onClick={() => handlePresetSelect('today')}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            preset === 'today'
              ? 'bg-sky-500 text-white shadow-md shadow-sky-500/20'
              : 'bg-slate-700/60 text-slate-300 hover:bg-slate-700'
          }`}
        >
          Today
        </button>

        <button
          onClick={() => handlePresetSelect('yesterday')}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            preset === 'yesterday'
              ? 'bg-sky-500 text-white shadow-md shadow-sky-500/20'
              : 'bg-slate-700/60 text-slate-300 hover:bg-slate-700'
          }`}
        >
          Yesterday
        </button>

        <button
          onClick={() => handlePresetSelect('7d')}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            preset === '7d'
              ? 'bg-sky-500 text-white shadow-md shadow-sky-500/20'
              : 'bg-slate-700/60 text-slate-300 hover:bg-slate-700'
          }`}
        >
          Last 7 Days
        </button>

        <button
          onClick={() => handlePresetSelect('30d')}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            preset === '30d'
              ? 'bg-sky-500 text-white shadow-md shadow-sky-500/20'
              : 'bg-slate-700/60 text-slate-300 hover:bg-slate-700'
          }`}
        >
          Last 30 Days
        </button>

        <button
          onClick={() => handlePresetSelect('month')}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            preset === 'month'
              ? 'bg-sky-500 text-white shadow-md shadow-sky-500/20'
              : 'bg-slate-700/60 text-slate-300 hover:bg-slate-700'
          }`}
        >
          This Month
        </button>

        <form onSubmit={handleCustomSubmit} className="flex items-center space-x-2 bg-slate-900/60 p-1 rounded-lg border border-slate-700">
          <Calendar className="w-4 h-4 text-slate-400 ml-2" />
          <input
            type="date"
            value={customStart}
            onChange={(e) => setCustomStart(e.target.value)}
            className="bg-transparent text-xs text-slate-200 border-0 focus:ring-0 p-1"
          />
          <span className="text-slate-500 text-xs">-</span>
          <input
            type="date"
            value={customEnd}
            onChange={(e) => setCustomEnd(e.target.value)}
            className="bg-transparent text-xs text-slate-200 border-0 focus:ring-0 p-1"
          />
          <button
            type="submit"
            className="bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs px-2.5 py-1 rounded font-medium transition-colors"
          >
            Apply
          </button>
        </form>
      </div>
    </div>
  );
}
