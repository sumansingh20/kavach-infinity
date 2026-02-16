'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertTriangle, Bell, CheckCircle, Clock, Eye, Filter, 
  RefreshCw, Search, X, ChevronDown, Download, Volume2, VolumeX
} from 'lucide-react';
import Link from 'next/link';

interface Alert {
  id: string;
  title: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  site: string;
  sensor: string;
  triggeredAt: Date;
  status: 'active' | 'acknowledged' | 'resolved';
  message: string;
  assignee?: string;
}

const generateMockAlerts = (): Alert[] => {
  const severities: Alert['severity'][] = ['critical', 'high', 'medium', 'low', 'info'];
  const statuses: Alert['status'][] = ['active', 'acknowledged', 'resolved'];
  const sites = ['Railway Junction A1', 'Power Substation B2', 'Industrial Plant C3', 'Metro Station D4', 'Smart City Hub E5'];
  const alertTypes = [
    'High Temperature Detected',
    'Vibration Anomaly',
    'Sensor Connection Lost',
    'Power Fluctuation',
    'Gas Leak Warning',
    'Unauthorized Access',
    'Equipment Malfunction',
    'Communication Timeout'
  ];

  return Array.from({ length: 50 }, (_, i) => ({
    id: `ALT-${String(i + 1).padStart(5, '0')}`,
    title: alertTypes[Math.floor(Math.random() * alertTypes.length)],
    severity: severities[Math.floor(Math.random() * severities.length)],
    site: sites[Math.floor(Math.random() * sites.length)],
    sensor: `SENSOR-${String(Math.floor(Math.random() * 1000)).padStart(3, '0')}`,
    triggeredAt: new Date(Date.now() - Math.random() * 86400000 * 7),
    status: statuses[Math.floor(Math.random() * statuses.length)],
    message: 'Anomaly detected in sensor readings. Immediate attention required.',
    assignee: Math.random() > 0.5 ? 'John Doe' : undefined,
  }));
};

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [filteredAlerts, setFilteredAlerts] = useState<Alert[]>([]);
  const [search, setSearch] = useState('');
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setAlerts(generateMockAlerts());
    setIsLoading(false);
  }, []);

  useEffect(() => {
    let result = alerts;

    if (search) {
      const searchLower = search.toLowerCase();
      result = result.filter(
        a => a.title.toLowerCase().includes(searchLower) ||
             a.site.toLowerCase().includes(searchLower) ||
             a.id.toLowerCase().includes(searchLower)
      );
    }

    if (severityFilter !== 'all') {
      result = result.filter(a => a.severity === severityFilter);
    }

    if (statusFilter !== 'all') {
      result = result.filter(a => a.status === statusFilter);
    }

    // Sort by severity and time
    result.sort((a, b) => {
      const severityOrder = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };
      if (severityOrder[a.severity] !== severityOrder[b.severity]) {
        return severityOrder[a.severity] - severityOrder[b.severity];
      }
      return b.triggeredAt.getTime() - a.triggeredAt.getTime();
    });

    setFilteredAlerts(result);
  }, [alerts, search, severityFilter, statusFilter]);

  const severityColors: Record<string, { bg: string; text: string; border: string; badge: string }> = {
    critical: { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500', badge: 'bg-red-500' },
    high: { bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500', badge: 'bg-orange-500' },
    medium: { bg: 'bg-yellow-500/10', text: 'text-yellow-400', border: 'border-yellow-500', badge: 'bg-yellow-500' },
    low: { bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500', badge: 'bg-blue-500' },
    info: { bg: 'bg-slate-500/10', text: 'text-slate-400', border: 'border-slate-500', badge: 'bg-slate-500' }
  };

  const statusColors: Record<string, { bg: string; text: string }> = {
    active: { bg: 'bg-red-500/20', text: 'text-red-400' },
    acknowledged: { bg: 'bg-yellow-500/20', text: 'text-yellow-400' },
    resolved: { bg: 'bg-green-500/20', text: 'text-green-400' }
  };

  const formatTime = (date: Date) => {
    const diff = Date.now() - date.getTime();
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)} min ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)} hours ago`;
    return date.toLocaleDateString();
  };

  const counts = {
    critical: alerts.filter(a => a.severity === 'critical' && a.status === 'active').length,
    high: alerts.filter(a => a.severity === 'high' && a.status === 'active').length,
    total: alerts.filter(a => a.status === 'active').length,
  };

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="bg-slate-800/50 backdrop-blur-lg border-b border-slate-700 sticky top-0 z-20">
        <div className="px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/dashboard" className="text-slate-400 hover:text-white transition">
              ← Dashboard
            </Link>
            <div className="h-6 w-px bg-slate-700" />
            <div className="flex items-center gap-2">
              <Bell className="w-6 h-6 text-kavach-400" />
              <h1 className="text-xl font-bold text-white">Alert Management</h1>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setSoundEnabled(!soundEnabled)}
              className={`p-2 rounded-lg transition ${
                soundEnabled ? 'bg-kavach-500/20 text-kavach-400' : 'bg-slate-700 text-slate-400'
              }`}
            >
              {soundEnabled ? <Volume2 className="w-5 h-5" /> : <VolumeX className="w-5 h-5" />}
            </button>
            <button className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition">
              <Download className="w-5 h-5" />
            </button>
            <button className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition">
              <RefreshCw className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Stats Bar */}
        <div className="px-6 py-3 border-t border-slate-700 flex items-center gap-6">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500 animate-pulse" />
            <span className="text-sm text-slate-400">
              <span className="text-red-400 font-bold">{counts.critical}</span> Critical
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-orange-500" />
            <span className="text-sm text-slate-400">
              <span className="text-orange-400 font-bold">{counts.high}</span> High
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-blue-500" />
            <span className="text-sm text-slate-400">
              <span className="text-white font-bold">{counts.total}</span> Active
            </span>
          </div>
        </div>
      </header>

      {/* Filters */}
      <div className="px-6 py-4 border-b border-slate-700 flex items-center gap-4 flex-wrap">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search alerts..."
            className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-kavach-500"
          />
        </div>

        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-kavach-500"
        >
          <option value="all">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
          <option value="info">Info</option>
        </select>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-kavach-500"
        >
          <option value="all">All Statuses</option>
          <option value="active">Active</option>
          <option value="acknowledged">Acknowledged</option>
          <option value="resolved">Resolved</option>
        </select>

        <span className="text-sm text-slate-400">
          Showing {filteredAlerts.length} of {alerts.length} alerts
        </span>
      </div>

      {/* Alert List */}
      <div className="p-6">
        <div className="space-y-3">
          <AnimatePresence>
            {filteredAlerts.map((alert, index) => (
              <motion.div
                key={alert.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ delay: index * 0.02 }}
                className={`border-l-4 ${severityColors[alert.severity].border} ${severityColors[alert.severity].bg} bg-slate-800/50 rounded-r-xl p-4 cursor-pointer hover:bg-slate-800 transition ${
                  alert.severity === 'critical' && alert.status === 'active' ? 'alert-critical' : ''
                }`}
                onClick={() => setSelectedAlert(alert)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`px-2 py-0.5 rounded text-xs font-bold ${severityColors[alert.severity].badge} text-white`}>
                        {alert.severity.toUpperCase()}
                      </span>
                      <span className={`px-2 py-0.5 rounded text-xs ${statusColors[alert.status].bg} ${statusColors[alert.status].text}`}>
                        {alert.status}
                      </span>
                      <span className="text-xs text-slate-500">{alert.id}</span>
                    </div>
                    <h4 className="font-semibold text-white mb-1">{alert.title}</h4>
                    <p className="text-sm text-slate-400 mb-2">{alert.message}</p>
                    <div className="flex items-center gap-4 text-xs text-slate-500">
                      <span>{alert.site}</span>
                      <span>•</span>
                      <span>{alert.sensor}</span>
                      <span>•</span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatTime(alert.triggeredAt)}
                      </span>
                      {alert.assignee && (
                        <>
                          <span>•</span>
                          <span>Assigned: {alert.assignee}</span>
                        </>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2 ml-4">
                    {alert.status === 'active' && (
                      <button className="px-3 py-1.5 text-sm bg-yellow-500/10 text-yellow-400 border border-yellow-500/20 rounded-lg hover:bg-yellow-500/20 transition">
                        Acknowledge
                      </button>
                    )}
                    {alert.status !== 'resolved' && (
                      <button className="px-3 py-1.5 text-sm bg-green-500/10 text-green-400 border border-green-500/20 rounded-lg hover:bg-green-500/20 transition">
                        Resolve
                      </button>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </div>

      {/* Alert Detail Modal */}
      <AnimatePresence>
        {selectedAlert && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
            onClick={() => setSelectedAlert(null)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="bg-slate-800 border border-slate-700 rounded-2xl p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto"
              onClick={e => e.stopPropagation()}
            >
              <div className="flex items-start justify-between mb-6">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`px-2 py-0.5 rounded text-xs font-bold ${severityColors[selectedAlert.severity].badge} text-white`}>
                      {selectedAlert.severity.toUpperCase()}
                    </span>
                    <span className="text-sm text-slate-400">{selectedAlert.id}</span>
                  </div>
                  <h3 className="text-xl font-bold text-white">{selectedAlert.title}</h3>
                </div>
                <button
                  onClick={() => setSelectedAlert(null)}
                  className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-slate-700/30 rounded-lg p-4">
                  <span className="text-sm text-slate-400">Status</span>
                  <div className={`mt-1 font-medium ${statusColors[selectedAlert.status].text}`}>
                    {selectedAlert.status.charAt(0).toUpperCase() + selectedAlert.status.slice(1)}
                  </div>
                </div>
                <div className="bg-slate-700/30 rounded-lg p-4">
                  <span className="text-sm text-slate-400">Site</span>
                  <div className="mt-1 font-medium text-white">{selectedAlert.site}</div>
                </div>
                <div className="bg-slate-700/30 rounded-lg p-4">
                  <span className="text-sm text-slate-400">Sensor</span>
                  <div className="mt-1 font-medium text-white">{selectedAlert.sensor}</div>
                </div>
                <div className="bg-slate-700/30 rounded-lg p-4">
                  <span className="text-sm text-slate-400">Triggered</span>
                  <div className="mt-1 font-medium text-white">
                    {selectedAlert.triggeredAt.toLocaleString()}
                  </div>
                </div>
              </div>

              <div className="bg-slate-700/30 rounded-lg p-4 mb-6">
                <span className="text-sm text-slate-400">Message</span>
                <div className="mt-2 text-white">{selectedAlert.message}</div>
              </div>

              <div className="flex gap-3">
                {selectedAlert.status === 'active' && (
                  <button className="flex-1 bg-yellow-500/10 text-yellow-400 border border-yellow-500/20 px-4 py-3 rounded-lg hover:bg-yellow-500/20 transition font-medium">
                    Acknowledge Alert
                  </button>
                )}
                {selectedAlert.status !== 'resolved' && (
                  <button className="flex-1 bg-green-500/10 text-green-400 border border-green-500/20 px-4 py-3 rounded-lg hover:bg-green-500/20 transition font-medium">
                    Resolve Alert
                  </button>
                )}
                <button className="px-4 py-3 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition font-medium">
                  View Details
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
