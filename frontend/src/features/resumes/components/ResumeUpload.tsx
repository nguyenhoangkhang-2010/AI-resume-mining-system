import { useRef, useState } from "react";
import type { ChangeEvent } from "react";

import { Button } from "@/components/ui";

interface ResumeUploadProps {
  onUpload?: (file: File) => Promise<unknown> | void;
  loading?: boolean;
}

export function ResumeUpload({
  onUpload,
  loading = false,
}: ResumeUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const [selectedFile, setSelectedFile] =
    useState<File | null>(null);

  async function handleChange(
    event: ChangeEvent<HTMLInputElement>,
  ) {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    setSelectedFile(file);

    try {
      await onUpload?.(file);
    } catch {
      // Parent hook handles the error.
    }

    event.target.value = "";
  }

  function handleChooseFile() {
    if (loading) {
      return;
    }

    inputRef.current?.click();
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
        <h3 className="text-lg font-semibold text-slate-900">
          Upload Resume
        </h3>

        <p className="mt-1 text-sm text-slate-500">
          Upload a resume file for parsing
          and candidate analysis.
        </p>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.doc,.docx"
        className="hidden"
        disabled={loading}
        onChange={handleChange}
      />

      <Button
        type="button"
        disabled={loading}
        onClick={handleChooseFile}
      >
        {loading ? "Uploading..." : "Choose Resume"}
      </Button>

      {selectedFile && (
        <div
          className="
            rounded-xl
            border
            border-slate-200
            bg-slate-50
            px-4
            py-3
          "
        >
          <p className="text-sm font-medium text-slate-900">
            {selectedFile.name}
          </p>

          <p className="mt-1 text-xs text-slate-500">
            {(selectedFile.size / 1024).toFixed(1)} KB
          </p>
        </div>
      )}
    </div>
  );
}