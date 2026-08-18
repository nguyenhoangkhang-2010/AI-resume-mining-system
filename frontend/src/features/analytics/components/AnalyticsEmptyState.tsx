import { EmptyState } from "@/components/ui";


export function AnalyticsEmptyState() {
  return (
    <EmptyState
      title="No analytics data"
      description="
        Analytics data will appear here
        once the system has enough activity.
      "
    />
  );
}