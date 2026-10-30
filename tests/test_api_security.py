import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_resume_catalog_service
from app.core.config.settings import settings
from app.core.security.api_keys import ApiKeyStore, fingerprint
from app.core.security.rate_limit import SlidingWindowLimiter, limiter
from app.core.security.startup import validate_security_settings
from app.main import app

ADMIN_KEY = "a" * 32
USER_KEY = "u" * 32
RESUME_ID = "665f1c2b8e4a4b0012345678"


class StubCatalog:
    def __init__(self):
        self.deleted = []

    def list_resumes(self, status_filter, limit, offset):
        return {"items": [], "total": 0, "limit": limit, "offset": offset}

    def delete_resume(self, resume_id):
        self.deleted.append(resume_id)


@pytest.fixture
def secured(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    monkeypatch.setattr(
        settings, "API_KEYS", f"admin:{ADMIN_KEY},user:{USER_KEY}"
    )


@pytest.fixture
def catalog():
    stub = StubCatalog()

    app.dependency_overrides[get_resume_catalog_service] = lambda: stub

    yield stub

    app.dependency_overrides.clear()


@pytest.fixture
def client(catalog):
    return TestClient(app, raise_server_exceptions=False)


# ----------------------------------------------------------------------
# Authentication
# ----------------------------------------------------------------------


def test_request_without_key_is_rejected(secured, client):
    response = client.get("/api/v1/resumes/")

    assert response.status_code == 401
    assert response.json()["code"] == "unauthorized"
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_wrong_key_is_rejected(secured, client):
    response = client.get("/api/v1/resumes/", headers={"X-API-Key": "x" * 32})

    assert response.status_code == 401


def test_key_in_x_api_key_header_is_accepted(secured, client):
    response = client.get("/api/v1/resumes/", headers={"X-API-Key": USER_KEY})

    assert response.status_code == 200


def test_key_as_bearer_token_is_accepted(secured, client):
    response = client.get(
        "/api/v1/resumes/", headers={"Authorization": f"Bearer {USER_KEY}"}
    )

    assert response.status_code == 200


def test_health_and_root_stay_open(secured, client):
    assert client.get("/").status_code == 200
    assert client.get("/health").status_code in (200, 503)


def test_auth_disabled_leaves_api_open(client):
    assert client.get("/api/v1/resumes/").status_code == 200


def test_rejection_does_not_echo_the_key(secured, client):
    response = client.get("/api/v1/resumes/", headers={"X-API-Key": "x" * 32})

    assert "x" * 32 not in response.text


# ----------------------------------------------------------------------
# Roles
# ----------------------------------------------------------------------


def test_user_key_cannot_delete(secured, client, catalog):
    response = client.delete(
        f"/api/v1/resumes/{RESUME_ID}", headers={"X-API-Key": USER_KEY}
    )

    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"
    assert catalog.deleted == []


def test_admin_key_can_delete(secured, client, catalog):
    response = client.delete(
        f"/api/v1/resumes/{RESUME_ID}", headers={"X-API-Key": ADMIN_KEY}
    )

    assert response.status_code == 204
    assert catalog.deleted == [RESUME_ID]


def test_delete_without_key_is_401_not_403(secured, client, catalog):
    response = client.delete(f"/api/v1/resumes/{RESUME_ID}")

    assert response.status_code == 401
    assert catalog.deleted == []


# ----------------------------------------------------------------------
# Rate limiting
# ----------------------------------------------------------------------


def test_requests_over_the_limit_get_429_with_retry_after(
    secured, client, monkeypatch
):
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(settings, "RATE_LIMIT_PER_MINUTE", 3)

    headers = {"X-API-Key": USER_KEY}

    statuses = [
        client.get("/api/v1/resumes/", headers=headers).status_code
        for _ in range(4)
    ]

    assert statuses == [200, 200, 200, 429]

    blocked = client.get("/api/v1/resumes/", headers=headers)

    assert blocked.json()["code"] == "rate_limited"
    assert int(blocked.headers["Retry-After"]) >= 1


def test_each_key_has_its_own_budget(secured, client, monkeypatch):
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(settings, "RATE_LIMIT_PER_MINUTE", 1)

    assert client.get(
        "/api/v1/resumes/", headers={"X-API-Key": USER_KEY}
    ).status_code == 200
    assert client.get(
        "/api/v1/resumes/", headers={"X-API-Key": ADMIN_KEY}
    ).status_code == 200
    assert client.get(
        "/api/v1/resumes/", headers={"X-API-Key": USER_KEY}
    ).status_code == 429


def test_unauthenticated_requests_do_not_use_up_a_budget(
    secured, client, monkeypatch
):
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(settings, "RATE_LIMIT_PER_MINUTE", 1)

    for _ in range(3):
        assert client.get("/api/v1/resumes/").status_code == 401

    assert client.get(
        "/api/v1/resumes/", headers={"X-API-Key": USER_KEY}
    ).status_code == 200


def test_rate_limit_can_be_disabled(secured, client, monkeypatch):
    monkeypatch.setattr(settings, "RATE_LIMIT_PER_MINUTE", 1)

    headers = {"X-API-Key": USER_KEY}

    assert all(
        client.get("/api/v1/resumes/", headers=headers).status_code == 200
        for _ in range(3)
    )


def test_limiter_forgets_old_requests():
    now = [0.0]
    window = SlidingWindowLimiter(clock=lambda: now[0])

    assert window.check("k", 2) is None
    assert window.check("k", 2) is None
    assert window.check("k", 2) == pytest.approx(60.0)

    now[0] = 59.0

    assert window.check("k", 2) == pytest.approx(1.0)

    now[0] = 60.5

    assert window.check("k", 2) is None


def test_rejected_requests_are_not_counted():
    now = [0.0]
    window = SlidingWindowLimiter(clock=lambda: now[0])

    window.check("k", 1)

    for _ in range(5):
        assert window.check("k", 1) is not None

    now[0] = 60.0

    assert window.check("k", 1) is None


# ----------------------------------------------------------------------
# Key parsing and startup validation
# ----------------------------------------------------------------------


def test_parse_reads_roles_and_keys():
    store = ApiKeyStore.parse(f" admin:{ADMIN_KEY} , user:{USER_KEY} ,")

    assert len(store) == 2
    assert store.verify(ADMIN_KEY).role == "admin"
    assert store.verify(USER_KEY).role == "user"
    assert store.verify("z" * 32) is None


def test_principal_name_is_a_fingerprint_not_the_key():
    principal = ApiKeyStore.parse(f"user:{USER_KEY}").verify(USER_KEY)

    assert principal.name == fingerprint(USER_KEY)
    assert USER_KEY not in principal.name


@pytest.mark.parametrize(
    "value",
    [
        "root:" + "k" * 32,
        "k" * 32,
        "admin:short",
        f"admin:{ADMIN_KEY},user:{ADMIN_KEY}",
    ],
)
def test_parse_rejects_bad_entries(value):
    with pytest.raises(ValueError):
        ApiKeyStore.parse(value)


def test_empty_value_means_no_keys():
    assert len(ApiKeyStore.parse(None)) == 0
    assert len(ApiKeyStore.parse("")) == 0


def test_startup_fails_when_auth_is_on_without_keys(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "API_KEYS", "")

    with pytest.raises(RuntimeError, match="API_KEYS is empty"):
        validate_security_settings(settings)


def test_startup_fails_on_malformed_keys(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "API_KEYS", "admin:short")

    with pytest.raises(RuntimeError, match="Invalid API_KEYS"):
        validate_security_settings(settings)


def test_startup_passes_with_valid_keys(secured):
    validate_security_settings(settings)


def test_startup_allows_auth_disabled_without_keys(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENABLED", False)
    monkeypatch.setattr(settings, "API_KEYS", "")

    validate_security_settings(settings)


# ----------------------------------------------------------------------
# Response headers
# ----------------------------------------------------------------------


def test_api_responses_carry_security_headers(client):
    response = client.get("/api/v1/resumes/")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Cache-Control"] == "no-store"


def test_limiter_state_is_reset_between_tests():
    assert limiter.check("fresh-key", 1) is None
