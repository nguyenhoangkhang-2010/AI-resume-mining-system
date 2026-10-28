import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class EvalJob:
    id: str
    title: str
    family: str
    description: str
    required_skills: List[str]
    experience_years: Optional[int] = None


@dataclass
class EvalExperience:
    role: str
    company: str
    start_date: str
    end_date: str
    description: List[str] = field(default_factory=list)


@dataclass
class EvalCandidate:
    id: str
    title: str
    summary: str
    skills: List[str]
    experience: List[EvalExperience] = field(default_factory=list)

    # Latent attributes used only to derive relevance labels. Rankers
    # must never read them.
    meta: Dict[str, object] = field(default_factory=dict)

    @property
    def text(self) -> str:
        """Free-text view of the profile, as a keyword search would see it."""

        parts = [self.title, self.summary, " ".join(self.skills)]

        for item in self.experience:
            parts.append(item.role)
            parts.extend(item.description)

        return "\n".join(part for part in parts if part)


@dataclass
class ExtractionDocument:
    id: str
    text: str
    gold_skills: List[str]


@dataclass
class EvalDataset:
    jobs: List[EvalJob]
    candidates: List[EvalCandidate]

    # relevance label sets: name -> job_id -> candidate_id -> grade (0-3)
    qrels: Dict[str, Dict[str, Dict[str, int]]]

    extraction_documents: List[ExtractionDocument] = field(default_factory=list)

    seed: Optional[int] = None

    def save(self, directory: str | Path) -> None:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

        payload = {
            "jobs.json": [asdict(job) for job in self.jobs],
            "candidates.json": [asdict(c) for c in self.candidates],
            "qrels.json": self.qrels,
            "extraction_documents.json": [
                asdict(doc) for doc in self.extraction_documents
            ],
            "manifest.json": {
                "seed": self.seed,
                "jobs": len(self.jobs),
                "candidates": len(self.candidates),
                "extraction_documents": len(self.extraction_documents),
                "qrels": sorted(self.qrels),
            },
        }

        for name, content in payload.items():
            (directory / name).write_text(
                json.dumps(content, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

    @classmethod
    def load(cls, directory: str | Path) -> "EvalDataset":
        directory = Path(directory)

        def read(name: str):
            return json.loads(
                (directory / name).read_text(encoding="utf-8")
            )

        candidates = []

        for item in read("candidates.json"):
            item["experience"] = [
                EvalExperience(**entry) for entry in item["experience"]
            ]
            candidates.append(EvalCandidate(**item))

        manifest = read("manifest.json")

        extraction_path = directory / "extraction_documents.json"

        documents = (
            [ExtractionDocument(**doc) for doc in read("extraction_documents.json")]
            if extraction_path.exists()
            else []
        )

        return cls(
            jobs=[EvalJob(**item) for item in read("jobs.json")],
            candidates=candidates,
            qrels=read("qrels.json"),
            extraction_documents=documents,
            seed=manifest.get("seed"),
        )
