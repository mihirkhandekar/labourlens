"""Pre-registered held-out retrieval diagnostics; audit and cache-only execution by default."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path

import numpy as np

from labourlens import paths, prices
from labourlens.answer import context as cx
from labourlens.retrieval import dense as dn
from labourlens.retrieval import evaluate as ev
from labourlens.retrieval import experiments_rerank as exp
from labourlens.retrieval import period as pr
from labourlens.retrieval import rerank as rr
from labourlens.retrieval import runtime as rt

METHODS = ("bm25", "dense", "hybrid", "R1a", "R1b", "R1b_x0.5", "R1b_x2", "R2", "R3")
SETS = {"registered31": ("gold_v3.7.jsonl", "heldout", 31),
        "fresh65": ("heldout_v2_v1.jsonl", "heldout", 65)}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_sets() -> tuple[dict, dict]:
    selected, metadata = {}, {}
    for name, (filename, split, expected_n) in SETS.items():
        path = ev.GOLD / filename
        all_cases = ev.load_cases(split, path)
        if len(all_cases) != expected_n or len({c["case_id"] for c in all_cases}) != expected_n:
            raise ValueError(f"{name}: expected {expected_n} unique cases")
        cases = [c for c in ev.text_cases(all_cases) if ev.gold_passages(c)]
        if not cases:
            raise ValueError(f"{name}: no eligible text cases")
        selected[name] = cases
        ids = {c["case_id"] for c in cases}
        metadata[name] = {"gold_path": str(path.relative_to(paths.ROOT)), "gold_sha256": digest(path),
                          "total_n": len(all_cases), "text_n": len(cases),
                          "excluded_ids": [c["case_id"] for c in all_cases if c["case_id"] not in ids]}
    return selected, metadata


def score(case: dict, ranked: list[str], world) -> dict:
    row = exp.score_row(case, ranked, world.chunks, ranked)
    context = cx.build_context([world.chunks[c] for c in ranked[:8]], world.passages_by_id)
    row["strict_passage_hit@8"] = bool(ev.gold_passages(case) & {p.passage_id for p in context[:8]})
    row["context_first8_ids"] = [p.passage_id for p in context[:8]]
    return row


def values(rows: list[dict]) -> dict[str, np.ndarray]:
    ranks = [r["first_relevant_rank"] for r in rows]
    return {"chunk_hit@8": np.array([float(r is not None and r <= 8) for r in ranks]),
            "strict_passage_hit@8": np.array([float(r["strict_passage_hit@8"]) for r in rows]),
            "mrr@10": np.array([1 / r if r is not None and r <= 10 else 0.0 for r in ranks])}


def aggregate(rows: list[dict]) -> dict:
    if not rows:
        raise ValueError("cannot score an empty case set")
    out = {"n": len(rows)}
    for key, v in values(rows).items():
        out[key] = {"mean": round(float(v.mean()), 6),
                    "ci95": [round(x, 6) for x in exp.bootstrap(v, np.random.default_rng(0))]}
    return out


def paired(rows: list[dict], base: list[dict]) -> dict:
    if [r["case_id"] for r in rows] != [r["case_id"] for r in base]:
        raise ValueError("paired cases must have identical IDs and order")
    a, b = values(rows), values(base)
    return {key: {"mean_difference": round(float((a[key] - b[key]).mean()), 6),
                  "ci95": [round(x, 6) for x in exp.bootstrap(a[key] - b[key], np.random.default_rng(0))],
                  "better": int((a[key] > b[key]).sum()), "worse": int((a[key] < b[key]).sum())} for key in a}


def pools(world, question: str) -> dict[str, list[str]]:
    bm, de = world.full_rankings(question)
    hints = pr.parse(question)
    hard = exp.fuse(bm, de, pr.matching_sources(hints), world.chunks)
    out = {"bm25": bm[0], "dense": de[:exp.DEPTH], "hybrid": exp.fuse(bm, de, None, world.chunks), "R1a": hard}
    per, stage = exp.hint_sets(hints)
    for name, mult in (("R1b", 1.0), ("R1b_x0.5", 0.5), ("R1b_x2", 2.0)):
        out[name] = exp.fuse(bm, de, None, world.chunks, (exp.BONUS * mult, per, stage) if (per or stage) else None)
    return {k: [cid for cid, _ in v] for k, v in out.items()}


def rerank_key(question: str, candidates: list) -> str:
    return hashlib.sha256(json.dumps([rr.MODEL, rr.load_prompt()[2], question,
                                      [c.chunk_id for c in candidates]]).encode()).hexdigest()[:24]


def cached_rerank(question: str, candidates: list, directories: list[Path]):
    key = rerank_key(question, candidates)
    for directory in directories:
        f = directory / f"{key}.json"
        if f.exists():
            result = rr.RerankResult(**{**json.loads(f.read_text())["result"], "cached": True})
            if sorted(result.order) != list(range(len(candidates))):
                raise ValueError(f"invalid cached rerank permutation: {f}")
            return result
    return None


def estimated_tokens(text: str) -> int:
    return math.ceil(len(text.encode()) / 4)


def execute(run_id: str, run: bool = False, allow_paid: bool = False) -> dict:
    if allow_paid and not run:
        raise ValueError("--allow-paid requires --run")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", run_id):
        raise ValueError("invalid experiment ID")
    output = paths.EXPERIMENTS / "eval" / run_id
    if output.exists():
        raise ValueError(f"experiment ID already exists: {output}")
    cases, metadata = load_sets()
    world = exp.World(exp.RunPaths("V31"), offline=True)
    prov = exp.provenance(list(world.chunks.values()), "per-set")
    if prov["corpus_version"] != "v3.1":
        raise ValueError("live corpus does not match frozen v3.1")
    # Private namespace never modifies the dev experiment's vectors or responses.
    private = paths.ROOT / "data" / "runs" / run_id / prov["corpus_hash"]
    local_qv = private / "query_vectors.json"
    frozen = json.loads(world.qv_file.read_text()) if world.qv_file.exists() else {}
    local = json.loads(local_qv.read_text()) if local_qv.exists() else {}
    shared = dn.VectorCache(rt.EMBEDDING_MODEL)
    vectors = {}
    missing = []
    for set_name, group in cases.items():
        for c in group:
            q = c["question"]
            key = hashlib.sha256(q.encode()).hexdigest()
            v = frozen.get(key, local.get(key))
            if v is None:
                v = shared.get(dn._h(rt.EMBEDDING_MODEL, q))
            if v is None:
                missing.append({"set": set_name, "case_id": c["case_id"], "question": q,
                                "question_sha256": key, "estimated_tokens": estimated_tokens(q)})
            else:
                vectors[key] = np.asarray(v, dtype=np.float32)
    unique_missing = {r["question_sha256"]: r for r in missing}
    cache_dirs = [private / "rerank", world.cache_dir / "rerank"]
    rerank_missing, prepared = [], {}
    world.query_vector = lambda q: vectors[hashlib.sha256(q.encode()).hexdigest()]
    for name, group in cases.items():
        metadata[name]["unresolved_gold_ids"] = sorted({p for c in group for p in ev.gold_passages(c) if p not in world.passages_by_id})
        for c in group:
            if hashlib.sha256(c["question"].encode()).hexdigest() not in vectors:
                continue
            lists = pools(world, c["question"])
            prepared[c["case_id"]] = lists
            for method, pool in (("R2", lists["hybrid"]), ("R3", lists["R1a"])):
                candidates = [world.chunks[i] for i in pool[:rr.POOL]]
                if cached_rerank(c["question"], candidates, cache_dirs) is None:
                    system, user, _ = rr.load_prompt()
                    tokens = estimated_tokens(system + user.format(candidates=rr.render(candidates), question=c["question"]))
                    rerank_missing.append({"set": name, "case_id": c["case_id"], "method": method,
                                           "cache_key": rerank_key(c["question"], candidates),
                                           "estimated_input_tokens": tokens,
                                           "estimated_cost_usd": prices.chat_cost(rr.MODEL, tokens, 4000)})
    # Missing vectors prevent exact pool inspection; do not present zero as the
    # complete reranking budget. Use the largest rendered chunks for planning.
    unknown_pool_estimate = 0.0
    if missing:
        largest = sorted(world.chunks.values(), key=lambda c: len(rr.render([c]).encode()), reverse=True)[:rr.POOL]
        system, user, _ = rr.load_prompt()
        rendered = rr.render(largest)
        unknown_pool_estimate = sum(
            2 * prices.chat_cost(rr.MODEL, estimated_tokens(system + user.format(candidates=rendered, question=r["question"])), 4000)
            for r in missing
        )
    audit = {"id": run_id, "sets": metadata, "provenance": prov,
             "script_sha256": digest(Path(__file__)), "price_sha256": digest(paths.SPECS / "prices.yaml"),
             "prompt_sha256": digest(rr.PROMPT_FILE),
             "missing_query_embeddings": [{k: v for k, v in r.items() if k != "question"} for r in missing],
             "missing_unique_query_count": len(unique_missing), "embedding_estimated_cost_usd": sum(r["estimated_tokens"] for r in unique_missing.values()) * 0.13 / 1_000_000,
             "token_estimator": "ceil(UTF-8 bytes / 4), heuristic, not measured usage",
             "rerank_cache_misses": rerank_missing, "rerank_audit_complete": not missing,
             "rerank_estimated_cost_usd": sum(r["estimated_cost_usd"] for r in rerank_missing),
             "unknown_pool_rerank_estimated_cost_usd": unknown_pool_estimate,
             "unknown_pool_rerank_estimate_method": "two calls per missing case, largest 30 rendered chunks, 4000 output tokens",
             "rerank_estimate_output_tokens_per_call": 4000, "answer_generation_calls": 0}
    output.mkdir(parents=True, exist_ok=False)
    (output / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    if not run:
        return audit
    if not allow_paid and (missing or rerank_missing):
        raise ValueError(f"offline cache incomplete; audit saved at {output / 'audit.json'}; use a new ID")
    if unique_missing:
        qs = [r["question"] for r in unique_missing.values()]
        embedded = dn.embed(rt.EMBEDDING_MODEL, qs, purpose=f"heldout-retrieval:{run_id}")
        for q, v in zip(qs, embedded):
            vectors[hashlib.sha256(q.encode()).hexdigest()] = v
    private.mkdir(parents=True, exist_ok=True)
    local_qv.write_text(json.dumps({k: v.tolist() for k, v in vectors.items()}))
    results, scores, total_cost = {}, [], 0.0
    for name, group in cases.items():
        rowsets = {m: [] for m in METHODS}
        for c in group:
            lists = prepared.get(c["case_id"]) or pools(world, c["question"])
            extra = {}
            for method, pool in (("R2", lists["hybrid"]), ("R3", lists["R1a"])):
                candidates = [world.chunks[i] for i in pool[:rr.POOL]]
                result = cached_rerank(c["question"], candidates, cache_dirs)
                if result is None:
                    if not allow_paid:
                        raise ValueError("offline rerank cache miss")
                    result = rr.rerank(c["question"], candidates, cache_dir=private / "rerank")
                    total_cost += result.cost_usd if not result.cached else 0.0
                    if total_cost > exp.BUDGET_USD:
                        raise exp.BudgetExceeded("new rerank spend exceeded $3; private responses retained")
                lists[method] = [pool[i] for i in result.order[:rr.POOL]]
                extra[method] = {"rerank_ok": result.ok, "cached": result.cached,
                                 "cost_usd": result.cost_usd, "tokens": [result.prompt_tokens, result.completion_tokens]}
            for method in METHODS:
                row = {**score(c, lists[method], world), **extra.get(method, {})}
                rowsets[method].append(row)
                scores.append({"set": name, "method": method, **row})
        results[name] = {"metrics": {m: aggregate(rows) for m, rows in rowsets.items()},
                         "paired_R3_minus_hybrid": paired(rowsets["R3"], rowsets["hybrid"]),
                         "rerank_failures": {m: sum(not r["rerank_ok"] for r in rowsets[m]) for m in ("R2", "R3")}}
    final = {"audit": audit, "results": results, "new_rerank_cost_usd": total_cost,
             "config": {"methods": METHODS, "bootstrap": "2000 percentile case resamples, seed 0, 95%", "chunks": rt.CHUNK_CONFIG,
                        "embedding": rt.EMBEDDING_MODEL, "rerank_model": rr.MODEL, "pool": rr.POOL,
                        "depth": exp.DEPTH, "rrf_c": exp.RRF_C, "soft_bonus": exp.BONUS, "R3_component": "R1a"}}
    (output / "scores.jsonl").write_text("".join(json.dumps(r) + "\n" for r in scores))
    (output / "metrics.json").write_text(json.dumps(final, indent=2) + "\n")
    return final


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", required=True)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--allow-paid", action="store_true")
    args = parser.parse_args()
    result = execute(args.id, args.run, args.allow_paid)
    audit = result.get("audit", result)
    print(json.dumps({"id": args.id, "sets": audit["sets"], "missing_unique_query_count": audit["missing_unique_query_count"],
                      "embedding_estimated_cost_usd": audit["embedding_estimated_cost_usd"],
                      "rerank_cache_miss_count": len(audit["rerank_cache_misses"]),
                      "rerank_estimated_cost_usd": audit["rerank_estimated_cost_usd"],
                      "unknown_pool_rerank_estimated_cost_usd": audit["unknown_pool_rerank_estimated_cost_usd"],
                      "rerank_audit_complete": audit["rerank_audit_complete"]}, indent=2))


if __name__ == "__main__":
    main()
