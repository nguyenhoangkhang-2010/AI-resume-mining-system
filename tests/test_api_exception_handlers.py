from fastapi import FastAPI
from fastapi.testclient import TestClient
from pymongo.errors import ServerSelectionTimeoutError

from app.api.exceptions.handlers import register_exception_handlers
from app.core.exceptions import (
    DatabaseUnavailableError,
    NotFoundError,
    ValidationFailedError,
)


def create_test_app():
    app = FastAPI()

    register_exception_handlers(app)

    @app.get("/not-found")
    def not_found():
        raise NotFoundError("Job not found")

    @app.get("/validation")
    def validation():
        raise ValidationFailedError("Bad input")

    @app.get("/database")
    def database():
        raise DatabaseUnavailableError()

    @app.get("/mongo-timeout")
    def mongo_timeout():
        raise ServerSelectionTimeoutError("no servers")

    @app.get("/value-error")
    def value_error():
        raise ValueError("internal programming error")

    @app.get("/runtime-error")
    def runtime_error():
        raise RuntimeError("Unexpected error")

    return app


app = create_test_app()
client = TestClient(
    app,
    raise_server_exceptions=False,
)


def test_not_found_error_handler():
    response = client.get("/not-found")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Job not found",
        "code": "not_found",
    }


def test_validation_error_handler():
    response = client.get("/validation")

    assert response.status_code == 422
    assert response.json()["code"] == "validation_failed"


def test_database_unavailable_handler():
    response = client.get("/database")

    assert response.status_code == 503
    assert response.json()["code"] == "database_unavailable"


def test_mongo_connection_failure_maps_to_503():
    response = client.get("/mongo-timeout")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Database is unavailable",
        "code": "database_unavailable",
    }


def test_value_error_is_not_reported_as_not_found():
    response = client.get("/value-error")

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"


def test_runtime_error_handler():
    response = client.get("/runtime-error")

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Internal server error",
        "code": "internal_error",
    }
