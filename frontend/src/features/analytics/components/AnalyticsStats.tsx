import {
  StatCard,
} from "@/components/charts";

import type {
  AnalyticsStat,
} from "../types/analytics";


interface AnalyticsStatsProps {
  stats: AnalyticsStat[];
}


export function AnalyticsStats({
  stats,
}: AnalyticsStatsProps) {
  if (stats.length === 0) {
    return null;
  }

  return (
    <section
      className="
        grid
        gap-6
        sm:grid-cols-2
        xl:grid-cols-4
      "
    >
      {stats.map((stat) => (
        <StatCard
          key={stat.id}
          title={stat.label}
          value={stat.value}
          trend={stat.trend}
          trendLabel={stat.trendLabel}
          chartData={stat.chartData}
        />
      ))}
    </section>
  );
}