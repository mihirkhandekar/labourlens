"""Generate human spot-check sheets. Sheets are pre-filled with OUR values and left blank for the reviewer.
Nothing here marks a row verified; only a person editing the sheet can do that.

Committed sheet: docs/human-review/ (numbers, ids, locators, links; no MOM text).
Local reading aid with passage text: private/review/ (gitignored).
"""

from __future__ import annotations

import json
import random

import pandas as pd

from labourlens import paths
from labourlens.data import raw_store

SEED = 20261030
OUT = paths.ROOT / "docs" / "human-review"
PRIV = paths.ROOT / "private" / "review"
APPROVED = ["resident_unemployment_rate", "vacancy_to_unemployed_ratio", "retrenched_employees", "employment_change_by_sector"]
REPORTS = ["mom-2025-q3-final", "mom-2025-q4-final", "mom-2026-q1-final", "mom-2026-q2-final"]
HEAD = "| # | Reviewer | Date | Result (match / mismatch / unclear) | Notes |\n|---|---|---|---|---|\n"


def _stat_rows() -> list[dict]:
    obs = pd.read_parquet(paths.PROCESSED / "observations.parquet")
    man = raw_store.load_manifest()
    rng = random.Random(SEED)
    pick: list[pd.Series] = []
    base = obs[obs.in_answer_scope & obs.value.notna()]
    for sid in APPROVED:
        d = base[base.source_id == sid].sort_values("observation_id")
        pick += [d.iloc[i] for i in rng.sample(range(len(d)), 2)]
    others = sorted(set(base.source_id) - set(APPROVED))
    for sid in rng.sample(others, 4):
        d = base[base.source_id == sid].sort_values("observation_id")
        pick.append(d.iloc[rng.randrange(len(d))])
    nulls = obs[(obs.source_id == "retrenched_by_industry") & obs.value.isna() & obs.in_answer_scope].sort_values("observation_id")
    pick.append(nulls.iloc[0])
    old = obs[(obs.source_id == "resident_unemployment_rate") & (obs.period < "2024-Q1") & obs.value.notna()].sort_values("observation_id")
    pick.append(old.iloc[rng.randrange(len(old))])
    rows = []
    for o in pick:
        m = man[o.source_id]
        rows.append(dict(obs=o, url=m.canonical_url, snap=m.snapshot_id))
    return rows


def stat_sheet() -> str:
    lines = ["# Statistical spot-check sheet (blank form)", "",
             "**Status: blank form, as generated on 30 Oct 2026; it holds no verdicts.** The owner recorded a decision on all 30 source checks (16 passage, 14 statistical) on 1 Nov 2026, after AI pre-review: AI-drafted and owner-confirmed; one reviewer, not independent inter-rater evidence. Result: `docs/human-review/owner-review-final-summary.md`. Open the dataset page, find the quarter, compare with 'Our value'. "
             "Fill the table at the bottom. Rows were drawn with a fixed seed (`data/review.py`, seed %d): at least two per approved dataset, "
             "four from other datasets, one '-' (null) cell and one pre-scope period." % SEED, "",
             "| # | Dataset | Period | Dimension | Our value | Unit | Our CSV locator | Observation id | Publisher page |", "|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(_stat_rows(), 1):
        o = r["obs"]
        v = "null (" + str(o.missing_reason) + ")" if pd.isna(o.value) else f"{o.value:g}"
        lines.append(f"| {i} | `{o.source_id}` | {o.period} | {o.dimension or '-'} | {v} | {o.unit} | {o.source_locator} | `{o.observation_id}` | [view]({r['url']}) |")
    lines += ["", "## Reviewer results", "", HEAD.rstrip()]
    lines += [f"| {i} |  |  |  |  |" for i in range(1, len(_stat_rows()) + 1)]
    return "\n".join(lines) + "\n"


def _passages() -> list[dict]:
    rng = random.Random(SEED)
    out = []
    for sid in REPORTS:
        rows = [json.loads(x) for x in (paths.PASSAGES / f"{sid}.jsonl").read_text().splitlines()]
        ok = [r for r in rows if r["quality_flag"] == "ok" and len(r["text"]) > 200]
        tab = [r for r in rows if r["quality_flag"] == "table_unreliable" and len(r["text"]) > 100]
        out += rng.sample(ok, 2) + rng.sample(tab, 1)
    for sid in ["mom-2026-q2-advance", "mom-2026-q2-final-release", "mom-2025-q3-advance", "mom-2025-q3-final-release"]:
        rows = [json.loads(x) for x in (paths.PASSAGES / f"{sid}.jsonl").read_text().splitlines()]
        ok = [r for r in rows if r["quality_flag"] == "ok" and len(r["text"]) > 150]
        out.append(rng.choice(ok))
    return out


def passage_sheets() -> tuple[str, str]:
    ps = _passages()
    pub = ["# Passage extraction spot-check sheet (blank form)", "",
           "**Status: blank form, as generated on 30 Oct 2026; it holds no verdicts.** The owner recorded a decision on all 30 source checks (16 passage, 14 statistical) on 1 Nov 2026, after AI pre-review: AI-drafted and owner-confirmed; one reviewer, not independent inter-rater evidence. Result: `docs/human-review/owner-review-final-summary.md`. For each row open the source document at the locator and check that the extracted text "
           "matches the page (words, numbers, units, nothing from another column or page). Extracted MOM text is not committed (rights); "
           "the owner has a local reading aid in `private/review/passage-text.md`. Rows: 2 narrative + 1 table passage per report, plus 4 HTML releases.", "",
           "| # | Source | Locator | Flag | Passage id | Original document |", "|---|---|---|---|---|---|"]
    priv = ["# Local reading aid: passage text (do not commit)", ""]
    for i, p in enumerate(ps, 1):
        pub.append(f"| {i} | `{p['source_id']}` | {p['locator']} | {p['quality_flag']} | `{p['passage_id']}` | [link]({p['original_url']}) |")
        priv += [f"## {i}. {p['source_id']} {p['locator']} ({p['quality_flag']})", "", p["text"], ""]
    pub += ["", "## Reviewer results", "", HEAD.rstrip()] + [f"| {i} |  |  |  |  |" for i in range(1, len(ps) + 1)]
    return "\n".join(pub) + "\n", "\n".join(priv)


def run() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    PRIV.mkdir(parents=True, exist_ok=True)
    (OUT / "statistical-spot-check.md").write_text(stat_sheet())
    pub, priv = passage_sheets()
    (OUT / "passage-spot-check.md").write_text(pub)
    (PRIV / "passage-text.md").write_text(priv)
    print("wrote", paths.rel(OUT / "statistical-spot-check.md"), paths.rel(OUT / "passage-spot-check.md"))
