import type { HTMLAttributes } from "react";

import { PageHeader } from "@/components/common";


export interface RecommendationsHeaderProps
  extends HTMLAttributes<HTMLDivElement> {}


export function RecommendationsHeader({
  className = "",
  ...props
}: RecommendationsHeaderProps) {
  return (
    <PageHeader
      title="Recommendations"
      description="Discover relevant career opportunities and candidate recommendations based on your matching results."
      className={className}
      {...props}
    />
  );
}