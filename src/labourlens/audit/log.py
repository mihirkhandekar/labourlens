"""Audit log and feedback log: append-only JSONL under data/audit/ (gitignored, local), for debugging, improvement and accountability.

One record per agent run (`runs-YYYY-MM-DD.jsonl`) and one per piece of user feedback (`feedback.jsonl`), joined by run_id.
Design rules:
- Everything passes through redaction (secrets, key shapes) before it is written.
- Records hold the question and the answer (needed to debug) but never raw MOM passages; evidence is referenced by id.
- Client identity is stored only as a salted hash (session and IP), never raw.
- Records carry the code version (git commit), prompt hashes and data manifest hash, so a run can be reproduced or compared.
- Writes are single-line appends under a lock; a failed audit write never breaks a user request (it is counted and logged to stderr).
- Retention: files are plain dated files; delete old ones with `labourlens audit-prune --days N`.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone

from labourlens import paths
from labourlens.mcp.redact import redact

SCHEMA_VERSION = 1
AUDIT_DIR = paths.DATA / "audit"
MAX_FIELD = 4000
_lock = threading.Lock()
_failures = 0


def _version() -> dict:
    v = {"git_commit": None}
    try:
        v["git_commit"] = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=3, cwd=paths.ROOT).stdout.strip() or None
    except Exception:  # noqa: BLE001
        pass
    man = paths.ROOT / "data" / "manifests" / "manifest.json"
    v["manifest_sha256"] = hashlib.sha256(man.read_bytes()).hexdigest()[:12] if man.exists() else None
    return v


_VERSION = _version()


def salted_hash(value: str | None) -> str | None:
    """Stable pseudonym for a session or IP. The salt comes from LABOURLENS_AUDIT_SALT (set one in production)."""
    if not value:
        return None
    salt = os.environ.get("LABOURLENS_AUDIT_SALT", "labourlens-dev-salt")
    return hashlib.sha256(f"{salt}|{value}".encode()).hexdigest()[:16]


def _clip(s: str | None, n: int = MAX_FIELD) -> str | None:
    return None if s is None else redact(s)[:n]


def _append(name: str, record: dict) -> None:
    global _failures
    try:
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        line = redact(json.dumps(record, ensure_ascii=False, default=str))
        with _lock, open(AUDIT_DIR / name, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:  # noqa: BLE001 - auditing must never break the request
        _failures += 1
        print(f"audit write failed: {type(e).__name__}", file=sys.stderr)


def run_record(res: dict, channel: str, session: str | None = None, ip: str | None = None, extra: dict | None = None) -> dict:
    """Build the audit record for one agent result (the dict returned by run_agent)."""
    trace = res["trace"]
    calls = [{"tool": e["detail"].get("tool"), "args": e["detail"].get("args"), "outcome": e["event"], "error_kind": e["detail"].get("error_kind"),
              "seconds": e["detail"].get("seconds")} for e in trace if e["node"] == "execute_tool"]
    guard = [{"node": e["node"], "event": e["event"], **{k: v for k, v in e["detail"].items() if k in ("findings", "input_flags")}}
             for e in trace if e["event"] in ("output_blocked",) or e["detail"].get("input_flags") or e["detail"].get("findings")]
    notes = next((e["detail"].get("data_quality_notes") for e in reversed(trace) if e["node"] == "assess_evidence"), None) or []
    a = res.get("answer")
    return {
        "schema": SCHEMA_VERSION, "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "run_id": res["run_id"], "channel": channel,
        "session": salted_hash(session), "client": salted_hash(ip), "question": _clip(res["question"], 1200),
        "question_sha256": hashlib.sha256(res["question"].encode()).hexdigest()[:16], "config": res["config"], "version": _VERSION,
        "outcome": res["outcome"], "status": a["status"] if a else None, "errors": [_clip(e, 300) for e in res.get("errors", [])],
        "rounds": res["rounds"], "tool_calls": calls, "operational_failures": sum(1 for c in calls if c["outcome"] == "operational_failure"),
        "tool_errors": sum(1 for c in calls if c["outcome"] == "error"), "guard_events": guard, "data_quality_notes": notes,
        "evidence_ids": [e["id"] for e in res.get("evidence", [])], "cited_ids": res.get("cited_ids", []),
        "n_claims": len(a["claims"]) if a else 0, "caveats": [_clip(c, 300) for c in (a["caveats"] if a else [])],
        "answer_summary": _clip(a["summary"], 600) if a else None,
        "attempts": sum(1 for e in trace if e["node"] == "generate_answer" and e["event"] == "generated"),
        "usage": res["usage"], "seconds": res["seconds"], **(extra or {}),
    }


def log_run(res: dict, channel: str, session: str | None = None, ip: str | None = None, extra: dict | None = None) -> None:
    rec = run_record(res, channel, session, ip, extra)
    _append(f"runs-{rec['ts'][:10]}.jsonl", rec)


def log_feedback(run_id: str, rating: str, comment: str | None = None, session: str | None = None, tags: list[str] | None = None) -> dict:
    """rating is 'up' or 'down'. The comment is length-capped and redacted. Returns the stored record."""
    if rating not in ("up", "down"):
        raise ValueError("rating must be 'up' or 'down'")
    rec = {"schema": SCHEMA_VERSION, "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "run_id": run_id[:32], "rating": rating,
           "comment": _clip((comment or "").replace("\x00", ""), 1000), "tags": [t[:40] for t in (tags or [])][:6], "session": salted_hash(session)}
    _append("feedback.jsonl", rec)
    return rec


def read_runs() -> list[dict]:
    out = []
    for f in sorted(AUDIT_DIR.glob("runs-*.jsonl")):
        out += [json.loads(line) for line in f.read_text(encoding="utf-8").splitlines() if line.strip()]
    return out


def read_feedback() -> list[dict]:
    f = AUDIT_DIR / "feedback.jsonl"
    return [json.loads(line) for line in f.read_text(encoding="utf-8").splitlines() if line.strip()] if f.exists() else []


def failures() -> int:
    return _failures


def prune(days: int) -> list[str]:
    cutoff = time.time() - days * 86400
    gone = []
    for f in AUDIT_DIR.glob("runs-*.jsonl"):
        if f.stat().st_mtime < cutoff:
            f.unlink()
            gone.append(f.name)
    return gone


def report() -> str:
    """Operational summary for debugging and improvement: outcomes, failure kinds, guards, cost, latency, negative feedback."""
    import statistics

    runs, fb = read_runs(), read_feedback()
    if not runs:
        return "No audit records yet."
    by = lambda key: sorted(((k, sum(1 for r in runs if r[key] == k)) for k in {r[key] for r in runs}), key=lambda x: -x[1])  # noqa: E731
    secs = sorted(r["seconds"] for r in runs)
    down = [f for f in fb if f["rating"] == "down"]
    run_by_id = {r["run_id"]: r for r in runs}
    lines = [f"# Audit report ({len(runs)} runs, {len(fb)} feedback records)", "",
             f"- channels: {dict(by('channel'))}", f"- outcomes: {dict(by('outcome'))}",
             f"- operational failures: {sum(r['operational_failures'] for r in runs)} tool calls in {sum(1 for r in runs if r['operational_failures'])} runs",
             f"- correctable tool errors: {sum(r['tool_errors'] for r in runs)} calls", f"- runs with a guard event (input flagged or output blocked): {sum(1 for r in runs if r['guard_events'])}",
             f"- runs with data-quality notes: {sum(1 for r in runs if r['data_quality_notes'])}",
             f"- latency p50 {statistics.median(secs):.1f} s, p95 {secs[max(0, int(len(secs) * .95) - 1)]:.1f} s; cost total ${sum(r['usage']['cost_usd'] for r in runs):.4f}",
             f"- feedback: {sum(1 for f in fb if f['rating'] == 'up')} up, {len(down)} down", ""]
    if down:
        lines += ["## Negative feedback to review (join on run_id)", ""]
        for f in down[-20:]:
            r = run_by_id.get(f["run_id"])
            lines.append(f"- {f['run_id']} {f['ts']}: outcome={r['outcome'] if r else 'unknown run'}; comment: {f['comment'] or '(none)'}")
    return "\n".join(lines) + "\n"


def show(run_id: str) -> str:
    """Timeline of one run, from the saved trace (data/runs/agent/<run_id>.json) plus its audit record."""
    f = paths.DATA / "runs" / "agent" / f"{run_id}.json"
    if not f.exists():
        return f"no saved trace for {run_id}"
    d = json.loads(f.read_text())
    out = [f"run {run_id}: outcome={d['outcome']} seconds={d['seconds']} cost=${d['usage']['cost_usd']:.5f}", f"question: {d['question']}"]
    for e in d["trace"]:
        out.append(f"  {e['node']:<18} {e['event']:<22} {json.dumps({k: v for k, v in e['detail'].items() if k != 'result'}, default=str)[:220]}")
    return "\n".join(out)
