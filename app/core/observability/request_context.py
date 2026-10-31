"""
Request ids and request metrics.

Every request gets an id (the caller's `X-Request-ID` if it looks safe, a new
one otherwise). It is returned in the response header and attached to every
log line written while the request is handled, so one failing request can be
followed through the logs.
"""

import re
import time
import uuid

from fastapi import Request
from loguru import logger

from app.core.observability.metrics import HTTP_REQUESTS, HTTP_SECONDS

HEADER = "X-Request-ID"

# Anything else could be used to forge log lines.
_SAFE_ID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")

UNMATCHED_ROUTE = "unmatched"


def request_id_for(request: Request) -> str:
    supplied = request.headers.get(HEADER, "")

    return supplied if _SAFE_ID.match(supplied) else uuid.uuid4().hex


def route_label(request: Request) -> str:
    """
    The path with the value of every path parameter replaced by its name
    ("/api/v1/resumes/{resume_id}"), so an id never becomes a label. A request
    that matched no route has one shared label.
    """

    if request.scope.get("route") is None:
        return UNMATCHED_ROUTE

    values = {
        str(value): name
        for name, value in (request.scope.get("path_params") or {}).items()
    }

    return "/".join(
        "{" + values[segment] + "}" if segment in values else segment
        for segment in request.url.path.split("/")
    )


async def observe_request(request: Request, call_next):
    request_id = request_id_for(request)
    started = time.perf_counter()
    status = 500

    with logger.contextualize(request_id=request_id):
        try:
            response = await call_next(request)
            status = response.status_code
        finally:
            elapsed = time.perf_counter() - started
            route = route_label(request)

            if route != "/metrics":
                HTTP_REQUESTS.labels(request.method, route, str(status)).inc()
                HTTP_SECONDS.labels(request.method, route).observe(elapsed)

        response.headers[HEADER] = request_id

        return response
