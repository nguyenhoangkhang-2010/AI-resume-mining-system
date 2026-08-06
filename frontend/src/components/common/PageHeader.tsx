import type { HTMLAttributes, ReactNode } from "react";

export interface PageHeaderProps
  extends HTMLAttributes<HTMLDivElement> {
  title: string;
  description?: string;
  actions?: ReactNode;
}

export default function PageHeader({
  title,
  description,
  actions,
  className = "",
  ...props
}: PageHeaderProps) {
  return (
    <div
      className={`
        flex
        flex-col
        gap-4
        md:flex-row
        md:items-center
        md:justify-between
        ${className}
      `}
      {...props}
    >
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">
          {title}
        </h1>

        {description && (
          <p className="mt-2 text-sm text-slate-500">
            {description}
          </p>
        )}
      </div>

      {actions && (
        <div className="flex items-center gap-3">
          {actions}
        </div>
      )}
    </div>
  );
}