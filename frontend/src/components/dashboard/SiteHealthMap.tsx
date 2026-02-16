'use client';

import { motion } from 'framer-motion';
import { MapPin, Train, Zap, Building2, Network, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';

interface Site {
  id: string;
  name: string;
  domain: string;
  status: 'healthy' | 'warning' | 'critical';
  sensors: number;
  alerts: number;
  riskScore: number;
  location: { lat: number; lng: number };
}

const mockSites: Site[] = [
  { id: '1', name: 'Railway Junction A1', domain: 'railway', status: 'healthy', sensors: 156, alerts: 0, riskScore: 12, location: { lat: 28.6, lng: 77.2 } },
  { id: '2', name: 'Power Substation B2', domain: 'power', status: 'warning', sensors: 89, alerts: 3, riskScore: 45, location: { lat: 28.5, lng: 77.3 } },
  { id: '3', name: 'Industrial Plant C3', domain: 'industrial', status: 'healthy', sensors: 234, alerts: 1, riskScore: 22, location: { lat: 28.7, lng: 77.1 } },
  { id: '4', name: 'Metro Station D4', domain: 'railway', status: 'critical', sensors: 78, alerts: 5, riskScore: 78, location: { lat: 28.65, lng: 77.25 } },
  { id: '5', name: 'Smart City Hub E5', domain: 'smartcity', status: 'healthy', sensors: 312, alerts: 0, riskScore: 8, location: { lat: 28.55, lng: 77.15 } },
  { id: '6', name: 'Power Grid F6', domain: 'power', status: 'healthy', sensors: 145, alerts: 2, riskScore: 28, location: { lat: 28.58, lng: 77.22 } },
];

const domainIcons: Record<string, any> = {
  railway: Train,
  power: Zap,
  industrial: Building2,
  smartcity: Network,
};

const statusColors = {
  healthy: { bg: 'bg-green-500/10', text: 'text-green-400', dot: 'bg-green-500' },
  warning: { bg: 'bg-yellow-500/10', text: 'text-yellow-400', dot: 'bg-yellow-500' },
  critical: { bg: 'bg-red-500/10', text: 'text-red-400', dot: 'bg-red-500 animate-pulse' },
};

export function SiteHealthMap() {
  const healthyCount = mockSites.filter(s => s.status === 'healthy').length;
  const warningCount = mockSites.filter(s => s.status === 'warning').length;
  const criticalCount = mockSites.filter(s => s.status === 'critical').length;

  return (
    <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-500/10 rounded-xl">
            <MapPin className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Site Health</h3>
            <p className="text-sm text-slate-400">{mockSites.length} monitored sites</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <CheckCircle className="w-4 h-4 text-green-400" />
            <span className="text-sm text-slate-400">{healthyCount}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <AlertTriangle className="w-4 h-4 text-yellow-400" />
            <span className="text-sm text-slate-400">{warningCount}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <XCircle className="w-4 h-4 text-red-400" />
            <span className="text-sm text-slate-400">{criticalCount}</span>
          </div>
        </div>
      </div>

      <div className="space-y-3 max-h-[300px] overflow-y-auto">
        {mockSites.map((site, idx) => {
          const DomainIcon = domainIcons[site.domain] || MapPin;
          const colors = statusColors[site.status];
          
          return (
            <motion.div
              key={site.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.05 }}
              className={`flex items-center gap-4 p-4 rounded-xl ${colors.bg} cursor-pointer hover:scale-[1.02] transition`}
            >
              <div className={`p-2 rounded-lg bg-slate-700/50`}>
                <DomainIcon className={`w-5 h-5 ${colors.text}`} />
              </div>
              
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-white">{site.name}</span>
                  <div className={`w-2 h-2 rounded-full ${colors.dot}`} />
                </div>
                <div className="flex items-center gap-4 mt-1 text-sm text-slate-400">
                  <span>{site.sensors} sensors</span>
                  <span>•</span>
                  <span>{site.alerts} alerts</span>
                  <span>•</span>
                  <span className={site.riskScore > 50 ? 'text-red-400' : site.riskScore > 30 ? 'text-yellow-400' : 'text-green-400'}>
                    {site.riskScore}% risk
                  </span>
                </div>
              </div>
              
              <div className={`px-3 py-1 rounded-full text-xs font-medium ${colors.bg} ${colors.text}`}>
                {site.status.toUpperCase()}
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
