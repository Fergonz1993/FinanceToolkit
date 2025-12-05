"""
REST API for FinanceToolkit

FastAPI-based web service exposing financial analysis capabilities.

Run with: uvicorn infrastructure.api:app --reload
"""

import asyncio
import json
import logging
import os
import re
import time
import uuid
from datetime import date, datetime
from typing import Any, Awaitable, Callable
from functools import lru_cache
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
import redis.asyncio as redis
from prometheus_client import Counter, Histogram, CONTENT_TYPE_LATEST, generate_latest

# Security imports
from .security import (
    SecurityHeadersMiddleware,
    limiter,
    rate_limit_exceeded_handler,
    verify_api_key,
    audit_logger,
    AuditEvent,
)
from .security import validators as security_validators

# Import will work when FinanceToolkit is installed
try:
    from financetoolkit import Toolkit
except ImportError:
    Toolkit = None

from .database import FinanceDatabase

# ============ CONFIGURATION ============

# Get configuration from environment variables
API_KEY = os.environ.get("FMP_API_KEY", "")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*")
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
API_CACHE_ENABLED = os.environ.get("API_CACHE_ENABLED", "true").lower() == "true"
API_CACHE_TTL_SECONDS = int(os.environ.get("API_CACHE_TTL", "300"))
API_REQUEST_TIMEOUT = float(os.environ.get("API_REQUEST_TIMEOUT", "15"))
API_REQUEST_RETRIES = int(os.environ.get("API_REQUEST_RETRIES", "1"))
API_REQUEST_BACKOFF_SECONDS = float(os.environ.get("API_REQUEST_BACKOFF", "0.5"))
METRICS_ENABLED = os.environ.get("METRICS_ENABLED", "true").lower() == "true"

# Validate CORS in production
def _parse_origins(origins_raw: str) -> list[str]:
    """Parse comma separated origins env var."""
    if origins_raw.strip() == "*":
        if ENVIRONMENT == "production":
            raise RuntimeError(
                "ALLOWED_ORIGINS cannot be '*' in production. "
                "Set specific origins: ALLOWED_ORIGINS=https://yourdomain.com"
            )
        return ["*"]
    return [origin.strip() for origin in origins_raw.split(",") if origin.strip()]

# ============ LOGGING SETUP ============

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "ticker"):
            log_data["ticker"] = record.ticker
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

# Configure logging
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.basicConfig(level=LOG_LEVEL, handlers=[handler])
logger = logging.getLogger(__name__)

# Redis client (lazy)
redis_client: redis.Redis | None = None

# Prometheus metrics
REQUEST_COUNT = Counter(
    "ftk_api_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "ftk_api_request_duration_seconds",
    "HTTP request latency",
    ["method", "path", "status"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
)

# ============ REDIS CACHE HELPERS ============


def _get_redis_client() -> redis.Redis | None:
    """Lazily initialize Redis client for caching."""
    global redis_client
    if redis_client is not None:
        return redis_client

    if not API_CACHE_ENABLED:
        return None

    try:
        redis_client = redis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            retry_on_timeout=True,
        )
        return redis_client
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Redis unavailable, disabling API cache",
            extra={"error": str(exc), "redis_url": REDIS_URL},
        )
        redis_client = None
        return None


