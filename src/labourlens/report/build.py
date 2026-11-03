"""Build an offline report from committed, explicitly curated artifacts.

Never import application pipelines here. In particular, saved answers, retrieved
passages, judge notes, prompts, and tool payloads are not presentation material.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
from urllib.parse import urlparse

from labourlens.data import catalog  # the answer-scope constants only; no pipeline code


_SCOPE = (catalog.ANSWER_SCOPE_START, catalog.ANSWER_SCOPE_END)
_TOKEN = re.compile(r"[A-Za-z0-9_@.+:=/() -]{1,96}\Z")
_KEY = re.compile(r"[A-Za-z0-9_@.+:=/-]{1,96}\Z")
_LABELS = {
    "unemployment_resident_sa": "Resident unemployment",
    "unemployment_overall_sa": "Overall unemployment",
    "unemployment_citizen_sa": "Citizen unemployment",
    "job_vacancies": "Job vacancies",
    "retrenched_employees": "Retrenched employees",
    "vacancy_ratio": "Vacancies per unemployed person",
    "reentry_6m": "Re-employment rate, 6 months after retrenchment",
}


_HELDOUT_V2_PAIRED = "experiments/heldout-v2/paired.json"
_HELDOUT_V2_ERRORS = "experiments/heldout-v2/error-analysis.json"
_HELDOUT_V31_PAIRED = "experiments/heldout-v2/paired-v3.1.json"
_FINAL_FRESH_PAIRED = "experiments/heldout-v2/paired-final.json"
_FINAL_DEV_PAIRED = "experiments/eval/paired-dev-final.txt"
_FINAL_REGISTERED_PAIRED = "experiments/heldout/paired-final.txt"
_FINAL_EVAL = re.compile(r"experiments/eval/agent-(?:dev|heldout)-FIN(?:2)?(?:V2)?-(?:r3|hybrid)/gpt-(?:6|5\.6)-luna\.metrics\.json")
_HELDOUT_V2_FILES = {_HELDOUT_V2_PAIRED, _HELDOUT_V2_ERRORS, _HELDOUT_V31_PAIRED, _FINAL_FRESH_PAIRED}
# Tool set v2 (D-046/D-048): separately keyed, never merged into the registered or X2 rows.
_TOOLFIX_CRITERIA = "experiments/tool-fix/criteria.json"
_TOOLFIX_PAIRED = {"toolset": "experiments/heldout-v2/paired-postfix-toolset.json", "r3_vs_hybrid": "experiments/heldout-v2/paired-postfix-r3-vs-hybrid.json"}
_TOOLFIX_EVAL = re.compile(r"experiments/eval/agent-(?:dev-X3|heldout-V2post-(?:r3|hybrid))/gpt-(?:6|5\.6)-luna\.(?:metrics\.json|cases\.jsonl)")
_E2EFIX_DIR = "experiments/threats/m7-e2efix-20261031/"
_E2EFIX_EXPERIMENT = "m7-e2efix-20261031"
_SECOND_JUDGE_SUMMARY = "experiments/xjudge/sonnet55-FIN-s60-b-20261102/summary.json"


def _corpus_version(path: str) -> str:
    """Explicit corpus label: v2 only for the separately labelled X1 artifacts, v3 only for dev X2."""
    if "/dev-R-V31" in path:
        return "v3.1"
    if "/agent-dev-X2/" in path:
        return "v3"
    return "v2" if re.search(r"/(?:agent-dev-X1|agent-heldout-X-(?:r3|hybrid)|extraction-v2-X1)/", path) else "v1"


def _label(value: object) -> str | None:
    if isinstance(value, str) and _TOKEN.fullmatch(value) and len(value.split()) <= 6:
        return value
    return None


def _number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _numeric(value: object, depth: int = 0) -> object:
    """Copy measurements, never arbitrary text or payload fields."""
    if depth > 6:
        return None
    if _number(value) or isinstance(value, bool):
        return value
    if isinstance(value, dict):
        result = {}
        for key, child in value.items():
            if isinstance(key, str) and _KEY.fullmatch(key):
                clean = _numeric(child, depth + 1)
                if clean is not None and clean != {} and clean != []:
                    result[key] = clean
        return result
    if isinstance(value, list) and all(_number(item) for item in value):
        return value
    return None


def _selected(row: dict, names: tuple[str, ...]) -> dict:
    return {name: row[name] for name in names if _number(row.get(name)) or isinstance(row.get(name), bool)}


class _Artifacts:
    def __init__(self, root: Path):
        self.root = root
        self.commit = self._git("rev-parse", "HEAD").decode().strip()
        listed = self._git("ls-files", "-z", "--", "data/export", "experiments", "docs/mcp-demo-transcript.md", "docs/decisions.md", "docs/progress.md", "data/manifests")
        self.paths = sorted(path for path in listed.decode().split("\0") if path and self._allowed(path))
        self.provenance: dict[str, dict] = {}
        self.cache: dict[str, object] = {}

    def _git(self, *args: str) -> bytes:
        return subprocess.check_output(["git", *args], cwd=self.root, stderr=subprocess.DEVNULL)

    @staticmethod
    def _allowed(path: str) -> bool:
        p = Path(path)
        if ".." in p.parts:
            return False
        # Development comparisons plus only the registered held-out models.
        # Raw held-out runs and extra/unregistered models stay private.
        if path in {_FINAL_DEV_PAIRED, "experiments/eval/final-mean.json"}:
            return True
        if path.startswith("experiments/eval/"):
            development = re.fullmatch(r"experiments/eval/agent-dev-A[1-5]/[^/]+", path)
            # Labelled non-registered runs (corpus v2 X1, corpus v3 X2): registered luna models only, no raw/judge files.
            heldout = re.fullmatch(
                r"experiments/eval/agent-(?:heldout-H|heldout-X|dev-X[12])(?:-(?:r3|hybrid))?/gpt-(?:6|5\.6)-luna\.(?:metrics\.json|cases\.jsonl)",
                path,
            ) if re.search(r"/agent-dev-X[12]/", path) or re.search(r"/agent-heldout-(?:H|X)-(?:r3|hybrid)/", path) else None
            # Signed held-out v2 (corpus v3): registered luna models only; kept out of the registered rows (see _heldout_v2).
            if heldout is None:
                heldout = re.fullmatch(r"experiments/eval/agent-heldout-V2-(?:r3|hybrid)/gpt-(?:6|5\.6)-luna\.(?:metrics\.json|cases\.jsonl)", path)
            if heldout is None:
                # Fresh-set re-run on corpus v3.1: metrics only, kept in its own section (see _heldout_v31).
                heldout = re.fullmatch(r"experiments/eval/agent-heldout-V31-(?:r3|hybrid)/gpt-(?:6|5\.6)-luna\.metrics\.json", path)
            if heldout is None:
                heldout = _FINAL_EVAL.fullmatch(path)
            if heldout is None:
                heldout = _TOOLFIX_EVAL.fullmatch(path)
            if not (development or heldout):
                return False
        if path.startswith("experiments/heldout-v2/") and path not in _HELDOUT_V2_FILES | set(_TOOLFIX_PAIRED.values()):
            # Held-out v2: the paired result and the id-only error analysis; review exports and audits stay out.
            return False
        if path.startswith("experiments/runs/agent-"):
            if not re.fullmatch(r"experiments/runs/agent-dev-A[1-5]/[^/]+", path):
                return False
        if path.startswith(_E2EFIX_DIR):
            # Threat run m7-e2efix: aggregate metrics and the summary only; raw verdicts stay private.
            if not re.fullmatch(_E2EFIX_DIR + r"(?:SUMMARY\.md|runs/gpt-(?:6|5\.6)-luna(?:\+naive)?\.metrics\.json)", path):
                return False
        return (
            (p.parent.as_posix() == "data/export" and p.suffix == ".json")
            or (path.startswith("experiments/") and p.suffix in {".json", ".jsonl", ".md"})
            or path in {"docs/mcp-demo-transcript.md", "docs/decisions.md", "docs/progress.md"}
            or re.fullmatch(r"experiments/heldout/paired(?:-v3\.[234]|-corpus-v2|-final)?\.txt", path) is not None
            or (path.startswith("data/manifests/") and p.suffix in {".json", ".jsonl"})
        )

    def load(self, path: str) -> object:
        if path in self.cache:
            return self.cache[path]
        entry = {"path": path, "status": "missing"}
        value: object = None
        if path in self.paths:
            try:
                # A tracked working-tree modification is not committed evidence.
                raw = self._git("show", f"{self.commit}:{path}")
                entry["sha256"] = hashlib.sha256(raw).hexdigest()
                text = raw.decode("utf-8")
                if path.endswith(".jsonl"):
                    value = [json.loads(line) for line in text.splitlines() if line.strip()]
                elif path.endswith(".json"):
                    value = json.loads(text)
                else:
                    value = text
                entry["status"] = "available"
            except (subprocess.CalledProcessError, UnicodeError, ValueError):
                entry["status"] = "unavailable"
        self.provenance[path] = entry
        self.cache[path] = value
        return value

    def mapping(self, path: str) -> dict:
        value = self.load(path)
        return value if isinstance(value, dict) else {}


def _scanner_summary(artifacts: _Artifacts) -> dict:
    """Project aggregate detector metrics only; never publish fixture text or predictions."""
    result = {}
    for label, name in (("before", "v2-baseline-test"), ("after", "v2-selected-test")):
        raw = artifacts.mapping(f"experiments/scanner/{name}/metrics.json").get("metrics", {})
        if not raw:
            continue
        def rates(record: dict) -> dict:
            return {key: record.get(key) for key in ("count", "n", "rate", "wilson95")}
        result[label] = {
            "recall": rates(raw.get("recall", {})),
            "false_positive_rate": rates(raw.get("false_positive_rate", {})),
            "by_class": {key: {metric: rates(value.get(metric, {})) for metric in ("recall", "false_positive_rate")}
                         for key, value in raw.get("by_class", {}).items()},
        }
    return result


def _section(summary: str, rows: list, paths: list[str], **extra: object) -> dict:
    return {"status": "available" if rows else "missing", "summary": summary,
            "metrics": {}, "rows": rows, "provenance": sorted(set(paths)), **extra}


def _experiments(artifacts: _Artifacts, prefix: str) -> tuple[list, list]:
    rows, paths = [], []
    for path in artifacts.paths:
        if path.startswith(prefix) and path.endswith(".metrics.json"):
            if prefix == "experiments/eval/" and ("/agent-heldout-V2-" in path or "/agent-heldout-V31-" in path or _FINAL_EVAL.fullmatch(path) or _TOOLFIX_EVAL.fullmatch(path)):
                continue  # reported only in the separately keyed evaluation.heldout_v2 and evaluation.tool_set_v2 sections
            data = artifacts.mapping(path)
            metrics = _numeric(data.get("metrics", data))
            if not metrics:
                continue
            row = {"id": path.removesuffix(".metrics.json"), "metrics": metrics, "provenance": [path]}
            if prefix in {"experiments/eval/", "experiments/runs/dev-", "experiments/runs/extraction-v2-X1/dev-"}:
                row["corpus_version"] = _corpus_version(path)
                if row["corpus_version"] == "v2":
                    row["gold_version"] = "v3.6 (evidence-ID migration only)"
                elif row["corpus_version"] == "v3":
                    # Dev X2: a regression check of the served system, several factors changed at once.
                    row.update({"gold_version": "v3.6", "regression_check": True, "crosscheck": True})
            if prefix == _E2EFIX_DIR + "runs/":
                row.update({"experiment": _E2EFIX_EXPERIMENT, "corpus_version": "v3", "crosscheck": True})
            label = _label(data.get("label", data.get("model", Path(path).name.removesuffix(".metrics.json"))))
            if label:
                row["label"] = label
            config = data.get("config")
            if isinstance(config, dict):
                row["configuration"] = _numeric(config)
                method = _label(config.get("retriever"))
                if method:
                    row["method"] = method
            strata = _numeric(data.get("by_family", data.get("by_category", {})))
            if strata:
                row["strata"] = strata
            if prefix == "experiments/eval/":
                if "/agent-heldout-" in path and not _Artifacts._allowed(path):
                    continue
                row["split"] = "heldout" if "/agent-heldout-" in path else "dev"
                if "/agent-heldout-X-" in path:
                    # Post-freeze diagnostic on corpus v2: the name says heldout, the status is not registered held-out evidence.
                    row.update({"diagnostic": True, "registered": False})
                elif "/agent-heldout-H-" in path:
                    row["registered"] = True
                source = data.get("provenance", {})
                if isinstance(source, dict):
                    fingerprint = _selected(source, ("eligible_n", "available_n"))
                    for key in ("gold_sha256", "git_head", "price_table_sha256"):
                        value = source.get(key)
                        if isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", value):
                            fingerprint[key] = value
                    prompts = source.get("prompt_sha256", {})
                    if isinstance(prompts, dict):
                        fingerprint["prompt_sha256"] = {
                            key: value for key, value in prompts.items()
                            if _label(key) and isinstance(value, str)
                            and re.fullmatch(r"[0-9a-f]{64}", value)
                        }
                    if fingerprint:
                        row["scoring_provenance"] = fingerprint
                # The legacy "answers" name uses all scored cases, not answers.
                if "cases_with_ungrounded_numbers" not in metrics and "answers_with_ungrounded_numbers" in metrics:
                    metrics["cases_with_ungrounded_numbers"] = metrics["answers_with_ungrounded_numbers"]
                judge = _label(data.get("judge"))
                if judge:
                    row["judge"] = judge
                # Legacy aggregates omit the fact denominator. Project only its
                # numeric total from the matching committed case records.
                case_path = path.removesuffix(".metrics.json") + ".cases.jsonl"
                if case_path in artifacts.paths:
                    cases = artifacts.load(case_path)
                    if isinstance(cases, list):
                        answered = [case for case in cases if isinstance(case, dict)
                                    and _number(case.get("claims_supported"))]
                        fact_counts = [case["facts_total"] for case in answered
                                       if _number(case.get("facts_total"))]
                        if fact_counts:
                            row["denominators"] = {"fact_coverage": sum(fact_counts)}
                            row["provenance"].append(case_path)
                            paths.append(case_path)
            rows.append(row)
            paths.append(path)
    return rows, paths


def _answer_costs(artifacts: _Artifacts, rows: list) -> None:
    """Read only numeric columns from recorded experiment tables."""
    for path in artifacts.paths:
        if not path.startswith("experiments/runs/answer-") or not path.endswith("-SUMMARY.md"):
            continue
        text = artifacts.load(path)
        if not isinstance(text, str):
            continue
        columns = None
        experiment = Path(path).name.removesuffix("-SUMMARY.md")
        for line in text.splitlines():
            if not line.startswith("|"):
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if cells and cells[0] == "config":
                columns = cells
                continue
            if columns is None or len(cells) != len(columns):
                continue
            label = _label(cells[0])
            if not label:
                continue
            for row in rows:
                if row.get("label") != label or Path(row["id"]).parent.name != experiment:
                    continue
                for name in ("cost_per_case_usd",):
                    if name not in columns:
                        continue
                    value = cells[columns.index(name)]
                    if re.fullmatch(r"\d+(?:\.\d+)?", value):
                        row["metrics"][name] = float(value)
                        row["provenance"] = sorted(set(row["provenance"] + [path]))


def _reconciliation(artifacts: _Artifacts) -> dict:
    path = "data/export/reconciliation.json"
    rows = []
    for quarter in artifacts.mapping(path).get("quarters", []):
        if not isinstance(quarter, dict):
            continue
        period = quarter.get("period", "")
        if not isinstance(period, str) or not re.fullmatch(r"\d{4}-Q[1-4]", period):
            continue
        row = {"period": period, "unit": "persons", "provenance": [path]}
        row.update(_selected(quarter, ("dataset_minus_final", "final_minus_advance")))
        for stage in ("advance", "final", "dataset_total"):
            source = quarter.get(stage)
            if not isinstance(source, dict) or not _number(source.get("value")):
                continue
            projected = {"value": source["value"]}
            for key in ("passage_id", "observation_id", "source_id", "publication_date", "snapshot_id"):
                if _label(source.get(key)):
                    projected[key] = source[key]
            row[stage] = projected
        rows.append(row)
    return _section("Advance and final releases differ by revision; dataset totals differ by population basis.", rows, [path])


def _sources(artifacts: _Artifacts) -> dict:
    path = "data/export/sources.json"
    sources = artifacts.mapping(path).get("sources", [])
    provenance = [path]
    if not isinstance(sources, list) or not sources:
        path = "data/manifests/manifest.json"
        sources = artifacts.mapping(path).get("entries", [])
        provenance.append(path)
    rows = []
    for source in sources if isinstance(sources, list) else []:
        if not isinstance(source, dict):
            continue
        row = {}
        for key in ("source_id", "publisher", "publication_date", "release_stage", "licence", "licence_id", "rights_status", "redistribution", "sha256", "snapshot_id", "type", "source_type"):
            value = _label(source.get(key))
            if value:
                row[key] = value
        url = source.get("url", source.get("canonical_url"))
        if isinstance(url, str):
            parsed = urlparse(url)
            if parsed.scheme == "https" and parsed.hostname and (parsed.hostname == "gov.sg" or parsed.hostname.endswith(".gov.sg")) and not parsed.query and not parsed.fragment and not parsed.username:
                row["url"] = url
        if row.get("source_id"):
            rows.append(row)
    counts = Counter(row.get("type", row.get("source_type", "unknown")) for row in rows)
    metrics = {"sources": len(rows), "by_type": dict(counts)}
    observations = _observations(artifacts)
    if observations is not None:
        metrics.update(observations.attrs["report_metrics"])
        provenance.append(_OBSERVATIONS)
    return _section("Metadata for official sources.", rows, provenance, metrics=metrics)


def _charts(artifacts: _Artifacts) -> list:
    path = "data/export/series.json"
    series = artifacts.mapping(path).get("series", {})
    card_sources = {
        card["card_id"]: card["source_id"]
        for card in artifacts.mapping("data/export/kpis.json").get("cards", [])
        if isinstance(card, dict) and _label(card.get("card_id")) and _label(card.get("source_id"))
    }
    known_sources = {
        source["source_id"]
        for source in artifacts.mapping("data/export/sources.json").get("sources", [])
        if isinstance(source, dict) and _label(source.get("source_id"))
    }
    charts = []
    if not isinstance(series, dict):
        return charts
    for key, data in series.items():
        if not _label(key) or not isinstance(data, dict):
            continue
        points = []
        for point in data.get("points", []):
            if not isinstance(point, dict):
                continue
            period = point.get("period", "")
            if isinstance(period, str) and re.fullmatch(r"\d{4}-Q[1-4]", period) and _SCOPE[0] <= period <= _SCOPE[1] and _number(point.get("value")):
                clean = {"period": period, "value": point["value"]}
                if _label(point.get("observation_id")):
                    clean["observation_id"] = point["observation_id"]
                points.append(clean)
        if points:
            source_id = _label(data.get("source_id")) or card_sources.get(key)
            if source_id is None and key in known_sources:
                source_id = key
            charts.append({"id": key, "title": _LABELS.get(key, key.replace("_", " ")[:80]),
                           "unit": _label(data.get("unit")) or "unspecified",
                           "population": _label(data.get("population")),
                           "adjustment": _label(data.get("adjustment")),
                           "description": "Validated quarterly observations. Series definitions are kept apart.",
                           "points": sorted(points, key=lambda point: point["period"]),
                           "source_ids": [source_id] if source_id else [],
                           "provenance": [path] + (["data/export/kpis.json"] if key in card_sources else [])})
    return charts


def _summary(artifacts: _Artifacts) -> dict:
    path = "data/export/kpis.json"
    cards = []
    for card in artifacts.mapping(path).get("cards", []):
        if not isinstance(card, dict):
            continue
        row = _selected(card, ("value", "change"))
        for key in ("card_id", "source_id", "observation_id", "period", "unit", "change_unit", "population", "adjustment"):
            if _label(card.get(key)):
                row[key] = card[key]
        row["label"] = _LABELS.get(card.get("card_id"), _label(card.get("label")) or "Labour indicator")
        row["provenance"] = [path]
        if "value" in row:
            cards.append(row)
    return {"title": "LabourLens research workbench", "scope": list(_SCOPE), "cards": cards,
            "status": "available" if cards else "missing", "provenance": [path]}


def _eda(charts: list) -> dict:
    rows = []
    for chart in charts:
        points = chart["points"]
        if len(points) < 2:
            continue
        first, last = points[0], points[-1]
        rows.append({"id": chart["id"], "label": chart["title"], "unit": chart["unit"],
                     "period_from": first["period"], "period_to": last["period"],
                     "start": first["value"], "end": last["value"],
                     "change": round(last["value"] - first["value"], 8),
                     "minimum": min(p["value"] for p in points),
                     "maximum": max(p["value"] for p in points),
                     "observations": len(points), "provenance": chart["provenance"]})
    return _section("Change between first and last observation. No causal claim.", rows, ["data/export/series.json"])


def _agent_trace(artifacts: _Artifacts) -> tuple[list, list, dict]:
    """Tool-use trace rows from generation-time score files, with outcomes taken from the current rescored case files.

    The generation-time scores were computed against the gold of the day. The registered current outcomes are
    `experiments/eval/<exp>/<model>.cases.jsonl`, the same records behind the headline tables, so behaviour,
    validity, tool-error and ungrounded-number counts come only from those. A run with no current case file, or a
    case absent from it (dropped, or its question text changed after the run), is left out.
    """
    trace, paths, errors = [], [], Counter()
    fields = ("tool_calls", "rounds", "seconds", "cost_usd", "attempts", "prompt_tokens", "completion_tokens")
    for path in artifacts.paths:
        if not path.startswith("experiments/runs/agent-") or not path.endswith(".scores.jsonl"):
            continue
        records = artifacts.load(path)
        case_path = path.replace("experiments/runs/", "experiments/eval/", 1).removesuffix(".scores.jsonl") + ".cases.jsonl"
        current = artifacts.load(case_path) if case_path in artifacts.paths else None
        if not isinstance(records, list) or not isinstance(current, list):
            continue
        rescored = {c["case_id"]: c for c in current if isinstance(c, dict) and isinstance(c.get("case_id"), str)}
        paths += [path, case_path]
        for record in records:
            if not isinstance(record, dict) or record.get("case_id") not in rescored:
                continue
            now = rescored[record["case_id"]]
            row = {"run_id": path.removesuffix(".scores.jsonl"), **_selected(record, fields),
                   **_selected(now, ("tool_errors", "behavior_ok", "valid", "operational_failure"))}
            for key in ("case_id", "family"):
                if _label(record.get(key)):
                    row[key] = record[key]
            # Counts and tool names only: never call arguments or results.
            row["tools_used"] = [tool for tool in record.get("tools_used", []) if tool in {"get_series", "get_statistic", "search_reports", "calculate", "calculate_change", "calculate_from_text_values", "get_source", "compare_periods"}]
            trace.append(row)
            for key, source in (("tool_errors", "tool_errors"), ("operational_failure", "operational_failure"), ("n_ungrounded_numbers", "ungrounded_numbers")):
                value = now.get(source)
                if _number(value) or isinstance(value, bool):
                    errors[key] += value
            if now.get("behavior_ok") is False:
                errors["behavior_mismatch"] += 1
            if now.get("valid") is False:
                errors["invalid_output"] += 1
    return trace, paths, dict(errors)


def _mcp(artifacts: _Artifacts) -> dict:
    path = "docs/mcp-demo-transcript.md"
    text = artifacts.load(path)
    if not isinstance(text, str):
        return _section("No protocol transcript is committed.", [], [path])
    rows = []
    for label, key in (("median latency per call", "latency_p50_ms"), ("p95 latency per call", "latency_p95_ms")):
        match = re.search(r"\| " + re.escape(label) + r" \| ([\d.]+) ms \| ([\d.]+) ms \|", text)
        if match:
            rows.append({"metric": key, "direct": float(match[1]), "mcp": float(match[2]), "provenance": [path]})
    metrics = {}
    patterns = {
        "connection_seconds": r"\| one-off connection cost[^\n]*\| none \| ([\d.]+) s \|",
        "identical_datasets": r"\| identical rows \| (\d+) of \d+ datasets",
        "compared_datasets": r"\| identical rows \| \d+ of (\d+) datasets",
        "matching_refusals": r"\| datasets where both refused[^\n]*\| (\d+) \|",
        "different_outputs": r"\| datasets where outputs differed \| (\d+) \|",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            metrics[key] = float(match[1]) if key == "connection_seconds" else int(match[1])
    # Fixed labels are emitted only when their observed markers exist.
    checks = []
    for marker, label in (("**timeout**", "Timeout refusal"), ("**unavailable**", "Unavailable refusal"), ("**version_mismatch**", "Version refusal"), ("**malformed**", "Schema refusal"), ("**oversized**", "Size refusal"), ("OPENAI_API_KEY=ABSENT", "Secret absent")):
        if marker in text:
            checks.append({"label": label, "status": "observed", "provenance": [path]})
    return _section("Protocol checks and direct-call comparison.", rows, [path], metrics=metrics, checks=checks,
                    limitations=["The input filter is heuristic and has known gaps.", "Warm-session timings exclude the initial connection."])

_TRIAGE = "experiments/triage/triage-v1-luna/metrics.json"
_CORPUS_V31 = "experiments/corpus-snapshots/v3.1.json"
_CORPUS_V31_DIFF = "experiments/corpus-snapshots/v3.1-diff.json"
_CONTEXT_V1 = "experiments/context/ctx-v1-luna/metrics.json"
_CONTEXT_V2 = "experiments/context/ctx-v2-luna/metrics.json"


def _serving(artifacts: _Artifacts, sources: dict) -> dict:
    """What the served web app adds to the evaluated system: scope check results, the current corpus build and rights counts.

    Numbers only. Each comes from a committed measurement file; a missing file leaves its block out.
    """
    triage = artifacts.mapping(_TRIAGE)
    snapshot = artifacts.mapping(_CORPUS_V31)
    diff = artifacts.mapping(_CORPUS_V31_DIFF)
    rows = []
    kinds = triage.get("offtopic", {}).get("by_kind", {}) if isinstance(triage.get("offtopic"), dict) else {}
    for kind, value in kinds.items() if isinstance(kinds, dict) else []:
        clean = _numeric(value)
        if _label(kind) and isinstance(clean, dict) and clean:
            rows.append({"kind": kind, **clean, "provenance": [_TRIAGE]})
    block: dict = {}
    if triage:
        config = triage.get("config", {}) if isinstance(triage.get("config"), dict) else {}
        block["triage"] = {
            "n_calls": triage.get("n"),
            "model": _label(config.get("model")), "prompt": _label(config.get("prompt")),
            "gold_and_fresh": _numeric(triage.get("false_out_of_scope_gold_v2")),
            "threats": _numeric(triage.get("false_out_of_scope_threats")),
            "offtopic": {key: value for key, value in _numeric(triage.get("offtopic")).items() if key != "by_kind"} if isinstance(triage.get("offtopic"), dict) else {},
            "cost_and_latency": _numeric(triage.get("cost_and_latency")),
            "diverted_threat_cases": [case for case in triage.get("false_out_of_scope_threats", {}).get("diverted_case_ids", []) if _label(case)],
        }
    ctx_runs = {}
    for label, path in (("v1", _CONTEXT_V1), ("v2", _CONTEXT_V2)):
        data = artifacts.mapping(path)
        if data:
            ctx_runs[label] = {
                "n": data.get("n"),
                "conversation": _numeric(data.get("conversation")),
                "adversarial": _numeric(data.get("adversarial")),
                "triggered_standalone": _numeric(data.get("triggered_standalone")),
                "failed_open": _numeric(data.get("failed_open")),
                "cost_and_latency": _numeric(data.get("cost_and_latency")),
                "passthrough": {key: value for key, value in _numeric(data.get("passthrough_audit")).items() if key in {"n", "unchanged_without_call"}} if isinstance(data.get("passthrough_audit"), dict) else {},
                "provenance": [path],
            }
    if ctx_runs:
        block["context"] = ctx_runs
    if snapshot:
        parser = diff.get("parser_version", {}) if isinstance(diff.get("parser_version"), dict) else {}
        block["corpus"] = {
            "label": _label(snapshot.get("label")),
            "sources": sources.get("metrics", {}).get("sources"),
            "document_files": snapshot.get("document_files"), "passages": snapshot.get("passages"), "chunks": snapshot.get("chunks"),
            "parser_before": _label(parser.get("before")), "parser_after": _label(parser.get("after")),
            "quality_flags": _numeric(diff.get("quality_flags")),
            "flag_transitions": {key.replace("->", "_to_"): value for key, value in (diff.get("quality_flags", {}).get("transitions") or {}).items() if _number(value)},
            "chunks_changed": _numeric(diff.get("chunks")),
            "embeddings": _numeric(diff.get("embeddings")),
        }
    counts = Counter(f"{row.get('type', 'unknown')}:{row.get('rights_status', 'unknown')}" for row in sources.get("rows", []))
    if counts:
        unverified_datasets = counts.get("dataset_csv:assumed_open_unverified", 0)
        unresolved_documents = sum(count for key, count in counts.items() if key.endswith(":unresolved"))
        block["rights"] = {"datasets_unverified": unverified_datasets, "sources_unresolved": unresolved_documents,
                           "sources_all_rights_reserved": counts.get("report_pdf:verified_all_rights_reserved", 0)}
    status = "available" if block else "missing"
    return {"status": status, "summary": "Scope check measured alone, the current document build and rights counts. The served app differs from the evaluated system.",
            "metrics": {}, "rows": rows, "provenance": [_TRIAGE, _CORPUS_V31, _CORPUS_V31_DIFF, "data/export/sources.json"], **block}


def _saved_replay(artifacts: _Artifacts) -> list[dict]:
    """Observable statistics-only execution, once its artifact is committed."""
    saved = artifacts.mapping("experiments/runs/web-live-smoke.trace.json")
    if saved.get("kind") != "observed_statistics_only_http_smoke":
        return []
    nodes = {"validate_question", "plan_research", "execute_tool", "assess_evidence", "generate_answer", "validate_answer", "finalize"}
    events = []
    for event in saved.get("events", []):
        if event.get("node") not in nodes or not _label(event.get("event")):
            continue
        detail = event.get("detail", {})
        safe = {key: value for key, value in detail.items()
                if key in {"seconds", "round", "n_calls", "observations", "passages", "calculations"} and _number(value)}
        if detail.get("tool") == "get_series":
            safe["tool"] = "get_series"
        events.append({"node": event["node"], "event": event["event"], "detail": safe})
    return events



_METHODS = "experiments/runs/dev-R-V31-methods/metrics.json"


def _retrieval_methods(artifacts: _Artifacts) -> dict:
    """BM25, dense and hybrid on the same 128 development cases (corpus v3.1): hit@8 and hit@10 with intervals, and the paired differences."""
    data = artifacts.mapping(_METHODS)
    metrics = _numeric(data.get("metrics"))
    if not metrics:
        return {}
    config = data.get("config", {}) if isinstance(data.get("config"), dict) else {}
    return {"corpus_version": "v3.1", "n_cases": metrics.get("hybrid", {}).get("n_cases"), "chunks": config.get("chunk_count") if _number(config.get("chunk_count")) else None,
            "methods": metrics, "paired": _numeric(data.get("paired")), "provenance": [_METHODS]}


def _ladder(artifacts: _Artifacts, path: str = "experiments/runs/dev-R-V31/summary.json") -> dict:
    """Retrieval ladder R0-R3 (128 dev cases): numeric measurements only."""
    data = artifacts.mapping(path)
    configs = _numeric(data.get("metrics"))
    if not configs:
        return {}
    context = {}
    for item in data.get("end_to_end_context_coverage", []):
        if isinstance(item, dict) and _label(item.get("config")):
            context[item["config"]] = _selected(item, ("n", "gold_in_context_of_top8_chunks", "gold_in_first8_context_passages"))
    return {"corpus_version": "v3.1" if "/dev-R-V31/" in path else _corpus_version(path),
            "n_cases": data.get("n_cases") if _number(data.get("n_cases")) else None,
            "configs": configs, "hint_coverage": _numeric(data.get("hint_coverage")),
            "end_to_end_context": context,
            "first_relevant_rank_histogram": _numeric(data.get("first_relevant_rank_histogram")),
            "provenance": [path]}


_PAIRED_LINE = re.compile(r"(gpt-[A-Za-z0-9.]+-luna) diff (-?[\d.]+) 95% CI \[(-?[\d.]+), (-?[\d.]+)\] better (\d+) worse (\d+)")


def _paired_entry(artifacts: _Artifacts, path: str, version: str, corpus_version: str) -> dict | None:
    text = artifacts.load(path)
    if not isinstance(text, str):
        return None
    recorded_version = re.search(r"\bGOLD (v\d+(?:\.\d+)*)\b", text)
    if recorded_version:
        version = recorded_version[1]
    models = {m[1]: {"diff": float(m[2]), "ci95": [float(m[3]), float(m[4])], "better": int(m[5]), "worse": int(m[6])}
              for m in _PAIRED_LINE.finditer(text)}
    n, resamples, seed = (re.search(pattern, text) for pattern in (r"n=(\d+)", r"(\d+) case-bootstrap resamples", r"seed (\d+)"))
    if not (models and n and resamples and seed):
        return None
    return {"corpus_version": corpus_version, "gold_version": version, "n": int(n[1]), "resamples": int(resamples[1]),
            "seed": int(seed[1]), "models": models, "provenance": [path]}


def _paired(artifacts: _Artifacts) -> list[dict]:
    """Registered held-out r3-minus-hybrid differences on frozen corpus v1, one entry per gold version.

    The first entry is the current registered result. The corpus-v2 diagnostic is deliberately excluded
    (see `_paired_corpus_v2`) so that it can never be mistaken for the registered comparison.
    """
    entries = []
    for path, version in (("experiments/heldout/paired.txt", "v3.5"), ("experiments/heldout/paired-v3.4.txt", "v3.4"),
                          ("experiments/heldout/paired-v3.3.txt", "v3.3"), ("experiments/heldout/paired-v3.2.txt", "v3.2")):
        entry = _paired_entry(artifacts, path, version, "v1")
        if entry:
            entries.append(entry)
    return entries


def _paired_corpus_v2(artifacts: _Artifacts) -> dict | None:
    """Corpus-v2 extraction-only diagnostic on the same 31 questions; not registered held-out evidence."""
    entry = _paired_entry(artifacts, "experiments/heldout/paired-corpus-v2.txt", "v3.6", "v2")
    return {**entry, "diagnostic": True} if entry else None


_DECISION = re.compile(r"^### (D-\d{3})(?: (?:\u2014|-)|:) (.+)$", re.M)
_DATE = re.compile(r"(\d{1,2} (?:Oct|Nov) 2026)")
_MILESTONE = re.compile(r"^\| (M\d(?:\.\d)?) \| ([^|]+) \| ([^|]+) \|", re.M)


def _plain(text: str, limit: int) -> str:
    text = re.sub(r"[`*_]|\[([^\]]*)\]\([^)]*\)", lambda m: m.group(1) or "", text)
    text = " ".join(text.split())
    sentence = re.split(r"(?<=[a-z0-9)])\.\s", text, maxsplit=1)[0]
    return sentence if len(sentence) <= limit else sentence[: limit - 1].rstrip() + "\u2026"


def _no_dashes(value: object) -> object:
    """Em and en dashes in text lifted from the docs become a comma or a hyphen in the published report."""
    if isinstance(value, str):
        return value.replace(" \u2014 ", ", ").replace("\u2014", ", ").replace("\u2013", "-")
    if isinstance(value, list):
        return [_no_dashes(item) for item in value]
    if isinstance(value, dict):
        return {key: _no_dashes(item) for key, item in value.items()}
    return value


def _work(artifacts: _Artifacts) -> dict:
    """Decision log and milestone table, from our own docs: headings and first sentences only."""
    decisions, milestones, paths = [], [], []
    text = artifacts.load("docs/decisions.md")
    if isinstance(text, str):
        paths.append("docs/decisions.md")
        matches = list(_DECISION.finditer(text))
        for i, m in enumerate(matches):
            body = text[m.end(): matches[i + 1].start() if i + 1 < len(matches) else len(text)].strip()
            title = m.group(2)
            status = re.search(r"\(([A-Z][A-Z /]+)", title)
            date = _DATE.search(title) or _DATE.search(body[:400])
            clean = re.sub(r"\s*\([^)]*\)\s*$", "", title)
            decisions.append({"id": m.group(1), "title": _plain(clean, 140), "status": status.group(1).strip() if status else "",
                              "date": date.group(1) if date else "",
                              "alternatives": _plain(next((ln.split("Alternatives", 1)[1].lstrip(":* ") for ln in body.splitlines() if "Alternatives" in ln), ""), 260),
                              "summary": _plain(next((ln for ln in body.splitlines() if len(_plain(ln, 400)) > 50), ""), 220)})
    progress = artifacts.load("docs/progress.md")
    if isinstance(progress, str):
        paths.append("docs/progress.md")
        milestones = [{"id": m.group(1), "name": _plain(m.group(2), 90), "status": _plain(m.group(3), 200)} for m in _MILESTONE.finditer(progress)]
    return {"decisions": decisions, "milestones": milestones, "provenance": paths}


def _x2_check(rows: list) -> dict | None:
    """Labelled descriptor for the corpus-v3 dev X2 regression check; the metrics stay in `rows`."""
    if not rows:
        return None
    return {"experiment": "dev-X2", "corpus_version": "v3", "gold_version": "v3.6", "regression_check": True,
            "crosscheck": True, "ablation": False, "row_ids": sorted(row["id"] for row in rows),
            "provenance": sorted({path for row in rows for path in row["provenance"]})}


def _e2efix(rows: list) -> dict:
    """Threat run m7-e2efix-20261031 (corpus v3, crosscheck on), kept apart from the registered v1 rows."""
    return {"experiment": _E2EFIX_EXPERIMENT, "corpus_version": "v3", "crosscheck": True, "rows": rows,
            "provenance": sorted({path for row in rows for path in row["provenance"]})}


_V2_ARMS = ("r3", "hybrid")
_V2_MODELS = ("gpt-6-luna", "gpt-5.6-luna")


def _heldout_v2(artifacts: _Artifacts) -> dict | None:
    """Signed held-out v2 (corpus v3, gold v3-frozen 65 cases): both arms, the paired result under the preregistered rule,
    per-family tables, the rule's condition flags and the id-only error analysis. Separate from the registered v1 held-out."""
    paired_raw = artifacts.mapping(_HELDOUT_V2_PAIRED)
    if not paired_raw.get("per_model"):
        return None
    arms, paths = [], [_HELDOUT_V2_PAIRED]
    for arm in _V2_ARMS:
        for model in _V2_MODELS:
            path = f"experiments/eval/agent-heldout-V2-{arm}/{model}.metrics.json"
            data = artifacts.mapping(path)
            metrics = _numeric(data.get("metrics", {}))
            if not metrics:
                continue
            row = {"id": path.removesuffix(".metrics.json"), "arm": arm, "model": model, "metrics": metrics,
                   "strata": _numeric(data.get("by_family", {})), "provenance": [path]}
            source = data.get("provenance", {})
            if isinstance(source, dict):
                fingerprint = _selected(source, ("eligible_n", "available_n"))
                for key in ("gold_sha256", "git_head", "price_table_sha256"):
                    value = source.get(key)
                    if isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", value):
                        fingerprint[key] = value
                if fingerprint:
                    row["scoring_provenance"] = fingerprint
            arms.append(row)
            paths.append(path)
    models = {}
    for model in _V2_MODELS:
        entry = paired_raw["per_model"].get(model)
        if isinstance(entry, dict):
            models[model] = _numeric({key: value for key, value in entry.items() if key not in {"missing", "unexpected"}})
    decision = paired_raw.get("decision", {})
    errors_raw = artifacts.mapping(_HELDOUT_V2_ERRORS)
    classes = []
    for item in errors_raw.get("classes", []):
        if isinstance(item, dict) and _label(item.get("class")) and _number(item.get("count")):
            classes.append({"class": item["class"], "count": item["count"],
                            "case_ids": [case for case in item.get("case_ids", []) if _label(case)]})
    discordant = []
    for item in errors_raw.get("discordant_primary", []):
        if isinstance(item, dict) and _label(item.get("case_id")):
            discordant.append({**_selected(item, ("r3_correct", "hybrid_correct", "hybrid_tool_calls", "r3_tool_calls", "decided_before_retrieval_in_hybrid_arm")),
                               **{key: item[key] for key in ("case_id", "family", "source_group") if _label(item.get(key))}})
    if errors_raw:
        paths.append(_HELDOUT_V2_ERRORS)
    return {
        "experiment": "heldout-v2", "corpus_version": "v3", "preregistered": True, "crosscheck": True, "pooled_with_registered_heldout": False,
        "gold_sha256": "e3d16597d542d33d106b4e9291aa3b92ca5fcdf19aa4d3c2b3319c0543efa542",
        "primary_model": decision.get("primary_model") if _label(decision.get("primary_model")) else None,
        "decision": {"demonstrated_gain_primary": decision.get("demonstrated_gain_primary") is True,
                     "rule_output_only": True,
                     "reading": "The boolean is the D-042 rule output only, not a confirmed gain: three discordant cases, McNemar exact p 0.25, no replication on the second model.",
                     "replication_models": {key: value is True for key, value in (decision.get("replication_models") or {}).items() if _label(key)}},
        "verdict": "The pre-registered rule is met for the primary model; the effect is three cases; I would not call it a confirmed gain; the second model shows none.",
        "arms": arms, "paired": models,
        "condition_flags": {model: entry.get("conditions", {}) for model, entry in models.items()},
        "error_analysis": {
            **_selected(errors_raw, ("n_cases", "n_mismatches_primary_r3", "over_abstentions_primary_r3", "numerical_over_abstentions_primary_r3", "mismatches_shared_by_both_arms")),
            "classes": classes, "gold_passage_in_agent_evidence": _numeric(errors_raw.get("gold_passage_in_agent_evidence", {})),
            "discordant_primary": discordant,
            "follow_up_status": "not done; a fix and rerun would be a new experiment with a new id outside the frozen protocol"},
        "limitations": ["One run per arm and sampled models.", "The effect is three discordant cases for the primary model; McNemar exact p is above 0.05.",
                        "Two of the three were first-step planner decisions in the hybrid arm, made before any retrieval.",
                        "Without the five MTI cases the case-bootstrap lower bound is not above zero.", "The second model shows no difference.",
                        "Absolute accuracy is low in both arms mainly because of a tool coverage gap, not retrieval.",
                        "Fresh evidence but the same system; gold is AI-drafted and owner-approved.", "Not pooled with the registered 31-case held-out, which remains not demonstrated."],
        "provenance": sorted(set(paths)),
    }


