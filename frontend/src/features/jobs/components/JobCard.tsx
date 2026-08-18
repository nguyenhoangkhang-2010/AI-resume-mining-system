import type { HTMLAttributes } from "react";

import type { Job } from "../types/job";

interface JobCardProps
  extends HTMLAttributes<HTMLDivElement> {
  job: Job;
}

export function JobCard({
  job,
  className = "",
  ...props
}: JobCardProps) {
  return (
    <article
      className={`
        rounded-2xl
        border
        border-slate-200
        bg-white
        p-6
        shadow-sm
        transition
        hover:shadow-md
        ${className}
      `}
      {...props}
    >
      <div
        className="
          flex
          flex-col
          gap-3
        "
      >
        <div>
          <h3
            className="
              text-lg
              font-semibold
              text-slate-900
            "
          >
            {job.title}
          </h3>

          {job.company && (
            <p
              className="
                mt-1
                text-sm
                text-slate-500
              "
            >
              {job.company}
            </p>
          )}
        </div>

        {job.location && (
          <p
            className="
              text-sm
              text-slate-600
            "
          >
            {job.location}
          </p>
        )}

        {job.description && (
          <p
            className="
              line-clamp-3
              text-sm
              text-slate-600
            "
          >
            {job.description}
          </p>
        )}

        {job.skills &&
          job.skills.length > 0 && (
            <div
              className="
                flex
                flex-wrap
                gap-2
              "
            >
              {job.skills.map(
                (skill) => (
                  <span
                    key={skill}
                    className="
                      rounded-full
                      bg-slate-100
                      px-3
                      py-1
                      text-xs
                      text-slate-700
                    "
                  >
                    {skill}
                  </span>
                ),
              )}
            </div>
          )}
      </div>
    </article>
  );
}