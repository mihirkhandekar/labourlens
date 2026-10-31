"""Validate the gold set and generate the owner's review sheet (D-017).

Validation is mechanical: schema, counts, ids exist, evidence belongs to the stated source. It cannot judge
whether a question is good or the evidence right; only the owner's review does that.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import date

import pandas as pd

from labourlens import paths
from labourlens.retrieval import evaluate as ev

FAMILIES = ["factual_lookup", "numerical_comparison", "cross_source_synthesis", "revision_conflict", "ambiguity_insufficient_causal", "adversarial"]
BEHAVIOURS = {"answer", "abstain", "clarify", "ignore_injection_and_answer", "refuse"}
REQUIRED = ["case_id", "split", "family", "question", "expected_behavior", "evidence_text", "evidence_data", "reference_facts",
            "calculation", "abstain_reason", "adversarial", "difficulty_note", "drafted_by", "reviewed_by", "review_status"]
REVIEW_DECISION_SOURCES = {"owner_manual", "agreed_with_ai_suggestion"}


def review_errors(case: dict) -> list[str]:
    """Check review provenance, not the correctness or independence of the verdict."""
    status = case.get("review_status")
    reviewer = case.get("reviewed_by")
    provenance = case.get("owner_review")
    if status == "draft":
        if reviewer is not None or provenance is not None:
            return ["draft review requires reviewed_by=null and no owner_review"]
        return []
    if status != "owner_reviewed":
        return ["review_status must be draft or owner_reviewed"]
    if not isinstance(reviewer, str) or not reviewer.strip():
        return ["owner_reviewed requires a named reviewed_by"]
    if not isinstance(provenance, dict):
        return ["owner_reviewed requires owner_review provenance"]
    errors = []
    if set(provenance) != {"reviewer", "decision_source", "date"}:
        errors.append("owner_review requires exactly reviewer, decision_source and date")
    if provenance.get("reviewer") != reviewer:
        errors.append("owner_review reviewer must match reviewed_by")
    source = provenance.get("decision_source")
    if not isinstance(source, str) or source not in REVIEW_DECISION_SOURCES:
        errors.append("owner_review decision_source must identify a per-card owner action")
    value = provenance.get("date")
    try:
        if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
            raise ValueError
    except ValueError:
        errors.append("owner_review date must be a valid YYYY-MM-DD date")
    return errors


def validate(path=None) -> list[str]:
    f = path or ev.GOLD / "draft_cases.jsonl"
    cases = [json.loads(line) for line in f.read_text().splitlines() if line.strip()]
    errs: list[str] = []
    pids: dict[str, str] = {}
    texts: dict[str, str] = {}
    for p in paths.PASSAGES.glob("*.jsonl"):
        for line in p.read_text().splitlines():
            d = json.loads(line)
            pids[d["passage_id"]] = d["source_id"]
            texts[d["passage_id"]] = d["text"]
    obs = pd.read_parquet(paths.PROCESSED / "observations.parquet").set_index("observation_id")
    seen = set()
    for c in cases:
        cid = c.get("case_id", "?")
        miss = [k for k in REQUIRED if k not in c]
        if miss:
            errs.append(f"{cid}: missing {miss}")
            continue
        if cid in seen:
            errs.append(f"{cid}: duplicate id")
        seen.add(cid)
        if c["family"] not in FAMILIES:
            errs.append(f"{cid}: bad family {c['family']}")
        if c["expected_behavior"] not in BEHAVIOURS:
            errs.append(f"{cid}: bad behaviour")
        if not cid.startswith("DEV-" if c["split"] == "dev" else "HO-"):
            errs.append(f"{cid}: id prefix does not match split")
        for e in c["evidence_text"]:
            for pid in e["passage_ids"]:
                if pid not in pids:
                    errs.append(f"{cid}: unknown passage {pid}")
                elif pids[pid] != e["source_id"]:
                    errs.append(f"{cid}: passage {pid} is not in {e['source_id']}")
        for e in c.get("partial_evidence_text", []):  # alternatives that cover only part of an answer: ids must still be real and match their source
            for pid in e["passage_ids"]:
                if pid not in pids:
                    errs.append(f"{cid}: unknown partial-evidence passage {pid}")
                elif pids[pid] != e["source_id"]:
                    errs.append(f"{cid}: partial-evidence passage {pid} is not in {e['source_id']}")
        for e in c["evidence_data"]:
            for oid in e["observation_ids"]:
                if oid not in obs.index:
                    errs.append(f"{cid}: unknown observation {oid}")
                elif obs.loc[oid, "source_id"] != e["source_id"] or obs.loc[oid, "period"] != e["period"]:
                    errs.append(f"{cid}: observation {oid} does not match {e['source_id']} {e['period']}")
        calc = c["calculation"]
        if calc:
            if isinstance(calc["inputs"], dict):  # literal values quoted from text evidence: each must appear in a cited passage
                text = " ".join(texts.get(pid, "") for e in c["evidence_text"] for pid in e["passage_ids"])
                for name, v in calc["inputs"].items():
                    if f"{v:g}" not in text and str(v) not in text:
                        errs.append(f"{cid}: calculation input {name}={v} not found in cited passages")
            else:
                for oid in calc["inputs"]:
                    if oid not in obs.index:
                        errs.append(f"{cid}: calculation input {oid} unknown")
        if c["expected_behavior"] == "answer" and not (c["evidence_text"] or c["evidence_data"]):
            errs.append(f"{cid}: answerable case with no evidence")
        if c["expected_behavior"] in ("abstain", "clarify") and not c["abstain_reason"]:
            errs.append(f"{cid}: abstain/clarify without reason")
        errs.extend(f"{cid}: {error}" for error in review_errors(c))
    cnt = Counter((c["split"], c["family"]) for c in cases)
    print(f"{len(cases)} cases;", dict(Counter(c["split"] for c in cases)))
    for fam in FAMILIES:
        print(f"  {fam}: dev={cnt[('dev', fam)]} heldout={cnt[('heldout', fam)]}")
    return errs


def _clip(text: str, n: int = 6) -> str:
    """Rights rule D-001/D-004: never reproduce more than n consecutive words of source text."""
    w = text.split()
    return text if len(w) <= n else " ".join(w[:n]) + " [...]"


def _clip_segments(text: str) -> str:
    return " | ".join(_clip(seg) for seg in text.split(" | "))


def _clip_locator(loc: str) -> str:
    head, sep, tail = loc.rpartition(", ")
    if sep and re.fullmatch(r"(?:item|para|paragraph|row|table|p\.?)\s*\S+", tail):
        return _clip(head) + sep + tail
    return _clip(loc)


def review_sheet() -> str:
    f = ev.GOLD / "draft_cases.jsonl"
    cases = [json.loads(line) for line in f.read_text().splitlines() if line.strip()]
    reviewed = sum(c.get("review_status") == "owner_reviewed" for c in cases)
    L = ["# Gold set review sheet", "",
         f"**Recorded owner review: {reviewed}/{len(cases)} cases.** Per-card owner actions may agree with AI suggestions; this is not independent inter-rater evidence.",
         "Review remaining cases in two passes to avoid anchoring on the draft (D-017):",
         "**Pass 1** (question only): is the question realistic for a policy researcher, in scope, unambiguous as intended? Note any evidence you would expect, before reading the draft.",
         "**Pass 2** (draft): open each listed source at the locator and check the draft evidence and reference facts. Then fill the row in the results table.", "",
         "Cases are in `experiments/gold/draft_cases.jsonl`. MOM text is not reproduced here.", ""]
    for c in cases:
        L += [f"### {c['case_id']} ({c['split']}, {c['family']})", "", f"**Question:** {c['question']}", ""]
    L += ["", "---", "## Pass 2: draft details", ""]
    for c in cases:
        ev_t = "; ".join(f"`{e['source_id']}` {_clip_locator(e['locator'])}{' (primary)' if e.get('primary') else ''}" for e in c["evidence_text"]) or "none"
        ev_d = "; ".join(f"`{e['source_id']}` {e['period']} {_clip(e.get('dimension') or '')}".strip() for e in c["evidence_data"]) or "none"
        L += [f"#### {c['case_id']}", f"- Expected behaviour: **{c['expected_behavior']}**", f"- Text evidence: {ev_t}", f"- Data evidence: {ev_d}",
              "- Reference facts: " + " | ".join(_clip_segments(x) for x in c["reference_facts"]) if c["reference_facts"] else "- Reference facts: none (non-answer case)"]
        if c["abstain_reason"]:
            L.append(f"- Why no answer: {c['abstain_reason']}")
        if c["adversarial"]:
            L.append(f"- Adversarial ({c['adversarial']['type']}); fixture needed: {c['adversarial']['fixture_needed']}")
        L += [""]
    L += ["", "## Reviewer results", "", "| Case | Reviewer | Date | Q realistic (Y/N) | Extra evidence expected (pass 1) | Draft evidence (right / partial / wrong) | Behaviour right (Y/N) | Notes |", "|---|---|---|---|---|---|---|---|"]
    L += [f"| {c['case_id']} |  |  |  |  |  |  |  |" for c in cases]
    return "\n".join(L) + "\n"
