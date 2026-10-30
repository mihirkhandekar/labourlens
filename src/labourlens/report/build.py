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
}


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
        listed = self._git("ls-files", "-z", "--", "data/export", "experiments", "docs/mcp-demo-transcript.md", "data/manifests")
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
        return (
            (p.parent.as_posix() == "data/export" and p.suffix == ".json")
            or (path.startswith("experiments/") and p.suffix in {".json", ".jsonl", ".md"})
            or path == "docs/mcp-demo-transcript.md"
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
            data = artifacts.mapping(path)
            metrics = _numeric(data.get("metrics", data))
            if not metrics:
                continue
            row = {"id": path.removesuffix(".metrics.json"), "metrics": metrics, "provenance": [path]}
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
    trace, paths, errors = [], [], Counter()
    fields = ("tool_calls", "rounds", "seconds", "cost_usd", "tool_errors", "attempts", "prompt_tokens", "completion_tokens", "behavior_ok", "valid", "operational_failure")
    for path in artifacts.paths:
        if not path.startswith("experiments/runs/agent-") or not path.endswith(".scores.jsonl"):
            continue
        records = artifacts.load(path)
        if not isinstance(records, list):
            continue
        paths.append(path)
        for record in records:
            if not isinstance(record, dict):
                continue
            row = {"run_id": path.removesuffix(".scores.jsonl"), **_selected(record, fields)}
            for key in ("case_id", "family"):
                if _label(record.get(key)):
                    row[key] = record[key]
            # Counts and tool names only: never call arguments or results.
            row["tools_used"] = [tool for tool in record.get("tools_used", []) if tool in {"get_series", "get_statistic", "search_reports", "calculate", "get_source", "compare_periods"}]
            trace.append(row)
            for key in ("tool_errors", "operational_failure", "n_ungrounded_numbers"):
                value = record.get(key)
                if _number(value) or isinstance(value, bool):
                    errors[key] += value
            if record.get("behavior_ok") is False:
                errors["behavior_mismatch"] += 1
            if record.get("valid") is False:
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



def build_report(root: Path) -> dict:
    artifacts = _Artifacts(root)
    sources = _sources(artifacts)
    charts = _charts(artifacts)
    summary = _summary(artifacts)
    retrieval_rows, retrieval_paths = _experiments(artifacts, "experiments/runs/dev-")
    answer_rows, answer_paths = _experiments(artifacts, "experiments/runs/answer-")
    _answer_costs(artifacts, answer_rows)
    answer_paths = sorted(set(answer_paths + [path for row in answer_rows for path in row["provenance"]]))
    reconciliation = _reconciliation(artifacts)
    agent_rows, agent_paths = _experiments(artifacts, "experiments/runs/agent-")
    eval_rows, eval_paths = _experiments(artifacts, "experiments/eval/")
    security_rows, security_paths = _experiments(artifacts, "experiments/threats/runs/")
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
        "retrieval": _section("Development retrieval comparisons. Configurations differ between experiments.", retrieval_rows, retrieval_paths),
        "answers": _section("Saved answer metrics. Model outputs are not published.", answer_rows, answer_paths,
                            limitations=["Costs that were not recorded are not estimated."]),
        "agent": _section("Bounded workflow measurements on statistics-only traces.", agent_rows, agent_paths + trace_paths, trace=trace, events=_saved_replay(artifacts)),
        "mcp": mcp,
        "reconciliation": reconciliation,
        "security": _section("Threat-suite measurements. They do not guarantee security.", security_rows, security_paths),
        "evaluation": _section("Recorded confidence intervals and AI-judged strata.", eval_rows, eval_paths,
                               errors={"scope": "agent score records", "counts": errors, "provenance": trace_paths},
                               limitations=["Development results are not held-out estimates.", "AI judgments are not human review.", "Metric definitions differ between evaluation stages."]),
        "quality": _section("Validation outcomes, including warnings.", quality_rows, [quality_path], metrics=_numeric(quality_data.get("summary", {}))),
        "limitations": ["Model outputs are not published.", "Report passages are not published.", "Missing artifacts are marked missing.", "Only committed artifacts supply measurements.", "Series definitions are kept separate.", "The population basis of the dataset employment series is unverified."],
        "provenance": {"commit": artifacts.commit, "artifacts": list(artifacts.provenance.values()),
                       "policy": "Committed artifacts only; numeric fields only."},
    }


def run(root: Path | str | None = None, output: Path | str | None = None) -> int:
    """Write the static report without downloads, model calls, or pipelines."""
    repository = Path(root) if root is not None else Path(__file__).resolve().parents[3]
    destination = Path(output) if output is not None else repository / "web/static/data/report.json"
    report = build_report(repository)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Report written: {destination}")
    return 0
