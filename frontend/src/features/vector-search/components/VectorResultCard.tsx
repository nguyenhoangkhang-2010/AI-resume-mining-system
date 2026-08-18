import type { HTMLAttributes } from "react";

import { Badge, Card } from "@/components/ui";

import type { VectorSearchResult } from "../types/vectorSearch";


export interface VectorResultCardProps
  extends HTMLAttributes<HTMLDivElement> {
  result: VectorSearchResult;
}


export function VectorResultCard({
  result,
  className = "",
  ...props
}: VectorResultCardProps) {
  return (
    <Card
      className={`
        flex
        flex-col
        gap-4
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
            {result.title}
          </h3>

          <p
            className="
              mt-1
              text-sm
              text-slate-500
            "
          >
            {result.type}
          </p>
        </div>

        <Badge variant="info">
          {result.similarity}%
        </Badge>
      </div>


      <p
        className="
          text-sm
          leading-6
          text-slate-600
        "
      >
        {result.description}
      </p>


      <div
        className="
          flex
          flex-wrap
          gap-2
        "
      >
        {result.tags.map((tag) => (
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