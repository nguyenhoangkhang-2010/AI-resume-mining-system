import type { HTMLAttributes } from "react";

import { Badge, Card } from "@/components/ui";

import type { RankingResult } from "../types/ranking";


export interface RankingCardProps
  extends HTMLAttributes<HTMLDivElement> {
  ranking: RankingResult;
}


export function RankingCard({
  ranking,
  className = "",
  ...props
}: RankingCardProps) {
  return (
    <Card
      className={`
        flex
        items-center
        gap-5
        p-6
        transition-shadow
        duration-200
        hover:shadow-md
        ${className}
      `}
      {...props}
    >
      <div
        className="
          flex
          h-12
          w-12
          shrink-0
          items-center
          justify-center
          rounded-xl
          bg-slate-100
          text-lg
          font-bold
          text-slate-700
        "
      >
        #{ranking.rank}
      </div>

      <div className="min-w-0 flex-1">
        <h3
          className="
            truncate
            text-lg
            font-semibold
            text-slate-900
          "
        >
          {ranking.candidateName}
        </h3>

        <p
          className="
            mt-1
            text-sm
            text-slate-500
          "
        >
          {ranking.position}
        </p>

        {ranking.summary && (
          <p
            className="
              mt-3
              text-sm
              leading-6
              text-slate-600
            "
          >
            {ranking.summary}
          </p>
        )}
      </div>

      <Badge variant="info">
        {ranking.score}%
      </Badge>
    </Card>
  );
}