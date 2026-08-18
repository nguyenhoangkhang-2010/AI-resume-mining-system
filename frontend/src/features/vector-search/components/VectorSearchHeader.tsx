import type { HTMLAttributes } from "react";

import { PageHeader } from "@/components/common";


export interface VectorSearchHeaderProps
  extends HTMLAttributes<HTMLDivElement> {}


export function VectorSearchHeader({
  className = "",
  ...props
}: VectorSearchHeaderProps) {
  return (
    <PageHeader
      title="Vector Search"
      description="Search and retrieve semantically similar candidates, resumes, and knowledge entities using vector-based similarity."
      className={className}
      {...props}
    />
  );
}