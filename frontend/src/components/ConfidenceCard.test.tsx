import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ConfidenceCard } from "./ConfidenceCard";

describe("ConfidenceCard", () => {
  it("shows the percentage, the level and why it is not higher", () => {
    render(
      <ConfidenceCard
        confidence={{
          score: 0.851,
          level: "medium",
          components: { completeness: 0.7, fields: 0.9 },
          sections: {},
          reasons: ["experience_missing", "read_by_ocr"],
        }}
      />,
    );

    expect(screen.getByText(/85% · medium/)).toBeInTheDocument();
    expect(screen.getByText(/Read it/)).toBeInTheDocument();
    expect(screen.getByText("No work experience was found.")).toBeInTheDocument();
    expect(screen.getByText(/read from an image/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Completeness: 70/)).toBeInTheDocument();
  });

  it("says a low score means reading the CV yourself, and lists no reasons when there are none", () => {
    render(<ConfidenceCard confidence={{ score: 0.1, level: "low", components: {}, sections: {}, reasons: [] }} />);

    expect(screen.getByText(/Read the CV yourself/)).toBeInTheDocument();
    expect(screen.queryByText("What lowered it")).not.toBeInTheDocument();
  });
});
