"""
Tiny in-memory stand-in for a MongoDB collection, enough for the catalog
services: equality filters, $in, array membership, sort/skip/limit,
projection by exclusion or inclusion, count and delete.
"""

from types import SimpleNamespace
from typing import Any, Dict, Iterable, List, Optional


def _same(candidate: Any, expected: Any, casefold: bool) -> bool:
    if casefold and isinstance(candidate, str) and isinstance(expected, str):
        return candidate.casefold() == expected.casefold()

    return candidate == expected


def _matches(document: Dict[str, Any], query: Dict[str, Any], casefold: bool) -> bool:
    for key, expected in query.items():
        value = document.get(key)

        if isinstance(expected, dict) and "$in" in expected:
            if value not in expected["$in"]:
                return False

        elif isinstance(value, list):
            if not any(_same(item, expected, casefold) for item in value):
                return False

        elif not _same(value, expected, casefold):
            return False

    return True


def _project(document: Dict[str, Any], projection: Optional[Dict[str, int]]) -> Dict[str, Any]:
    if not projection:
        return dict(document)

    if any(flag == 0 for flag in projection.values()):
        return {k: v for k, v in document.items() if projection.get(k, 1) != 0}

    return {k: v for k, v in document.items() if k == "_id" or projection.get(k)}


class FakeCursor:
    def __init__(self, documents: List[Dict[str, Any]]):
        self.documents = documents

    def sort(self, keys):
        for key, direction in reversed(keys):
            self.documents.sort(key=lambda d: d.get(key), reverse=direction < 0)

        return self

    def skip(self, count: int):
        self.documents = self.documents[count:]

        return self

    def limit(self, count: int):
        self.documents = self.documents[:count]

        return self

    def __iter__(self):
        return iter(self.documents)


class FakeCollection:
    def __init__(self, documents: Optional[Iterable[Dict[str, Any]]] = None):
        self.documents: List[Dict[str, Any]] = [dict(d) for d in (documents or [])]

    def _select(self, query: Dict[str, Any], collation: Any = None):
        return [d for d in self.documents if _matches(d, query, collation is not None)]

    def find(self, query=None, projection=None, collation=None):
        selected = self._select(query or {}, collation)

        return FakeCursor([_project(d, projection) for d in selected])

    def find_one(self, query=None, projection=None):
        selected = self._select(query or {})

        return _project(selected[0], projection) if selected else None

    def count_documents(self, query=None, collation=None):
        return len(self._select(query or {}, collation))

    def delete_one(self, query):
        selected = self._select(query)

        if selected:
            self.documents.remove(selected[0])

        return SimpleNamespace(deleted_count=1 if selected else 0)

    def delete_many(self, query):
        selected = self._select(query)

        for document in selected:
            self.documents.remove(document)

        return SimpleNamespace(deleted_count=len(selected))
