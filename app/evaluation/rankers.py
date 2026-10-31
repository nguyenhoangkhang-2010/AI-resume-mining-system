import math
import re
import zlib
from collections import Counter
from typing import Dict, List, Protocol, Sequence

import numpy as np

from app.evaluation.pooling import ProfileEmbedder
from app.evaluation.dataset import EvalCandidate, EvalDataset, EvalJob
from app.matching.embedding_text import CandidateTextBuilder, JobTextBuilder
from app.matching.ranking.candidate_scorer import HybridCandidateScorer
from app.matching.reranking.cross_encoder_reranker import PairScorer, fuse_scores
from app.matching.scoring.skill_overlap_scorer import SkillOverlapScorer
from app.matching.similarity.similarity_engine import SimilarityEngine
from app.models.candidate import CandidateModel, Experience, PersonalInfo
from app.models.job import JobModel


TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9+#./-]*")


def tokenize(text: str) -> List[str]:
    return [
        token.rstrip(".,-/")
        for token in TOKEN_PATTERN.findall(text.lower())
        if token.rstrip(".,-/")
    ]


# ---------------------------------------------------------------- embeddings


class Embedder(Protocol):
    def encode(self, texts: Sequence[str]) -> np.ndarray:
        """Returns L2-normalised vectors, one row per text."""


class HashingEmbedder:
    """
    Deterministic bag-of-words embedder (feature hashing). It needs no
    model download, so it keeps tests and quick offline runs cheap, but it
    is not a semantic model.
    """

    def __init__(self, dimension: int = 256):
        self.dimension = dimension

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        matrix = np.zeros((len(texts), self.dimension), dtype=np.float32)

        for row, text in enumerate(texts):
            for token, count in Counter(tokenize(text)).items():
                column = zlib.crc32(token.encode("utf-8")) % self.dimension
                matrix[row, column] += count

        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0

        return matrix / norms


class ServiceEmbedder:
    """
    The project's real sentence-transformer model, loaded on first use.
    """

    def __init__(self):
        self._service = None

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        if self._service is None:
            from app.embeddings.services.embedding_service import (
                EmbeddingService,
            )

            self._service = EmbeddingService()

        return self._service.generate_batch_embeddings(list(texts))


class CachedEmbedder:
    """
    Memoises embeddings by text so rankers that embed the same strings
    do not pay for them twice.
    """

    def __init__(self, embedder: Embedder):
        self.embedder = embedder
        self._cache: Dict[str, np.ndarray] = {}

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        missing = [t for t in dict.fromkeys(texts) if t not in self._cache]

        if missing:
            for text, vector in zip(missing, self.embedder.encode(missing)):
                self._cache[text] = vector

        return np.stack([self._cache[text] for text in texts])


# --------------------------------------------------------------- adapters


def to_job_model(job: EvalJob, normalizer) -> JobModel:
    return JobModel(
        title=job.title,
        description=job.description,
        raw_text=job.description,
        required_skills=list(job.required_skills),
        normalized_skills=list(
            dict.fromkeys(
                normalizer.normalize(skill) for skill in job.required_skills
            )
        ),
        experience_years=job.experience_years,
    )


def to_candidate_model(
    candidate: EvalCandidate,
    index: int,
    normalizer,
) -> CandidateModel:

    skills = [skill.lower().strip() for skill in candidate.skills]

    return CandidateModel(
        resume_id=candidate.id,
        personal_info=PersonalInfo(full_name=candidate.full_name or None),
        summary=candidate.summary,
        skills=skills,
        normalized_skills=list(
            dict.fromkeys(normalizer.normalize(skill) for skill in skills)
        ),
        experience=[
            Experience(
                role=entry.role,
                company=entry.company,
                start_date=entry.start_date,
                end_date=entry.end_date,
                description=list(entry.description),
            )
            for entry in candidate.experience
        ],
        faiss_id=index,
    )


# ------------------------------------------------------------------ rankers


class Ranker:
    name = "ranker"

    def prepare(self, dataset: EvalDataset) -> None:
        self.dataset = dataset

    def scores(self, job: EvalJob) -> Dict[str, float]:
        raise NotImplementedError

    def rank(self, job: EvalJob) -> List[str]:
        scores = self.scores(job)

        return [
            candidate_id
            for candidate_id, _ in sorted(
                scores.items(),
                key=lambda item: (-item[1], item[0]),
            )
        ]


