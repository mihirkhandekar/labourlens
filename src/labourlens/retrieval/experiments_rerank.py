"""Retrieval improvement experiments R0-R3 (D-029), dev split only. One factor at a time on the same chunks, embeddings and cases.

R0 baseline hybrid RRF (current candidate default)   R1a/R1b query-metadata hard filter / soft boost (period.py)
R2 LLM listwise rerank of the top 30 (rerank.py)      R3 best R1 + R2, run only if both help individually (pre-registered rule)
Committed outputs: metrics and per-case scores (chunk ids, ranks, flags), no MOM text. Raw rerank responses: data/runs/dev-R2/ (gitignored).
"""

from __future__ import annotations

import hashlib
import json
import statistics
import time
import re
import subprocess
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from labourlens import paths
from labourlens.answer import context as cx
from labourlens.retrieval import chunk as ck
from labourlens.retrieval import dense as dn
from labourlens.retrieval import evaluate as ev
from labourlens.retrieval import period as pr
from labourlens.retrieval import rerank as rr
from labourlens.retrieval import runtime as rt
from labourlens.retrieval.bm25_index import BM25Config, BM25Index

DEPTH = 50
RRF_C = 60
BONUS = 0.5 / (RRF_C + 1)  # pre-registered primary soft-boost bonus per matching hint
BUDGET_USD = 3.0
KS = (3, 5, 8, 10)
RUNS = paths.EXPERIMENTS / "runs"
MATRIX_FILE = paths.ROOT / "data" / "runs" / "dev-R0" / "dense_matrix.npy"
QV_FILE = paths.ROOT / "data" / "runs" / "dev-R0" / "query_vectors.json"


@dataclass(frozen=True)
class RunPaths:
    tag: str | None = None

    def __post_init__(self) -> None:
        if self.tag is not None and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", self.tag):
            raise ValueError("tag must contain only letters, digits, underscores and hyphens, starting with a letter or digit")

    def config(self, name: str) -> Path:
        return RUNS / (f"dev-R-{self.tag}-{name}" if self.tag is not None else f"dev-{name}")

    def summary(self, markdown: bool = False) -> Path:
        if self.tag is not None:
            return RUNS / f"dev-R-{self.tag}" / ("SUMMARY.md" if markdown else "summary.json")
        return RUNS / ("dev-R-SUMMARY.md" if markdown else "dev-R-summary.json")

    def cache(self, corpus_hash: str) -> Path:
        identity = hashlib.sha256(f"{corpus_hash}:{rt.EMBEDDING_MODEL}:{rt.CHUNK_CONFIG}".encode()).hexdigest()
        return paths.ROOT / "data" / "runs" / f"dev-R-{self.tag}" / identity

    def refuse_existing(self) -> None:
        if self.tag is not None:
            outputs = [self.summary().parent, *(self.config(n) for n in ("R0", "R1a", "R1b", "R1b_x0.5", "R1b_x2", "R2", "R3"))]
            if any(p.exists() for p in outputs):
                raise SystemExit(f"retrieval tag {self.tag!r} already exists; choose a new tag")


def provenance(chunks: list, gold_sha: str) -> dict:
    corpus_hash = ck.corpus_hash(chunks)
    snapshot = json.loads((paths.EXPERIMENTS / "corpus-snapshots" / "v3.1.json").read_text())
    version = "v3.1" if snapshot["chunk_corpus_sha256"] == corpus_hash and snapshot["chunks"] == len(chunks) else "unregistered"
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=paths.ROOT, text=True).strip()
    return {"corpus_version": version, "chunk_count": len(chunks), "corpus_hash": corpus_hash,
            "gold_file_sha256": gold_sha, "code_commit": commit}


class BudgetExceeded(RuntimeError):
    pass


