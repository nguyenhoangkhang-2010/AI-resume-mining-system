import type { HTMLAttributes } from "react";

import { MatchCard } from "./MatchCard";
import type { MatchResult } from "../types/matching";


export interface MatchingResultListProps
  extends HTMLAttributes<HTMLDivElement> {
  matches: MatchResult[];
}


export function MatchingResultList({
  matches,
  className = "",
  ...props
}: MatchingResultListProps) {
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
      {matches.map((match) => (
        <MatchCard
          key={match.id}
          match={match}
        />
      ))}
    </div>
  );
}