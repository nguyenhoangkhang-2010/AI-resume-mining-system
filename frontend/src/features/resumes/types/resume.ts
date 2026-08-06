export type ResumeStatus =
  | "uploaded"
  | "processing"
  | "completed"
  | "failed";


export interface Resume {
  id: string;

  name: string;

  fileName: string;

  status: ResumeStatus;

  createdAt?: string;
}