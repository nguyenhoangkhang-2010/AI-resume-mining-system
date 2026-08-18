import type { HTMLAttributes } from "react";

import type { Job } from "../types/job";

import { JobCard } from "./JobCard";

interface JobsListProps
  extends HTMLAttributes<HTMLDivElement> {
  jobs: Job[];
}

export function JobsList({
  jobs,
  className = "",
  ...props
}: JobsListProps) {
  return (
    <div
      className={`
        grid
        gap-6
        md:grid-cols-2
        ${className}
      `}
      {...props}
    >
      {jobs.map((job) => (
        <JobCard
          key={job.id}
          job={job}
        />
      ))}
    </div>
  );
}