"""Offline, append-only E1b; see docs/experiments/chunk-size-300-400.md."""
from __future__ import annotations

import hashlib
import json
import statistics
import subprocess
from pathlib import Path

import numpy as np
import yaml

from labourlens import paths
from labourlens.retrieval import chunk as ck, evaluate as ev
from labourlens.retrieval.bm25_index import BM25Config

EXP = "dev-E1b-chunk-size"
NAMES = ("blocks", "merge120", "merge200", "fixed150", "merge300", "merge400")
OLD = {
    "merge120": ("f462aa03", "2a6288fef3d75546703fe8bd2b74337565f488e9a48c75a9134244259293b5a0"),
    "merge200": ("1b6eaa43", "4f3724fc92fca21a507e67441846e08c73420f885d493c413c8e812926dd0e13"),
}


def short_locators(row):
    """Saved case files keep at most six words of a heading locator (rights policy: quotes of at most six words)."""
    ranked = []
    for x in row["ranked"]:
        words = x["locator"].split()
        ranked.append({**x, "locator": x["locator"] if len(words) <= 6 else " ".join(words[:6]) + " …"})
    return {**row, "ranked": ranked}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def aggregate(rows: list[dict]) -> dict:
    n = len(rows)
    result = {"n_cases": n}
    for k in (1, 3, 5, 8, 10):
        result[f"hit@{k}"] = round(sum(0 < (r["first_relevant_rank"] or 99) <= k for r in rows) / n, 4)
    result["mrr"] = round(sum(1 / r["first_relevant_rank"] for r in rows if r["first_relevant_rank"]) / n, 4)
    result["passage_recall@5"] = round(statistics.mean(r["passage_recall@5"] for r in rows), 4)
    result["ctx_words@5"] = round(statistics.mean(sum(x["words"] for x in r["ranked"][:5]) for r in rows), 1)
    result["by_family_hit@8"] = {
        f: {"n": len(rs), "hit@8": round(sum(0 < (r["first_relevant_rank"] or 99) <= 8 for r in rs) / len(rs), 4)}
        for f in sorted({r["family"] for r in rows})
        for rs in [[r for r in rows if r["family"] == f]]
    }
    return result


def paired(base: list[dict], rows: list[dict]) -> dict:
    assert [r["case_id"] for r in base] == [r["case_id"] for r in rows]
    a = np.array([r["first_relevant_rank"] or 99 for r in base])
    b = np.array([r["first_relevant_rank"] or 99 for r in rows])
    delta = (b <= 8).astype(int) - (a <= 8).astype(int)
    rng = np.random.default_rng(20261110)
    means = delta[rng.integers(0, len(delta), size=(10000, len(delta)))].mean(axis=1)
    return {"rank_better": int((b < a).sum()), "rank_worse": int((b > a).sum()), "rank_same": int((b == a).sum()),
            "hit8_better": int((delta > 0).sum()), "hit8_worse": int((delta < 0).sum()), "hit8_same": int((delta == 0).sum()),
            "hit8_difference": round(float(delta.mean()), 4), "hit8_difference_bootstrap95": np.quantile(means, [0.025, 0.975]).round(4).tolist()}


def exclusive(path: Path, text: str) -> None:
    with path.open("x") as f:
        f.write(text)


