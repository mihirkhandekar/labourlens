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


_SCOPE = ("2024-Q1", "2026-Q2")
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
_HELDOUT_V2_FILES = {_HELDOUT_V2_PAIRED, _HELDOUT_V2_ERRORS}
# Tool set v2 (D-046/D-048): separately keyed, never merged into the registered or X2 rows.
_TOOLFIX_CRITERIA = "experiments/tool-fix/criteria.json"
_TOOLFIX_PAIRED = {"toolset": "experiments/heldout-v2/paired-postfix-toolset.json", "r3_vs_hybrid": "experiments/heldout-v2/paired-postfix-r3-vs-hybrid.json"}
_TOOLFIX_EVAL = re.compile(r"experiments/eval/agent-(?:dev-X3|heldout-V2post-(?:r3|hybrid))/gpt-(?:6|5\.6)-luna\.(?:metrics\.json|cases\.jsonl)")
_E2EFIX_DIR = "experiments/threats/m7-e2efix-20261031/"
_E2EFIX_EXPERIMENT = "m7-e2efix-20261031"


def _corpus_version(path: str) -> str:
    """Explicit corpus label: v2 only for the separately labelled X1 artifacts, v3 only for dev X2."""
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
            or re.fullmatch(r"experiments/heldout/paired(?:-v3\.[234]|-corpus-v2)?\.txt", path) is not None
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


def _section(summary: str, rows: list, paths: list[str], **extra: object) -> dict:
    return {"status": "available" if rows else "missing", "summary": summary,
            "metrics": {}, "rows": rows, "provenance": sorted(set(paths)), **extra}


def _experiments(artifacts: _Artifacts, prefix: str) -> tuple[list, list]:
    rows, paths = [], []
    for path in artifacts.paths:
        if path.startswith(prefix) and path.endswith(".metrics.json"):
            if prefix == "experiments/eval/" and ("/agent-heldout-V2-" in path or _TOOLFIX_EVAL.fullmatch(path)):
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
    return _section("Metadata for official sources.", rows, provenance, metrics={"sources": len(rows), "by_type": dict(counts)})


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



def _ladder(artifacts: _Artifacts, path: str = "experiments/runs/dev-R-summary.json") -> dict:
    """Retrieval ladder R0-R3 (128 dev cases): numeric measurements only."""
    data = artifacts.mapping(path)
    configs = _numeric(data.get("metrics"))
    if not configs:
        return {}
    context = {}
    for item in data.get("end_to_end_context_coverage", []):
        if isinstance(item, dict) and _label(item.get("config")):
            context[item["config"]] = _selected(item, ("n", "gold_in_context_of_top8_chunks", "gold_in_first8_context_passages"))
    return {"corpus_version": _corpus_version(path),
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


_DECISION = re.compile(r"^### (D-\d{3}) \u2014 (.+)$", re.M)
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
                   "rows": dev_rows, "criteria": criteria, "all_criteria_passed": bool(criteria) and all(v["all_pass"] for v in criteria.values())},
        "v2post": {"label": "Post-freeze diagnostic. Not held-out, and not a replacement of the frozen held-out v2 result (D-045). The tool set was designed after the errors of these 65 cases were analysed, so any gain here is optimistic by construction.",
                   "post_freeze_diagnostic": True, "heldout": False, "replaces_frozen_result": False,
                   "gold_sha256": "e3d16597d542d33d106b4e9291aa3b92ca5fcdf19aa4d3c2b3319c0543efa542",
                   "rows": post_rows, "paired": paired, "tool_use": tool_use},
        "verdict": "Not adopted: the pre-declared dev criteria failed for both models. The default tool set is unchanged and the threat suite has not been run under tool set v2.",
        "provenance": sorted(set(paths)),
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
    tool_v2 = _tool_set_v2(artifacts)
    eval_paths = eval_paths + list((tool_v2 or {}).get("provenance", []))
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
        "retrieval": _section("Development retrieval comparisons. Configurations differ between experiments.", retrieval_rows, retrieval_paths + ladder.get("provenance", []) + ladder_v2.get("provenance", []), ladder=ladder, ladder_corpus_v2=ladder_v2),
        "answers": _section("Saved answer metrics. Model outputs are not published.", answer_rows, answer_paths,
                            limitations=["Costs that were not recorded are not estimated."]),
        "agent": _section("Bounded workflow measurements on statistics-only traces.", agent_rows, agent_paths + trace_paths, trace=trace, events=_saved_replay(artifacts)),
        "mcp": mcp,
        "reconciliation": reconciliation,
        "security": _section("Threat-suite measurements. They do not guarantee security. `postfix` and `e2efix` are separate labelled runs; neither replaces the registered rows.", security_rows, security_paths + postfix_paths + e2efix_paths, postfix=postfix_rows, e2efix=_e2efix(e2efix_rows)),
        "evaluation": _section("Development A1–A5 and registered held-out H-r3/H-hybrid luna runs. Measurements retain their recorded gold versions. Owner review complete 1 Nov 2026: all 403 labelling items (268 gold cases, 65 held-out v2 cases, 40 saved answers, 30 source checks) decided card by card by the owner's own click, after AI pre-review and after the runs were scored; one reviewer, not independent inter-rater evidence. Gold v3.5 development and all four registered held-out rescoring runs are complete on existing generated outputs; held-out stale judge entries were rejudged. `paired` holds the registered corpus-v1 comparison, current first, with v3.2–v3.4 history; `corpus_v2_diagnostic` is a separate extraction-only diagnostic; `dev_x2_regression_check` labels the corpus-v3 dev X2 rows (a regression check, not an ablation). `heldout_v2` is the signed held-out v2 run on corpus v3, reported separately and never pooled with the registered held-out.", eval_rows, eval_paths + [path for entry in paired + ([paired_v2] if paired_v2 else []) for path in entry["provenance"]] + list((v2_held or {}).get("provenance", [])),
                               errors={"scope": "rescored case records (experiments/eval, gold as recorded in each metrics file)", "counts": errors, "provenance": trace_paths}, paired=paired, corpus_v2_diagnostic=paired_v2, dev_x2_regression_check=_x2_check(x2_rows), heldout_v2=v2_held, tool_set_v2=tool_v2,
                               limitations=["Generation used AI-drafted gold before owner review; the owner then reviewed every gold case (one reviewer, after the runs were scored), and four change-clicks were not applied under the out-of-period policy, so labels are unchanged in gold v3.7.", "All 403 labelling items were decided by one reviewer's own click: a single person's post hoc review, not independent annotation or inter-rater evidence.", "Current v3.5 and historical paired intervals include zero; the comparison is inconclusive under the registered rule.", "Gold v3.5 changes HO-022 after held-out execution; rescoring is post-run adjudication, not a fresh frozen-gold experiment.", "Metric definitions differ between evaluation stages.", "Dev X2 (corpus v3, gold v3.6, crosscheck on, 14 runtime changes) is a regression check of the served system, not an ablation: several factors changed at once, and the ungrounded-number check was widened, so that metric is not comparable with A3 or X1."]),
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
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Report written: {destination}")
    return 0
