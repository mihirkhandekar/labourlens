"""Deterministic derived indicators with lineage, used as built-in consistency checks.

Each derived row lists the observation_ids it was computed from, so it can be traced to source cells.
No denominators are invented: retrenchments per 1,000 employees is NOT computed because no employee-count
dataset is in the verified source set (MOM reports quote the rate but the denominator is not in our data).
"""

from __future__ import annotations

import pandas as pd

from labourlens.models import stable_id


def _series(obs: pd.DataFrame, **filters: str) -> pd.DataFrame:
    m = pd.Series(True, index=obs.index)
    for k, v in filters.items():
        m &= obs[k] == v
    return obs[m & obs.value.notna()].set_index("period")[["value", "observation_id"]]


def compute(obs: pd.DataFrame) -> dict:
    rows: list[dict] = []

    # 1. Retrenchment components should add up to the total (rounding in the source is to 10 persons).
    tot = _series(obs, source_id="retrenched_employees")
    perm = _series(obs, source_id="retrenched_permanent")
    term = _series(obs, source_id="retrenched_term_contract")
    for p in sorted(set(tot.index) & set(perm.index) & set(term.index)):
        diff = perm.loc[p, "value"] + term.loc[p, "value"] - tot.loc[p, "value"]
        rows.append(dict(
            derived_id=stable_id("retrench_components", p), indicator_id="retrenchment_components_minus_total", period=p,
            value=float(diff), unit="persons", formula="permanent + term_contract - total",
            inputs=[perm.loc[p, "observation_id"], term.loc[p, "observation_id"], tot.loc[p, "observation_id"]],
            published_value=float(tot.loc[p, "value"]), abs_diff=float(abs(diff))))

    # 2. SA minus NSA unemployment-rate gap per population, in percentage points.
    for pop in ("resident", "overall", "citizen"):
        sa = _series(obs, indicator_id="unemployment_rate", population=pop, adjustment="seasonally_adjusted")
        ns = _series(obs, indicator_id="unemployment_rate", population=pop, adjustment="not_adjusted")
        for p in sorted(set(sa.index) & set(ns.index)):
            gap = round(sa.loc[p, "value"] - ns.loc[p, "value"], 6)
            rows.append(dict(
                derived_id=stable_id("sa_nsa_gap", pop, p), indicator_id=f"unemployment_rate_sa_minus_nsa_{pop}", period=p,
                value=float(gap), unit="percentage_points", formula="SA rate - NSA rate",
                inputs=[sa.loc[p, "observation_id"], ns.loc[p, "observation_id"]], published_value=None, abs_diff=None))

    # 3. Vacancy ratio recomputed from counts: vacancies (establishment survey) / unemployed (household survey, SA, overall).
    #    Two different surveys, so exact equality is not expected; the gap is reported, not hidden.
    jv = _series(obs, source_id="job_vacancy_count")
    ue = _series(obs, source_id="unemployed_overall", adjustment="seasonally_adjusted")
    pub = _series(obs, source_id="vacancy_to_unemployed_ratio")
    for p in sorted(set(jv.index) & set(ue.index) & set(pub.index)):
        calc = jv.loc[p, "value"] / ue.loc[p, "value"]
        rows.append(dict(
            derived_id=stable_id("vacancy_ratio_recomputed", p), indicator_id="vacancy_to_unemployed_ratio_recomputed", period=p,
            value=float(round(calc, 4)), unit="ratio", formula="job_vacancy_count / unemployed_overall(SA)",
            inputs=[jv.loc[p, "observation_id"], ue.loc[p, "observation_id"]],
            published_value=float(pub.loc[p, "value"]), abs_diff=float(round(abs(calc - pub.loc[p, "value"]), 4))))

    table = pd.DataFrame(rows)
    table["inputs"] = table["inputs"].apply(lambda x: "|".join(x))
    table = table.sort_values(["indicator_id", "period"], kind="stable").reset_index(drop=True)

    def scope(df: pd.DataFrame) -> pd.DataFrame:
        return df[(df.period >= "2024-Q1") & (df.period <= "2026-Q2")]

    summary = {}
    for ind in ("retrenchment_components_minus_total", "vacancy_to_unemployed_ratio_recomputed"):
        d = scope(table[table.indicator_id == ind])
        summary[ind] = {"n": int(len(d)), "max_abs_diff": float(d.abs_diff.max()) if len(d) else None,
                        "mean_abs_diff": float(d.abs_diff.mean()) if len(d) else None}
    return {"table": table, "summary": summary}
