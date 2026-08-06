import { ErrorState, Loading } from "@/components/common";

import { DashboardContent } from "./DashboardContent";
import { DashboardHeader } from "./DashboardHeader";
import { useDashboard } from "../hooks/useDashboard";
import { DashboardCharts } from "./DashboardCharts";
import { DashboardRecentActivity } from "./DashboardRecentActivity";
import { DashboardStats } from "./DashboardStats";



export function DashboardView() {
  const {
    loading,
    error,
    data,
  } = useDashboard();

  if (loading) {
    return <Loading />;
  }

  if (error) {
    return (
      <ErrorState
        title="Failed to load dashboard"
        description={error.message}
      />
    );
  }

  if (!data) {
    return null;
  }

    return (
    <>
      <DashboardHeader />

      <DashboardContent
        stats={
          <DashboardStats
            stats={data.stats}
          />
        }
        charts={
          <DashboardCharts
            charts={data.charts}
          />
        }
        activity={
          <DashboardRecentActivity
            activities={data.activities}
          />
        }
      />
    </>
  );
}