class World:
    def __init__(self, run_paths: RunPaths | None = None, offline: bool = False) -> None:
        self.offline = offline  # True: a missing cached vector stops the run instead of calling the embeddings API
        self.passages = ck.load_passages()
        chunks = ck.build_chunks(ck.CONFIGS[rt.CHUNK_CONFIG], self.passages)
        self.chunks = {c.chunk_id: c for c in chunks}
        self.bm25 = BM25Index.build(chunks, BM25Config())
        self.cache_dir = run_paths.cache(ck.corpus_hash(chunks)) if run_paths is not None and run_paths.tag is not None else None
        self.qv_file = self.cache_dir / "query_vectors.json" if self.cache_dir is not None else QV_FILE
        self.dense = self._frozen_dense(chunks)
        self.passages_by_id = {p["passage_id"]: p for p in self.passages}
        self.n = len(chunks)

    def _frozen_dense(self, chunks) -> dn.DenseIndex:
        """Chunk vectors frozen per corpus on first use (same reason as query vectors): the shared embedding cache can lose entries to a concurrent
        writer and the hosted API re-embeds them with tiny differences, which flips near-ties between runs."""
        cfg = dn.DenseConfig(rt.EMBEDDING_MODEL)
        ids = [c.chunk_id for c in chunks]
        tag = hashlib.sha256("|".join(ids).encode()).hexdigest()[:16]
        f = self.cache_dir / "dense_matrix.npy" if self.cache_dir is not None else MATRIX_FILE.with_name(f"dense_matrix_{tag}.npy")
        if f.exists():
            d = object.__new__(dn.DenseIndex)
            d.cfg, d.chunk_ids, d.matrix = cfg, ids, np.load(f)
            return d
        if self.offline:
            raise SystemExit(f"offline: frozen dense matrix missing at {f}; not calling the API")
        d = dn.DenseIndex(chunks, cfg)
        f.parent.mkdir(parents=True, exist_ok=True)
        np.save(f, d.matrix)
        return d

    def query_vector(self, question: str) -> np.ndarray:
        """Query vectors are frozen on first use (data/runs, gitignored): the hosted embedding API is not bit-identical across calls and the shared
        embedding cache can be rewritten by a concurrent process, either of which re-orders near-ties between runs of the same experiment."""
        self.qv_file.parent.mkdir(parents=True, exist_ok=True)
        if not hasattr(self, "_qv"):
            self._qv = json.loads(self.qv_file.read_text()) if self.qv_file.exists() else {}
        key = hashlib.sha256(question.encode()).hexdigest()
        if key not in self._qv and self.offline:
            raise SystemExit(f"offline: no cached query vector for {question[:60]!r} in {self.qv_file}; not calling the API")
        if key not in self._qv:
            self._qv[key] = dn.embed(rt.EMBEDDING_MODEL, [question], purpose="queries")[0].tolist()
            self.qv_file.write_text(json.dumps(self._qv))
        return np.asarray(self._qv[key], dtype=np.float32)

    def full_rankings(self, question: str):
        # (top DEPTH, full): k=DEPTH is searched separately because bm25s orders tied scores differently by k, and R0 must equal the shipped hybrid
        bm = (self.bm25.search(question, DEPTH), self.bm25.search(question, self.n))
        q = self.query_vector(question)
        s = self.dense.matrix @ q
        order = np.argsort(-s)
        return bm, [(self.dense.chunk_ids[int(i)], float(s[i])) for i in order]


def fuse(bm: tuple[list, list], de: list, allowed: frozenset[str] | None, chunks: dict, boosts: tuple[float, frozenset | None, frozenset | None] | None = None) -> list[tuple[str, float]]:
    """Top-DEPTH of each list (after optional document restriction), reciprocal rank fusion, optional additive bonus."""
    if allowed is None:
        bm_l = bm[0]
    else:
        bm_l = [x for x in bm[1] if chunks[x[0]].source_id in allowed]
        de = [x for x in de if chunks[x[0]].source_id in allowed]
    fused = dn.rrf([bm_l[:DEPTH], de[:DEPTH]], k=10**9, c=RRF_C)
    if boosts:
        bonus, period_ids, stage_ids = boosts
        fused = [(cid, s + bonus * ((period_ids is not None and chunks[cid].source_id in period_ids) + (stage_ids is not None and chunks[cid].source_id in stage_ids)))
                 for cid, s in fused]
        fused.sort(key=lambda x: -x[1])
    return fused


def hint_sets(hints: pr.Hints) -> tuple[frozenset | None, frozenset | None]:
    docs = pr.catalogue()
    per = frozenset(d.source_id for d in docs if pr.period_match(d, hints)) if hints.quarters else None
    stg = frozenset(d.source_id for d in docs if pr.stage_match(d, hints)) if hints.stage else None
    return per, stg


