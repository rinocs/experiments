"""
Rate limiting per utente con sliding window in memoria.
- Configurable via env: RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW_SEC
- In produzione sostituire il dict in-memory con Redis (drop-in)
"""
import os, time
from collections import defaultdict, deque
from fastapi import HTTPException, status

RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "20"))
RATE_LIMIT_WINDOW_SEC = int(os.getenv("RATE_LIMIT_WINDOW_SEC", "60"))

_windows: dict[str, deque] = defaultdict(deque)


def check_rate_limit(user_id: str) -> None:
    """Sliding window rate limiter. Raises 429 se il limite è superato."""
    now = time.monotonic()
    window = _windows[user_id]

    # rimuovi richieste fuori dalla finestra
    while window and now - window[0] > RATE_LIMIT_WINDOW_SEC:
        window.popleft()

    if len(window) >= RATE_LIMIT_REQUESTS:
        retry_after = int(RATE_LIMIT_WINDOW_SEC - (now - window[0])) + 1
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit: max {RATE_LIMIT_REQUESTS} req/{RATE_LIMIT_WINDOW_SEC}s. Riprova tra {retry_after}s.",
            headers={"Retry-After": str(retry_after)},
        )

    window.append(now)
