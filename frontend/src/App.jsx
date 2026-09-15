import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import DashboardPage from './pages/DashboardPage';
import SettingsPage from './pages/SettingsPage';
import LoginPage from './pages/LoginPage';
import { authService, dashboardService } from './services/api';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(authService.isAuthenticated());
  const [activeTab, setActiveTab] = useState('dashboard'); // 'dashboard', 'settings'
  const [isMockData, setIsMockData] = useState(true);

  useEffect(() => {
    if (isAuthenticated) {
      dashboardService.getSettingsStatus()
        .then((res) => setIsMockData(res.use_mock_data))
        .catch((err) => console.error(err));
    }
  }, [isAuthenticated]);

  if (!isAuthenticated) {
    return <LoginPage onLoginSuccess={() => setIsAuthenticated(true)} />;
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col w-full max-w-full pt-16">
      <Navbar
        isMockData={isMockData}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-1.5 sm:px-6 lg:px-8 py-4 sm:py-8">
        {activeTab === 'dashboard' && <DashboardPage />}
        {activeTab === 'settings' && <SettingsPage />}
      </main>

      <footer className="border-t border-slate-800 bg-slate-900/50 py-4 text-center text-xs text-slate-500">
        Internal Ad Performance & Profitability Analytics Dashboard &copy; {new Date().getFullYear()}
      </footer>
    </div>
  );
}
