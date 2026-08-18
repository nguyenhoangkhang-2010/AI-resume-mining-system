import {
  Area,
  AreaChart as RechartsAreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export interface AreaChartProps<
  T extends Record<string, unknown>,
> {
  data: T[];
  xKey: keyof T;
  yKey: keyof T;
  color?: string;
}

export default function AreaChart<
  T extends Record<string, unknown>,
>({
  data,
  xKey,
  yKey,
  color = "#2563eb",
}: AreaChartProps<T>) {
  return (
    <ResponsiveContainer
      width="100%"
      height={320}
    >
      <RechartsAreaChart data={data}>
        <defs>
          <linearGradient
            id="areaGradient"
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

        <CartesianGrid strokeDasharray="3 3" />

        <XAxis dataKey={String(xKey)} />

        <YAxis />

        <Tooltip />

        <Area
          type="monotone"
          dataKey={String(yKey)}
          stroke={color}
          strokeWidth={2}
          fill="url(#areaGradient)"
        />
      </RechartsAreaChart>
    </ResponsiveContainer>
  );
}