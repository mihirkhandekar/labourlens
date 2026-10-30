"""Advance vs final vs dataset reconciliation of the headline 'total employment change'.

Three kinds of numbers describe 'employment change in a quarter' and must never be merged silently:
  advance   MOM advance release (preliminary), published ~6 weeks after quarter end
  final     MOM Labour Market Report / press release (headline excludes migrant domestic workers, MDW)
  dataset   SingStat/MOM table 'Changes in employment by sector', row 'Total Changes In Employment'

Outputs numbers, release dates and passage IDs only (no MOM text is copied into the artifact).
"""

from __future__ import annotations

import re

import pandas as pd

from labourlens.models import DocumentPassage

_PAT = re.compile(r"[Tt]otal employment[^.]{0,120}?(?:grew|increased|expanded|rose|grow|increase)[^.]{0,40}?by\s+([\d,]{4,7})")

QUARTERS = {
    "2025-Q3": ("mom-2025-q3-advance", "mom-2025-q3-final-release"),
    "2025-Q4": ("mom-2025-q4-advance", "mom-2025-q4-final-release"),
    "2026-Q1": ("mom-2026-q1-advance", "mom-2026-q1-final-release"),
    "2026-Q2": ("mom-2026-q2-advance", "mom-2026-q2-final-release"),
}


def _headline(passages: list[DocumentPassage], source_id: str) -> dict | None:
    for p in passages:
        if p.source_id != source_id:
            continue
        m = _PAT.search(p.text.replace("\xa0", " "))
        if m:
            return {"value": int(m.group(1).replace(",", "")), "passage_id": p.passage_id, "locator": p.locator,
                    "publication_date": p.publication_date, "release_stage": p.release_stage}
    return None


def build(obs: pd.DataFrame, passages: list[DocumentPassage]) -> dict:
    ds = obs[(obs.source_id == "employment_change_by_sector") & (obs.sector_path == "Total Changes In Employment")]
    rows = []
    for period, (adv_id, fin_id) in QUARTERS.items():
        adv = _headline(passages, adv_id)
        fin = _headline(passages, fin_id)
        d = ds[ds.period == period]
        dsv = d.iloc[0] if len(d) else None
        row = {
            "period": period,
            "advance": adv,
            "final": fin,
            "dataset_total": None if dsv is None or pd.isna(dsv.value) else {
                "value": int(dsv.value), "observation_id": dsv.observation_id, "source_id": "employment_change_by_sector",
                "snapshot_id": dsv.snapshot_id},
        }
        if adv and fin:
            row["final_minus_advance"] = fin["value"] - adv["value"]
        if fin and row["dataset_total"]:
            row["dataset_minus_final"] = row["dataset_total"]["value"] - fin["value"]
        rows.append(row)
    return {
        "description": "Headline total employment change by quarter from three source kinds. Values are persons.",
        "interpretation_note": (
            "MOM headline totals exclude migrant domestic workers (MDW) per the 2Q 2026 report. The dataset total's population "
            "basis is UNVERIFIED. A stable positive gap (dataset minus final) is consistent with an MDW difference but this is an "
            "INFERENCE, not a verified fact."),
        "quarters": rows,
    }
