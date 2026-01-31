'use client';

import { motion } from 'framer-motion';
import { Activity, Wifi, WifiOff, AlertTriangle, CheckCircle } from 'lucide-react';

interface SensorStatus {
  type: string;
  total: number;
  online: number;
  offline: number;
  warning: number;
}

const mockSensorData: SensorStatus[] = [
  { type: 'Temperature', total: 450, online: 442, offline: 3, warning: 5 },
  { type: 'Vibration', total: 380, online: 375, offline: 2, warning: 3 },
  { type: 'Pressure', total: 290, online: 285, offline: 1, warning: 4 },
  { type: 'Proximity', total: 520, online: 512, offline: 4, warning: 4 },
  { type: 'Gas', total: 180, online: 178, offline: 0, warning: 2 },
  { type: 'Thermal', total: 245, online: 240, offline: 2, warning: 3 },
  { type: 'Motion', total: 390, online: 385, offline: 3, warning: 2 },
  { type: 'Network', total: 392, online: 388, offline: 2, warning: 2 },
];

export function SensorStatusGrid() {
  const totals = mockSensorData.reduce(
    (acc, s) => ({
      total: acc.total + s.total,
      online: acc.online + s.online,
      offline: acc.offline + s.offline,
      warning: acc.warning + s.warning,
    }),
    { total: 0, online: 0, offline: 0, warning: 0 }
  );

  return (
    <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-green-500/10 rounded-xl">
            <Activity className="w-5 h-5 text-green-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Sensor Status</h3>
            <p className="text-sm text-slate-400">{totals.total} total sensors</p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-1.5">
            <Wifi className="w-4 h-4 text-green-400" />
            <span className="text-slate-400">{totals.online}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <WifiOff className="w-4 h-4 text-red-400" />
            <span className="text-slate-400">{totals.offline}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <AlertTriangle className="w-4 h-4 text-yellow-400" />
            <span className="text-slate-400">{totals.warning}</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {mockSensorData.map((sensor, idx) => (
          <motion.div
            key={sensor.type}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: idx * 0.05 }}
            className="bg-slate-700/30 rounded-xl p-4 hover:bg-slate-700/50 transition cursor-pointer"
          >
            <div className="text-sm text-slate-400 mb-2">{sensor.type}</div>
            <div className="text-2xl font-bold text-white mb-2">{sensor.total}</div>
            
            {/* Status bar */}
            <div className="h-2 bg-slate-600 rounded-full overflow-hidden flex">
              <div
                className="bg-green-500 h-full"
                style={{ width: `${(sensor.online / sensor.total) * 100}%` }}
              />
              <div
                className="bg-yellow-500 h-full"
                style={{ width: `${(sensor.warning / sensor.total) * 100}%` }}
              />
              <div
                className="bg-red-500 h-full"
                style={{ width: `${(sensor.offline / sensor.total) * 100}%` }}
              />
            </div>
            
            <div className="flex items-center justify-between mt-2 text-xs">
              <span className="text-green-400">{sensor.online} online</span>
              {sensor.offline > 0 && (
                <span className="text-red-400">{sensor.offline} offline</span>
              )}
            </div>
          </motion.div>
        ))}
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-6 mt-4 pt-4 border-t border-slate-700">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-green-500" />
          <span className="text-sm text-slate-400">Online ({((totals.online / totals.total) * 100).toFixed(1)}%)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-yellow-500" />
          <span className="text-sm text-slate-400">Warning ({((totals.warning / totals.total) * 100).toFixed(1)}%)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500" />
          <span className="text-sm text-slate-400">Offline ({((totals.offline / totals.total) * 100).toFixed(1)}%)</span>
        </div>
      </div>
    </div>
  );
}
