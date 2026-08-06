import type { HTMLAttributes } from "react";

interface JobsHeaderProps
  extends HTMLAttributes<HTMLDivElement> {
  title?: string;
  description?: string;
}

export function JobsHeader({
  title = "Jobs",
  description = "Explore and manage job opportunities",
  className = "",
  ...props
}: JobsHeaderProps) {
  return (
    <header
      className={`
        flex
        flex-col
        gap-2
        ${className}
      `}
      {...props}
    >
      <h1
        className="
          text-3xl
          font-bold
          tracking-tight
          text-slate-900
        "
      >
        {title}
      </h1>

      <p
        className="
          text-sm
          text-slate-500
        "
      >
        {description}
      </p>
    </header>
  );
}