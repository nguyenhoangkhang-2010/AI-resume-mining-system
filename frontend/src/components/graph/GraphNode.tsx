import type { HTMLAttributes, ReactNode } from "react";

export interface GraphNodeProps
  extends HTMLAttributes<HTMLDivElement> {
  icon?: ReactNode;
  heading: ReactNode;
  subtitle?: ReactNode;
  selected?: boolean;
}

export default function GraphNode({
  icon,
  title,
  subtitle,
  selected = false,
  className = "",
  ...props
}: GraphNodeProps) {
  return (
    <div
      className={`
        flex
        items-center
        gap-3
        rounded-xl
        border
        bg-white
        p-4
        shadow-sm
        transition-all
        ${
          selected
            ? "border-blue-500 ring-2 ring-blue-100"
            : "border-slate-200"
        }
        ${className}
      `}
      {...props}
    >
      {icon && (
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-100">
          {icon}
        </div>
      )}

      <div className="min-w-0">
        <div className="truncate font-semibold text-slate-900">
          {title}
        </div>

        {subtitle && (
          <div className="truncate text-sm text-slate-500">
            {subtitle}
          </div>
        )}
      </div>
    </div>
  );
}