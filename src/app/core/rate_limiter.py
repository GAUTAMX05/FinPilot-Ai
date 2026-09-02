# -*- coding: utf-8 -*-
import time
import threading
from typing import Dict, Tuple, Optional, Any
from fastapi import HTTPException


class RateLimiter:
    """
    Sliding window in-memory rate limiter and daily AI token/request cost governor.
    Prevents API abuse, denial-of-service, and runaway LLM billing.
    """

    def __init__(self, max_requests_per_minute: int = 30, daily_request_cap: int = 200, daily_token_cap: int = 100000):
        self.max_requests_per_minute = max_requests_per_minute
        self.daily_request_cap = daily_request_cap
        self.daily_token_cap = daily_token_cap
        
        self._lock = threading.Lock()
        # client_key -> list of timestamps
        self._minute_windows: Dict[str, list] = {}
        # client_key -> (day_timestamp, request_count, estimated_tokens)
        self._daily_usage: Dict[str, Tuple[float, int, int]] = {}

    def check_rate_limit(self, client_key: str, estimated_tokens: int = 250) -> Dict[str, Any]:
        """
        Validates whether client request is within both the 1-minute rate window
        and the 24-hour cost/token budget.
        Raises HTTP 429 if exceeded.
        """
        now = time.time()
        with self._lock:
            # 1. Minute Window Check
            timestamps = self._minute_windows.setdefault(client_key, [])
            # Prune timestamps older than 60 seconds
            self._minute_windows[client_key] = [t for t in timestamps if now - t < 60.0]
            
            if len(self._minute_windows[client_key]) >= self.max_requests_per_minute:
                retry_after = int(60.0 - (now - self._minute_windows[client_key][0])) + 1
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded: Maximum {self.max_requests_per_minute} AI requests per minute allowed. Please wait {retry_after} seconds before retrying.",
                    headers={"Retry-After": str(max(1, retry_after))}
                )

            # 2. Daily Cost Budget Check
            day_start, req_count, token_count = self._daily_usage.get(client_key, (now, 0, 0))
            # Reset daily budget after 86400 seconds (24 hours)
            if now - day_start >= 86400.0:
                day_start, req_count, token_count = now, 0, 0

            if req_count >= self.daily_request_cap or token_count >= self.daily_token_cap:
                raise HTTPException(
                    status_code=429,
                    detail=f"Daily AI cost safety budget reached ({req_count}/{self.daily_request_cap} calls, {token_count}/{self.daily_token_cap} tokens). Service protected from unbounded LLM spend. Resets daily.",
                    headers={"Retry-After": "3600"}
                )

            # Record this call
            self._minute_windows[client_key].append(now)
            self._daily_usage[client_key] = (day_start, req_count + 1, token_count + estimated_tokens)

            return {
                "allowed": True,
                "remaining_minute_requests": self.max_requests_per_minute - len(self._minute_windows[client_key]),
                "daily_requests_used": req_count + 1,
                "daily_request_cap": self.daily_request_cap,
            }


rate_limiter = RateLimiter(max_requests_per_minute=30, daily_request_cap=200, daily_token_cap=100000)