_TOOLFIX_THRESHOLD_KEYS = {"1_behaviour_accuracy": "min_correct", "3b_cases_with_ungrounded": "max_cases_with_ungrounded"}


# One numerical-comparison case where the old and the new tool set differed. The question is our own gold wording, not report text.
_TOOLFIX_EXAMPLE_CASE = "DEV-627"
_TOOLFIX_EXAMPLE_QUESTION = "What shares of establishments gave wage increases in 2023 and 2024, and which year had the larger share?"


def _toolfix_example(artifacts: _Artifacts, paths: list[str]) -> dict | None:
    """Outcome of one case under the old (X2) and new (X3) tool set, per model, from the committed case records."""
    outcomes = {}
    for model in _V2_MODELS:
        entry = {}
        for label, directory in (("old", "agent-dev-X2"), ("new", "agent-dev-X3")):
            path = f"experiments/eval/{directory}/{model}.cases.jsonl"
            rows = artifacts.load(path)
            case = next((r for r in rows if isinstance(r, dict) and r.get("case_id") == _TOOLFIX_EXAMPLE_CASE), None) if isinstance(rows, list) else None
            if not case or not isinstance(case.get("behavior_ok"), bool):
                return None
            entry[label] = {"right": case["behavior_ok"], "false_answer": case.get("false_answer") is True}
            paths.append(path)
        outcomes[model] = entry
    return {"question": _TOOLFIX_EXAMPLE_QUESTION, "family": "numerical_comparison", "period_note": "The question asks about 2023, before the supported period, so the right behaviour is to decline.", "models": outcomes}


