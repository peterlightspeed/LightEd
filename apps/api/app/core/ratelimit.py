"""Tiny in-memory sliding-window rate limiter used as a FastAPI dependency.

Per client IP + route bucket. Good enough for one instance (Render free tier). With several
instances switch the store to Redis (see todo.md). Returns 429 with a Retry-After header.
"""
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

from app.core.config import settings

_hits: dict[str, deque] = defaultdict(deque)


class RateLimiter:
    def __init__(self, limit: int, window_seconds: int, name: str):
        self.limit, self.window, self.name = limit, window_seconds, name

    def __call__(self, request: Request) -> None:
        if not settings.rate_limit_enabled:
            return
        fwd = request.headers.get("x-forwarded-for", "")
        ip = fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else "?")
        key, now = f"{self.name}:{ip}", time.monotonic()
        q = _hits[key]
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.limit:
            retry = max(1, int(self.window - (now - q[0])))
            raise HTTPException(429, f"Too many requests. Try again in {retry}s.", headers={"Retry-After": str(retry)})
        q.append(now)
        if len(_hits) > 5000:  # crude memory cap
            for k in [k for k, v in _hits.items() if not v][:1000]:
                _hits.pop(k, None)
