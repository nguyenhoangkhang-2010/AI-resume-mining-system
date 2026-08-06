import {
  EmptyState,
} from "@/components/ui";


export function ResumeEmptyState() {
  return (
    <EmptyState
      title="No resumes found"
      description="
        Upload a resume to start
        extracting candidate information.
      "
    />
  );
}