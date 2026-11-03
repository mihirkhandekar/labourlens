"""Invariant checks over the manifest, observations, passages and packaging.

Each check returns pass / warn / fail with a concrete detail string. `warn` marks a real, documented
data characteristic (for example publisher '-' markers); `fail` blocks the build exit code.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pandas as pd

from labourlens import paths
from labourlens.data import catalog, raw_store
from labourlens.models import sha256_hex

SCOPE_LO, SCOPE_HI = catalog.ANSWER_SCOPE_START, catalog.ANSWER_SCOPE_END


def _check(name: str, ok: bool, detail: str, *, warn: bool = False) -> dict[str, Any]:
    return {"name": name, "status": "pass" if ok else ("warn" if warn else "fail"), "detail": detail}


def _quarters(first: str, last: str) -> list[str]:
    y, q = int(first[:4]), int(first[-1])
    ly, lq = int(last[:4]), int(last[-1])
    out = []
    while (y, q) <= (ly, lq):
        out.append(f"{y}-Q{q}")
        q += 1
        if q == 5:
            y, q = y + 1, 1
    return out


def check_manifest() -> list[dict]:
    out: list[dict] = []
    m = raw_store.load_manifest()
    wanted = [d["source_id"] for d in catalog.datasets()] + [d["source_id"] for d in catalog.documents()]
    missing = [s for s in wanted if s not in m]
    out.append(_check("manifest.all_sources_present", not missing, f"{len(wanted)} catalogued, missing={missing}"))
    bad_status = [s for s in wanted if s in m and m[s].retrieval_status != "ok"]
    out.append(_check("manifest.all_retrievals_ok", not bad_status, f"not ok: {bad_status}"))
    incomplete, mismatched, local_only_absent = [], [], []
    for s in wanted:
        e = m.get(s)
        if not e or e.retrieval_status != "ok":
            continue
        if not (e.sha256 and e.byte_count and e.retrieval_utc and e.snapshot_id and e.mime_type is not None):
            incomplete.append(s)
        p = paths.ROOT / (e.raw_path or "")
        if not p.exists():
            if e.redistribution_policy != "commit_raw":
                local_only_absent.append(s)  # not committed by design; absent in a fresh clone
            else:
                mismatched.append((s, "file missing"))
        else:
            data = p.read_bytes()
            if sha256_hex(data) != e.sha256 or len(data) != e.byte_count:
                mismatched.append((s, "hash/size mismatch"))
    out.append(_check("manifest.required_fields_present", not incomplete, f"incomplete: {incomplete}"))
    out.append(_check("manifest.raw_files_match_sha256", not mismatched,
                      f"mismatches: {mismatched}; local-only, not present (not checked): {local_only_absent}"))
    text = (paths.MANIFESTS / "manifest.json").read_text() + (paths.MANIFESTS / "manifest_history.jsonl").read_text()
    leaked = [t for t in ("X-Amz", "Signature=", "Security-Token") if t in text]
    out.append(_check("manifest.no_signed_url_material", not leaked, f"found markers: {leaked}"))
    unresolved = [s for s in wanted if s in m and m[s].rights_status == "unresolved"]
    out.append(_check("rights.unresolved_sources_listed", not unresolved,
                      f"{len(unresolved)} sources still have unresolved rights (kept local-only): {unresolved}", warn=True))
    return out


def check_datasets(obs: pd.DataFrame, quarantine: pd.DataFrame, per_source: dict) -> list[dict]:
    out: list[dict] = []
    for d in catalog.datasets():
        sid = d["source_id"]
        ps = per_source.get(sid, {})
        if ps.get("status") != "ok":
            out.append(_check(f"dataset.{sid}.contract", False, f"{ps}"))
            continue
        spec = catalog.adapter_spec(sid)
        o = obs[obs.source_id == sid]
        nq = int((quarantine.source_id == sid).sum()) if len(quarantine) else 0
        out.append(_check(f"dataset.{sid}.no_quarantined_rows", nq == 0, f"quarantined={nq}"))
        # coverage endpoints
        have = o[o.value.notna()].period
        out.append(_check(f"dataset.{sid}.first_last_period",
                          have.min() == spec["expected_first_period"] or sid == "employment_change_by_sector",
                          f"first={have.min()} expected={spec['expected_first_period']}; last={have.max()} expected={spec['expected_last_period']}")
                   if have.max() == spec["expected_last_period"] else
                   _check(f"dataset.{sid}.first_last_period", False, f"last={have.max()} expected={spec['expected_last_period']}"))
        # duplicates
        key = ["indicator_id", "population", "adjustment", "sector_path", "dimension", "period"]
        dups = int(o.duplicated(subset=key).sum())
        out.append(_check(f"dataset.{sid}.no_duplicate_keys", dups == 0, f"duplicates={dups}"))
        # unique IDs
        out.append(_check(f"dataset.{sid}.observation_ids_unique", o.observation_id.is_unique, ""))
        # plausible range
        bad = 0
        for m in spec["measures"]:
            lo, hi = m["plausible_range"]
            mm = o if m["column"] == "*" else o[(o.indicator_id == m["indicator_id"]) & (o.adjustment == m["adjustment"])]
            v = mm.value.dropna()
            if m["column"] == "*":
                total = mm[mm.sector_level == 0].value.dropna()
                bad += int(((total < lo) | (total > hi)).sum())
            else:
                bad += int(((v < lo) | (v > hi)).sum())
        out.append(_check(f"dataset.{sid}.values_in_plausible_range", bad == 0, f"outside={bad}"))
        # in-scope completeness: every series x every quarter present as a row
        scope = o[o.in_answer_scope]
        last = min(SCOPE_HI, spec["expected_last_period"])  # a source that ends before the scope end is declared in its spec
        expected_q = _quarters(SCOPE_LO, last)
        grp_cols = ["indicator_id", "population", "adjustment", "sector_path", "dimension"]
        incomplete = [g for g, df in scope.groupby(grp_cols) if sorted(df.period.unique()) != expected_q]
        out.append(_check(f"dataset.{sid}.in_scope_rows_cover_declared_quarters", not incomplete, f"quarters expected {SCOPE_LO} to {last}; series with gaps={len(incomplete)}"))
        miss = scope[scope.value.isna()]
        out.append(_check(f"dataset.{sid}.in_scope_values_present", len(miss) == 0,
                          f"{len(miss)} of {len(scope)} in-scope cells have no published number "
                          f"(reasons: {dict(miss.missing_reason.value_counts())})", warn=True))
    return out


def check_hierarchies(obs: pd.DataFrame) -> list[dict]:
    out: list[dict] = []
    # Sector table: children should sum to the parent within rounding (source rounds to 100 persons).
    spec = catalog.adapter_spec("employment_change_by_sector")
    tol_child = spec["sum_tolerance_per_child"]
    # Cells the publisher prints as '-' are missing, not zero: a parent whose own or any child's cell is missing has an indeterminate sum
    # and is skipped and counted (as in the industry check below). The 2020 sheet has such cells under Other Services Industries.
    s = obs[(obs.source_id == "employment_change_by_sector") & obs.in_answer_scope]
    worst, n_checked, skipped, over = 0.0, 0, 0, []
    for period, g in s.groupby("period"):
        by_path = g.set_index("sector_path").value
        for path in by_path.index:
            kids = [p for p in by_path.index if p.startswith(path + " > ") and p.count(" > ") == path.count(" > ") + 1]
            if not kids:
                continue
            if by_path[path] != by_path[path] or by_path[kids].isna().any():
                skipped += 1
                continue
            diff = abs(by_path[path] - by_path[kids].sum())
            n_checked += 1
            worst = max(worst, diff)
            if diff > tol_child * len(kids):
                over.append((period, path, float(diff)))
    out.append(_check("sector.children_sum_to_parent_within_rounding", not over,
                      f"checked={n_checked} parent/period pairs, skipped_due_to_dash_cells={skipped}, max_abs_diff={worst:.0f} persons, tolerance={tol_child}/child, exceeded={over[:3]}"))
    # Industry table: children sum to parent; '-' cells make some sums indeterminate, those are skipped and counted.
    r = obs[(obs.source_id == "retrenched_by_industry") & obs.in_answer_scope]
    spec2 = catalog.adapter_spec("retrenched_by_industry")
    parents = {k: v["parent"] for k, v in spec2["industry_hierarchy"].items()}
    unknown = sorted(set(r.dimension) - set(parents))
    out.append(_check("industry.in_scope_names_all_in_hierarchy", not unknown, f"unknown industries={unknown}"))
    checked = skipped = 0
    worst = 0.0
    over = []
    for period, g in r.groupby("period"):
        val = g.set_index("dimension").value
        for par in set(p for p in parents.values() if p):
            kids = [k for k, p in parents.items() if p == par and k in val.index]
            if val[par] != val[par] or any(val[k] != val[k] for k in kids):  # NaN present -> indeterminate
                skipped += 1
                continue
            diff = abs(val[par] - val[kids].sum())
            checked += 1
            worst = max(worst, diff)
            if diff > 10 * (len(kids) + 1):
                over.append((period, par, float(diff)))
    out.append(_check("industry.children_sum_to_parent_within_rounding", not over,
                      f"checked={checked}, skipped_due_to_dash_cells={skipped}, max_abs_diff={worst:.0f}, exceeded={over[:3]}"))
    return out


def check_derived(der: dict) -> list[dict]:
    s = der["summary"]
    c = s["retrenchment_components_minus_total"]
    v = s["vacancy_to_unemployed_ratio_recomputed"]
    return [
        _check("derived.retrenchment_parts_equal_total", c["max_abs_diff"] is not None and c["max_abs_diff"] <= 20,
               f"in-scope quarters={c['n']}, max |perm+term-total|={c['max_abs_diff']} persons (source rounds to 10)"),
        _check("derived.vacancy_ratio_recomputed_vs_published", v["max_abs_diff"] is not None and v["max_abs_diff"] <= 0.15,
               f"in-scope quarters={v['n']}, max abs diff={v['max_abs_diff']}, mean={v['mean_abs_diff']} "
               "(different surveys; a gap is expected, a large one would signal a definition problem)", warn=True),
    ]


def check_passages(passages: list, pstats: list[dict]) -> list[dict]:
    out: list[dict] = []
    ids = [p.passage_id for p in passages]
    out.append(_check("passages.ids_unique", len(ids) == len(set(ids)), f"{len(ids)} passages"))
    out.append(_check("passages.non_empty_text", all(p.text.strip() for p in passages), ""))
    pdf_bad = [p.passage_id for p in passages if p.page_number is None and p.locator.startswith("p.")]
    out.append(_check("passages.pdf_have_page_numbers", not pdf_bad, f"bad={pdf_bad[:3]}"))
    html_bad = [p.passage_id for p in passages if p.page_number is None and not p.locator.startswith("section:")]
    out.append(_check("passages.html_have_section_locator", not html_bad, f"bad={html_bad[:3]}"))
    not_ok = [s["source_id"] for s in pstats if s.get("status") != "ok"]
    out.append(_check("passages.every_document_extracted", not not_ok, f"not extracted: {not_ok}"))
    mism = [s["source_id"] for s in pstats if "date_matches_catalog" in s and not s["date_matches_catalog"]]
    out.append(_check("passages.html_date_matches_catalog", not mism, f"mismatched publication dates: {mism}"))
    flags = pd.Series([p.quality_flag for p in passages]).value_counts().to_dict()
    out.append(_check("passages.quality_flag_distribution", True, f"{flags}"))
    empty_pages = []
    for s in pstats:
        if "pages" in s and s["passages"] < 0.5 * s["pages"]:
            empty_pages.append((s["source_id"], s["pages"], s["passages"]))
    out.append(_check("passages.low_yield_documents", not empty_pages,
                      f"documents with fewer than 0.5 passages per page (text may be in images/tables): {empty_pages}", warn=True))
    return out


ALLOW_FILE = paths.SPECS / "injection_scan_allow.txt"
TEXT_COLUMNS = ["dimension", "title", "indicator_id", "missing_reason", "population", "adjustment"]


def scan_injection(passages: list, obs: pd.DataFrame) -> dict:
    """Ingestion-time scan: instruction-like text or hidden characters in report passages or in text fields of statistics rows.
    Heuristic (labourlens.security.guards): it catches common phrasing and hidden characters, not paraphrase. A flagged item is
    reviewed by a person; reviewed false positives are listed by id in specs/injection_scan_allow.txt (one id per line, '#' comments)."""
    from labourlens.security.guards import injection_flags

    allow = set()
    if ALLOW_FILE.exists():
        allow = {ln.split("#")[0].strip() for ln in ALLOW_FILE.read_text().splitlines() if ln.split("#")[0].strip()}
    hits = []
    for ps in passages:
        flags = injection_flags(ps.text)
        if flags and ps.passage_id not in allow:
            hits.append({"kind": "passage", "id": ps.passage_id, "flags": flags})
    if len(obs):
        cols = [c for c in TEXT_COLUMNS if c in obs.columns]
        seen: dict[str, list[str]] = {}
        for c in cols:
            for v in obs[c].dropna().astype(str).unique():
                flags = injection_flags(v)
                if flags:
                    seen.setdefault(f"{c}:{v}", flags)
        for k, flags in seen.items():
            if f"obs:{k}" not in allow:
                hits.append({"kind": "observation_field", "id": k, "flags": flags})
    return {"passages_scanned": len(passages), "text_values_scanned": int(sum(obs[c].nunique() for c in TEXT_COLUMNS if c in obs.columns)) if len(obs) else 0, "hits": hits}


def check_injection(passages: list, obs: pd.DataFrame) -> list[dict]:
    r = scan_injection(passages, obs)
    shown = [f"{h['kind']}:{h['id']}:{','.join(h['flags'])}" for h in r["hits"][:5]]
    return [_check("security.no_instruction_like_text_in_sources", not r["hits"],
                   f"scanned {r['passages_scanned']} passages and {r['text_values_scanned']} distinct text values; hits={len(r['hits'])} {shown}")]


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=paths.ROOT, capture_output=True, text=True, check=False).stdout


def check_packaging() -> list[dict]:
    """Rights-aware packaging: nothing from MOM reports may be tracked or untracked-but-unignored."""
    out: list[dict] = []
    visible = (_git("ls-files") + _git("ls-files", "--others", "--exclude-standard")).splitlines()
    bad = [f for f in visible if f.lower().endswith(".pdf") and not f.startswith("reference/")]
    # the assessment PDF is ignored by .gitignore; any other PDF in the working tree must be ignored too
    out.append(_check("packaging.no_pdf_visible_to_git", not bad, f"visible PDFs: {bad}"))
    leak = [f for f in visible if f.startswith(("data/raw/", "data/passages/", "study/", "private/"))]
    out.append(_check("packaging.private_paths_ignored", not leak, f"visible private paths: {leak[:5]}"))
    snap = [f for f in visible if f.startswith("data/snapshots/")]
    non_csv = [f for f in snap if not (f.endswith(".csv") or f.endswith(".metadata.json"))]
    out.append(_check("packaging.snapshots_only_open_licence_csv_and_metadata", not non_csv, f"unexpected: {non_csv[:5]}"))
    return out


def run_all(obs, quarantine, passages, pstats, per_source, der, rec) -> dict:
    checks = []
    checks += check_manifest()
    checks += check_datasets(obs, quarantine, per_source)
    checks += check_hierarchies(obs)
    checks += check_derived(der)
    checks += check_passages(passages, pstats)
    checks += check_injection(passages, obs)
    checks += check_packaging()
    # reconciliation presence for the documented revision example
    q2 = next((q for q in rec["quarters"] if q["period"] == "2026-Q2"), None)
    ok = bool(q2 and q2["advance"] and q2["final"] and q2["dataset_total"])
    detail = "missing advance/final/dataset value for 2026-Q2" if not ok else (
        f"advance={q2['advance']['value']} ({q2['advance']['publication_date']}), final={q2['final']['value']} "
        f"({q2['final']['publication_date']}), dataset={q2['dataset_total']['value']}")
    checks.append(_check("reconcile.q2_2026_three_values_present", ok, detail))
    counts = pd.Series([c["status"] for c in checks]).value_counts().to_dict()
    return {"summary": counts, "checks": checks}


def write_markdown(report: dict, out: Path) -> None:
    lines = ["# Data quality report (generated)", "",
             "Generated by `labourlens build`. Machine-readable twin: `validation.json`.", "",
             f"Summary: {report['summary']}", "", "| Status | Check | Detail |", "|---|---|---|"]
    for c in report["checks"]:
        d = c["detail"].replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {c['status']} | `{c['name']}` | {d} |")
    out.write_text("\n".join(lines) + "\n")
