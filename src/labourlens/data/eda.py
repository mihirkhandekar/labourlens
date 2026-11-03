"""Exploratory figures and findings computed from the validated observation store (never hand-typed).

Design rules (kpi-dashboard-design): one message per chart, units in axis labels, comparison context on
every series, consistent colour meaning (one hue per concept), no 3D, source line on every figure.
Findings text is generated from the same numbers, so it cannot drift from the charts.
"""

from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from labourlens import paths
from labourlens.data import catalog

INK, MUTED, GRID = "#1f2933", "#6b7785", "#e4e7eb"
C_A, C_B, C_C = "#1f6feb", "#d1495b", "#2a9d8f"  # blue=unemployment/final, red=retrenchment/risk, teal=vacancy/dataset
SRC = "Source: MOM / SingStat via data.gov.sg (Singapore Open Data Licence v1.0); MOM press releases. LabourLens snapshot 2026-10-30."


def _style(ax, title: str, ylabel: str) -> None:
    ax.set_title(title, loc="left", fontsize=12, color=INK, fontweight="bold")
    ax.set_ylabel(ylabel, color=MUTED, fontsize=9)
    ax.set_axisbelow(True)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=8)


def _q(period: str) -> float:
    return int(period[:4]) + (int(period[-1]) - 1) / 4


def _series(obs: pd.DataFrame, **f: str) -> pd.DataFrame:
    m = pd.Series(True, index=obs.index)
    for k, v in f.items():
        m &= obs[k] == v
    return obs[m & obs.value.notna()].sort_values("period")


