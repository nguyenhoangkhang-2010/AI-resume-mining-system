import math

from fastapi import Depends, Request, Security
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger

from app.core.config.settings import settings
from app.core.exceptions import (
    ForbiddenError,
    RateLimitedError,
    UnauthorizedError,
)
from app.core.security.api_keys import (
    ADMIN,
    ANONYMOUS,
    Principal,
    key_store_for,
)
from app.core.security.rate_limit import limiter

# Both are shown as "Authorize" options in Swagger UI. The key is accepted in
# either header: X-API-Key: <key> or Authorization: Bearer <key>.
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


def authenticate(
    request: Request,
    x_api_key: str | None = Security(api_key_header),
    bearer: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> Principal:
    """Resolves the caller, or raises 401 when authentication is required."""

    if not settings.AUTH_ENABLED:
        principal = ANONYMOUS
    else:
        key = x_api_key or (bearer.credentials if bearer else None)

        found = (
            key_store_for(settings.API_KEYS).verify(key) if key else None
        )

        if found is None:
            logger.warning(
                "Rejected request without a valid API key: {} {}",
                request.method,
                request.url.path,
            )

            raise UnauthorizedError()

        principal = found

    request.state.principal = principal

    return principal


def require_admin(principal: Principal = Depends(authenticate)) -> Principal:
    if principal.role != ADMIN:
        raise ForbiddenError("This action needs an admin API key.")

    return principal


def _client_id(request: Request, principal: Principal) -> str:
    if principal is ANONYMOUS:
        return request.client.host if request.client else "unknown"

    return principal.name


def _enforce(request: Request, principal: Principal, bucket: str, limit: int) -> None:
    if not settings.RATE_LIMIT_ENABLED:
        return

    wait = limiter.check(f"{bucket}:{_client_id(request, principal)}", limit)

    if wait is not None:
        retry_after = max(1, math.ceil(wait))

        raise RateLimitedError(
            f"Too many requests. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )


def rate_limit(
    request: Request,
    principal: Principal = Depends(authenticate),
) -> None:
    _enforce(request, principal, "general", settings.RATE_LIMIT_PER_MINUTE)


def heavy_rate_limit(
    request: Request,
    principal: Principal = Depends(authenticate),
) -> None:
    """For endpoints that run the embedding model or the LLM."""

    _enforce(request, principal, "heavy", settings.RATE_LIMIT_HEAVY_PER_MINUTE)
