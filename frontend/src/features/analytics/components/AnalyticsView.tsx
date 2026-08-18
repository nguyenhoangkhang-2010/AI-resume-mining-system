import {
  ErrorState,
  Loading,
} from "@/components/common";

import { AnalyticsHeader } from "./AnalyticsHeader";
import { AnalyticsStats } from "./AnalyticsStats";
import { AnalyticsCharts } from "./AnalyticsCharts";
import { AnalyticsEmptyState } from "./AnalyticsEmptyState";

import { useAnalytics } from "../hooks/useAnalytics";


export function AnalyticsView() {
  const {
    loading,
    error,
    data,
  } = useAnalytics();


  if (loading) {
    return <Loading />;
  }


  if (error) {
    return (
      <ErrorState
        title="Failed to load analytics"
        description={error.message}
      />
    );
  }


  return (
    <section
      className="
        flex
        flex-col
        gap-6
      "
    >
      <AnalyticsHeader />

      {!data ||
      (
        data.stats.length === 0 &&
        data.charts.length === 0
      ) ? (
        <AnalyticsEmptyState />
      ) : (
        <>
          <AnalyticsStats
            stats={data.stats}
          />

          <AnalyticsCharts
            charts={data.charts}
          />
        </>
      )}
    </section>
  );
}