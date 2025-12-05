"""
Rate Limiting for FinanceToolkit API

Uses slowapi for request rate limiting.
"""

import logging
import os
from functools import lru_cache

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Configuration from environment
RATE_LIMIT_PER_MINUTE = os.environ.get("RATE_LIMIT_PER_MINUTE", "60")
RATE_LIMIT_ENABLED = os.environ.get("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_STORAGE = os.environ.get("RATE_LIMIT_STORAGE", "redis").lower()
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_storage_uri() -> str | None:
    """
    Resolve storage backend for rate limiting.

    Prefers Redis when enabled; falls back to in-memory storage if Redis is disabled
    or misconfigured.
    """
    if not RATE_LIMIT_ENABLED:
        return None

    if RATE_LIMIT_STORAGE == "redis":
        return REDIS_URL

    if RATE_LIMIT_STORAGE in {"memory", "in-memory"}:
        return None

    logger.warning(
        "Unknown RATE_LIMIT_STORAGE, defaulting to in-memory",
        extra={"storage": RATE_LIMIT_STORAGE},
    )
    return None


def get_rate_limit_key(request: Request) -> str:
    """
    Get the rate limit key for a request.

    Uses API key hash if available (authenticated requests),
    otherwise falls back to IP address.
    """
    # Use API key hash if available (more accurate for authenticated users)
    if hasattr(request.state, "api_key_hash"):
        return f"key:{request.state.api_key_hash}"

    # Fall back to IP address
    return f"ip:{get_remote_address(request)}"


# Create limiter instance
limiter = Limiter(
    key_func=get_rate_limit_key,
    storage_uri=_get_storage_uri(),
    enabled=RATE_LIMIT_ENABLED,
    default_limits=[f"{RATE_LIMIT_PER_MINUTE}/minute"]
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Custom handler for rate limit exceeded errors.

    Returns a JSON response with retry information.
    """
    # Get retry-after from exception if available
    retry_after = getattr(exc, "retry_after", 60)

    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "detail": f"Too many requests. Limit: {RATE_LIMIT_PER_MINUTE}/minute",
            "retry_after_seconds": retry_after
        },
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": RATE_LIMIT_PER_MINUTE,
        }
    )


# Decorator shortcuts for common rate limits
def limit_standard(func):
    """Standard rate limit: 60/minute"""
    return limiter.limit(f"{RATE_LIMIT_PER_MINUTE}/minute")(func)


def limit_heavy(func):
    """Heavy endpoint rate limit: 10/minute (for expensive operations)"""
    return limiter.limit("10/minute")(func)


def limit_light(func):
    """Light endpoint rate limit: 120/minute (for simple queries)"""
    return limiter.limit("120/minute")(func)
