import { EmptyState } from "@/components/ui";


export function RankingEmptyState() {
  return (
    <EmptyState
      title="No ranking results"
      description="Ranking results will appear here once candidate evaluation data is available."
    />
  );
}