def main() -> None:
    out = paths.EXPERIMENTS / "runs" / EXP
    summary_path = out.parent / f"{EXP}-SUMMARY.md"
    ev.refuse_existing([out, summary_path])
    snapshot_path = paths.EXPERIMENTS / "corpus-snapshots" / "v3.1.json"
    snapshot = json.loads(snapshot_path.read_text())
    for name, expected in snapshot["passage_file_sha256"].items():
        assert sha((paths.PASSAGES / name).read_bytes()) == expected, f"changed passage file: {name}"
    passages = ck.load_passages([Path(f).stem for f in snapshot["passage_file_sha256"]])
    assert len(passages) == snapshot["passages"]
    cases = ev.text_cases(ev.load_cases("dev"))
    assert cases
    old_rows = [json.loads(x) for x in (out.parent / "dev-E1-chunking" / "merge120.cases.jsonl").read_text().splitlines() if x.strip()]
    original_ids = {r["case_id"] for r in old_rows}
    assert original_ids <= {c["case_id"] for c in ev.load_cases("dev")}
    subset_ids = original_ids & {c["case_id"] for c in cases}
    excluded = sorted(original_ids - subset_ids)
    gold_ids = set().union(*(ev.gold_passages(c) for c in cases))
    words = {p["passage_id"]: len(p["text"].split()) for p in passages}
    assert gold_ids <= words.keys()
    prices = yaml.safe_load((paths.ROOT / "specs" / "prices.yaml").read_text())
    provenance = {"commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                  "gold_file": "experiments/gold/draft_cases.jsonl", "gold_sha256": sha((ev.GOLD / "draft_cases.jsonl").read_bytes()),
                  "snapshot_sha256": sha(snapshot_path.read_bytes()), "corpus_version": "v3.1", "passage_files_verified": len(snapshot["passage_file_sha256"]),
                  "passages": len(passages), "case_ids": [c["case_id"] for c in cases], "secondary_case_ids": sorted(subset_ids),
                  "original_E1_case_ids": sorted(original_ids), "secondary_excluded_no_current_text_gold": excluded,
                  "bootstrap_seed": 20261110, "bootstrap_resamples": 10000, "gold_unique_passages": len(gold_ids)}
    results = {}
    for name in NAMES:
        cfg = ck.CONFIGS[name]
        chunks = ck.build_chunks(cfg, passages)
        ids_sha = sha("\n".join(c.chunk_id for c in chunks).encode())
        if name in OLD:
            assert (cfg.config_hash(), ids_sha) == OLD[name], f"old chunk identity changed: {name}"
        if name == "merge200":
            assert ck.corpus_hash(chunks) == snapshot["chunk_corpus_sha256"]
        first = ev.run_config(cfg, BM25Config(), cases, passages)
        second = ev.run_config(cfg, BM25Config(), cases, passages)
        assert first["rows"] == second["rows"], f"nondeterministic rows: {name}"
        without_time = lambda r: {k: v for k, v in r["metrics"].items() if k != "latency_ms_p50"}
        assert without_time(first) == without_time(second), f"nondeterministic metrics: {name}"
        m = first["metrics"]
        m.update(aggregate(first["rows"]))
        total_words = sum(c.word_count for c in chunks)
        easier = {pid for c in chunks for pid in c.source_passage_ids if pid in gold_ids and c.word_count >= 4 * max(1, words[pid])}
        m.update({"mean_chunk_words": round(total_words / len(chunks), 2), "total_chunk_words": total_words,
                  "chunk_config_hash": cfg.config_hash(), "chunk_ids_sha256": ids_sha,
                  "gold_passages_in_at_least_4x_chunk": len(easier), "deterministic_rebuild": True})
        if name in ("merge300", "merge400"):
            tokens = round(total_words * 1.33)
            m["estimated_fresh_embedding"] = {"tokens": tokens, "assumption_tokens_per_word": 1.33,
                "usd_by_model": {model: round(tokens * rate["input"] / 1e6, 6) for model, rate in prices["embedding"].items()}}
            # Scenario only: 30 average-size chunks per case, excluding prompt/metadata/output overhead.
            rerank_tokens = round(len(cases) * 30 * total_words / len(chunks) * 1.33)
            m["estimated_R3_candidate_text_only"] = {"tokens": rerank_tokens, "model": "gpt-6-luna", "input_usd": round(rerank_tokens * prices["chat"]["gpt-6-luna"]["input"] / 1e6, 6)}
        first["secondary"] = aggregate([r for r in first["rows"] if r["case_id"] in subset_ids])
        results[name] = first
    for name, result in results.items():
        for baseline in ("merge200", "merge120"):
            result["metrics"][f"paired_vs_{baseline}"] = paired(results[baseline]["rows"], result["rows"])
            result["secondary"][f"paired_vs_{baseline}"] = paired([r for r in results[baseline]["rows"] if r["case_id"] in subset_ids], [r for r in result["rows"] if r["case_id"] in subset_ids])
    # Deterministically choose first case with all four relevant chunks and at least one rank change.
    examples = []
    for i, case in enumerate(cases):
        rs = {n: results[n]["rows"][i] for n in ("merge120", "merge200", "merge300", "merge400")}
        if all(r["first_relevant_rank"] for r in rs.values()) and len({r["first_relevant_rank"] for r in rs.values()}) > 1:
            examples.append({"case_id": case["case_id"], "selection": "first input case with top10 relevance for all four and differing ranks", "configs": {n: {"rank": r["first_relevant_rank"], **r["ranked"][r["first_relevant_rank"] - 1]} for n, r in rs.items()}})
            break
    provenance["worked_example"] = examples
    lines = ["# E1b chunk-size BM25 (MEASURED, dev only)", "", f"Primary n={len(cases)}; secondary eligible original E1 id subset n={len(subset_ids)} of {len(original_ids)}, using current gold and v3.1 corpus, not historical scores. Excluded ids with no current answerable text gold: {excluded}. DEV-034 is now abstain with no evidence_text; no fabricated relevance or miss is assigned.", "", "Paired columns = first-relevant-rank better/worse/same; missing top10 = rank 99. Intervals = paired hit@8 difference, 10,000 case bootstrap samples, seed 20261110.", ""]
    for subset in (False, True):
        lines += ["## " + ("Secondary original E1 case-id subset" if subset else "Primary current dev text cases"), "", "| config | chunks | mean words | hit@1 | @3 | @5 | @8 | @10 | MRR | passage recall@5 | ctx words@5 | vs merge200 B/W/S | vs merge120 B/W/S | hit@8 delta vs 200 [95% CI] |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|"]
        for name, r in results.items():
            m = r["secondary"] if subset else r["metrics"]
            p, q = (m[f"paired_vs_{b}"] for b in ("merge200", "merge120"))
            counts = lambda x: "/".join(str(x[f"rank_{k}"]) for k in ("better", "worse", "same"))
            vals = [name, r["metrics"]["n_chunks"], r["metrics"]["mean_chunk_words"], *(m[f"hit@{k}"] for k in (1, 3, 5, 8, 10)), m["mrr"], m["passage_recall@5"], m["ctx_words@5"], counts(p), counts(q), f"{p['hit8_difference']} {p['hit8_difference_bootstrap95']}"]
            lines.append("| " + " | ".join(map(str, vals)) + " |")
        lines.append("")
    lines += ["## Family hit@8 (primary)", "", "| family | n | " + " | ".join(NAMES) + " |", "|---|---:|" + "---:|" * len(NAMES)]
    for family, f in results["merge200"]["metrics"]["by_family_hit@8"].items():
        lines.append("| " + " | ".join(map(str, [family, f["n"], *(results[n]["metrics"]["by_family_hit@8"][family]["hit@8"] for n in NAMES)])) + " |")
    lines += ["", "## Worked example (no passage text)", "", "```json", json.dumps(examples, indent=2), "```", "", "## Provenance and cost estimates", "", "Full provenance: `dev-E1b-chunk-size/provenance.json`; per-config metrics include identities, deterministic rebuild, easier-target counts, token/cost estimates and both paired comparisons. Cost assumptions: 1.33 tokens/word; cached specs/prices.yaml, not live-verified. Fresh embedding estimate includes all chunk words (including overlap); no cache reuse assumed. R3 scenario uses 30 corpus-average chunks × n cases and gpt-6-luna input price; excludes metadata, prompt, query embeddings, output/reasoning and generation, so is not an all-in forecast. No paid calls ran.", ""]
    out.mkdir(parents=True, exist_ok=False)
    exclusive(out / "provenance.json", json.dumps(provenance, indent=2) + "\n")
    for name, r in results.items():
        exclusive(out / f"{name}.metrics.json", json.dumps({"label": name, "config": r["config"], "metrics": r["metrics"], "secondary": r["secondary"]}, indent=2) + "\n")
        exclusive(out / f"{name}.cases.jsonl", "\n".join(json.dumps(short_locators(row)) for row in r["rows"]) + "\n")
    exclusive(summary_path, "\n".join(lines) + "\n")
    print("\n".join(lines))
    print("PASS: six configs rebuilt twice; identical rows and all non-timing metrics; old config/chunk ids unchanged; v3.1 files and merge200 corpus fingerprint verified.")


if __name__ == "__main__":
    main()
