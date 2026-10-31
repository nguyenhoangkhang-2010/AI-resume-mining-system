"""
Recommends jobs to a candidate: the jobs that fit a profile best, with the
reasons.

It is the recruiter-side matching run the other way round. The candidate's
profile is embedded and the most similar jobs are fetched from the job index;
each is then scored with the same hybrid scorer (skill coverage, semantic
similarity, experience) and the same weights, so a job and a candidate get
the same score whichever of them is the query.
"""

from typing import Any, Dict, List, Optional

from loguru import logger

from app.core.exceptions import ConflictError, NotFoundError
from app.core.identifiers import parse_object_id
from app.database.mongodb.connection import mongo_db
from app.matching.embedding_text import CandidateTextBuilder
from app.matching.ranking.candidate_scorer import HybridCandidateScorer
from app.matching.ranking.ranking_config import RankingConfig
from app.matching.similarity.similarity_engine import SimilarityEngine
from app.models.candidate import CandidateModel
from app.models.job import JobModel
from app.schemas.job_match_schema import (
    JobMatch,
    JobMatchMetadata,
    JobMatchResponse,
)
from app.schemas.ranked_candidate_schema import ScoreBreakdown
from app.vector_store.job_vector_store import JobVectorStore

# Jobs are fetched this many times wider than requested, because the
# location and score filters remove some of them afterwards.
RETRIEVAL_FACTOR = 5
MIN_RETRIEVAL = 50


class JobRecommendationService:

    def __init__(
        self,
        embedding_service: Optional[Any] = None,
        job_vector_store: Optional[JobVectorStore] = None,
        scorer: Optional[HybridCandidateScorer] = None,
        config: Optional[RankingConfig] = None,
    ) -> None:
        self._embedding_service = embedding_service
        self.job_vector_store = job_vector_store or JobVectorStore()
        self.scorer = scorer or HybridCandidateScorer()
        self.config = config or RankingConfig()
        self.similarity = SimilarityEngine()
        self.text_builder = CandidateTextBuilder()

    @property
    def embedding_service(self) -> Any:
        if self._embedding_service is None:
            from app.embeddings.services.embedding_service import EmbeddingService

            self._embedding_service = EmbeddingService()

        return self._embedding_service

    @property
    def db(self):
        return mongo_db.get_db()

    @property
    def jobs_col(self):
        return self.db["jobs"]

    @property
    def candidates_col(self):
        return self.db["candidates"]

    @property
    def resumes_col(self):
        return self.db["resumes"]

    # ------------------------------------------------------------------

    def recommend_for_resume(self, resume_id: str, **options: Any) -> JobMatchResponse:
        """The same, starting from the resume a candidate uploaded."""

        object_id = parse_object_id(resume_id, "Resume")

        if not self.resumes_col.find_one({"_id": object_id}, {"_id": 1}):
            raise NotFoundError(f"Resume not found: {resume_id}")

        candidate = self.candidates_col.find_one(
            {"resume_id": str(object_id)}, {"_id": 1}
        )

        if not candidate:
            raise ConflictError(
                "This resume has no candidate profile yet: it is still being "
                "processed or could not be read. Check GET /resumes/{id}/status."
            )

        return self.recommend_for_candidate(str(candidate["_id"]), **options)

    def recommend_for_candidate(
        self,
        candidate_id: str,
        top_k: int = 10,
        min_score: Optional[float] = None,
        location: Optional[str] = None,
    ) -> JobMatchResponse:
        threshold = self.config.min_overall_score if min_score is None else min_score
        candidate = self._get_candidate(candidate_id)

        embedding = self.embedding_service.generate_embedding(
            self.text_builder.text(candidate)
        )
        hits = self.job_vector_store.search(
            embedding, top_k=max(MIN_RETRIEVAL, top_k * RETRIEVAL_FACTOR)
        )
        similarity_by_id = {hit["faiss_id"]: hit["similarity_score"] for hit in hits}
        jobs = self._get_jobs(list(similarity_by_id))

        wanted = (location or "").strip().casefold()
        matches: List[JobMatch] = []
        below = outside = 0

        for job in jobs:
            if wanted and wanted not in (job.location or "").casefold():
                outside += 1
                continue

            score = self.scorer.score(
                job=job,
                candidate=candidate,
                semantic_score=self.similarity.normalize_score(
                    similarity_by_id[job.faiss_id]  # type: ignore[index]
                ),
            )

            if score.overall_score < threshold:
                below += 1
                continue

            matches.append(self._build(job, score))

        matches.sort(key=lambda match: (-match.score, match.job_id))

        return JobMatchResponse(
            candidate_id=candidate_id,
            results=matches[:top_k],
            metadata=JobMatchMetadata(
                retrieved=len(jobs),
                ranked=min(len(matches), top_k),
                below_min_score=below,
                outside_location=outside,
                unindexed_jobs=self.jobs_col.count_documents({"faiss_id": None}),
                min_score=threshold,
            ),
        )

    # ------------------------------------------------------------------

    def _get_candidate(self, candidate_id: str) -> CandidateModel:
        object_id = parse_object_id(candidate_id, "Candidate")
        document: Optional[Dict[str, Any]] = self.candidates_col.find_one(
            {"_id": object_id}
        )

        if not document:
            raise NotFoundError(f"Candidate not found: {candidate_id}")

        return CandidateModel(**{**document, "_id": str(document["_id"])})

    def _get_jobs(self, faiss_ids: List[int]) -> List[JobModel]:
        if not faiss_ids:
            return []

        jobs = []

        for document in self.jobs_col.find({"faiss_id": {"$in": faiss_ids}}):
            try:
                jobs.append(JobModel(**{**document, "_id": str(document["_id"])}))
            except Exception as exc:
                logger.warning("A stored job could not be read and is skipped: {}", exc)

        return jobs

    @staticmethod
    def _build(job: JobModel, score: Any) -> JobMatch:
        return JobMatch(
            job_id=str(job.id),
            title=job.title,
            location=job.location,
            occupation=job.occupation,
            experience_years=job.experience_years,
            required_skills=job.required_skills,
            score=score.overall_score,
            skill_gaps=score.missing_skills,
            score_breakdown=ScoreBreakdown(
                skill_score=score.skill_score,
                semantic_score=score.semantic_score,
                experience_score=score.experience_score,
                confidence_score=score.confidence_score,
                matched_skills=score.matched_skills,
                explanation=score.explanation or {},
            ),
        )