def fig_vacancy_vs_unemployment(obs: pd.DataFrame, out) -> dict:
    ratio = _series(obs, source_id="vacancy_to_unemployed_ratio")
    ur = _series(obs, indicator_id="unemployment_rate", population="resident", adjustment="seasonally_adjusted")
    lo = "2019-Q1"
    ratio, ur = ratio[ratio.period >= lo], ur[ur.period >= lo]
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.plot(ratio.period.map(_q), ratio.value, color=C_C, lw=2)
    ax.set_xlim(2019, 2026.5)
    scope_start = _q(catalog.ANSWER_SCOPE_START)
    ax.axvspan(scope_start, 2026.5, color="#f1f5f9", zorder=0)
    ax.text(scope_start + 0.05, ax.get_ylim()[1] * 0.97, f"answer scope {catalog.ANSWER_SCOPE_START} to {catalog.ANSWER_SCOPE_END}", fontsize=8, color=MUTED, va="top")
    _style(ax, "Vacancies per unemployed person have eased from their 2022 peak", "ratio (vacancies per unemployed person, SA)")
    ax2 = ax.twinx()
    ax2.plot(ur.period.map(_q), ur.value, color=C_A, lw=2, ls="--")
    ax2.set_ylabel("resident unemployment rate, SA (%)", color=MUTED, fontsize=9)
    ax2.tick_params(colors=MUTED, labelsize=8)
    for s in ("top", "right", "left"):
        ax2.spines[s].set_visible(False)
    ax.plot([], [], color=C_C, lw=2, label="Vacancy-to-unemployed ratio (left)")
    ax.plot([], [], color=C_A, lw=2, ls="--", label="Resident unemployment rate, SA (right)")
    ax.legend(frameon=False, fontsize=8, loc="upper right", bbox_to_anchor=(1, 0.88))
    fig.text(0.01, 0.01, SRC, fontsize=6.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(out, dpi=160)
    plt.close(fig)
    peak = ratio.loc[ratio.value.idxmax()]
    last = ratio.iloc[-1]
    return {"ratio_peak_period": peak.period, "ratio_peak": float(peak.value), "ratio_last_period": last.period,
            "ratio_last": float(last.value), "ur_last": float(ur.iloc[-1].value), "ur_scope_min": float(ur[ur.period >= catalog.ANSWER_SCOPE_START].value.min()),
            "ur_scope_max": float(ur[ur.period >= catalog.ANSWER_SCOPE_START].value.max())}


def fig_retrenchment(obs: pd.DataFrame, out) -> dict:
    tot = _series(obs, source_id="retrenched_employees")
    tot = tot[(tot.period >= catalog.ANSWER_SCOPE_START) & (tot.period <= catalog.ANSWER_SCOPE_END)]
    ind = obs[(obs.source_id == "retrenched_by_industry") & (obs.in_answer_scope) & (obs.sector_level == 1)]
    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 4.2), gridspec_kw={"width_ratios": [1.1, 1]})
    a.bar(tot.period, tot.value, color=[C_B if p == "2026-Q2" else "#e9a3ac" for p in tot.period])
    for x, v in zip(tot.period, tot.value):
        a.text(x, v + 40, f"{int(v):,}", ha="center", fontsize=5.5, rotation=90, va="bottom", color=INK)
    a.tick_params(axis="x", rotation=60)
    _style(a, "Retrenchments rose in 2026-Q2", "retrenched employees (persons)")
    pivot = ind.pivot_table(index="period", columns="dimension", values="value", aggfunc="first")
    order = [c for c in ["services", "manufacturing", "construction", "others"] if c in pivot.columns]
    bottom = pd.Series(0.0, index=pivot.index)
    cols = {"services": C_B, "manufacturing": "#e9a3ac", "construction": "#f4d1d6", "others": "#cbd2d9"}
    for c in order:
        v = pivot[c].fillna(0)
        b.bar(pivot.index, v, bottom=bottom, color=cols[c], label=c)
        bottom += v
    b.tick_params(axis="x", rotation=60)
    b.legend(frameon=False, fontsize=8)
    _style(b, "Services account for most of the quarterly total", "retrenched employees by top-level industry (persons)")
    fig.text(0.01, 0.01, SRC + " Industry values rounded to 10; '-' cells counted as 0 for stacking only.", fontsize=6.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(out, dpi=160)
    plt.close(fig)
    last, prev = tot.iloc[-1], tot.iloc[-2]
    svc = pivot.loc["2026-Q2", "services"] if "services" in pivot.columns else float("nan")
    return {"last_period": last.period, "last": float(last.value), "prev_period": prev.period, "prev": float(prev.value),
            "pct_change": float((last.value / prev.value - 1) * 100), "services_share_last": float(svc / last.value * 100)}


def fig_reconciliation(rec: dict, out) -> dict:
    rows = rec["quarters"]
    x = range(len(rows))
    fig, ax = plt.subplots(figsize=(9, 4.2))
    w = 0.26
    ax.bar([i - w for i in x], [r["advance"]["value"] for r in rows], w, color="#9fb8e8", label="MOM advance release")
    ax.bar(list(x), [r["final"]["value"] for r in rows], w, color=C_A, label="MOM final (excl. migrant domestic workers)")
    ax.bar([i + w for i in x], [r["dataset_total"]["value"] for r in rows], w, color=C_C, label="SingStat/MOM sector table total (basis unverified)")
    for i, r in enumerate(rows):
        for dx, key in ((-w, "advance"), (0, "final")):
            ax.text(i + dx, r[key]["value"] + 300, f"{r[key]['value']:,}", ha="center", fontsize=7, color=INK)
        ax.text(i + w, r["dataset_total"]["value"] + 300, f"{r['dataset_total']['value']:,}", ha="center", fontsize=7, color=INK)
    ax.set_xticks(list(x))
    ax.set_xticklabels([r["period"] for r in rows])
    _style(ax, "Three sources, three 'total employment change' numbers per quarter", "persons")
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    fig.text(0.01, 0.01, SRC, fontsize=6.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(out, dpi=160)
    plt.close(fig)
    gaps = [r["dataset_minus_final"] for r in rows]
    revs = [r["final_minus_advance"] for r in rows]
    return {"dataset_minus_final": gaps, "final_minus_advance": revs, "periods": [r["period"] for r in rows]}


def run() -> None:
    paths.FIGURES.mkdir(parents=True, exist_ok=True)
    obs = pd.read_parquet(paths.PROCESSED / "observations.parquet")
    rec = json.loads((paths.ARTIFACTS / "reconciliation.json").read_text())
    f1 = fig_vacancy_vs_unemployment(obs, paths.FIGURES / "fig1_vacancy_vs_unemployment.png")
    f2 = fig_retrenchment(obs, paths.FIGURES / "fig2_retrenchment.png")
    f3 = fig_reconciliation(rec, paths.FIGURES / "fig3_employment_change_reconciliation.png")
    findings = [
        "# Exploratory findings (generated from the validated store)",
        "",
        "Numbers below are computed by `labourlens.data.eda` from `data/processed/observations.parquet`; they are descriptive, not causal.",
        "",
        f"1. **Vacancy-to-unemployed ratio** peaked at {f1['ratio_peak']:.2f} in {f1['ratio_peak_period']} (since 2019) and stood at "
        f"{f1['ratio_last']:.2f} in {f1['ratio_last_period']}, while the resident unemployment rate (SA) stayed between "
        f"{f1['ur_scope_min']:.1f}% and {f1['ur_scope_max']:.1f}% across {catalog.ANSWER_SCOPE_START} to {catalog.ANSWER_SCOPE_END} (latest {f1['ur_last']:.1f}%). "
        "Figure: `artifacts/figures/fig1_vacancy_vs_unemployment.png`. The ratio is vacancies per unemployed person, not a percentage.",
        f"2. **Retrenchments** rose from {f2['prev']:,.0f} ({f2['prev_period']}) to {f2['last']:,.0f} ({f2['last_period']}), "
        f"{f2['pct_change']:+.1f}%; services were {f2['services_share_last']:.0f}% of the latest quarter's top-level industry total. "
        "Figure: `artifacts/figures/fig2_retrenchment.png`.",
        f"3. **Revisions and definitions:** across {', '.join(f3['periods'])}, final minus advance headline employment change was "
        f"{', '.join(f'{v:+,}' for v in f3['final_minus_advance'])} persons, and the sector-table total exceeded MOM's final headline by "
        f"{', '.join(f'{v:,}' for v in f3['dataset_minus_final'])} persons. The consistent gap is **consistent with** a migrant-domestic-worker "
        "definition difference but that is an inference, not a verified fact. Figure: `artifacts/figures/fig3_employment_change_reconciliation.png`.",
        "",
        "Human review: these findings and figures have not been separately reviewed by a person. The 14 statistical source checks in `docs/human-review/` compare a sample of the underlying values with the publisher, not these findings.",
    ]
    (paths.ARTIFACTS / "eda-findings.md").write_text("\n".join(findings) + "\n")
