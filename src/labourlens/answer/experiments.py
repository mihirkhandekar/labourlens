"""Answer-generation experiments (D-016, D-022, D-024). One factor at a time, dev split only until the freeze.

G1 model (same prompt, same retrieval, k=5)
G2 prompt variant on the best G1 model     (added after G1 is read)
G3 evidence size k on the best G1 model    (added after G1 is read)
Retrieval is fixed for these runs: hybrid RRF, merge200 chunks, text-embedding-3-large (chosen on dev in M3 step 1; not frozen).
Raw outputs (they contain MOM quotes) go to data/runs/ (gitignored). Committed files hold metrics and per-case scores only.
"""

from __future__ import annotations

import json
import statistics
from concurrent.futures import ThreadPoolExecutor

from labourlens import paths, prices
from labourlens.answer import pipeline as pl
from labourlens.answer import validate as vd
from labourlens.retrieval import chunk as ck
from labourlens.retrieval import dense as dn
from labourlens.retrieval import evaluate as ev
from labourlens.retrieval.bm25_index import BM25Config, BM25Index

EXPECTED_STATUS = {"answer": "answered", "ignore_injection_and_answer": "answered", "abstain": "abstained", "clarify": "clarify", "refuse": "refused"}
MODELS = ("gpt-6-luna", "gpt-6-sol", "gpt-6.1-terra", "gpt-5.6-luna", "gpt-5.4-mini", "gpt-4.1-mini")
WORKERS = 4


def in_scope(case: dict) -> bool:
    """M3 scope (D-024): everything except answer cases whose evidence is statistical only (they need the M4 tool)."""
    return not (EXPECTED_STATUS[case["expected_behavior"]] == "answered" and not case["evidence_text"])


def retriever_and_corpus():
    passages = ck.load_passages()
    chunks = ck.build_chunks(ck.CONFIGS["merge200"], passages)
    hybrid = dn.HybridIndex(BM25Index.build(chunks, BM25Config()), dn.DenseIndex(chunks, dn.DenseConfig("text-embedding-3-large")))
    return hybrid, {c.chunk_id: c for c in chunks}, {p["passage_id"]: p for p in passages}


def score(case: dict, rec: dict) -> dict:
    expected = EXPECTED_STATUS[case["expected_behavior"]]
    a = rec["answer"]
    gold = ev.gold_passages(case) if case["evidence_text"] else set()
    s = {"case_id": case["case_id"], "family": case["family"], "expected": expected, "status": a["status"] if a else None,
         "valid": rec["valid"], "operational_failure": rec["operational_failure"], "attempts": rec["attempts"],
         "behavior_ok": bool(a) and a["status"] == expected, "errors": rec["errors"], "n_ungrounded_numbers": len(rec["ungrounded_numbers"]),
         "seconds": rec["seconds"], "prompt_tokens": rec["prompt_tokens"], "completion_tokens": rec["completion_tokens"]}
    if gold:
        s["gold_in_context"] = bool(gold & set(rec["context_passage_ids"]))
        s["gold_cited"] = bool(gold & set(rec["cited_passage_ids"]))
    if expected == "answered" and a:
        text = " ".join([a["summary"]] + [c["text"] for c in a["claims"]])
        want = vd.key_numbers(" ".join(case["reference_facts"]))
        have = vd.numbers(text)
        s["key_number_recall"] = round(len(want & have) / len(want), 3) if want else None
    return s


