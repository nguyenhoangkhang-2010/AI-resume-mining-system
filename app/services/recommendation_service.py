from typing import List

from app.core.exceptions import NotFoundError
from app.core.identifiers import parse_object_id
from app.database.mongodb.connection import mongo_db
from app.matching.scoring.skill_overlap_scorer import SkillOverlapScorer
from app.models.candidate import CandidateModel
from app.models.job import JobModel
from app.schemas.recommendation_schema import (
    RecommendationItem,
    SkillRecommendations,
)


class RecommendationService:
    """What a candidate is missing for a job, and how to close the gap."""

    def __init__(self, engine):
        self.engine = engine
        self.overlap = SkillOverlapScorer()

    def recommend(self, job_id: str, candidate_id: str) -> SkillRecommendations:
        db = mongo_db.get_db()

        job_oid = parse_object_id(job_id, "Job")
        candidate_oid = parse_object_id(candidate_id, "Candidate")

        job_document = db["jobs"].find_one({"_id": job_oid})

        if not job_document:
            raise NotFoundError(f"Job not found: {job_id}")

        candidate_document = db["candidates"].find_one({"_id": candidate_oid})

        if not candidate_document:
            raise NotFoundError(f"Candidate not found: {candidate_id}")

        job_document["_id"] = str(job_document["_id"])
        candidate_document["_id"] = str(candidate_document["_id"])

        job = JobModel(**job_document)
        candidate = CandidateModel(**candidate_document)

        required = job.normalized_skills or job.required_skills
        owned = [*candidate.normalized_skills, *candidate.skills]

        missing = self.overlap.score(required, owned).missing

        if not missing:
            return SkillRecommendations(
                job_id=job_id,
                candidate_id=candidate_id,
                missing_skills=[],
                recommendations=[],
            )

        response = self.engine.recommend(required, owned)

        return SkillRecommendations(
            job_id=job_id,
            candidate_id=candidate_id,
            missing_skills=missing,
            recommendations=self._unique(response.recommendations),
        )

    @staticmethod
    def _unique(items: List[RecommendationItem]) -> List[RecommendationItem]:
        seen = set()
        result = []

        for item in items:
            key = (item.type, item.title.casefold())

            if key in seen:
                continue

            seen.add(key)
            result.append(item)

        return result
