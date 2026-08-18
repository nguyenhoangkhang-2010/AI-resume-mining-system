import api from "./api";


export interface CreateJobPayload {

  title: string;

  description: string;

}


export async function createJob(
  data: CreateJobPayload
) {

  const response = await api.post(
    "/jobs/",
    data
  );


  return response.data;
}