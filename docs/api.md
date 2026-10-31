# API reference

Interactive documentation is served at `/docs` (Swagger UI) and
`/openapi.json`. All routes are under `/api/v1`.

## Authentication and limits

Every `/api/v1` route needs an API key, sent as `X-API-Key: <key>` or
`Authorization: Bearer <key>` (both are offered by the Authorize button in
Swagger UI). `/`, `/health` and the docs stay open. Keys are configured with
`API_KEYS=role:key,role:key` and have one of two roles:

| Role | Can do |
|---|---|
| `user` | everything except deleting |
| `admin` | everything, including `DELETE /resumes/{id}` and `DELETE /jobs/{id}` |

- Requests are limited per key per minute (`RATE_LIMIT_PER_MINUTE`, default
  120). Endpoints that run the embedding model or the LLM (upload, job
  creation, search, recommendations) use a stricter budget
  (`RATE_LIMIT_HEAVY_PER_MINUTE`, default 20). Over the limit the API
  answers 429 with a `Retry-After` header.
- Browsers may call the API only from the origins in `CORS_ORIGINS`
  (comma-separated; empty means no cross-origin access).
- Job descriptions are limited to `MAX_JOB_DESCRIPTION_CHARS` characters.

## Conventions

- **Lists** return `{ "items": [...], "total": N, "limit": L, "offset": O }`,
  newest first. `limit` is 1-100 (default 20), `offset` starts at 0.
- **Errors** return `{ "detail": "...", "code": "..." }`. Codes: `not_found`
  (404, also for a malformed id), `conflict` (409), `file_too_large` (413),
  `unsupported_file_type` (415), `invalid_upload` (400), `unauthorized`
  (401), `forbidden` (403), `rate_limited` (429),
  `database_unavailable` (503), `internal_error` (500). Request validation
  errors are 422.
- **Contact details** (email, phone, links) appear only in
  `GET /candidates/{id}` and in match results; lists and search results show
  the name and skills only.

## Resumes

| Method | Path | Purpose |
|---|---|---|
| POST | `/resumes/upload` | Upload a PDF or a Word `.docx` (also PNG or JPEG when `OCR_ENABLED=true`); returns 202 and processes it in the background. A `.docx` that is not a Word document, or an image that cannot be opened, is refused with 400 |
| GET | `/resumes/` | List resumes; filter with `?status=pending\|processing\|processed\|needs_review\|failed` |
| GET | `/resumes/{id}` | Resume detail, including the `candidate_id` once indexed |
| GET | `/resumes/{id}/status` | Status with `reason`, `warnings` and `confidence` |
| DELETE | `/resumes/{id}` | Delete the resume, its candidate, its vector and the uploaded file (409 while processing) |

`needs_review` means the file was readable but nothing usable was extracted
(for example a scanned PDF without OCR); `reason` says why.

`confidence` (in the list, the detail and the status; absent until the resume
has been processed) says how far the extraction can be trusted:

```json
{
  "score": 0.82,
  "level": "high",
  "components": {"completeness": 0.85, "structure": 1.0, "extraction": 0.9, "fields": 0.7},
  "sections": {"experience": 1.0, "education": 1.0, "skills": 0.7},
  "reasons": ["dates_not_matched_to_entries"]
}
```

`score` is 0 to 1 and is not a probability; `level` is `high` (0.9 and up),
`medium` (0.5 and up) or `low`. `reasons` are short codes for what lowered it
(for example `read_by_ocr`, `experience_section_guessed`,
`experience_read_by_model`, `experience_without_dates`, `education_missing`).
Below `LOW_CONFIDENCE_WARNING` (default 0.5) the resume gets the warning
`low_confidence`; below `REVIEW_BELOW_CONFIDENCE` (default 0, off) it is held as
`needs_review` with that reason instead of being indexed. How well the score
follows the real accuracy is in [evaluation/confidence.md](evaluation/confidence.md).

`warnings` may contain `possible_prompt_injection`: the resume text contains
phrases that try to instruct the language model (for example "ignore all
previous instructions"). The resume is still processed, with control tokens
removed from the prompt and name-like fields checked against the text, but a
recruiter should read it.

## Jobs

| Method | Path | Purpose |
|---|---|---|
| POST | `/jobs/` | Create a job from a description (optional `location`); skills, experience and responsibilities are extracted and the job's vector is indexed so it can be recommended |
| GET | `/jobs/` | List jobs (summaries) |
| GET | `/jobs/{id}` | Job detail (same shape as the create response) |
| DELETE | `/jobs/{id}` | Delete a job |

## Candidates

| Method | Path | Purpose |
|---|---|---|
| GET | `/candidates/` | List candidate summaries; `?skill=python` filters by normalised skill, ignoring case |
| GET | `/candidates/{id}` | Full candidate profile |
| GET | `/candidates/{id}/jobs` | Jobs that fit this candidate, best first, with reasons (see below) |

## Recommending jobs to a candidate

`GET /candidates/{id}/jobs` (or `GET /resumes/{id}/jobs`, which finds the
candidate built from a resume and answers 409 until it has been processed)
returns the jobs that fit a profile best. Typical flow for a candidate:
upload a CV, poll `GET /resumes/{id}/status` until `processed`, then call
`GET /resumes/{id}/jobs`.

| Parameter | Default | Meaning |
|---|---|---|
| `top_k` | 10 | jobs to return (1-50) |
| `min_score` | 50 | leave out jobs scoring below this (0-100) |
| `location` | none | only jobs whose location contains this text, ignoring case |

Each result has the job (`title`, `location`, `experience_years`,
`required_skills`), a `score` (0-100) that orders the list, `skill_gaps` (the
required skills the profile does not show) and a `score_breakdown` with the
skill, semantic and experience scores, the matched skills and a sentence
explaining each. Scores use the same hybrid scorer and weights as ranking
candidates for a job, so a job and a candidate get the same score whichever
is the query. The `metadata` says how many jobs were retrieved, left out by
the score and location filters, and how many jobs have no vector yet
(`unindexed_jobs`; they cannot be recommended until `scripts/reindex_jobs.py`
has been run). Jobs with no semantic similarity to the profile are not
retrieved at all. The score is a suggestion for the candidate, not a judgement
of ability.

## Matching, search and recommendations

| Method | Path | Purpose |
|---|---|---|
| GET | `/matches/{job_id}` | Rank candidates for a job (skills, semantic similarity, experience) with a per-component breakdown |
| POST | `/search/candidates` | Free-text semantic search: `{ "query": "...", "top_k": 10 }`; scores are 0-100 |
| GET | `/recommendations/?job_id=...&candidate_id=...` | Skills the candidate lacks for the job and suggested ways to learn them |

Recommendations come from the configured providers (ESCO, industry skills,
static course list); a missing skill without an entry in any of them gets no
suggestion.
