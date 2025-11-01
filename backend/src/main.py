"""
FastAPI application for Restaurant Voice Assistant.

Multi-tenant RAG system with vector similarity search, caching,
and secure webhook endpoints for Vapi.ai integration.
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from src.api import vapi, embeddings, health
from src.api.calls import router as calls_router
from src.api.restaurants import router as restaurants_router
from src.config import get_settings
from src.middleware.request_id import RequestIDMiddleware, get_request_id
from src.middleware.rate_limit import get_rate_limiter, get_rate_limit_exceeded_handler
import logging
import sys

settings = get_settings()

log_level = logging.DEBUG if settings.environment == "development" else logging.INFO

class RequestIDFormatter(logging.Formatter):
    """Custom formatter that handles request_id in log records."""
    def format(self, record):
        request_id = getattr(record, 'request_id', 'N/A')
        record.request_id = request_id
        return super().format(record)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(RequestIDFormatter('%(asctime)s - [%(name)s] [request_id=%(request_id)s] - %(levelname)s - %(message)s'))
logging.basicConfig(level=log_level, handlers=[handler])

app = FastAPI(
    title="Restaurant Voice Assistant API",
    description="Multi-tenant RAG system for Vapi voice assistants",
    version="1.0.0"
)

limiter = get_rate_limiter()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, get_rate_limit_exceeded_handler())

app.add_middleware(RequestIDMiddleware)

cors_origins = (
    ["*"] if settings.cors_origins == "*"
    else [origin.strip() for origin in settings.cors_origins.split(",")]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(vapi.router, prefix="/api/vapi", tags=["Vapi"])
app.include_router(embeddings.router,
                   prefix="/api/embeddings", tags=["Embeddings"])
app.include_router(calls_router, prefix="/api", tags=["Calls"])
app.include_router(restaurants_router, prefix="/api", tags=["Restaurants"])


if settings.rate_limit_enabled:
    from slowapi.util import get_remote_address
    
    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        """Apply rate limiting to all endpoints except health checks and docs."""
        if request.url.path.startswith("/api/health") or request.url.path.startswith("/docs") or request.url.path.startswith("/openapi.json") or request.url.path == "/":
            return await call_next(request)
        
        per_minute = settings.rate_limit_per_minute
        try:
            limiter.check(f"{per_minute}/minute", key_func=lambda: get_remote_address(request))
        except RateLimitExceeded:
            request_id = get_request_id(request)
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Rate limit exceeded for {get_remote_address(request)}",
                extra={"request_id": request_id, "path": request.url.path}
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"Rate limit exceeded: {per_minute} requests per minute",
                    "request_id": request_id
                }
            )
        
        return await call_next(request)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc):
    """Handle unexpected errors without exposing internal details."""
    logger = logging.getLogger(__name__)
    request_id = get_request_id(request)
    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True,
        extra={"request_id": request_id}
    )

    error_detail = {"detail": "An internal error occurred", "request_id": request_id}
    if settings.environment != "production":
        error_detail["error"] = str(exc)
    
    return JSONResponse(
        status_code=500,
        content=error_detail
    )


@app.get("/")
async def root():
    return {
        "message": "Restaurant Voice Assistant API",
        "docs": "/docs",
        "health": "/api/health"
    }
