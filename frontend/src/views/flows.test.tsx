import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SAMPLE_CVS } from "../api/demo";
import App from "../app/App";
import { ConnectionProvider } from "../app/context";

function open(hash: string) {
  window.location.hash = hash;

  return render(
    <ConnectionProvider forceDemo>
      <App />
    </ConnectionProvider>,
  );
}

const matches = () => document.querySelectorAll(".matches .match").length;

describe("the recorded demo, end to end", () => {
  it("shows an uploaded sample being read, its confidence and the jobs that fit", async () => {
    open("#cv");

    fireEvent.click(screen.getAllByRole("button", { name: new RegExp(SAMPLE_CVS[0].label) })[0]);

    await waitFor(() => expect(screen.getByText("Processed")).toBeInTheDocument(), { timeout: 8000 });
    expect(screen.getByLabelText("Extraction confidence")).toBeInTheDocument();
    expect(await screen.findByText("Jobs that fit this CV")).toBeInTheDocument();
    await waitFor(() => expect(matches()).toBeGreaterThan(0));
  }, 15000);

  it("holds a scan for review and explains why, without recommendations", async () => {
    open("#cv");

    fireEvent.click(screen.getByRole("button", { name: /scanned/i }));

    await waitFor(() => expect(screen.getByText("Needs review")).toBeInTheDocument(), { timeout: 8000 });
    expect(screen.getByText(/No text could be read/)).toBeInTheDocument();
    expect(screen.queryByText("Jobs that fit this CV")).not.toBeInTheDocument();
  }, 15000);

  it("ranks candidates for the job that is picked", async () => {
    open("#jobs");

    await waitFor(() => expect(document.querySelectorAll(".row").length).toBeGreaterThan(0));
    fireEvent.click(document.querySelector(".row")!);

    await waitFor(() => expect(matches()).toBeGreaterThan(0));
    expect(screen.getByText(/below the minimum score/)).toBeInTheDocument();
  });

  it("answers a preset search", async () => {
    open("#search");

    fireEvent.click(screen.getAllByRole("button", { name: /Kubernetes/ })[0]);

    await waitFor(() => expect(matches()).toBeGreaterThan(0));
  });

  it("filters the resume list by state", async () => {
    open("#resumes");

    await waitFor(() => expect(document.querySelectorAll(".list > li").length).toBeGreaterThan(1));
    fireEvent.click(screen.getByRole("button", { name: /^Needs review/ }));

    await waitFor(() => expect(document.querySelectorAll(".list > li").length).toBe(1));
  });
});
