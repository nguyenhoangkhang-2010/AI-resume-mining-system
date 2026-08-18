import type { HTMLAttributes } from "react";

import { Badge, Card } from "@/components/ui";

import type { Recommendation } from "../types/recommendation";


export interface RecommendationCardProps
  extends HTMLAttributes<HTMLDivElement> {
  recommendation: Recommendation;
}


export function RecommendationCard({
  recommendation,
  className = "",
  ...props
}: RecommendationCardProps) {
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
              text-lg
              font-semibold
              text-slate-900
            "
          >
            {recommendation.title}
          </h3>

          <p
            className="
              mt-1
              text-sm
              text-slate-500
            "
          >
            {recommendation.category}
          </p>
        </div>

        <Badge variant="info">
          {recommendation.score}%
        </Badge>
      </div>

      <p
        className="
          text-sm
          leading-6
          text-slate-600
        "
      >
        {recommendation.description}
      </p>

      <div
        className="
          flex
          flex-wrap
          gap-2
        "
      >
        {recommendation.tags.map((tag) => (
          <Badge
            key={tag}
            variant="default"
          >
            {tag}
          </Badge>
        ))}
      </div>
    </Card>
  );
}