from collections import defaultdict, deque
from threading import Lock
from time import monotonic
from fastapi import HTTPException, Request

_attempts: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()


def clear_limits() -> None:
    """Clear in-memory buckets; used by isolated tests and operational resets."""
    with _lock:
        _attempts.clear()


def limit_auth(max_attempts: int):
    """Small single-process auth limiter; replace with Redis when horizontally scaling."""
    async def check(request: Request) -> None:
        key = f"{request.url.path}:{request.client.host if request.client else 'unknown'}"
        now = monotonic()
        with _lock:
            entries = _attempts[key]
            while entries and entries[0] < now - 60:
                entries.popleft()
            if len(entries) >= max_attempts:
                raise HTTPException(429, "Too many authentication attempts; try again shortly")
            entries.append(now)
    return check
