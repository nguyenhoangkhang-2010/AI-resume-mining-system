import type { HTMLAttributes } from "react";

import { RecommendationCard } from "./RecommendationCard";
import type { Recommendation } from "../types/recommendation";


export interface RecommendationsListProps
  extends HTMLAttributes<HTMLDivElement> {
  recommendations: Recommendation[];
}


export function RecommendationsList({
  recommendations,
  className = "",
  ...props
}: RecommendationsListProps) {
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
      {recommendations.map((recommendation) => (
        <RecommendationCard
          key={recommendation.id}
          recommendation={recommendation}
        />
      ))}
    </div>
  );
}