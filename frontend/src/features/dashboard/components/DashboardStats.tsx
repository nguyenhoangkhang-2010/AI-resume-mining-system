import {
  BriefcaseBusiness,
  Database,
  FileUser,
  Target,
} from "lucide-react";

import StatCard from "@/components/charts/StatCard";

import type { DashboardStat } from "../types/dashboard";

interface DashboardStatsProps {
  stats: DashboardStat[];
}

const iconMap = {
  candidates: <FileUser size={20} />,
  jobs: <BriefcaseBusiness size={20} />,
  matching: <Target size={20} />,
  knowledge: <Database size={20} />,
};

export function DashboardStats({
  stats,
}: DashboardStatsProps) {
  return (
    <section
      className="
        grid
        gap-6
        md:grid-cols-2
        xl:grid-cols-4
      "
    >
      {stats.map((stat) => (
        <StatCard
          key={stat.id}
          title={stat.title}
          value={stat.value}
          trend={stat.trend}
          trendLabel={stat.trendLabel}
          chartData={stat.chartData}
          color={stat.color}
          icon={
            iconMap[
              stat.id as keyof typeof iconMap
            ]
          }
        />
      ))}
    </section>
  );
}