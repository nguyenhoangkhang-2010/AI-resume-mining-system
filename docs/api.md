# API reference

Interactive documentation is served at `/docs` (Swagger UI) and
`/openapi.json`. All routes are under `/api/v1`. There is no authentication
yet, so keep the API bound to localhost (see [deployment.md](deployment.md)).

## Conventions

- **Lists** return `{ "items": [...], "total": N, "limit": L, "offset": O }`,
  newest first. `limit` is 1-100 (default 20), `offset` starts at 0.
- **Errors** return `{ "detail": "...", "code": "..." }`. Codes: `not_found`
  (404, also for a malformed id), `conflict` (409), `file_too_large` (413),
  `unsupported_file_type` (415), `invalid_upload` (400),
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
