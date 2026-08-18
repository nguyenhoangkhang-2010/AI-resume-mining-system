import type {
  Resume,
} from "../types/resume";


interface ResumeCardProps {
  resume: Resume;
}


export function ResumeCard({
  resume,
}: ResumeCardProps) {
  return (
    <article
      className="
        rounded-2xl
        border
        border-slate-200
        bg-white
        p-6
        shadow-sm
        transition
        hover:shadow-md
      "
    >
      <div
        className="
          flex
          items-start
          justify-between
          gap-4
        "
      >
        <div>
          <h3
            className="
              text-lg
              font-semibold
              text-slate-900
            "
          >
            {resume.name}
          </h3>

          <p
            className="
              mt-2
              text-sm
              text-slate-500
            "
          >
            {resume.fileName}
          </p>
        </div>


        <span
          className="
            rounded-full
            bg-slate-100
            px-3
            py-1
            text-xs
            font-medium
            text-slate-600
          "
        >
          {resume.status}
        </span>
      </div>


      {resume.createdAt && (
        <p
          className="
            mt-4
            text-xs
            text-slate-400
          "
        >
          Uploaded:
          {" "}
          {resume.createdAt}
        </p>
      )}
    </article>
  );
}