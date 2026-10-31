"""
Rebuilds the job vector index from the jobs stored in MongoDB.

    python -m scripts.reindex_jobs
    python -m scripts.reindex_jobs --dry-run

Run it once for jobs created before job recommendation existed (they have no
vector, so they are never recommended), and after the embedding text changes.
Stop the API first: it keeps the index in memory and would overwrite the file.
"""

import argparse

from app.database.mongodb.connection import mongo_db


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    mongo_db.connect()

    try:
        jobs = mongo_db.get_db()["jobs"]
        total = jobs.count_documents({})
        unindexed = jobs.count_documents({"faiss_id": None})

        print(f"{total} jobs, {unindexed} without a vector.")

        if args.dry_run:
            return

        # Heavy imports are deferred so --dry-run stays fast.
        from app.embeddings.services.embedding_service import EmbeddingService
        from app.services.job_reindex_service import JobReindexService
        from app.vector_store.job_vector_store import JobVectorStore

        count = JobReindexService(
            mongo_db.get_db(), EmbeddingService(), JobVectorStore()
        ).reindex()

        print(f"Indexed {count} jobs.")
    finally:
        mongo_db.close()


if __name__ == "__main__":
    main()
