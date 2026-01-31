'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, Legend 
} from 'recharts';
import { Activity, TrendingUp } from 'lucide-react';

const generateData = () => {
  const now = new Date();
  const data = [];
  
  for (let i = 23; i >= 0; i--) {
    const hour = new Date(now.getTime() - i * 60 * 60 * 1000);
    data.push({
      time: hour.toLocaleTimeString('en-US', { hour: '2-digit' }),
      alerts: Math.floor(Math.random() * 10) + 2,
      anomalies: Math.floor(Math.random() * 5),
      sensors: 2800 + Math.floor(Math.random() * 100),
      temperature: 45 + Math.random() * 20,
      risk: 30 + Math.random() * 30,
    });
  }
  
  return data;
};

export function MetricsChart() {
  const [data] = useState(generateData);
  const [activeMetric, setActiveMetric] = useState<'alerts' | 'risk' | 'sensors'>('alerts');

  const metrics = [
    { key: 'alerts', label: 'Alerts', color: '#f97316' },
    { key: 'risk', label: 'Risk Score', color: '#eab308' },
    { key: 'sensors', label: 'Active Sensors', color: '#22c55e' },
  ];

  return (
    <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-kavach-500/10 rounded-xl">
            <Activity className="w-5 h-5 text-kavach-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">System Metrics</h3>
            <p className="text-sm text-slate-400">24-hour trend</p>
          </div>
        </div>

        <div className="flex gap-2">
          {metrics.map((metric) => (
            <button
              key={metric.key}
              onClick={() => setActiveMetric(metric.key as any)}
              className={`px-3 py-1.5 text-sm rounded-lg transition ${
                activeMetric === metric.key
                  ? 'bg-kavach-500/20 text-kavach-400 border border-kavach-500/30'
                  : 'text-slate-400 hover:bg-slate-700'
              }`}
            >
              {metric.label}
            </button>
          ))}
        </div>
      </div>

      <div className="h-[280px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="alertsGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f97316" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="riskGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#eab308" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#eab308" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="sensorsGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis 
              dataKey="time" 
              stroke="#64748b"
              tick={{ fill: '#94a3b8', fontSize: 12 }}
            />
            <YAxis 
              stroke="#64748b"
              tick={{ fill: '#94a3b8', fontSize: 12 }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
                color: '#fff'
              }}
            />
            {activeMetric === 'alerts' && (
              <Area
                type="monotone"
                dataKey="alerts"
                stroke="#f97316"
                strokeWidth={2}
                fill="url(#alertsGradient)"
              />
            )}
            {activeMetric === 'risk' && (
              <Area
                type="monotone"
                dataKey="risk"
                stroke="#eab308"
                strokeWidth={2}
                fill="url(#riskGradient)"
              />
            )}
            {activeMetric === 'sensors' && (
              <Area
                type="monotone"
                dataKey="sensors"
                stroke="#22c55e"
                strokeWidth={2}
                fill="url(#sensorsGradient)"
              />
            )}
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-slate-700">
        <div className="text-center">
          <div className="text-2xl font-bold text-orange-400">
            {data[data.length - 1].alerts}
          </div>
          <div className="text-sm text-slate-400">Current Alerts</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-yellow-400">
            {data[data.length - 1].risk.toFixed(0)}%
          </div>
          <div className="text-sm text-slate-400">Risk Score</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-green-400">
            {data[data.length - 1].sensors}
          </div>
          <div className="text-sm text-slate-400">Active Sensors</div>
        </div>
      </div>
    </div>
  );
}
