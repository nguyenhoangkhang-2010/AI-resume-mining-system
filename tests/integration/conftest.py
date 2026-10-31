import uuid

import pytest
from pymongo import MongoClient

from app.core.config.settings import settings
from app.database.mongodb import connection as connection_module


@pytest.fixture(scope="module")
def client():
    mongo = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=2000)

    try:
        mongo.admin.command("ping")
    except Exception:
        pytest.skip(f"MongoDB is not reachable at {settings.MONGO_URI}")

    yield mongo

    mongo.close()


@pytest.fixture
def database(client, monkeypatch):
    """
    A throwaway database (named ai_resume_it_*) wired into the application's
    connection; dropped afterwards. The configured application database is
    never used.
    """

    name = f"ai_resume_it_{uuid.uuid4().hex[:12]}"

    monkeypatch.setattr(settings, "DB_NAME", name)
    monkeypatch.setattr(connection_module.mongo_db, "client", None)
    monkeypatch.setattr(connection_module.mongo_db, "db", None)

    connection_module.mongo_db.connect()

    yield connection_module.mongo_db.get_db()

    connection_module.mongo_db.close()
    client.drop_database(name)
