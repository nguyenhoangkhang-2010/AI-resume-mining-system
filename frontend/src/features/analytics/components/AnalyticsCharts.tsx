import {
  AreaChart,
  BarChart,
  DonutChart,
  LineChart,
  RadarChart,
} from "@/components/charts";

import type {
  AnalyticsChart,
} from "../types/analytics";


interface AnalyticsChartsProps {
  charts: AnalyticsChart[];
}


export function AnalyticsCharts({
  charts,
}: AnalyticsChartsProps) {
  return (
    <section
      className="
        grid
        gap-6
        lg:grid-cols-2
      "
    >
      {charts.map((chart) => {
        switch (chart.type) {
          case "line":
            return (
              <LineChart
                key={chart.id}
                data={chart.data}
                xKey={chart.xKey ?? ""}
                yKey={chart.yKey ?? ""}
                color={chart.color}
              />
            );

          case "area":
            return (
              <AreaChart
                key={chart.id}
                data={chart.data}
                xKey={chart.xKey ?? ""}
                yKey={chart.yKey ?? ""}
                color={chart.color}
              />
            );

          case "bar":
            return (
              <BarChart
                key={chart.id}
                data={chart.data}
                xKey={chart.xKey ?? ""}
                yKey={chart.yKey ?? ""}
                color={chart.color}
              />
            );

          case "donut":
            return (
                <DonutChart
                key={chart.id}
                data={
                    chart.data as {
                    name: string;
                    value: number;
                    }[]
                }
                />
            );
          case "radar":
            return (
              <RadarChart
                key={chart.id}
                data={chart.data}
                nameKey={chart.nameKey ?? ""}
                valueKey={chart.valueKey ?? ""}
                color={chart.color}
              />
            );

          default:
            return null;
        }
      })}
    </section>
  );
}