def _json_default_serializer(obj: Any):
    """Fallback serializer for JSON dumps."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    # Handle numpy/pandas scalars if present
    if hasattr(obj, "item"):
        try:
            return obj.item()
        except Exception:  # noqa: BLE001
            pass
    return str(obj)


async def get_cached_payload(cache_key: str) -> Any | None:
    """Retrieve cached payload from Redis, if available."""
    client = _get_redis_client()
    if not client:
        return None

    try:
        cached = await client.get(cache_key)
        if cached is None:
            return None
        return json.loads(cached)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Cache read failed", extra={"key": cache_key, "error": str(exc)})
        return None


async def set_cached_payload(cache_key: str, payload: Any, ttl: int | None = None) -> None:
    """Store payload in Redis with TTL."""
    client = _get_redis_client()
    if not client:
        return

    try:
        await client.set(
            cache_key,
            json.dumps(payload, default=_json_default_serializer),
            ex=ttl or API_CACHE_TTL_SECONDS,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Cache write failed", extra={"key": cache_key, "error": str(exc)})


def cache_key_for(prefix: str, *parts: str) -> str:
    """Build a namespaced cache key."""
    safe_parts = [prefix, *[p.replace(" ", "").lower() for p in parts if p is not None]]
    return "ftk-api:" + ":".join(safe_parts)


async def cached_response(
    request: Request,
    cache_key: str,
    compute: Callable[[], Awaitable[Any]],
    ttl: int | None = None,
    ticker: str | None = None,
    tickers: list[str] | None = None,
):
    """
    Generic helper to serve cached responses with audit logging.

    Args:
        request: FastAPI request
        cache_key: Redis cache key
        compute: coroutine that returns the payload
        ttl: optional cache TTL
        ticker/tickers: optional audit metadata
    """
    cached = await get_cached_payload(cache_key)
    if cached is not None:
        audit_logger.log(AuditEvent.CACHE_HIT, request, ticker=ticker, tickers=tickers, extra={"cache_key": cache_key})
        return cached

    audit_logger.log(AuditEvent.CACHE_MISS, request, ticker=ticker, tickers=tickers, extra={"cache_key": cache_key})
    result = await compute()
    await set_cached_payload(cache_key, result, ttl=ttl)
    return result


async def get_redis_health() -> dict:
    """Check Redis connectivity for health endpoints."""
    client = _get_redis_client()
    if client is None:
        return {
            "enabled": API_CACHE_ENABLED,
            "status": "disabled" if not API_CACHE_ENABLED else "unavailable",
        }

    try:
        await client.ping()
        return {
            "enabled": True,
            "status": "up",
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis health check failed", extra={"error": str(exc)})
        return {
            "enabled": True,
            "status": "down",
            "error": str(exc),
        }


# ============ MIDDLEWARE ============

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to each request for tracing."""
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        start_time = time.time()
        response = await call_next(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        # Log request
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} ({duration_ms}ms)",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            }
        )

        # Metrics
        if METRICS_ENABLED:
            labels = {
                "method": request.method,
                "path": request.url.path,
                "status": str(response.status_code),
            }
            REQUEST_COUNT.labels(**labels).inc()
            REQUEST_LATENCY.labels(**labels).observe(duration_ms / 1000.0)

        return response

# ============ APP INITIALIZATION ============