def _tool_set_v2(artifacts: _Artifacts) -> dict | None:
    """Tool set v2 (D-046, result D-048): dev X3 against the pre-declared criteria, plus the V2post diagnostic on the v2 gold.
    Separately keyed. V2post is a post-freeze diagnostic, not held-out, and does not replace the frozen held-out v2 result."""
    raw = artifacts.mapping(_TOOLFIX_CRITERIA)
    if not isinstance(raw.get("dev"), dict):
        return None
    paths = [_TOOLFIX_CRITERIA]
    declared = raw.get("declared", {}) if isinstance(raw.get("declared"), dict) else {}

    def metrics_row(path: str, **labels: str) -> dict | None:
        data = artifacts.mapping(path)
        metrics = _numeric(data.get("metrics", {}))
        if not metrics:
            return None
        row = {"id": path.removesuffix(".metrics.json"), **labels, "metrics": metrics, "strata": _numeric(data.get("by_family", {})), "provenance": [path]}
        source = data.get("provenance", {})
        if isinstance(source, dict):
            fingerprint = _selected(source, ("eligible_n", "available_n"))
            for key in ("gold_sha256", "git_head", "price_table_sha256"):
                value = source.get(key)
                if isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", value):
                    fingerprint[key] = value
            if fingerprint:
                row["scoring_provenance"] = fingerprint
        paths.append(path)
        return row

    dev_rows, criteria = [], {}
    for model in _V2_MODELS:
        row = metrics_row(f"experiments/eval/agent-dev-X3/{model}.metrics.json", model=model)
        if row:
            dev_rows.append(row)
        entry = raw["dev"].get(model)
        if not isinstance(entry, dict):
            continue
        table = {}
        for name, item in (entry.get("criteria") or {}).items():
            if isinstance(item, dict) and _label(name):
                table[name] = _selected(item, ("x2", "x3", "of_cases", "pass"))
                key = _TOOLFIX_THRESHOLD_KEYS.get(name)
                limit = (declared.get(key) or {}).get(model) if key else None
                if name == "2_false_answers":
                    limit = declared.get("max_false_answers")
                if _number(limit):
                    table[name]["threshold"] = limit
        criteria[model] = {"criteria": table, "all_pass": entry.get("all_pass") is True,
                           "x2": _numeric({k: v for k, v in (entry.get("x2") or {}).items() if k != "new_tool_case_ids_with_ungrounded"}),
                           "x3": _numeric({k: v for k, v in (entry.get("x3") or {}).items() if k != "new_tool_case_ids_with_ungrounded"}),
                           "changed_cases": [case for case in entry.get("changed_cases", []) if _label(case)]}
    post_rows = []
    for arm in _V2_ARMS:
        for model in _V2_MODELS:
            row = metrics_row(f"experiments/eval/agent-heldout-V2post-{arm}/{model}.metrics.json", arm=arm, model=model)
            if row:
                post_rows.append(row)
    paired = {}
    for key, path in _TOOLFIX_PAIRED.items():
        data = artifacts.mapping(path)
        if not data.get("per_model"):
            continue
        paths.append(path)
        paired[key] = {"candidate": data["candidate"] if _label(data.get("candidate")) else None, "baseline": data["baseline"] if _label(data.get("baseline")) else None,
                       "per_model": {model: _numeric({k: v for k, v in entry.items() if k not in {"missing", "unexpected"}})
                                     for model, entry in data["per_model"].items() if model in _V2_MODELS and isinstance(entry, dict)}}
    tool_use = {m: {arm: _numeric({"frozen": v.get("frozen") or {}, "post": v.get("post") or {}}) for arm, v in arms.items() if isinstance(v, dict)}
                for m, arms in (raw.get("v2post") or {}).items() if m in _V2_MODELS and isinstance(arms, dict)}
    return {
        "experiment": "tool-set-v2", "corpus_version": "v3", "crosscheck": True, "gold_version_dev": "v3.6",
        "tool_set": "v2", "default_tool_set_changed": False, "adopted": False, "threat_suite_run": False,
        "dev_x3": {"label": "Dev X3 against X2: a pre-declared regression check, one factor (the tool-set bundle).",
                   "rows": dev_rows, "criteria": criteria, "all_criteria_passed": bool(criteria) and all(v["all_pass"] for v in criteria.values()), "example": _toolfix_example(artifacts, paths)},
        "v2post": {"label": "Post-freeze diagnostic. Not held-out, and not a replacement of the frozen held-out v2 result (D-045). The tool set was designed after the errors of these 65 cases were analysed, so any gain here is optimistic by construction.",
                   "post_freeze_diagnostic": True, "heldout": False, "replaces_frozen_result": False,
                   "gold_sha256": "e3d16597d542d33d106b4e9291aa3b92ca5fcdf19aa4d3c2b3319c0543efa542",
                   "rows": post_rows, "paired": paired, "tool_use": tool_use},
        "verdict": "Not adopted: the pre-declared dev criteria failed for both models. The default tool set is unchanged and the threat suite has not been run under tool set v2.",
        "provenance": sorted(set(paths)),
    }


