# backend/core/middleware.py

import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = round((time.time() - start) * 1000, 2)
        logger.info(
            f"{request.method} {request.url.path} "
            f"→ {response.status_code} ({duration}ms)"
        )
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests: dict = {}

    async def dispatch(self, request: Request, call_next):
        import time
        client_ip = request.client.host
        now = time.time()
        window_start = now - self.window
        self.requests[client_ip] = [
            t for t in self.requests.get(client_ip, []) if t > window_start
        ]
        if len(self.requests[client_ip]) >= self.max_requests:
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=429, content={"error": "Too many requests"})
        self.requests[client_ip].append(now)
        return await call_next(request)

# Add to main.py:
# from core.middleware import RequestLoggingMiddleware, RateLimitMiddleware
# app.add_middleware(RequestLoggingMiddleware)
# app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)