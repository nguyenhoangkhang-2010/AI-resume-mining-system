from typing import Dict, List

from loguru import logger
from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database
from pymongo.errors import PyMongoError


# collection -> index specs
INDEXES: Dict[str, List[dict]] = {
    "candidates": [
        {"keys": [("faiss_id", ASCENDING)], "unique": True, "name": "faiss_id_unique"},
        {"keys": [("resume_id", ASCENDING)], "unique": True, "name": "resume_id_unique"},
    ],
    "resumes": [
        {"keys": [("upload_status", ASCENDING)], "name": "upload_status"},
        {"keys": [("upload_status", ASCENDING), ("created_at", ASCENDING)], "name": "upload_status_created"},
    ],
    "jobs": [
        {"keys": [("created_at", DESCENDING)], "name": "created_at_desc"},
    ],
}


def ensure_indexes(db: Database) -> List[str]:
    """
    Creates the indexes the application relies on and returns the names of
    the ones that could not be created (for example a unique index over
    data that already contains duplicates). Failures are logged, not raised,
    so the API still starts.
    """

    failed: List[str] = []

    for collection, specs in INDEXES.items():
        for spec in specs:
            name = f"{collection}.{spec['name']}"

            try:
                db[collection].create_index(
                    spec["keys"],
                    unique=spec.get("unique", False),
                    name=spec["name"],
                )
            except PyMongoError as exc:
                failed.append(name)
                logger.error(
                    f"Could not create MongoDB index {name}: {exc}. "
                    f"If it is a unique index, remove the duplicate documents first."
                )

    return failed
