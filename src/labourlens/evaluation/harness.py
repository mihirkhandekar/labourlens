"""Evaluation harness (M6): accuracy, hallucination, citation quality, latency and cost from saved raw agent runs.

Deterministic measures need no model: behaviour, key-number recall, calculation correctness, ungrounded numbers, quote validity,
gold-citation recall, tool errors, latency, cost. Judged measures use an LLM (labelled AI, never human): claim support against the
cited evidence, and coverage or contradiction of the reference facts. Confidence intervals are bootstrap 95% over cases.
The gold labels and the judge are both AI-produced: results show consistency with draft labels, not ground truth until the owner reviews.
"""

from __future__ import annotations

import json
import hashlib
import random
import statistics

from labourlens import paths
from labourlens.agent import experiments as agx
from labourlens.answer import llm
from labourlens.prices import chat_cost
from labourlens.retrieval import evaluate as ev
from labourlens.evaluation.provenance import file_hash, snapshot

JUDGE_MODEL = "gpt-6.1-terra"  # a different model from the generators (gpt-6-luna, gpt-5.6-luna, gpt-4.1-mini)
JUDGE_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["claims", "facts"],
    "properties": {
        "claims": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["index", "verdict", "note"],
                   "properties": {"index": {"type": "integer"}, "verdict": {"type": "string", "enum": ["supported", "partial", "unsupported"]}, "note": {"type": "string"}}}},
        "facts": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["index", "status", "note"],
                  "properties": {"index": {"type": "integer"}, "status": {"type": "string", "enum": ["covered", "missing", "contradicted"]}, "note": {"type": "string"}}}},
    },
}


def judge_input(case: dict, rec: dict) -> str:
    """Exact user payload shared by the judge and its content-addressed cache."""
    a = rec["answer"]
    ev_text = rec.get("evidence_text", {})
    claims = []
    for i, c in enumerate(a["claims"]):
        cited = {x["label"] for x in c["citations"]}
        claims.append(f"[{i}] {c['text']}\n    cites: " + " | ".join(f"{lab}: {ev_text.get(lab, '(missing)')}" for lab in sorted(cited)))
    facts = "\n".join(f"[{i}] {f}" for i, f in enumerate(case["reference_facts"])) or "(none)"
    user = f"QUESTION: {case['question']}\n\nANSWER summary: {a['summary']}\n\nCLAIMS:\n" + "\n".join(claims) + f"\n\nREFERENCE FACTS:\n{facts}"
    return user


def judgement_hash(case: dict, rec: dict) -> str:
    payload = {"question": case["question"], "reference_facts": case["reference_facts"],
               "expected_behavior": case["expected_behavior"], "answer_payload": judge_input(case, rec) if judge_eligible(rec) else rec.get("answer"),
               "model": JUDGE_MODEL, "prompt_sha256": file_hash(paths.ROOT / "prompts" / "judge_v1.md")}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def judge_eligible(rec: dict) -> bool:
    a = rec.get("answer")
    return bool(a and a["status"] == "answered" and a["claims"])


def cached_judgement(case: dict, rec: dict, cache: dict, *, judge: bool, rejudge_stale: bool = True):
    """Legacy/mismatched entries are never reused, including in offline --no-judge mode."""
    key = judgement_hash(case, rec)
    entry = cache.get(case["case_id"])
    if isinstance(entry, dict) and entry.get("input_sha256") == key:
        return entry["judgement"]
    if case["case_id"] in cache and not rejudge_stale:
        raise ValueError(f"Stale judgment for {case['case_id']}: input hash changed or absent; use --rejudge-stale")
    if not judge:
        return None
    result = judge_one(case, rec)
    cache[case["case_id"]] = {"input_sha256": key, "judgement": result}
    return result


def judge_one(case: dict, rec: dict) -> dict | None:
    """Judge claim support even for false answers; reference coverage requires gold facts."""
    if not judge_eligible(rec):
        return None
    system = (paths.ROOT / "prompts" / "judge_v1.md").read_text()
    r = llm.chat(JUDGE_MODEL, [{"role": "system", "content": system}, {"role": "user", "content": judge_input(case, rec)}], schema=JUDGE_SCHEMA, schema_name="judgement")
    out = json.loads(r.content)
    out["cost_usd"] = chat_cost(JUDGE_MODEL, r.prompt_tokens, r.completion_tokens)
    return out


