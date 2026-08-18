import type { HTMLAttributes, ReactNode } from "react";
import { TriangleAlert } from "lucide-react";

export interface ErrorStateProps
  extends HTMLAttributes<HTMLDivElement> {
  title?: string;
  description?: string;
  icon?: ReactNode;
  action?: ReactNode;
}

export default function ErrorState({
  title = "Something went wrong",
  description = "An unexpected error occurred. Please try again.",
  icon,
  action,
  className = "",
  ...props
}: ErrorStateProps) {
  return (
    <div
      className={`
        flex
        flex-col
        items-center
        justify-center
        rounded-xl
        border
        border-slate-200
        bg-white
        px-8
        py-12
        text-center
        ${className}
      `}
      {...props}
    >
      <div className="mb-4 text-red-500">
        {icon ?? <TriangleAlert size={48} />}
      </div>

      <h2 className="text-lg font-semibold text-slate-900">
        {title}
      </h2>

      <p className="mt-2 max-w-md text-sm text-slate-500">
        {description}
      </p>

      {action && (
        <div className="mt-6">
          {action}
        </div>
      )}
    </div>
  );
}