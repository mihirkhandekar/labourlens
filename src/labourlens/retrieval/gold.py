"""Validate the gold set and generate the owner's review sheet (D-017).

Validation is mechanical: schema, counts, ids exist, evidence belongs to the stated source. It cannot judge
whether a question is good or the evidence right; only the owner's review does that.
"""

from __future__ import annotations

import json
from collections import Counter

import pandas as pd

from labourlens import paths
from labourlens.retrieval import evaluate as ev

FAMILIES = ["factual_lookup", "numerical_comparison", "cross_source_synthesis", "revision_conflict", "ambiguity_insufficient_causal", "adversarial"]
BEHAVIOURS = {"answer", "abstain", "clarify", "ignore_injection_and_answer", "refuse"}
REQUIRED = ["case_id", "split", "family", "question", "expected_behavior", "evidence_text", "evidence_data", "reference_facts",
            "calculation", "abstain_reason", "adversarial", "difficulty_note", "drafted_by", "reviewed_by", "review_status"]


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
        if c["review_status"] != "draft" or c["reviewed_by"]:
            errs.append(f"{cid}: review fields must stay draft/null until the owner reviews")
    cnt = Counter((c["split"], c["family"]) for c in cases)
    print(f"{len(cases)} cases;", dict(Counter(c["split"] for c in cases)))
    for fam in FAMILIES:
        print(f"  {fam}: dev={cnt[('dev', fam)]} heldout={cnt[('heldout', fam)]}")
    return errs


def review_sheet() -> str:
    f = ev.GOLD / "draft_cases.jsonl"
    cases = [json.loads(line) for line in f.read_text().splitlines() if line.strip()]
    L = ["# Gold set review sheet (UNREVIEWED)", "",
         "**Status: not reviewed by a human.** Review each case in two passes to avoid anchoring on the draft (D-017):",
         "**Pass 1** (question only): is the question realistic for a policy researcher, in scope, unambiguous as intended? Note any evidence you would expect, before reading the draft.",
         "**Pass 2** (draft): open each listed source at the locator and check the draft evidence and reference facts. Then fill the row in the results table.", "",
         "Cases are in `experiments/gold/draft_cases.jsonl`. MOM text is not reproduced here.", ""]
    for c in cases:
        L += [f"### {c['case_id']} ({c['split']}, {c['family']})", "", f"**Question:** {c['question']}", ""]
    L += ["", "---", "## Pass 2: draft details", ""]
    for c in cases:
        ev_t = "; ".join(f"`{e['source_id']}` {e['locator']}{' (primary)' if e.get('primary') else ''}" for e in c["evidence_text"]) or "none"
        ev_d = "; ".join(f"`{e['source_id']}` {e['period']} {e.get('dimension') or ''}".strip() for e in c["evidence_data"]) or "none"
        L += [f"#### {c['case_id']}", f"- Expected behaviour: **{c['expected_behavior']}**", f"- Text evidence: {ev_t}", f"- Data evidence: {ev_d}",
              "- Reference facts: " + " | ".join(c["reference_facts"]) if c["reference_facts"] else "- Reference facts: none (non-answer case)"]
        if c["abstain_reason"]:
            L.append(f"- Why no answer: {c['abstain_reason']}")
        if c["adversarial"]:
            L.append(f"- Adversarial ({c['adversarial']['type']}); fixture needed: {c['adversarial']['fixture_needed']}")
        L += [""]
    L += ["", "## Reviewer results", "", "| Case | Reviewer | Date | Q realistic (Y/N) | Extra evidence expected (pass 1) | Draft evidence (right / partial / wrong) | Behaviour right (Y/N) | Notes |", "|---|---|---|---|---|---|---|---|"]
    L += [f"| {c['case_id']} |  |  |  |  |  |  |  |" for c in cases]
    return "\n".join(L) + "\n"
