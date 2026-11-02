"""Dense and hybrid retrieval experiments (D-016, D-021, D-022). One factor at a time, dev split only.

E5 embedding model (dense only, merge120 chunks, plain chunk text)
E6 retrieval mode on the E5 winner: BM25 vs dense vs hybrid (RRF), on merge120 and merge200
E7 embedded-text header (document title and section heading) on/off, on the E5 winner, dense only, merge120
The E5 winner is chosen by MRR on dev, then hit@10; this is tuning on dev, which is allowed. Held-out is untouched.
"""

from __future__ import annotations

import json
import statistics

from labourlens import paths
from labourlens.retrieval import chunk as ck
from labourlens.retrieval import dense as dn
from labourlens.retrieval import evaluate as ev
from labourlens.retrieval.bm25_index import BM25Config, BM25Index

MODELS = ("text-embedding-3-small", "text-embedding-3-large", "text-embedding-ada-002")
BASE_CHUNK = ck.CONFIGS["merge120"]
BM = BM25Config()
COLS = "| config | hit@1 | hit@3 | hit@5 | hit@10 | page_hit@5 (lenient) | MRR | passage_recall@5 | ctx words@5 | chunks | p50 ms | vs BM25 baseline (rank of first relevant) |\n|---|---|---|---|---|---|---|---|---|---|---|---|"


def _paired(base_rows: list[dict], rows: list[dict]) -> str:
    better = worse = 0
    for a, b in zip(base_rows, rows):
        ra, rb = a["first_relevant_rank"] or 99, b["first_relevant_rank"] or 99
        better += rb < ra
        worse += rb > ra
    return f"{better} better / {worse} worse / {len(rows) - better - worse} same"


def _row(label: str, r: dict, base: dict) -> str:
    m = r["metrics"]
    return (f"| {label} | {m['hit@1']} | {m['hit@3']} | {m['hit@5']} | {m['hit@10']} | {m['page_hit@5']} | {m['mrr']} | {m['passage_recall@5']} "
            f"| {m['ctx_words@5']} | {m['n_chunks']} | {m['latency_ms_p50']} | {_paired(base['rows'], r['rows'])} |")


def _query_api_ms(model: str) -> str:
    f = paths.INDEX / "embeddings" / model / "usage.jsonl"
    rows = [json.loads(x) for x in f.read_text().splitlines()] if f.exists() else []
    q = [r["seconds"] * 1000 for r in rows if r["purpose"] == "queries"]
    return f"{statistics.median(q):.0f} ms median over {len(q)} uncached query calls" if q else "no uncached query calls recorded"


def run(split: str = "dev", force: bool = False) -> None:
    root = paths.EXPERIMENTS / "runs"
    # E7's exact labels depend on the measured E5 winner. Guard every E5–E7
    # metrics/cases file before any embedding work, including partial runs.
    ev.refuse_existing([root / f"{split}-dense-SUMMARY.md", root / f"{split}-dense-summary.json"]
                       + [p for exp in ("E5", "E6", "E7") for suffix in ("metrics.json", "cases.jsonl")
                          for p in (root / f"{split}-dense-{exp}").glob(f"*.{suffix}")], force)
    passages = ck.load_passages()
    cases = ev.text_cases(ev.load_cases(split))
    if not cases:
        raise SystemExit(f"no text-evidence cases in split {split}")
    base = ev.run_config(BASE_CHUNK, BM, cases, passages)
    exp = f"{split}-dense"
    out = [f"# Dense and hybrid retrieval experiments, split `{split}` (n={len(cases)} text-evidence cases)", "",
           "Gold labels are AI drafts, not human-reviewed. Dev tuning only. Paired column compares with the BM25 baseline (merge120, default settings).", ""]
    results: dict[str, dict] = {}

    # E5
    out += ["## E5-embedding-model (dense only, merge120)", "", COLS, _row("bm25 baseline", base, base)]
    ev.write_run(f"{exp}-E5", "bm25_baseline", base, force=force)
    e5 = {}
    for model in MODELS:
        r = ev.run_config(BASE_CHUNK, BM, cases, passages, lambda ch, m=model: dn.DenseIndex(ch, dn.DenseConfig(m)), f"dense:{model}")
        e5[model] = r
        ev.write_run(f"{exp}-E5", model, r, force=force)
        out.append(_row(model, r, base))
        results[f"E5/{model}"] = r["metrics"]
    winner = max(MODELS, key=lambda m: (e5[m]["metrics"]["mrr"], e5[m]["metrics"]["hit@10"]))
    out += ["", f"Winner on dev by MRR then hit@10: `{winner}`.", ""]

    # E6
    out += [f"## E6-retrieval-mode (embedding `{winner}`)", "", COLS]
    for cname in ("merge120", "merge200"):
        cc = ck.CONFIGS[cname]
        cfg = dn.DenseConfig(winner)
        runs = {
            f"{cname} bm25": ev.run_config(cc, BM, cases, passages),
            f"{cname} dense": ev.run_config(cc, BM, cases, passages, lambda ch: dn.DenseIndex(ch, cfg), f"dense:{cfg.key()}"),
            f"{cname} hybrid-rrf": ev.run_config(cc, BM, cases, passages,
                                                 lambda ch: dn.HybridIndex(BM25Index.build(ch, BM), dn.DenseIndex(ch, cfg)), f"hybrid-rrf:{cfg.key()}"),
        }
        for label, r in runs.items():
            ev.write_run(f"{exp}-E6", label, r, force=force)
            out.append(_row(label, r, base))
            results[f"E6/{label}"] = r["metrics"]
    out.append("")

    # E7
    out += [f"## E7-embedded-text-header (dense only, `{winner}`, merge120)", "", COLS]
    for hdr in (False, True):
        cfg = dn.DenseConfig(winner, header=hdr)
        r = ev.run_config(BASE_CHUNK, BM, cases, passages, lambda ch, c=cfg: dn.DenseIndex(ch, c), f"dense:{cfg.key()}")
        ev.write_run(f"{exp}-E7", cfg.key(), r, force=force)
        out.append(_row(f"header={'on' if hdr else 'off'}", r, base))
        results[f"E7/header={hdr}"] = r["metrics"]
    out.append("")

    # cost and latency, measured
    out += ["## Measured API usage (from `usage.jsonl`; tokens are as reported by the API)", "", "| model | calls | inputs | tokens | query embedding latency |", "|---|---|---|---|---|"]
    for m in MODELS:
        u = dn.usage_totals(m)
        out.append(f"| {m} | {u['calls']} | {u['inputs']} | {u['tokens']} | {_query_api_ms(m)} |")
    out.append("")
    text = "\n".join(out) + "\n"
    (paths.EXPERIMENTS / "runs" / f"{exp}-SUMMARY.md").write_text(text)
    (paths.EXPERIMENTS / "runs" / f"{exp}-summary.json").write_text(json.dumps(results, indent=1))
    print(text)
