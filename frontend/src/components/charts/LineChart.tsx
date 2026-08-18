import {
  CartesianGrid,
  Line,
  LineChart as RechartsLineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export interface LineChartProps<
  T extends Record<string, unknown>,
> {
  data: T[];
  xKey: keyof T;
  yKey: keyof T;
  color?: string;
}

export default function LineChart<
  T extends Record<string, unknown>,
>({
  data,
  xKey,
  yKey,
  color = "#2563eb",
}: LineChartProps<T>) {
  return (
    <ResponsiveContainer
      width="100%"
      height={320}
    >
      <RechartsLineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />

        <XAxis dataKey={String(xKey)} />

        <YAxis />

        <Tooltip />

        <Line
          type="monotone"
          dataKey={String(yKey)}
          stroke={color}
          strokeWidth={3}
          dot={{ r: 4 }}
          activeDot={{ r: 6 }}
        />
      </RechartsLineChart>
    </ResponsiveContainer>
  );
}