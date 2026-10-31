"""
Records the answers of the real API on synthetic data for the demo site.

    python -m scripts.make_demo_fixtures

The API runs in this process with the real models, a real FAISS index and the
real CV pipeline (without the language model, so it runs anywhere); only
MongoDB is an in-memory fake. Four sample CVs go through the same
`ResumeService.process_resume` as an upload; jobs and candidates are the
synthetic evaluation data with invented names. The answers of the endpoints the
interface calls are written to frontend/src/demo/fixtures.json, so the demo
shows real outputs, not hand-written ones, and contains no real person.

The output is deterministic apart from tiny floating-point differences.
"""

import argparse
import asyncio
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import fitz
import httpx
import mongomock
from bson import ObjectId
from loguru import logger

from app.core.config.settings import settings

TARGET = Path("frontend/src/demo/fixtures.json")

FIRST = ["Linh", "Minh", "An", "Thu", "Bao", "Mai", "Khoa", "Lan", "Duc", "Hoa", "Nam", "Vy"]
LAST = ["Tran", "Nguyen", "Le", "Pham", "Hoang", "Vu", "Dang", "Bui", "Do", "Ngo"]

PRESET_QUERIES = [
    "backend engineer who knows Kubernetes and PostgreSQL",
    "machine learning engineer with PyTorch and NLP experience",
    "frontend developer with React and TypeScript",
    "someone to run our CI/CD and cloud infrastructure",
]

TOP_MATCHES = 10
BASE_TIME = datetime(2026, 1, 5, 9, 0, 0)


def oid(kind: int, number: int) -> ObjectId:
    """Stable ids, so a re-run changes only what really changed."""

    return ObjectId(f"{kind:02x}{number:022x}")


def invented_name(index: int) -> str:
    return f"{LAST[index % len(LAST)]} {FIRST[(index * 7) % len(FIRST)]} {FIRST[(index * 5 + 3) % len(FIRST)]}"


def scanned_pdf(path: Path) -> None:
    """A page that is only a picture: there is no text to read without OCR."""

    pixmap = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 400, 500), False)
    pixmap.set_rect(pixmap.irect, (235, 235, 235))

    with fitz.open() as document:
        document.new_page().insert_image(fitz.Rect(30, 30, 565, 810), pixmap=pixmap)
        document.save(str(path))


def sample_pdfs(directory: Path) -> List[Dict[str, Any]]:
    from app.evaluation.cv_industries import IndustryCorpusBuilder

    wanted = [
        ("software", "single", "en", "cv_software_engineer.pdf", "Software engineer",
         "English, one column, standard headings: read by rules."),
        ("software", "two_column", "vi", "cv_software_vietnamese.pdf", "Software engineer, in Vietnamese",
         "Vietnamese with accents, a sidebar and a main column."),
        ("healthcare", "two_column", "vi", "cv_nurse_vietnamese.pdf", "Nurse, in Vietnamese",
         "A field with no matching job in the demo, and a layout the rules read only in part."),
    ]
    samples = []

    for industry, layout, language, filename, label, description in wanted:
        documents = IndustryCorpusBuilder(
            seed=3, industries=[industry], layouts=[layout], wordings=("industry",)
        ).build(directory / f"{industry}_{layout}")
        source = next(d for d in documents if d.language == language)
        target = directory / filename
        target.write_bytes(source.path.read_bytes())
        samples.append({"filename": filename, "path": target, "label": label, "description": description})

    scan = directory / "cv_scanned_no_text.pdf"
    scanned_pdf(scan)
    samples.append(
        {
            "filename": scan.name,
            "path": scan,
            "label": "A scanned CV",
            "description": "Only a picture, no text layer: without OCR it is held for review, not guessed at.",
        }
    )

    return samples