def score_row(case: dict, ranked: list[str], chunks: dict, pool_ranked: list[str], extra: dict | None = None) -> dict:
    gold = ev.gold_passages(case)
    rels = [int(bool(gold & set(chunks[c].source_passage_ids))) for c in ranked[:10]]
    first = next((i + 1 for i, r in enumerate(rels) if r), None)
    pool_first = next((i + 1 for i, c in enumerate(pool_ranked) if gold & set(chunks[c].source_passage_ids)), None)
    cov8 = len(gold & {p for c in ranked[:8] for p in chunks[c].source_passage_ids}) / len(gold)
    return {"case_id": case["case_id"], "family": case["family"], "first_relevant_rank": first, "pool_first_relevant_rank": pool_first,
            "gold_passage_coverage@8": round(cov8, 4), "ranked": [{"chunk_id": c, "relevant": r} for c, r in zip(ranked[:10], rels)], **(extra or {})}


def bootstrap(x: np.ndarray, rng: np.random.Generator, n: int = 2000) -> tuple[float, float]:
    idx = rng.integers(0, len(x), size=(n, len(x)))
    m = x[idx].mean(axis=1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def metrics(rows: list[dict], base_rows: list[dict] | None, latency_ms: list[float], cost: list[float] | None, extra_lat: list[float] | None) -> dict:
    n = len(rows)
    fr = [r["first_relevant_rank"] for r in rows]
    h = {k: np.array([1.0 if f and f <= k else 0.0 for f in fr]) for k in KS}
    rng = np.random.default_rng(0)
    out: dict = {"n_cases": n}
    for k in KS:
        out[f"hit@{k}"] = round(float(h[k].mean()), 4)
    out["mrr@10"] = round(sum(1 / f for f in fr if f) / n, 4)
    out["gold_passage_coverage@8"] = round(statistics.mean(r["gold_passage_coverage@8"] for r in rows), 4)
    out["pool_recall@30"] = round(sum(1 for r in rows if r["pool_first_relevant_rank"] and r["pool_first_relevant_rank"] <= 30) / n, 4)
    out["pool_recall@50"] = round(sum(1 for r in rows if r["pool_first_relevant_rank"] and r["pool_first_relevant_rank"] <= 50) / n, 4)
    lo, hi = bootstrap(h[8], rng)
    out["hit@8_ci95"] = [round(lo, 4), round(hi, 4)]
    if base_rows is not None:
        b8 = np.array([1.0 if r["first_relevant_rank"] and r["first_relevant_rank"] <= 8 else 0.0 for r in base_rows])
        d = h[8] - b8
        dlo, dhi = bootstrap(d, rng)
        out["hit@8_diff_vs_R0"] = round(float(d.mean()), 4)
        out["hit@8_diff_ci95"] = [round(dlo, 4), round(dhi, 4)]
        out["paired_hit@8_better_worse"] = [int((d > 0).sum()), int((d < 0).sum())]
        b_rank = [r["first_relevant_rank"] or 99 for r in base_rows]
        out["paired_rank_better_worse_same"] = [sum(1 for a, b in zip(fr, b_rank) if (a or 99) < b), sum(1 for a, b in zip(fr, b_rank) if (a or 99) > b),
                                                sum(1 for a, b in zip(fr, b_rank) if (a or 99) == b)]
    for key, sel in (("family", lambda r: r["family"]), ("hint", lambda r: "has_hint" if r["has_hint"] else "no_hint")):
        grp: dict[str, list] = {}
        for r in rows:
            grp.setdefault(sel(r), []).append(1.0 if r["first_relevant_rank"] and r["first_relevant_rank"] <= 8 else 0.0)
        out[f"by_{key}_hit@8"] = {g: {"n": len(v), "hit@8": round(sum(v) / len(v), 3)} for g, v in sorted(grp.items())}
    out["added_latency_ms_p50"] = round(statistics.median(extra_lat), 2) if extra_lat else 0.0
    out["added_latency_ms_p95"] = round(float(np.percentile(extra_lat, 95)), 2) if extra_lat else 0.0
    out["retrieval_fuse_ms_p50"] = round(statistics.median(latency_ms), 3)
    if cost is not None:
        out["cost_usd_per_query_mean"] = round(statistics.mean(cost), 6)
        out["cost_usd_total"] = round(sum(cost), 5)
    return out


def write(exp: str, m: dict, rows: list[dict], config: dict) -> None:
    d = RUNS / exp
    d.mkdir(parents=True, exist_ok=True)
    (d / "metrics.json").write_text(json.dumps({"config": config, "metrics": m}, indent=1))
    (d / "scores.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")


def coverage_check(label: str, rows: list[dict], cases: dict, w: World) -> dict:
    in_ctx = in_first8 = 0
    for r in rows:
        gold = ev.gold_passages(cases[r["case_id"]])
        chunks = [w.chunks[x["chunk_id"]] for x in r["ranked"][:8]]
        ctx_ids = [p.passage_id for p in cx.build_context(chunks, w.passages_by_id)]
        in_ctx += bool(gold & set(ctx_ids))
        in_first8 += bool(gold & set(ctx_ids[:8]))
    n = len(rows)
    return {"config": label, "n": n, "gold_in_context_of_top8_chunks": round(in_ctx / n, 4), "gold_in_first8_context_passages": round(in_first8 / n, 4)}


def fmt_ci(m: dict) -> str:
    return f"{m['hit@8']:.3f} [{m['hit@8_ci95'][0]:.3f}, {m['hit@8_ci95'][1]:.3f}]"


def run(split: str = "dev", rerank_on: bool = True, tag: str | None = None) -> None:
    if split != "dev":
        raise SystemExit("retrieval-exp2 runs on the dev split only (held-out stays untouched)")
    run_paths = RunPaths(tag)
    run_paths.refuse_existing()
    t_start = time.time()
    w = World(run_paths) if tag is not None else World()
    gold_sha = hashlib.sha256((ev.GOLD / "draft_cases.jsonl").read_bytes()).hexdigest()  # recorded with the results: the gold file is still being corrected
    run_provenance = provenance(list(w.chunks.values()), gold_sha) if tag is not None else {}
    cases = ev.text_cases(ev.load_cases("dev"))
    by_case = {c["case_id"]: c for c in cases}
    print(f"{len(cases)} dev text cases, {w.n} chunks")
    prep = []  # per case: question, hints, full rankings
    for c in cases:
        t0 = time.perf_counter()
        hints = pr.parse(c["question"])
        parse_ms = (time.perf_counter() - t0) * 1000
        bm, de = w.full_rankings(c["question"])
        prep.append((c, hints, parse_ms, bm, de))

    # sanity: R0 here must equal the shipped hybrid retriever (first 10 cases; reported, since a re-embedded query can move near-ties)
    shipped = dn.HybridIndex(w.bm25, w.dense)
    r0_same = sum([x[0] for x in fuse(bm, de, None, w.chunks)[:50]] == [x[0] for x in shipped.search(c["question"], 50)] for c, _, _, bm, de in prep[:10])
    print(f"R0 equals the shipped hybrid on {r0_same}/10 checked cases")

    results: dict[str, dict] = {}
    rowsets: dict[str, list[dict]] = {}

    def local_config(name: str, make_pool) -> None:
        rows, lat = [], []
        for c, hints, parse_ms, bm, de in prep:
            t0 = time.perf_counter()
            pool = make_pool(hints, bm, de)
            ms = (time.perf_counter() - t0) * 1000 + (parse_ms if name != "R0" else 0.0)
            lat.append(ms)
            ids = [x[0] for x in pool]
            rows.append(score_row(c, ids, w.chunks, ids, {"has_hint": hints.any(), "period_hint": bool(hints.quarters), "stage_hint": hints.stage}))
        rowsets[name] = rows
        results[name] = {"lat": lat}

    local_config("R0", lambda h, bm, de: fuse(bm, de, None, w.chunks))
    local_config("R1a", lambda h, bm, de: fuse(bm, de, pr.matching_sources(h), w.chunks))

    def soft(mult: float):
        def f(h, bm, de):
            per, stg = hint_sets(h)
            return fuse(bm, de, None, w.chunks, (BONUS * mult, per, stg) if (per or stg) else None)
        return f

    local_config("R1b", soft(1.0))
    local_config("R1b_x0.5", soft(0.5))
    local_config("R1b_x2", soft(2.0))
    base_lat = results["R0"]["lat"]
    for name in ("R0", "R1a", "R1b", "R1b_x0.5", "R1b_x2"):
        lat = results[name]["lat"]
        extra = [a - b for a, b in zip(lat, base_lat)] if name != "R0" else None
        results[name] = metrics(rowsets[name], None if name == "R0" else rowsets["R0"], lat, None, extra)

    total_cost = 0.0

    def run_rerank(name: str, pool_fn) -> None:
        nonlocal total_cost
        pools = []
        for c, hints, parse_ms, bm, de in prep:
            pools.append((c, hints, [x[0] for x in pool_fn(hints, bm, de)]))
        out: dict[str, rr.RerankResult] = {}
        with ThreadPoolExecutor(max_workers=6) as ex:
            cache_kwargs = {"cache_dir": w.cache_dir / "rerank"} if tag is not None else {}
            futs = {ex.submit(rr.rerank, c["question"], [w.chunks[i] for i in ids[:rr.POOL]], **cache_kwargs): (c, ids) for c, _, ids in pools}
            for f in as_completed(futs):
                c, _ = futs[f]
                out[c["case_id"]] = f.result()
                total_cost += out[c["case_id"]].cost_usd if not out[c["case_id"]].cached else 0.0
                if total_cost > BUDGET_USD:
                    for g in futs:
                        g.cancel()
                    raise BudgetExceeded(f"rerank spend {total_cost:.3f} USD exceeds the {BUDGET_USD} USD cap")
        rows, cost, lat = [], [], []
        for c, hints, ids in pools:
            r = out[c["case_id"]]
            ranked = [ids[i] for i in r.order[:rr.POOL]]
            rows.append(score_row(c, ranked, w.chunks, ids, {"has_hint": hints.any(), "period_hint": bool(hints.quarters), "stage_hint": hints.stage,
                                                              "rerank_ok": r.ok, "rerank_tokens": [r.prompt_tokens, r.completion_tokens, r.reasoning_tokens]}))
            cost.append(r.cost_usd)
            lat.append(r.seconds * 1000)
        rowsets[name] = rows
        m = metrics(rows, rowsets["R0"], base_lat, cost, lat)
        m["rerank_failures"] = sum(1 for r in rows if not r["rerank_ok"])
        m["rerank_latency_s_p50_p95"] = [round(statistics.median(lat) / 1000, 2), round(float(np.percentile(lat, 95)) / 1000, 2)]
        results[name] = m

    r3_ran = False
    if rerank_on:
        run_rerank("R2", lambda h, bm, de: fuse(bm, de, None, w.chunks))
        r1_best = max(("R1a", "R1b"), key=lambda n: (results[n]["hit@8"], results[n]["mrr@10"]))
        gain1 = results[r1_best]["hit@8"] - results["R0"]["hit@8"]
        gain2 = results["R2"]["hit@8"] - results["R0"]["hit@8"]
        print(f"R1 best={r1_best} gain {gain1:+.3f}; R2 gain {gain2:+.3f}")
        if gain1 >= 0.05 and gain2 >= 0.05:
            r3_ran = True
            if r1_best == "R1a":
                run_rerank("R3", lambda h, bm, de: fuse(bm, de, pr.matching_sources(h), w.chunks))
            else:
                def pool_soft(h, bm, de):
                    per, stg = hint_sets(h)
                    return fuse(bm, de, None, w.chunks, (BONUS, per, stg) if (per or stg) else None)
                run_rerank("R3", pool_soft)
            results["R3"]["r1_component"] = r1_best
            a = np.array([1.0 if r["first_relevant_rank"] and r["first_relevant_rank"] <= 8 else 0.0 for r in rowsets["R3"]])
            b = np.array([1.0 if r["first_relevant_rank"] and r["first_relevant_rank"] <= 8 else 0.0 for r in rowsets["R2"]])
            lo, hi = bootstrap(a - b, np.random.default_rng(0))
            results["R3"]["hit@8_diff_vs_R2"] = round(float((a - b).mean()), 4)
            results["R3"]["hit@8_diff_vs_R2_ci95"] = [round(lo, 4), round(hi, 4)]
            results["R3"]["paired_hit@8_vs_R2_better_worse"] = [int((a > b).sum()), int((a < b).sum())]

    names = [n for n in ("R0", "R1a", "R1b", "R2", "R3") if n in results]
    for n in names + ["R1b_x0.5", "R1b_x2"]:
        write(run_paths.config(n).name, results[n], rowsets[n], {"split": "dev", "chunks": rt.CHUNK_CONFIG, "embedding": rt.EMBEDDING_MODEL, "depth": DEPTH, "rrf_c": RRF_C,
                                                  "gold_file_sha256": gold_sha, "soft_bonus": BONUS if n.startswith("R1b") or n == "R3" else None, "rerank_model": rr.MODEL if n in ("R2", "R3") else None,
                                                  "rerank_prompt_hash": rr.load_prompt()[2] if n in ("R2", "R3") else None, "pool": rr.POOL if n in ("R2", "R3") else None, **run_provenance})
    candidates = [n for n in ("R1a", "R1b", "R2", "R3") if n in results]
    best = max(candidates, key=lambda n: (results[n]["hit@8"], results[n]["mrr@10"]))
    cov = [coverage_check("R0", rowsets["R0"], by_case, w), coverage_check(best, rowsets[best], by_case, w)]
    summary = {"n_cases": len(cases), "gold_file_sha256": gold_sha, "r0_equals_shipped_hybrid_first10": r0_same, "corpus_hash": ck.corpus_hash(list(w.chunks.values())), "best_vs_R0": best, "r3_ran": r3_ran, "total_cost_usd_rerank_new_calls": round(total_cost, 5),
               "end_to_end_context_coverage": cov, "metrics": {n: results[n] for n in names + ["R1b_x0.5", "R1b_x2"]},
               "hint_coverage": {"any_hint": sum(1 for c, h, *_ in prep if h.any()), "period_hint": sum(1 for c, h, *_ in prep if h.quarters),
                                 "stage_hint": sum(1 for c, h, *_ in prep if h.stage), "stage_conflict": sum(1 for c, h, *_ in prep if h.stage_conflict),
                                 "filter_active_R1a": sum(1 for c, h, *_ in prep if pr.matching_sources(h) is not None),
                                 "period_hint_but_no_document_in_period": sum(1 for c, h, *_ in prep if h.quarters and not any(pr.period_match(d, h) for d in pr.catalogue())),
                                 "hint_but_no_filter": sum(1 for c, h, *_ in prep if h.any() and pr.matching_sources(h) is None)},
               "first_relevant_rank_histogram": {n: dict(sorted(Counter(r["first_relevant_rank"] or 0 for r in rowsets[n]).items())) for n in names}}
    if tag is not None:
        summary.update(run_provenance)
        summary["tag"] = tag
        summary["changes_vs_frozen_R_series"] = "Current corpus and gold, current code, isolated corpus-and-model-keyed caches; same development comparison and conditional R3 rule. Not new held-out evidence."
    run_paths.summary().parent.mkdir(parents=True, exist_ok=True)
    run_paths.summary().write_text(json.dumps(summary, indent=1))
    L = [f"# Retrieval improvement experiments R0-R3, dev text cases (n={len(cases)})", "",
         f"Generated by `labourlens retrieval-exp2`; numbers come from `experiments/runs/dev-R*/metrics.json`. Gold file sha256 `{gold_sha}`.", "",
         "| config | hit@3 | hit@5 | hit@8 [95% CI] | hit@10 | MRR@10 | gold-passage coverage@8 | pool recall@30 / @50 | hit@8 diff vs R0 [95% CI] | paired hit@8 better/worse | added latency p50 ms | cost $/query |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    if tag is not None:
        L[2] = (f"Generated by `labourlens retrieval-exp2 --tag {tag}`; configuration metrics in "
                f"`experiments/runs/dev-R-{tag}-R*/metrics.json`. Gold file sha256 `{gold_sha}`.")
        L[4:4] = [f"## {run_provenance['corpus_version']} re-run", "",
                  f"Corpus: {run_provenance['chunk_count']:,} chunks; hash `{run_provenance['corpus_hash']}`. Code commit `{run_provenance['code_commit']}`.",
                  "", "Changed versus the frozen R-series: " + summary["changes_vs_frozen_R_series"],
                  "Frozen R-series files are unchanged. Historical differences are not a controlled estimate of a retrieval-only effect.", ""]
    for n in names + ["R1b_x0.5", "R1b_x2"]:
        m = results[n]
        diff = "-" if n == "R0" else f"{m['hit@8_diff_vs_R0']:+.3f} [{m['hit@8_diff_ci95'][0]:+.3f}, {m['hit@8_diff_ci95'][1]:+.3f}]"
        pair = "-" if n == "R0" else f"{m['paired_hit@8_better_worse'][0]} / {m['paired_hit@8_better_worse'][1]}"
        L.append(f"| {n} | {m['hit@3']} | {m['hit@5']} | {fmt_ci(m)} | {m['hit@10']} | {m['mrr@10']} | {m['gold_passage_coverage@8']} | {m['pool_recall@30']} / {m['pool_recall@50']} | {diff} | {pair} "
                 f"| {m['added_latency_ms_p50']} | {m.get('cost_usd_per_query_mean', 0)} |")
    L += ["", "## hit@8 by family", "", "| config | " + " | ".join(f"{f}" for f in results["R0"]["by_family_hit@8"]) + " |", "|---|" + "---|" * len(results["R0"]["by_family_hit@8"])]
    for n in names + ["R1b_x0.5", "R1b_x2"]:
        L.append(f"| {n} | " + " | ".join(f"{v['hit@8']} (n={v['n']})" for v in results[n]["by_family_hit@8"].values()) + " |")
    L += ["", "## hit@8 by whether the question carries a period/stage hint", "", "| config | " + " | ".join(results["R0"]["by_hint_hit@8"]) + " |", "|---|" + "---|" * len(results["R0"]["by_hint_hit@8"])]
    for n in names + ["R1b_x0.5", "R1b_x2"]:
        L.append(f"| {n} | " + " | ".join(f"{v['hit@8']} (n={v['n']})" for v in results[n]["by_hint_hit@8"].values()) + " |")
    L += ["", f"Hint coverage: {json.dumps(summary['hint_coverage'])}", "", f"## End-to-end context coverage (retrieval only; best config = {best})", "",
          "| config | gold passage in the context built from the top-8 chunks | gold passage in the first 8 context passages |", "|---|---|---|"]
    L += [f"| {c['config']} | {c['gold_in_context_of_top8_chunks']} | {c['gold_in_first8_context_passages']} |" for c in cov]
    L += ["", f"Rerank spend on new API calls this run: ${total_cost:.4f}. Wall time {time.time() - t_start:.0f}s.", ""]
    run_paths.summary(markdown=True).write_text("\n".join(L) + "\n")
    print("\n".join(L))


METHODS = ("bm25", "dense", "hybrid")
METHOD_LABEL = {"bm25": "BM25 only", "dense": "Dense only", "hybrid": "Hybrid (RRF, = R0)"}


def methods_dir(tag: str) -> Path:
    return RUNS / f"dev-R-{tag}-methods"


def method_hits(rows: list[dict], k: int) -> np.ndarray:
    return np.array([1.0 if r["first_relevant_rank"] and r["first_relevant_rank"] <= k else 0.0 for r in rows])


def run_methods(tag: str) -> dict:
    """BM25, dense and hybrid on the same dev cases and corpus, from cached vectors only (rules: docs/experiments/retrieval-v31-rerun.md)."""
    RunPaths(tag)  # validates the tag
    out_dir = methods_dir(tag)
    if out_dir.exists():
        raise SystemExit(f"{out_dir} already exists; choose a new tag")
    w = World(RunPaths(tag), offline=True)
    gold_sha = hashlib.sha256((ev.GOLD / "draft_cases.jsonl").read_bytes()).hexdigest()
    prov = provenance(list(w.chunks.values()), gold_sha)
    cases = ev.text_cases(ev.load_cases("dev"))
    rowsets: dict[str, list[dict]] = {m: [] for m in METHODS}
    for c in cases:
        bm, de = w.full_rankings(c["question"])
        lists = {"bm25": [x[0] for x in bm[0]], "dense": [x[0] for x in de[:DEPTH]], "hybrid": [x[0] for x in fuse(bm, de, None, w.chunks)]}
        for m in METHODS:
            rowsets[m].append(score_row(c, lists[m], w.chunks, lists[m]))
    r0 = [json.loads(line) for line in (RUNS / f"dev-R-{tag}-R0" / "scores.jsonl").read_text().splitlines() if line]
    r0_rank = {r["case_id"]: r["first_relevant_rank"] for r in r0}
    r0_match = sum(r["first_relevant_rank"] == r0_rank.get(r["case_id"], "absent") for r in rowsets["hybrid"])
    rng = np.random.default_rng(0)
    metrics_out: dict = {}
    for m in METHODS:
        rows, fr = rowsets[m], [r["first_relevant_rank"] for r in rowsets[m]]
        entry: dict = {"n_cases": len(rows), "mrr@10": round(sum(1 / f for f in fr if f and f <= 10) / len(rows), 4)}
        for k in (8, 10):
            h = method_hits(rows, k)
            lo, hi = bootstrap(h, rng)
            entry[f"hit@{k}"], entry[f"hit@{k}_ci95"] = round(float(h.mean()), 4), [round(lo, 4), round(hi, 4)]
        metrics_out[m] = entry
    paired = {}
    for other in ("bm25", "dense"):
        d = method_hits(rowsets["hybrid"], 8) - method_hits(rowsets[other], 8)
        lo, hi = bootstrap(d, rng)
        paired[f"hybrid_minus_{other}_hit@8"] = {"diff": round(float(d.mean()), 4), "ci95": [round(lo, 4), round(hi, 4)], "better_worse": [int((d > 0).sum()), int((d < 0).sum())]}
    r0_hit8 = json.loads((RUNS / f"dev-R-{tag}-R0" / "metrics.json").read_text())["metrics"]["hit@8"]
    result = {"config": {"split": "dev", "chunks": rt.CHUNK_CONFIG, "embedding": rt.EMBEDDING_MODEL, "depth": DEPTH, "rrf_c": RRF_C, "bootstrap": "2000 percentile resamples, seed 0", **prov},
              "metrics": metrics_out, "paired": paired,
              "hybrid_matches_R0_first_relevant_rank": {"matching_cases": r0_match, "of": len(cases), "R0_hit@8": r0_hit8}}
    out_dir.mkdir(parents=True)
    (out_dir / "metrics.json").write_text(json.dumps(result, indent=1))
    per_case = [{"case_id": c["case_id"], "family": c["family"], **{f"{m}_first_relevant_rank": rowsets[m][i]["first_relevant_rank"] for m in METHODS}} for i, c in enumerate(cases)]
    (out_dir / "scores.jsonl").write_text("\n".join(json.dumps(r) for r in per_case) + "\n")
    n = len(cases)

    def cell(m: str, k: int) -> str:
        e = metrics_out[m]
        return f"{e[f'hit@{k}']:.3f} [{e[f'hit@{k}_ci95'][0]:.3f}, {e[f'hit@{k}_ci95'][1]:.3f}]"
    L = [f"# BM25, dense and hybrid on the same {n} development cases (corpus {prov['corpus_version']}, {prov['chunk_count']:,} chunks)", "",
         f"Generated by `labourlens retrieval-exp2 --tag {tag} --methods`. Rules were declared before running in `docs/experiments/retrieval-v31-rerun.md`. "
         f"Gold file sha256 `{gold_sha}`; code commit `{prov['code_commit']}`. Cached vectors only; no API call. 95% intervals: case bootstrap.", "",
         "| method | hit@8 [95% CI] | hit@10 [95% CI] | MRR@10 |", "|---|---|---|---|"]
    L += [f"| {METHOD_LABEL[m]} | {cell(m, 8)} | {cell(m, 10)} | {metrics_out[m]['mrr@10']} |" for m in METHODS]
    L += ["", f"Hybrid equals the R0 row of `dev-R-{tag}-R0` on {r0_match} of {n} cases by first relevant rank (R0 hit@8 {r0_hit8}).", "",
          "Paired hit@8, hybrid minus the single method: " + "; ".join(
              f"{k.split('_')[2]}: {v['diff']:+.3f} [{v['ci95'][0]:+.3f}, {v['ci95'][1]:+.3f}] ({v['better_worse'][0]} better, {v['better_worse'][1]} worse)" for k, v in paired.items()) + ".", "",
          "## Why the early deck figure differs", "",
          f"The early comparison reported hit@10 on 24 cases over a 46-document corpus; the later hybrid (R0) hit@8 is on these {n} cases over {prov['chunk_count']:,} chunks of the current build. The two differ in three ways at once: "
          "(1) the cutoff, hit@10 against hit@8 (the table above gives both for the same cases, so the effect of k alone is visible); "
          "(2) the case pool, 24 early cases against the larger development set, which includes harder question families; "
          "(3) the corpus, 46 documents against the current build, where many more near-duplicate and period-confusable passages compete with the right one. "
          "The method is the same; the numbers are not comparable across those settings. This table is the like-for-like version.", ""]
    (out_dir / "SUMMARY.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    return result
