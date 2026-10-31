"""Export presentation-ready JSON for the interactive report page (built at a later milestone).

Contains only numbers, definitions, identifiers and links. No MOM report text is exported (rights unresolved or
all-rights-reserved). Every figure carries its observation_id so the page can open a provenance drawer.

Output directory: data/export/ (committed; derived from Open-Data-Licence datasets plus MOM headline numbers).
"""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from labourlens import paths
from labourlens.data import raw_store

EXPORT = paths.DATA / "export"
SCHEMA = "export-0.1"

# Headline KPI cards: 5-7 per kpi-dashboard-design. (card_id, label, filter, higher_is)
KPIS = [
    ("unemployment_resident_sa", "Resident unemployment rate (SA)", dict(indicator_id="unemployment_rate", population="resident", adjustment="seasonally_adjusted"), "worse"),
    ("unemployment_overall_sa", "Overall unemployment rate (SA)", dict(indicator_id="unemployment_rate", population="overall", adjustment="seasonally_adjusted"), "worse"),
    ("vacancy_ratio", "Job vacancies per unemployed person (SA)", dict(source_id="vacancy_to_unemployed_ratio"), "better"),
    ("job_vacancy_rate", "Job vacancy rate", dict(source_id="job_vacancy_rate"), "better"),
    ("retrenchments", "Retrenched employees", dict(source_id="retrenched_employees"), "worse"),
    ("reentry_6m", "Re-employment rate, 6 months after retrenchment", dict(source_id="reentry_6m"), "better"),
]

SERIES = {
    "unemployment_resident_sa": dict(indicator_id="unemployment_rate", population="resident", adjustment="seasonally_adjusted"),
    "unemployment_resident_nsa": dict(indicator_id="unemployment_rate", population="resident", adjustment="not_adjusted"),
    "unemployment_overall_sa": dict(indicator_id="unemployment_rate", population="overall", adjustment="seasonally_adjusted"),
    "unemployment_citizen_sa": dict(indicator_id="unemployment_rate", population="citizen", adjustment="seasonally_adjusted"),
    "vacancy_ratio": dict(source_id="vacancy_to_unemployed_ratio"),
    "job_vacancy_rate": dict(source_id="job_vacancy_rate"),
    "job_vacancies": dict(source_id="job_vacancy_count"),
    "retrenchments": dict(source_id="retrenched_employees"),
    "retrenched_permanent": dict(source_id="retrenched_permanent"),
    "retrenched_term_contract": dict(source_id="retrenched_term_contract"),
    "resignation_rate": dict(source_id="resignation_rate"),
    "recruitment_rate": dict(source_id="recruitment_rate"),
    "reentry_6m": dict(source_id="reentry_6m"),
    "reentry_12m": dict(source_id="reentry_12m"),
}


def _pick(obs: pd.DataFrame, f: dict[str, str]) -> pd.DataFrame:
    m = pd.Series(True, index=obs.index)
    for k, v in f.items():
        m &= obs[k] == v
    return obs[m & obs.value.notna()].sort_values("period")


def _delta(unit: str, last: float, prev: float) -> dict[str, Any]:
    if unit == "percent":
        return {"change": round(last - prev, 4), "change_unit": "percentage_points"}
    if unit == "ratio":
        return {"change": round(last - prev, 4), "change_unit": "ratio_points"}
    return {"change": round(last - prev, 4), "change_unit": "persons", "change_pct": round((last / prev - 1) * 100, 2)}


def _dump(name: str, body: Any) -> None:
    EXPORT.mkdir(parents=True, exist_ok=True)
    (EXPORT / name).write_text(json.dumps(body, indent=1, ensure_ascii=False, sort_keys=True) + "\n")