def seed(database: Any, candidates: int, directory: Path) -> None:
    from app.core.constants.app_constants import EMBEDDING_VERSION
    from app.embeddings.services.embedding_service import EmbeddingService
    from app.evaluation.rankers import to_candidate_model, to_job_model
    from app.evaluation.synthetic import SyntheticDatasetGenerator
    from app.matching.embedding_text import CandidateTextBuilder
    from app.matching.skills.factory.skill_normalizer_factory import create_skill_normalizer
    from app.models.candidate import PersonalInfo
    from app.services.job_indexer import JobIndexer
    from app.vector_store.vector_store import VectorStore

    dataset = SyntheticDatasetGenerator(seed=11, n_candidates=candidates, jobs_per_family=2).generate()
    normalizer = create_skill_normalizer()
    embedder = EmbeddingService()
    vectors = VectorStore()
    builder = CandidateTextBuilder()

    for index, candidate in enumerate(dataset.candidates, start=1):
        model = to_candidate_model(candidate, index, normalizer)
        model.personal_info = PersonalInfo(full_name=invented_name(index))
        model.embedding_version = EMBEDDING_VERSION
        vectors.add_candidate_embedding(index, embedder.generate_embedding(builder.text(model)))
        document = model.model_dump(by_alias=True, exclude={"id"})
        document["_id"] = oid(2, index)
        document["created_at"] = BASE_TIME + timedelta(minutes=index)
        database["candidates"].insert_one(document)

    indexer = JobIndexer()

    for index, job in enumerate(dataset.jobs, start=1):
        model = to_job_model(job, normalizer)
        model.location = ["Ha Noi", "Ho Chi Minh City", "Da Nang", "Remote"][index % 4]
        model.faiss_id = indexer.index(database, model)
        document = model.model_dump(by_alias=True, exclude={"id"})
        document["_id"] = oid(3, index)
        document["created_at"] = BASE_TIME + timedelta(hours=index)
        database["jobs"].insert_one(document)


def process_samples(database: Any, samples: List[Dict[str, Any]]) -> None:
    from app.evaluation.pipeline_factory import NoModel, build_pipeline
    from app.services.resume_service import ResumeService

    service = ResumeService(resume_pipeline=build_pipeline(NoModel()))

    for number, sample in enumerate(samples, start=1):
        resume_id = oid(1, number)
        sample["id"] = str(resume_id)
        database["resumes"].insert_one(
            {
                "_id": resume_id,
                "filename": sample["filename"],
                "file_path": str(sample["path"]),
                "upload_status": "pending",
                "created_at": BASE_TIME + timedelta(days=1, minutes=number),
            }
        )
        service.process_resume(str(resume_id))


async def record(samples: List[Dict[str, Any]], job_ids: List[str]) -> Dict[str, Any]:
    from app.main import app

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://demo", timeout=300) as client:

        async def get(path: str) -> Any:
            response = await client.get(path)
            response.raise_for_status()

            return response.json()

        jobs = await get("/api/v1/jobs/?limit=50")
        matches = {}

        for job_id in job_ids:
            match = await get(f"/api/v1/matches/{job_id}")
            match["results"] = match["results"][:TOP_MATCHES]
            matches[job_id] = match

        searches = {}

        for query in PRESET_QUERIES:
            response = await client.post("/api/v1/search/candidates", json={"query": query, "top_k": 6})
            response.raise_for_status()
            searches[query] = response.json()

        recorded = []

        for sample in samples:
            status = await get(f"/api/v1/resumes/{sample['id']}/status")
            recommended = None

            if status["status"] == "processed":
                recommended = await get(f"/api/v1/resumes/{sample['id']}/jobs?top_k=6")

            recorded.append(
                {
                    "id": sample["id"],
                    "label": sample["label"],
                    "description": sample["description"],
                    "filename": sample["filename"],
                    "status": status,
                    "jobs": recommended,
                }
            )

        resumes = await get("/api/v1/resumes/?limit=50")

    return {
        "generated": "recorded from the real API on synthetic data",
        "jobs": jobs,
        "matches": matches,
        "searches": searches,
        "resumes": resumes,
        "samples": recorded,
    }


CONTACT_FIELDS = ("email", "phone", "linkedin", "github")


def without_contact_details(value: Any) -> Any:
    """Even invented contact details are left out of what is published."""

    if isinstance(value, dict):
        return {
            key: (
                {k: (None if k in CONTACT_FIELDS else v) for k, v in item.items()}
                if key == "personal_info" and isinstance(item, dict)
                else without_contact_details(item)
            )
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [without_contact_details(item) for item in value]

    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=int, default=60)
    parser.add_argument("--out", default=str(TARGET))
    args = parser.parse_args()

    logger.remove()

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        settings.FAISS_INDEX_PATH = str(root / "candidate.index")
        settings.JOB_FAISS_INDEX_PATH = str(root / "job.index")
        settings.AUTH_ENABLED = False
        settings.RATE_LIMIT_ENABLED = False

        from app.database.mongodb.connection import mongo_db

        client = mongomock.MongoClient()
        mongo_db.client = client  # type: ignore[assignment]
        mongo_db.db = client["demo"]

        samples = sample_pdfs(root)
        seed(mongo_db.db, args.candidates, root)
        process_samples(mongo_db.db, samples)

        job_ids = [str(job["_id"]) for job in mongo_db.db["jobs"].find().sort("created_at", 1)]
        fixtures = without_contact_details(asyncio.run(record(samples, job_ids)))

    out = Path(args.out)
    out.write_text(json.dumps(fixtures, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
