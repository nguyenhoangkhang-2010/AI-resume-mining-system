import { useMemo, useState } from "react";

import type {
  Resume,
} from "../types/resume";


interface UseResumesResult {
  resumes: Resume[];

  loading: boolean;

  error: Error | null;

  uploadResume: (
    file: File,
  ) => void;
}


export function useResumes(): UseResumesResult {
  const [resumes, setResumes] =
    useState<Resume[]>([]);


  const [loading, setLoading] =
    useState(false);


  const [error, setError] =
    useState<Error | null>(null);


  function uploadResume(
    file: File,
  ) {
    try {
      setLoading(true);
      setError(null);


      const newResume: Resume = {
        id: crypto.randomUUID(),

        name: file.name,

        fileName: file.name,

        status: "uploaded",

        createdAt:
          new Date()
            .toISOString(),
      };


      setResumes((current) => [
        ...current,
        newResume,
      ]);

    } catch (err) {
      setError(
        err instanceof Error
          ? err
          : new Error(
              "Failed to upload resume",
            ),
      );
    } finally {
      setLoading(false);
    }
  }


  return useMemo(
    () => ({
      resumes,

      loading,

      error,

      uploadResume,
    }),
    [
      resumes,
      loading,
      error,
    ],
  );
}