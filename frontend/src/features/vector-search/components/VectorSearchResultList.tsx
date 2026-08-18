import type { HTMLAttributes } from "react";

import { VectorResultCard } from "./VectorResultCard";

import type { VectorSearchResult } from "../types/vectorSearch";


export interface VectorSearchResultListProps
  extends Omit<HTMLAttributes<HTMLDivElement>, "results"> {
  results: VectorSearchResult[];
}


export function VectorSearchResultList({
  results,
  className = "",
  ...props
}: VectorSearchResultListProps) {
  return (
    <div
      className={`
        grid
        grid-cols-1
        gap-4
        lg:grid-cols-2
        ${className}
      `}
      {...props}
    >
      {results.map((result) => (
        <VectorResultCard
          key={result.id}
          result={result}
        />
      ))}
    </div>
  );
}