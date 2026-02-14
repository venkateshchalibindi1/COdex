from __future__ import annotations

import time
from collections import defaultdict


class DomainThrottle:
    def __init__(self, delay_seconds: float) -> None:
        self.delay_seconds = delay_seconds
        self.last_called: dict[str, float] = defaultdict(float)

    def wait(self, domain: str) -> None:
        elapsed = time.time() - self.last_called[domain]
        to_sleep = self.delay_seconds - elapsed
        if to_sleep > 0:
            time.sleep(to_sleep)
        self.last_called[domain] = time.time()