def case_metrics(case: dict, rec: dict, judged: dict | None) -> dict:
    s = agx.score_run(case, rec)
    a = rec["answer"]
    m = {"case_id": case["case_id"], "family": case["family"], "behavior_ok": s["behavior_ok"], "false_answer": s["expected"] != "answered" and s["status"] == "answered",
         "over_abstain": s["expected"] == "answered" and s["status"] in ("abstained", "refused", "clarify"), "valid": s["valid"],
         "operational_failure": s["operational_failure"], "key_number_recall": s.get("key_number_recall"), "calc_correct": s.get("calc_correct"),
         "ungrounded_numbers": s["n_ungrounded_numbers"], "gold_cited": s.get("gold_cited"), "seconds": s["seconds"], "cost_usd": s["cost_usd"],
         "tool_errors": s["tool_errors"], "n_claims": len(a["claims"]) if a else 0}
    if judged:
        cl = judged["claims"]
        m["claims_supported"] = sum(c["verdict"] == "supported" for c in cl)
        m["claims_partial"] = sum(c["verdict"] == "partial" for c in cl)
        m["claims_unsupported"] = sum(c["verdict"] == "unsupported" for c in cl)
        fs = judged["facts"] if case.get("reference_facts") else []
        m["facts_total"] = len(fs)
        m["facts_covered"] = sum(f["status"] == "covered" for f in fs)
        m["facts_contradicted"] = sum(f["status"] == "contradicted" for f in fs)
        m["judge_cost_usd"] = judged["cost_usd"]
        m["judge_notes"] = [c["note"] for c in cl if c["verdict"] != "supported" and c["note"]] + [f["note"] for f in fs if f["status"] == "contradicted" and f["note"]]
    return m


def _rate(rows, key, pred=bool, where=lambda r: True):
    xs = [pred(r[key]) for r in rows if where(r) and r.get(key) is not None]
    return (sum(xs) / len(xs), len(xs)) if xs else (None, 0)


def bootstrap_ci(values: list[float], n: int = 2000, seed: int = 7) -> tuple[float, float]:
    rng = random.Random(seed)
    means = sorted(statistics.fmean(rng.choices(values, k=len(values))) for _ in range(n))
    return means[int(0.025 * n)], means[int(0.975 * n) - 1]


def rate_ci(rows, key, where=lambda r: True, pred=bool) -> dict:
    vals = [float(pred(r[key])) for r in rows if where(r) and r.get(key) is not None]
    if not vals:
        return {"rate": None, "n": 0}
    lo, hi = bootstrap_ci(vals)
    return {"rate": round(statistics.fmean(vals), 3), "ci95": [round(lo, 3), round(hi, 3)], "n": len(vals)}


def pooled_ci(rows: list[dict], num, den, n: int = 2000, seed: int = 7) -> dict:
    """Pooled ratio (e.g. supported claims / all claims) with a bootstrap CI that resamples CASES, since claims in one answer are not independent."""
    rows = [r for r in rows if den(r)]
    if not rows:
        return {"rate": None, "n": 0}
    rng = random.Random(seed)
    point = sum(num(r) for r in rows) / sum(den(r) for r in rows)
    stats = []
    for _ in range(n):
        smp = rng.choices(rows, k=len(rows))
        d = sum(den(r) for r in smp)
        stats.append(sum(num(r) for r in smp) / d if d else point)
    stats.sort()
    return {"rate": round(point, 3), "ci95": [round(stats[int(0.025 * n)], 3), round(stats[int(0.975 * n) - 1], 3)], "n": sum(den(r) for r in rows), "n_cases": len(rows)}


def aggregate(rows: list[dict]) -> dict:
    answered = [r for r in rows if "claims_supported" in r]
    tot_claims = sum(r["claims_supported"] + r["claims_partial"] + r["claims_unsupported"] for r in answered)
    facts = sum(r["facts_total"] for r in answered)
    return {
        "n_cases": len(rows),
        "behaviour_accuracy": rate_ci(rows, "behavior_ok"),
        "false_answer_rate": rate_ci(rows, "false_answer", where=lambda r: not r["over_abstain"] and r["family"] is not None),
        "over_abstention_rate": rate_ci(rows, "over_abstain"),
        "key_number_recall": rate_ci(rows, "key_number_recall", pred=float),
        "calc_correct": rate_ci(rows, "calc_correct"),
        "gold_cited_any": rate_ci(rows, "gold_cited"),
        # Denominator is every scored case, including abstentions and operational failures.
        "cases_with_ungrounded_numbers": rate_ci(rows, "ungrounded_numbers"),
        "answers_with_ungrounded_numbers": rate_ci(rows, "ungrounded_numbers"),  # legacy alias for report consumers
        "claims_judged": tot_claims,
        "claim_supported_rate": pooled_ci(answered, lambda r: r["claims_supported"], lambda r: r["claims_supported"] + r["claims_partial"] + r["claims_unsupported"]),
        "claim_unsupported_rate": pooled_ci(answered, lambda r: r["claims_unsupported"], lambda r: r["claims_supported"] + r["claims_partial"] + r["claims_unsupported"]),
        "answers_with_any_unsupported_claim": rate_ci(answered, "claims_unsupported"),
        "fact_coverage": pooled_ci(answered, lambda r: r["facts_covered"], lambda r: r["facts_total"]),
        "answers_contradicting_a_reference_fact": rate_ci(answered, "facts_contradicted", where=lambda r: r["facts_total"] > 0),
        "latency_p50_s": round(statistics.median(r["seconds"] for r in rows), 1),
        "latency_p95_s": round(sorted(r["seconds"] for r in rows)[max(0, int(len(rows) * 0.95) - 1)], 1),
        "cost_per_case_usd": round(statistics.fmean(r["cost_usd"] for r in rows), 5),
        "judge_cost_total_usd": round(sum(r.get("judge_cost_usd", 0) for r in rows), 4),
    }


