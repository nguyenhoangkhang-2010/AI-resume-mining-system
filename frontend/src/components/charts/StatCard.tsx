import type { HTMLAttributes, ReactNode } from "react";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  YAxis,
} from "recharts";

export interface StatCardProps
  extends HTMLAttributes<HTMLDivElement> {
  title: string;

  value: string | number;

  trend: number;

  trendLabel?: string;

  icon?: ReactNode;

  chartData: {
    value: number;
  }[];

  color?: string;
}

export default function StatCard({
  title,
  value,
  trend,
  trendLabel = "from last month",
  icon,
  chartData,
  color = "#2563eb",
  className = "",
  ...props
}: StatCardProps) {
  const positive = trend >= 0;

  return (
    <div
      className={`
        rounded-2xl
        border
        border-slate-200
        bg-white
        p-6
        shadow-sm
        transition-all
        duration-200
        hover:shadow-lg
        ${className}
      `}
      {...props}
    >
      {/* Header */}

      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-400">
            {title}
          </p>

          <h2 className="mt-4 text-5xl font-bold tracking-tight text-slate-900">
            {value}
          </h2>

          <div
            className={`mt-3 flex items-center gap-2 text-sm font-medium ${
              positive
                ? "text-emerald-600"
                : "text-red-500"
            }`}
          >
            <span>
              {positive ? "▲" : "▼"}
            </span>

            <span>
              {Math.abs(trend)}%
            </span>

            <span className="text-slate-500">
              {trendLabel}
            </span>
          </div>
        </div>

        <div className="rounded-xl bg-slate-100 p-3">
          {icon}
        </div>
      </div>

      {/* Chart */}

      <div className="mt-8 h-32">
        <ResponsiveContainer
          width="100%"
          height="100%"
        >
          <AreaChart data={chartData}>
            <defs>
              <linearGradient
                id={`gradient-${title}`}
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >
                <stop
                  offset="5%"
                  stopColor={color}
                  stopOpacity={0.35}
                />

                <stop
                  offset="95%"
                  stopColor={color}
                  stopOpacity={0}
                />
              </linearGradient>
            </defs>

            <CartesianGrid
              strokeDasharray="3 3"
              vertical={false}
            />

            <YAxis
              axisLine={false}
              tickLine={false}
              width={35}
              tick={{
                fontSize: 10,
              }}
            />

            <Tooltip />

            <Area
              dataKey="value"
              stroke={color}
              strokeWidth={3}
              fill={`url(#gradient-${title})`}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}