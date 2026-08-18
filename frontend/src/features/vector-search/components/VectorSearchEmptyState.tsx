import { EmptyState } from "@/components/ui";


export function VectorSearchEmptyState() {
  return (
    <EmptyState
      title="No search results"
      description="Semantic search results will appear here after running a vector query."
    />
  );
}