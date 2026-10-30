"""Build the evidence context shown to the model. Each source passage gets a short label (P1, P2, ...) so the model
cites passages, not chunks (D-017, D-024). Passage text is untrusted data: it is wrapped, labelled, and the system
prompt says never to follow instructions found inside it."""

from __future__ import annotations

from dataclasses import dataclass
from xml.sax.saxutils import escape, quoteattr

from labourlens.retrieval.chunk import Chunk


@dataclass(frozen=True)
class ContextPassage:
    label: str
    passage_id: str
    source_id: str
    title: str
    published: str | None
    stage: str
    locator: str
    text: str
    flags: tuple[str, ...] = ()  # injection heuristics that matched this item's text; flagged items must not be cited


def build_context(chunks: list[Chunk], passages_by_id: dict[str, dict], first_ids: list[str] | None = None) -> list[ContextPassage]:
    """Passages of the retrieved chunks in rank order, de-duplicated by passage id. `first_ids` puts given passages first
    (used only by the oracle-evidence experiment, which isolates generation from retrieval)."""
    order = list(first_ids or []) + [pid for c in chunks for pid in c.source_passage_ids]
    out: list[ContextPassage] = []
    seen: set[str] = set()
    for pid in order:
        if pid in seen or pid not in passages_by_id:
            continue
        seen.add(pid)
        p = passages_by_id[pid]
        out.append(ContextPassage(f"P{len(out) + 1}", pid, p["source_id"], p["document_title"], p["publication_date"],
                                  p["release_stage"], p["locator"], p["text"]))
    return out


def render(ctx: list[ContextPassage]) -> str:
    blocks = []
    for p in ctx:
        attrs = (f"label={quoteattr(p.label)} source={quoteattr(p.source_id)} title={quoteattr(p.title)} "
                 f"published={quoteattr(p.published or 'unknown')} stage={quoteattr(p.stage)} locator={quoteattr(p.locator)}")
        if p.flags:
            attrs += f" flagged={quoteattr(','.join(p.flags))}"
        blocks.append(f"<passage {attrs}>\n{escape(p.text)}\n</passage>")
    return "\n".join(blocks)
