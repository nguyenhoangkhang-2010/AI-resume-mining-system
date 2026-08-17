import {
  ResumesHeader,
} from "./ResumesHeader";

import {
  ResumeUpload,
} from "./ResumeUpload";

import {
  ResumeList,
} from "./ResumeList";

import {
  ResumeEmptyState,
} from "./ResumeEmptyState";

import {
  useResumes,
} from "../hooks/useResumes";


export function ResumesView() {
  const {
    resumes,
    loading,
    error,
    uploadResume,
  } = useResumes();

  if (error) {
    return (
      <div>
        Failed to process resume.
        Please try again.
      </div>
    );
  }

  return (
    <section
      className="
        flex
        flex-col
        gap-6
      "
    >
      <ResumesHeader />

      <ResumeUpload
        onUpload={uploadResume}
      />

      {loading && (
        <div>
          Uploading resume...
        </div>
      )}

      {resumes.length === 0 ? (
        <ResumeEmptyState />
      ) : (
        <ResumeList
          resumes={resumes}
        />
      )}
    </section>
  );
}