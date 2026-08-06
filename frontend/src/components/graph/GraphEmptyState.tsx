import type { HTMLAttributes, ReactNode } from "react";

export interface GraphEmptyStateProps
  extends HTMLAttributes<HTMLDivElement> {
  icon?: ReactNode;
  heading: ReactNode;
  description?: ReactNode;
}

export default function GraphEmptyState({
  icon,
  title,
  description,
  className = "",
  ...props
}: GraphEmptyStateProps) {
  return (
    <div
      className={`
        flex
        h-full
        flex-col
        items-center
        justify-center
        gap-3
        text-center
        ${className}
      `}
      {...props}
    >
      {icon && (
        <div className="rounded-full bg-slate-100 p-4 text-slate-500">
          {icon}
        </div>
      )}

      <h3 className="text-lg font-semibold text-slate-900">
        {title}
      </h3>

      {description && (
        <p className="max-w-md text-sm text-slate-500">
          {description}
        </p>
      )}
    </div>
  );
}