"""In-memory rate limiting: per-visitor hourly and global daily caps.

Keeps API spend bounded without external services. State lives in RAM and
resets on container restart, which is acceptable for abuse protection.
"""

from __future__ import annotations

import threading
import time
from collections import deque

PER_HOUR_LIMIT: int = 15
PER_DAY_GLOBAL_LIMIT: int = 100
_HOUR_SECONDS: int = 3_600
_DAY_SECONDS: int = 86_400

HOURLY_REFUSAL: str = (
    "We've covered quite a lot this hour. Let's pick this up again a bit "
    "later — or book a call in the calendar below and we'll talk directly."
)
DAILY_REFUSAL: str = (
    "I'm getting a lot of questions today and pausing new answers for now. "
    "Book a call in the calendar below, or come back tomorrow."
)


class RateLimiter:
    """Sliding-window limiter: per-IP hourly cap plus a global daily cap."""

    def __init__(
        self,
        per_hour: int = PER_HOUR_LIMIT,
        per_day_global: int = PER_DAY_GLOBAL_LIMIT,
    ) -> None:
        self._per_hour = per_hour
        self._per_day_global = per_day_global
        self._by_ip: dict[str, deque[float]] = {}
        self._global: deque[float] = deque()
        self._lock = threading.Lock()

    def check(self, visitor_ip: str) -> str | None:
        """Register one message attempt and return a refusal text if over limit.

        Args:
            visitor_ip: Best-effort identifier of the visitor.

        Returns:
            None when the message is allowed; a first-person refusal otherwise.
        """
        now = time.time()
        with self._lock:
            self._prune(self._global, now - _DAY_SECONDS)
            if len(self._global) >= self._per_day_global:
                return DAILY_REFUSAL
            visitor_window = self._by_ip.setdefault(visitor_ip, deque())
            self._prune(visitor_window, now - _HOUR_SECONDS)
            if len(visitor_window) >= self._per_hour:
                return HOURLY_REFUSAL
            visitor_window.append(now)
            self._global.append(now)
            return None

    @staticmethod
    def _prune(window: deque[float], cutoff: float) -> None:
        """Drop timestamps older than ``cutoff`` from the left of the window."""
        while window and window[0] < cutoff:
            window.popleft()
