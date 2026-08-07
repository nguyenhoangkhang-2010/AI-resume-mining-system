import api from "./api";


export async function matchCandidates(
  jobId: string,
) {
  const response = await api.get(
    `/matches/${jobId}`,
  );

  return response.data;
}