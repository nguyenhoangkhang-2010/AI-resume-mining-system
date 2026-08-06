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


  if (loading) {
    return (
      <div>
        Loading resumes...
      </div>
    );
  }


  if (error) {
    return (
      <div>
        Failed to load resumes
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