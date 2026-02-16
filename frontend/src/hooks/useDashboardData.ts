'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

interface DashboardStats {
  totalSites: number;
  activeSensors: number;
  activeAlerts: number;
  systemHealth: number;
  criticalAlerts: number;
  sensorUptime: number;
}

interface DashboardData {
  stats: DashboardStats;
  recentAlerts: any[];
  siteHealth: any[];
  sensorStatus: any;
}

async function fetchDashboardData(): Promise<DashboardData> {
  try {
    const response = await api.get('/api/v1/dashboard/stats');
    return response.data;
  } catch (error) {
    // Return mock data for demo
    return {
      stats: {
        totalSites: 40,
        activeSensors: 2847,
        activeAlerts: 23,
        systemHealth: 99.7,
        criticalAlerts: 2,
        sensorUptime: 99.2,
      },
      recentAlerts: [],
      siteHealth: [],
      sensorStatus: {},
    };
  }
}

export function useDashboardData() {
  return useQuery({
    queryKey: ['dashboard'],
    queryFn: fetchDashboardData,
    refetchInterval: 10000, // Refetch every 10 seconds
  });
}
