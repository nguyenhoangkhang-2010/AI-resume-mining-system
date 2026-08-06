import {
  AreaChart,
  BarChart,
  ChartContainer,
  DonutChart,
  LineChart,
  RadarChart,
} from "@/components/charts";

import type { DashboardChart } from "../types/dashboard";

interface DashboardChartsProps {
  charts: DashboardChart[];
}

export function DashboardCharts({
  charts,
}: DashboardChartsProps) {
  return (
    <section
      className="
        grid
        gap-6
        lg:grid-cols-2
      "
    >
      {charts.map((chart) => (
        <ChartContainer
          key={chart.id}
          title={chart.title}
          subtitle={chart.subtitle}
        >
          {renderChart(chart)}
        </ChartContainer>
      ))}
    </section>
  );
}

function renderChart(chart: DashboardChart) {
  switch (chart.type) {
    case "line":
      return (
        <LineChart<Record<string, unknown>>
          data={chart.data}
          xKey={chart.xKey}
          yKey={chart.yKey}
          color={chart.color}
        />
      );

    case "area":
      return (
        <AreaChart<Record<string, unknown>>
          data={chart.data}
          xKey={chart.xKey}
          yKey={chart.yKey}
          color={chart.color}
        />
      );

    case "bar":
      return (
        <BarChart<Record<string, unknown>>
          data={chart.data}
          xKey={chart.xKey}
          yKey={chart.yKey}
          color={chart.color}
        />
      );

    case "donut":
      return (
        <DonutChart
          data={chart.data}
        />
      );

    case "radar":
      return (
        <RadarChart<Record<string, unknown>>
          data={chart.data}
          nameKey={chart.nameKey}
          valueKey={chart.valueKey}
          color={chart.color}
        />
      );
  }
}