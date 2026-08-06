import type { HTMLAttributes, ReactNode } from "react";

import Card from "@/components/ui/Card";

export interface ChartContainerProps
  extends HTMLAttributes<HTMLDivElement> {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}

export default function ChartContainer({
  title,
  subtitle,
  actions,
  children,
  className = "",
  ...props
}: ChartContainerProps) {
  return (
    <Card
      className={`flex h-full flex-col p-6 ${className}`}
      {...props}
    >
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">
            {title}
          </h3>

          {subtitle && (
            <p className="mt-1 text-sm text-slate-500">
              {subtitle}
            </p>
          )}
        </div>

        {actions && (
          <div className="flex items-center gap-2">
            {actions}
          </div>
        )}
      </div>

      <div className="min-h-[300px] flex-1">
        {children}
      </div>
    </Card>
  );
}