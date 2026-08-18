import type { HTMLAttributes } from "react";

export interface GraphLegendItem {
  label: string;
  color: string;
}

export interface GraphLegendProps
  extends HTMLAttributes<HTMLDivElement> {
  items?: GraphLegendItem[];
}

export default function GraphLegend({
  items = [],
  className = "",
  ...props
}: GraphLegendProps) {
  return (
    <div
      className={`flex flex-wrap gap-4 ${className}`}
      {...props}
    >
      {items.map((item) => (
        <div
          key={item.label}
          className="flex items-center gap-2"
        >
          <span
            className="h-3 w-3 rounded-full"
            style={{
              backgroundColor: item.color,
            }}
          />

          <span className="text-sm text-slate-600">
            {item.label}
          </span>
        </div>
      ))}
    </div>
  );
}