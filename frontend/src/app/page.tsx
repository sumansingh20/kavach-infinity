'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, Activity, AlertTriangle, Server, Train, Zap, Building2, Network } from 'lucide-react';
import Link from 'next/link';

export default function Home() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const domains = [
    { name: 'Railways & Metro', icon: Train, color: 'from-blue-500 to-blue-700', stats: '12 Sites' },
    { name: 'Power & Utilities', icon: Zap, color: 'from-yellow-500 to-orange-600', stats: '8 Sites' },
    { name: 'Industrial Safety', icon: Building2, color: 'from-green-500 to-emerald-700', stats: '15 Sites' },
    { name: 'Smart Cities', icon: Network, color: 'from-purple-500 to-purple-700', stats: '5 Sites' },
  ];

  const stats = [
    { label: 'Active Sites', value: '40', icon: Server },
    { label: 'Sensors Online', value: '2,847', icon: Activity },
    { label: 'Alerts Today', value: '23', icon: AlertTriangle },
    { label: 'System Health', value: '99.7%', icon: Shield },
  ];

  if (!mounted) return null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        {/* Background Effects */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-kavach-900/20 via-transparent to-transparent" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-kavach-500/10 blur-[120px] rounded-full" />
        
        {/* Header */}
        <header className="relative z-10 px-6 py-4 flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center gap-3">
            <div className="relative">
              <Shield className="w-10 h-10 text-kavach-400" />
              <div className="absolute inset-0 animate-ping">
                <Shield className="w-10 h-10 text-kavach-400 opacity-30" />
              </div>
            </div>
            <div>
              <h1 className="text-2xl font-bold gradient-text">KAVACH-INFINITY</h1>
              <p className="text-xs text-slate-400">Critical Infrastructure Protection</p>
            </div>
          </div>
          
          <nav className="flex items-center gap-4">
            <Link href="/login" className="px-4 py-2 text-sm text-slate-300 hover:text-white transition">
              Login
            </Link>
            <Link 
              href="/dashboard"
              className="px-6 py-2 bg-gradient-to-r from-kavach-500 to-kavach-600 rounded-lg text-white font-medium hover:from-kavach-400 hover:to-kavach-500 transition shadow-lg shadow-kavach-500/25"
            >
              Dashboard
            </Link>
          </nav>
        </header>

        {/* Hero Content */}
        <main className="relative z-10 px-6 pt-20 pb-32 max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-center mb-16"
          >
            <h2 className="text-5xl md:text-6xl font-bold text-white mb-6">
              AI-Powered Safety
              <br />
              <span className="gradient-text">for Critical Infrastructure</span>
            </h2>
            <p className="text-xl text-slate-400 max-w-2xl mx-auto mb-8">
              Real-time monitoring, predictive analytics, and automated response 
              for railways, power grids, industrial facilities, and smart cities.
            </p>
            <div className="flex items-center justify-center gap-4">
              <Link
                href="/dashboard"
                className="px-8 py-3 bg-gradient-to-r from-kavach-500 to-kavach-600 rounded-xl text-white font-semibold hover:from-kavach-400 hover:to-kavach-500 transition shadow-xl shadow-kavach-500/30 flex items-center gap-2"
              >
                <Activity className="w-5 h-5" />
                Live Dashboard
              </Link>
              <Link
                href="/demo"
                className="px-8 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white font-semibold hover:bg-slate-700 transition"
              >
                Watch Demo
              </Link>
            </div>
          </motion.div>

          {/* Stats Grid */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-16"
          >
            {stats.map((stat, idx) => (
              <div
                key={stat.label}
                className="glass-dark rounded-2xl p-6 text-center hover:scale-105 transition-transform"
              >
                <stat.icon className="w-8 h-8 text-kavach-400 mx-auto mb-3" />
                <div className="text-3xl font-bold text-white mb-1">{stat.value}</div>
                <div className="text-sm text-slate-400">{stat.label}</div>
              </div>
            ))}
          </motion.div>

          {/* Domain Cards */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
          >
            <h3 className="text-2xl font-bold text-white text-center mb-8">Protected Domains</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {domains.map((domain, idx) => (
                <motion.div
                  key={domain.name}
                  whileHover={{ y: -5 }}
                  className="relative overflow-hidden rounded-2xl bg-slate-800/50 border border-slate-700/50 p-6 cursor-pointer group"
                >
                  <div className={`absolute inset-0 bg-gradient-to-br ${domain.color} opacity-0 group-hover:opacity-10 transition-opacity`} />
                  <domain.icon className="w-12 h-12 text-kavach-400 mb-4" />
                  <h4 className="text-lg font-semibold text-white mb-2">{domain.name}</h4>
                  <p className="text-sm text-slate-400">{domain.stats} monitored</p>
                  <div className="mt-4 flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                    <span className="text-xs text-green-400">All systems operational</span>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </main>
      </div>

      {/* Live Status Bar */}
      <div className="fixed bottom-0 left-0 right-0 bg-slate-900/90 backdrop-blur-lg border-t border-slate-700 py-3 px-6">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-sm text-slate-300">System Status: <span className="text-green-400">Operational</span></span>
            </div>
            <div className="text-sm text-slate-400">
              Last Update: <span className="text-slate-300">{new Date().toLocaleTimeString()}</span>
            </div>
          </div>
          <div className="text-sm text-slate-400">
            Powered by <span className="text-kavach-400 font-medium">KAVACH AI Engine v2.0</span>
          </div>
        </div>
      </div>
    </div>
  );
}
