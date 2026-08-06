import { JobsEmptyState } from "./JobsEmptyState";
import { JobsFilter } from "./JobsFilter";
import { JobsHeader } from "./JobsHeader";
import { JobsList } from "./JobsList";
import { JobsSearch } from "./JobsSearch";

import { useJobs } from "../hooks/useJobs";

import { useState } from "react";


export function JobsView() {
  const {
    loading,
    error,
    jobs,
  } = useJobs();

  const [query, setQuery] =
    useState("");

  const [filter, setFilter] =
    useState("");

  if (loading) {
    return (
      <div>
        Loading jobs...
      </div>
    );
  }

  if (error) {
    return (
      <div>
        Failed to load jobs
      </div>
    );
  }

  return (
    <section
      className="
        flex
        flex-col
        gap-6
      "
    >
      <JobsHeader />

      <div
        className="
          flex
          flex-col
          gap-4
        "
      >
        <JobsSearch
          value={query}
          onChange={setQuery}
          onSearch={() => {}}
        />

        <JobsFilter
          value={filter}
          onChange={setFilter}
        />
      </div>


      {jobs.length === 0 ? (
        <JobsEmptyState />
      ) : (
        <JobsList
          jobs={jobs}
        />
      )}
    </section>
  );
}