# Initialize FastAPI app
app = FastAPI(
    title="FinanceToolkit API",
    description="REST API for financial analysis using FinanceToolkit",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add rate limiter state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Add security headers middleware (must be first to apply to all responses)
app.add_middleware(SecurityHeadersMiddleware)

# Add request ID middleware
app.add_middleware(RequestIDMiddleware)

# Enable CORS for web frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_origins(ALLOWED_ORIGINS),
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# Initialize database
db = FinanceDatabase("finance_api_cache.db")


def _error_payload(message: str, code: str, request: Request, detail: Any | None = None) -> dict:
    """Create a consistent error payload."""
    payload = {
        "code": code,
        "message": message,
        "request_id": getattr(request.state, "request_id", None),
    }
    if detail is not None:
        payload["detail"] = detail
    return payload


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Return consistent structure for HTTP errors."""
    detail = exc.detail if isinstance(exc.detail, dict) else None
    message = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(str(message), code=f"http_{exc.status_code}", request=request, detail=detail),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return consistent structure for validation errors."""
    return JSONResponse(
        status_code=422,
        content=_error_payload("Validation failed", code="validation_error", request=request, detail=exc.errors()),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catch-all to avoid leaking stack traces to clients."""
    logger.exception("Unhandled error", extra={"path": request.url.path})
    return JSONResponse(
        status_code=500,
        content=_error_payload("Internal server error", code="internal_error", request=request),
    )


def _validate_confidence(value: float) -> float:
    if not 0 < value < 1:
        raise HTTPException(status_code=400, detail="confidence_level must be between 0 and 1")
    return value


def normalize_ticker(ticker: str) -> str:
    """Validate and normalize ticker strings."""
    return security_validators.normalize_ticker(ticker)


# Pydantic models for request/response
class TickerRequest(BaseModel):
    tickers: list[str]
    start_date: Optional[str] = "2020-01-01"
    end_date: Optional[str] = None


class RatioResponse(BaseModel):
    ticker: str
    period: str
    ratios: dict


class HealthScoreResponse(BaseModel):
    ticker: str
    altman_z_score: Optional[float] = None
    piotroski_f_score: Optional[int] = None
    interpretation: dict


# Helper function to get toolkit
@lru_cache(maxsize=128)
def _get_toolkit_cached(tickers_key: tuple[str, ...], start_date: str, quarterly: bool):
    """Cache Toolkit instances to reduce API initialization cost."""
    tickers = list(tickers_key)
    if not Toolkit:
        raise HTTPException(
            status_code=500,
            detail="FinanceToolkit not installed. Run: pip install financetoolkit"
        )

    if not API_KEY:
        raise HTTPException(
            status_code=500,
            detail="FMP_API_KEY environment variable not set"
        )

    return Toolkit(
        tickers=tickers,
        api_key=API_KEY,
        start_date=start_date,
        quarterly=quarterly,
    )


def get_toolkit(tickers: list[str], start_date: str = "2020-01-01", quarterly: bool = False):
    """Create or retrieve a cached Toolkit instance with validated tickers."""
    normalized = tuple(sorted(normalize_ticker(t) for t in tickers))
    return _get_toolkit_cached(normalized, start_date, quarterly)


async def run_toolkit_call(
    fn: Callable[[], Any],
    *,
    op: str,
    ticker: str | None = None,
):
    """
    Execute a Toolkit call with timeout and retries.

    The Toolkit methods are synchronous; we run them in a worker thread to avoid
    blocking the event loop, and wrap with asyncio timeouts and simple backoff.
    """
    last_exc: Exception | None = None
    for attempt in range(API_REQUEST_RETRIES + 1):
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(fn),
                timeout=API_REQUEST_TIMEOUT,
            )
        except asyncio.TimeoutError as exc:
            last_exc = exc
            logger.warning(
                "Toolkit call timed out",
                extra={"op": op, "ticker": ticker, "attempt": attempt + 1},
            )
        except Exception as exc:  # noqa: BLE001
            if isinstance(exc, HTTPException):
                raise
            last_exc = exc
            logger.warning(
                "Toolkit call failed",
                extra={"op": op, "ticker": ticker, "attempt": attempt + 1, "error": str(exc)},
            )

        if attempt < API_REQUEST_RETRIES:
            await asyncio.sleep(API_REQUEST_BACKOFF_SECONDS * (attempt + 1))

    status_code = 504 if isinstance(last_exc, asyncio.TimeoutError) else 502
    raise HTTPException(status_code=status_code, detail=f"{op} unavailable")


# ============ ENDPOINTS ============

@app.get("/")
async def root():
    """API root - basic info."""
    return {
        "service": "FinanceToolkit API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_liveness():
    """
    Liveness probe - is the service running?

    Used by load balancers and orchestrators (Cloud Run, Kubernetes).
    Returns 200 if the service is alive, regardless of dependencies.
    """
    return {"status": "alive"}


@app.get("/health/ready")
async def health_readiness():
    """
    Readiness probe - is the service ready to accept traffic?

    Checks all dependencies (API key, database, toolkit).
    Returns 200 only if all checks pass.
    """
    redis_health = await get_redis_health()
    redis_ok = (not redis_health["enabled"]) or redis_health["status"] == "up"
    checks = {
        "api_key_configured": bool(API_KEY),
        "toolkit_available": Toolkit is not None,
        "database_connected": db is not None,
        "redis_cache_available": redis_ok,
    }

    all_ready = all(checks.values())

    if not all_ready:
        raise HTTPException(
            status_code=503,
            detail={"status": "not_ready", "checks": {**checks, "redis": redis_health}}
        )

    return {
        "status": "ready",
        "checks": {**checks, "redis": redis_health}
    }


@app.get("/api/health")
async def health_check():
    """Detailed health check with cache statistics."""
    cache_stats = db.get_cache_stats()
    redis_health = await get_redis_health()
    return {
        "status": "healthy",
        "environment": ENVIRONMENT,
        "api_key_configured": bool(API_KEY),
        "toolkit_available": Toolkit is not None,
        "cache_stats": cache_stats,
        "redis": redis_health,
    }


@app.get("/metrics")
async def metrics():
    """Expose Prometheus metrics."""
    if not METRICS_ENABLED:
        raise HTTPException(status_code=404, detail="Metrics disabled")
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


# ============ FINANCIAL STATEMENTS ============

@app.get("/api/statements/income/{ticker}")
@limiter.limit("60/minute")
async def get_income_statement(
    request: Request,
    ticker: str,
    quarterly: bool = Query(False, description="Get quarterly data"),
    api_key: str = Depends(verify_api_key),
):
    """Get income statement for a ticker."""
    normalized = normalize_ticker(ticker)
    audit_logger.data_access(request, ticker=normalized)
    cache_key = cache_key_for("statement:income", normalized, f"q{int(quarterly)}")

    async def compute():
        toolkit = get_toolkit([normalized], quarterly=quarterly)
        statement = await run_toolkit_call(
            lambda: toolkit.get_income_statement(),
            op="income_statement",
            ticker=normalized,
        )
        return {
            "ticker": normalized,
            "type": "income_statement",
            "quarterly": quarterly,
            "data": statement.to_dict()
        }

    try:
        return await cached_response(request, cache_key, compute, ticker=normalized)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to fetch income statement", extra={"ticker": normalized})
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/statements/balance/{ticker}")
@limiter.limit("60/minute")
async def get_balance_sheet(
    request: Request,
    ticker: str,
    quarterly: bool = Query(False, description="Get quarterly data"),
    api_key: str = Depends(verify_api_key),
):
    """Get balance sheet for a ticker."""
    normalized = normalize_ticker(ticker)
    audit_logger.data_access(request, ticker=normalized)
    cache_key = cache_key_for("statement:balance", normalized, f"q{int(quarterly)}")

    async def compute():
        toolkit = get_toolkit([normalized], quarterly=quarterly)
        statement = await run_toolkit_call(
            lambda: toolkit.get_balance_sheet_statement(),
            op="balance_sheet",
            ticker=normalized,
        )
        return {
            "ticker": normalized,
            "type": "balance_sheet",
            "quarterly": quarterly,
            "data": statement.to_dict()
        }

    try:
        return await cached_response(request, cache_key, compute, ticker=normalized)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to fetch balance sheet", extra={"ticker": normalized})
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/statements/cashflow/{ticker}")
@limiter.limit("60/minute")
async def get_cash_flow(
    request: Request,
    ticker: str,
    quarterly: bool = Query(False, description="Get quarterly data"),
    api_key: str = Depends(verify_api_key),
):
    """Get cash flow statement for a ticker."""
    normalized = normalize_ticker(ticker)
    audit_logger.data_access(request, ticker=normalized)
    cache_key = cache_key_for("statement:cashflow", normalized, f"q{int(quarterly)}")

    async def compute():
        toolkit = get_toolkit([normalized], quarterly=quarterly)
        statement = await run_toolkit_call(
            lambda: toolkit.get_cash_flow_statement(),
            op="cash_flow",
            ticker=normalized,
        )
        return {
            "ticker": normalized,
            "type": "cash_flow",
            "quarterly": quarterly,
            "data": statement.to_dict()
        }

    try:
        return await cached_response(request, cache_key, compute, ticker=normalized)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to fetch cash flow", extra={"ticker": normalized})
        raise HTTPException(status_code=500, detail=str(e))


# ============ RATIOS ============

@app.get("/api/ratios/profitability/{ticker}")
@limiter.limit("60/minute")
async def get_profitability_ratios(
    request: Request,
    ticker: str,
    api_key: str = Depends(verify_api_key),
):
    """Get profitability ratios for a ticker."""
    normalized = normalize_ticker(ticker)
    audit_logger.data_access(request, ticker=normalized)
    cache_key = cache_key_for("ratios:profitability", normalized)

    async def compute():
        toolkit = get_toolkit([normalized])
        ratios = await run_toolkit_call(
            lambda: toolkit.ratios.collect_profitability_ratios(),
            op="ratios_profitability",
            ticker=normalized,
        )
        return {
            "ticker": normalized,
            "category": "profitability",
            "ratios": ratios.to_dict()
        }

    try:
        return await cached_response(request, cache_key, compute, ticker=normalized)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to fetch profitability ratios", extra={"ticker": normalized})
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ratios/liquidity/{ticker}")
@limiter.limit("60/minute")
async def get_liquidity_ratios(
    request: Request,
    ticker: str,
    api_key: str = Depends(verify_api_key),
):
    """Get liquidity ratios for a ticker."""
    normalized = normalize_ticker(ticker)
    audit_logger.data_access(request, ticker=normalized)
    cache_key = cache_key_for("ratios:liquidity", normalized)

    async def compute():
        toolkit = get_toolkit([normalized])
        ratios = await run_toolkit_call(
            lambda: toolkit.ratios.collect_liquidity_ratios(),
            op="ratios_liquidity",
            ticker=normalized,
        )
        return {
            "ticker": normalized,
            "category": "liquidity",
            "ratios": ratios.to_dict()
        }

    try:
        return await cached_response(request, cache_key, compute, ticker=normalized)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to fetch liquidity ratios", extra={"ticker": normalized})
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ratios/solvency/{ticker}")
@limiter.limit("60/minute")
async def get_solvency_ratios(
    request: Request,
    ticker: str,
    api_key: str = Depends(verify_api_key),
):
    """Get solvency ratios for a ticker."""
    normalized = normalize_ticker(ticker)
    audit_logger.data_access(request, ticker=normalized)
    cache_key = cache_key_for("ratios:solvency", normalized)

    async def compute():
        toolkit = get_toolkit([normalized])
        ratios = await run_toolkit_call(
            lambda: toolkit.ratios.collect_solvency_ratios(),
            op="ratios_solvency",
            ticker=normalized,
        )
        return {
            "ticker": normalized,
            "category": "solvency",
            "ratios": ratios.to_dict()
        }

    try:
        return await cached_response(request, cache_key, compute, ticker=normalized)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to fetch solvency ratios", extra={"ticker": normalized})
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ratios/valuation/{ticker}")
@limiter.limit("60/minute")
async def get_valuation_ratios(
    request: Request,
    ticker: str,
    api_key: str = Depends(verify_api_key),
):
    """Get valuation ratios for a ticker."""
    normalized = normalize_ticker(ticker)
    audit_logger.data_access(request, ticker=normalized)
    cache_key = cache_key_for("ratios:valuation", normalized)

    async def compute():
        toolkit = get_toolkit([normalized])
        ratios = await run_toolkit_call(
            lambda: toolkit.ratios.collect_valuation_ratios(),
            op="ratios_valuation",
            ticker=normalized,
        )
        return {
            "ticker": normalized,
            "category": "valuation",
            "ratios": ratios.to_dict()
        }

    try:
        return await cached_response(request, cache_key, compute, ticker=normalized)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to fetch valuation ratios", extra={"ticker": normalized})
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ratios/all/{ticker}")
@limiter.limit("30/minute")
async def get_all_ratios(
    request: Request,
    ticker: str,
    api_key: str = Depends(verify_api_key),
):
    """Get all financial ratios for a ticker."""
    normalized = normalize_ticker(ticker)
    audit_logger.data_access(request, ticker=normalized)
    cache_key = cache_key_for("ratios:all", normalized)

    async def compute():
        toolkit = get_toolkit([normalized])
        ratios = await run_toolkit_call(
            lambda: toolkit.ratios.collect_all_ratios(),
            op="ratios_all",
            ticker=normalized,
        )
        return {
            "ticker": normalized,
            "category": "all",
            "ratios": ratios.to_dict()
        }

    try:
        return await cached_response(request, cache_key, compute, ticker=normalized)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to fetch all ratios", extra={"ticker": normalized})
        raise HTTPException(status_code=500, detail=str(e))


# ============ HEALTH SCORES ============

@app.get("/api/health-score/{ticker}")
@limiter.limit("60/minute")
async def get_health_scores(
    request: Request,
    ticker: str,
    api_key: str = Depends(verify_api_key),
):
    """
    Get financial health scores (Altman Z-Score, Piotroski F-Score).

    Returns:
        - altman_z_score: Bankruptcy prediction (>2.99 safe, <1.81 risky)
        - piotroski_f_score: Financial strength (0-9, higher is better)
        - interpretations: Plain English explanations
    """
    normalized = normalize_ticker(ticker)
    audit_logger.data_access(request, ticker=normalized)
    cache_key = cache_key_for("healthscore", normalized)

    async def compute():
        toolkit = get_toolkit([normalized])

        # Get scores
        altman = await run_toolkit_call(
            lambda: toolkit.models.get_altman_z_score(),
            op="altman_z_score",
            ticker=normalized,
        )
        piotroski = await run_toolkit_call(
            lambda: toolkit.models.get_piotroski_f_score(),
            op="piotroski_f_score",
            ticker=normalized,
        )

        # Get latest values
        altman_latest = float(altman.iloc[:, -1].values[0]) if not altman.empty else None
        piotroski_latest = int(piotroski.iloc[:, -1].values[0]) if not piotroski.empty else None

        # Interpret Altman Z-Score
        altman_interpretation = "Unknown"
        if altman_latest:
            if altman_latest > 2.99:
                altman_interpretation = "Safe Zone - Low bankruptcy risk"
            elif altman_latest > 1.81:
                altman_interpretation = "Grey Zone - Moderate risk, monitor closely"
            else:
                altman_interpretation = "Distress Zone - High bankruptcy risk"

        # Interpret Piotroski F-Score
        piotroski_interpretation = "Unknown"
        if piotroski_latest is not None:
            if piotroski_latest >= 8:
                piotroski_interpretation = "Excellent - Strong financial health"
            elif piotroski_latest >= 5:
                piotroski_interpretation = "Average - Mixed signals"
            else:
                piotroski_interpretation = "Poor - Financial weakness, caution advised"

        return {
            "ticker": normalized,
            "altman_z_score": altman_latest,
            "piotroski_f_score": piotroski_latest,
            "interpretation": {
                "altman": altman_interpretation,
                "piotroski": piotroski_interpretation
            },
            "historical": {
                "altman": altman.to_dict() if not altman.empty else {},
                "piotroski": piotroski.to_dict() if not piotroski.empty else {}
            }
        }

    try:
        return await cached_response(request, cache_key, compute, ticker=normalized)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to fetch health scores", extra={"ticker": normalized})
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dupont/{ticker}")
@limiter.limit("60/minute")
async def get_dupont_analysis(
    request: Request,
    ticker: str,
    api_key: str = Depends(verify_api_key),
):
    """
    Get DuPont Analysis - breaks down ROE into components.

    Components:
        - Net Profit Margin (profitability)
        - Asset Turnover (efficiency)
        - Equity Multiplier (leverage)
    """
    normalized = normalize_ticker(ticker)
    audit_logger.data_access(request, ticker=normalized)
    cache_key = cache_key_for("dupont", normalized)

    async def compute():
        toolkit = get_toolkit([normalized])
        dupont = await run_toolkit_call(
            lambda: toolkit.models.get_dupont_analysis(),
            op="dupont_analysis",
            ticker=normalized,
        )
        return {
            "ticker": normalized,
            "analysis": "dupont",
            "explanation": "ROE = Net Margin × Asset Turnover × Equity Multiplier",
            "data": dupont.to_dict()
        }

    try:
        return await cached_response(request, cache_key, compute, ticker=normalized)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to fetch DuPont analysis", extra={"ticker": normalized})
        raise HTTPException(status_code=500, detail=str(e))


# ============ RISK METRICS ============

@app.get("/api/risk/{ticker}")
@limiter.limit("60/minute")
async def get_risk_metrics(
    request: Request,
    ticker: str,
    confidence_level: float = Query(
        0.95,
        gt=0.0,
        lt=1.0,
        description="Confidence level for VaR (0.9, 0.95, 0.99)"
    ),
    api_key: str = Depends(verify_api_key),
):
    """
    Get risk metrics for a ticker.

    Returns:
        - value_at_risk: Maximum expected loss at confidence level
        - max_drawdown: Largest peak-to-trough decline
        - beta: Volatility relative to market
    """
    normalized = normalize_ticker(ticker)
    audit_logger.data_access(request, ticker=normalized)
    cache_key = cache_key_for("risk", normalized, f"c{confidence_level}")

    async def compute():
        toolkit = get_toolkit([normalized])

        var = await run_toolkit_call(
            lambda: toolkit.risk.get_value_at_risk(confidence_level=confidence_level),
            op="risk_var",
            ticker=normalized,
        )
        max_dd = await run_toolkit_call(
            lambda: toolkit.risk.get_maximum_drawdown(),
            op="risk_max_drawdown",
            ticker=normalized,
        )

        return {
            "ticker": normalized,
            "confidence_level": confidence_level,
            "value_at_risk": var.to_dict() if hasattr(var, 'to_dict') else float(var),
            "max_drawdown": max_dd.to_dict() if hasattr(max_dd, 'to_dict') else float(max_dd),
            "interpretation": {
                "var": f"At {confidence_level*100}% confidence, daily loss won't exceed this amount",
                "max_drawdown": "Largest historical peak-to-trough decline"
            }
        }

    try:
        return await cached_response(request, cache_key, compute, ticker=normalized)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to fetch risk metrics", extra={"ticker": normalized})
        raise HTTPException(status_code=500, detail=str(e))


# ============ COMPARISON ============

@app.post("/api/compare")
@limiter.limit("30/minute")
async def compare_tickers(
    http_request: Request,
    request: TickerRequest,
    api_key: str = Depends(verify_api_key),
):
    """
    Compare multiple tickers side by side.

    Returns key metrics for all requested tickers.
    """
    try:
        tickers = security_validators.validate_tickers(request.tickers)
        audit_logger.data_access(http_request, tickers=tickers)
        cache_key = cache_key_for(
            "compare",
            ",".join(sorted(tickers)),
            request.start_date or "none",
            f"q{int(request.quarterly)}",
        )

        async def compute():
            toolkit = get_toolkit(tickers, request.start_date, quarterly=request.quarterly)

            profitability = await run_toolkit_call(
                lambda: toolkit.ratios.collect_profitability_ratios(),
                op="ratios_profitability",
            )
            valuation = await run_toolkit_call(
                lambda: toolkit.ratios.collect_valuation_ratios(),
                op="ratios_valuation",
            )

            return {
                "tickers": tickers,
                "comparison": {
                    "profitability": profitability.to_dict(),
                    "valuation": valuation.to_dict()
                }
            }

        return await cached_response(http_request, cache_key, compute, tickers=tickers)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to compare tickers", extra={"tickers": request.tickers})
        raise HTTPException(status_code=500, detail=str(e))


# ============ QUICK ANALYSIS ============

@app.get("/api/quick-analysis/{ticker}")
@limiter.limit("30/minute")
async def quick_analysis(
    request: Request,
    ticker: str,
    api_key: str = Depends(verify_api_key),
):
    """
    Quick comprehensive analysis of a ticker.

    Returns a summary of key metrics across all categories.
    """
    normalized = normalize_ticker(ticker)
    audit_logger.data_access(request, ticker=normalized)
    cache_key = cache_key_for("quick", normalized)

    async def compute():
        toolkit = get_toolkit([normalized])

        # Get key metrics
        profitability = await run_toolkit_call(
            lambda: toolkit.ratios.collect_profitability_ratios(),
            op="ratios_profitability",
            ticker=normalized,
        )
        altman = await run_toolkit_call(
            lambda: toolkit.models.get_altman_z_score(),
            op="altman_z_score",
            ticker=normalized,
        )
        piotroski = await run_toolkit_call(
            lambda: toolkit.models.get_piotroski_f_score(),
            op="piotroski_f_score",
            ticker=normalized,
        )

        # Extract latest values
        latest_year = profitability.columns[-1] if not profitability.empty else "N/A"

        summary = {
            "ticker": ticker,
            "latest_period": str(latest_year),
            "profitability": {},
            "health_scores": {},
            "overall_assessment": ""
        }

        # Extract key profitability metrics
        if not profitability.empty:
            for metric in ['Gross Margin', 'Net Profit Margin', 'Return on Equity']:
                try:
                    val = profitability.loc[(normalized, metric), latest_year]
                    summary["profitability"][metric] = round(float(val) * 100, 2) if val else None
                except (KeyError, TypeError):
                    pass

        # Extract health scores
        altman_val = float(altman.iloc[:, -1].values[0]) if not altman.empty else None
        piotroski_val = int(piotroski.iloc[:, -1].values[0]) if not piotroski.empty else None

        summary["health_scores"] = {
            "altman_z_score": round(altman_val, 2) if altman_val else None,
            "piotroski_f_score": piotroski_val
        }

        # Generate overall assessment
        assessment_points = []
        if altman_val and altman_val > 2.99:
            assessment_points.append("Low bankruptcy risk")
        elif altman_val and altman_val < 1.81:
            assessment_points.append("HIGH bankruptcy risk")

        if piotroski_val and piotroski_val >= 8:
            assessment_points.append("Strong financial health")
        elif piotroski_val and piotroski_val <= 4:
            assessment_points.append("Weak financial health")

        summary["overall_assessment"] = "; ".join(assessment_points) if assessment_points else "Moderate"

        return summary

    try:
        return await cached_response(request, cache_key, compute, ticker=normalized)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed quick analysis", extra={"ticker": normalized})
        raise HTTPException(status_code=500, detail=str(e))


# ============ CACHE MANAGEMENT ============

@app.get("/api/cache/stats")
async def cache_stats():
    """Get cache statistics."""
    return db.get_cache_stats()


@app.get("/api/cache/tickers")
async def cached_tickers():
    """List all cached tickers."""
    return {"tickers": db.list_cached_tickers()}


@app.delete("/api/cache/{ticker}")
@limiter.limit("10/minute")
async def clear_ticker_cache(
    request: Request,
    ticker: str,
    api_key: str = Depends(verify_api_key),
):
    """Clear cache for a specific ticker."""
    audit_logger.log(AuditEvent.CACHE_CLEAR, request, ticker=ticker)
    db.clear_cache(ticker)
    return {"message": f"Cache cleared for {ticker}"}


@app.delete("/api/cache")
@limiter.limit("5/minute")
async def clear_all_cache(
    request: Request,
    api_key: str = Depends(verify_api_key),
):
    """Clear all cached data."""
    audit_logger.log(AuditEvent.CACHE_CLEAR, request, extra={"scope": "all"})
    db.clear_cache()
    return {"message": "All cache cleared"}


# Run with: uvicorn infrastructure.api:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