def by_family(rows: list[dict]) -> dict:
    out = {}
    for fam in sorted({r["family"] for r in rows}):
        sub = [r for r in rows if r["family"] == fam]
        out[fam] = {"n": len(sub), "behaviour_accuracy": rate_ci(sub, "behavior_ok")["rate"], "false_answer": sum(r["false_answer"] for r in sub),
                    "over_abstain": sum(r["over_abstain"] for r in sub),
                    "unsupported_claims": sum(r.get("claims_unsupported", 0) for r in sub), "contradicted_facts": sum(r.get("facts_contradicted", 0) for r in sub)}
    return out


def run(exp: str = "agent-dev-A1", split: str = "dev", labels: list[str] | None = None, judge: bool = True,
        rejudge_stale: bool = True) -> None:
    cases = {c["case_id"]: c for c in ev.load_cases(split)}
    raw_dir = paths.DATA / "runs" / exp
    pub = paths.EXPERIMENTS / "eval" / exp
    pub.mkdir(parents=True, exist_ok=True)
    reviewed = sum(c.get("review_status") == "owner_reviewed" for c in cases.values())
    report = [f"# Evaluation of `{exp}` ({split}, n={len(cases)})", "",
              f"Gold was AI-drafted; {reviewed}/{len(cases)} cases record per-card owner review, which may agree with AI suggestions and is not independent inter-rater evidence. "
              "The judge is AI-produced. Judge model: `" + JUDGE_MODEL + "` (different from the generators). "
              "Intervals are bootstrap 95% over cases; with this n, treat differences under about 10 points as noise.", ""]
    for f in sorted(raw_dir.glob("*.jsonl")):
        label = f.stem
        if labels and label not in labels:
            continue
        recs = [json.loads(line) for line in f.read_text().splitlines() if line.strip()]
        rows = []
        cache = pub / f"{label}.judgements.json"
        judgements = json.loads(cache.read_text()) if cache.exists() else {}
        for rec in recs:
            case = cases.get(rec["case_id"])
            if case is None or rec.get("question") != case["question"]:
                continue  # dropped from the gold set, or the question text changed after this run (the run answered a different question)
            judged = cached_judgement(case, rec, judgements, judge=judge, rejudge_stale=rejudge_stale)
            rows.append(case_metrics(case, rec, judged))
        cache.write_text(json.dumps(judgements, indent=1))
        agg = aggregate(rows)
        configs = {r.get("config", "") for r in recs}
        if len(configs) != 1:
            raise ValueError(f"Mixed AgentConfig keys in {f}")
        provenance = snapshot(next(iter(configs)), len(rows), len(cases))
        (pub / f"{label}.metrics.json").write_text(json.dumps({"label": label, "judge": JUDGE_MODEL, "provenance": provenance,
            "metric_definitions": {"cases_with_ungrounded_numbers": "fraction of all scored cases with an ungrounded numeric warning",
                                   "answers_with_ungrounded_numbers": "legacy alias of cases_with_ungrounded_numbers; denominator is all scored cases"},
            "metrics": agg, "by_family": by_family(rows)}, indent=1))
        (pub / f"{label}.cases.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        fmt = lambda d: "n/a" if d["rate"] is None else f"{d['rate']} [{d['ci95'][0]}, {d['ci95'][1]}] (n={d['n']})"  # noqa: E731
        report += [f"## {label}", "", "| measure | value |", "|---|---|"]
        report += [f"| {k} | {fmt(v) if isinstance(v, dict) else v} |" for k, v in agg.items()]
        report += ["", "| family | n | behaviour acc | false answers | over-abstentions | unsupported claims | contradicted facts |", "|---|---|---|---|---|---|---|"]
        report += [f"| {k} | {v['n']} | {v['behaviour_accuracy']} | {v['false_answer']} | {v['over_abstain']} | {v['unsupported_claims']} | {v['contradicted_facts']} |" for k, v in by_family(rows).items()]
        report += [""]
    (paths.EXPERIMENTS / "eval" / f"{exp}-REPORT.md").write_text("\n".join(report) + "\n")
    print("\n".join(report))
