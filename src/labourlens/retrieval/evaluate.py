"""Retrieval evaluation against gold evidence labelled at the passage level (D-017).

A retrieved chunk is relevant if any of its `source_passage_ids` is in the case's gold passage set. That makes
chunk variants comparable: a 150-word chunk and a single block are both scored by the same labelled evidence.
Because bigger chunks cover more passages (an easier target) every run also reports how many words a reader or
model would receive, so the cost of that advantage is visible.

Metrics (answerable text-evidence cases only):
  hit@k      share of cases with at least one relevant chunk in the top k
  mrr        mean reciprocal rank of the first relevant chunk (0 if none in the top 10)
  passage_recall@5  share of the case's gold passages covered by the top 5 chunks (strict: gold lists often include the
                    same fact from several sources, so this is lower than hit@5 even for good retrieval)
  ctx_words@5  mean words in the top 5 chunks
  page_hit@5/10  LENIENT secondary: a chunk also counts if it covers a PDF page that holds a gold passage (HTML
                 sections still need a passage match). Shown because passage-level labels can miss a neighbouring
                 block on the same page; it is not the headline metric.
  latency_ms_p50 median query time
"""

from __future__ import annotations

import json
import statistics
import time
from dataclasses import asdict
from pathlib import Path

from labourlens import paths
from labourlens.retrieval import chunk as ck
from labourlens.retrieval.bm25_index import BM25Config, BM25Index

GOLD = paths.EXPERIMENTS / "gold"
TOP = 10


def load_cases(split: str, path: Path | None = None) -> list[dict]:
    f = path or GOLD / "draft_cases.jsonl"
    cases = [json.loads(line) for line in f.read_text().splitlines() if line.strip()]
    return [c for c in cases if c["split"] == split]


def text_cases(cases: list[dict]) -> list[dict]:
    return [c for c in cases if c["expected_behavior"] in ("answer", "ignore_injection_and_answer") and c.get("evidence_text")]


def gold_passages(case: dict) -> set[str]:
    return {pid for e in case["evidence_text"] for pid in e["passage_ids"]}


def run_config(chunk_cfg: ck.ChunkConfig, bm_cfg: BM25Config, cases: list[dict], passages: list[dict],
               retriever=None, retriever_label: str = "bm25") -> dict:
    """retriever: optional callable(chunks) -> object with .search(query, k); default is BM25 with bm_cfg."""
    chunks = ck.build_chunks(chunk_cfg, passages)
    by_id = {c.chunk_id: c for c in chunks}
    page_of = {p["passage_id"]: (p["source_id"], p["page_number"]) for p in passages}
    idx = retriever(chunks) if retriever else BM25Index.build(chunks, bm_cfg)
    rows, lat = [], []
    for case in cases:
        gold = gold_passages(case)
        t0 = time.perf_counter()
        hits = idx.search(case["question"], TOP)
        lat.append((time.perf_counter() - t0) * 1000)
        rels = [int(bool(gold & set(by_id[cid].source_passage_ids))) for cid, _ in hits]
        gold_pages = {page_of[g] for g in gold if page_of[g][1] is not None}

        def page_rel(cid: str) -> int:
            c = by_id[cid]
            if gold & set(c.source_passage_ids):
                return 1
            return int(c.page_start is not None and any(s_ == c.source_id and c.page_start <= pg <= c.page_end for s_, pg in gold_pages))

        prels = [page_rel(cid) for cid, _ in hits]
        first_page = next((i + 1 for i, r in enumerate(prels) if r), None)
        first = next((i + 1 for i, r in enumerate(rels) if r), None)
        rows.append({
            "case_id": case["case_id"], "family": case["family"], "n_gold_passages": len(gold), "first_relevant_rank": first, "first_page_rank": first_page,
            "ranked": [{"chunk_id": cid, "score": round(s, 4), "relevant": r, "words": by_id[cid].word_count, "source_id": by_id[cid].source_id,
                        "locator": by_id[cid].locator} for (cid, s), r in zip(hits, rels)],
            "passage_recall@5": len(gold & {p for cid, _ in hits[:5] for p in by_id[cid].source_passage_ids}) / len(gold),
        })
    n = len(rows)

    def hit(k: int) -> float:
        return sum(1 for r in rows if r["first_relevant_rank"] and r["first_relevant_rank"] <= k) / n

    metrics = {
        "n_cases": n, "n_chunks": len(chunks), "corpus_hash": ck.corpus_hash(chunks),
        "hit@1": round(hit(1), 4), "hit@3": round(hit(3), 4), "hit@5": round(hit(5), 4), "hit@10": round(hit(10), 4),
        "page_hit@5": round(sum(1 for r in rows if r["first_page_rank"] and r["first_page_rank"] <= 5) / n, 4),
        "page_hit@10": round(sum(1 for r in rows if r["first_page_rank"] and r["first_page_rank"] <= 10) / n, 4),
        "mrr": round(sum(1 / r["first_relevant_rank"] for r in rows if r["first_relevant_rank"]) / n, 4),
        "passage_recall@5": round(statistics.mean(r["passage_recall@5"] for r in rows), 4),
        "ctx_words@5": round(statistics.mean(sum(x["words"] for x in r["ranked"][:5]) for r in rows), 1),
        "latency_ms_p50": round(statistics.median(lat), 3),
    }
    fam: dict[str, list[dict]] = {}
    for r in rows:
        fam.setdefault(r["family"], []).append(r)
    metrics["by_family_hit@5"] = {f: {"n": len(v), "hit@5": round(sum(1 for r in v if r["first_relevant_rank"] and r["first_relevant_rank"] <= 5) / len(v), 3)} for f, v in sorted(fam.items())}
    return {"config": {"chunk": asdict(chunk_cfg), "bm25": asdict(bm_cfg), "retriever": retriever_label}, "metrics": metrics, "rows": rows}


def write_run(exp_id: str, label: str, result: dict) -> Path:
    d = paths.EXPERIMENTS / "runs" / exp_id
    d.mkdir(parents=True, exist_ok=True)
    stem = label.replace("/", "_")
    (d / f"{stem}.metrics.json").write_text(json.dumps({"label": label, "config": result["config"], "metrics": result["metrics"]}, indent=1, default=str))
    (d / f"{stem}.cases.jsonl").write_text("\n".join(json.dumps(r) for r in result["rows"]) + "\n")
    return d
