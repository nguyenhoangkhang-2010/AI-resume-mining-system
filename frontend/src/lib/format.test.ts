import { describe, expect, it } from "vitest";

import { confidencePercent, confidenceReason, statusLabel, statusReason, warningText } from "./format";

describe("format", () => {
  it("explains the known confidence reasons in plain words", () => {
    expect(confidenceReason("read_by_ocr")).toMatch(/image/);
    expect(confidenceReason("dates_not_matched_to_entries")).toMatch(/date ranges/);
  });

  it("builds a sentence for the per-section reasons", () => {
    expect(confidenceReason("experience_section_guessed")).toMatch(/experience section was guessed/);
    expect(confidenceReason("education_without_section")).toMatch(/education/);
  });

  it("falls back to readable text for a reason it does not know", () => {
    expect(confidenceReason("some_new_reason")).toBe("some new reason");
  });

  it("rounds the confidence to whole percent", () => {
    expect(confidencePercent(0.8514)).toBe(85);
    expect(confidencePercent(1)).toBe(100);
  });

  it("names the states, warnings and status reasons", () => {
    expect(statusLabel("needs_review")).toBe("Needs review");
    expect(statusLabel("weird")).toBe("weird");
    expect(warningText("low_confidence")).toMatch(/read this CV yourself/);
    expect(statusReason("no_text_extracted")).toMatch(/scan/);
    expect(statusReason(null)).toBe("");
  });
});
