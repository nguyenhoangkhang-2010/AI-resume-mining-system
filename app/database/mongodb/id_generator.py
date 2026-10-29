from pymongo import ReturnDocument
from pymongo.database import Database


FAISS_ID_COUNTER = "faiss_id"


def next_faiss_id(db: Database) -> int:
    """
    Returns a new unique FAISS id from an atomic counter stored in MongoDB.

    A timestamp-based id collides when two uploads are processed in the
    same millisecond, and FAISS would then hold two vectors under one id.
    """

    document = db["counters"].find_one_and_update(
        {"_id": FAISS_ID_COUNTER},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )

    if document is None:
        raise RuntimeError("Could not obtain the next faiss id from MongoDB")

    return int(document["seq"])
