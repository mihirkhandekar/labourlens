# Audit, logging and feedback

Purpose: debugging a single bad answer, finding systematic failures, improving the system from user feedback, and accountability. Implementation: `src/labourlens/audit/log.py`, web hooks in `src/labourlens/report/`. Tests: `tests/test_audit_and_notes.py`, `tests/web/test_audit.py`.

## What is recorded (all local, under `data/audit/`, gitignored)

| File | One line per | Key fields |
|---|---|---|
| `runs-YYYY-MM-DD.jsonl` | agent run | run_id, timestamp, channel (web, cli), salted session and client hashes, question (redacted, clipped) and its hash, config (models and prompt versions), code version (git commit) and data manifest hash, outcome and answer status, tool calls (tool, arguments, outcome, error kind, seconds), operational failures and correctable errors, guard events (input flagged, output blocked), data-quality notes, evidence ids and cited ids, claim count, caveats, answer summary, token usage, cost, latency |
| `feedback.jsonl` | user feedback | run_id, thumbs up or down, tags (wrong_number, wrong_source, missing_info, other), comment (clipped, redacted), session hash |
| `events-YYYY-MM-DD.jsonl` | rejected or administrative request | kind (rate limited, budget exhausted, unauthenticated, kill switch, oversized, bad input), hashed identifiers, route, status, generic reason |
| `data/runs/agent/<run_id>.json` | full trace of a run | every node event with details, redacted; the audit record points to it by run_id |

Never recorded: API keys or secrets (values and key-shaped strings are redacted before every write), raw IP addresses or session ids (salted hashes only; set `LABOURLENS_AUDIT_SALT` in production), whole MOM passages (evidence is stored as ids; the answer summary and caveats can contain short quotes).

## Using it

```
uv run labourlens audit-report          # outcomes, failure kinds, guard events, latency, cost, negative feedback to review
uv run labourlens audit-show <run_id>   # timeline of one run from its saved trace
uv run labourlens audit-prune --days 30 # delete old run logs
```
Feedback joins to runs on `run_id`, so a thumbs-down opens the exact trace, config and code version that produced the answer. Improvement loop (D-011, a proposal rather than RLHF): review negative feedback weekly, add reproducible failures as new gold cases (marked draft until a human reviews them), re-run the evaluation, then change prompts or retrieval.

## Properties
- An audit write failure never breaks a request: it is counted and reported on stderr (tested).
- Records are single-line appends under a lock, so concurrent runs do not interleave.
- Retention is by file date; deletion is explicit. Data-subject requests: delete by `session` hash.
- The same record schema is used for batch experiments and live use, so offline findings and production behaviour can be compared.

## Missing data and conflicting information (agent behaviour)
Code, not the model, detects these and passes notes to the answer step in a non-citeable `<data_quality_notes>` block (`src/labourlens/agent/tools.py`): a period inside the requested range with no row, a null value the source marks unavailable, more than one series (population, adjustment or indicator) in one result, and advance and final releases of the same quarter in one evidence set. The answer prompt (`answer_v4`, rule 9) tells the model never to estimate such values, to report what is missing and answer the rest, and to report conflicting versions with source and stage rather than choose silently. Operational failures (tool down, timeout) are a different class: they end in an operational-failure outcome, never in "no data". Effect on quality: see the A1 versus A2 experiment in `docs/experiments/`.
