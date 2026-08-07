import type {
  HTMLAttributes,
  ReactNode,
} from "react";

import {
  cn,
} from "@/lib/utils";

export interface EmptyStateProps
  extends HTMLAttributes<HTMLDivElement> {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}

export default function EmptyState({
  icon,
  title,
  description,
  action,
  className,
  ...props
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        `
        flex
        flex-col
        items-center
        justify-center
        rounded-xl
        border
        border-dashed
        border-slate-300
        bg-white
        px-8
        py-12
        text-center
        `,
        className,
      )}
      {...props}
    >
      {icon && (
        <div className="mb-4 text-slate-400">
          {icon}
        </div>
      )}


      <h3
        className="
          text-lg
          font-semibold
          text-slate-900
        "
      >
        {title}
      </h3>

      {description && (
        <p
          className="
            mt-2
            max-w-md
            text-sm
            leading-6
            text-slate-500
          "
        >
          {description}
        </p>
      )}

      {action && (
        <div className="mt-6">
          {action}
        </div>
      )}
    </div>
  );
}