"""Redaction for logs, traces and anything written to disk. Removes secrets, signed URLs and e-mail addresses (data minimisation)."""

from __future__ import annotations

import logging
import os
import re

_PATTERNS = [
    (re.compile(r"sk-[A-Za-z0-9_\-]{16,}"), "[REDACTED_API_KEY]"),
    (re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._\-]{12,}"), r"\1[REDACTED_TOKEN]"),
    (re.compile(r"(?i)(x-amz-signature|signature|token|key)=([^&\s\\\"']{6,})"), r"\1=[REDACTED]"),
    (re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"), "[REDACTED_EMAIL]"),
]
SECRET_ENV_HINTS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL")


def secret_values() -> list[str]:
    """Values of secret-looking environment variables in this process (length 8 or more), used for exact-match redaction."""
    values = [v for k, v in os.environ.items() if any(h in k.upper() for h in SECRET_ENV_HINTS) and len(v) >= 8]
    values.extend(code.strip() for code in os.getenv("LABOURLENS_ACCESS_CODES", "").split(",") if len(code.strip()) >= 8)
    return values


def redact(text: str, extra_secrets: list[str] | None = None) -> str:
    for s in sorted({s for s in (extra_secrets or []) + secret_values() if len(s) >= 8}, key=len, reverse=True):
        text = text.replace(s, "[REDACTED_SECRET]")
    for pat, rep in _PATTERNS:
        text = pat.sub(rep, text)
    return text


def redact_values(value, extra_secrets: list[str] | None = None):
    """Redact string values before serialization, preserving dictionary keys and types."""
    if isinstance(value, str):
        return redact(value, extra_secrets)
    if isinstance(value, dict):
        return {key: redact_values(item, extra_secrets) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_values(item, extra_secrets) for item in value]
    return value


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact(record.getMessage())
        record.args = None
        return True
