import {
  useState,
} from "react";

import {
  useMutation,
} from "@tanstack/react-query";


import {
  createJob,
} from "@/services/job.service";


import type {
  Job,
} from "../types/job";


import type {
  CreateJobPayload,
} from "@/services/job.service";


export function useJobs(){

  const [jobs,setJobs] =
    useState<Job[]>([]);
  const mutation =
    useMutation({
      mutationFn:
        createJob,
      onSuccess:
        (data)=>{
          setJobs(
            current=>[
              ...current,
              data,
            ],
          );
        },
    });
  return {
    jobs,
    createJob:
      mutation.mutateAsync,
    loading:
      mutation.isPending,
    error:
      mutation.error,
  };
}