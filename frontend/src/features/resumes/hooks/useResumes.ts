import {
  useState,
} from "react";

import {
  useMutation,
} from "@tanstack/react-query";


import {
  uploadResume as uploadResumeApi,
} from "@/services/resume.service";


import type {
  Resume,
} from "../types/resume";


export function useResumes() {

  const [resumes, setResumes] =
    useState<Resume[]>([]);


  const mutation =
    useMutation({
      mutationFn:
        (file: File) =>
          uploadResumeApi(file),
      onSuccess:
        (data, file) => {
          const newResume: Resume = {
            id:
              data.id ??
              crypto.randomUUID(),
            name:
              file.name,
            fileName:
              file.name,
            status:
              "uploaded",
            createdAt:
              new Date()
              .toISOString(),
          };
          setResumes(
            current => [
              ...current,
              newResume,
            ],
          );
        },
    });
  return {
    resumes,
    uploadResume:
      mutation.mutateAsync,
    loading:
      mutation.isPending,
    error:
      mutation.error,
  };
}