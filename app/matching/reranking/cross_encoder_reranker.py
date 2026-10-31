"""
Second-stage reranking of the best candidates with a cross-encoder.

The first stage (a vector search and the hybrid score) compares a job and a
profile through separately computed vectors and a few counted features. A
cross-encoder reads the job text and the profile text together, which can
tell apart things a vector cannot ("led a team" against "worked with a
team"), but it costs one model run per pair, so it is applied only to the
head of the list and its score is blended with the first-stage score rather
than replacing it.
"""

import threading
from typing import Any, Dict, List, Mapping, Optional, Protocol, Sequence, Tuple

from loguru import logger

from app.matching.embedding_text import CandidateTextBuilder, JobTextBuilder

SCORE_SCALE = 100.0


class PairScorer(Protocol):
    def score(self, pairs: Sequence[Tuple[str, str]]) -> List[float]:
        """One relevance value per (job text, candidate text) pair; higher is better."""


class CrossEncoderPairScorer:
    """A sentence-transformers cross-encoder, loaded on first use."""

    def __init__(
        self,
        model_name: str,
        batch_size: int = 16,
        max_length: int = 512,
    ) -> None:
        self.model_name = model_name
        self.batch_size = batch_size
        self.max_length = max_length
        self._model: Any = None
        self._lock = threading.Lock()

    def _load(self) -> Any:
        with self._lock:
            if self._model is None:
                from sentence_transformers import CrossEncoder

                logger.info("Loading reranker model {}", self.model_name)
                self._model = CrossEncoder(
                    self.model_name,
                    max_length=self.max_length,
                    trust_remote_code=False,
                )

        return self._model

    def score(self, pairs: Sequence[Tuple[str, str]]) -> List[float]:
        if not pairs:
            return []

        model = self._load()

        with self._lock:
            values = model.predict(
                [list(pair) for pair in pairs],
                batch_size=self.batch_size,
                show_progress_bar=False,
            )

        return [float(value) for value in values]


class CachedPairScorer:
    """Remembers the score of every pair, so repeated evaluation runs cost nothing."""

    def __init__(self, scorer: PairScorer) -> None:
        self.scorer = scorer
        self._cache: Dict[Tuple[str, str], float] = {}

    def score(self, pairs: Sequence[Tuple[str, str]]) -> List[float]:
        missing = [pair for pair in dict.fromkeys(pairs) if pair not in self._cache]

        if missing:
            for pair, value in zip(missing, self.scorer.score(missing)):
                self._cache[pair] = value

        return [self._cache[pair] for pair in pairs]


def scale_to_percent(values: Sequence[float]) -> List[float]:
    """Min-max scaling to 0..100 over the window; a window of equal values maps to 50."""

    if not values:
        return []

    low, high = min(values), max(values)

    if high == low:
        return [SCORE_SCALE / 2] * len(values)

    return [SCORE_SCALE * (value - low) / (high - low) for value in values]


def fuse_scores(
    first_stage: Sequence[float],
    cross_encoder: Sequence[float],
    weight: float,
) -> List[float]:
    """
    Blend of the first-stage score (0..100) and the cross-encoder score
    scaled to 0..100 over the same window. weight 0 keeps the first stage,
    weight 1 uses the cross-encoder alone.
    """

    if len(first_stage) != len(cross_encoder):
        raise ValueError("Both score lists need one value per candidate.")

    if not 0.0 <= weight <= 1.0:
        raise ValueError("weight must be between 0 and 1.")

    scaled = scale_to_percent(cross_encoder)

    return [
        (1.0 - weight) * base + weight * ce
        for base, ce in zip(first_stage, scaled)
    ]


class CrossEncoderReranker:
    """Reorders the first `top_n` ranked candidates; the rest keep their order below them."""

    def __init__(
        self,
        scorer: PairScorer,
        top_n: int = 50,
        weight: float = 0.25,
        candidate_text=None,
        job_text=None,
    ) -> None:
        if top_n < 1:
            raise ValueError("top_n must be at least 1.")

        self.scorer = scorer
        self.top_n = top_n
        self.weight = weight
        self.candidate_text = candidate_text or CandidateTextBuilder().text
        self.job_text = job_text or JobTextBuilder().text

    def rerank(
        self,
        job: Any,
        ranked: Sequence[Any],
        candidates: Mapping[int, Any],
    ) -> List[Any]:
        """
        `ranked` is sorted best first; `candidates[id(item)]` is the profile
        behind each item. Items get `similarity_score` set to the blended
        score and `score_breakdown.rerank_score` to the cross-encoder score
        (0..100 over the window). Returns the new order.
        """

        window = list(ranked[: self.top_n])
        tail = list(ranked[self.top_n:])

        if len(window) < 2:
            return list(ranked)

        job_text = self.job_text(job)
        pairs = [
            (job_text, self.candidate_text(candidates[id(item)]))
            for item in window
        ]

        try:
            raw = self.scorer.score(pairs)
        except Exception:
            # A failing second stage must not take the ranking down with it.
            logger.exception("Reranking failed; keeping the first-stage order.")
            return list(ranked)

        scaled = scale_to_percent(raw)
        fused = fuse_scores(
            [item.similarity_score for item in window],
            raw,
            self.weight,
        )

        for item, ce_score, score in zip(window, scaled, fused):
            item.similarity_score = round(score, 2)

            if item.score_breakdown is not None:
                item.score_breakdown.rerank_score = round(ce_score, 2)

        window.sort(key=lambda item: item.similarity_score, reverse=True)

        return window + tail


def build_reranker(
    model_name: str,
    top_n: int,
    weight: float,
    scorer: Optional[PairScorer] = None,
) -> CrossEncoderReranker:
    return CrossEncoderReranker(
        scorer or CrossEncoderPairScorer(model_name),
        top_n=top_n,
        weight=weight,
    )
