from app.matching.ranking.ranking_filter import RankingFilter
from app.matching.ranking.ranking_builder import RankingBuilder
from app.matching.similarity.similarity_engine import SimilarityEngine
from app.matching.recommendation.recommendation_engine import RecommendationEngine


class RankingPipeline:

    def __init__(
        self,
        similarity_engine=None,
        recommendation_engine=None,
        ranking_filter=None,
        ranking_builder=None,
    ):
        self.similarity_engine = (
            similarity_engine
            or SimilarityEngine()
        )

        self.recommendation_engine = (
            recommendation_engine
            or RecommendationEngine()
        )

        self.ranking_filter = (
            ranking_filter
            or RankingFilter()
        )

        self.ranking_builder = (
            ranking_builder
            or RankingBuilder()
        )

    def process(
        self,
        job,
        candidates,
        score_map,
    ):

        ranked_list = []

        for candidate in candidates:

            if candidate.faiss_id not in score_map:
                continue

            raw_score = score_map[candidate.faiss_id]

            if not self.ranking_filter.accept(raw_score):
                continue

            normalized_score = (
                self.similarity_engine.normalize_score(
                    raw_score
                )
            )

            skill_gaps = (
                self.recommendation_engine.analyze_skill_gaps(
                    required_skills=job.required_skills,
                    candidate_skills=candidate.skills,
                )
            )

            ranked_candidate = self.ranking_builder.build(
                candidate=candidate,
                similarity_score=normalized_score,
                skill_gaps=skill_gaps,
            )

            ranked_list.append(
                ranked_candidate
            )

        return ranked_list