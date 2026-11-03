"""Minimal OpenAI chat client with strict structured outputs. Reads the key from OPENAI_API_KEY only. Every call returns
latency and token usage so cost can be computed from measurements (D-022). Bounded: per-call timeout, limited retries
on transient errors, no hidden loops."""

from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass

import httpx

from labourlens.answer.schema import json_schema

API = "https://api.openai.com/v1/chat/completions"
TIMEOUT_S = 180.0
MAX_RETRIES = 3


class LLMError(RuntimeError):
    def __init__(self, message: str, attempts: int = 0):
        super().__init__(message)
        self.attempts = attempts


@dataclass
class LLMResult:
    content: str
    prompt_tokens: int
    completion_tokens: int
    reasoning_tokens: int
    seconds: float
    refusal: str | None = None
    attempts: int = 1


async def _bounded_post(body: dict, key: str, seconds: float):
    """Cancel the HTTP operation at the total deadline, not just between socket reads."""
    async with httpx.AsyncClient(timeout=seconds) as client:
        return await asyncio.wait_for(
            client.post(API, json=body, headers={"Authorization": f"Bearer {key}"}), timeout=seconds
        )


def chat(model: str, messages: list[dict], max_completion_tokens: int = 6000, extra: dict | None = None,
         schema: dict | None = None, schema_name: str = "answer", timeout_s: float | None = None,
         max_attempts: int | None = None, retry_backoff_s: float | None = None, retry_all_5xx: bool = False) -> LLMResult:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise LLMError("OPENAI_API_KEY is not set")
    body = {"model": model, "messages": messages, "max_completion_tokens": max_completion_tokens,
            "response_format": {"type": "json_schema", "json_schema": {"name": schema_name, "strict": True, "schema": schema or json_schema()}},
            **(extra or {})}
    last = ""
    deadline = None if timeout_s is None else time.perf_counter() + timeout_s
    limit = MAX_RETRIES if max_attempts is None else max_attempts
    if limit < 1 or (retry_backoff_s is not None and retry_backoff_s < 0):
        raise ValueError("Invalid retry bounds")
    for attempt in range(limit):
        backoff = 2 ** attempt if retry_backoff_s is None else retry_backoff_s
        remaining = None if deadline is None else deadline - time.perf_counter()
        if remaining is not None and remaining <= 0:
            raise LLMError("chat deadline exceeded", attempts=attempt)
        t0 = time.perf_counter()
        try:
            if remaining is None:
                r = httpx.post(API, json=body, headers={"Authorization": f"Bearer {key}"}, timeout=TIMEOUT_S)
            else:
                r = asyncio.run(_bounded_post(body, key, remaining))
        except (httpx.TransportError, TimeoutError) as e:
            last = f"transport error: {type(e).__name__}"
            if deadline is not None:
                raise LLMError(last, attempts=attempt + 1) from e
            time.sleep(backoff)
            continue
        dt = time.perf_counter() - t0
        if r.status_code == 200:
            try:
                d = r.json()
                msg = d["choices"][0]["message"]
                u = d["usage"]
                return LLMResult(msg.get("content") or "", int(u["prompt_tokens"]), int(u["completion_tokens"]),
                                 (u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0), dt, msg.get("refusal"), attempt + 1)
            except (KeyError, IndexError, TypeError, ValueError, AttributeError) as e:  # malformed provider body is an operational failure
                raise LLMError(f"chat API returned an unexpected response shape: {type(e).__name__}", attempts=attempt + 1) from e
        last = f"{r.status_code}: {r.text[:300]}"
        transient = r.status_code in (429, 500, 502, 503, 504) or (retry_all_5xx and 500 <= r.status_code < 600)
        if not transient:
            raise LLMError(f"chat API {last}", attempts=attempt + 1)
        if (max_attempts is not None and attempt + 1 == limit) or (deadline is not None and deadline - time.perf_counter() <= backoff):
            raise LLMError(f"chat API {last}", attempts=attempt + 1)
        time.sleep(backoff)
    raise LLMError(f"chat API failed after {limit} attempts: {last}", attempts=limit)
