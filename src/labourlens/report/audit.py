"""Fail-safe web admission events in the shared, pseudonymised audit stream."""
from datetime import datetime, timezone

from labourlens.audit import log


def log_event(kind: str, session: str | None, ip: str | None, detail: dict | None = None) -> None:
    """Store no questions, codes, tokens or raw client identifiers in admission logs."""
    try:
        now = datetime.now(timezone.utc)
        safe_detail = {key: value for key, value in (detail or {}).items()
                       if key in {"route", "status", "reason"} and isinstance(value, (str, int, bool))}
        log._append(f"events-{now.date()}.jsonl", {
            "schema": log.SCHEMA_VERSION, "ts": now.isoformat(timespec="seconds"), "kind": kind,
            "channel": "web", "session": log.salted_hash(session), "client": log.salted_hash(ip), "detail": safe_detail,
        })
    except Exception:
        # The shared writer is already fail-safe; preserve that contract if a caller overrides it.
        pass


def log_injected_run(result: dict, question: str, session: str | None, ip: str | None) -> None:
    """Injected offline runners bypass run_agent's audit wrapper, so audit them once here."""
    try:
        normalized = {"question": question, "config": {"runner": "injected"}, "rounds": 0, "seconds": 0,
                      "outcome": "operational_failure", "usage": {}, "trace": [], **result}
        log.log_run(normalized, channel="web", session=session, ip=ip)
    except Exception:
        pass
