"""Chunking variants for the retrieval experiments (D-015, D-016).

Input: extracted passages (layout blocks). Output: chunks that always carry `source_passage_ids`, so any
chunking variant can be scored against evidence labelled at the passage level (D-017) and any citation
traces back to blocks, pages and text hashes.

Variants (ChunkConfig.mode):
  blocks  every eligible passage is its own chunk (the unmodified baseline)
  merge   adjacent eligible passages under the same section heading are merged to about `target_words`,
          with whole-passage overlap of about `overlap_words`; never crosses a source or a heading
  fixed   layout-blind sliding windows of `target_words` over the concatenated eligible text of one
          document, stride = target_words - overlap_words

Eligibility: only passages whose quality_flag is in `include_flags` (default: ok). Table-like and garbled
blocks are kept in the passage store but are not retrieved by default; including tables is itself a factor
that can be tested.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from labourlens import paths
from labourlens.models import sha256_hex, stable_id


@dataclass(frozen=True)
class ChunkConfig:
    name: str
    mode: str  # blocks | merge | fixed
    target_words: int = 0
    overlap_words: int = 0
    include_flags: tuple[str, ...] = ("ok",)

    def config_hash(self) -> str:
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()[:8]


CONFIGS = {
    "blocks": ChunkConfig("blocks", "blocks"),
    "merge120": ChunkConfig("merge120", "merge", 120, 30),
    "merge200": ChunkConfig("merge200", "merge", 200, 40),
    "fixed150": ChunkConfig("fixed150", "fixed", 150, 30),
    "merge300": ChunkConfig("merge300", "merge", 300, 60),
    "merge400": ChunkConfig("merge400", "merge", 400, 80),
}


class Chunk(BaseModel):
    model_config = ConfigDict(frozen=True)
    chunk_id: str
    chunk_config: str
    source_id: str
    snapshot_id: str
    original_url: str
    document_title: str
    publication_date: str | None
    release_stage: str
    page_start: int | None
    page_end: int | None
    section_heading: str
    locator: str
    text: str
    word_count: int
    text_sha256: str
    source_passage_ids: list[str]
    rights_status: str


def load_passages(source_ids: list[str] | None = None) -> list[dict]:
    out: list[dict] = []
    for f in sorted(paths.PASSAGES.glob("*.jsonl")):
        if source_ids and f.stem not in source_ids:
            continue
        out += [json.loads(line) for line in f.read_text().splitlines() if line.strip()]
    return out


def _wc(t: str) -> int:
    return len(t.split())


def _locator(ps: list[dict]) -> tuple[int | None, int | None, str]:
    pages = [p["page_number"] for p in ps if p["page_number"] is not None]
    if pages:
        lo, hi = min(pages), max(pages)
        return lo, hi, f"p.{lo}" if lo == hi else f"pp.{lo}-{hi}"
    return None, None, ps[0]["locator"] if len(ps) == 1 else f"{ps[0]['locator']} to {ps[-1]['locator']}"


def _make(cfg: ChunkConfig, idx: int, ps: list[dict], text: str | None = None) -> Chunk:
    text = text if text is not None else "\n".join(p["text"] for p in ps)
    lo, hi, loc = _locator(ps)
    first = ps[0]
    return Chunk(
        chunk_id=stable_id(cfg.name, cfg.config_hash(), first["source_id"], ps[0]["passage_id"], ps[-1]["passage_id"], idx),
        chunk_config=cfg.name, source_id=first["source_id"], snapshot_id=first["snapshot_id"], original_url=first["original_url"],
        document_title=first["document_title"], publication_date=first["publication_date"], release_stage=first["release_stage"],
        page_start=lo, page_end=hi, section_heading=first.get("section_heading", ""), locator=loc, text=text, word_count=_wc(text),
        text_sha256=sha256_hex(text.encode()), source_passage_ids=[p["passage_id"] for p in ps], rights_status=first["rights_status"],
    )


def _merge_group(cfg: ChunkConfig, group: list[dict], start_idx: int) -> list[Chunk]:
    chunks: list[Chunk] = []
    i = 0
    while i < len(group):
        cur: list[dict] = []
        words = 0
        j = i
        while j < len(group) and (not cur or words + _wc(group[j]["text"]) <= cfg.target_words * 1.25):
            cur.append(group[j])
            words += _wc(group[j]["text"])
            j += 1
            if words >= cfg.target_words:
                break
        if j >= len(group) and chunks and words < cfg.target_words / 4:
            # short tail: fold into the previous chunk instead of emitting a thin fragment
            prev = chunks.pop()
            ps = [*[p for p in group if p["passage_id"] in set(prev.source_passage_ids)], *cur]
            seen: set[str] = set()
            ps = [p for p in ps if not (p["passage_id"] in seen or seen.add(p["passage_id"]))]
            chunks.append(_make(cfg, start_idx + len(chunks), ps))
            break
        chunks.append(_make(cfg, start_idx + len(chunks), cur))
        if j >= len(group):
            break
        back, ow = j, 0  # step back whole passages until the overlap budget is used, always advancing at least one
        while back > i + 1 and ow + _wc(group[back - 1]["text"]) <= cfg.overlap_words:
            back -= 1
            ow += _wc(group[back]["text"])
        i = back
    return chunks


def build_chunks(cfg: ChunkConfig, passages: list[dict]) -> list[Chunk]:
    elig = [p for p in passages if p["quality_flag"] in cfg.include_flags]
    by_src: dict[str, list[dict]] = {}
    for p in elig:
        by_src.setdefault(p["source_id"], []).append(p)
    chunks: list[Chunk] = []
    for sid in sorted(by_src):
        ps = by_src[sid]
        if cfg.mode == "blocks":
            chunks += [_make(cfg, i, [p]) for i, p in enumerate(ps)]
        elif cfg.mode == "merge":
            groups: list[list[dict]] = []
            for p in ps:
                if groups and groups[-1][0].get("section_heading", "") == p.get("section_heading", ""):
                    groups[-1].append(p)
                else:
                    groups.append([p])
            n = 0
            for g in groups:
                got = _merge_group(cfg, g, n)
                n += len(got)
                chunks += got
        elif cfg.mode == "fixed":
            words: list[tuple[str, int]] = [(w, pi) for pi, p in enumerate(ps) for w in p["text"].split()]
            stride = max(1, cfg.target_words - cfg.overlap_words)
            n = 0
            for s in range(0, len(words), stride):
                win = words[s : s + cfg.target_words]
                if len(win) < cfg.target_words / 4 and n:
                    break
                used = sorted({pi for _, pi in win})
                chunks.append(_make(cfg, n, [ps[k] for k in used], text=" ".join(w for w, _ in win)))
                n += 1
                if s + cfg.target_words >= len(words):
                    break
        else:
            raise ValueError(f"unknown chunk mode {cfg.mode}")
    return chunks


def corpus_hash(chunks: list[Chunk]) -> str:
    h = hashlib.sha256()
    for c in sorted(chunks, key=lambda c: c.chunk_id):
        h.update(f"{c.chunk_id}:{c.text_sha256}\n".encode())
    return h.hexdigest()


def save_chunks(cfg: ChunkConfig, chunks: list[Chunk]) -> Path:
    d = paths.INDEX / "chunks"
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{cfg.name}-{cfg.config_hash()}.jsonl"
    f.write_text("\n".join(c.model_dump_json() for c in chunks) + "\n")
    return f
