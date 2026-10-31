# Load test

Generated 2026-10-31 by `scripts/load_test.py`: 300 synthetic candidates in a real FAISS index and the real embedding model; MongoDB replaced by an in-memory fake; the API called in-process. 60 requests per row (the first matches rows send each job once), closed loop. CPU only, 14 cores / 20 threads.

| Endpoint | Concurrency | Requests/s | p50 ms | p95 ms | p99 ms | Errors |
|---|---|---|---|---|---|---|
| GET /api/v1/matches/{job_id}, jobs not seen before | 1 | 7.3 | 99 | 433 | 439 | 0 |
| GET /api/v1/matches/{job_id}, jobs not seen before | 4 | 7.9 | 442 | 746 | 812 | 0 |
| GET /api/v1/matches/{job_id}, jobs not seen before | 16 | 9.9 | 1399 | 1814 | 2390 | 0 |
| GET /api/v1/matches/{job_id}, jobs seen before | 1 | 11.3 | 63 | 380 | 395 | 0 |
| GET /api/v1/matches/{job_id}, jobs seen before | 4 | 11.5 | 238 | 611 | 647 | 0 |
| GET /api/v1/matches/{job_id}, jobs seen before | 16 | 12.6 | 1368 | 1622 | 1723 | 0 |
| GET /api/v1/candidates/?limit=20 | 1 | 52.4 | 12 | 23 | 354 | 0 |
| GET /api/v1/candidates/?limit=20 | 4 | 79.9 | 46 | 96 | 142 | 0 |
| GET /api/v1/candidates/?limit=20 | 16 | 98.8 | 154 | 179 | 195 | 0 |
| GET /api/v1/jobs/ | 1 | 430.3 | 2 | 3 | 3 | 0 |
| GET /api/v1/jobs/ | 4 | 402.0 | 9 | 11 | 23 | 0 |
| GET /api/v1/jobs/ | 16 | 436.3 | 34 | 48 | 52 | 0 |

Warm-up (job services and models, done at startup): 25.7 s. Peak memory of the process: 1242 MB.
