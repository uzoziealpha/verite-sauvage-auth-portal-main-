# backend-python/app/middleware/ratelimit.py

import time
from typing import Dict, Tuple
from fastapi import Request, HTTPException

# Simple in-memory rate limiting:
# max 30 requests per minute per IP, only on /customer-verify
WINDOW_SECONDS = 60
MAX_REQUESTS = 30

# IP -> (window_start_ts, count)
_request_log: Dict[str, Tuple[float, int]] = {}


async def rate_limit(request: Request):
    """
    Very simple per-IP rate limiter for /customer-verify.

    For real production at scale, combine this with Cloudflare / a proper limiter.
    """
    path = request.url.path
    if not path.startswith("/customer-verify"):
        return

    ip = request.client.host or "unknown"
    now = time.time()

    window_start, count = _request_log.get(ip, (now, 0))

    # Reset window if older than WINDOW_SECONDS
    if now - window_start > WINDOW_SECONDS:
        window_start, count = now, 0

    count += 1
    _request_log[ip] = (window_start, count)

    if count > MAX_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please wait and try again.",
        )
