import type { HTMLAttributes } from "react";

interface JobsEmptyStateProps
  extends HTMLAttributes<HTMLDivElement> {
  title?: string;
  description?: string;
}

export function JobsEmptyState({
  title = "No jobs found",
  description = "There are currently no available job opportunities.",
  className = "",
  ...props
}: JobsEmptyStateProps) {
  return (
    <div
      className={`
        flex
        min-h-60
        flex-col
        items-center
        justify-center
        rounded-2xl
        border
        border-dashed
        border-slate-200
        bg-white
        p-6
        text-center
        ${className}
      `}
      {...props}
    >
      <h3
        className="
          text-lg
          font-semibold
          text-slate-900
        "
      >
        {title}
      </h3>

      <p
        className="
          mt-2
          max-w-md
          text-sm
          text-slate-500
        "
      >
        {description}
      </p>
    </div>
  );
}