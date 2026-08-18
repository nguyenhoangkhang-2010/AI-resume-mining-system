import type {
  HTMLAttributes,
  ReactNode,
} from "react";

interface DashboardContentProps
  extends HTMLAttributes<HTMLDivElement> {
  stats: ReactNode;
  charts: ReactNode;
  activity: ReactNode;
}

export function DashboardContent({
  stats,
  charts,
  activity,
  className = "",
  ...props
}: DashboardContentProps) {
  return (
    <div
      className={`
        flex
        flex-col
        gap-6
        ${className}
      `}
      {...props}
    >
      {stats}

      <div
        className="
          grid
          gap-6
          xl:grid-cols-[2fr_1fr]
        "
      >
        <div className="space-y-6">
          {charts}
        </div>

        <aside>
          {activity}
        </aside>
      </div>
    </div>
  );
}