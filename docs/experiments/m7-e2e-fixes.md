# M7 end-to-end review: runtime and deploy fixes

Source reports: `docs/human-review/e2e-review-runtime-answer-path.md` and `docs/human-review/e2e-review-security-deploy.md`.
Every finding below was checked against the code before fixing. Nothing here re-runs a frozen experiment, so no published
evaluation number changes. Several changes alter the behaviour of the **served** system compared with the **evaluated**
system; those are listed in the behaviour-change table so a reader can tell the two apart.

## Behaviour changes (served system vs the evaluated system)

| # | Change | Affects evaluated results? |
|---|---|---|
| B1 | The web projection uses the validator's quote matching (`answer.validate.quote_in`). A quote may span a PDF line break, differ in case, or be reused by several claims and still keep its citation. A quote repeated inside one claim is listed once. | No: presentation only. Offline runs score the raw answer, not the projection. |
| B2 | The ungrounded-number check also covers the summary and the caveats, using key figures only (decimals, comma-grouped numbers, integers of 100 or more; years, quarter digits and small counts are ignored). **Status semantics are unchanged**: it stays a soft finding in the trace (`ungrounded_numbers`), it does not make an answer `invalid`. | No: the answer, outcome and score are the same. Trace events gain more entries. |
| B3 | The browser projection adds `answer.ungrounded_numbers` and a caveat "Number not found in evidence: ..." when the last `validate_answer` found a key figure that is absent from the evidence. | No (web only). The served card now shows a notice the evaluated card never showed. |
| B4 | `crosscheck.figures` ignores any sentence that names a month and year. A monthly figure is no longer compared with the quarterly dataset value. | Slightly: the T-I06 threat result was measured with the old rule. The planted-figure threat uses quarter wording, which is still checked (`test_planted_figure_is_detected...`). The frozen `experiments/threats` outputs are untouched. |
| B5 | `AgentConfig.run_deadline_s` (default `None`) bounds the total time of the planner and answer LLM calls. The web app sets 80 s (`Settings.run_deadline_s`, below the 90 s request timeout). Offline runs keep `None` and call `llm.chat` exactly as before. `llm.chat` now also retries a 429/5xx inside a deadline while time remains (it raised at once before). | No for evaluated runs. A slow provider now ends a web run as `operational_failure` instead of holding a demo slot. |
| B6 | A malformed provider body (`KeyError`, bad JSON envelope, missing `usage`) raises `LLMError`; any exception in the planner or answer node becomes `operational_failure`; a planner reply without `decision`/`calls`/`note` is an `operational_failure` too (it was a `KeyError`). | No. |
| B7 | MCP route: when the client quarantines rows, the agent says so ("withheld by the MCP client as unsafe ... not because the dataset lacks it") instead of "the dataset has no row". | No: the evaluated runs used the direct route. |
| B8 | Startup fails fast when a chunk has no cached vector and `LABOURLENS_ALLOW_EMBED=0` (the container default, set in `Dockerfile` and compose). Local runs keep the old default (embedding allowed). Per-question embeddings still call the API. | No. |
| B9 | `/healthz` returns `corpus` (`passage_set_sha256`, `passages`, `chunks`); audit records carry `version.corpus` and fall back to `LABOURLENS_BUILD` for the commit when git is absent. Saved run JSON also gets a `corpus` key. | No. |
| B10 | Login lock is per client address (10 failures in 10 minutes). A global threshold (200) still refuses invalid codes, but a valid code is never refused by either lock. The per-address request limit (5 a minute) is unchanged. | No. |
| B11 | Feedback is accepted only for run ids that the same session started (404 otherwise); `feedback.jsonl` is capped at 2 MiB. | No. |
| B12 | Rights window: 13-word window on letters and digits only (punctuation, hyphens, zero-width characters and case ignored) plus an 80-character window on the space-free text. | No for scores. On saved answered runs the share with at least one withheld text field rises from 253 of 2,161 (11.7%) to 394 (18.2%); almost all of the rise is punctuation normalisation of genuine verbatim overlap. |
| B13 | `audit-prune` also removes old `events-*.jsonl` and drops feedback records older than the cutoff (unreadable lines are kept). | No. |
| B14 | `deploy/runtime-data.txt` ships `cache.npz` (not the stale `keys.json`/`vectors.npy` pair) and the three passage files that were missing. | No. |

## Findings

### Fixed

