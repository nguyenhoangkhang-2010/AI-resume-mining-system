# Running with Docker

## Quick start

```bash
cp .env.example .env          # set MONGO_ROOT_PASSWORD at least
docker compose up --build
```

The API listens on `http://127.0.0.1:8000` (`/docs` for Swagger, `/health` for
status; it returns 503 while MongoDB is unreachable). MongoDB is not published
on the host. To open a shell in it:

```bash
docker compose exec mongodb mongosh -u resume_admin --authenticationDatabase admin
```

## Using the MongoDB already on your computer

`docker compose up` starts its own, empty MongoDB (with the password from
`.env`). To use the MongoDB that is already installed on your computer instead,
keeping its data and without a password if it has none, run only the API:

```bash
docker compose -f docker-compose.host-db.yml up --build -d
```

This also mounts your local `data/uploads` and `faiss_index` folders, so the
container sees the same resumes and index as a locally started server. Do not
run both at the same time: they would write the same index file. If your
MongoDB requires a login, set `MONGO_USERNAME` and `MONGO_PASSWORD` in `.env`.

## What the stack contains

| Piece | Notes |
|---|---|
| `mongodb` | `mongo:7`, root user created from `MONGO_ROOT_USER` / `MONGO_ROOT_PASSWORD`, health-checked; the API starts only after it is healthy. |
| `api` | Multi-stage image running as an unprivileged user (uid 10001) with a `/health` health check. |
| Volumes | `mongo_data`, `uploads` (`/app/data/uploads`), `faiss_data` (`/app/faiss_index`), `hf_cache` (Hugging Face models). |
| `./models` | Bind-mounted read-only at `/app/models`; put the GGUF file there for `LLM_PROVIDER=llama_cpp`. |

The first start downloads the embedding model into `hf_cache`.

## Configuration

Everything is configured through `.env` (see `.env.example`). Values set under
`environment:` in `docker-compose.yml` (Mongo connection, FAISS path) override
`.env`. The API gets the Mongo credentials as `MONGO_USERNAME` /
`MONGO_PASSWORD`, so passwords need no URL-encoding.

`docker compose config` prints the resolved configuration **including secrets
from `.env`** (for example `HF_TOKEN`); do not paste its output anywhere.

## Build options

| Build argument | Default | Purpose |
|---|---|---|
| `WITH_LLAMA_CPP` | `true` | Installs `llama-cpp-python` (compiled from source, takes many minutes). Needed for `LLM_PROVIDER=llama_cpp`. |
| `TORCH_INDEX_URL` | CPU wheels | Use `https://download.pytorch.org/whl/cu124` (or the matching CUDA version) for an NVIDIA GPU build, and also set `LLM_DEVICE` / `NER_DEVICE`. GPU use at runtime additionally requires the NVIDIA Container Toolkit and a `deploy.resources.reservations.devices` entry for the `api` service. |

```bash
docker build -f docker/Dockerfile --build-arg WITH_LLAMA_CPP=false -t ai-resume-mining .
```

## Things to know

- **Run a single worker.** The FAISS index and the model singletons live in
  process memory, so do not start uvicorn with `--workers`. Scaling out needs a
  shared vector store.
- **Authentication is on by default.** The API refuses to start until
  `API_KEYS` is set in `.env` (`role:key` pairs, keys at least 24 characters;
  generate one with `python -c "import secrets; print(secrets.token_urlsafe(32))"`).
  `AUTH_ENABLED=false` opens every endpoint and is only for a private
  development machine. Keys are read from the environment, so changing them
  needs a restart; there are no user accounts or JWT login.
- Rate limits are counted in the process memory, which is correct for the
  single worker above but resets on restart. Set `CORS_ORIGINS` to the
  origin of your frontend (for example `http://localhost:3000`) to allow
  browser access.
- Keep the port bound to `127.0.0.1` unless a reverse proxy with TLS sits in
  front: API keys are sent in headers and are readable on plain HTTP.
- `NER_TRUST_REMOTE_CODE` stays `false`: models from the Hugging Face Hub
  are not allowed to run their own Python code.
- **Memory and speed of the local model.** `LLM_PREFIX_CACHE_MB` (default
  1024) is extra memory for the model state after each prompt's fixed
  instructions, so they are read once instead of for every CV; lower it on
  a small machine or set 0 to turn it off. `EXTRACTION_RULES_FIRST` (default
  true) reads regular sections without the model; see
  [evaluation/extraction_speed_README.md](evaluation/extraction_speed_README.md).
  The model is used by one request at a time (calls are serialised).
- CV section headings the built-in vocabulary does not know ("Clinical
  Experience") are put to the language model once and the answer is kept in
  `HEADING_CACHE_PATH` (default `faiss_index/heading_cache.json`, so it lives
  in the same volume as the index). The first CV with a new heading takes a
  few seconds longer; the file can be deleted at any time.
- The rule parsers' word lists are JSON files; add a language or a field's own
  words by mounting a folder and setting `VOCABULARY_DIR` (see
  [vocabulary.md](vocabulary.md)).
- Jobs have their own vector index (`JOB_FAISS_INDEX_PATH`, default
  `faiss_index/job.index`, in the same volume as the candidate index). Jobs created
  before job recommendation existed have no vector; stop the API and run
  `docker compose exec api python -m scripts.reindex_jobs` (or run it locally)
  once to index them.
- After the embedding text changes (`EMBEDDING_VERSION`), rebuild the index;
  to check or repair it, run the operational scripts inside the stack:

  ```bash
  docker compose exec api python -m scripts.check_index_consistency
  docker compose exec api python -m scripts.reindex_candidates --dry-run
  ```

## Dependencies

`requirements.txt` holds the pinned runtime dependencies. Optional extras:
`requirements-llama.txt` (local GGUF backend), `requirements-analytics.txt`
(Streamlit dashboard) and `requirements-dev.txt` (tests, ruff, mypy).
