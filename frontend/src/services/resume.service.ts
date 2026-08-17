import api from "./api";

export type BackendResumeStatus =
  | "pending"
  | "processing"
  | "processed"
  | "failed";

export interface UploadResumeResponse {
  id: string;
  filename: string;
  upload_status: BackendResumeStatus;
  created_at: string;
}

export interface ResumeStatusResponse {
  resume_id: string;
  status: BackendResumeStatus;
}

export async function uploadResume(
  file: File,
): Promise<UploadResumeResponse> {
  const formData = new FormData();

  formData.append("file", file);

  const response = await api.post<UploadResumeResponse>(
    "/resumes/upload",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    },
  );

  return response.data;
}

export async function getResumeStatus(
  resumeId: string,
): Promise<ResumeStatusResponse> {
  const response =
    await api.get<ResumeStatusResponse>(
      `/resumes/${resumeId}/status`,
    );

  return response.data;
}