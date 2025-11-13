"""Performance monitoring middleware."""

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Monitor and log API request performance."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log performance."""
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log based on duration
        if duration > 5.0:  # Very slow (>5s)
            logger.error(
                f"🐌 VERY SLOW: {request.method} {request.url.path} "
                f"took {duration:.2f}s"
            )
        elif duration > 2.0:  # Slow (>2s)
            logger.warning(
                f"⚠️  SLOW: {request.method} {request.url.path} " f"took {duration:.2f}s"
            )
        else:
            logger.info(
                f"✅ {request.method} {request.url.path} "
                f"completed in {duration:.3f}s"
            )

        # Add performance header
        response.headers["X-Process-Time"] = f"{duration:.3f}s"

        return response
