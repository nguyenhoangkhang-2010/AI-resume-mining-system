"""
Rebuilds the FAISS index from the candidates stored in MongoDB.

    python -m scripts.reindex_candidates
    python -m scripts.reindex_candidates --dry-run

Run it after the embedding text changes (see EMBEDDING_VERSION). Back up
the index file first if you want to be able to roll back.
"""

import argparse

from app.core.constants.app_constants import EMBEDDING_VERSION
from app.database.mongodb.connection import mongo_db
from app.models.candidate import CandidateModel


def load_candidates() -> list[CandidateModel]:
    collection = mongo_db.get_db()["candidates"]

    return [
        CandidateModel(**{**document, "_id": str(document["_id"])})
        for document in collection.find({})
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    mongo_db.connect()

    try:
        candidates = load_candidates()

        stale = [c for c in candidates if c.embedding_version != EMBEDDING_VERSION]

        print(
            f"{len(candidates)} candidates, {len(stale)} indexed with an "
            f"older embedding version (current: {EMBEDDING_VERSION})."
        )

        if args.dry_run:
            return

        # Heavy imports are deferred so --dry-run stays fast.
        from app.embeddings.services.embedding_service import EmbeddingService
        from app.services.candidate_reindex_service import (
            CandidateReindexService,
        )
        from app.vector_store.vector_store import VectorStore

        count = CandidateReindexService(
            EmbeddingService(),
            VectorStore(),
        ).reindex(candidates)

        mongo_db.get_db()["candidates"].update_many(
            {},
            {"$set": {"embedding_version": EMBEDDING_VERSION}},
        )

        print(f"Reindexed {count} candidates.")
    finally:
        mongo_db.close()


if __name__ == "__main__":
    main()
