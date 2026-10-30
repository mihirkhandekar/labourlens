"""Retrieve -> build context -> generate structured answer -> validate -> at most one repair (ADR-002 bound)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from pydantic import ValidationError

from labourlens import paths
from labourlens.answer import context as cx
from labourlens.answer import llm, validate
from labourlens.answer.schema import Answer

PROMPTS = paths.ROOT / "prompts"


@dataclass(frozen=True)
class AnswerConfig:
    model: str
    prompt: str = "answer_v1"
    k: int = 5  # retrieved chunks shown to the model
    max_completion_tokens: int = 6000
    oracle: bool = False  # experiment only: gold passages are placed first in the context

    def key(self) -> str:
        return f"{self.model}|{self.prompt}|k{self.k}" + ("|oracle" if self.oracle else "")


def load_prompt(version: str) -> tuple[str, str, str]:
    system = (PROMPTS / f"{version}.md").read_text()
    user = (PROMPTS / f"{version}_user.md").read_text()
    h = hashlib.sha256((system + user).encode()).hexdigest()[:12]
    return system, user, h


def _parse(content: str) -> tuple[Answer | None, str | None]:
    try:
        return Answer.model_validate(json.loads(content)), None
    except json.JSONDecodeError:
        return None, "output is not valid JSON"
    except ValidationError as e:  # locations only; the message would echo model output
        return None, "output does not match the answer schema at: " + ", ".join(".".join(map(str, x["loc"])) for x in e.errors()[:5])


def answer_question(question: str, retriever, chunks_by_id: dict, passages_by_id: dict, cfg: AnswerConfig, oracle_ids: list[str] | None = None) -> dict:
    hits = retriever.search(question, cfg.k)
    chunks = [chunks_by_id[cid] for cid, _ in hits]
    ctx = cx.build_context(chunks, passages_by_id, oracle_ids if cfg.oracle else None)
    system, user_t, _ = load_prompt(cfg.prompt)
    messages = [{"role": "system", "content": system},
                {"role": "user", "content": user_t.format(context=cx.render(ctx), question=question)}]
    calls, errors, ans, report = [], [], None, None
    for attempt in range(2):  # first try plus one repair
        try:
            res = llm.chat(cfg.model, messages, cfg.max_completion_tokens)
        except llm.LLMError as e:
            errors = [f"operational failure: {e}"]
            break
        calls.append({"prompt_tokens": res.prompt_tokens, "completion_tokens": res.completion_tokens,
                      "reasoning_tokens": res.reasoning_tokens, "seconds": round(res.seconds, 2)})
        ans, perr = _parse(res.content)
        if ans is not None:
            report = validate.check(ans, ctx)
            errors = report.errors
        else:
            errors = [res.refusal or perr or "empty output"]
        if not errors:
            break
        if attempt == 0:
            messages = messages + [{"role": "assistant", "content": res.content or "{}"},
                                   {"role": "user", "content": (PROMPTS / "repair_v1.md").read_text().format(errors="\n".join(f"- {e}" for e in errors))}]
    return {
        "question": question, "config": cfg.key(), "answer": ans.model_dump() if ans else None,
        "valid": bool(ans) and not errors, "errors": errors, "operational_failure": any(e.startswith("operational failure") for e in errors), "attempts": len(calls),
        "ungrounded_numbers": report.ungrounded_numbers if report else [],
        "cited_passage_ids": report.cited_passage_ids if report else [],
        "context_passage_ids": [p.passage_id for p in ctx], "context_labels": {p.label: p.passage_id for p in ctx},
        "calls": calls, "seconds": round(sum(c["seconds"] for c in calls), 2),
        "prompt_tokens": sum(c["prompt_tokens"] for c in calls), "completion_tokens": sum(c["completion_tokens"] for c in calls),
    }
