"""Listwise LLM rerank of retrieval candidates (experiment R2, D-029). One call per query, strict structured output of
passage labels, deterministic validation, fallback to the incoming order on any failure. Candidate text is untrusted data:
XML-escaped, labelled, and the prompt says to ignore instructions inside it (same pattern as the answer step)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from xml.sax.saxutils import escape, quoteattr

from labourlens import paths, prices
from labourlens.answer import llm
from labourlens.retrieval.chunk import Chunk

MODEL = "gpt-6-luna"
POOL = 30
KEEP = 10
PROMPT_FILE = paths.ROOT / "prompts" / "rerank_v1.md"
CACHE_DIR = paths.ROOT / "data" / "runs" / "dev-R2" / "cache"  # raw responses; gitignored


def load_prompt() -> tuple[str, str, str]:
    system, user = PROMPT_FILE.read_text().split("<!-- user -->\n")
    return system.strip(), user, hashlib.sha256((system + user).encode()).hexdigest()[:12]


def label_of(i: int) -> str:
    return f"C{i + 1}"


def render(chunks: list[Chunk]) -> str:
    out = []
    for i, c in enumerate(chunks):
        attrs = (f"label={quoteattr(label_of(i))} source={quoteattr(c.source_id)} title={quoteattr(c.document_title)} "
                 f"published={quoteattr(c.publication_date or 'unknown')} stage={quoteattr(c.release_stage)} locator={quoteattr(c.locator)}")
        out.append(f"<passage {attrs}>\n{escape(c.text)}\n</passage>")
    return "\n".join(out)


def schema(n: int) -> dict:
    labels = [label_of(i) for i in range(n)]
    return {"type": "object", "additionalProperties": False, "required": ["ranking"],
            "properties": {"ranking": {"type": "array", "items": {"type": "string", "enum": labels}}}}


def parse_ranking(content: str, n: int) -> list[int] | None:
    """Indices into the candidate list, validated: known labels only, no duplicates, at most KEEP. None if unusable."""
    try:
        labels = json.loads(content)["ranking"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return None
    valid = {label_of(i): i for i in range(n)}
    out: list[int] = []
    for lab in labels if isinstance(labels, list) else []:
        if isinstance(lab, str) and lab in valid and valid[lab] not in out:
            out.append(valid[lab])
    return out[:KEEP]


def merge_order(chosen: list[int], n: int) -> list[int]:
    """Reranked picks first, then the remaining candidates in their incoming order."""
    return chosen + [i for i in range(n) if i not in chosen]


@dataclass
class RerankResult:
    order: list[int]  # candidate indices, best first
    seconds: float = 0.0
    cost_usd: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    ok: bool = True
    note: str = ""
    cached: bool = False


def rerank(question: str, candidates: list[Chunk], model: str = MODEL, use_cache: bool = True,
           timeout_s: float | None = None) -> RerankResult:
    n = len(candidates)
    system, user_t, phash = load_prompt()
    key = hashlib.sha256(json.dumps([model, phash, question, [c.chunk_id for c in candidates]]).encode()).hexdigest()[:24]
    cf = CACHE_DIR / f"{key}.json"
    if use_cache and cf.exists():
        d = json.loads(cf.read_text())
        r = RerankResult(**{**d["result"], "cached": True})
        return r
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user_t.format(candidates=render(candidates), question=question)}]
    try:
        kwargs = {} if timeout_s is None else {"timeout_s": timeout_s}
        res = llm.chat(model, messages, 4000, schema=schema(n), schema_name="rerank", **kwargs)
    except llm.LLMError as e:
        return RerankResult(list(range(n)), ok=False, note=f"operational failure: {str(e)[:120]}")
    chosen = parse_ranking(res.content, n)
    cost = prices.chat_cost(model, res.prompt_tokens, res.completion_tokens)
    r = RerankResult(merge_order(chosen or [], n), res.seconds, cost, res.prompt_tokens, res.completion_tokens, res.reasoning_tokens,
                     ok=bool(chosen), note="" if chosen else "no usable ranking; incoming order kept")
    if use_cache:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cf.write_text(json.dumps({"question_sha": hashlib.sha256(question.encode()).hexdigest()[:12], "raw": res.content, "result": r.__dict__ | {"cached": False}}))
    return r
