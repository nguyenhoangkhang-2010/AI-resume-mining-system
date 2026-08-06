import type { HTMLAttributes, ReactNode } from "react";

export interface GraphErrorStateProps
  extends HTMLAttributes<HTMLDivElement> {
  heading?: ReactNode;
  description?: ReactNode;
  action?: ReactNode;
}

export default function GraphErrorState({
  heading = "Unable to load graph",
  description,
  action,
  className = "",
  ...props
}: GraphErrorStateProps) {
  return (
    <div
      className={`flex h-full min-h-[320px] flex-col items-center justify-center gap-4 text-center ${className}`}
      {...props}
    >
      <div className="rounded-full bg-red-50 p-4">
        <span className="text-2xl">⚠️</span>
      </div>

      <div>
        <h3 className="text-lg font-semibold text-slate-900">
          {heading}
        </h3>

        {description && (
          <p className="mt-2 max-w-md text-sm text-slate-500">
            {description}
          </p>
        )}
      </div>

      {action}
    </div>
  );
}