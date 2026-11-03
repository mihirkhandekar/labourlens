"""Process-local annual-serving caches; no credentials or raw questions are retained as keys.

The immutable corpus fingerprint is part of every key. LRU and TTL bound retention;
failed/fallback/quarantined work is never retained. A waiter has its own deadline.
Disk query vectors remain owned by dense.embed/VectorCache, not this module.
"""
from __future__ import annotations

from collections import OrderedDict
from concurrent.futures import Future
from dataclasses import dataclass
import hashlib
import json
import threading
import time
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


def normalise(text: str) -> str:
    """Whitespace only: preserve case, punctuation, numbers, periods and word order."""
    return " ".join(text.split())


def identity(*parts) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()


@dataclass
class _Entry(Generic[T]):
    value: T
    expires: float


class SingleflightLRU(Generic[T]):
    """Bound both completed entries and in-flight keys; compute outside the lock.

    At capacity, unrelated misses run uncached rather than creating an unbounded
    pending table. Exceptions propagate to current waiters but never enter the LRU.
    """

    def __init__(self, capacity: int, ttl_s: float = 300.0):
        if capacity < 1 or ttl_s <= 0:
            raise ValueError("positive cache capacity and TTL required")
        self.capacity, self.ttl_s = capacity, ttl_s
        self._lock = threading.Lock()
        self._entries: OrderedDict[str, _Entry[T]] = OrderedDict()
        self._pending: dict[str, Future] = {}

    def get_or_compute(self, key: str, compute: Callable[[], T], *, eligible: Callable[[T], bool] = lambda _: True,
                       timeout_s: float = 10.0) -> tuple[T, bool]:
        with self._lock:
            now = time.monotonic()
            for expired in [k for k, v in self._entries.items() if v.expires <= now]:
                del self._entries[expired]
            entry = self._entries.get(key)
            if entry is not None:
                self._entries.move_to_end(key)
                return entry.value, True
            pending = self._pending.get(key)
            owner = pending is None
            if owner and len(self._pending) < self.capacity:
                pending = self._pending[key] = Future()
            elif owner:
                pending = None
        if not owner:
            return pending.result(timeout=max(0.0, timeout_s)), True
        try:
            value = compute()
            retain = eligible(value)
            with self._lock:
                if retain:
                    self._entries[key] = _Entry(value, time.monotonic() + self.ttl_s)
                    self._entries.move_to_end(key)
                    while len(self._entries) > self.capacity:
                        self._entries.popitem(last=False)
                if pending is not None:
                    self._pending.pop(key, None)
            if pending is not None:
                pending.set_result(value)
            return value, False
        except BaseException as exc:
            with self._lock:
                if pending is not None:
                    self._pending.pop(key, None)
            if pending is not None:
                pending.set_exception(exc)
            raise


SEARCHES: SingleflightLRU = SingleflightLRU(64)
QUERY_VECTORS: SingleflightLRU = SingleflightLRU(256)


def query_vector(corpus: dict, model: str, query: str, timeout_s: float):
    """Read existing disk VectorCache via embed on RAM miss; only cold disk misses use network."""
    from labourlens.retrieval import dense

    text = normalise(query)
    key = identity("annual-query-v1", corpus, model, text)

    def compute():
        with dense.embedding_deadline(timeout_s):
            vector = dense.embed(model, [text], purpose="queries")[0]
        vector.setflags(write=False)
        return vector

    return QUERY_VECTORS.get_or_compute(key, compute, timeout_s=timeout_s)[0]
