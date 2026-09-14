import React from 'react';
import { BarChart3, LogOut, Settings, ShieldAlert } from 'lucide-react';
import { authService } from '../services/api';

export default function Navbar({ isMockData, activeTab, setActiveTab }) {
  return (
    <header className="bg-slate-800/80 backdrop-blur border-b border-slate-700/60 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-3">
            <div className="bg-gradient-to-tr from-sky-500 to-indigo-500 p-2 rounded-xl text-white shadow-lg shadow-sky-500/20">
              <BarChart3 className="w-6 h-6" />
            </div>
            <div>
              <span className="font-bold text-lg text-white tracking-tight">Ad Analytics</span>
              <span className="ml-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-700 text-sky-400 border border-slate-600">
                Dashboard
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {isMockData && (
              <div className="hidden md:flex items-center space-x-1.5 bg-amber-500/10 text-amber-400 border border-amber-500/30 text-xs px-3 py-1.5 rounded-lg font-medium">
                <ShieldAlert className="w-4 h-4" />
                <span>Mock Data Mode (Simulation)</span>
              </div>
            )}

            <nav className="flex space-x-2">
              <button
                onClick={() => setActiveTab('dashboard')}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === 'dashboard'
                    ? 'bg-sky-600 text-white'
                    : 'text-slate-300 hover:bg-slate-700 hover:text-white'
                }`}
              >
                Dashboard
              </button>
              <button
                onClick={() => setActiveTab('settings')}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center space-x-1.5 ${
                  activeTab === 'settings'
                    ? 'bg-sky-600 text-white'
                    : 'text-slate-300 hover:bg-slate-700 hover:text-white'
                }`}
              >
                <Settings className="w-4 h-4" />
                <span>Settings</span>
              </button>
            </nav>

            <button
              onClick={authService.logout}
              className="p-2 text-slate-400 hover:text-rose-400 hover:bg-slate-700/50 rounded-lg transition-colors"
              title="Sign Out"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
