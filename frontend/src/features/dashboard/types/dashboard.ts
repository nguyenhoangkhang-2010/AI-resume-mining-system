import type { DonutChartData } from "@/components/charts";

export interface DashboardStat {
  id: "candidates" | "jobs" | "matching" | "knowledge";
  title: string;
  value: string | number;
  trend: number;
  trendLabel?: string;
  chartData: {
    value: number;
  }[];
  color?: string;
}

export interface DashboardActivity {
  id: string;
  title: string;
  description: string;
  timestamp: string;
}

interface DashboardChartBase {
  id: string;
  title: string;
  subtitle?: string;
  color?: string;
}

export interface DashboardLineChart
  extends DashboardChartBase {
  type: "line";
  data: Record<string, unknown>[];
  xKey: string;
  yKey: string;
}

export interface DashboardAreaChart
  extends DashboardChartBase {
  type: "area";
  data: Record<string, unknown>[];
  xKey: string;
  yKey: string;
}

export interface DashboardBarChart
  extends DashboardChartBase {
  type: "bar";
  data: Record<string, unknown>[];
  xKey: string;
  yKey: string;
}

export interface DashboardRadarChart
  extends DashboardChartBase {
  type: "radar";
  data: Record<string, unknown>[];
  nameKey: string;
  valueKey: string;
}

export interface DashboardDonutChart
  extends DashboardChartBase {
  type: "donut";
  data: DonutChartData[];
}

export type DashboardChart =
  | DashboardLineChart
  | DashboardAreaChart
  | DashboardBarChart
  | DashboardRadarChart
  | DashboardDonutChart;

export interface DashboardData {
  stats: DashboardStat[];
  activities: DashboardActivity[];
  charts: DashboardChart[];
}