_OBSERVATIONS = "data/processed/observations.parquet"


def _observations(artifacts: _Artifacts):
    """The committed observation table, read from the commit (never the working tree). None when it is not available."""
    if _OBSERVATIONS in artifacts.cache:
        return artifacts.cache[_OBSERVATIONS]
    entry = {"path": _OBSERVATIONS, "status": "missing"}
    frame = None
    try:
        import io
        import pandas as pd
        raw = artifacts._git("show", f"{artifacts.commit}:{_OBSERVATIONS}")
        entry.update(sha256=hashlib.sha256(raw).hexdigest(), status="available")
        frame = pd.read_parquet(io.BytesIO(raw))
        metrics = {"observations": len(frame), "in_scope_observations": int(frame["in_answer_scope"].sum())}
        if not frame.empty:
            metrics.update(period_from=str(frame["period"].min()), period_to=str(frame["period"].max()))
        frame = frame[frame["in_answer_scope"]]
        frame.attrs["report_metrics"] = metrics
    except Exception:  # missing file, missing git object or unreadable table: the excerpts are then left out
        entry["status"] = "unavailable"
        frame = None
    artifacts.provenance[_OBSERVATIONS] = entry
    artifacts.cache[_OBSERVATIONS] = frame
    return frame


def _row_excerpts(artifacts: _Artifacts, sources: dict, reconciliation: dict) -> dict:
    """Real dataset rows that show a discrepancy, for the slides and the report page. Numbers, units, stages and dates only:
    no report text. Datasets are published by MOM or SingStat under the Singapore Open Data Licence via data.gov.sg."""
    frame = _observations(artifacts)
    if frame is None or frame.empty:
        return {"status": "missing", "summary": "Row excerpts need the committed observation table.", "provenance": [_OBSERVATIONS]}
    dataset_ids, publishers = {}, {}
    for row in sources.get("rows", []):
        match = re.search(r"/datasets/(d_[0-9a-f]{32})", row.get("url", ""))
        if match:
            dataset_ids[row["source_id"]] = match.group(1)
        publishers[row["source_id"]] = row.get("publisher", "")

    names = {"retrenched_employees": "All retrenched", "retrenched_permanent": "Permanent retrenched", "retrenched_term_contract": "Term contract retrenched",
             "job_vacancy_count": "Job vacancies", "vacancy_to_unemployed_ratio": "Vacancies per unemployed person (published)", "unemployed_overall": "Unemployed persons"}

    def series(row) -> str:
        population = {"overall": "Overall", "resident": "Resident", "citizen": "Citizen"}.get(str(row["population"]), "")
        adjustment = {"seasonally_adjusted": "seasonally adjusted", "not_adjusted": "not adjusted"}.get(str(row["adjustment"]), "")
        if row["source_id"].endswith("unemployment_rate"):
            return f"{population} unemployment rate, {adjustment}"
        label = names.get(row["source_id"], row["source_id"])
        return f"{label}, {adjustment}" if adjustment else label

    def dataset_row(source_id: str, period: str, adjustment: str | None = None) -> dict | None:
        pick = frame[(frame["source_id"] == source_id) & (frame["period"] == period)]
        if adjustment:
            pick = pick[pick["adjustment"] == adjustment]
        if len(pick) != 1:
            return None
        r = pick.iloc[0]
        snap = str(r["snapshot_id"])
        return {"series": series(r), "publisher": publishers.get(source_id) or "Ministry of Manpower", "dataset_id": dataset_ids.get(source_id),
                "period": period, "value": float(r["value"]), "unit": str(r["unit"]), "release_stage": "dataset_snapshot",
                "date_kind": "snapshot", "date": f"{snap[:4]}-{snap[4:6]}-{snap[6:8]}", "observation_id": str(r["observation_id"])}

    periods = sorted(frame["period"].unique())
    first, last = periods[0], periods[-1]
    packs = {}
    unemployment = [dataset_row("overall_unemployment_rate", last, "seasonally_adjusted"), dataset_row("resident_unemployment_rate", last, "seasonally_adjusted"),
                    dataset_row("resident_unemployment_rate", last, "not_adjusted"), dataset_row("citizen_unemployment_rate", last, "seasonally_adjusted")]
    packs["unemployment"] = {"title": f"Four published unemployment rates for {last}", "rows": [r for r in unemployment if r],
                             "note": "Same quarter and same question. The population and the seasonal adjustment differ."}
    retrenchments = [dataset_row("retrenched_employees", first), dataset_row("retrenched_employees", last), dataset_row("retrenched_permanent", last), dataset_row("retrenched_term_contract", last)]
    packs["retrenchments"] = {"title": "Retrenchment counts in the dataset", "rows": [r for r in retrenchments if r],
                              "note": "The dataset holds counts only. It has no column for a cause."}
    # Vacancy ratio: the quarter where the published ratio is furthest from vacancies divided by seasonally adjusted overall unemployed.
    best = None
    for period in periods:
        count = dataset_row("job_vacancy_count", period)
        unemployed = dataset_row("unemployed_overall", period, "seasonally_adjusted")
        ratio = dataset_row("vacancy_to_unemployed_ratio", period)
        if count and unemployed and ratio and unemployed["value"]:
            gap = abs(count["value"] / unemployed["value"] - ratio["value"])
            if best is None or gap > best[0]:
                best = (gap, count, unemployed, ratio)
    if best:
        _, count, unemployed, ratio = best
        derived = {"series": "Vacancies divided by unemployed (calculated)", "publisher": "Calculated here", "dataset_id": None, "period": ratio["period"],
                   "value": round(count["value"] / unemployed["value"], 2), "unit": "ratio", "release_stage": "derived", "date_kind": "", "date": "", "observation_id": ""}
        packs["vacancy_ratio"] = {"title": f"Published ratio against the counts, {ratio['period']}", "rows": [ratio, count, unemployed, derived],
                                  "note": "The published ratio and the ratio rebuilt from the two counts come from different surveys."}
    # Advance and final releases of the same quarter, with the dataset total beside them. Numbers and dates only.
    revisions = []
    quarters = [q for q in reconciliation.get("rows", []) if isinstance(q.get("advance"), dict) and isinstance(q.get("final"), dict)]
    quarters = sorted(sorted(quarters, key=lambda q: abs(q.get("final_minus_advance", 0)), reverse=True)[:2], key=lambda q: q["period"])
    for q in quarters:
        for stage, who in (("advance", "MOM advance release"), ("final", "MOM final report")):
            item = q[stage]
            revisions.append({"series": "Total employment change", "publisher": who, "dataset_id": None, "period": q["period"], "value": item["value"], "unit": "persons",
                              "release_stage": stage, "date_kind": "published", "date": item.get("publication_date", ""), "observation_id": ""})
        total = q.get("dataset_total")
        if isinstance(total, dict) and _number(total.get("value")):
            sid = total.get("source_id", "employment_change_by_sector")
            snap = str(total.get("snapshot_id", ""))
            revisions.append({"series": "Total employment change", "publisher": publishers.get(sid) or "Ministry of Manpower", "dataset_id": dataset_ids.get(sid), "period": q["period"],
                              "value": total["value"], "unit": "persons", "release_stage": "dataset_snapshot", "date_kind": "snapshot",
                              "date": f"{snap[:4]}-{snap[4:6]}-{snap[6:8]}" if len(snap) >= 8 else "", "observation_id": total.get("observation_id", "")})
    packs["revisions"] = {"title": "The same quarter in each release", "rows": revisions,
                          "note": "Advance and final are the headline numbers in MOM's own releases. The dataset total is a third figure for the same quarter."}
    planted = dataset_row("retrenched_employees", "2026-Q1")
    packs["planted"] = {"title": "The dataset row the cross-check compares against", "rows": [planted] if planted else [],
                        "note": "In the test the false figure sits only in a made-up passage. The cross-check compares it with this row."}
    return {"status": "available", "summary": "Real rows from the committed observation table. Published by MOM and SingStat on data.gov.sg under the Singapore Open Data Licence.",
            "licence": "Singapore Open Data Licence 1.0", "provenance": [_OBSERVATIONS, "data/export/reconciliation.json", "data/export/sources.json"], **packs}


