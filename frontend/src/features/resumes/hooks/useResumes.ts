import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  getResumeStatus,
  uploadResume,
} from "@/services/resume.service";

import type {
  Resume,
} from "../types/resume";

import type {
  UploadResumeResponse,
} from "@/services/resume.service";

import {
  useState,
} from "react";

function mapResume(
  data: UploadResumeResponse,
): Resume {
  return {
    id: data.id,
    name: data.filename,
    fileName: data.filename,
    status: data.upload_status,
    createdAt: data.created_at,
  };
}

export function useResumes() {
  const queryClient = useQueryClient();

  const [
    uploadedResume,
    setUploadedResume,
  ] = useState<Resume | null>(null);

  const mutation = useMutation({
    mutationFn: uploadResume,

    onSuccess: (data) => {
      setUploadedResume(
        mapResume(data),
      );

      queryClient.invalidateQueries({
        queryKey: ["resumes"],
      });
    },
  });

  const statusQuery = useQuery({
    queryKey: [
      "resume-status",
      uploadedResume?.id,
    ],

    queryFn: () =>
      getResumeStatus(
        uploadedResume!.id,
      ),

    enabled:
      Boolean(uploadedResume?.id),

    refetchInterval: (query) => {
      const status =
        query.state.data?.status;

      if (
        status === "processed" ||
        status === "failed"
      ) {
        return false;
      }

      return 2000;
    },
  });

  const resume: Resume | null =
    uploadedResume
      ? {
          ...uploadedResume,
          status:
            statusQuery.data?.status ??
            uploadedResume.status,
        }
      : null;

  return {
    resumes: resume
      ? [resume]
      : [],

    uploadResume:
      mutation.mutateAsync,

    loading:
      mutation.isPending,

    error:
      mutation.error ??
      statusQuery.error,

    statusLoading:
      statusQuery.isLoading,

    refetchStatus:
      statusQuery.refetch,
  };
}