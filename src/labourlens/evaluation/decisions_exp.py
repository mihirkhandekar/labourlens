"""Preregistered Decisions experiments; dry-run by default, no production imports/callsite changes."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import html
import json
import os
from pathlib import Path
import re
from datetime import datetime, timezone
import subprocess

from labourlens import paths
from labourlens.agent import decisions, smalltalk, triage
from labourlens.evaluation import harness, triage_check
from labourlens.retrieval.evaluate import load_cases

REFERENCE = paths.EXPERIMENTS / "xjudge/sonnet55-FIN-s60-b-20261102"
BASELINE = paths.EXPERIMENTS / "triage/triage-v1-luna"
REGISTRATION = "docs/experiments/decisions-api-prereg.md"
EXPECTED = {
    "gold": "af3ad02690ed1dabb69e2be7f7bb984f707f1352b95c8bd693d0fb51e9410d8f",
    "v2": "e3d16597d542d33d106b4e9291aa3b92ca5fcdf19aa4d3c2b3319c0543efa542",
    "threats": "17fd3bf5a195f19b40110493f838a929104f41d7009c853332a2b83c8a82b77b",
    "offtopic": "e6170b69260e6c73a1b5a2a0c2f2ee2d1c4d76abdea3b0d1a6003e06d9fee69f",
}
REFERENCE_HASHES = {
    "labels.json": "6005b6af236c3fb1fcc0c9dcb2a2f6fb69ffbac980ffe10bf5b42e1e4a693fc2",
    "sample.json": "6b4200eabe6982ab4c04d7f8b1c38af8401d8a7c751e1be24f9d67cb0131154d",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    return [json.loads(s) for s in path.read_text().splitlines() if s.strip()]


def dump(path, data):
    with path.open("x") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def body_for(task, text, prompt):
    question = {"name": "route" if task == "triage" else "support", "type": "choice" if task == "triage" else "predicate", "instructions": prompt}
    if task == "triage":
        question["choices"] = [{"value": r, "description": next(line.split(": ", 1)[1] for line in prompt.splitlines() if line.startswith(r + ": "))} for r in triage.ROUTES]
        question["instructions"] = prompt.split("\nin_scope:", 1)[0].strip()
    return {"model": decisions.MODEL, "input": text, "questions": [question]}


def prepare_triage():
    hashes = {}
    for name, path in triage_check.SETS:
        if sha(path) != EXPECTED[name]:
            raise ValueError(f"Frozen triage input mismatch: {name}")
        hashes[str(path.relative_to(paths.ROOT))] = sha(path)
    for name, expected in (("raw.jsonl", "1029171d0b494ef659b378827bf597c41e58c594ec31ab9bd7721419360c6e7a"),
                           ("metrics.json", "a544504444a2a00327e7ad7c5a85299787e2bc248477f56e9a4cb4e1827d90eb")):
        p = BASELINE / name
        if sha(p) != expected:
            raise ValueError("Frozen triage baseline mismatch")
        hashes[str(p.relative_to(paths.ROOT))] = sha(p)
    baseline = rows(BASELINE / "raw.jsonl")
    cases = triage_check.load_cases()
    fields = ("case_id", "set", "kind", "question", "expected_route")
    if [{k: c[k] for k in fields} for c in cases] != [{k: c[k] for k in fields} for c in baseline] or len(cases) != 409:
        raise ValueError("Triage identities differ from historical baseline")
    return [{**{k: c[k] for k in fields if k != "question"}, "repeat": repeat,
             "_input": "<user_message>\n" + html.escape(c["question"], quote=False) + "\n</user_message>",
             "skipped": not c["question"].strip() or len(c["question"]) > 1000} for repeat in range(3) for c in cases], hashes


def prepare_support():
    hashes = {}
    for name, expected in REFERENCE_HASHES.items():
        p = REFERENCE / name
        if sha(p) != expected:
            raise ValueError("Frozen support reference mismatch")
        hashes[str(p.relative_to(paths.ROOT))] = sha(p)
    sample = json.loads((REFERENCE / "sample.json").read_text())
    labels = json.loads((REFERENCE / "labels.json").read_text())
    key = lambda x: tuple(x[k] for k in ("model", "set", "arm", "case_id"))
    look = {key(x): x for x in sample}
    if len(look) != len(sample):
        raise ValueError("Duplicate support identities")
    runs, judges, golds = {}, {}, {}
    out = []
    for item in labels:
        if item["status"] != "valid":
            continue
        s = look[key(item)]
        model, run = item["model"], s["source_run"]
        raw = paths.DATA / "runs" / run / f"{model}.jsonl"
        judge = paths.EXPERIMENTS / "eval" / run / f"{model}.judgements.json"
        gold = paths.EXPERIMENTS / "gold" / ("heldout_v2_v1.jsonl" if item["set"] == "fresh" else "gold_v3.7.jsonl")
        for p in (raw, judge, gold):
            hashes[str(p.relative_to(paths.ROOT))] = sha(p)
        if raw not in runs:
            rr = rows(raw)
            runs[raw] = {r["case_id"]: r for r in rr}
            if len(rr) != len(runs[raw]):
                raise ValueError("Duplicate saved answers")
            judges[judge] = json.loads(judge.read_text())
        if gold not in golds:
            golds[gold] = {c["case_id"]: c for split in ("dev", "heldout") for c in load_cases(split, gold)}
        rec = runs[raw][item["case_id"]]
        case = golds[gold][item["case_id"]]
        saved = judges[judge][item["case_id"]]
        if sha(gold) != s["gold_sha256"] or saved["input_sha256"] != s["original_input_sha256"] or harness.judgement_hash(case, rec) != saved["input_sha256"]:
            raise ValueError("Stale support judgement fingerprint")
        claims = rec["answer"]["claims"]
        if len(claims) != len(item["second"]["claims"]) or len(claims) != len(item["original"]["claims"]):
            raise ValueError("Claim index mismatch")
        second_cost = sum(a["list_price_usd"] for a in item["attempts"])
        for index, c in enumerate(claims):
            cited = sorted({ct["label"] for ct in c["citations"]})
            if not cited or any(label not in rec["evidence_text"] for label in cited):
                raise ValueError("Missing cited evidence")
            text = json.dumps({"claim": c["text"], "evidence": {label: rec["evidence_text"][label] for label in cited}}, ensure_ascii=False)
            out.append({**{k: item[k] for k in ("case_id", "model", "set", "arm", "family")}, "claim_index": index,
                        "label": item["second"]["claims"][index], "original_label": item["original"]["claims"][index],
                        "cited_ids": cited, "answer_claim_count": len(claims), "original_answer_cost_usd": saved["judgement"].get("cost_usd"),
                        "second_answer_cost_usd": second_cost, "second_attempts": [{k: a[k] for k in ("attempt", "cached", "status")} for a in item["attempts"]],
                        "input_sha256": hashlib.sha256(text.encode()).hexdigest(), "_input": text, "skipped": False})
    if len(out) != 441:
        raise ValueError("Expected 441 frozen cited claims")
    return out, hashes


def fallback(route):
    if route == "in_scope":
        return ""
    if route == "small_talk":
        return smalltalk.answer_for("greeting")["summary"]
    if route == "unsafe_or_sensitive":
        return "I cannot help with this request. If you are at risk of harm, contact local emergency services or someone you trust."
    return "I only answer questions about Singapore labour-market statistics and MOM report passages for Q1 2024 to Q2 2026. I cannot help with this topic."


def classify(client, body, case):
    public = {k: v for k, v in case.items() if not k.startswith("_")}
    if case["skipped"]:
        info = {"error": "skipped_question_length", "seconds": 0.0, "attempts": 0,
                "usage": {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}}
    else:
        info = client.call(body)
    if body["questions"][0]["type"] == "choice":
        route = info.get("choice", "in_scope") if not info["error"] else "in_scope"
        route70 = route if info.get("confidence", 0) >= 0.7 else "in_scope"
        # Only route/numeric metadata is persisted; fixed reply is available to the adapter, not generated.
        triage.answer_for(route, fallback(route))
        info.update(route=route, route70=route70, confidence=info.get("confidence"), probabilities=info.get("probabilities"))
    else:
        info["probability"] = info.get("probability")
    return {**public, **info}


def registration_commit():
    r = subprocess.run(["git", "log", "-1", "--format=%H", "--", REGISTRATION], cwd=paths.ROOT, capture_output=True, text=True, check=True)
    if not r.stdout.strip():
        raise ValueError("Commit the registration before paid execution")
    committed = subprocess.run(["git", "show", f"{r.stdout.strip()}:{REGISTRATION}"], cwd=paths.ROOT, capture_output=True, check=True).stdout
    if committed != (paths.ROOT / REGISTRATION).read_bytes():
        raise ValueError("Working registration differs from committed protocol")
    return r.stdout.strip()


def run(task, experiment, confirm=False, budget_path=None, client=None):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", experiment):
        raise ValueError("Use a new simple experiment id")
    out = paths.EXPERIMENTS / ("triage" if task == "triage" else "eval") / experiment
    if out.exists():
        raise FileExistsError("Experiment directory already exists; choose a new id")
    cases, hashes = prepare_triage() if task == "triage" else prepare_support()
    prompt_path = paths.ROOT / "prompts" / ("triage_decisions_v1.md" if task == "triage" else "support_decisions_v1.md")
    prompt = prompt_path.read_text()
    bodies = [body_for(task, c["_input"], prompt) for c in cases]
    bound = sum((len(json.dumps(b, ensure_ascii=False).encode()) + 4096) * decisions.WRITE_RATE / 1e6 for c, b in zip(cases, bodies) if not c["skipped"])
    estimated_tokens = sum((len(json.dumps(b, ensure_ascii=False).encode()) + 2) // 3 + 1024
                           for c, b in zip(cases, bodies) if not c["skipped"])
    budget_path = budget_path or paths.DATA / "runs/decisions-api-budget.json"
    manifest = {"task": task, "expected_n": len(cases), "inputs_sha256": hashes, "prompt_sha256": sha(prompt_path),
                "registration_sha256": sha(paths.ROOT / REGISTRATION), "config": {"model": decisions.MODEL, "endpoint": decisions.API,
                "timeout_s": 8, "retries": 1, "backoff_s": 0.5, "workers": 6, "max_usd": 3, "budget_path": str(budget_path),
                "one_attempt_conservative_usd": bound, "two_attempt_conservative_usd": 2 * bound,
                "estimated_uncached_usd": estimated_tokens * decisions.INPUT_RATE / 1e6,
                "estimate_method": "UTF-8 bytes/3 plus 1024 protocol tokens per request; heuristic, not measured usage",
                "price_source": "https://developers.openai.com/api/docs/guides/decisions#pricing-and-availability",
                "second_judge_cost": "attempt list prices, cached attempts included; row metadata preserves cache/retry status"}}
    print(json.dumps(manifest, indent=2))
    if not confirm:
        print("Dry run: no model calls or files written. Use --yes to spend.")
        return 0
    if client is None and not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is required for --yes; no calls made")
    manifest["registration_commit"] = registration_commit()
    manifest["git_commit"] = subprocess.run(["git", "rev-parse", "HEAD"], cwd=paths.ROOT, capture_output=True, text=True, check=True).stdout.strip()
    manifest["started_at"] = datetime.now(timezone.utc).isoformat()
    out.mkdir(parents=True, exist_ok=False)
    dump(out / "manifest.json", manifest)
    client = client or decisions.Client(decisions.Budget(budget_path))
    completed = 0
    seen = set()
    reason = None
    try:
        # Bounded batches prevent dispatching the whole schedule after a budget failure.
        with (out / "raw.jsonl").open("x") as f:
            with ThreadPoolExecutor(max_workers=6) as pool:
                for start in range(0, len(cases), 6):
                    batch = list(zip(cases[start:start + 6], bodies[start:start + 6]))
                    futures = [pool.submit(classify, client, b, c) for c, b in batch]
                    fatal = None
                    for future in futures:
                        try:
                            r = future.result()
                            f.write(json.dumps(r, ensure_ascii=False) + "\n")
                            f.flush()
                            completed += 1
                            seen.add(tuple(r.get(k) for k in ("case_id", "set", "model", "arm", "claim_index", "repeat")))
                            if r.get("stop") or r["error"] == "unknown_cost_stop":
                                fatal = decisions.DecisionError(r["error"])
                        except Exception as e:
                            fatal = e
                    if fatal:
                        raise fatal
    except KeyboardInterrupt:
        reason = "owner_cancelled"
    except Exception as e:
        reason = str(e) if isinstance(e, decisions.DecisionError) else type(e).__name__
    identity_fields = ("case_id", "set", "model", "arm", "claim_index", "repeat")
    missing = [{k: c[k] for k in identity_fields if k in c} for c in cases
               if tuple(c.get(k) for k in identity_fields) not in seen]
    status = {"status": "complete" if reason is None and completed == len(cases) else "incomplete", "reason": reason,
              "scheduled_n": len(cases), "completed_n": completed, "missing": missing,
              "finished_at": datetime.now(timezone.utc).isoformat()}
    dump(out / "status.json", status)
    print(json.dumps(status))
    return 0 if status["status"] == "complete" else 1
