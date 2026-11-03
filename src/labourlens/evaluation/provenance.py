"""Content fingerprints for evaluation inputs (never a claim of historical provenance)."""
from __future__ import annotations

import hashlib
import subprocess

from labourlens import paths


def file_hash(path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def snapshot(config: str, eligible_n: int, available_n: int, gold_path=None) -> dict:
    parts = config.split("|")
    planner = next((p for p in parts if p.startswith("planner_v")), None)
    answer = next((p for p in parts if p.startswith("answer_v")), None)
    prompts = {"planner": planner, "answer": answer, "judge": "judge_v1", "rerank": "rerank_v1",
               "planner_user": f"{planner}_user" if planner else None, "answer_user": f"{answer}_user" if answer else None}
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=paths.ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        head = None
    return {"gold_sha256": file_hash(gold_path or paths.EXPERIMENTS / "gold" / "draft_cases.jsonl"),
            "prompt_sha256": {role: file_hash(paths.ROOT / "prompts" / f"{name}.md") if name else None for role, name in prompts.items()},
            "agent_config": config, "git_head": head, "price_table_sha256": file_hash(paths.SPECS / "prices.yaml"),
            "eligible_n": eligible_n, "available_n": available_n,
            "fingerprint_scope": "files at scoring time; generation-time provenance only when saved in raw run"}


def sampling_block(cfg, now: str | None = None, temperature=None, top_p=None) -> dict:
    """Sampling settings for a NEW generation run (planner and answer step of an AgentConfig). The request body sets no temperature, top_p
    or seed (labourlens.answer.llm.chat), so unless explicitly passed they are recorded as 'provider-default'; reruns are not bit-reproducible."""
    import inspect
    from datetime import datetime, timezone

    from labourlens.answer import llm

    def role(model: str, prompt: str, max_tokens: int) -> dict:
        return {"model": model, "prompt_file": f"prompts/{prompt}.md", "prompt_sha256": file_hash(paths.ROOT / "prompts" / f"{prompt}.md"),
                "user_prompt_file": f"prompts/{prompt}_user.md", "user_prompt_sha256": file_hash(paths.ROOT / "prompts" / f"{prompt}_user.md"),
                "max_completion_tokens": max_tokens}

    answer_max = inspect.signature(llm.chat).parameters["max_completion_tokens"].default
    return {"planner": {**role(cfg.planner_model, cfg.planner_prompt, 1500), "mode": getattr(cfg, "planner_mode", "structured")}, "answer": role(cfg.answer_model, cfg.answer_prompt, answer_max),
            "temperature": "provider-default" if temperature is None else temperature, "top_p": "provider-default" if top_p is None else top_p,
            "seed": None, "recorded_at": now or datetime.now(timezone.utc).isoformat(timespec="seconds")}
