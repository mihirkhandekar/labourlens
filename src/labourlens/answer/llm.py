"""Minimal OpenAI chat client with strict structured outputs. Reads the key from OPENAI_API_KEY only. Every call returns
latency and token usage so cost can be computed from measurements (D-022). Bounded: per-call timeout, limited retries
on transient errors, no hidden loops."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass

import httpx

from labourlens.answer.schema import json_schema

API = "https://api.openai.com/v1/chat/completions"
TIMEOUT_S = 180.0
MAX_RETRIES = 3


class LLMError(RuntimeError):
    pass


@dataclass
class LLMResult:
    content: str
    prompt_tokens: int
    completion_tokens: int
    reasoning_tokens: int
    seconds: float
    refusal: str | None = None


def chat(model: str, messages: list[dict], max_completion_tokens: int = 6000, extra: dict | None = None,
         schema: dict | None = None, schema_name: str = "answer") -> LLMResult:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise LLMError("OPENAI_API_KEY is not set")
    body = {"model": model, "messages": messages, "max_completion_tokens": max_completion_tokens,
            "response_format": {"type": "json_schema", "json_schema": {"name": schema_name, "strict": True, "schema": schema or json_schema()}},
            **(extra or {})}
    last = ""
    for attempt in range(MAX_RETRIES):
        t0 = time.perf_counter()
        try:
            r = httpx.post(API, json=body, headers={"Authorization": f"Bearer {key}"}, timeout=TIMEOUT_S)
        except httpx.TransportError as e:
            last = f"transport error: {type(e).__name__}"
            time.sleep(2 ** attempt)
            continue
        dt = time.perf_counter() - t0
        if r.status_code == 200:
            d = r.json()
            msg = d["choices"][0]["message"]
            u = d["usage"]
            return LLMResult(msg.get("content") or "", u["prompt_tokens"], u["completion_tokens"],
                             (u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0), dt, msg.get("refusal"))
        last = f"{r.status_code}: {r.text[:300]}"
        if r.status_code not in (429, 500, 502, 503, 504):
            raise LLMError(f"chat API {last}")
        time.sleep(2 ** attempt)
    raise LLMError(f"chat API failed after {MAX_RETRIES} attempts: {last}")
