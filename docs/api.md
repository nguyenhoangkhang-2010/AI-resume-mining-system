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
| POST | `/resumes/upload` | Upload a PDF or DOCX; returns 202 and processes it in the background |
| GET | `/resumes/` | List resumes; filter with `?status=pending\|processing\|processed\|needs_review\|failed` |
| GET | `/resumes/{id}` | Resume detail, including the `candidate_id` once indexed |
| GET | `/resumes/{id}/status` | Status with `reason` and `warnings` |
| DELETE | `/resumes/{id}` | Delete the resume, its candidate, its vector and the uploaded file (409 while processing) |

`needs_review` means the file was readable but nothing usable was extracted
(for example a scanned PDF without OCR); `reason` says why.

`warnings` may contain `possible_prompt_injection`: the resume text contains
phrases that try to instruct the language model (for example "ignore all
previous instructions"). The resume is still processed, with control tokens
removed from the prompt and name-like fields checked against the text, but a
recruiter should read it.

## Jobs

| Method | Path | Purpose |
|---|---|---|
| POST | `/jobs/` | Create a job from a description; skills, experience and responsibilities are extracted |
| GET | `/jobs/` | List jobs (summaries) |
| GET | `/jobs/{id}` | Job detail (same shape as the create response) |
| DELETE | `/jobs/{id}` | Delete a job |

## Candidates

| Method | Path | Purpose |
|---|---|---|
| GET | `/candidates/` | List candidate summaries; `?skill=python` filters by normalised skill, ignoring case |
| GET | `/candidates/{id}` | Full candidate profile |

## Matching, search and recommendations

| Method | Path | Purpose |
|---|---|---|
| GET | `/matches/{job_id}` | Rank candidates for a job (skills, semantic similarity, experience) with a per-component breakdown |
| POST | `/search/candidates` | Free-text semantic search: `{ "query": "...", "top_k": 10 }`; scores are 0-100 |
| GET | `/recommendations/?job_id=...&candidate_id=...` | Skills the candidate lacks for the job and suggested ways to learn them |

Recommendations come from the configured providers (ESCO, industry skills,
static course list); a missing skill without an entry in any of them gets no
suggestion.
