# Running it: the worker, observability, the CI gate and load

What happens between an upload and a ranked list, how to see what the system is
doing, and how a regression is stopped before it is merged. Measurements are
from one CPU-only development machine (14 cores) and are floors, not forecasts.

## 1. CV processing is a durable queue

Before, an upload ran as a FastAPI background task. If the process restarted,
the CV stayed `processing` for ever; a failure was never retried; and how many
CVs ran at once was whatever the thread pool allowed.

Now an upload only stores the file and a `pending` resume. Worker threads in
the API process take resumes from the database
([resume_queue.py](../app/workers/resume_queue.py),
[resume_worker.py](../app/workers/resume_worker.py)):

| Need | How |
|---|---|
| No two workers take the same CV | one atomic `find_one_and_update` moves `pending` to `processing` and stamps a lease |
| A dead worker does not lose the CV | the lease expires (`WORKER_LEASE_SECONDS`, renewed every third of it while working) and the CV is claimed again; resumes left `processing` by the old code are picked up too |
| Temporary failures are retried | an unclassified error puts the CV back with a delay that doubles from `WORKER_RETRY_BACKOFF_SECONDS`, up to `WORKER_MAX_ATTEMPTS`; a damaged, encrypted or missing file fails at once |
| A CV that kills its worker does not do so for ever | after the maximum number of takes it is marked `failed` with reason `too_many_attempts` |
| Load is bounded | `WORKER_CONCURRENCY` threads (default 1; the language model runs one prompt at a time) |
| Clean stop | the API waits `WORKER_SHUTDOWN_SECONDS` for the CV in hand; if it takes longer, the lease runs out and another start continues it |

`PROCESSING_MODE=inline` restores the old behaviour.

**Why not Redis and Celery.** They would give priorities, rate limits and a
dashboard, and need one more service. The database is already required, the
queue is a few hundred lines with tests, and it sits behind four methods
(`claim`, `renew`, `retry_later`, `fail`) if the volume ever asks for more.

**What it does not do.** The workers must live in the API process: the vector
index is held in the memory of the process that adds to it, so a separate worker
would index CVs the API could not find. A second API replica would not see them
either. Running the worker elsewhere, or scaling out, needs a shared vector
store, which is not built. `WORKER_EMBEDDED=false` therefore only pauses
processing.

Tested with an in-memory MongoDB for the query logic (14 queue tests, 10 worker
tests including crash, retry, lease renewal and shutdown) and, in CI, against a
real MongoDB with eight threads claiming 40 CVs ([test_queue_integration.py](../tests/integration/test_queue_integration.py)).
The integration tests could not run on the development machine (no Docker/Mongo
running), so they have only run in CI.

## 2. Observability

- **Request ids.** Every response has `X-Request-ID` (the caller's if it is
  8-64 safe characters, otherwise generated) and every log line written while
  handling the request carries it; worker log lines carry `resume_id`.
  `LOG_FORMAT=json` writes one JSON object per line with those as fields.
- **Metrics** at `/metrics` (Prometheus text; admin key when auth is on;
  `METRICS_ENABLED`): `http_requests_total` and `http_request_duration_seconds`
  by method, route template and status (the template, not the URL, so an id
  never becomes a label; unmatched paths share one label), `resume_jobs_total`
  by outcome, `resume_job_duration_seconds`, and the queue gauges
  `resume_queue_pending`, `resume_queue_processing` and
  `resume_queue_oldest_pending_seconds`, read when scraped.
- **`/ready`** answers 200 only when the database answers, the models are loaded,
  the start-up warm-up has finished and the worker threads are alive; `/health`
  stays the cheap liveness check.

A useful alert: `resume_queue_oldest_pending_seconds` growing means the worker is
stuck or slower than the arrival rate.

## 3. A CI gate on quality, not only on code

The unit tests say the code does what it was written to do; they do not notice
a change that makes ranking or section detection worse. `python -m
scripts.eval_gate` (a CI step, about 90 seconds) re-runs the evaluations on
small fixed synthetic sets and compares headline numbers with
[gate_baseline.json](evaluation/gate_baseline.json):

| Check | Baseline |
|---|---|
| ranking nDCG@10 and MRR, both label sets | 0.894 / 0.924, MRR 1.0 |
| section line accuracy, English/Vietnamese CVs | 0.897 |
| section line accuracy, French/Spanish/German/Portuguese/Russian CVs | 0.923 |
| score shift caused by a pronoun, a name, a career break | at most 0.05 points |

A fall of more than 0.02 fails the build; an improvement passes and says so, and
`--update` rewrites the baseline in the same commit as the change that earned it.
The sets are small, so the 0.02 tolerance is a noise floor, not a quality bar,
and the gate cannot see anything the sets do not contain.

## 4. Load and what it found

[load_test.md](evaluation/load_test.md), from `python -m scripts.load_test`:
300 synthetic candidates in a real FAISS index, the real embedding model,
MongoDB replaced by an in-memory fake, the API called in-process. So it measures
what the API itself does and leaves out the network and the database server.

- **Matching is CPU-bound and does not scale with concurrency.** Throughput stays
  between 7 and 13 requests per second from 1 to 16 concurrent callers while latency
  grows in proportion (p50 99 ms alone, about 1.4 s at 16): one model run per
  request, on cores the other requests also need. More callers wait longer;
  more throughput needs more cores, a GPU, or fewer model runs.
- **Embedding the job was most of the request** (profile: 117 of 180 ms). Texts
  are now cached in a small LRU (`EMBEDDING_CACHE_SIZE`, default 512), so a job
  that is matched again skips it: in the same run, p50 99 to 63 ms and 7.3 to
  11.3 requests per second for jobs seen before. The first match of a job still
  pays the model run.
- **The first call to the jobs endpoints took 71 seconds.** Their services
  (occupation taxonomy, job models) were built lazily by the first request; the
  load test showed it as a p99 of 71 s on a request that otherwise takes 8 ms. A
  start-up warm-up now builds them on a thread (25.7 s here, `WARMUP_ENABLED`),
  and `/ready` waits for it.
- Peak memory of the process in the test: about 1.2 GB (embedding model, NER
  not loaded, no language model).

Runs on this machine vary by tens of percent from one to the next (the
candidates list went from 29 to 52 requests/s between two runs with no change
to it), so compare rows within one report, not across reports.

## Limits kept honest

- Rate limits are counted in process memory: correct for the single process
  this runs as, reset by a restart, and independent per replica.
- Reindexing after an embedding text change is still a script (`scripts.reindex_candidates`,
  `scripts.reindex_jobs`) run with the API stopped.
- No end-to-end load test with a real MongoDB or with uploads: processing a CV
  takes minutes on CPU and is measured by the extraction benchmarks instead.
