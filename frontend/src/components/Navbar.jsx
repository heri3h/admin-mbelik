import React, { useState, useEffect, useRef } from 'react';
import { Menu, X, Settings, LogOut, ShieldAlert, LayoutDashboard, Sliders, Bell, CheckCheck, Trash2, Clock, Check } from 'lucide-react';
import { authService, dashboardService } from '../services/api';

function formatRelativeTime(dateString) {
  if (!dateString) return '';
  try {
    const dStr = dateString.endsWith('Z') ? dateString : `${dateString}Z`;
    const date = new Date(dStr);
    const now = new Date();
    const diffSec = Math.floor((now - date) / 1000);
    if (diffSec < 60) return 'Just now';
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHour = Math.floor(diffMin / 60);
    if (diffHour < 24) return `${diffHour}h ago`;
    const diffDay = Math.floor(diffHour / 24);
    if (diffDay < 7) return `${diffDay}d ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  } catch {
    return '';
  }
}

export default function Navbar({ isMockData, activeTab, setActiveTab, onOpenPricingModal }) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isNotifOpen, setIsNotifOpen] = useState(false);
  const notifRef = useRef(null);

  const handleTabClick = (tab) => {
    setActiveTab(tab);
    setIsMobileMenuOpen(false);
  };

  const fetchNotifications = async () => {
    try {
      const data = await dashboardService.getNotifications();
      if (data) {
        setNotifications(data.notifications || []);
        setUnreadCount(data.unread_count || 0);
      }
    } catch (err) {
      // Silent fail on background polling
    }
  };

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 45000); // Poll every 45s
    return () => clearInterval(interval);
  }, []);

  // Close notifications dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (notifRef.current && !notifRef.current.contains(e.target)) {
        setIsNotifOpen(false);
      }
    };
    if (isNotifOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isNotifOpen]);

  const handleMarkAllRead = async () => {
    try {
      await dashboardService.markNotificationRead();
      setUnreadCount(0);
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch (err) {
      console.error('Failed to mark notifications read', err);
    }
  };

  const handleItemClick = async (notif) => {
    if (!notif.is_read) {
      try {
        await dashboardService.markNotificationRead(notif.id);
        setUnreadCount((c) => Math.max(0, c - 1));
        setNotifications((prev) =>
          prev.map((n) => (n.id === notif.id ? { ...n, is_read: true } : n))
        );
      } catch (err) {
        console.error('Failed to mark item read', err);
      }
    }
  };

  const handleClearAll = async () => {
    try {
      await dashboardService.clearNotifications();
      setNotifications([]);
      setUnreadCount(0);
    } catch (err) {
      console.error('Failed to clear notifications', err);
    }
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-16 bg-slate-800 border-b border-slate-700/60 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo & Name */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => handleTabClick('dashboard')}>
            <img src="/logo.png" alt="Mbelik" className="h-8 sm:h-9 w-auto object-contain" />
            <span className="font-bold text-lg text-white tracking-tight">Ad Analytics</span>
          </div>

          {/* Desktop Right Menu */}
          <div className="hidden md:flex items-center space-x-3">
            {isMockData && (
              <div className="flex items-center space-x-1.5 bg-amber-500/10 text-amber-400 border border-amber-500/30 text-xs px-3 py-1.5 rounded-lg font-medium">
                <ShieldAlert className="w-4 h-4" />
                <span>Mock Data Mode</span>
              </div>
            )}

            <nav className="flex space-x-2">
              <button
                onClick={() => handleTabClick('dashboard')}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === 'dashboard'
                    ? 'bg-sky-600 text-white shadow-sm'
                    : 'text-slate-300 hover:bg-slate-700 hover:text-white'
                }`}
              >
                Dashboard
              </button>

              <button
                onClick={onOpenPricingModal}
                className="px-3 py-2 bg-slate-700/70 hover:bg-slate-700 text-sky-300 border border-sky-500/30 rounded-lg text-sm font-medium transition-colors flex items-center space-x-1.5"
                title="GAM Auto Pricing Central Config"
              >
                <Sliders className="w-4 h-4 text-sky-400" />
                <span>Pricing Config</span>
              </button>

              <button
                onClick={() => handleTabClick('settings')}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center space-x-1.5 ${
                  activeTab === 'settings'
                    ? 'bg-sky-600 text-white shadow-sm'
                    : 'text-slate-300 hover:bg-slate-700 hover:text-white'
                }`}
              >
                <Settings className="w-4 h-4" />
                <span>Settings</span>
              </button>
            </nav>

            {/* Notification Bell Dropdown */}
            <div className="relative" ref={notifRef}>
              <button
                onClick={() => setIsNotifOpen(!isNotifOpen)}
                className={`relative p-2 rounded-lg transition-colors cursor-pointer ${
                  isNotifOpen
                    ? 'bg-slate-700 text-white'
                    : 'text-slate-300 hover:bg-slate-700 hover:text-white'
                }`}
                title="Notifications"
                aria-label="View Notifications"
              >
                <Bell className="w-5 h-5" />
                {unreadCount > 0 && (
                  <span className="absolute top-1.5 right-1.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-rose-500 px-1 text-[10px] font-bold text-white shadow-sm ring-2 ring-slate-800">
                    {unreadCount > 9 ? '9+' : unreadCount}
                  </span>
                )}
              </button>

              {/* Notification Popover Panel */}
              {isNotifOpen && (
                <div className="absolute right-0 mt-2 w-80 sm:w-96 rounded-2xl bg-slate-900 border border-slate-700/80 shadow-2xl overflow-hidden z-50 animate-in fade-in zoom-in-95 duration-150">
                  {/* Popover Header */}
                  <div className="p-3.5 border-b border-slate-800 bg-slate-900/90 flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Bell className="w-4 h-4 text-sky-400" />
                      <span className="text-sm font-bold text-white">Notifications</span>
                      {unreadCount > 0 && (
                        <span className="px-1.5 py-0.2 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30 text-[10px] font-semibold">
                          {unreadCount} new
                        </span>
                      )}
                    </div>
                    <div className="flex items-center space-x-1">
                      {unreadCount > 0 && (
                        <button
                          onClick={handleMarkAllRead}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-sky-400 hover:bg-slate-800 transition-colors text-xs flex items-center gap-1 cursor-pointer"
                          title="Mark all as read"
                        >
                          <CheckCheck className="w-3.5 h-3.5" />
                          <span className="hidden sm:inline text-[11px]">Read all</span>
                        </button>
                      )}
                      {notifications.length > 0 && (
                        <button
                          onClick={handleClearAll}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors cursor-pointer"
                          title="Clear all notifications"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Popover Content */}
                  <div className="max-h-80 overflow-y-auto divide-y divide-slate-800/60">
                    {notifications.length === 0 ? (
                      <div className="p-8 text-center">
                        <div className="inline-flex p-3 rounded-full bg-slate-800/80 text-slate-500 mb-2">
                          <Bell className="w-6 h-6" />
                        </div>
                        <p className="text-xs font-semibold text-slate-300">All caught up!</p>
                        <p className="text-[11px] text-slate-500 mt-0.5">No notifications right now.</p>
                      </div>
                    ) : (
                      notifications.map((notif) => (
                        <div
                          key={notif.id}
                          onClick={() => handleItemClick(notif)}
                          className={`p-3.5 hover:bg-slate-800/60 transition-colors cursor-pointer flex items-start gap-3 ${
                            !notif.is_read ? 'bg-sky-500/5' : ''
                          }`}
                        >
                          <div
                            className={`p-2 rounded-xl shrink-0 mt-0.5 ${
                              notif.type === 'override_expired'
                                ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                                : 'bg-sky-500/10 text-sky-400 border border-sky-500/20'
                            }`}
                          >
                            <Clock className="w-4 h-4" />
                          </div>

                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between gap-1">
                              <span className="text-xs font-bold text-slate-100 truncate">
                                {notif.title}
                              </span>
                              <span className="text-[10px] text-slate-500 shrink-0">
                                {formatRelativeTime(notif.created_at)}
                              </span>
                            </div>
                            <p className="text-[11px] text-slate-300 mt-1 leading-snug break-words">
                              {notif.message}
                            </p>
                            {notif.domain && (
                              <div className="mt-1.5 flex items-center gap-1.5">
                                <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-mono border border-slate-700/60">
                                  {notif.domain}
                                </span>
                                {!notif.is_read && (
                                  <span className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-pulse"></span>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            <button
              onClick={authService.logout}
              className="p-2 text-slate-400 hover:text-rose-400 hover:bg-slate-700/50 rounded-lg transition-colors cursor-pointer"
              title="Sign Out"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>

          {/* Mobile Right Bar (Bell + Hamburger) */}
          <div className="flex md:hidden items-center space-x-2">
            {/* Mobile Bell Button */}
            <div className="relative">
              <button
                onClick={() => {
                  setIsNotifOpen(!isNotifOpen);
                  setIsMobileMenuOpen(false);
                }}
                className="p-2 rounded-xl bg-slate-900/80 border border-slate-700 text-slate-300 hover:text-white transition-colors relative"
                aria-label="Toggle Notifications"
              >
                <Bell className="w-5 h-5" />
                {unreadCount > 0 && (
                  <span className="absolute top-1 right-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-rose-500 px-1 text-[10px] font-bold text-white ring-2 ring-slate-900">
                    {unreadCount > 9 ? '9+' : unreadCount}
                  </span>
                )}
              </button>

              {/* Mobile Popover Panel */}
              {isNotifOpen && (
                <div className="fixed inset-x-3 top-18 rounded-2xl bg-slate-900 border border-slate-700/80 shadow-2xl overflow-hidden z-50">
                  <div className="p-3.5 border-b border-slate-800 bg-slate-900/90 flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Bell className="w-4 h-4 text-sky-400" />
                      <span className="text-sm font-bold text-white">Notifications</span>
                      {unreadCount > 0 && (
                        <span className="px-1.5 py-0.2 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30 text-[10px] font-semibold">
                          {unreadCount} new
                        </span>
                      )}
                    </div>
                    <div className="flex items-center space-x-2">
                      {unreadCount > 0 && (
                        <button
                          onClick={handleMarkAllRead}
                          className="p-1 rounded text-xs text-sky-400 hover:bg-slate-800"
                        >
                          Mark read
                        </button>
                      )}
                      <button
                        onClick={() => setIsNotifOpen(false)}
                        className="p-1 rounded text-slate-400 hover:text-white"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  <div className="max-h-72 overflow-y-auto divide-y divide-slate-800">
                    {notifications.length === 0 ? (
                      <div className="p-6 text-center text-xs text-slate-400">
                        No notifications right now.
                      </div>
                    ) : (
                      notifications.map((notif) => (
                        <div
                          key={notif.id}
                          onClick={() => handleItemClick(notif)}
                          className={`p-3 text-xs flex flex-col gap-1 ${
                            !notif.is_read ? 'bg-sky-500/10' : ''
                          }`}
                        >
                          <div className="flex items-center justify-between font-bold text-slate-100">
                            <span>{notif.title}</span>
                            <span className="text-[10px] text-slate-500 font-normal">
                              {formatRelativeTime(notif.created_at)}
                            </span>
                          </div>
                          <p className="text-slate-300 text-[11px]">{notif.message}</p>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Hamburger Button */}
            <button
              onClick={() => {
                setIsMobileMenuOpen(!isMobileMenuOpen);
                setIsNotifOpen(false);
              }}
              className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-700 text-slate-300 hover:text-white hover:bg-slate-700 transition-colors focus:outline-none"
              aria-label="Toggle Navigation Menu"
            >
              {isMobileMenuOpen ? <X className="w-5 h-5 text-sky-400" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Dropdown Menu Drawer */}
      {isMobileMenuOpen && (
        <div className="md:hidden bg-slate-900/95 border-b border-slate-700/80 px-4 pt-3 pb-4 space-y-2 animate-in slide-in-from-top-2 duration-200 shadow-2xl">
          {isMockData && (
            <div className="flex items-center space-x-2 bg-amber-500/10 text-amber-400 border border-amber-500/30 text-xs p-2.5 rounded-xl font-medium mb-3">
              <ShieldAlert className="w-4 h-4 shrink-0" />
              <span>Mock Data Mode (Simulation)</span>
            </div>
          )}

          <button
            onClick={() => handleTabClick('dashboard')}
            className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-bold transition-all ${
              activeTab === 'dashboard'
                ? 'bg-sky-600 text-white shadow-md shadow-sky-600/20'
                : 'text-slate-300 hover:bg-slate-800 hover:text-white'
            }`}
          >
            <LayoutDashboard className="w-5 h-5" />
            <span>Dashboard</span>
          </button>

          <button
            onClick={() => {
              setIsMobileMenuOpen(false);
              onOpenPricingModal();
            }}
            className="w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-bold text-sky-300 bg-slate-800/80 border border-sky-500/30 hover:bg-slate-800 hover:text-white transition-all"
          >
            <Sliders className="w-5 h-5 text-sky-400" />
            <span>Auto Pricing Config</span>
          </button>

          <button
            onClick={() => handleTabClick('settings')}
            className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-bold transition-all ${
              activeTab === 'settings'
                ? 'bg-sky-600 text-white shadow-md shadow-sky-600/20'
                : 'text-slate-300 hover:bg-slate-800 hover:text-white'
            }`}
          >
            <Settings className="w-5 h-5" />
            <span>Settings</span>
          </button>

          <div className="pt-2 border-t border-slate-800">
            <button
              onClick={() => {
                setIsMobileMenuOpen(false);
                authService.logout();
              }}
              className="w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-bold text-rose-400 hover:bg-rose-500/10 transition-all cursor-pointer"
            >
              <LogOut className="w-5 h-5" />
              <span>Sign Out</span>
            </button>
          </div>
        </div>
      )}
    </header>
  );
}