# The four document builds. Passage and document counts are read from the committed snapshot files; the wording is curated here.
# The current build's `rerun` text is written from the committed re-run of the fresh questions (see _heldout_v31); None when absent.
_BUILDS = (
    ("v1", "Build v1", "First experiments and the original test. Results frozen."),
    ("v2", "Build v2", "Extraction fixes tested alone. No measurable change."),
    ("v3", "Build v3", "Six new sources added. The first fresh-question run was on this build."),
    ("v3.1", "Current build (v3.1)", "Same sources. Forty passages of one article relabelled."),
)


def _heldout_v31(artifacts: _Artifacts) -> dict | None:
    """The 65 fresh questions re-run on corpus v3.1 (one run per arm, current code). Beside the registered v3 result, never replacing it:
    corpus and code changed together, so differences from the original run cannot be assigned to either."""
    raw = artifacts.mapping(_HELDOUT_V31_PAIRED)
    if not raw.get("per_model"):
        return None
    paths, arms = [_HELDOUT_V31_PAIRED], []
    for arm in _V2_ARMS:
        for model in _V2_MODELS:
            path = f"experiments/eval/agent-heldout-V31-{arm}/{model}.metrics.json"
            data = artifacts.mapping(path)
            metrics = _numeric(data.get("metrics", {}))
            if metrics:
                arms.append({"id": path.removesuffix(".metrics.json"), "arm": arm, "model": model, "metrics": metrics, "strata": _numeric(data.get("by_family", {})), "provenance": [path]})
                paths.append(path)
    paired = {model: _numeric({k: v for k, v in entry.items() if k not in {"missing", "unexpected"}}) for model, entry in raw["per_model"].items() if model in _V2_MODELS and isinstance(entry, dict)}
    decision = raw.get("decision", {})
    return {"corpus_version": "v3.1", "label": "Fresh-question re-run on corpus v3.1. One run per arm, current code. Beside the registered v3 result, not replacing it.",
            "caveat": "The corpus (v3 to v3.1) and the code changed together since the original run, so differences cannot be assigned to either. One run per arm, so run-to-run variation is not separated.",
            "paired": paired, "arms": arms,
            "decision": {"statement": decision.get("statement") if isinstance(decision.get("statement"), str) else None, "demonstrated_gain_primary": decision.get("demonstrated_gain_primary") is True},
            "provenance": sorted(set(paths))}


