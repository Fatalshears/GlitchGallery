"""Thread-safe token bucket used to cap total download bandwidth."""

import threading
import time
from typing import Callable


class TokenBucket:
    """Allows `rate` tokens per second on average, with bursts up to `capacity`.

    One token = one byte here. `clock` and `sleep` are injectable so tests can
    run without real waiting.
    """

    def __init__(
        self,
        rate: float,
        capacity: float | None = None,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ):
        if rate <= 0:
            raise ValueError("rate must be > 0")
        self.rate = rate
        self.capacity = capacity if capacity is not None else rate
        self._tokens = self.capacity
        self._clock = clock
        self._sleep = sleep
        self._last = clock()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = self._clock()
        self._tokens = min(self.capacity, self._tokens + (now - self._last) * self.rate)
        self._last = now

    def consume(self, n: int) -> None:
        """Block until `n` tokens are available, then take them.

        Requests larger than `capacity` are taken in capacity-sized slices so
        they cannot deadlock.
        """
        while n > 0:
            take = min(n, self.capacity)
            with self._lock:
                self._refill()
                if self._tokens >= take:
                    self._tokens -= take
                    n -= take
                    continue
                wait = (take - self._tokens) / self.rate
            self._sleep(wait)
