import type { HTMLAttributes, ReactNode } from "react";

export interface GraphEdgeProps
  extends HTMLAttributes<HTMLDivElement> {
  source: ReactNode;
  target: ReactNode;
  label?: ReactNode;
}

export default function GraphEdge({
  source,
  target,
  label,
  className = "",
  ...props
}: GraphEdgeProps) {
  return (
    <div
      className={`
        flex
        items-center
        gap-3
        text-sm
        text-slate-600
        ${className}
      `}
      {...props}
    >
      <span>{source}</span>

      <span className="text-slate-400">→</span>

      <span>{target}</span>

      {label && (
        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs">
          {label}
        </span>
      )}
    </div>
  );
}