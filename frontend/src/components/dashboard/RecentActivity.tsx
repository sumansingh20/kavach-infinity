'use client';

import { motion } from 'framer-motion';
import { Activity, AlertTriangle, Bell, CheckCircle, Clock, Settings, User, Shield } from 'lucide-react';

interface ActivityItem {
  id: string;
  type: 'alert' | 'user' | 'system' | 'safety';
  message: string;
  timestamp: string;
  user?: string;
}

const mockActivity: ActivityItem[] = [
  { id: '1', type: 'alert', message: 'Critical alert triggered at Railway Junction A1', timestamp: '2 min ago' },
  { id: '2', type: 'user', message: 'John Doe acknowledged alert #1245', timestamp: '5 min ago', user: 'John Doe' },
  { id: '3', type: 'system', message: 'AI model retrained with 1,247 new samples', timestamp: '15 min ago' },
  { id: '4', type: 'safety', message: 'Safety override released at Power Substation B2', timestamp: '32 min ago' },
  { id: '5', type: 'alert', message: 'Sensor TEMP-042 restored to normal', timestamp: '1 hour ago' },
  { id: '6', type: 'user', message: 'Admin updated site configuration', timestamp: '2 hours ago', user: 'Admin' },
  { id: '7', type: 'system', message: 'Daily backup completed successfully', timestamp: '3 hours ago' },
  { id: '8', type: 'alert', message: 'Vibration anomaly detected at Industrial Plant C3', timestamp: '4 hours ago' },
];

const typeConfig = {
  alert: { icon: AlertTriangle, color: 'text-orange-400', bg: 'bg-orange-500/10' },
  user: { icon: User, color: 'text-blue-400', bg: 'bg-blue-500/10' },
  system: { icon: Settings, color: 'text-slate-400', bg: 'bg-slate-500/10' },
  safety: { icon: Shield, color: 'text-green-400', bg: 'bg-green-500/10' },
};

export function RecentActivity() {
  return (
    <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-purple-500/10 rounded-xl">
          <Activity className="w-5 h-5 text-purple-400" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-white">Recent Activity</h3>
          <p className="text-sm text-slate-400">System events and actions</p>
        </div>
      </div>

      <div className="space-y-4 max-h-[300px] overflow-y-auto">
        {mockActivity.map((item, idx) => {
          const config = typeConfig[item.type];
          const Icon = config.icon;

          return (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05 }}
              className="flex items-start gap-3"
            >
              <div className={`p-2 rounded-lg ${config.bg} flex-shrink-0`}>
                <Icon className={`w-4 h-4 ${config.color}`} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-white truncate">{item.message}</p>
                <div className="flex items-center gap-2 mt-1 text-xs text-slate-500">
                  <Clock className="w-3 h-3" />
                  <span>{item.timestamp}</span>
                  {item.user && (
                    <>
                      <span>•</span>
                      <span>{item.user}</span>
                    </>
                  )}
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      <button className="w-full mt-4 py-2 text-sm text-kavach-400 hover:text-kavach-300 border border-slate-700 rounded-lg hover:bg-slate-700/50 transition">
        View All Activity
      </button>
    </div>
  );
}
