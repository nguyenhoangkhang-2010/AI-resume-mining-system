import { describe, expect, it } from "vitest";

import fixtures from "../demo/fixtures.json";
import { PRESET_QUERIES, SAMPLE_CVS, demoApi } from "./demo";

describe("demoApi", () => {
  it("has samples, jobs and recorded searches", () => {
    expect(SAMPLE_CVS.length).toBeGreaterThanOrEqual(3);
    expect(PRESET_QUERIES.length).toBeGreaterThanOrEqual(3);
  });

  it("walks an upload through pending, processing and the recorded result", async () => {
    let clock = 1_000;
    const api = demoApi(() => clock);
    const sample = SAMPLE_CVS[0];

    const created = await api.uploadResume(new File([], sample.filename));
    expect(created.id).toBe(sample.id);

    expect((await api.resumeStatus(sample.id)).status).toBe("pending");

    clock += 800;
    expect((await api.resumeStatus(sample.id)).status).toBe("processing");

    clock += 2_000;
    const done = await api.resumeStatus(sample.id);
    expect(done.status).toBe("processed");
    expect(done.confidence?.level).toBeDefined();
  });

  it("refuses a file that is not a sample", async () => {
    await expect(demoApi().uploadResume(new File([], "mine.pdf"))).rejects.toMatchObject({ status: 400 });
  });

  it("has a held-for-review sample that gets no recommendations", async () => {
    const held = fixtures.samples.find((sample) => sample.status.status === "needs_review");
    expect(held).toBeDefined();
    await expect(demoApi().jobsForResume(held!.id)).rejects.toMatchObject({ status: 409 });
  });

  it("answers a match for every recorded job and 404 for others", async () => {
    const api = demoApi();

    for (const job of (await api.listJobs()).items ?? []) {
      expect((await api.matchCandidates(job.id)).results?.length).toBeGreaterThan(0);
    }

    await expect(api.matchCandidates("nope")).rejects.toMatchObject({ status: 404 });
  });

  it("answers the preset questions and nothing for others", async () => {
    const api = demoApi();

    expect((await api.searchCandidates(PRESET_QUERIES[0])).results?.length).toBeGreaterThan(0);
    expect((await api.searchCandidates("something else")).results).toEqual([]);
  });

  it("cannot create a job", async () => {
    await expect(demoApi().createJob({ title: "x", description: "y" })).rejects.toThrow(/live API/);
  });
});

describe("the recorded data", () => {
  const text = JSON.stringify(fixtures);

  it("contains no email address or phone number", () => {
    expect(text).not.toMatch(/[\w.+-]+@[\w-]+\.[\w.]+/);
    expect(text).not.toMatch(/\+\d[\d ]{8,}/);
  });

  it("matches the shape the screens read", () => {
    for (const sample of fixtures.samples) {
      expect(sample.status.status).toMatch(/processed|needs_review|failed/);
      expect(sample.filename).toMatch(/\.pdf$/);
    }
  });
});
