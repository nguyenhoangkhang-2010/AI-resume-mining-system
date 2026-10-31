import { useState } from "react";

import { useConnection } from "../app/context";
import { isFinal, type JobMatches, type ResumeStatus } from "../api/types";
import { ConfidenceCard } from "../components/ConfidenceCard";
import { JobFit } from "../components/Matches";
import { Badge, Empty, ErrorNotice, Icon, PageHead, Steps } from "../components/ui";
import { SAMPLE_CVS } from "../api/demo";
import { statusLabel, statusReason, warningText } from "../lib/format";
import { usePolling } from "../lib/usePolling";

const TONE = { processed: "good", needs_review: "warn", failed: "bad" } as const;
const STEPS = ["Uploaded", "In queue", "Reading", "Result"];

/** Which step is in progress: the file is uploaded, then queued, then read, then there is a result. */
function stepAt(status: ResumeStatus | null): number {
  if (!status || status.status === "pending") return 1;
  if (status.status === "processing") return 2;

  return STEPS.length;
}

/** Upload a CV, watch it being read, see how far to trust it and which jobs fit. */
export function UploadView() {
  const { api } = useConnection();
  const [resumeId, setResumeId] = useState<string | null>(null);
  const [filename, setFilename] = useState("");
  const [status, setStatus] = useState<ResumeStatus | null>(null);
  const [jobs, setJobs] = useState<JobMatches | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const [dragging, setDragging] = useState(false);

  const waiting = resumeId !== null && (status === null || !isFinal(status.status));

  usePolling(
    waiting,
    async () => {
      const next = await api.resumeStatus(resumeId!);
      setStatus(next);

      if (next.status === "processed") {
        // The recommendations only exist once the candidate is indexed.
        api.jobsForResume(resumeId!).then(setJobs).catch(setError);
      }

      return isFinal(next.status);
    },
    (failure) => setError(failure),
    api.mode === "demo" ? 700 : 1500,
  );

  async function send(file: File) {
    setError(null);
    setStatus(null);
    setJobs(null);
    setBusy(true);

    try {
      const created = await api.uploadResume(file);
      setFilename(created.filename);
      setResumeId(created.id);
    } catch (failure) {
      setResumeId(null);
      setError(failure);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHead eyebrow="Step 1" title="Read a CV">
        Drop in a PDF or Word file. It is read in the background, and this page follows it: what was found, how far
        to trust it, and which jobs fit.
      </PageHead>

      <div className="grid">
        <section className="stack sticky">
          {api.mode === "live" ? (
            <label
              className={dragging ? "dropzone dropzone-over" : "dropzone"}
              onDragOver={(event) => {
                event.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={(event) => {
                event.preventDefault();
                setDragging(false);
                const file = event.dataTransfer.files?.[0];
                if (file) void send(file);
              }}
            >
              <input
                type="file"
                accept=".pdf,.docx,.png,.jpg,.jpeg"
                aria-label="CV file"
                disabled={busy}
                onChange={(event) => {
                  const file = event.target.files?.[0];
                  if (file) void send(file);
                  event.target.value = "";
                }}
              />
              <Icon name="upload" />
              <strong>{busy ? "Uploading…" : "Drop a CV here, or choose a file"}</strong>
              <span>PDF or Word (.docx). Photos (PNG, JPEG) only when the server has OCR on.</span>
            </label>
          ) : (
            <div className="card">
              <p className="eyebrow">Try a sample</p>
              <p className="muted">These CVs are synthetic. Pick one to watch it being read.</p>
              <div className="samples">
                {SAMPLE_CVS.map((sample) => (
                  <button
                    key={sample.id}
                    type="button"
                    className="sample"
                    disabled={busy}
                    onClick={() => void send(new File([], sample.filename))}
                  >
                    <strong>{sample.label}</strong>
                    <span>{sample.description}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          <ErrorNotice error={error} />
        </section>

        <section className="stack">
          {!resumeId && <Empty>Nothing uploaded yet. The result appears here.</Empty>}

          {resumeId && (
            <div className="card">
              <header className="card-head">
                <h3>{filename}</h3>
                <Badge tone={status && status.status in TONE ? TONE[status.status as keyof typeof TONE] : "neutral"}>
                  {status ? statusLabel(status.status) : "Uploaded"}
                </Badge>
              </header>

              <Steps steps={STEPS} at={stepAt(status)} failed={status?.status === "failed"} />

              {waiting && <p className="muted">This takes seconds to minutes on a CPU.</p>}

              {status?.reason && <p className="muted">{statusReason(status.reason)}</p>}

              {(status?.warnings ?? []).length > 0 && (
                <ul className="reasons">
                  {status!.warnings!.map((warning) => (
                    <li key={warning}>{warningText(warning)}</li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {status?.confidence && <ConfidenceCard confidence={status.confidence} />}

          {status?.status === "processed" && (
            <div className="stack">
              <h2>Jobs that fit this CV</h2>
              {!jobs && <p className="muted">Looking for jobs…</p>}
              {jobs && jobs.results && jobs.results.length === 0 && <Empty>No job reaches the minimum score.</Empty>}
              <ol className="matches">
                {(jobs?.results ?? []).map((match, index) => (
                  <JobFit key={match.job_id} rank={index + 1} match={match} />
                ))}
              </ol>
            </div>
          )}
        </section>
      </div>
    </>
  );
}
