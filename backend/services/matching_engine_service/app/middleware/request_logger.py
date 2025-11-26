import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from common.logging import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        # Start timer
        start_time = time.time()

        # Generate request ID
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        # Log request
        logger.info(
            f"[{request_id}] {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
            },
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration = (time.time() - start_time) * 1000

            # Log response
            logger.info(
                f"[{request_id}] {response.status_code} - {duration:.2f}ms",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "duration_ms": duration,
                },
            )

            # Add headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{duration:.2f}ms"

            return response

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(
                f"[{request_id}] Error: {str(e)} - {duration:.2f}ms",
                exc_info=True,
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "duration_ms": duration,
                },
            )
            raise
