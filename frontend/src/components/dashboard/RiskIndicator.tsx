'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, Shield, TrendingDown, TrendingUp, Minus } from 'lucide-react';

interface RiskData {
  overall: number;
  level: 'critical' | 'high' | 'medium' | 'low' | 'minimal';
  trend: 'increasing' | 'stable' | 'decreasing';
  factors: {
    name: string;
    score: number;
    weight: number;
  }[];
  recommendations: string[];
}

const mockRiskData: RiskData = {
  overall: 0.42,
  level: 'medium',
  trend: 'stable',
  factors: [
    { name: 'Sensor Health', score: 0.15, weight: 0.20 },
    { name: 'Active Alerts', score: 0.55, weight: 0.30 },
    { name: 'Historical Incidents', score: 0.30, weight: 0.20 },
    { name: 'Anomaly Trend', score: 0.45, weight: 0.15 },
    { name: 'Environmental', score: 0.20, weight: 0.10 },
    { name: 'Time Pattern', score: 0.10, weight: 0.05 },
  ],
  recommendations: [
    'Review and address active alerts, prioritizing critical severity',
    'Investigate increasing anomaly patterns for potential system issues',
    'Schedule maintenance at next opportunity'
  ]
};

export function RiskIndicator() {
  const [data, setData] = useState<RiskData>(mockRiskData);
  const [animatedScore, setAnimatedScore] = useState(0);

  useEffect(() => {
    // Animate the score on mount
    const target = data.overall * 100;
    const duration = 1500;
    const steps = 60;
    const increment = target / steps;
    let current = 0;
    
    const timer = setInterval(() => {
      current += increment;
      if (current >= target) {
        setAnimatedScore(target);
        clearInterval(timer);
      } else {
        setAnimatedScore(current);
      }
    }, duration / steps);

    return () => clearInterval(timer);
  }, [data.overall]);

  const levelColors = {
    critical: { ring: 'stroke-red-500', text: 'text-red-400', bg: 'bg-red-500/10' },
    high: { ring: 'stroke-orange-500', text: 'text-orange-400', bg: 'bg-orange-500/10' },
    medium: { ring: 'stroke-yellow-500', text: 'text-yellow-400', bg: 'bg-yellow-500/10' },
    low: { ring: 'stroke-blue-500', text: 'text-blue-400', bg: 'bg-blue-500/10' },
    minimal: { ring: 'stroke-green-500', text: 'text-green-400', bg: 'bg-green-500/10' },
  };

  const TrendIcon = data.trend === 'increasing' ? TrendingUp : data.trend === 'decreasing' ? TrendingDown : Minus;
  const trendColor = data.trend === 'increasing' ? 'text-red-400' : data.trend === 'decreasing' ? 'text-green-400' : 'text-slate-400';

  const circumference = 2 * Math.PI * 45;
  const strokeDashoffset = circumference - (animatedScore / 100) * circumference;

  return (
    <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className={`p-2 rounded-xl ${levelColors[data.level].bg}`}>
          <Shield className={`w-5 h-5 ${levelColors[data.level].text}`} />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-white">Risk Assessment</h3>
          <p className="text-sm text-slate-400">Aggregated risk score</p>
        </div>
      </div>

      {/* Circular Progress */}
      <div className="flex justify-center mb-6">
        <div className="relative w-40 h-40">
          <svg className="w-full h-full -rotate-90">
            {/* Background circle */}
            <circle
              cx="80"
              cy="80"
              r="45"
              fill="none"
              stroke="currentColor"
              strokeWidth="10"
              className="text-slate-700"
            />
            {/* Progress circle */}
            <motion.circle
              cx="80"
              cy="80"
              r="45"
              fill="none"
              strokeWidth="10"
              strokeLinecap="round"
              className={levelColors[data.level].ring}
              strokeDasharray={circumference}
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset }}
              transition={{ duration: 1.5, ease: "easeOut" }}
            />
          </svg>
          {/* Center text */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={`text-3xl font-bold ${levelColors[data.level].text}`}>
              {animatedScore.toFixed(0)}%
            </span>
            <span className="text-sm text-slate-400 uppercase">{data.level} Risk</span>
          </div>
        </div>
      </div>

      {/* Trend */}
      <div className="flex items-center justify-center gap-2 mb-6">
        <TrendIcon className={`w-4 h-4 ${trendColor}`} />
        <span className={`text-sm ${trendColor}`}>
          Trend: {data.trend}
        </span>
      </div>

      {/* Risk Factors */}
      <div className="space-y-3 mb-6">
        <h4 className="text-sm font-medium text-slate-300">Risk Factors</h4>
        {data.factors.map((factor) => (
          <div key={factor.name} className="flex items-center gap-3">
            <div className="flex-1">
              <div className="flex items-center justify-between text-sm mb-1">
                <span className="text-slate-400">{factor.name}</span>
                <span className="text-white">{(factor.score * 100).toFixed(0)}%</span>
              </div>
              <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                <motion.div
                  className={`h-full rounded-full ${
                    factor.score > 0.6 ? 'bg-red-500' :
                    factor.score > 0.4 ? 'bg-yellow-500' :
                    'bg-green-500'
                  }`}
                  initial={{ width: 0 }}
                  animate={{ width: `${factor.score * 100}%` }}
                  transition={{ duration: 1, delay: 0.2 }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recommendations */}
      <div>
        <h4 className="text-sm font-medium text-slate-300 mb-2">Recommendations</h4>
        <ul className="space-y-2">
          {data.recommendations.slice(0, 2).map((rec, idx) => (
            <li key={idx} className="flex items-start gap-2 text-sm text-slate-400">
              <AlertTriangle className="w-4 h-4 text-yellow-400 flex-shrink-0 mt-0.5" />
              {rec}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