def run() -> None:
    obs = pd.read_parquet(paths.PROCESSED / "observations.parquet")
    manifest = raw_store.load_manifest()
    validation = json.loads((paths.ARTIFACTS / "validation.json").read_text())
    rec = json.loads((paths.ARTIFACTS / "reconciliation.json").read_text())

    cards = []
    for card_id, label, f, good in KPIS:
        s = _pick(obs, f)
        s = s[s.period <= "2026-Q2"]
        last, prev = s.iloc[-1], s.iloc[-2]
        same_q_last_year = s[s.period == f"{int(last.period[:4]) - 1}-Q{last.period[-1]}"]
        card = {
            "card_id": card_id, "label": label, "period": last.period, "value": float(last.value), "unit": last.unit,
            "population": last.population, "adjustment": last.adjustment, "observation_id": last.observation_id,
            "source_id": last.source_id, "previous": {"period": prev.period, "value": float(prev.value), "observation_id": prev.observation_id},
            **_delta(last.unit, float(last.value), float(prev.value)),
            "year_ago": None if same_q_last_year.empty else {"period": same_q_last_year.iloc[0].period, "value": float(same_q_last_year.iloc[0].value),
                                                           "observation_id": same_q_last_year.iloc[0].observation_id},
            "higher_is": good,
            "sparkline": [{"period": r.period, "value": float(r.value)} for r in s[s.period >= "2022-Q1"].itertuples()],
        }
        cards.append(card)
    _dump("kpis.json", {"schema_version": SCHEMA, "answer_scope": ["2024-Q1", "2026-Q2"], "cards": cards})

    series = {}
    for name, f in SERIES.items():
        s = _pick(obs, f)
        s = s[(s.period >= "2019-Q1") & (s.period <= "2026-Q2")]
        series[name] = {"unit": s.iloc[0].unit, "population": s.iloc[0].population, "adjustment": s.iloc[0].adjustment,
                        "points": [{"period": r.period, "value": float(r.value), "observation_id": r.observation_id} for r in s.itertuples()]}
    _dump("series.json", {"schema_version": SCHEMA, "series": series})

    ind = obs[(obs.source_id == "retrenched_by_industry") & obs.in_answer_scope]
    _dump("retrenchments_by_industry.json", {"schema_version": SCHEMA, "note": "Rounded to 10 by the publisher. null = '-' in source (not a published number, not zero).",
          "rows": [{"period": r.period, "industry": r.dimension, "level": None if pd.isna(r.sector_level) else int(r.sector_level),
                    "path": r.sector_path, "value": None if pd.isna(r.value) else float(r.value), "observation_id": r.observation_id}
                   for r in ind.itertuples()]})

    sec = obs[(obs.source_id == "employment_change_by_sector") & obs.in_answer_scope]
    _dump("employment_change_by_sector.json", {"schema_version": SCHEMA, "population_basis": "unverified",
          "rows": [{"period": r.period, "sector": r.dimension, "level": int(r.sector_level), "path": r.sector_path,
                    "value": None if pd.isna(r.value) else float(r.value), "observation_id": r.observation_id} for r in sec.itertuples()]})

    _dump("reconciliation.json", {"schema_version": SCHEMA, **rec})

    srcs = []
    for sid, e in sorted(manifest.items()):
        srcs.append({"source_id": sid, "title": e.title, "publisher": e.publisher, "type": e.source_type, "url": e.canonical_url,
                     "release_stage": e.release_stage, "publication_date": e.publication_date, "snapshot_id": e.snapshot_id,
                     "sha256": e.sha256, "rights_status": e.rights_status, "redistribution": e.redistribution_policy,
                     "licence": e.licence_id})
    _dump("sources.json", {"schema_version": SCHEMA,
          "attribution": "Contains information from data.gov.sg datasets (MOM, SingStat) accessed 2026-10-30, made available under the "
                         "Singapore Open Data Licence v1.0: https://developers.data.gov.sg/open-data-licence. Not endorsed by any agency.",
          "sources": srcs})
    keep = [c for c in validation["checks"] if c["status"] != "pass" or c["name"].startswith(("manifest.", "packaging.", "reconcile."))]
    _dump("quality.json", {"schema_version": SCHEMA, "summary": validation["summary"], "notable_checks": keep})
    print(f"exported {len(list(EXPORT.glob('*.json')))} files to {paths.rel(EXPORT)}")
