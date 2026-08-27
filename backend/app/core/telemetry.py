import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List
from datetime import datetime
import threading

logger = logging.getLogger(__name__)

@dataclass
class TelemetryEntry:
    timestamp: datetime
    operation: str
    latency_ms: float
    llm_calls: int = 0
    tokens_used: int = 0
    estimated_cost: float = 0.0
    success: bool = True
    cache_hit: bool = False
    error: str = ""

class TelemetryTracker:
    def __init__(self):
        self._entries: List[TelemetryEntry] = []
        self._lock = threading.Lock()
        self._total_llm_calls: int = 0
        self._total_tokens: int = 0
        self._total_cost: float = 0.0
        self._total_requests: int = 0
        self._failed_requests: int = 0
        self._cache_hits: int = 0

    def record(self, entry: TelemetryEntry):
        with self._lock:
            self._entries.append(entry)
            self._total_requests += 1
            self._total_llm_calls += entry.llm_calls
            self._total_tokens += entry.tokens_used
            self._total_cost += entry.estimated_cost
            if not entry.success:
                self._failed_requests += 1
            if entry.cache_hit:
                self._cache_hits += 1

    def get_summary(self) -> dict:
        with self._lock:
            recent = self._entries[-100:] if self._entries else []
            avg_latency = sum(e.latency_ms for e in recent) / max(len(recent), 1)
            success_rate = ((self._total_requests - self._failed_requests) / max(self._total_requests, 1)) * 100
            return {
                "total_requests": self._total_requests,
                "failed_requests": self._failed_requests,
                "success_rate": round(success_rate, 1),
                "average_latency_ms": round(avg_latency, 1),
                "total_llm_calls": self._total_llm_calls,
                "total_tokens": self._total_tokens,
                "estimated_cost": round(self._total_cost, 4),
                "cache_hits": self._cache_hits,
                "cache_hit_rate": round((self._cache_hits / max(self._total_requests, 1)) * 100, 1),
            }

    def get_recent(self, limit: int = 50) -> list:
        with self._lock:
            return [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "operation": e.operation,
                    "latency_ms": e.latency_ms,
                    "llm_calls": e.llm_calls,
                    "tokens_used": e.tokens_used,
                    "estimated_cost": e.estimated_cost,
                    "success": e.success,
                    "cache_hit": e.cache_hit,
                }
                for e in self._entries[-limit:]
            ]

telemetry = TelemetryTracker()

class TelemetryContext:
    def __init__(self, operation: str):
        self.operation = operation
        self.start_time = 0
        self.llm_calls = 0
        self.tokens_used = 0
        self.estimated_cost = 0.0
        self.cache_hit = False

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        latency_ms = (time.time() - self.start_time) * 1000
        entry = TelemetryEntry(
            timestamp=datetime.utcnow(),
            operation=self.operation,
            latency_ms=latency_ms,
            llm_calls=self.llm_calls,
            tokens_used=self.tokens_used,
            estimated_cost=self.estimated_cost,
            success=exc_type is None,
            cache_hit=self.cache_hit,
            error=str(exc_val) if exc_val else "",
        )
        telemetry.record(entry)
        return False
