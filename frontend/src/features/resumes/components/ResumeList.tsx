import {
  ResumeCard,
} from "./ResumeCard";

import type {
  Resume,
} from "../types/resume";


interface ResumeListProps {
  resumes: Resume[];
}


export function ResumeList({
  resumes,
}: ResumeListProps) {
  return (
    <section
      className="
        grid
        gap-6
        md:grid-cols-2
        xl:grid-cols-3
      "
    >
      {resumes.map((resume) => (
        <ResumeCard
          key={resume.id}
          resume={resume}
        />
      ))}
    </section>
  );
}