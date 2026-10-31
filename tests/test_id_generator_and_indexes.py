import threading

from pymongo.errors import OperationFailure

from app.database.mongodb import connection as connection_module
from app.database.mongodb.id_generator import next_faiss_id
from app.database.mongodb.indexes import INDEXES, ensure_indexes


class FakeCounters:
    """Behaves like an atomic find_one_and_update on one counter document."""

    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()
        self.calls = []

    def find_one_and_update(self, query, update, upsert, return_document):
        self.calls.append((query, update, upsert))

        with self.lock:
            self.value += update["$inc"]["seq"]

            return {"_id": query["_id"], "seq": self.value}


def test_next_faiss_id_uses_atomic_increment():
    counters = FakeCounters()

    first = next_faiss_id({"counters": counters})
    second = next_faiss_id({"counters": counters})

    assert (first, second) == (1, 2)
    assert counters.calls[0] == (
        {"_id": "faiss_id"},
        {"$inc": {"seq": 1}},
        True,
    )


def test_concurrent_ids_are_unique():
    counters = FakeCounters()
    ids = []

    def worker():
        for _ in range(50):
            ids.append(next_faiss_id({"counters": counters}))

    threads = [threading.Thread(target=worker) for _ in range(8)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert len(ids) == 400
    assert len(set(ids)) == 400


class FakeCollection:
    def __init__(self, fail=False):
        self.created = []
        self.fail = fail

    def create_index(self, keys, unique, name):
        if self.fail and unique:
            raise OperationFailure("E11000 duplicate key")

        self.created.append((keys, unique, name))


class IndexDb:
    def __init__(self, failing=()):
        self.collections = {
            name: FakeCollection(fail=name in failing) for name in INDEXES
        }

    def __getitem__(self, name):
        return self.collections[name]


def test_ensure_indexes_creates_all_declared_indexes():
    db = IndexDb()

    assert ensure_indexes(db) == []

    names = {
        (collection, created[2])
        for collection, fake in db.collections.items()
        for created in fake.created
    }

    assert ("candidates", "faiss_id_unique") in names
    assert ("candidates", "resume_id_unique") in names
    assert ("jobs", "created_at_desc") in names


def test_candidate_lookup_keys_are_unique_indexes():
    specs = {spec["name"]: spec for spec in INDEXES["candidates"]}

    assert specs["faiss_id_unique"]["unique"] is True
    assert specs["resume_id_unique"]["unique"] is True


def test_ensure_indexes_reports_failures_without_raising():
    failed = ensure_indexes(IndexDb(failing={"candidates"}))

    assert failed == [
        "candidates.faiss_id_unique",
        "candidates.resume_id_unique",
    ]


def test_connect_creates_indexes(monkeypatch):
    calls = []

    class Admin:
        def command(self, name):
            return {"ok": 1}

    class Client:
        admin = Admin()

        def __init__(self, *args, **kwargs):
            pass

        def __getitem__(self, name):
            return f"db:{name}"

        def close(self):
            pass

    monkeypatch.setattr(connection_module, "MongoClient", Client)
    monkeypatch.setattr(
        connection_module, "ensure_indexes", lambda db: calls.append(db) or []
    )
    monkeypatch.setattr(connection_module.mongo_db, "client", None)
    monkeypatch.setattr(connection_module.mongo_db, "db", None)

    connection_module.mongo_db.connect()

    assert calls == [connection_module.mongo_db.db]
