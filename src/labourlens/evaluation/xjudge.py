"""Pre-declared, paired second-family FIN judge; public outputs contain labels only."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import time

import httpx
import yaml

from labourlens import paths
from labourlens.evaluation import harness as h
from labourlens.evaluation.provenance import file_hash
from labourlens.retrieval.evaluate import load_cases

# Official ID: https://platform.claude.com/docs/en/models/overview (read 2026-11-02).
JUDGE_MODEL = "claude-sonnet-5-5"
MODEL_ENV = "LABOURLENS_XJUDGE_MODEL"
SEED = 20261102
SAMPLE_SIZE = 60
MAX_OUTPUT = 6000
API = "https://api.anthropic.com/v1/messages"
SETS = (("dev", "agent-dev-FIN", "gold_v3.7.jsonl"),
        ("heldout", "agent-heldout-FIN", "gold_v3.7.jsonl"),
        ("fresh", "agent-heldout-FINV2", "heldout_v2_v1.jsonl"))
MODELS = ("gpt-6-luna", "gpt-5.6-luna")


class JudgeError(RuntimeError):
    """Safe public error: never include provider bodies or request headers."""


class CapExceeded(JudgeError):
    pass


class IncompleteJudgement(JudgeError):
    """The schema is valid but the required claim/fact indices are not."""


def index_diagnostics(judgement: dict, case: dict, rec: dict) -> dict:
    return {field: {"expected": n, "returned": len(judgement[field]),
                    "indices": [row.get("index") for row in judgement[field]]}
            for field, n in (("claims", len(rec["answer"]["claims"])), ("facts", len(case["reference_facts"])))}


def redact(text: str) -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    return text.replace(key, "[REDACTED]") if key else text


def dump(path: Path, value) -> None:
    path.write_text(redact(json.dumps(value, indent=2, ensure_ascii=False)) + "\n")


def prices(model: str):
    entry = yaml.safe_load((paths.ROOT / "specs/prices.yaml").read_text())["chat"].get(model, {})
    return (entry["input"], entry["output"]) if entry.get("verified") is True else None


@dataclass
class Budget:
    maximum: float
    rates: tuple[float, float]
    charged: float = 0.0
    actual: float = 0.0

    def reserve(self, input_tokens: int, output_tokens: int) -> float:
        amount = (input_tokens * self.rates[0] + output_tokens * self.rates[1]) / 1e6
        if self.charged + amount > self.maximum:
            raise CapExceeded("Dollar cap: next attempt's worst-case reservation exceeds --max-usd")
        self.charged += amount
        return amount

    def settle(self, reserved: float, usage: dict) -> None:
        actual = (usage["input_tokens"] * self.rates[0] + usage["output_tokens"] * self.rates[1]) / 1e6
        self.actual += actual
        self.charged += actual - reserved
        if actual > reserved or self.charged > self.maximum:
            raise CapExceeded("Provider usage exceeded conservative reservation; no further calls permitted")


class AnthropicProvider:
    def call(self, model: str, system: str, user: str, budget: Budget) -> dict:
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise JudgeError("ANTHROPIC_API_KEY is not set")
        body = {"model": model, "max_tokens": MAX_OUTPUT, "system": system,
                "messages": [{"role": "user", "content": user}],
                "output_config": {"format": {"type": "json_schema", "schema": h.JUDGE_SCHEMA}}}
        bound = len(json.dumps(body, ensure_ascii=False).encode()) + 4096
        for attempt in range(3):
            reservation = budget.reserve(bound, MAX_OUTPUT)
            try:
                response = httpx.post(API, json=body, headers={"x-api-key": key, "anthropic-version": "2023-06-01"}, timeout=180.0)
            except httpx.TransportError:
                # Ambiguous billing: retain reservation even when no response arrived.
                if attempt == 2:
                    raise JudgeError("Anthropic transport failed after three attempts") from None
                time.sleep(2 ** attempt)
                continue
            if response.status_code != 200:
                if response.status_code in (429, 500, 502, 503, 504) and attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                raise JudgeError(f"Anthropic HTTP {response.status_code}; response body withheld")
            try:
                raw = response.json()
                usage = raw["usage"]
                if any(type(usage[k]) is not int or usage[k] < 0 for k in ("input_tokens", "output_tokens")):
                    raise ValueError()
                if usage.get("cache_creation_input_tokens", 0) or usage.get("cache_read_input_tokens", 0):
                    raise ValueError()  # caching is not requested; do not silently misprice it
                budget.settle(reservation, usage)
                blocks = [b for b in raw["content"] if b.get("type") == "text"]
                if raw["stop_reason"] != "end_turn" or len(blocks) != 1:
                    raise ValueError()
                return {"judgement": json.loads(blocks[0]["text"]), "usage": {k: usage[k] for k in ("input_tokens", "output_tokens")}}
            except (KeyError, TypeError, ValueError):
                raise JudgeError("Anthropic returned malformed/truncated judgement or usage") from None
        raise JudgeError("Anthropic attempts exhausted")


def validate(judgement: dict, case: dict, rec: dict) -> None:
    """Validate the shared schema plus complete, unique, zero-based indices."""
    if not isinstance(judgement, dict) or set(judgement) != {"claims", "facts"}:
        raise JudgeError("Invalid judgement object")
    for field, label, allowed, n in (("claims", "verdict", {"supported", "partial", "unsupported"}, len(rec["answer"]["claims"])),
                                      ("facts", "status", {"covered", "missing", "contradicted"}, len(case["reference_facts"]))):
        rows = judgement[field]
        if not isinstance(rows, list):
            raise JudgeError("Invalid judgement array")
        if len(rows) != n:
            raise IncompleteJudgement("Judgement label count mismatch")
        for row in rows:
            if (not isinstance(row, dict) or set(row) != {"index", label, "note"} or type(row["index"]) is not int
                    or row[label] not in allowed or not isinstance(row["note"], str)):
                raise JudgeError("Invalid judgement label")
        if sorted(row["index"] for row in rows) != list(range(n)):
            raise IncompleteJudgement("Judgement indices are not complete and unique")


def stratified_sample(items: list[dict], size: int = SAMPLE_SIZE, seed: int = SEED) -> list[dict]:
    strata = defaultdict(list)
    for item in items:
        strata[(item["set"], item["case"]["family"])].append(item)
    if len(items) < size:
        raise JudgeError(f"Only {len(items)} paired eligible cases; need {size}")
    keys = sorted(strata)
    allocation = {k: size * len(strata[k]) // len(items) for k in keys}
    remainder = sorted(keys, key=lambda k: (-(size * len(strata[k]) % len(items)), k))
    for k in remainder[:size - sum(allocation.values())]:
        allocation[k] += 1
    rng = random.Random(seed)
    selected = []
    for k in keys:
        selected.extend(rng.sample(sorted(strata[k], key=lambda x: x["case"]["case_id"]), allocation[k]))
    return sorted(selected, key=lambda x: (x["set"], x["case"]["case_id"]))


def load_sample() -> tuple[list[dict], dict]:
    selected, populations = [], {}
    for model in MODELS:
        candidates = []
        for set_name, base, gold_name in SETS:
            gold = paths.EXPERIMENTS / "gold" / gold_name
            cases = load_cases("dev" if set_name == "dev" else "heldout", gold)
            arms, judges = {}, {}
            for arm in ("r3", "hybrid"):
                exp = f"{base}-{arm}"
                raw = paths.DATA / "runs" / exp / f"{model}.jsonl"
                arms[arm] = {r["case_id"]: r for r in map(json.loads, raw.read_text().splitlines()) if h.judge_eligible(r)}
                judges[arm] = json.loads((paths.EXPERIMENTS / "eval" / exp / f"{model}.judgements.json").read_text())
            for case in cases:
                cid = case["case_id"]
                if not all(cid in arms[a] for a in arms):
                    continue
                entries = {}
                for arm in arms:
                    rec = arms[arm][cid]
                    cached = judges[arm].get(cid, {})
                    if rec.get("question") != case["question"] or cached.get("input_sha256") != h.judgement_hash(case, rec):
                        raise JudgeError(f"Missing/stale first-judge input: {model}/{set_name}/{arm}/{cid}")
                    original = {k: cached["judgement"][k] for k in ("claims", "facts")}
                    validate(original, case, rec)
                    entries[arm] = {"rec": rec, "original": original, "run": f"{base}-{arm}"}
                candidates.append({"model": model, "set": set_name, "case": case, "arms": entries, "gold_sha256": file_hash(gold)})
        populations[model] = dict(Counter(f"{i['set']}/{i['case']['family']}" for i in candidates))
        selected.extend(stratified_sample(candidates))
    return selected, populations


def agreement(left: list, right: list) -> dict:
    if len(left) != len(right):
        raise ValueError("Unpaired labels")
    n = len(left)
    if not n:
        return {"n": 0, "raw_agreement": None, "kappa": None}
    observed = sum(a == b for a, b in zip(left, right)) / n
    a, b = Counter(left), Counter(right)
    expected = sum(a[k] * b[k] for k in set(a) | set(b)) / n ** 2
    return {"n": n, "raw_agreement": observed, "kappa": (observed - expected) / (1 - expected) if expected < 1 else None}


def labels(j: dict) -> dict:
    return {field: [row[label] for row in sorted(j[field], key=lambda x: x["index"])]
            for field, label in (("claims", "verdict"), ("facts", "status"))}


def rates(rows: list[dict], judge: str) -> dict:
    out = {}
    for field, positive, metric in (("claims", "supported", "claim_support"), ("facts", "covered", "fact_coverage")):
        n = sum(len(r[judge][field]) for r in rows)
        yes = sum(r[judge][field].count(positive) for r in rows)
        out[metric] = {"positive": yes, "total": n, "rate": yes / n if n else None}
    return out


def analyse(rows: list[dict]) -> dict:
    sampled = rows
    omissions = [r for r in sampled if r.get("status") == "judge_omitted"]
    groups = defaultdict(list)
    for row in sampled:
        groups[(row["model"], row["set"], row["case_id"])].append(row)
    included = {key for key, pair in groups.items() if len(pair) == 2 and all(r.get("status", "valid") == "valid" for r in pair)}
    rows = [r for r in sampled if (r["model"], r["set"], r["case_id"]) in included]
    excluded = [{k: r[k] for k in ("model", "set", "case_id", "arm", "family")} for r in sampled
                if r.get("status", "valid") == "valid" and (r["model"], r["set"], r["case_id"]) not in included]
    denominators = {}
    for model in sorted({r["model"] for r in sampled}):
        for scope in ("all", "dev", "heldout", "fresh"):
            sub = [r for r in sampled if r["model"] == model and (scope == "all" or r["set"] == scope)]
            if not sub:
                continue
            omitted = sum(r.get("status") == "judge_omitted" for r in sub)
            analysed = sum(r["model"] == model and (scope == "all" or r["set"] == scope) for r in rows)
            denominators[f"{model}/{scope}"] = {"sampled_items": len(sub), "valid_items": len(sub) - omitted,
                                              "judge_omitted_items": omitted, "sampled_pairs": len(sub) // 2,
                                              "analysed_pairs": analysed // 2, "excluded_pairs": (len(sub) - analysed) // 2}
    comparisons = {}
    for name, field, predicate in (("claim_labels", "claims", None), ("any_unsupported", "claims", "unsupported"),
                                    ("any_contradicted", "facts", "contradicted")):
        left, right = [], []
        for r in rows:
            if predicate is None:
                left.extend(r["original"][field]); right.extend(r["second"][field])
            elif r["original"][field]:
                left.append(predicate in r["original"][field]); right.append(predicate in r["second"][field])
        comparisons[name] = agreement(left, right)
    arms = {}
    paired = {}
    for model in sorted({r["model"] for r in rows}):
        paired[model] = {}
        for scope in ("all", "dev", "heldout", "fresh"):
            sub = [r for r in rows if r["model"] == model and (scope == "all" or r["set"] == scope)]
            if not sub:
                continue
            arm_rates = {a: {j: rates([r for r in sub if r["arm"] == a], j) for j in ("original", "second")} for a in ("r3", "hybrid")}
            arms[f"{model}/{scope}"] = arm_rates
            paired[model][scope] = {}
            for field, positive, metric in (("claims", "supported", "claim_support"), ("facts", "covered", "fact_coverage")):
                differences = {}
                for judge in ("original", "second"):
                    rr, hr = (arm_rates[a][judge][metric]["rate"] for a in ("r3", "hybrid"))
                    by_id = defaultdict(dict)
                    for row in sub:
                        xs = row[judge][field]
                        if xs:
                            by_id[row["case_id"]][row["arm"]] = xs.count(positive) / len(xs)
                    ds = [x["r3"] - x["hybrid"] for x in by_id.values() if len(x) == 2]
                    differences[judge] = {"pooled_r3_minus_hybrid": rr - hr if rr is not None and hr is not None else None,
                                          "mean_paired_r3_minus_hybrid": sum(ds) / len(ds) if ds else None, "n_pairs": len(ds)}
                flips = {}
                for key in ("pooled_r3_minus_hybrid", "mean_paired_r3_minus_hybrid"):
                    a, b = (differences[j][key] for j in ("original", "second"))
                    flips[key] = a * b < 0 if a is not None and b is not None else None
                paired[model][scope][metric] = {"judges": differences, "sign_flip": flips}
    disagreements = defaultdict(list)
    for r in rows:
        if r["original"] != r["second"]:
            disagreements[r["family"]].append(r)
    return {"agreement": comparisons, "arm_rates": arms, "paired": paired, "disagreements_by_family": dict(disagreements),
            "denominators": denominators, "excluded_valid_partners": excluded,
            "judge_omitted": {"count": len(omissions), "by_family": dict(Counter(r["family"] for r in omissions)),
                              "by_arm": dict(Counter(f"{r['model']}/{r['arm']}" for r in omissions)), "items": omissions},
            "omission_problem": bool(omissions),
            "incompleteness_warning": "Rates and agreement are conditional on valid pairs; omitted items are not imputed." if omissions else None,
            "low_kappa_problem": any(v["kappa"] is not None and v["kappa"] < .4 for v in comparisons.values()),
            "sign_flip_problem": any(flag is True for model in paired.values() for scope in model.values() for metric in scope.values() for flag in metric["sign_flip"].values())}


def run(experiment: str, *, max_usd: float = 5, dry_run: bool = False, summary_only: bool = False, provider=None) -> int:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", experiment):
        raise ValueError("Experiment id must be a simple name")
    pub = paths.EXPERIMENTS / "xjudge" / experiment
    if summary_only:
        print((pub / "SUMMARY.md").read_text())
        print((pub / "summary.json").read_text())
        return 0
    if pub.exists():
        raise FileExistsError(f"Experiment id already exists: {experiment}")
    if not math.isfinite(max_usd) or max_usd <= 0:
        raise ValueError("--max-usd must be finite and positive")
    model = os.environ.get(MODEL_ENV, JUDGE_MODEL)
    selected, populations = load_sample()
    system = (paths.ROOT / "prompts/judge_v1.md").read_text()
    price = prices(model)
    calls = [(item, arm, h.judge_input(item["case"], item["arms"][arm]["rec"])) for item in selected for arm in ("r3", "hybrid")]
    input_estimate = sum(math.ceil(len((system + user).encode()) / 3) + 1024 for _, _, user in calls)
    plan = {"model": model, "original_judge": h.JUDGE_MODEL, "seed": SEED, "n_calls": len(calls), "eligible_populations": populations,
            "sample_counts": dict(Counter(f"{i['model']}/{i['set']}/{i['case']['family']}" for i in selected)),
            "input_tokens_estimate": input_estimate, "output_tokens_estimate": 1000 * len(calls),
            "estimated_usd": (input_estimate * price[0] + 1000 * len(calls) * price[1]) / 1e6 if price else None,
            "price_status": "verified list-price estimate, not invoice" if price else "UNVERIFIED: tokens only; paid run refused",
            "prompt_sha256": file_hash(paths.ROOT / "prompts/judge_v1.md"),
            "schema_sha256": hashlib.sha256(json.dumps(h.JUDGE_SCHEMA, sort_keys=True).encode()).hexdigest()}
    print(redact(json.dumps(plan, indent=2)))
    if dry_run:
        return 0
    if not price:
        raise JudgeError("No verified price for model override; cannot enforce dollar cap")
    provider = provider or AnthropicProvider()
    budget = Budget(max_usd, price)
    pub.mkdir(parents=True, exist_ok=False)
    cache_dir = paths.DATA / "runs" / "xjudge"
    cache_dir.mkdir(parents=True, exist_ok=True)
    rows, inputs, prepared = [], [], []
    for item, arm, user in calls:
        body = {"model": model, "system": system, "user": user, "schema": h.JUDGE_SCHEMA,
                "adapter": "anthropic-native-json-v1", "max_tokens": MAX_OUTPUT}
        digest = hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        case, entry = item["case"], item["arms"][arm]
        identity = {"case_id": case["case_id"], "family": case["family"], "model": item["model"], "set": item["set"], "arm": arm}
        inputs.append({**identity, "input_sha256": digest, "gold_sha256": item["gold_sha256"], "source_run": entry["run"],
                       "original_input_sha256": h.judgement_hash(case, entry["rec"])})
        prepared.append((case, entry, identity, digest, user))
    dump(pub / "sample.json", inputs)
    tokens = Counter()
    cached_calls = 0
    semantic_retries = 0
    attempt_count = 0
    status, error = "complete", None
    try:
        for case, entry, identity, digest, user in prepared:
            attempt_records = []
            for semantic_attempt in range(2):
                cache = cache_dir / f"{digest}{'.retry1' if semantic_attempt else ''}.json"
                from_cache = cache.exists()
                if from_cache:
                    result = json.loads(cache.read_text())
                    if result.get("input_sha256") != digest:
                        raise JudgeError("Cache fingerprint mismatch")
                    cached_calls += 1
                else:
                    result = provider.call(model, system, user, budget)
                    result["input_sha256"] = digest
                    dump(cache, result)
                tokens.update(result["usage"])
                attempt_count += 1
                if semantic_attempt:
                    semantic_retries += 1
                attempt_record = {"attempt": semantic_attempt, "cached": from_cache, "usage": result["usage"],
                                  "list_price_usd": (result["usage"]["input_tokens"] * price[0] + result["usage"]["output_tokens"] * price[1]) / 1e6}
                try:
                    validate(result["judgement"], case, entry["rec"])
                except IncompleteJudgement:
                    attempt_record.update(status="invalid_indices", diagnostics=index_diagnostics(result["judgement"], case, entry["rec"]))
                    attempt_records.append(attempt_record)
                    if semantic_attempt == 0:
                        continue
                    rows.append({**identity, "status": "judge_omitted", "reason": "incomplete_or_duplicate_or_extra_indices",
                                 "original": labels(entry["original"]), "second": None, "attempts": attempt_records})
                else:
                    attempt_record["status"] = "valid"
                    attempt_records.append(attempt_record)
                    rows.append({**identity, "status": "valid", "original": labels(entry["original"]),
                                 "second": labels(result["judgement"]), "attempts": attempt_records})
                break
    except Exception as exc:
        status = "aborted"
        # Only controlled messages are safe; no arbitrary provider/stub exception text.
        error = redact(str(exc)) if isinstance(exc, JudgeError) else f"Operational failure: {type(exc).__name__} (details withheld)"
    summary = {**plan, "status": status, "error": error, "completed_calls": len(rows), "cached_calls": cached_calls,
               "processed_judge_attempts": attempt_count, "semantic_retries": semantic_retries,
               "new_judge_attempts": attempt_count - cached_calls,
               "tokens_including_cached_calls": dict(tokens), "new_spend_list_price_usd": budget.actual,
               "charged_including_uncertain_attempt_reservations_usd": budget.charged, "max_usd": max_usd,
               "analysis": analyse(rows) if status == "complete" else None}
    dump(pub / "labels.json", rows)
    dump(pub / "summary.json", summary)
    text = (f"# Second-family judge: {experiment}\n\nStatus: **{status}**. Judge: `{model}` versus `{h.JUDGE_MODEL}`. "
            f"Completed {len(rows)}/{len(calls)} items ({cached_calls} cached attempts, {semantic_retries} semantic retries). New list-price spend ${budget.actual:.6f}; "
            f"budget accounting including uncertain attempts ${budget.charged:.6f}, cap ${max_usd:.2f}.\n\n"
            "See summary.json for agreement, paired differences, problem flags and family disagreements; labels.json contains labels only. "
            "No human review; one saved generation run, conditional paired answered sample; costs are token-based estimates, not invoices. "
            "Aborted runs have no inferential analysis.\n")
    if error:
        text += f"\nError: {error}\n"
    if summary["analysis"]:
        text += "\n```json\n" + json.dumps({k: v for k, v in summary["analysis"].items() if k != "disagreements_by_family"}, indent=2) + "\n```\n"
    (pub / "SUMMARY.md").write_text(redact(text))
    print(redact(text))
    return 0 if status == "complete" else 1