def aggregate(scores: list[dict], model: str) -> dict:
    n = len(scores)
    def rate(xs):
        xs = list(xs)
        return round(sum(xs) / len(xs), 3) if xs else None
    ans = [s for s in scores if s["expected"] == "answered"]
    non = [s for s in scores if s["expected"] != "answered"]
    krs = [s["key_number_recall"] for s in ans if s.get("key_number_recall") is not None]
    secs = sorted(s["seconds"] for s in scores)
    return {
        "n": n, "n_answer_cases": len(ans), "n_nonanswer_cases": len(non),
        "valid_rate": rate(s["valid"] for s in scores), "repair_rate": rate(s["attempts"] > 1 for s in scores),
        "operational_failures": sum(s["operational_failure"] for s in scores),
        "behavior_accuracy": rate(s["behavior_ok"] for s in scores),
        "answer_case_behavior": rate(s["behavior_ok"] for s in ans), "nonanswer_case_behavior": rate(s["behavior_ok"] for s in non),
        "over_abstention_rate": rate(s["status"] != "answered" for s in ans),
        "false_answer_rate": rate(s["status"] == "answered" for s in non),
        "numbers_complete_rate": rate(s["status"] == "answered" and (s.get("key_number_recall") in (None, 1.0)) for s in ans),
        "gold_in_context_rate": rate(s["gold_in_context"] for s in scores if "gold_in_context" in s),
        "gold_cited_rate": rate(s["gold_cited"] for s in ans if "gold_cited" in s),
        "gold_cited_given_in_context": rate(s["gold_cited"] for s in ans if s.get("gold_in_context")),
        "key_number_recall": round(statistics.mean(krs), 3) if krs else None,
        "answers_with_ungrounded_numbers": rate(s["n_ungrounded_numbers"] > 0 for s in ans),
        "latency_p50_s": secs[len(secs) // 2], "latency_max_s": secs[-1],
        "prompt_tokens_mean": round(statistics.mean(s["prompt_tokens"] for s in scores)), "completion_tokens_mean": round(statistics.mean(s["completion_tokens"] for s in scores)),
        "total_tokens": sum(s["prompt_tokens"] + s["completion_tokens"] for s in scores),
        "cost_per_case_usd": round(sum(prices.chat_cost(model, s["prompt_tokens"], s["completion_tokens"]) for s in scores) / n, 5),
    }


def run_config(label: str, cfg: pl.AnswerConfig, cases: list[dict], world, exp: str) -> dict:
    retr, chunks_by_id, passages_by_id = world
    def one(case):
        gold = sorted(ev.gold_passages(case)) if case["evidence_text"] else None
        return case, pl.answer_question(case["question"], retr, chunks_by_id, passages_by_id, cfg, gold)
    with ThreadPoolExecutor(WORKERS) as ex:
        pairs = list(ex.map(one, cases))
    raw = paths.DATA / "runs" / exp
    raw.mkdir(parents=True, exist_ok=True)
    (raw / f"{label}.jsonl").write_text("\n".join(json.dumps({"case_id": c["case_id"], **r}) for c, r in pairs) + "\n")
    scores = [score(c, r) for c, r in pairs]
    pub = paths.EXPERIMENTS / "runs" / exp
    pub.mkdir(parents=True, exist_ok=True)
    (pub / f"{label}.scores.jsonl").write_text("\n".join(json.dumps(s) for s in scores) + "\n")
    m = aggregate(scores, cfg.model)
    (pub / f"{label}.metrics.json").write_text(json.dumps({"label": label, "config": cfg.key(), "prompt_hash": pl.load_prompt(cfg.prompt)[2], "metrics": m}, indent=1))
    return m


COLS = ["valid_rate", "repair_rate", "behavior_accuracy", "over_abstention_rate", "false_answer_rate", "numbers_complete_rate", "gold_in_context_rate",
        "gold_cited_rate", "key_number_recall", "answers_with_ungrounded_numbers", "latency_p50_s", "total_tokens", "cost_per_case_usd"]


def table(rows: dict[str, dict]) -> list[str]:
    out = ["| config | " + " | ".join(COLS) + " |", "|---|" + "---|" * len(COLS)]
    for label, m in rows.items():
        out.append(f"| {label} | " + " | ".join(str(m[c]) for c in COLS) + " |")
    return out


def _per_model(make):
    return lambda models: {m: make(m) for m in models}


EXPERIMENTS = {
    "G1": ("model comparison, retrieved evidence", _per_model(lambda m: pl.AnswerConfig(m)), MODELS),
    "G0": ("model comparison, ORACLE evidence (gold passages placed first, then retrieved); isolates generation from retrieval",
           _per_model(lambda m: pl.AnswerConfig(m, oracle=True)), MODELS),
    "G3": ("evidence size k (chunks shown to the model), two fast models",
           lambda models: {f"{m} k={k}": pl.AnswerConfig(m, k=k) for m in models for k in (3, 5, 8)}, ("gpt-4.1-mini", "gpt-5.4-mini")),
    "G4": ("k=8 for the two cheapest cautious models (the owner's prefer-declining policy, D-026)",
           lambda models: {f"{m} k=8": pl.AnswerConfig(m, k=8) for m in models}, ("gpt-5.6-luna", "gpt-6-luna")),
}


def run(split: str = "dev", only: list[str] | None = None, exp_name: str = "G1") -> None:
    desc, make, default_models = EXPERIMENTS[exp_name]
    cases = [c for c in ev.load_cases(split) if in_scope(c)]
    world = retriever_and_corpus()
    exp = f"answer-{split}-{exp_name}"
    rows = {}
    for label, cfg in make(only or default_models).items():
        print(f"[answer] {exp_name} {label} on {len(cases)} cases", flush=True)
        rows[label] = run_config(label, cfg, cases, world, exp)
    text = "\n".join([f"# Answer generation, split `{split}`, {exp_name}: {desc} (n={len(cases)} cases)", "",
                      "Draft gold labels. Prompt `answer_v1`; retrieval fixed; k=5 unless the label says otherwise. Rates are over cases.", ""] + table(rows)) + "\n"
    (paths.EXPERIMENTS / "runs" / f"{exp}-SUMMARY.md").write_text(text)
    print(text)


def resummarize(exp: str, title: str) -> None:
    """Rebuild a summary table from saved per-case scores (no API calls)."""
    rows = {}
    for f in sorted((paths.EXPERIMENTS / "runs" / exp).glob("*.scores.jsonl")):
        rows[f.name.removesuffix(".scores.jsonl")] = aggregate([json.loads(x) for x in f.read_text().splitlines()], f.name.split(".scores")[0].split()[0])
    text = "\n".join([title, ""] + table(rows)) + "\n"
    (paths.EXPERIMENTS / "runs" / f"{exp}-SUMMARY.md").write_text(text)
    print(text)
