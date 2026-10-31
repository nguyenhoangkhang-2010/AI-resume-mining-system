"""
Load test of the read endpoints with the real models and a real FAISS index.

    python -m scripts.load_test --candidates 300 --requests 60 --out docs/evaluation/load_test.md

The API runs inside this process (httpx talks to the ASGI app directly) with
the sentence-transformer model and FAISS as in production. MongoDB is replaced
by an in-memory fake, so the numbers include everything the API does itself
(routing, validation, embedding the job, searching, scoring, serialising) and
exclude the network and the database server. They are a floor for latency on
this machine, not a forecast for a deployment.

Requests are sent closed-loop: with concurrency C, C workers each send the next
request as soon as their previous answer arrives. Nothing is written to your
databases: the candidates are synthetic, the index is a temporary file.
"""

import argparse
import asyncio
import statistics
import tempfile
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Callable, List, Sequence

import httpx
import mongomock
import psutil
from loguru import logger

from app.core.config.settings import settings


@dataclass
class Run:
    endpoint: str
    concurrency: int
    latencies: List[float] = field(default_factory=list)
    errors: int = 0
    seconds: float = 0.0

    def percentile(self, fraction: float) -> float:
        ordered = sorted(self.latencies)

        if not ordered:
            return float("nan")

        return ordered[min(len(ordered) - 1, int(fraction * len(ordered)))]

    @property
    def throughput(self) -> float:
        return len(self.latencies) / self.seconds if self.seconds else 0.0


def prepare(candidates: int, directory: Path) -> List[str]:
    """Fills the fake database and a temporary FAISS index; returns the job ids."""

    settings.FAISS_INDEX_PATH = str(directory / "candidate.index")
    settings.AUTH_ENABLED = False
    settings.RATE_LIMIT_ENABLED = False

    from app.core.constants.app_constants import EMBEDDING_VERSION
    from app.database.mongodb.connection import mongo_db
    from app.embeddings.services.embedding_service import EmbeddingService
    from app.evaluation.rankers import to_candidate_model, to_job_model
    from app.evaluation.synthetic import SyntheticDatasetGenerator
    from app.matching.embedding_text import CandidateTextBuilder
    from app.matching.skills.factory.skill_normalizer_factory import (
        create_skill_normalizer,
    )
    from app.vector_store.vector_store import VectorStore

    client = mongomock.MongoClient()
    mongo_db.client = client  # type: ignore[assignment]
    mongo_db.db = client["load_test"]

    dataset = SyntheticDatasetGenerator(seed=42, n_candidates=candidates).generate()
    normalizer = create_skill_normalizer()
    embedder = EmbeddingService()
    vectors = VectorStore()
    builder = CandidateTextBuilder()

    for index, candidate in enumerate(dataset.candidates, start=1):
        model = to_candidate_model(candidate, index, normalizer)
        model.embedding_version = EMBEDDING_VERSION
        vectors.add_candidate_embedding(index, embedder.generate_embedding(builder.text(model)))
        mongo_db.db["candidates"].insert_one(model.model_dump(by_alias=True, exclude={"id"}))

    job_ids = []

    for job in dataset.jobs:
        document = to_job_model(job, normalizer).model_dump(by_alias=True, exclude={"id"})
        job_ids.append(str(mongo_db.db["jobs"].insert_one(document).inserted_id))

    return job_ids


async def drive(
    client: httpx.AsyncClient,
    endpoint: str,
    make_path: Callable[[int], str],
    total: int,
    concurrency: int,
) -> Run:
    run = Run(endpoint, concurrency)
    counter = iter(range(total))

    async def worker() -> None:
        for number in counter:
            started = time.perf_counter()
            response = await client.get(make_path(number))
            run.latencies.append(time.perf_counter() - started)

            if response.status_code != 200:
                run.errors += 1

    started = time.perf_counter()
    await asyncio.gather(*(worker() for _ in range(concurrency)))
    run.seconds = time.perf_counter() - started

    return run


async def run_all(job_ids: Sequence[str], total: int, levels: Sequence[int]) -> List[Run]:
    from app.embeddings.services.embedding_service import embedding_cache
    from app.main import app

    runs: List[Run] = []
    transport = httpx.ASGITransport(app=app)

    def match(n: int) -> str:
        return f"/api/v1/matches/{job_ids[n % len(job_ids)]}"

    async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=300) as client:
        # (endpoint, path, requests, empty the embedding cache first)
        workloads = [
            ("GET /api/v1/matches/{job_id}, jobs not seen before", match, len(job_ids), True),
            ("GET /api/v1/matches/{job_id}, jobs seen before", match, total, False),
            ("GET /api/v1/candidates/?limit=20", lambda n: f"/api/v1/candidates/?limit=20&offset={(n % 5) * 20}", total, False),
            ("GET /api/v1/jobs/", lambda n: "/api/v1/jobs/", total, False),
        ]

        for endpoint, path, count, cold in workloads:
            for concurrency in levels:
                if cold:
                    embedding_cache.clear()

                runs.append(await drive(client, endpoint, path, count, concurrency))
                print(
                    f"{endpoint} c={concurrency}: "
                    f"{runs[-1].throughput:.1f} req/s, p95 {runs[-1].percentile(0.95) * 1000:.0f} ms, "
                    f"{runs[-1].errors} errors",
                    flush=True,
                )

    return runs


def report(runs: Sequence[Run], candidates: int, total: int, peak_mb: float, warm_seconds: float) -> str:
    lines = [
        "# Load test",
        "",
        f"Generated {date.today().isoformat()} by `scripts/load_test.py`: {candidates} synthetic "
        f"candidates in a real FAISS index and the real embedding model; MongoDB replaced by an "
        f"in-memory fake; the API called in-process. {total} requests per row (the first matches rows send each job once), closed loop. "
        f"CPU only, {psutil.cpu_count(logical=False)} cores / {psutil.cpu_count()} threads.",
        "",
        "| Endpoint | Concurrency | Requests/s | p50 ms | p95 ms | p99 ms | Errors |",
        "|---|---|---|---|---|---|---|",
    ]

    for run in runs:
        lines.append(
            f"| {run.endpoint} | {run.concurrency} | {run.throughput:.1f} | "
            f"{statistics.median(run.latencies) * 1000:.0f} | {run.percentile(0.95) * 1000:.0f} | "
            f"{run.percentile(0.99) * 1000:.0f} | {run.errors} |"
        )

    lines += [
        "",
        f"Warm-up (job services and models, done at startup): {warm_seconds:.1f} s. "
        f"Peak memory of the process: {peak_mb:.0f} MB.",
        "",
    ]

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=int, default=300)
    parser.add_argument("--requests", type=int, default=60)
    parser.add_argument("--concurrency", default="1,4,16")
    parser.add_argument("--out", default="docs/evaluation/load_test.md")
    args = parser.parse_args()

    logger.remove()

    levels = [int(level) for level in args.concurrency.split(",")]

    with tempfile.TemporaryDirectory() as directory:
        job_ids = prepare(args.candidates, Path(directory))

        from app.bootstrap import warm_up

        started = time.perf_counter()
        warm_up()
        warm_seconds = time.perf_counter() - started

        runs = asyncio.run(run_all(job_ids, args.requests, levels))

    peak_mb = psutil.Process().memory_info().rss / 1024 / 1024

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report(runs, args.candidates, args.requests, peak_mb, warm_seconds), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
