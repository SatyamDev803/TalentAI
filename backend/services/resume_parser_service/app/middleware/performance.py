import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from common.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):

    EXCLUDED_PATHS = {
        "/health",
        "/metrics",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/favicon.ico",
    }

    def __init__(
        self,
        app,
        slow_threshold: float = 2.0,
        very_slow_threshold: float = 5.0,
    ):
        super().__init__(app)
        self.slow_threshold = slow_threshold
        self.very_slow_threshold = very_slow_threshold

    async def dispatch(self, request: Request, call_next: Callable) -> Response:

        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        start_time = time.time()

        # Extract request metadata
        method = request.method
        path = request.url.path
        client_host = request.client.host if request.client else "unknown"

        try:
            # Process request
            response = await call_next(request)

            # Calculate request duration
            duration = time.time() - start_time
            status_code = response.status_code

            # Log request with metrics
            self._log_request(
                method=method,
                path=path,
                duration=duration,
                status_code=status_code,
                client_host=client_host,
            )

            # Add performance headers to response
            response.headers["X-Process-Time"] = f"{duration:.3f}s"
            response.headers["X-Request-ID"] = getattr(
                request.state, "request_id", "unknown"
            )

            return response

        except Exception as e:
            # Log failed requests
            duration = time.time() - start_time
            logger.error(
                f"REQUEST FAILED: {method} {path} "
                f"after {duration:.3f}s | Error: {str(e)} | Client: {client_host}"
            )
            raise

    def _log_request(
        self,
        method: str,
        path: str,
        duration: float,
        status_code: int,
        client_host: str,
    ):
        # Determine log level based on status and duration
        if status_code >= 500:
            log_level = "error"
            severity = "SERVER_ERROR"
        elif status_code >= 400:
            log_level = "warning"
            severity = "CLIENT_ERROR"
        elif duration > self.very_slow_threshold:
            log_level = "error"
            severity = "VERY_SLOW"
        elif duration > self.slow_threshold:
            log_level = "warning"
            severity = "SLOW"
        else:
            log_level = "info"
            severity = "OK"

        # Format log message
        message = (
            f"[{severity}] {method} {path} | "
            f"Status: {status_code} | "
            f"Duration: {duration:.3f}s | "
            f"Client: {client_host}"
        )

        # Log at appropriate level
        if log_level == "error":
            logger.error(message)
        elif log_level == "warning":
            logger.warning(message)
        else:
            if not settings.is_production or duration > 1.0:
                logger.info(message)
            else:
                logger.debug(message)
