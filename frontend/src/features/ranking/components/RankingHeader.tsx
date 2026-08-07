import type { HTMLAttributes } from "react";

import { PageHeader } from "@/components/common";


export interface RankingHeaderProps
  extends HTMLAttributes<HTMLDivElement> {}


export function RankingHeader({
  className = "",
  ...props
}: RankingHeaderProps) {
  return (
    <PageHeader
      title="Candidate Ranking"
      description="Rank candidates based on their matching relevance and evaluation results."
      className={className}
      {...props}
    />
  );
}