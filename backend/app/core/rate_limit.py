from __future__ import annotations

import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.responses import JSONResponse


class InMemoryRateLimiter:
    """Small per-process sliding-window limiter for MVP request protection."""

    def __init__(self, limit_per_minute: int) -> None:
        self.limit_per_minute = limit_per_minute
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    async def __call__(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.method == "OPTIONS":
            return await call_next(request)

        now = time.monotonic()
        client = request.client.host if request.client else "unknown"
        bucket = self._hits[client]
        while bucket and now - bucket[0] > 60:
            bucket.popleft()

        if len(bucket) >= self.limit_per_minute:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again shortly."},
            )

        bucket.append(now)
        return await call_next(request)