| Report | Finding | Fix | Test |
|---|---|---|---|
| Runtime 1 (P1) | Web layer dropped validator-accepted citations | One shared `quote_in`; reuse across claims kept (B1) | `tests/web/test_runtime_fixes.py` (line break, reuse, still drops absent quotes) |
| Runtime 2 (P1) | Fabricated numbers pass as answered | Summary and caveats checked; browser notice (B2, B3). Status not changed. | `test_fabricated_numbers_...`, `test_browser_projection_...` |
| Runtime 3 (P1) | T-I06 monthly vs quarterly false positive | Month mentions skipped (B4) | `tests/retrieval/test_crosscheck.py::test_monthly_figure_...` and `..._quarterly_figure_that_disagrees_is_still_detected` |
| Runtime 4 / Security 5 | No deadline on LLM calls | Run-level deadline (B5) | `tests/retrieval/test_runtime_fixes.py`, `test_default_web_runner_passes_a_run_deadline` |
| Runtime 5 | Quarantined MCP rows hidden | Count carried on the rows, reported in notes and tool message (B7) | `test_quarantined_mcp_rows_...` |
| Runtime 6 | `KeyError` escaped `run_agent` | B6 | `test_unexpected_provider_exception_...`, `test_malformed_provider_body_...` |
| Security 1 | Stale runtime-data list | B14, plus `test_runtime_data_list_covers_every_local_passage_file_and_the_embedding_snapshot` and the corpus-marked `test_listed_runtime_files_alone_start_the_runtime_offline` (copies only the listed files to a temp directory and starts the runtime with embedding forbidden) | as named |
| Security 1, 2 | Startup could call the embeddings API; corpus unidentified | B8, B9 | `test_missing_chunk_vectors_stop_startup_...`, `test_healthz_reports_the_corpus_fingerprint`, `test_audit_record_carries_corpus_and_build_fallback` |
| Security 3 | One address could lock all logins | B10 | `test_login_lock_is_per_address_...`, `test_global_failure_threshold_...` |
| Security 4 | Rights window evadable | B12 | `test_obfuscated_copy_of_evidence_is_withheld` (case, spacing, punctuation, hyphen, zero-width, line break), `test_short_independent_paraphrase_is_not_withheld` |
| Security 7 | Feedback unbound, no size cap | B11 | `test_feedback_is_bound_to_the_session_...`, `test_feedback_file_has_a_size_cap` |
| Security 8 | Prune incomplete | B13 | `test_prune_covers_events_and_old_feedback_records` |
| Security 9 | No commit in production audit records | B9 | as above |

Existing tests were updated to the new contracts: feedback tests now ask first; the global-lock test became the per-address and
global-threshold tests; the quote-limit test now checks uniqueness per claim and counts unique quotes against the 120-word budget;
`/healthz` has a `corpus` key; one `run_agent` fake accepts the new `cfg` argument.

### Measured on saved runs (`data/runs/agent`, read only; 2,161 answered runs that kept `evidence_text`)

| Measure | Before | After |
|---|---|---|
| Citations the validator accepts | 5,194 | 5,194 |
| Citations shown in the browser projection | 4,188 (80.6%) | 5,172 (99.6%) |
| Claims shown with no citation | 633 of 3,894 | 12 |
| Answered runs with at least one uncited claim | 451 (20.9%) | 8 (0.4%) |

The 22 citations still dropped are limited by the 120-word quote budget or the once-per-claim rule (not broken down further). Answered runs that would show the
new "Number not found" notice (key figures only): 112 of 2,161 (5.2%). Free-text-only flags (summary or caveats): 92 of 2,161.
These are flags to review, not proven errors: a figure the model derived itself (for example a rounded change) is flagged too.
Scripts were run from `/tmp` and are not committed.

### Disputed or narrowed

- Runtime 2 asked for a hard error; not done. Making it an error changes which answers count as `invalid` and would need a re-run of the
  development set. The visible notice and wider soft check are in; the hard rule is a decision for the owner.
- The runtime review's "minimum quote length" idea was not adopted: a short quote (a figure) is legitimate for a statistic.
- Alias extension of the crosscheck to the three new datasets was not trivial (they are not persons or percentages in the
  closed grammar); left out.

### Deferred (not in this slice)

Runtime 7 (round-2 planner failure after good evidence), 8 (crosscheck recall; sentence joining), 9 (`enforce` rewrite), 10 (web
`unavailable` status), 11 (planner sees locator text), 12 (`_fmt` rounding), 13 and 14 (persisted BM25 wording; query-vector
cache) and Security 6, 10 to 13. Reason: none is a P1; each needs its own design or a live check (Caddy log, provider
spend cap) and was not asked for in this pass.

## Section for `docs/deploy.md` (DocsFix to merge)

**Corpus identity.** `GET /healthz` returns `{"status","version","corpus"}`. `corpus.passage_set_sha256` is a hash of the sorted
passage ids (each id embeds a content hash), with `passages` and `chunks` counts. After an upload, compare it with the local value
(on the machine that built the corpus: `uv run python -c 'from labourlens.retrieval import chunk as c, runtime as r; p=c.load_passages(); k=c.build_chunks(c.CONFIGS[r.CHUNK_CONFIG], p); print(r.corpus_fingerprint({x["passage_id"]:x for x in p}, {y.chunk_id:y for y in k}))'`; it printed `d402120f6f8f`, 16,419 passages, 1,847 chunks on 31 Oct 2026) before
assuming v1 or v2 is served. Audit records carry the same value under `version.corpus`.

**No embedding at startup.** The container sets `LABOURLENS_ALLOW_EMBED=0`. If `cache.npz` lacks a vector for any chunk the app
exits at start with "embedding cache incomplete", the health check fails and `deploy.sh` rolls back; it never calls the paid API.
`deploy/runtime-data.txt` lists exactly what must be uploaded (`scripts/upload-corpus.sh`), including `cache.npz`.

**Retention.** Run once a day (cron or a systemd timer) from `/srv/labourlens/deploy` as the deploy user:

```
IMAGE_TAG="$(cat /srv/labourlens/state/current_tag)" docker compose --env-file /srv/labourlens/.env \
  run --rm --no-deps --entrypoint labourlens app audit-prune --days 30
```

It deletes audit run logs, daily event files and saved traces older than 30 days and drops feedback records older than 30 days.
It does not touch `budget.json`. No timer is installed by this change.
