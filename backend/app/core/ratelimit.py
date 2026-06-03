"""
In-memory sliding-window rate limiter.

NOT for distributed deployment — state is per-process and lost on restart.
For multi-worker deployments, replace with Redis-backed implementation.
"""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable

from fastapi import HTTPException, Request, status


class _SlidingWindowCounter:
    __slots__ = ("_max_requests", "_window_seconds", "_requests")

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._requests: list[float] = []

    def is_allowed(self) -> bool:
        now = time.monotonic()
        cutoff = now - self._window_seconds
        self._requests = [t for t in self._requests if t > cutoff]
        if len(self._requests) >= self._max_requests:
            return False
        self._requests.append(now)
        return True


class RateLimiter:
    def __init__(self, max_requests: int = 5, window_seconds: int = 60) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._limits: dict[str, _SlidingWindowCounter] = defaultdict(
            lambda: _SlidingWindowCounter(max_requests, window_seconds)
        )

    def __call__(self, request: Request) -> None:
        key = self._make_key(request)
        if not self._limits[key].is_allowed():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {self._window_seconds}s.",
            )

    @staticmethod
    def _real_ip(request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host or "unknown"
        return "unknown"

    def _make_key(self, request: Request) -> str:
        client_ip = self._real_ip(request)
        route = request.url.path
        return f"{client_ip}:{route}"


# Pre-built rate limiters for auth endpoints
auth_rate_limit = RateLimiter(max_requests=10, window_seconds=60)
setup_rate_limit = RateLimiter(max_requests=5, window_seconds=60)
