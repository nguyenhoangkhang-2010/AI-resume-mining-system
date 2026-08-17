export type ResumeStatus =
  | "pending"
  | "processing"
  | "processed"
  | "failed";

export interface Resume {
  id: string;
  name: string;
  fileName: string;
  status: ResumeStatus;
  createdAt?: string;
}