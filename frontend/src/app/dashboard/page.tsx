'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Activity, AlertTriangle, Bell, ChevronDown, Clock, 
  Menu, Moon, RefreshCw, Search, Server, Settings, 
  Shield, Sun, User, X, Zap, Train, Building2, Network,
  TrendingUp, TrendingDown, Minus, Eye, CheckCircle
} from 'lucide-react';
import Link from 'next/link';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useDashboardData } from '@/hooks/useDashboardData';
import { AlertsPanel } from '@/components/dashboard/AlertsPanel';
import { SiteHealthMap } from '@/components/dashboard/SiteHealthMap';
import { MetricsChart } from '@/components/dashboard/MetricsChart';
import { SensorStatusGrid } from '@/components/dashboard/SensorStatusGrid';
import { RiskIndicator } from '@/components/dashboard/RiskIndicator';
import { RecentActivity } from '@/components/dashboard/RecentActivity';

export default function DashboardPage() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [darkMode, setDarkMode] = useState(true);
  const { isConnected, lastMessage } = useWebSocket();
  const { data, isLoading, refetch } = useDashboardData();

  const navItems = [
    { name: 'Dashboard', icon: Activity, href: '/dashboard', active: true },
    { name: 'Sites', icon: Server, href: '/dashboard/sites' },
    { name: 'Sensors', icon: Zap, href: '/dashboard/sensors' },
    { name: 'Alerts', icon: Bell, href: '/dashboard/alerts' },
    { name: 'AI Models', icon: Shield, href: '/dashboard/ai' },
    { name: 'Safety', icon: AlertTriangle, href: '/dashboard/safety' },
    { name: 'Settings', icon: Settings, href: '/dashboard/settings' },
  ];

  const stats = data?.stats || {
    totalSites: 40,
    activeSensors: 2847,
    activeAlerts: 23,
    systemHealth: 99.7,
    criticalAlerts: 2,
    sensorUptime: 99.2,
  };

  return (
    <div className={`min-h-screen ${darkMode ? 'dark bg-slate-900' : 'bg-slate-100'}`}>
      {/* Sidebar */}
      <aside className={`fixed top-0 left-0 h-full z-40 transition-all duration-300 ${
        sidebarOpen ? 'w-64' : 'w-20'
      } bg-slate-800 border-r border-slate-700`}>
        {/* Logo */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <Shield className="w-8 h-8 text-kavach-400" />
            {sidebarOpen && (
              <span className="font-bold text-white">KAVACH-∞</span>
            )}
          </div>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-slate-400 hover:text-white transition"
          >
            <Menu className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-2">
          {navItems.map((item) => (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition ${
                item.active
                  ? 'bg-kavach-500/20 text-kavach-400'
                  : 'text-slate-400 hover:bg-slate-700/50 hover:text-white'
              }`}
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              {sidebarOpen && <span>{item.name}</span>}
            </Link>
          ))}
        </nav>

        {/* Connection Status */}
        <div className="absolute bottom-4 left-4 right-4">
          <div className={`flex items-center gap-2 px-4 py-3 rounded-xl ${
            isConnected ? 'bg-green-500/10' : 'bg-red-500/10'
          }`}>
            <div className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'
            }`} />
            {sidebarOpen && (
              <span className={`text-sm ${
                isConnected ? 'text-green-400' : 'text-red-400'
              }`}>
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            )}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className={`transition-all duration-300 ${
        sidebarOpen ? 'ml-64' : 'ml-20'
      }`}>
        {/* Header */}
        <header className="h-16 bg-slate-800/50 backdrop-blur-lg border-b border-slate-700 flex items-center justify-between px-6 sticky top-0 z-30">
          <div className="flex items-center gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search sites, sensors, alerts..."
                className="w-80 bg-slate-700/50 border border-slate-600 rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-kavach-500"
              />
            </div>
          </div>

          <div className="flex items-center gap-4">
            <button
              onClick={() => refetch()}
              className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition"
            >
              {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>
            <button className="relative p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition">
              <Bell className="w-5 h-5" />
              {stats.criticalAlerts > 0 && (
                <span className="absolute top-0 right-0 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                  {stats.criticalAlerts}
                </span>
              )}
            </button>
            <div className="flex items-center gap-2 pl-4 border-l border-slate-700">
              <div className="w-8 h-8 bg-kavach-500 rounded-full flex items-center justify-center text-white font-medium">
                A
              </div>
              <span className="text-sm text-white">Admin</span>
            </div>
          </div>
        </header>

        {/* Dashboard Content */}
        <div className="p-6">
          {/* Page Title */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold text-white">Dashboard Overview</h1>
              <p className="text-slate-400">Real-time monitoring of all protected infrastructure</p>
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <Clock className="w-4 h-4" />
              Last updated: {new Date().toLocaleTimeString()}
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <StatsCard
              title="Total Sites"
              value={stats.totalSites}
              icon={Server}
              trend="stable"
              color="blue"
            />
            <StatsCard
              title="Active Sensors"
              value={stats.activeSensors.toLocaleString()}
              icon={Activity}
              trend="up"
              change="+12"
              color="green"
            />
            <StatsCard
              title="Active Alerts"
              value={stats.activeAlerts}
              icon={AlertTriangle}
              trend="down"
              change="-5"
              color="yellow"
            />
            <StatsCard
              title="System Health"
              value={`${stats.systemHealth}%`}
              icon={Shield}
              trend="stable"
              color="kavach"
            />
          </div>

          {/* Main Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            {/* Left Column - Alerts */}
            <div className="lg:col-span-2">
              <AlertsPanel />
            </div>

            {/* Right Column - Risk */}
            <div>
              <RiskIndicator />
            </div>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <MetricsChart />
            <SensorStatusGrid />
          </div>

          {/* Bottom Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <SiteHealthMap />
            <RecentActivity />
          </div>
        </div>
      </main>
    </div>
  );
}

// Stats Card Component
function StatsCard({ 
  title, 
  value, 
  icon: Icon, 
  trend, 
  change, 
  color 
}: {
  title: string;
  value: string | number;
  icon: any;
  trend: 'up' | 'down' | 'stable';
  change?: string;
  color: string;
}) {
  const colorClasses: Record<string, string> = {
    blue: 'text-blue-400 bg-blue-500/10',
    green: 'text-green-400 bg-green-500/10',
    yellow: 'text-yellow-400 bg-yellow-500/10',
    red: 'text-red-400 bg-red-500/10',
    kavach: 'text-kavach-400 bg-kavach-500/10',
  };

  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus;
  const trendColor = trend === 'up' ? 'text-green-400' : trend === 'down' ? 'text-red-400' : 'text-slate-400';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-xl ${colorClasses[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
        {change && (
          <div className={`flex items-center gap-1 ${trendColor}`}>
            <TrendIcon className="w-4 h-4" />
            <span className="text-sm">{change}</span>
          </div>
        )}
      </div>
      <div className="text-3xl font-bold text-white mb-1">{value}</div>
      <div className="text-sm text-slate-400">{title}</div>
    </motion.div>
  );
}
