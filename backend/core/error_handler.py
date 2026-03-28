# backend/core/error_handler.py

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging, traceback, time

logging.basicConfig(
    filename="/home/aiads/ai-ads-consultant/logs/app.log",
    level=logging.ERROR,
    format="%(asctime)s — %(levelname)s — %(message)s"
)
logger = logging.getLogger(__name__)

class AppError(Exception):
    def __init__(self, message: str, code: int = 500, details: dict = {}):
        self.message = message
        self.code = code
        self.details = details

async def app_error_handler(request: Request, exc: AppError):
    logger.error(f"AppError: {exc.message} | Path: {request.url.path}")
    return JSONResponse(status_code=exc.code, content={
        "error": exc.message, "details": exc.details, "path": str(request.url.path)
    })

async def http_error_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={
        "error": "Validation failed",
        "details": exc.errors()
    })

async def global_error_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled: {traceback.format_exc()}")
    return JSONResponse(status_code=500, content={"error": "Internal server error"})

# Retry decorator with exponential backoff
def with_retry(max_retries=3, base_delay=1.0):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    wait = base_delay * (2 ** attempt)
                    logger.warning(f"Attempt {attempt+1} failed: {e}. Retrying in {wait}s...")
                    time.sleep(wait)
        return wrapper
    return decorator

# Add to main.py:
# from core.error_handler import app_error_handler, http_error_handler, validation_error_handler, global_error_handler, AppError
# app.add_exception_handler(AppError, app_error_handler)
# app.add_exception_handler(HTTPException, http_error_handler)
# app.add_exception_handler(RequestValidationError, validation_error_handler)
# app.add_exception_handler(Exception, global_error_handler)