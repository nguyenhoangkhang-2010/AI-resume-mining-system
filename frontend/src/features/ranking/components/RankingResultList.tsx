import type { HTMLAttributes } from "react";

import { RankingCard } from "./RankingCard";
import type { RankingResult } from "../types/ranking";


export interface RankingResultListProps
  extends HTMLAttributes<HTMLDivElement> {
  rankings: RankingResult[];
}


export function RankingResultList({
  rankings,
  className = "",
  ...props
}: RankingResultListProps) {
  return (
    <div
      className={`
        flex
        flex-col
        gap-4
        ${className}
      `}
      {...props}
    >
      {rankings.map((ranking) => (
        <RankingCard
          key={ranking.id}
          ranking={ranking}
        />
      ))}
    </div>
  );
}