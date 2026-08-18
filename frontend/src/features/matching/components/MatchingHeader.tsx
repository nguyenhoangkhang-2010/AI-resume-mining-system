import type { HTMLAttributes } from "react";

import { PageHeader } from "@/components/common";


export interface MatchingHeaderProps
  extends HTMLAttributes<HTMLDivElement> {}


export function MatchingHeader({
  className = "",
  ...props
}: MatchingHeaderProps) {
  return (
    <PageHeader
      title="Candidate Matching"
      description="Find the most relevant candidates for your job requirements."
      className={className}
      {...props}
    />
  );
}
