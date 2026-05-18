import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import structlog

logger = structlog.get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start = time.perf_counter()

        with structlog.contextvars.bound_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        ):
            logger.info("request_started")
            try:
                response = await call_next(request)
                elapsed_ms = int((time.perf_counter() - start) * 1000)
                logger.info(
                    "request_completed",
                    status=response.status_code,
                    elapsed_ms=elapsed_ms,
                )
                response.headers["X-Request-ID"] = request_id
                return response
            except Exception as exc:
                elapsed_ms = int((time.perf_counter() - start) * 1000)
                logger.error("request_failed", error=str(exc), elapsed_ms=elapsed_ms)
                raise
