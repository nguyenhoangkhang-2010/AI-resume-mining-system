export { default as DashboardPage } from "./page";

export { DashboardView } from "./components/DashboardView";

export { DashboardHeader } from "./components/DashboardHeader";
export { DashboardStats } from "./components/DashboardStats";
export { DashboardCharts } from "./components/DashboardCharts";
export { DashboardRecentActivity } from "./components/DashboardRecentActivity";
export { DashboardContent } from "./components/DashboardContent";

export { useDashboard } from "./hooks/useDashboard";

export type {
  DashboardData,
  DashboardStat,
  DashboardActivity,
  DashboardChart,
} from "./types/dashboard";