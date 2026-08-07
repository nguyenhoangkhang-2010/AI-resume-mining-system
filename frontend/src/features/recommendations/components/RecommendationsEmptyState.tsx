import { EmptyState } from "@/components/ui";


export function RecommendationsEmptyState() {
  return (
    <EmptyState
      title="No recommendations"
      description="Recommendations will appear here once matching and ranking results are available."
    />
  );
}