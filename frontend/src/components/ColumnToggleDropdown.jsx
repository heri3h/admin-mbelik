import React, { useState, useRef, useEffect } from 'react';
import { Columns, RotateCcw, ChevronDown } from 'lucide-react';

export default function ColumnToggleDropdown({ columns, visibleColumns, onToggleColumn, onResetColumns }) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const visibleCount = Object.values(visibleColumns).filter(Boolean).length;
  const totalCount = columns.length;

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-900 hover:bg-slate-700/80 border border-slate-700 text-slate-300 hover:text-white rounded-lg text-xs font-semibold transition-all cursor-pointer select-none shrink-0"
        title="Show/Hide Table Columns"
      >
        <Columns className="w-3.5 h-3.5 text-indigo-400" />
        <span>Columns</span>
        <span className="bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded text-[10px] font-mono">
          {visibleCount}/{totalCount}
        </span>
        <ChevronDown className={`w-3 h-3 text-slate-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-56 bg-slate-900 border border-slate-700/90 rounded-xl shadow-2xl z-50 p-3 space-y-2 animate-in fade-in duration-150">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <span className="text-xs font-bold text-white flex items-center gap-1.5">
              <Columns className="w-3.5 h-3.5 text-indigo-400" />
              Toggle Columns
            </span>
            <button
              onClick={onResetColumns}
              className="text-[10px] text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1 hover:underline cursor-pointer"
            >
              <RotateCcw className="w-2.5 h-2.5" />
              Reset
            </button>
          </div>

          <div className="max-h-60 overflow-y-auto space-y-1 pr-1 custom-scrollbar">
            {columns.map((col) => {
              const isChecked = Boolean(visibleColumns[col.key]);
              return (
                <label
                  key={col.key}
                  className="flex items-center space-x-2.5 px-2 py-1.5 rounded-lg hover:bg-slate-800 text-xs text-slate-300 cursor-pointer transition-colors select-none"
                >
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => onToggleColumn(col.key)}
                    className="w-3.5 h-3.5 rounded border-slate-700 bg-slate-800 text-indigo-500 focus:ring-indigo-500 focus:ring-offset-slate-900 cursor-pointer"
                  />
                  <span className={isChecked ? 'text-white font-medium' : 'text-slate-400'}>
                    {col.label}
                  </span>
                </label>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
