"""One-factor-at-a-time BM25 experiments (D-016). Baseline: merge120, stopwords on, period normalisation on,
no stemming, k1=1.5, b=0.75. Each experiment changes ONE factor. Raw per-case outputs are written under
experiments/runs/<exp_id>/. Tuning uses the dev split only; the held-out split is run once, after freeze.
"""

from __future__ import annotations

import json
from dataclasses import replace

from labourlens import paths
from labourlens.retrieval import chunk as ck
from labourlens.retrieval import evaluate as ev
from labourlens.retrieval.bm25_index import BM25Config
from labourlens.retrieval.tokenize import TokConfig

BASE_CHUNK = ck.CONFIGS["merge120"]
BASE_BM = BM25Config()


def grid() -> dict[str, list[tuple[str, ck.ChunkConfig, BM25Config]]]:
    t = BASE_BM.tok
    return {
        "E1-chunking": [(n, ck.CONFIGS[n], BASE_BM) for n in ("blocks", "merge120", "merge200", "fixed150")]
        + [("merge120+tables", replace(BASE_CHUNK, name="merge120t", include_flags=("ok", "table_unreliable")), BASE_BM)],
        "E2-tokenisation": [
            ("baseline", BASE_CHUNK, BASE_BM),
            ("stem_on", BASE_CHUNK, replace(BASE_BM, tok=replace(t, stem=True))),
            ("stopwords_off", BASE_CHUNK, replace(BASE_BM, tok=replace(t, stopwords=False))),
            ("period_norm_off", BASE_CHUNK, replace(BASE_BM, tok=replace(t, period_normalise=False))),
        ],
        "E4-combined": [("merge200+stopwords_off", ck.CONFIGS["merge200"], replace(BASE_BM, tok=replace(t, stopwords=False))),
                        ("merge200+stopwords_off+b=0.4", ck.CONFIGS["merge200"], replace(BASE_BM, b=0.4, tok=replace(t, stopwords=False)))],
        "E3-bm25-params": [(f"k1={k}", BASE_CHUNK, replace(BASE_BM, k1=k)) for k in (0.9, 1.2, 1.5, 2.0)]
        + [(f"b={b}", BASE_CHUNK, replace(BASE_BM, b=b)) for b in (0.4, 0.75, 0.9)],
    }


def _paired(base_rows: list[dict], rows: list[dict]) -> str:
    better = worse = 0
    for a, b in zip(base_rows, rows):
        ra, rb = a["first_relevant_rank"] or 99, b["first_relevant_rank"] or 99
        better += rb < ra
        worse += rb > ra
    return f"{better} better / {worse} worse / {len(rows) - better - worse} same"


def run(split: str = "dev") -> None:
    passages = ck.load_passages()
    cases = ev.text_cases(ev.load_cases(split))
    if not cases:
        raise SystemExit(f"no text-evidence cases in split {split}; gold set missing?")
    results = {}
    base = ev.run_config(BASE_CHUNK, BASE_BM, cases, passages)
    summary = [f"# Retrieval experiments, split `{split}` (n={len(cases)} text-evidence cases)", "",
               "Gold: `experiments/gold/draft_cases.jsonl` (DRAFT, not yet human-reviewed). Baseline: merge120, stopwords on, "
               "period normalisation on, no stemming, k1=1.5, b=0.75. Differences on this few cases are small-sample; read the paired column.", ""]
    for exp, items in grid().items():
        summary += [f"## {exp}", "", "| config | hit@1 | hit@3 | hit@5 | hit@10 | page_hit@5 (lenient) | MRR | passage_recall@5 | ctx words@5 | chunks | p50 ms | vs baseline (rank of first relevant) |",
                    "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for label, cc, bc in items:
            r = base if (cc == BASE_CHUNK and bc == BASE_BM) else ev.run_config(cc, bc, cases, passages)
            ev.write_run(f"{split}-{exp}", label, r)
            m = r["metrics"]
            results[f"{exp}/{label}"] = m
            summary.append(f"| {label} | {m['hit@1']} | {m['hit@3']} | {m['hit@5']} | {m['hit@10']} | {m['page_hit@5']} | {m['mrr']} | {m['passage_recall@5']} | {m['ctx_words@5']} | {m['n_chunks']} | {m['latency_ms_p50']} | {_paired(base['rows'], r['rows'])} |")
        summary.append("")
    out = paths.EXPERIMENTS / "runs" / f"{split}-SUMMARY.md"
    out.write_text("\n".join(summary) + "\n")
    (paths.EXPERIMENTS / "runs" / f"{split}-summary.json").write_text(json.dumps(results, indent=1))
    print("\n".join(summary))
