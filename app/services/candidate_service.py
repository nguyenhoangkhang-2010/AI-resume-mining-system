from typing import Any, Dict, Optional

from pymongo.collation import Collation

from app.core.exceptions import NotFoundError
from app.core.identifiers import parse_object_id
from app.database.mongodb.connection import mongo_db
from app.models.candidate import CandidateModel
from app.schemas.candidate_schema import CandidateResponse, CandidateSummary
from app.schemas.page import Page

SUMMARY_SKILLS = 10

# Skill filters ignore case ("Python" finds "python").
CASE_INSENSITIVE = Collation(locale="en", strength=2)


def summarize(document: Dict[str, Any]) -> CandidateSummary:
    skills = document.get("normalized_skills") or document.get("skills") or []
    personal = document.get("personal_info") or {}

    return CandidateSummary(
        id=str(document["_id"]),
        resume_id=str(document.get("resume_id", "")),
        full_name=personal.get("full_name"),
        skills=skills[:SUMMARY_SKILLS],
        skill_count=len(skills),
        experience_entries=len(document.get("experience") or []),
        created_at=document.get("created_at"),
    )


class CandidateService:
    """Listing and reading candidates."""

    @property
    def candidates_col(self):
        return mongo_db.get_db()["candidates"]

    def list_candidates(
        self,
        skill: Optional[str],
        limit: int,
        offset: int,
    ) -> Page[CandidateSummary]:

        query: Dict[str, Any] = (
            {"normalized_skills": skill.strip()} if skill and skill.strip() else {}
        )

        options: Dict[str, Any] = {"collation": CASE_INSENSITIVE} if query else {}

        documents = (
            self.candidates_col.find(query, **options)
            .sort([("created_at", -1), ("_id", -1)])
            .skip(offset)
            .limit(limit)
        )

        return Page[CandidateSummary](
            items=[summarize(document) for document in documents],
            total=self.candidates_col.count_documents(query, **options),
            limit=limit,
            offset=offset,
        )

    def get_candidate(self, candidate_id: str) -> CandidateResponse:
        object_id = parse_object_id(candidate_id, "Candidate")

        document = self.candidates_col.find_one({"_id": object_id})

        if not document:
            raise NotFoundError(f"Candidate not found: {candidate_id}")

        document["_id"] = str(document["_id"])

        return CandidateResponse.model_validate(CandidateModel(**document))
