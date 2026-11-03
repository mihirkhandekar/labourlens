"""Experimental Decisions client. No production callsites; bodies and keys never enter errors."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
import fcntl
import json
import math
import os
from pathlib import Path
import time

import httpx

API = "https://api.openai.com/v1/decisions"
MODEL = "gpt-6-luna"
TIMEOUT = 8.0
# Official Decisions guide, Pricing and availability, inspected 3 November 2026.
# Cache writes conservatively use the higher standard 12-hour rate for reservations.
INPUT_RATE, READ_RATE, WRITE_RATE = 0.10, 0.01, 0.25


class DecisionError(RuntimeError):
    pass


class BudgetExceeded(DecisionError):
    pass


def finite_probability(value):
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
        raise DecisionError("invalid_probability")
    return float(value)


def parse_answer(data: dict, question: dict) -> dict:
    try:
        answers = data["answers"]
        if not isinstance(answers, list) or len(answers) != 1:
            raise DecisionError("invalid_answer_count")
        a = answers[0]
        if a.get("name") != question["name"]:
            raise DecisionError("invalid_answer_name")
        if a.get("type") == "refusal":
            raise DecisionError("refusal")
        if a.get("type") != question["type"]:
            raise DecisionError("invalid_answer_type")
        if a["type"] == "predicate":
            return {"probability": finite_probability(a["probability"])}
        allowed = [c["value"] for c in question["choices"]]
        ps = a["probabilities"]
        if not isinstance(ps, list) or len(ps) != len(allowed):
            raise DecisionError("invalid_distribution")
        vals = [p["value"] for p in ps]
        if len(set(vals)) != len(allowed) or set(vals) != set(allowed) or a["choice"] not in allowed:
            raise DecisionError("invalid_choice")
        probs = {p["value"]: finite_probability(p["probability"]) for p in ps}
        if abs(sum(probs.values()) - 1) > 0.001:
            raise DecisionError("invalid_distribution")
        return {"choice": a["choice"], "confidence": finite_probability(a["confidence"]), "probabilities": probs}
    except (KeyError, TypeError, AttributeError, ValueError):
        raise DecisionError("invalid_answer_shape") from None


def usage_info(data: dict) -> dict:
    try:
        u = data["usage"]
        n = u["input_tokens"]
        out = u.get("output_tokens", 0)
        details = u.get("input_tokens_details") or {}
        reads = details.get("cached_tokens", 0)
        writes = details.get("cache_write_tokens", 0)
        if any(type(v) is not int or v < 0 for v in (n, out, reads, writes)) or reads + writes > n:
            raise ValueError()
        # Without documented write duration, retain the reservation and mark cost unknown.
        cost = None if writes else ((n - reads) * INPUT_RATE + reads * READ_RATE) / 1e6
        return {"input_tokens": n, "output_tokens": out, "cached_tokens": reads,
                "cache_write_tokens": writes, "cost_usd": cost, "price_status": "unknown_cache_write_duration" if writes else "verified_list_price"}
    except (KeyError, TypeError, ValueError, AttributeError):
        raise DecisionError("invalid_usage") from None


class Budget:
    """File-locked shared ledger. Ambiguously billed attempts retain their reservation."""
    def __init__(self, path: Path, maximum: float = 3.0):
        if not math.isfinite(maximum) or not 0 < maximum <= 3:
            raise ValueError("Budget must be positive and no more than $3")
        self.path, self.maximum = path, maximum

    def _update(self, delta: float, *, reserve=False):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.seek(0)
            content = f.read()
            d = json.loads(content) if content else {"charged_usd": 0.0, "maximum_usd": self.maximum}
            if d["maximum_usd"] != self.maximum:
                raise DecisionError("shared_budget_limit_mismatch")
            amount = d["charged_usd"] + delta
            if reserve and amount > self.maximum:
                raise BudgetExceeded("shared_dollar_cap")
            d["charged_usd"] = max(0.0, amount)
            f.seek(0)
            f.truncate()
            json.dump(d, f)
            f.flush()
            os.fsync(f.fileno())
            if amount > self.maximum:
                raise BudgetExceeded("usage_exceeded_reservation")

    def reserve(self, body: dict) -> float:
        # UTF-8 bytes upper-bound token count, plus protocol overhead; no output charge.
        amount = (len(json.dumps(body, ensure_ascii=False).encode()) + 4096) * WRITE_RATE / 1e6
        self._update(amount, reserve=True)
        return amount

    def settle(self, reserved: float, usage: dict):
        if usage["cost_usd"] is None:
            raise DecisionError("unknown_cost_stop")
        self._update(usage["cost_usd"] - reserved)


async def _post(body, key, remaining):
    async with httpx.AsyncClient(timeout=remaining) as client:
        return await asyncio.wait_for(client.post(API, json=body, headers={"Authorization": f"Bearer {key}"}), remaining)


@dataclass
class Client:
    budget: Budget
    post: object = None

    def call(self, body: dict) -> dict:
        start = time.perf_counter()
        result = {"error": None, "seconds": 0.0, "attempts": 0,
                  "usage": {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}}
        unsettled = False
        known_attempts = 0
        try:
            key = os.environ.get("OPENAI_API_KEY")
            if not key:
                raise DecisionError("missing_api_key")
            for attempt in range(2):
                remaining = TIMEOUT - (time.perf_counter() - start)
                if remaining <= 0:
                    raise DecisionError("deadline")
                reservation = self.budget.reserve(body)
                unsettled = True
                result["attempts"] += 1
                if self.post is None:
                    response = asyncio.run(_post(body, key, remaining))
                else:
                    response = self.post(body, remaining)
                if response.status_code != 200:
                    # No reliable usage on error; keep reservation, include unknown total cost.
                    result["usage"]["cost_usd"] = None
                    if (response.status_code == 429 or 500 <= response.status_code < 600) and attempt == 0 and TIMEOUT - (time.perf_counter() - start) > 0.5:
                        time.sleep(0.5)
                        continue
                    raise DecisionError(f"http_{response.status_code}")
                data = response.json()
                usage = usage_info(data)
                known_attempts += 1
                for k in ("input_tokens", "output_tokens"):
                    result["usage"][k] += usage[k]
                result["usage"].update({k: v for k, v in usage.items() if k not in ("input_tokens", "output_tokens", "cost_usd")})
                prior = result["usage"]["cost_usd"]
                result["usage"]["cost_usd"] = None if prior is None or usage["cost_usd"] is None else prior + usage["cost_usd"]
                self.budget.settle(reservation, usage)
                unsettled = False
                if time.perf_counter() - start > TIMEOUT:
                    raise DecisionError("deadline")
                result.update(parse_answer(data, body["questions"][0]))
                break
        except BudgetExceeded as e:
            result["error"] = str(e)
            result["stop"] = True
            if unsettled:
                result["usage"]["cost_usd"] = None
        except DecisionError as e:
            result["error"] = str(e)
            if unsettled:
                result["usage"]["cost_usd"] = None
        except (httpx.TransportError, TimeoutError):
            result["error"] = "transport_timeout"
            result["usage"]["cost_usd"] = None
        except Exception:
            result["error"] = "invalid_provider_response"
            result["usage"]["cost_usd"] = None
        result["seconds"] = time.perf_counter() - start
        result["usage"]["complete"] = known_attempts == result["attempts"]
        return result