class BM25Ranker(Ranker):
    """Okapi BM25 over the free text of each profile."""

    name = "bm25"

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

    def prepare(self, dataset: EvalDataset) -> None:
        super().prepare(dataset)

        self.ids = [c.id for c in dataset.candidates]
        self.term_counts = [
            Counter(tokenize(c.text)) for c in dataset.candidates
        ]
        self.lengths = [sum(c.values()) for c in self.term_counts]
        self.average_length = sum(self.lengths) / len(self.lengths)

        document_frequency: Counter = Counter()
        for counts in self.term_counts:
            document_frequency.update(counts.keys())

        total = len(self.ids)
        self.idf = {
            term: math.log(1 + (total - df + 0.5) / (df + 0.5))
            for term, df in document_frequency.items()
        }

    def scores(self, job: EvalJob) -> Dict[str, float]:
        query_terms = set(tokenize(job.description))

        result = {}

        for candidate_id, counts, length in zip(
            self.ids, self.term_counts, self.lengths
        ):
            score = 0.0

            for term in query_terms:
                frequency = counts.get(term, 0)

                if not frequency:
                    continue

                denominator = frequency + self.k1 * (
                    1 - self.b + self.b * length / self.average_length
                )

                score += self.idf[term] * frequency * (self.k1 + 1) / denominator

            result[candidate_id] = score

        return result


class TfidfRanker(Ranker):
    """Cosine similarity between TF-IDF vectors of job and profile text."""

    name = "tfidf"

    def prepare(self, dataset: EvalDataset) -> None:
        from sklearn.feature_extraction.text import TfidfVectorizer

        super().prepare(dataset)

        self.ids = [c.id for c in dataset.candidates]
        self.vectorizer = TfidfVectorizer(
            tokenizer=tokenize,
            lowercase=False,
            token_pattern=None,
        )
        self.matrix = self.vectorizer.fit_transform(
            [c.text for c in dataset.candidates]
        )

    def scores(self, job: EvalJob) -> Dict[str, float]:
        query = self.vectorizer.transform([job.description])
        similarities = (self.matrix @ query.T).toarray().ravel()

        return dict(zip(self.ids, similarities.tolist()))


class SkillOverlapRanker(Ranker):
    """Share of the job's required skills present in the profile."""

    name = "skill_overlap"

    def __init__(self, normalizer):
        self.normalizer = normalizer
        self.scorer = SkillOverlapScorer()

    def prepare(self, dataset: EvalDataset) -> None:
        super().prepare(dataset)

        self.candidates = [
            to_candidate_model(c, index, self.normalizer)
            for index, c in enumerate(dataset.candidates)
        ]

    def scores(self, job: EvalJob) -> Dict[str, float]:
        job_model = to_job_model(job, self.normalizer)

        result = {}

        for candidate in self.candidates:
            overlap = self.scorer.score(
                job_model.normalized_skills,
                [*candidate.normalized_skills, *candidate.skills],
            )

            result[candidate.resume_id] = overlap.score or 0.0

        return result


class SemanticRanker(Ranker):
    """
    Cosine similarity of embeddings.

    mode="skills" mirrors the production system, which embeds only the
    skill list. mode="fulltext" embeds the whole profile against the whole
    job description.
    """

    def __init__(self, embedder: Embedder, normalizer, mode: str = "skills"):
        if mode not in {"skills", "fulltext"}:
            raise ValueError(f"Unknown semantic mode: {mode}")

        self.embedder = embedder
        self.normalizer = normalizer
        self.mode = mode
        self.name = f"semantic_{mode}"

    def prepare(self, dataset: EvalDataset) -> None:
        super().prepare(dataset)

        self.ids = [c.id for c in dataset.candidates]

        if self.mode == "skills":
            texts = [
                " ".join(
                    to_candidate_model(c, i, self.normalizer).normalized_skills
                )
                for i, c in enumerate(dataset.candidates)
            ]
        else:
            texts = [c.text for c in dataset.candidates]

        self.matrix = self.embedder.encode(texts)

    def job_text(self, job: EvalJob) -> str:
        if self.mode == "skills":
            return " ".join(job.required_skills)

        return job.description

    def cosine_scores(self, job: EvalJob) -> np.ndarray:
        query = self.embedder.encode([self.job_text(job)])[0]

        return self.matrix @ query

    def scores(self, job: EvalJob) -> Dict[str, float]:
        return dict(zip(self.ids, self.cosine_scores(job).tolist()))


class ProfileSemanticRanker(Ranker):
    """
    Cosine similarity of embeddings built from the production profile
    text (roles, summary, skills, experience bullets, projects) and job
    text (title, skills, responsibilities).

    pooled=True embeds each section separately and averages the vectors;
    pooled=False embeds one concatenated string, which the model truncates
    at 128 tokens.
    """

    def __init__(self, embedder: Embedder, normalizer, pooled: bool = True):
        self.embedder = embedder
        self.normalizer = normalizer
        self.pooled = pooled
        self.profile_embedder = ProfileEmbedder(embedder)
        self.candidate_builder = CandidateTextBuilder()
        self.job_builder = JobTextBuilder()
        self.name = (
            "semantic_profile_pooled" if pooled else "semantic_profile_concat"
        )

    def prepare(self, dataset: EvalDataset) -> None:
        super().prepare(dataset)

        self.ids = [c.id for c in dataset.candidates]

        candidates = [
            to_candidate_model(c, index, self.normalizer)
            for index, c in enumerate(dataset.candidates)
        ]

        if self.pooled:
            self.matrix = self.profile_embedder.embed_many(
                [self.candidate_builder.sections(c) for c in candidates]
            )
        else:
            self.matrix = self.embedder.encode(
                [self.candidate_builder.text(c) for c in candidates]
            )

    def cosine_scores(self, job: EvalJob) -> np.ndarray:
        job_model = to_job_model(job, self.normalizer)

        if self.pooled:
            query = self.profile_embedder.embed(
                self.job_builder.sections(job_model)
            )
        else:
            query = self.embedder.encode([self.job_builder.text(job_model)])[0]

        return self.matrix @ query

    def scores(self, job: EvalJob) -> Dict[str, float]:
        return dict(zip(self.ids, self.cosine_scores(job).tolist()))


