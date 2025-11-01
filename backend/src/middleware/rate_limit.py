"""Rate limiting middleware."""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request

limiter = Limiter(key_func=get_remote_address)


def get_rate_limiter():
    """Get rate limiter instance."""
    return limiter


def get_rate_limit_exceeded_handler():
    """Get rate limit exceeded handler."""
    return _rate_limit_exceeded_handler

