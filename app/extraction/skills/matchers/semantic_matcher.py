from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
from loguru import logger
from sentence_transformers import util

from app.embeddings.models.embedding_model import EmbeddingModelSingleton
from app.extraction.skills.repository import SkillRepository
from app.extraction.skills.matchers.base_matcher import BaseMatcher
from app.extraction.skills.config.matching_config import MatchingConfig
from app.models.skill_match import SkillMatch


class SemanticSkillMatcher(BaseMatcher):

    MIN_NGRAM = 2
    MAX_NGRAM = 4

    def __init__(self):
        self.repository = SkillRepository()

        self.skill_objects = (
            self.repository.get_all_skill_objects()
        )

        embedding_singleton = EmbeddingModelSingleton()

        self.model = embedding_singleton.model

        self.corpus = [
            self._build_document(skill)
            for skill in self.skill_objects
        ]

        self.skill_embeddings = self._encode(
            self.corpus
        )

    def find_best_match(
        self,
        query: str,
        threshold: float = MatchingConfig.SEMANTIC_MIN_SCORE,
    ) -> Optional[Tuple[str, float]]:

        if not query or not query.strip():
            return None

        query_embedding = self._encode(
            [query]
        )

        similarity = util.cos_sim(
            query_embedding,
            self.skill_embeddings,
        )

        scores = self._to_numpy(similarity)[0]

        best_score, best_index, margin = self._top_match(
            scores
        )

        if best_score < threshold:
            return None

        if margin < MatchingConfig.SEMANTIC_MIN_MARGIN:
            return None

        best_skill = self.skill_objects[
            best_index
        ]

        return (
            best_skill["name"],
            best_score,
        )

    def match_with_confidence(
        self,
        text: str,
        threshold: float = MatchingConfig.SEMANTIC_DEFAULT_THRESHOLD,
    ) -> List[SkillMatch]:

        if not text or not text.strip():
            return []

        candidates = self._build_ngram_candidates(
            text
        )

        if not candidates:
            return []

        candidate_embeddings = self._encode(
            candidates
        )

        similarity = util.cos_sim(
            candidate_embeddings,
            self.skill_embeddings,
        )

        scores = self._to_numpy(similarity)

        extracted: Dict[str, SkillMatch] = {}

        for candidate_phrase, row in zip(candidates, scores):

            best_score, best_index, margin = self._top_match(
                row
            )

            if best_score < threshold:
                continue

            if margin < MatchingConfig.SEMANTIC_MIN_MARGIN:
                continue

            best_skill = self.skill_objects[
                best_index
            ]["name"]

            logger.debug(
                "Semantic match accepted: phrase='{}' -> skill='{}' "
                "(score={:.4f}, margin={:.4f})",
                candidate_phrase,
                best_skill,
                best_score,
                margin,
            )

            if (
                best_skill not in extracted
                or best_score > extracted[best_skill].confidence
            ):
                extracted[best_skill] = SkillMatch(
                    skill=best_skill,
                    confidence=best_score,
                    source="semantic",
                )

        return list(extracted.values())

    @staticmethod
    def _top_match(
        row: np.ndarray,
    ) -> Tuple[float, int, float]:

        if row.size == 0:
            return 0.0, -1, 0.0

        best_index = int(
            np.argmax(row)
        )

        best_score = float(
            row[best_index]
        )

        if row.size == 1:
            return best_score, best_index, best_score

        second_best = float(
            np.partition(row, -2)[-2]
        )

        margin = best_score - second_best

        return best_score, best_index, margin

    def _build_ngram_candidates(
        self,
        text: str,
    ) -> List[str]:

        words = text.split()

        if not words:
            return []

        candidates = set()

        for n in range(self.MIN_NGRAM, self.MAX_NGRAM + 1):

            for i in range(len(words) - n + 1):

                phrase = " ".join(
                    words[i:i + n]
                )

                phrase = phrase.strip()

                if phrase:
                    candidates.add(phrase)

        return list(candidates)

    def _encode(
        self,
        texts: List[str],
    ):

        return self.model.encode(
            texts,
            convert_to_tensor=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

    @staticmethod
    def _to_numpy(
        tensor,
    ) -> np.ndarray:

        return (
            tensor
            .detach()
            .cpu()
            .numpy()
        )

    @staticmethod
    def _build_document(skill):
        parts = [
            skill["name"],
        ]

        parts.extend(
            skill.get("aliases", [])
        )

        return " ".join(
            part
            for part in parts
            if part
        )