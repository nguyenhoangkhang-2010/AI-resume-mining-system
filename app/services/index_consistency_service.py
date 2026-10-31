from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Sequence

from loguru import logger

from app.matching.embedding_text import CandidateTextBuilder
from app.models.candidate import CandidateModel


@dataclass
class ConsistencyReport:
    # candidates stored in MongoDB whose vector is not in the index
    missing_in_index: List[int] = field(default_factory=list)

    # vectors in the index that no stored candidate refers to
    orphan_vectors: List[int] = field(default_factory=list)

    # faiss ids used by more than one candidate (needs manual resolution)
    duplicate_faiss_ids: List[int] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not (
            self.missing_in_index
            or self.orphan_vectors
            or self.duplicate_faiss_ids
        )


class IndexConsistencyService:
    """
    Compares MongoDB candidates (the source of truth) with the FAISS index
    and repairs the differences that can be repaired safely.
    """

    def __init__(
        self,
        vector_store,
        embedding_service=None,
        text_builder: CandidateTextBuilder | None = None,
    ):
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.text_builder = text_builder or CandidateTextBuilder()

    def check(self, candidates: Sequence[CandidateModel]) -> ConsistencyReport:
        counts = Counter(candidate.faiss_id for candidate in candidates)
        stored_ids = set(counts)
        indexed_ids = self.vector_store.indexed_ids()

        return ConsistencyReport(
            missing_in_index=sorted(stored_ids - indexed_ids),
            orphan_vectors=sorted(indexed_ids - stored_ids),
            duplicate_faiss_ids=sorted(
                faiss_id for faiss_id, count in counts.items() if count > 1
            ),
        )

    def repair(
        self,
        candidates: Sequence[CandidateModel],
        report: ConsistencyReport | None = None,
    ) -> Dict[str, int]:
        """
        Removes orphan vectors and re-embeds candidates missing from the
        index. Candidates sharing a faiss id are left alone.
        """

        report = report or self.check(candidates)

        removed = 0

        for faiss_id in report.orphan_vectors:
            if self.vector_store.remove_candidate_embedding(faiss_id):
                removed += 1

        added = 0

        if report.missing_in_index:
            if self.embedding_service is None:
                raise ValueError(
                    "An embedding service is required to re-add missing vectors"
                )

            by_id = {c.faiss_id: c for c in candidates}
            skipped = set(report.duplicate_faiss_ids)

            for faiss_id in report.missing_in_index:
                if faiss_id in skipped:
                    continue

                embedding = self.embedding_service.generate_embedding(
                    self.text_builder.text(by_id[faiss_id])
                )

                if self.vector_store.add_candidate_embedding(faiss_id, embedding):
                    added += 1
                else:
                    logger.error(f"Could not re-add vector {faiss_id}.")

        self.vector_store.flush()

        return {"removed_orphans": removed, "added_missing": added}
