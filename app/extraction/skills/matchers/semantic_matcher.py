from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

import numpy as np

from app.extraction.skills.repository import SkillRepository
from app.extraction.skills.matchers.base_matcher import BaseMatcher
from app.extraction.skills.config.matching_config import MatchingConfig
from app.models.skill_match import SkillMatch


class SemanticSkillMatcher(BaseMatcher):

    def __init__(self):
        self.repository = SkillRepository()
        self.skill_objects = (
            self.repository.get_all_skill_objects()
        )

        self.model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

        self.corpus = [
            self._build_document(skill)
            for skill in self.skill_objects
        ]

        self.skill_embeddings = self.model.encode(
            self.corpus,
            convert_to_numpy=True,
            show_progress_bar=True
        )

    def find_best_match(
        self,
        query: str,
        threshold: float = MatchingConfig.SEMANTIC_MIN_SCORE,
    ):

        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True
        )

        similarities = cosine_similarity(
            query_embedding,
            self.skill_embeddings
        )[0]

        best_index = np.argmax(
            similarities
        )

        score = similarities[
            best_index
        ]

        if score < threshold:
            return None

        best_skill = self.skill_objects[
            best_index
        ]

        return (
            best_skill["name"],
            float(score)
        )

    def match_with_confidence(
        self,
        text: str,
        threshold: float = MatchingConfig.SEMANTIC_DEFAULT_THRESHOLD,
    ) -> list[SkillMatch]:

        extracted = {}

        words = text.split()

        for word in words:

            result = self.find_best_match(
                word,
                threshold,
            )

            if result:

                skill, score = result

                if (
                    skill not in extracted
                    or score > extracted[skill].confidence
                ):
                    extracted[skill] = SkillMatch(
                        skill=skill,
                        confidence=score,
                        source="semantic",
                    )

        return list(extracted.values())

    def _build_document(self, skill):
        parts = [
            skill["name"],
            skill.get("domain", ""),
            skill.get("category", "")
        ]

        parts.extend(
            skill.get("aliases", [])
        )

        return " ".join(
            part
            for part in parts
            if part
        )