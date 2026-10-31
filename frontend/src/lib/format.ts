export function percent(value: number | null | undefined): string {
  return value === null || value === undefined ? "–" : `${Math.round(value)}%`;
}

/** 0..1 confidence as a whole percentage. */
export function confidencePercent(score: number): number {
  return Math.round(score * 100);
}

const CONFIDENCE_REASONS: Record<string, string> = {
  read_by_ocr: "The text was read from an image, which makes mistakes more likely.",
  very_little_text: "Very little text was found in the file.",
  name_missing: "No name was found.",
  contact_missing: "No email or phone number was found.",
  experience_missing: "No work experience was found.",
  education_missing: "No education was found.",
  skills_missing: "No skills were found.",
  experience_without_dates: "Most jobs have no dates.",
  dates_not_matched_to_entries:
    "The CV has date ranges that no job or school entry received, so entries may be missing.",
  experience_read_by_model: "Experience was read by the language model, not by rules.",
  education_read_by_model: "Education was read by the language model, not by rules.",
};

export function confidenceReason(code: string): string {
  const known = CONFIDENCE_REASONS[code];

  if (known) return known;

  const section = /^(experience|education|skills)_(section_guessed|without_section)$/.exec(code);

  if (section) {
    return section[2] === "section_guessed"
      ? `The ${section[1]} section was guessed from its content, not found by its heading.`
      : `Entries were found for ${section[1]} but no matching section.`;
  }

  return code.replace(/_/g, " ");
}

const WARNINGS: Record<string, string> = {
  no_experience_found: "No work experience found",
  no_education_found: "No education found",
  no_skills_found: "No skills found",
  no_name_found: "No name found",
  no_contact_found: "No contact details found",
  low_confidence: "Low confidence: read this CV yourself",
  possible_prompt_injection: "Contains text that tries to instruct the AI; read it yourself",
};

export function warningText(code: string): string {
  return WARNINGS[code] ?? code.replace(/_/g, " ");
}

const STATUS_REASONS: Record<string, string> = {
  no_text_extracted: "No text could be read (a scan without OCR?)",
  no_content_extracted: "Text was read but nothing usable was found in it",
  unreadable_file: "The file could not be opened",
  password_protected: "The file is password protected",
  file_missing: "The uploaded file is missing",
  processing_error: "Processing failed",
  too_many_attempts: "Processing failed repeatedly",
  low_confidence: "Held for review because of low confidence",
};

export function statusReason(code: string | null | undefined): string {
  return code ? (STATUS_REASONS[code] ?? code.replace(/_/g, " ")) : "";
}

const STATUS_LABEL: Record<string, string> = {
  pending: "Waiting",
  processing: "Reading the CV…",
  processed: "Processed",
  needs_review: "Needs review",
  failed: "Failed",
};

export function statusLabel(status: string): string {
  return STATUS_LABEL[status] ?? status;
}

export const COMPONENT_LABEL: Record<string, string> = {
  completeness: "Completeness",
  structure: "Sections found",
  extraction: "Read by rules",
  fields: "Field quality",
};
