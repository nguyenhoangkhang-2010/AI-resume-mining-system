import type { HTMLAttributes } from "react";

import { Badge, Card } from "@/components/ui";

import type { MatchResult } from "../types/matching";


export interface MatchCardProps
  extends HTMLAttributes<HTMLDivElement> {
  match: MatchResult;
}


export function MatchCard({
  match,
  className = "",
  ...props
}: MatchCardProps) {
  return (
    <Card
      className={`
        flex
        flex-col
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
          items-start
          justify-between
          gap-4
        "
      >
        <div className="min-w-0">
          <h3
            className="
              truncate
              text-lg
              font-semibold
              text-slate-900
            "
          >
            {match.candidateName}
          </h3>

          <p
            className="
              mt-1
              text-sm
              text-slate-500
            "
          >
            {match.position}
          </p>
        </div>

        <Badge>
          {match.score}%
        </Badge>
      </div>

      <div
        className="
          flex
          flex-wrap
          gap-2
        "
      >
        {match.skills.map((skill) => (
          <Badge
            key={skill}
            variant="default"
          >
            {skill}
          </Badge>
        ))}
      </div>

      {match.summary && (
        <p
          className="
            text-sm
            leading-6
            text-slate-600
          "
        >
          {match.summary}
        </p>
      )}
    </Card>
  );
}