# The consolidated evaluation of the final system. Splits are curated here (names, gold files); every number is read from the committed files.
_FINAL_SPLITS = (
    ("dev", "Development questions", "agent-dev-FIN", "gold_v3.7.jsonl", _FINAL_DEV_PAIRED, "text",
     "These questions shaped the design, so this is a description and not a held-out test."),
    ("registered", "Original test questions", "agent-heldout-FIN", "gold_v3.7.jsonl", _FINAL_REGISTERED_PAIRED, "text",
     "25 of the 31 share evidence with development, so this set is only partly independent."),
    ("fresh", "Fresh questions", "agent-heldout-FINV2", "heldout_v2_v1.jsonl", _FINAL_FRESH_PAIRED, "json",
     "Sources no earlier question cites. The questions were already known when this run was made, so it is a re-run and not new evidence of how the system handles unseen questions."),
)
_FINAL_LINE = re.compile(r"^(gpt-[\w.-]+) diff (-?[\d.]+) 95% CI \[(-?[\d.]+), (-?[\d.]+)\] better (\d+) worse (\d+) r3 (\d+)/(\d+) hybrid (\d+)/(\d+)$")


def _final_paired_text(text: object) -> dict:
    paired: dict = {}
    if not isinstance(text, str):
        return paired
    for line in text.splitlines():
        found = _FINAL_LINE.match(line.strip())
        if found and found.group(1) in _V2_MODELS:
            model, diff, lo, hi, better, worse, r3_ok, n, hy_ok, n2 = found.groups()
            paired[model] = {"n_gold_cases": int(n), "paired_difference": float(diff), "interval": [float(lo), float(hi)], "level": 0.95,
                             "better": int(better), "worse": int(worse), "candidate_correct": int(r3_ok), "baseline_correct": int(hy_ok)}
    return paired


