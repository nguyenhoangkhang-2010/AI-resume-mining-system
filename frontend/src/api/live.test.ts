import { afterEach, describe, expect, it, vi } from "vitest";

import { liveApi } from "./live";
import { ApiError } from "./types";

const settings = { baseUrl: "http://api.test/", apiKey: "secret-key" };

function respond(body: unknown, init: ResponseInit = {}) {
  return Promise.resolve(new Response(JSON.stringify(body), { status: 200, ...init }));
}

afterEach(() => vi.unstubAllGlobals());

describe("liveApi", () => {
  it("sends the key and calls the path under the base address", async () => {
    const fetchMock = vi.fn().mockImplementation(() => respond({ items: [], total: 0, limit: 50, offset: 0 }));
    vi.stubGlobal("fetch", fetchMock);

    await liveApi(() => settings).listJobs();

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://api.test/api/v1/jobs/?limit=50");
    expect(new Headers(init.headers).get("X-API-Key")).toBe("secret-key");
  });

  it("sends no key header when none is set", async () => {
    const fetchMock = vi.fn().mockImplementation(() => respond({ items: [] }));
    vi.stubGlobal("fetch", fetchMock);

    await liveApi(() => ({ baseUrl: "", apiKey: "" })).listResumes();

    expect(new Headers(fetchMock.mock.calls[0][1].headers).has("X-API-Key")).toBe(false);
  });

  it("posts JSON for a job and form data for a file", async () => {
    const fetchMock = vi.fn().mockImplementation(() => respond({}));
    vi.stubGlobal("fetch", fetchMock);
    const api = liveApi(() => settings);

    await api.createJob({ title: "Engineer", description: "Build things" });
    await api.uploadResume(new File(["x"], "cv.pdf"));

    const [, job] = fetchMock.mock.calls[0];
    expect(new Headers(job.headers).get("Content-Type")).toBe("application/json");
    expect(JSON.parse(job.body)).toEqual({ title: "Engineer", description: "Build things" });

    const [, upload] = fetchMock.mock.calls[1];
    expect(upload.body).toBeInstanceOf(FormData);
    expect(new Headers(upload.headers).has("Content-Type")).toBe(false);
  });

  it("turns an error body into an ApiError with the code", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(() => respond({ detail: "bad key", code: "unauthorized" }, { status: 401 })),
    );

    await expect(liveApi(() => settings).listJobs()).rejects.toMatchObject({
      status: 401,
      code: "unauthorized",
      message: "bad key",
    });
  });

  it("reads Retry-After from a rate limit answer", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockImplementation(() =>
          respond({ detail: "slow down", code: "rate_limited" }, { status: 429, headers: { "Retry-After": "12" } }),
        ),
    );

    await expect(liveApi(() => settings).searchCandidates("x")).rejects.toMatchObject({
      status: 429,
      retryAfter: 12,
    });
  });

  it("reports an unreachable API as status 0", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("network")));

    const failure = await liveApi(() => settings)
      .listJobs()
      .catch((error) => error);

    expect(failure).toBeInstanceOf(ApiError);
    expect(failure.status).toBe(0);
  });

  it("reads the body of a 503 from /ready", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(() => respond({ status: "not_ready", models: "loading" }, { status: 503 })),
    );

    expect(await liveApi(() => settings).ready()).toEqual({ status: "not_ready", models: "loading" });
  });
});