class HybridRanker(Ranker):
    """
    The production scoring path: skill coverage, semantic similarity and
    experience, via HybridCandidateScorer. No minimum-score filter is
    applied so every candidate receives a rank.

    `semantic` is the ranker that supplies cosine similarities; by default
    the profile-text embedding used in production (pass a skills-only
    SemanticRanker to reproduce the earlier behaviour).
    """

    def __init__(
        self,
        embedder: Embedder,
        normalizer,
        use_experience: bool = True,
        semantic=None,
        name: str | None = None,
    ):
        self.semantic = semantic or ProfileSemanticRanker(
            embedder, normalizer, pooled=False
        )
        self.normalizer = normalizer
        self.use_experience = use_experience
        self.scorer = HybridCandidateScorer()
        self.similarity = SimilarityEngine()
        self.name = name or (
            "hybrid" if use_experience else "hybrid_no_experience"
        )

    def prepare(self, dataset: EvalDataset) -> None:
        super().prepare(dataset)

        self.semantic.prepare(dataset)

        self.candidates = [
            to_candidate_model(c, index, self.normalizer)
            for index, c in enumerate(dataset.candidates)
        ]

    def scores(self, job: EvalJob) -> Dict[str, float]:
        job_model = to_job_model(job, self.normalizer)

        if not self.use_experience:
            job_model.experience_years = None

        cosines = self.semantic.cosine_scores(job)

        result = {}

        for candidate, cosine in zip(self.candidates, cosines):
            matching = self.scorer.score(
                job=job_model,
                candidate=candidate,
                semantic_score=self.similarity.normalize_score(float(cosine)),
            )

            result[candidate.resume_id] = matching.overall_score

        return result


class RerankedRanker(Ranker):
    """
    A first-stage ranker whose best `top_n` candidates are reordered by a
    cross-encoder blended with the first-stage score, as the production
    reranker does (CrossEncoderReranker). Candidates below the window keep
    their first-stage order.
    """

    def __init__(
        self,
        base: Ranker,
        pair_scorer: PairScorer,
        normalizer,
        top_n: int = 50,
        weight: float = 0.5,
        name: str | None = None,
    ):
        self.base = base
        self.pair_scorer = pair_scorer
        self.normalizer = normalizer
        self.top_n = top_n
        self.weight = weight
        self.candidate_builder = CandidateTextBuilder()
        self.job_builder = JobTextBuilder()
        self.name = name or f"{base.name}+rerank(w={weight:g},n={top_n})"

    def prepare(self, dataset: EvalDataset) -> None:
        super().prepare(dataset)

        self.base.prepare(dataset)

        self.texts = {
            candidate.id: self.candidate_builder.text(
                to_candidate_model(candidate, index, self.normalizer)
            )
            for index, candidate in enumerate(dataset.candidates)
        }

    def scores(self, job: EvalJob) -> Dict[str, float]:
        base_scores = self.base.scores(job)

        ordered = sorted(base_scores, key=lambda cid: (-base_scores[cid], cid))
        window, tail = ordered[: self.top_n], ordered[self.top_n:]

        job_text = self.job_builder.text(to_job_model(job, self.normalizer))
        raw = self.pair_scorer.score([(job_text, self.texts[cid]) for cid in window])
        fused = fuse_scores([base_scores[cid] for cid in window], raw, self.weight)

        result = dict(zip(window, fused))

        # Everything below the window stays below it.
        floor = min(fused, default=0.0) - 1.0
        lowest = max((base_scores[cid] for cid in tail), default=0.0)

        for cid in tail:
            result[cid] = floor - (lowest - base_scores[cid])

        return result


def build_default_rankers(embedder: Embedder, normalizer) -> List[Ranker]:
    embedder = CachedEmbedder(embedder)

    return [
        BM25Ranker(),
        TfidfRanker(),
        SkillOverlapRanker(normalizer),
        SemanticRanker(embedder, normalizer, mode="skills"),
        SemanticRanker(embedder, normalizer, mode="fulltext"),
        ProfileSemanticRanker(embedder, normalizer, pooled=False),
        ProfileSemanticRanker(embedder, normalizer, pooled=True),
        HybridRanker(
            embedder,
            normalizer,
            use_experience=True,
            semantic=SemanticRanker(embedder, normalizer, mode="skills"),
            name="hybrid_skills_embedding",
        ),
        HybridRanker(embedder, normalizer, use_experience=False),
        HybridRanker(embedder, normalizer, use_experience=True),
    ]