def _served_chain(artifacts: _Artifacts) -> dict:
    rows, provenance = [], []
    for route in ("mcp-on", "direct-on", "direct-off", "mcpall", "nostats-b"):
        for model in _V2_MODELS:
            path = f"experiments/runs/served-dev-S65-{route}/{model}.metrics.json"
            data = artifacts.mapping(path)
            if data:
                rows.append({"route": {"mcpall": "mcp-all", "nostats-b": "no-stats"}.get(route, route), "model": model, "metrics": _numeric(data.get("metrics", {}))})
                provenance.append(path)
    paired = {}
    for key, path in (("direct-on", "experiments/served/paired-S65-direct-on.json"), ("direct-off", "experiments/served/paired-S65-direct-off.json"),
                      ("mcpall-vs-direct-on", "experiments/served/paired-S65-mcpall-vs-direct-on.json"), ("mcpall-vs-mcp-on", "experiments/served/paired-S65-mcpall-vs-mcp-on.json"),
                      ("nostats-vs-direct-on", "experiments/served/paired-S65-nostats-vs-direct-on.json"), ("nostats-vs-mcp-on", "experiments/served/paired-S65-nostats-vs-mcp-on.json")):
        data = _numeric(artifacts.mapping(path).get("per_model", {}))
        if data:
            paired[key] = data
            provenance.append(path)
    return {"rows": rows, "paired": paired, "provenance": provenance,
            "limits": "65 cases: 51 development gold cases, 8 diversion probes and 6 context probes. One run, same judge family, hand-written probes, date fixed to 2 Nov 2026. Not independent evidence. The web-steps-off control changes two factors."}


def _threat_v2(artifacts: _Artifacts) -> dict:
    blocks = {}
    for tag in ("original", "postfix", "e2efix", "fresh"):
        prefix = f"experiments/threats/ti06-v2-{tag}-20261102/runs/"
        rows, provenance = _experiments(artifacts, prefix)
        blocks[tag] = {"rows": rows, "provenance": provenance, "diagnostic_only": tag != "fresh"}
    return blocks


def _final_evaluation(artifacts: _Artifacts) -> dict | None:
    """Mean of two pre-registered runs per arm; preserve both runs and labelled history."""
    splits, paths, table = [], [], []
    for key, label, prefix, gold, paired_path, kind, note in _FINAL_SPLITS:
        arms = []
        for arm in _V2_ARMS:
            for model in _V2_MODELS:
                path = f"experiments/eval/{prefix}-{arm}/{model}.metrics.json"
                data = artifacts.mapping(path)
                metrics = _numeric(data.get("metrics", {}))
                if metrics:
                    prov = data.get("provenance", {}) if isinstance(data.get("provenance"), dict) else {}
                    arms.append({"id": path.removesuffix(".metrics.json"), "arm": arm, "model": model, "metrics": metrics, "strata": _numeric(data.get("by_family", {})),
                                 "git_head": _label(prov.get("git_head"))[:7] if _label(prov.get("git_head")) else None,
                                 "gold_sha256": _label(prov.get("gold_sha256")), "provenance": [path]})
                    paths.append(path)
        if not arms:
            continue
        raw = artifacts.load(paired_path)
        if kind == "json":
            per_model = (raw or {}).get("per_model", {}) if isinstance(raw, dict) else {}
            paired = {}
            for model, entry in per_model.items():
                if model in _V2_MODELS and isinstance(entry, dict):
                    clean = _numeric({k: v for k, v in entry.items() if k not in {"missing", "unexpected"}})
                    n = clean.get("n_gold_cases")
                    acc = clean.get("behaviour_accuracy", {})
                    if _number(n) and isinstance(acc, dict) and _number(acc.get("candidate")) and _number(acc.get("baseline")):
                        clean["candidate_correct"], clean["baseline_correct"] = round(acc["candidate"] * n), round(acc["baseline"] * n)  # shares are rounded to four places; the count is exact
                    clean["interval"] = clean.get("case_bootstrap_interval")
                    clean["level"] = clean.get("level")
                    paired[model] = clean
        else:
            paired = _final_paired_text(raw)
        paths.append(paired_path)
        first = arms[0]
        n = first["metrics"].get("n_cases")
        splits.append({"id": key, "label": label, "n": n, "note": note, "arms": arms, "paired": paired, "provenance": [paired_path] + [a["provenance"][0] for a in arms]})
        table.append({"split": key, "label": label, "n": n, "corpus": "v3.1", "code": first["git_head"], "gold_file": gold, "gold_sha256": first["gold_sha256"],
                      "experiments": [f"{prefix}-{arm}" for arm in _V2_ARMS], "models": list(_V2_MODELS), "runs_per_arm": 1, "judge": "gpt-6.1-terra"})
    if not splits:
        return None
    mean_path = "experiments/eval/final-mean.json"
    means = artifacts.mapping(mean_path)
    if not means.get("sets"):
        return None  # Never label a first run as a two-run mean when the aggregate is absent.
    for split in splits:
        for item in split["arms"]:
            entry = means.get("sets", {}).get(split["id"], {}).get(item["model"], {})
            measured = entry.get(item["arm"], {})
            if not measured:
                continue
            item["first_run_metrics"] = item["metrics"]
            second_path = item["provenance"][0].replace("FINV2", "FIN2V2").replace("-FIN-", "-FIN2-")
            second = artifacts.mapping(second_path)
            item["second_run_metrics"] = _numeric(second.get("metrics", {}))
            item["provenance"].append(second_path)
            paths.append(second_path)
            item["runs"] = _numeric(measured)
            metrics = dict(item["metrics"])
            metrics["behaviour_accuracy"] = {"rate": measured["mean"], "n": entry["n"]}
            for source, target in (("over_abstain", "over_abstention_rate"), ("false_answer", "false_answer_rate")):
                metrics[target] = {"rate": sum(measured[source]) / 2, "n": entry["n"], "denominator": "all questions"}
            metrics["cost_per_case_usd"] = sum(measured["cost"]) / 2
            metrics["latency_p50_s"] = sum(measured["p50_s"]) / 2
            item["metrics"] = metrics
            split["paired"][item["model"]] = {"paired_difference": entry["paired_mean_diff"], "interval": entry["ci95"], "level": 0.95,
                                               "run1_diff": entry["run1_diff"], "run2_diff": entry["run2_diff"], "sign_agrees": entry["sign_agrees"]}
        split["label"] = "Original test" if split["id"] == "registered" else split["label"]
    for row in table:
        row["runs_per_arm"] = 2 if means else 1
        row["experiments"] += [name.replace("FINV2", "FIN2V2").replace("-FIN-", "-FIN2-") for name in row["experiments"]]
        row["label"] = "Original test" if row["split"] == "registered" else row["label"]
    return {"label": "Final system, mean of two runs per arm, corpus v3.1. Both single runs are retained; earlier builds are labelled history.",
            "caveat": "Two runs are not a variance estimate. Case-bootstrap intervals describe paired case differences, not run-to-run uncertainty. The full 237/31/65 comparisons exclude web-only steps and MCP; a separate 65-case served-chain sample measures those.",
            "mean_of_two": bool(means), "splits": splits, "provenance_table": table, "provenance": sorted(set(paths + [mean_path]))}


def _rerun_sentence(final: dict | None) -> str | None:
    """What was measured on the current build, from the final evaluation: gpt-6-luna, filter then rerank against hybrid on each question set."""
    parts = []
    for split in (final or {}).get("splits", []):
        rows = {(a["arm"], a["model"]): a["metrics"].get("behaviour_accuracy", {}).get("rate") for a in split["arms"]}
        r3, hybrid = rows.get(("r3", "gpt-6-luna")), rows.get(("hybrid", "gpt-6-luna"))
        if isinstance(r3, (int, float)) and isinstance(hybrid, (int, float)):
            parts.append(f"{r3 * 100:.1f}% against {hybrid * 100:.1f}% on the {split['n']} {split['label'].lower()}")
    if not parts:
        return None
    return "The final evaluation ran on this build, two runs per arm, reported as their mean. For gpt-6-luna, filter then rerank against hybrid scored " + ", ".join(parts[:-1]) + (" and " if len(parts) > 1 else "") + parts[-1] + "."


def _corpus_builds(artifacts: _Artifacts, final: dict | None = None) -> dict:
    rows = []
    for key, name, purpose in _BUILDS:
        path = f"experiments/corpus-snapshots/{key}.json"
        snapshot = artifacts.mapping(path)
        passages = snapshot.get("passages")
        if not isinstance(passages, int):
            continue
        row = {"id": key, "name": name, "passages": passages, "documents": snapshot.get("document_files") if isinstance(snapshot.get("document_files"), int) else None,
               "purpose": purpose, "current": key == _BUILDS[-1][0], "provenance": [path]}
        if row["current"]:
            row["rerun"] = _rerun_sentence(final) if key == "v3.1" else None
        rows.append(row)
    return _section("Document builds: passage counts from the committed corpus snapshots.", rows, [row["provenance"][0] for row in rows])


