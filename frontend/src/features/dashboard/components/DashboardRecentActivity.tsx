import type { DashboardActivity } from "../types/dashboard";

interface DashboardRecentActivityProps {
  activities: DashboardActivity[];
}

export function DashboardRecentActivity({
  activities,
}: DashboardRecentActivityProps) {
  return (
    <section
      className="
        rounded-2xl
        border
        border-slate-200
        bg-white
        p-6
        shadow-sm
      "
    >
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-slate-900">
          Recent Activity
        </h2>

        <p className="mt-1 text-sm text-slate-500">
          Latest platform updates
        </p>
      </div>

      <div className="space-y-5">
        {activities.map((activity) => (
          <article
            key={activity.id}
            className="flex items-start gap-4"
          >
            <span
              className="
                mt-1
                h-3
                w-3
                rounded-full
                bg-blue-600
              "
            />

            <div className="flex-1">
              <h3 className="font-medium text-slate-900">
                {activity.title}
              </h3>

              <p className="mt-1 text-sm text-slate-500">
                {activity.description}
              </p>

              <time className="mt-2 block text-xs text-slate-400">
                {activity.timestamp}
              </time>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}