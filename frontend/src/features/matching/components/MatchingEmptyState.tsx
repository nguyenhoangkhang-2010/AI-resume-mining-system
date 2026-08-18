import { EmptyState } from "@/components/ui";


export function MatchingEmptyState() {
  return (
    <EmptyState
      title="No matching results"
      description="Matching results will appear here once candidates and job requirements are available."
    />
  );
}