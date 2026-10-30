"""Fail-safe web admission events in the shared, pseudonymised audit stream."""
from datetime import datetime, timezone
import threading
import time

from labourlens.audit import log

KNOWN_ROUTES = frozenset({"/api/status", "/api/login", "/api/logout", "/api/ask", "/api/feedback"})
EVENT_MAX_BYTES = 1024 * 1024
EVENT_MAX_CLIENTS = 4096
_sample_lock = threading.Lock()
_sample_minute = -1
_sample_directory = None
_sample_clients: set[str | None] = set()


def _sample_client(client: str | None) -> bool:
    """At most one event per pseudonymous client per minute, with bounded state."""
    global _sample_minute, _sample_directory
    minute = int(time.monotonic() // 60)
    with _sample_lock:
        if minute != _sample_minute or _sample_directory != log.AUDIT_DIR:
            _sample_clients.clear()
            _sample_minute = minute
            _sample_directory = log.AUDIT_DIR
        if client in _sample_clients or len(_sample_clients) >= EVENT_MAX_CLIENTS:
            return False
        _sample_clients.add(client)
        return True


def log_event(kind: str, session: str | None, ip: str | None, detail: dict | None = None) -> None:
    """Store no questions, codes, tokens or raw client identifiers in admission logs."""
    try:
        route = (detail or {}).get("route")
        if route not in KNOWN_ROUTES:
            return
        client = log.salted_hash(ip)
        if not _sample_client(client):
            return
        now = datetime.now(timezone.utc)
        safe_detail = {key: value[:160] if isinstance(value, str) else value
                       for key, value in (detail or {}).items()
                       if key in {"route", "status", "reason"} and isinstance(value, (str, int, bool))}
        log._append(f"events-{now.date()}.jsonl", {
            "schema": log.SCHEMA_VERSION, "ts": now.isoformat(timespec="seconds"), "kind": kind[:64],
            "channel": "web", "session": log.salted_hash(session), "client": client, "detail": safe_detail,
        }, max_bytes=EVENT_MAX_BYTES)
    except Exception as error:
        # Salt acquisition can fail before the shared writer is reached.
        log._write_failure(error)


def log_injected_run(result: dict, question: str, session: str | None, ip: str | None) -> None:
    """Injected offline runners bypass run_agent's audit wrapper, so audit them once here."""
    try:
        normalized = {"question": question, "config": {"runner": "injected"}, "rounds": 0, "seconds": 0,
                      "outcome": "operational_failure", "usage": {}, "trace": [], **result}
        log.log_run(normalized, channel="web", session=session, ip=ip)
    except Exception:
        pass
