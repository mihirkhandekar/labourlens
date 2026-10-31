"""Corpus fingerprints: content hashes of the built passages, observations and chunks (no publisher text is stored).

Used to prove that adding sources is additive: every source that existed in an earlier fingerprint must keep byte-identical passage files
and identical per-source observation hashes. Reads local build outputs only; no network, no model calls, no writes.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from labourlens import paths


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def passage_file_hashes(root: Path | None = None) -> dict[str, str]:
    d = root or paths.PASSAGES
    return {f.name: _sha(f.read_bytes()) for f in sorted(d.glob("*.jsonl"))}


def observation_hashes(obs: pd.DataFrame | None = None) -> dict[str, dict]:
    """Per source: row count and a hash over its sorted (observation_id, period, raw_value) lines."""
    if obs is None:
        obs = pd.read_parquet(paths.PROCESSED / "observations.parquet")
    out: dict[str, dict] = {}
    for sid, g in obs.groupby("source_id"):
        lines = sorted(f"{r.observation_id}|{r.period}|{r.raw_value}" for r in g.itertuples())
        out[str(sid)] = {"rows": len(g), "sha256": _sha("\n".join(lines).encode())}
    return out


def fingerprint(label: str, gold_path: Path | None = None) -> dict:
    from labourlens.retrieval import chunk as ck

    passages = ck.load_passages()
    chunks = ck.build_chunks(ck.CONFIGS["merge200"], passages)
    files = passage_file_hashes()
    gold = gold_path or paths.EXPERIMENTS / "gold" / "draft_cases.jsonl"
    return {
        "label": label,
        "gold_sha256": _sha(gold.read_bytes()),
        "document_files": len(files),
        "passages": len(passages),
        "passage_file_sha256": files,
        "manifest_sha256": _sha((paths.MANIFESTS / "manifest.json").read_bytes()),
        "observations": observation_hashes(),
        "chunk_config": "merge200",
        "chunks": len(chunks),
        "chunk_corpus_sha256": ck.corpus_hash(chunks),
    }


def write(label: str, out: Path | None = None) -> Path:
    out = out or paths.EXPERIMENTS / "corpus-snapshots" / f"{label}.json"
    out.write_text(json.dumps(fingerprint(label), indent=2) + "\n")
    return out
