"""
Compares the candidates stored in MongoDB with the FAISS index.

    python -m scripts.check_index_consistency
    python -m scripts.check_index_consistency --repair

--repair removes vectors that no candidate refers to and re-embeds
candidates that are missing from the index. Candidates that share a faiss
id are only reported.
"""

import argparse

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
    parser.add_argument("--repair", action="store_true")
    args = parser.parse_args()

    mongo_db.connect()

    try:
        from app.vector_store.vector_store import VectorStore
        from app.services.index_consistency_service import (
            IndexConsistencyService,
        )

        candidates = load_candidates()

        embedding_service = None

        if args.repair:
            from app.embeddings.services.embedding_service import (
                EmbeddingService,
            )

            embedding_service = EmbeddingService()

        service = IndexConsistencyService(VectorStore(), embedding_service)

        report = service.check(candidates)

        print(f"Candidates in MongoDB: {len(candidates)}")
        print(f"Missing from the index: {len(report.missing_in_index)}")
        print(f"Orphan vectors in the index: {len(report.orphan_vectors)}")
        print(f"Duplicate faiss ids: {len(report.duplicate_faiss_ids)}")

        if report.ok:
            print("Index and database are consistent.")
            return

        if args.repair:
            print(service.repair(candidates, report))
        else:
            print("Run with --repair to fix what can be fixed safely.")
    finally:
        mongo_db.close()


if __name__ == "__main__":
    main()