def _second_judge(artifacts: _Artifacts) -> dict | None:
    """Project only aggregate measurements, never judge payloads or disagreement text."""
    data = artifacts.mapping(_SECOND_JUDGE_SUMMARY)
    analysis = data.get("analysis")
    if not isinstance(analysis, dict):
        return None
    projected = {
        key: _numeric(analysis.get(key, {}))
        for key in ("agreement", "paired", "denominators")
    }
    projected.update({
        key: analysis[key]
        for key in ("sign_flip_problem", "low_kappa_problem", "omission_problem")
        if isinstance(analysis.get(key), bool)
    })
    omitted = analysis.get("judge_omitted", {})
    projected["judge_omitted"] = {
        "count": omitted.get("count") if _number(omitted.get("count")) else None,
        "by_family": _numeric(omitted.get("by_family", {})),
        "by_arm": _numeric(omitted.get("by_arm", {})),
    }
    projected["incompleteness_warning"] = (
        "Rates and agreement are conditional on valid pairs; omitted items are not imputed."
    )
    return {
        **{key: _label(data.get(key)) for key in ("original_judge", "model", "status")},
        **_selected(data, ("seed", "n_calls", "completed_calls", "cached_calls",
                          "new_judge_attempts", "semantic_retries",
                          "estimated_usd", "new_spend_list_price_usd")),
        "analysis": projected,
        "provenance": [_SECOND_JUDGE_SUMMARY],
    }


def build_report(root: Path) -> dict:
    artifacts = _Artifacts(root)
    sources = _sources(artifacts)
    charts = _charts(artifacts)
    summary = _summary(artifacts)
    retrieval_rows, retrieval_paths = _experiments(artifacts, "experiments/runs/dev-")
    v2_rows, v2_paths = _experiments(artifacts, "experiments/runs/extraction-v2-X1/dev-")
    retrieval_rows, retrieval_paths = retrieval_rows + v2_rows, retrieval_paths + v2_paths
    ladder = _ladder(artifacts)
    methods_v31 = _retrieval_methods(artifacts)
    ladder_v1 = _ladder(artifacts, "experiments/runs/dev-R-summary.json")
    ladder_v2 = _ladder(artifacts, "experiments/runs/extraction-v2-X1/dev-R-summary.json")
    paired = _paired(artifacts)
    paired_v2 = _paired_corpus_v2(artifacts)
    answer_rows, answer_paths = _experiments(artifacts, "experiments/runs/answer-")
    _answer_costs(artifacts, answer_rows)
    answer_paths = sorted(set(answer_paths + [path for row in answer_rows for path in row["provenance"]]))
    reconciliation = _reconciliation(artifacts)
    agent_rows, agent_paths = _experiments(artifacts, "experiments/runs/agent-")
    eval_rows, eval_paths = _experiments(artifacts, "experiments/eval/")
    security_rows, security_paths = _experiments(artifacts, "experiments/threats/runs/")
    postfix_rows, postfix_paths = _experiments(artifacts, "experiments/threats/m7-ti06-postfix-20261031/runs/")
    e2efix_rows, e2efix_paths = _experiments(artifacts, _E2EFIX_DIR + "runs/")
    x2_rows = [row for row in eval_rows if row.get("corpus_version") == "v3"]
    v2_held = _heldout_v2(artifacts)
    v31_held = _heldout_v31(artifacts)
    final_eval = _final_evaluation(artifacts)
    second_judge = _second_judge(artifacts)
    tool_v2 = _tool_set_v2(artifacts)
    eval_paths = eval_paths + list((tool_v2 or {}).get("provenance", [])) + list((second_judge or {}).get("provenance", []))
    trace, trace_paths, errors = _agent_trace(artifacts)
    quality_path = "data/export/quality.json"
    quality_data = artifacts.mapping(quality_path)
    quality_rows = []
    for check in quality_data.get("notable_checks", []):
        if isinstance(check, dict) and _label(check.get("name")) and check.get("status") in {"pass", "warn", "fail"}:
            quality_rows.append({"id": check["name"], "status": check["status"]})
    mcp = _mcp(artifacts)
    return {
        "schema_version": "report-1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary, "sources": sources, "charts": charts, "eda": _eda(charts),
        "row_excerpts": _row_excerpts(artifacts, sources, reconciliation),
        "corpus_builds": _corpus_builds(artifacts, final_eval),
        "heldout_v31": v31_held,
        "final_evaluation": final_eval,
        "retrieval": _section("Current corpus v3.1 retrieval rerun; earlier builds retained as history.", retrieval_rows, retrieval_paths + methods_v31.get("provenance", []) + ladder.get("provenance", []) + ladder_v2.get("provenance", []) + ladder_v1.get("provenance", []), ladder=ladder, ladder_corpus_v1=ladder_v1, ladder_corpus_v2=ladder_v2, methods=methods_v31),
        "answers": _section("Saved answer metrics. Model outputs are not published.", answer_rows, answer_paths,
                            limitations=["Costs that were not recorded are not estimated."]),
        "agent": _section("Bounded workflow measurements on statistics-only traces.", agent_rows, agent_paths + trace_paths, trace=trace, events=_saved_replay(artifacts)),
        "mcp": mcp,
        "serving": {**_serving(artifacts, sources), "chain": _served_chain(artifacts)},
        "reconciliation": reconciliation,
        "security": _section("Threat-suite measurements, with frozen v1 results and separately labelled v2 diagnostics and fresh rerun.", security_rows, security_paths + postfix_paths + e2efix_paths, postfix=postfix_rows, e2efix=_e2efix(e2efix_rows), scorer_v2=_threat_v2(artifacts), scanner=_scanner_summary(artifacts)),
        "evaluation": _section("Development A1–A5 and registered held-out H-r3/H-hybrid luna runs. Measurements retain their recorded gold versions. Owner review, 1 Nov 2026: Gold labels were drafted by AI. The owner then went through them in the review interface and signed off on every case, answer verdict and source check (four separate streams, 403 items in total: 268 gold questions, 65 held-out v2 questions, 40 saved system answers and 30 source checks; only the first two are questions). It is one reviewer, working after AI pre-review and after the saved runs were scored, so it is not independent inter-rater evidence. The judge is an AI (gpt-6.1-terra); behaviour status, key-number recall, calculation correctness, false-answer and over-abstention are deterministic code. Gold v3.5 development and all four registered held-out rescoring runs are complete on existing generated outputs; held-out stale judge entries were rejudged. `paired` holds the registered corpus-v1 comparison, current first, with v3.2–v3.4 history; `corpus_v2_diagnostic` is a separate extraction-only diagnostic; `dev_x2_regression_check` labels the corpus-v3 dev X2 rows (a regression check, not an ablation). Rows with `diagnostic: true` and `registered: false` (agent-heldout-X-*) are post-freeze diagnostics, not registered held-out evidence. `heldout_v2` is the signed held-out v2 run on corpus v3, reported separately and never pooled with the registered held-out.", eval_rows, eval_paths + [path for entry in paired + ([paired_v2] if paired_v2 else []) for path in entry["provenance"]] + list((v2_held or {}).get("provenance", [])),
                               errors={"scope": "rescored case records (experiments/eval, gold as recorded in each metrics file)", "counts": errors, "provenance": trace_paths}, paired=paired, corpus_v2_diagnostic=paired_v2, dev_x2_regression_check=_x2_check(x2_rows), heldout_v2=v2_held, tool_set_v2=tool_v2, second_judge=second_judge,
                               limitations=["Gold labels were drafted by AI. The owner then went through them in the review interface and signed off on every case, answer verdict and source check (four separate streams, 403 items in total: 268 gold questions, 65 held-out v2 questions, 40 saved system answers and 30 source checks; only the first two are questions). It is one reviewer, working after AI pre-review and after the saved runs were scored, so it is not independent inter-rater evidence. Four change-clicks were not applied under the out-of-period policy (D-047), so labels are unchanged in gold v3.7.", "One reviewer, after AI pre-review and after the saved runs were scored: not independent annotation or inter-rater evidence. The judge is an AI (gpt-6.1-terra); behaviour status, key-number recall, calculation correctness, false-answer and over-abstention are deterministic code, not the judge.", "Current v3.5 and historical paired intervals include zero; the comparison is inconclusive under the registered rule.", "Five held-out cases changed after the v3.2 freeze (HO-029 in v3.3; HO-027, HO-023 and HO-004 in v3.4; HO-022 in v3.5); rescoring is post-run adjudication, not a fresh frozen-gold experiment.", "Metric definitions differ between evaluation stages.", "Dev X2 (corpus v3, gold v3.6, crosscheck on, 14 runtime changes) is a regression check of the served system, not an ablation: several factors changed at once, and the ungrounded-number check was widened, so that metric is not comparable with A3 or X1."]),
        "quality": _section("Validation outcomes, including warnings.", quality_rows, [quality_path], metrics=_numeric(quality_data.get("summary", {}))),
        "work": _work(artifacts),
        "limitations": ["Model outputs are not published.", "Report passages are not published.", "Missing artifacts are marked missing.", "Only committed artifacts supply measurements.", "Series definitions are kept separate.", "The population basis of the dataset employment series is unverified."],
        "provenance": {"commit": artifacts.commit, "artifacts": list(artifacts.provenance.values()),
                       "policy": "Committed artifacts only; numeric fields only."},
    }


def run(root: Path | str | None = None, output: Path | str | None = None) -> int:
    """Write the static report without downloads, model calls, or pipelines."""
    repository = Path(root) if root is not None else Path(__file__).resolve().parents[3]
    destination = Path(output) if output is not None else repository / "web/static/data/report.json"
    report = _no_dashes(build_report(repository))
    from labourlens.report.innovation import project_innovation

    report["innovation"] = project_innovation(repository, report)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Report written: {destination}")
    return 0
