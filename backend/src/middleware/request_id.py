"""Middleware for request ID tracking."""
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to generate and track request IDs for debugging."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(
            REQUEST_ID_HEADER) or str(uuid.uuid4())

        request.state.request_id = request_id

        logger.info(
            f"Request {request.method} {request.url.path}",
            extra={"request_id": request_id,
                   "method": request.method, "path": request.url.path}
        )

        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response


def get_request_id(request: Request) -> str:
    """Get request ID from request state."""
    return getattr(request.state, "request_id", "unknown")
