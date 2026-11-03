"""Dev-only prompt tuning and a committed, contemporaneous fresh routing trial."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import html
import json
import os
from pathlib import Path
import re
import subprocess
import time

from labourlens import paths, prices
from labourlens.agent import decisions, triage
from labourlens.answer import llm
from labourlens.answer.pipeline import load_prompt
from labourlens.evaluation import decisions_exp as v1

PREREG = paths.ROOT / "docs/experiments/decisions-api-v2-prereg.md"
FRESH = paths.EXPERIMENTS / "triage/fresh_cases_v2.jsonl"
SELECTION = paths.EXPERIMENTS / "triage/decisions-v2-selection.json"
THRESHOLDS = (0.0, 0.3, 0.5, 0.7, 0.9)
GLOBAL_BUDGET = paths.DATA / "runs/decisions-api-budget.json"
TUNE_BUDGET = paths.DATA / "runs/decisions-api-v2-tuning-budget.json"
FRESH_SHA256 = "fc431214c64643b5d8e63f76e4ad39a9fd31c6d61566613d9ab372d7016f8a7d"


def utc():
    return datetime.now(timezone.utc).isoformat()


def committed(path):
    rel = str(path.relative_to(paths.ROOT))
    p = subprocess.run(["git", "log", "-1", "--format=%H", "--", rel], cwd=paths.ROOT, capture_output=True, text=True, check=True)
    if not p.stdout.strip():
        raise ValueError(f"Commit before paid execution: {rel}")
    content = subprocess.run(["git", "show", f"{p.stdout.strip()}:{rel}"], cwd=paths.ROOT, capture_output=True, check=True).stdout
    if content != path.read_bytes():
        raise ValueError(f"Uncommitted change to frozen file: {rel}")
    return p.stdout.strip()


class TuningBudget:
    """Every tuning reservation must fit both the $1 phase cap and original $3 cap."""
    def __init__(self):
        self.global_budget = decisions.Budget(GLOBAL_BUDGET)
        self.phase_budget = decisions.Budget(TUNE_BUDGET, maximum=1.0)

    def reserve(self, body):
        phase = self.phase_budget.reserve(body)
        try:
            global_amount = self.global_budget.reserve(body)
        except Exception:
            self.phase_budget._update(-phase)
            raise
        return (global_amount, phase)

    def settle(self, reserved, usage):
        self.global_budget.settle(reserved[0], usage)
        self.phase_budget.settle(reserved[1], usage)


def effective(row, threshold):
    if row.get("error") or row.get("confidence") is None or row["confidence"] < threshold:
        return "in_scope"
    return row["raw_route"]


def dev_metrics(rows, threshold):
    routed = [(r, effective(r, threshold)) for r in rows]
    legitimate = [(r, route) for r, route in routed if r["expected_route"] == "in_scope"]
    off = [(r, route) for r, route in routed if r["expected_route"] != "in_scope"]
    return {"threshold": threshold, "n": len(rows),
            "diversions": sum(route != "in_scope" for _, route in legitimate),
            "exact_matches": sum(route == r["expected_route"] for r, route in routed),
            "non_in_scope_recall": sum(route != "in_scope" for _, route in off),
            "operational_errors": sum(bool(r.get("error")) for r in rows)}


def rank(metrics, iteration=0):
    return (metrics["diversions"], -metrics["exact_matches"], -metrics["non_in_scope_recall"], metrics["threshold"], iteration)


def check_paid():
    if v1.sha(FRESH) != FRESH_SHA256:
        raise ValueError("Fresh labels differ from the registered SHA-256")
    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY required; no calls made")
    return committed(PREREG), committed(FRESH)


def decision_body(case, prompt):
    return v1.body_for("triage", "<user_message>\n" + html.escape(case["question"], quote=False) + "\n</user_message>", prompt)


def decision_call(client, case, prompt, threshold):
    start = time.perf_counter()
    body = decision_body(case, prompt)
    r = client.call(body)
    raw = r.get("choice", "in_scope") if not r["error"] else "in_scope"
    out = {k: v for k, v in case.items() if k != "question"}
    out.update(r, raw_route=raw, skipped=False, confidence=r.get("confidence"))
    out["route"] = effective(out, threshold)
    out["seconds"] = time.perf_counter() - start
    if out["seconds"] > 8:
        out.update(error="deadline", route="in_scope", raw_route="in_scope")
    return out


def chat_call(budget, case, chat=None):
    start = time.perf_counter()
    chat = chat or llm.chat
    system, user, _ = load_prompt("triage_v1")
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user.format(question=html.escape(case["question"], quote=False))}]
    # Reserve both permitted attempts before spending. A failed first attempt's usage is unknown.
    price = prices.table()["chat"][triage.MODEL]
    bound = len(json.dumps(messages, ensure_ascii=False).encode()) + 4096
    per_attempt = (bound * price["input"] + triage.MAX_COMPLETION_TOKENS * price["output"]) / 1e6
    reserved = per_attempt * 2
    out = {k: v for k, v in case.items() if k != "question"}
    out.update(route="in_scope", raw_route="in_scope", confidence=None, error=None, attempts=0, skipped=False,
               usage={"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "complete": True})
    charged = False
    try:
        budget._update(reserved, reserve=True)
        charged = True
        r = chat(triage.MODEL, messages, max_completion_tokens=triage.MAX_COMPLETION_TOKENS,
                 schema=triage.json_schema(), schema_name="triage", timeout_s=max(0.001, 8 - (time.perf_counter() - start)),
                 max_attempts=2, retry_backoff_s=0.5, retry_all_5xx=True)
        out["attempts"] = r.attempts
        cost = prices.chat_cost(triage.MODEL, r.prompt_tokens, r.completion_tokens)
        budget._update(cost - reserved if r.attempts == 1 else cost - per_attempt)
        out["usage"] = {"input_tokens": r.prompt_tokens, "output_tokens": r.completion_tokens,
                        "cost_usd": cost if r.attempts == 1 else None, "complete": r.attempts == 1}
        if r.refusal:
            out["error"] = "refusal"
        else:
            try:
                parsed = triage.Triage.model_validate(json.loads(r.content))
                if parsed.route != "in_scope" and not triage.clean_reply(parsed.reply):
                    raise ValueError()
                out["route"] = out["raw_route"] = parsed.route
            except (ValueError, TypeError):
                out["error"] = "invalid_output"
    except decisions.BudgetExceeded as e:
        out.update(error=str(e), stop=True)
        out["usage"].update(cost_usd=None if charged else 0.0, complete=not charged)
    except llm.LLMError as e:
        out["error"] = "chat_provider_error"
        out["attempts"] = e.attempts
        out["usage"].update(cost_usd=None if charged else 0.0, complete=not charged)
    except Exception:
        out["error"] = "chat_operational_error"
        out["usage"].update(cost_usd=None if charged else 0.0, complete=not charged)
    out["seconds"] = time.perf_counter() - start
    if out["seconds"] > 8:
        out.update(error="deadline", route="in_scope", raw_route="in_scope")
    return out


def execute(out, manifest, schedule, call, prompt=None):
    out.mkdir(parents=True, exist_ok=False)
    if prompt is not None:
        with (out / "prompt.md").open("x") as f:
            f.write(prompt)
    v1.dump(out / "manifest.json", {**manifest, "started_at": utc()})
    completed, reason = [], None
    try:
        with (out / "raw.jsonl").open("x") as f, ThreadPoolExecutor(max_workers=6) as pool:
            for start in range(0, len(schedule), 6):
                batch = schedule[start:start + 6]
                futures = [pool.submit(call, c) for c in batch]
                for future in futures:
                    try:
                        row = future.result()
                    except KeyboardInterrupt:
                        reason = "owner_cancelled"
                        row = future.result()  # retain the already-running attempt before stopping dispatch
                    except Exception:
                        reason = "fatal_operational_error"
                        continue
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
                    f.flush()
                    completed.append(row)
                    if row.get("stop") or row.get("error") == "unknown_cost_stop":
                        reason = row["error"]
                if reason:
                    break
    except KeyboardInterrupt:
        reason = "owner_cancelled"
    status = {"status": "complete" if reason is None and len(completed) == len(schedule) else "incomplete", "reason": reason,
              "scheduled_n": len(schedule), "completed_n": len(completed), "finished_at": utc()}
    identity = lambda c: (c["case_id"], c.get("arm"), c.get("repeat"))
    seen = {identity(c) for c in completed}
    status["missing"] = [{k: c[k] for k in ("case_id", "arm", "repeat") if k in c} for c in schedule if identity(c) not in seen]
    v1.dump(out / "status.json", status)
    return completed, status


def tune(iteration: int, prompt_path: Path, yes=False):
    if iteration not in range(1, 6):
        raise ValueError("At most five tuning iterations: 1 through 5")
    out = paths.EXPERIMENTS / "triage" / f"decisions-triage-tune-{iteration}"
    if out.exists():
        raise FileExistsError("Tuning id already exists, including incomplete attempts")
    if iteration > 1 and not (out.parent / f"decisions-triage-tune-{iteration - 1}/status.json").exists():
        raise ValueError("Run tuning iterations in order; no missing prior attempts")
    if SELECTION.exists():
        raise ValueError("Tuning is closed once the final prompt is selected")
    from labourlens.evaluation.decisions_v2_cases import audit
    fresh_audit = audit(FRESH)
    _, hashes = v1.prepare_triage()
    cases = [{k: c[k] for k in ("case_id", "set", "kind", "question", "expected_route")} for c in v1.rows(v1.BASELINE / "raw.jsonl")]
    prompt = prompt_path.read_text()
    bodies = [decision_body(c, prompt) for c in cases]
    estimated = sum((len(json.dumps(b).encode()) / 3 + 1024) * decisions.INPUT_RATE / 1e6 for b in bodies)
    manifest = {"phase": "dev_tuning", "iteration": iteration, "contaminated_for_scoring": True, "expected_n": 409,
                "prompt_sha256": v1.sha(prompt_path), "inputs_sha256": hashes, "threshold_grid": THRESHOLDS,
                "fresh_cases_sha256": fresh_audit["sha256"],
                "estimated_uncached_usd": estimated, "estimate_method": "bytes/3 plus 1024 tokens, heuristic",
                "global_cap_usd": 3, "incremental_tuning_cap_usd": 1, "workers": 6}
    print(json.dumps(manifest, indent=2))
    if not yes:
        return 0
    manifest["prereg_commit"], manifest["fresh_cases_commit"] = check_paid()
    manifest["fresh_cases_sha256"] = v1.sha(FRESH)
    manifest["prereg_sha256"] = v1.sha(PREREG)
    manifest["git_commit"] = subprocess.run(["git", "rev-parse", "HEAD"], cwd=paths.ROOT, capture_output=True, text=True, check=True).stdout.strip()
    manifest["implementation_sha256"] = {str(p.relative_to(paths.ROOT)): v1.sha(p) for p in
                                        (Path(__file__), paths.ROOT / "src/labourlens/agent/decisions.py",
                                         paths.ROOT / "src/labourlens/answer/llm.py", paths.ROOT / "specs/prices.yaml")}
    client = decisions.Client(TuningBudget())
    completed, status = execute(out, manifest, cases, lambda c: decision_call(client, c, prompt, 0.0), prompt=prompt)
    metrics = [dev_metrics(completed, threshold) for threshold in THRESHOLDS]
    v1.dump(out / "metrics.json", {"thresholds": metrics, "best": min(metrics, key=rank), "usable_for_selection": status["status"] == "complete"})
    return 0 if status["status"] == "complete" else 1


def freeze(out=SELECTION):
    if out.exists():
        raise FileExistsError("Selection already frozen")
    candidates = []
    v1.prepare_triage()
    dev_labels = {r["case_id"]: r["expected_route"] for r in v1.rows(v1.BASELINE / "raw.jsonl")}
    for i in range(1, 6):
        d = paths.EXPERIMENTS / "triage" / f"decisions-triage-tune-{i}"
        if not d.exists():
            continue
        status = json.loads((d / "status.json").read_text())
        if status["status"] != "complete":
            continue
        manifest = json.loads((d / "manifest.json").read_text())
        raw = v1.rows(d / "raw.jsonl")
        if len(raw) != 409 or len({r["case_id"] for r in raw}) != 409:
            raise ValueError("Incomplete dev tuning identities")
        if {r["case_id"]: r["expected_route"] for r in raw} != dev_labels:
            raise ValueError("Dev tuning labels differ from frozen cases")
        if manifest["fresh_cases_sha256"] != v1.sha(FRESH) or manifest["prereg_sha256"] != v1.sha(PREREG):
            raise ValueError("Fresh labels or registration changed after tuning")
        m = min((dev_metrics(raw, threshold) for threshold in THRESHOLDS), key=rank)
        if v1.sha(d / "prompt.md") != manifest["prompt_sha256"]:
            raise ValueError("Frozen tuning prompt changed")
        candidates.append((rank(m, i), d, m))
    if not candidates:
        raise ValueError("No completed dev tuning iteration to freeze")
    _, d, m = min(candidates, key=lambda c: c[0])
    payload = {"selected_tuning_id": d.name, "prompt_path": str((d / "prompt.md").relative_to(paths.ROOT)),
               "prompt_sha256": v1.sha(d / "prompt.md"), "threshold": m["threshold"], "dev_metrics": m,
               "tuning_raw_sha256": v1.sha(d / "raw.jsonl"),
               "cases_sha256": v1.sha(FRESH), "prereg_sha256": v1.sha(PREREG), "selection_rule": "min diversions, max exact matches, max off-topic recall, lower threshold, earlier iteration"}
    v1.dump(out, payload)
    print(json.dumps(payload, indent=2))
    return 0


def score(experiment, yes=False):
    if not re.fullmatch(r"decisions-triage-fresh-[A-Za-z0-9_-]+", experiment):
        raise ValueError("Use a new decisions-triage-fresh-<id> experiment")
    out = paths.EXPERIMENTS / "triage" / experiment
    if out.exists():
        raise FileExistsError("Fresh scoring id already exists")
    if any((paths.EXPERIMENTS / "triage").glob("decisions-triage-fresh-*/manifest.json")):
        raise ValueError("One fresh scoring attempt only; preserve existing outputs and register any extension")
    from labourlens.evaluation.decisions_v2_cases import audit
    case_audit = audit(FRESH)
    selection = json.loads(SELECTION.read_text())
    prompt_path = paths.ROOT / selection["prompt_path"]
    if v1.sha(prompt_path) != selection["prompt_sha256"] or v1.sha(FRESH) != selection["cases_sha256"] or v1.sha(PREREG) != selection["prereg_sha256"]:
        raise ValueError("Selected prompt, cases or prereg changed")
    if v1.sha(prompt_path.parent / "raw.jsonl") != selection["tuning_raw_sha256"]:
        raise ValueError("Selected tuning outputs changed")
    if load_prompt("triage_v1")[2] != "de176c25e4b6":
        raise ValueError("Frozen chat control prompt changed")
    cases = v1.rows(FRESH)
    prompt = prompt_path.read_text()
    schedule = []
    for repeat in range(3):
        for index, case in enumerate(cases):
            # Alternation balances first/second position; each six-request batch includes both arms.
            for arm in (("D", "C") if (index + repeat) % 2 == 0 else ("C", "D")):
                schedule.append({**case, "arm": arm, "repeat": repeat})
    manifest = {"expected_n": len(schedule), "cases_sha256": v1.sha(FRESH), "prompt_sha256": selection["prompt_sha256"],
                "threshold": selection["threshold"], "selected_tuning_id": selection["selected_tuning_id"],
                "prereg_sha256": v1.sha(PREREG), "case_audit": case_audit, "workers": 6, "repeats": 3,
                "model": decisions.MODEL, "control_prompt": "triage_v1", "control_prompt_sha256": v1.sha(paths.ROOT / "prompts/triage_v1.md"),
                "control_user_prompt_sha256": v1.sha(paths.ROOT / "prompts/triage_v1_user.md"),
                "deadline_s": 8, "max_attempts": 2, "backoff_s": 0.5, "global_cap_usd": 3}
    print(json.dumps(manifest, indent=2))
    if not yes:
        return 0
    manifest["prereg_commit"], manifest["cases_commit"] = check_paid()
    manifest["selection_commit"] = committed(SELECTION)
    manifest["prompt_commit"] = committed(prompt_path)
    manifest["git_commit"] = subprocess.run(["git", "rev-parse", "HEAD"], cwd=paths.ROOT, capture_output=True, text=True, check=True).stdout.strip()
    client = decisions.Client(decisions.Budget(GLOBAL_BUDGET))
    def call(c):
        return decision_call(client, c, prompt, selection["threshold"]) if c["arm"] == "D" else chat_call(client.budget, c)
    _, status = execute(out, manifest, schedule, call)
    return 0 if status["status"] == "complete" else 1
