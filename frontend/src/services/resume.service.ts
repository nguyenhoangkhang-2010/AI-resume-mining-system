import api from "./api";


export interface UploadResumeResponse {
  id: string;
  filename: string;
  status?: string;
}


export async function uploadResume(
  file: File
) {

  const formData = new FormData();

  formData.append(
    "file",
    file
  );


  const response = await api.post(
    "/resumes/upload",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );


  return response.data;
}