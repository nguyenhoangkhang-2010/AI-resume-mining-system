import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart as RechartsRadarChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

export interface RadarChartProps<
  T extends Record<string, unknown>,
> {
  data: T[];
  nameKey: keyof T;
  valueKey: keyof T;
  color?: string;
}

export default function RadarChart<
  T extends Record<string, unknown>,
>({
  data,
  nameKey,
  valueKey,
  color = "#2563eb",
}: RadarChartProps<T>) {
  return (
    <ResponsiveContainer
      width="100%"
      height={320}
    >
      <RechartsRadarChart data={data}>
        <PolarGrid />

        <PolarAngleAxis
          dataKey={String(nameKey)}
        />

        <PolarRadiusAxis />

        <Tooltip />

        <Radar
          dataKey={String(valueKey)}
          stroke={color}
          fill={color}
          fillOpacity={0.35}
        />
      </RechartsRadarChart>
    </ResponsiveContainer>
  );
}