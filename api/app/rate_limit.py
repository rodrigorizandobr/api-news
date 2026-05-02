"""Rate limiting configuration for api-news."""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize limiter with IP-based rate limiting
limiter = Limiter(key_func=get_remote_address)

# Default rate limit: 10 requests per minute per IP
DEFAULT_RATE_LIMIT = "10/minute"

# Higher limit for /health endpoint
HEALTH_RATE_LIMIT = "100/minute"

# News endpoint rate limit
NEWS_RATE_LIMIT = "5/minute"
