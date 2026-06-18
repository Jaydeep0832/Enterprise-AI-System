"""
middleware.py — FastAPI middleware for request timing and logging.
"""

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logger import setup_logger

logger = setup_logger()


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Add request duration header and log slow requests."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        response.headers["X-Request-Duration-Ms"] = f"{duration_ms:.2f}"

        if duration_ms > 5000:
            logger.warning(
                f"Slow request: {request.method} {request.url.path} took {duration_ms:.0f}ms"
            )

        return response
