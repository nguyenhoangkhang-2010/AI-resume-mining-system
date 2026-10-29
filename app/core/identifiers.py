from bson import ObjectId
from bson.errors import InvalidId

from app.core.exceptions import NotFoundError


def parse_object_id(value: str, resource: str) -> ObjectId:
    """
    Converts an id taken from a URL. A malformed id cannot belong to any
    document, so it is reported as "not found" like an unknown one.
    """

    try:
        return ObjectId(value)
    except (InvalidId, TypeError) as exc:
        raise NotFoundError(f"{resource} not found: {value}") from exc
