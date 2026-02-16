'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, Bell, CheckCircle, Clock, Eye, Filter, X } from 'lucide-react';

interface Alert {
  id: string;
  title: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  site: string;
  sensor: string;
  triggeredAt: string;
  status: 'active' | 'acknowledged' | 'resolved';
  message: string;
}

const mockAlerts: Alert[] = [
  {
    id: '1',
    title: 'High Temperature Detected',
    severity: 'critical',
    site: 'Railway Junction A1',
    sensor: 'TEMP-001',
    triggeredAt: '2 min ago',
    status: 'active',
    message: 'Temperature reading 95°C exceeds threshold of 85°C'
  },
  {
    id: '2',
    title: 'Vibration Anomaly',
    severity: 'high',
    site: 'Power Substation B2',
    sensor: 'VIB-042',
    triggeredAt: '15 min ago',
    status: 'active',
    message: 'Unusual vibration pattern detected on transformer unit'
  },
  {
    id: '3',
    title: 'Sensor Connection Lost',
    severity: 'medium',
    site: 'Industrial Plant C3',
    sensor: 'NET-015',
    triggeredAt: '1 hour ago',
    status: 'acknowledged',
    message: 'Network sensor offline for 30 minutes'
  },
  {
    id: '4',
    title: 'Low Battery Warning',
    severity: 'low',
    site: 'Smart City Hub D4',
    sensor: 'BAT-078',
    triggeredAt: '3 hours ago',
    status: 'active',
    message: 'Battery level at 15%, replacement recommended'
  },
  {
    id: '5',
    title: 'Routine Maintenance Due',
    severity: 'info',
    site: 'Metro Station E5',
    sensor: 'MAINT-003',
    triggeredAt: '1 day ago',
    status: 'active',
    message: 'Scheduled maintenance due in 7 days'
  }
];

export function AlertsPanel() {
  const [alerts, setAlerts] = useState<Alert[]>(mockAlerts);
  const [filter, setFilter] = useState<string>('all');
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);

  const severityColors: Record<string, { bg: string; text: string; border: string }> = {
    critical: { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-l-red-500' },
    high: { bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-l-orange-500' },
    medium: { bg: 'bg-yellow-500/10', text: 'text-yellow-400', border: 'border-l-yellow-500' },
    low: { bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-l-blue-500' },
    info: { bg: 'bg-slate-500/10', text: 'text-slate-400', border: 'border-l-slate-500' }
  };

  const filteredAlerts = filter === 'all' 
    ? alerts 
    : alerts.filter(a => a.severity === filter);

  return (
    <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-red-500/10 rounded-xl">
            <Bell className="w-5 h-5 text-red-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Active Alerts</h3>
            <p className="text-sm text-slate-400">{alerts.filter(a => a.status === 'active').length} unresolved</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="bg-slate-700/50 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-kavach-500"
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
            <option value="info">Info</option>
          </select>
        </div>
      </div>

      <div className="space-y-3 max-h-[400px] overflow-y-auto">
        <AnimatePresence>
          {filteredAlerts.map((alert, index) => (
            <motion.div
              key={alert.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ delay: index * 0.05 }}
              className={`border-l-4 ${severityColors[alert.severity].border} bg-slate-700/30 rounded-r-xl p-4 cursor-pointer hover:bg-slate-700/50 transition ${
                alert.severity === 'critical' ? 'alert-critical' : ''
              }`}
              onClick={() => setSelectedAlert(alert)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${severityColors[alert.severity].bg} ${severityColors[alert.severity].text}`}>
                      {alert.severity.toUpperCase()}
                    </span>
                    <span className={`px-2 py-0.5 rounded-full text-xs ${
                      alert.status === 'active' ? 'bg-red-500/20 text-red-400' :
                      alert.status === 'acknowledged' ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-green-500/20 text-green-400'
                    }`}>
                      {alert.status}
                    </span>
                  </div>
                  <h4 className="font-medium text-white mb-1">{alert.title}</h4>
                  <p className="text-sm text-slate-400 mb-2">{alert.message}</p>
                  <div className="flex items-center gap-4 text-xs text-slate-500">
                    <span>{alert.site}</span>
                    <span>•</span>
                    <span>{alert.sensor}</span>
                    <span>•</span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {alert.triggeredAt}
                    </span>
                  </div>
                </div>
                <div className="flex gap-1">
                  <button className="p-2 text-slate-400 hover:text-white hover:bg-slate-600 rounded-lg transition">
                    <Eye className="w-4 h-4" />
                  </button>
                  <button className="p-2 text-slate-400 hover:text-green-400 hover:bg-green-500/10 rounded-lg transition">
                    <CheckCircle className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Alert Detail Modal */}
      <AnimatePresence>
        {selectedAlert && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
            onClick={() => setSelectedAlert(null)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="bg-slate-800 border border-slate-700 rounded-2xl p-6 max-w-lg w-full mx-4"
              onClick={e => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">{selectedAlert.title}</h3>
                <button
                  onClick={() => setSelectedAlert(null)}
                  className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-sm text-slate-400">Severity</span>
                    <div className={`mt-1 ${severityColors[selectedAlert.severity].text}`}>
                      {selectedAlert.severity.toUpperCase()}
                    </div>
                  </div>
                  <div>
                    <span className="text-sm text-slate-400">Status</span>
                    <div className="mt-1 text-white">{selectedAlert.status}</div>
                  </div>
                  <div>
                    <span className="text-sm text-slate-400">Site</span>
                    <div className="mt-1 text-white">{selectedAlert.site}</div>
                  </div>
                  <div>
                    <span className="text-sm text-slate-400">Sensor</span>
                    <div className="mt-1 text-white">{selectedAlert.sensor}</div>
                  </div>
                </div>
                <div>
                  <span className="text-sm text-slate-400">Message</span>
                  <div className="mt-1 text-white">{selectedAlert.message}</div>
                </div>
                <div className="flex gap-3 pt-4">
                  <button className="flex-1 bg-yellow-500/10 text-yellow-400 border border-yellow-500/20 px-4 py-2 rounded-lg hover:bg-yellow-500/20 transition">
                    Acknowledge
                  </button>
                  <button className="flex-1 bg-green-500/10 text-green-400 border border-green-500/20 px-4 py-2 rounded-lg hover:bg-green-500/20 transition">
                    Resolve
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
