import {
  Button,
} from "@/components/ui";

import type {
  ChangeEvent,
} from "react";


interface ResumeUploadProps {
  onUpload?: (
    file: File,
  ) => void;
}


export function ResumeUpload({
  onUpload,
}: ResumeUploadProps) {

  function handleChange(
    event: ChangeEvent<HTMLInputElement>,
  ) {
    const file =
      event.target.files?.[0];

    if (!file) {
      return;
    }

    onUpload?.(file);
  }


  return (
    <div
      className="
        flex
        flex-col
        gap-4
        rounded-2xl
        border
        border-dashed
        border-slate-300
        bg-white
        p-6
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
          Upload Resume
        </h3>

        <p
          className="
            mt-1
            text-sm
            text-slate-500
          "
        >
          Upload a resume file for
          parsing and candidate analysis.
        </p>
      </div>


      <label
        className="
          cursor-pointer
        "
      >
        <input
          type="file"
          accept=".pdf,.doc,.docx"
          className="hidden"
          onChange={handleChange}
        />

        <Button>
          Choose Resume
        </Button>
      </label>
    </div>
  );
}