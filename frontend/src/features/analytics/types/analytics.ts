export interface AnalyticsStat {
  id: string;
  label: string;
  value: number | string;
  trend: number;
  trendLabel?: string;
  chartData: {
    value: number;
  }[];
}

export interface AnalyticsChart {
  id: string;
  title: string;
  type:
    | "line"
    | "area"
    | "bar"
    | "donut"
    | "radar";

  data: Record<string, unknown>[];

  xKey?: string;
  yKey?: string;

  nameKey?: string;
  valueKey?: string;

  color?: string;
}

export interface AnalyticsData {
  stats: AnalyticsStat[];
  charts: AnalyticsChart[];
}