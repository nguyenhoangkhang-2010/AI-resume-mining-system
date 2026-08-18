import {
  Bar,
  BarChart as RechartsBarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export interface BarChartProps<T extends Record<string, unknown>> {
  data: T[];
  xKey: keyof T;
  yKey: keyof T;
  color?: string;
}

export default function BarChart<
  T extends Record<string, unknown>
>({
  data,
  xKey,
  yKey,
  color = "#2563eb",
}: BarChartProps<T>) {
  return (
    <ResponsiveContainer
      width="100%"
      height={320}
    >
      <RechartsBarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />

        <XAxis dataKey={String(xKey)} />

        <YAxis />

        <Tooltip />

        <Bar
          dataKey={String(yKey)}
          fill={color}
          radius={[6, 6, 0, 0]}
        />
      </RechartsBarChart>
    </ResponsiveContainer>
  );
}