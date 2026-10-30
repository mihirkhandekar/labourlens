"""Redaction for logs, traces and anything written to disk. Removes secrets, signed URLs and e-mail addresses (data minimisation)."""

from __future__ import annotations

import logging
import os
import re

_PATTERNS = [
    (re.compile(r"sk-[A-Za-z0-9_\-]{16,}"), "[REDACTED_API_KEY]"),
    (re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._\-]{12,}"), r"\1[REDACTED_TOKEN]"),
    (re.compile(r"(?i)(x-amz-signature|signature|token|key)=([^&\s\"']{6,})"), r"\1=[REDACTED]"),
    (re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"), "[REDACTED_EMAIL]"),
]
SECRET_ENV_HINTS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL")


def secret_values() -> list[str]:
    """Values of secret-looking environment variables in this process (length 8 or more), used for exact-match redaction."""
    return [v for k, v in os.environ.items() if any(h in k.upper() for h in SECRET_ENV_HINTS) and len(v) >= 8]


def redact(text: str, extra_secrets: list[str] | None = None) -> str:
    for s in sorted(set((extra_secrets or []) + secret_values()), key=len, reverse=True):
        text = text.replace(s, "[REDACTED_SECRET]")
    for pat, rep in _PATTERNS:
        text = pat.sub(rep, text)
    return text


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact(record.getMessage())
        record.args = None
        return True
