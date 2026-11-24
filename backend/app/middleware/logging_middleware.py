"""
Request Logging & Timing Middleware
"""
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("cyberlab.access")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        
        response = await call_next(request)
        
        process_time_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} "
            f"({process_time_ms}ms) [client: {client_ip}]"
        )
        response.headers["X-Process-Time-Ms"] = str(process_time_ms)
        return response
