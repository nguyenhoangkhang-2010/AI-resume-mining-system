import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

export interface DonutChartData {
  name: string;
  value: number;
  color?: string;
}

export interface DonutChartProps {
  data: DonutChartData[];
  innerRadius?: number;
  outerRadius?: number;
}

const DEFAULT_COLORS = [
  "#2563eb",
  "#14b8a6",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#06b6d4",
  "#84cc16",
];

export default function DonutChart({
  data,
  innerRadius = 65,
  outerRadius = 95,
}: DonutChartProps) {
  return (
    <ResponsiveContainer width="100%" height={320}>
      <PieChart>
        <Tooltip />

        <Legend />

        <Pie
          data={data}
          dataKey="value"
          nameKey="name"
          innerRadius={innerRadius}
          outerRadius={outerRadius}
          paddingAngle={3}
        >
          {data.map((entry, index) => (
            <Cell
              key={entry.name}
              fill={
                entry.color ??
                DEFAULT_COLORS[index % DEFAULT_COLORS.length]
              }
            />
          ))}
        </Pie>
      </PieChart>
    </ResponsiveContainer>
  );
}