# -*- coding: utf-8 -*-
import time
import threading
from typing import Dict, Any, Optional, Tuple


class IdempotencyService:
    """
    Enforces server-side idempotency across financial transactions,
    AI checkout requests, and disbursement operations using X-Idempotency-Key.
    Prevents duplicate charge and order replays within a TTL window.
    """

    def __init__(self, ttl_seconds: int = 900):  # 15 minutes TTL
        self.ttl_seconds = ttl_seconds
        self._lock = threading.Lock()
        # key -> (timestamp, response_dict)
        self._store: Dict[str, Tuple[float, Dict[str, Any]]] = {}

    def get_cached_response(self, idempotency_key: Optional[str]) -> Optional[Dict[str, Any]]:
        """Returns previously recorded response if key was executed within the TTL window."""
        if not idempotency_key:
            return None

        now = time.time()
        with self._lock:
            # Prune expired keys
            expired = [k for k, (ts, _) in self._store.items() if now - ts > self.ttl_seconds]
            for k in expired:
                del self._store[k]

            entry = self._store.get(idempotency_key)
            if entry:
                ts, res = entry
                if now - ts <= self.ttl_seconds:
                    res_copy = dict(res)
                    res_copy["idempotent_replay"] = True
                    return res_copy
        return None

    def record_response(self, idempotency_key: Optional[str], response_dict: Dict[str, Any]):
        """Caches response for the given idempotency key."""
        if not idempotency_key:
            return

        with self._lock:
            self._store[idempotency_key] = (time.time(), dict(response_dict))


idempotency_service = IdempotencyService(ttl_seconds=900)
