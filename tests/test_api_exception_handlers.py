from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.exceptions.handlers import register_exception_handlers


def create_test_app():
    app = FastAPI()

    register_exception_handlers(app)

    @app.get("/value-error")
    def value_error():
        raise ValueError("Job not found")

    @app.get("/runtime-error")
    def runtime_error():
        raise RuntimeError("Unexpected error")

    return app


app = create_test_app()
client = TestClient(
    app,
    raise_server_exceptions=False,
)


def test_value_error_handler():
    response = client.get("/value-error")

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_runtime_error_handler():
    response = client.get("/runtime-error")

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Internal server error"
    }