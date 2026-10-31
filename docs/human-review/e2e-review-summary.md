# End-to-end review: summary and finding status

On 31 Oct 2026 five independent AI reviewers (not human review) traced the whole flow. Each finding was checked against code or artefacts before a fix; some were disputed or narrowed. Fix details: `docs/experiments/m7-e2e-fixes.md` (runtime, deploy), `docs/experiments/m7-eval-fixes.md` (evaluation) and decision D-043 in `docs/decisions.md`. Statuses: **fixed**, **narrowed** (partly fixed), **deferred** (reason given), **owner** (needs an owner decision or action). A blank fixer record is marked "no fix recorded".

| Report | Scope | P0 | P1 | P2 |
|---|---|---:|---:|---:|
| [Data](e2e-review-data.md) | sources, manifest, parsing, data sheet | 0 | 5 | 9 |
| [Runtime and answer path](e2e-review-runtime-answer-path.md) | retrieval, agent, answer, MCP | 0 | 5 | 9 |
| [Evaluation](e2e-review-evaluation.md) | gold, scoring, held-out, freeze | 0 | 7 | 10 |
| [Security and deploy](e2e-review-security-deploy.md) | web, rights, audit, deployment | 0 | 4 | 9 |
| [Deliverables](e2e-review-deliverables.md) | documents, website, demo | 3 | 7 | 7 |

## Data

| Finding | Status |
|---|---|
| P1-1 data sheet stale | fixed (rewritten with v3 numbers) |
| P1-2 which corpus is current | fixed (corpus-versions statement in README and docs) |
| P1-3 three datasets labelled verified-open | fixed (now `assumed_open_unverified`, local-only) |
| P1-4 wrong `raw_path` on re-fetch | fixed (CSV selection in `store_snapshot`) |
| P1-5 MTI tables labelled garbled | owner: refined rule written but not applied; 44 MTI passages would change and need rebuild, reindex and re-embed |
| P2-1 failed fetch overwrites manifest entry | deferred |
| P2-2 no writer lock for fetch/build/export | deferred |
| P2-7 stale `data/export/*.json` | owner: run `labourlens export` |
| P2-9 reconcile covers 4 quarters | deferred |
| P2-3, P2-4, P2-5, P2-6, P2-8 | no fix recorded (fetch status reporting was made honest) |

## Runtime and answer path

| Finding | Status |
|---|---|
| 1 validated citations dropped in web result | fixed (citations shown 4,188 to 5,172 of 5,194; runs with an uncited claim 451 to 8) |
| 2 fabricated numbers pass as answered | narrowed: wider soft check and browser notice; a hard error would change which answers are invalid and needs a development re-run (owner) |
| 3 T-I06 monthly versus quarterly false positive | fixed with regression tests; guard not re-measured since |
| 4 no LLM deadline | fixed (80 s run deadline in web app) |
| 5 quarantined MCP rows hidden | fixed |
| 6 provider-shape errors escape graph | fixed |
| 7 round-2 planner failure discards evidence | deferred (needs design) |
| 8 cross-check recall near zero | deferred (needs design; limit disclosed) |
| 9 `enforce` rewrites whole claim | deferred |
| 10 web hides operational outcomes | deferred |
| 11 planner sees locator text | deferred |
| 12 same-series guard and rounding | deferred |
| 13, 14 BM25 persistence, embedding cache growth | deferred |

## Evaluation

| Finding | Status |
|---|---|
| P1-1 `agent-exp` overwrites frozen runs | fixed (`--force` required) |
| P1-2 `eval` under a different gold | fixed (`--allow-gold-mismatch`; gold v3.2 to v3.5 archived) |
| P1-3 freeze not independently timestamped | disclosed (Provenance limits in the evaluation report); cannot be repaired |
| P1-4 report stale on T-I06 guard | fixed (docs) |
| P1-5 refined scorer is post hoc | disclosed, strict result kept beside it; not changeable |
| P1-6 v2 acceptance rule underpowered | fixed by revision before any run (D-042); owner sign-off pending |
| P1-7 `paired` ignores gold | fixed |
| P2-1 p95 one rank low | fixed (held-out r3 luna6 26.6 to 27.8 s; dev A3 luna6 35.6 to 37.0 s) |
| P2-2 header-only report on missing runs | fixed |
| P2-6 error panel pooled stale scores | fixed (behaviour mismatches 418 to 393) |
| P2-7 README gold hash | fixed (v3.5 and v3.6 both stated) |
| P2-3 `paired.txt` has no producing code | deferred |
| P2-4 A1/A2 versus A3 case sets | deferred |
| P2-5 lenient calculation scorer | deferred (changing it alters published numbers) |
| P2-8 untracked snapshot directories | owner: commit or ignore |
| P2-9 judge shares provider with generators | deferred (stated limitation) |
| P2-10 threat suite saturates | deferred (stated limitation) |

## Security and deploy

| Finding | Status |
|---|---|
| 1 stale runtime-data list | fixed |
| 2 corpus unidentified in API and audit | fixed (`/healthz` and audit carry a fingerprint) |
| 3 one address can lock all logins | fixed (per-address lock) |
| 4 rights window evadable | narrowed: normalised window plus 80-character window; still a heuristic |
| 5 no run deadline | fixed |
| 7 feedback unbound and uncapped | fixed |
| 8 incomplete retention | fixed (`audit-prune` extended; no timer installed) |
| 9 no commit in audit records | fixed |
| 11 docs conflict with live site | fixed (README, deploy, progress) |
| 6 embedding cache rewrite per query | deferred |
| 10 real client address unverified | deferred (needs a live check) |
| 12, 13 partial pinning, log hygiene | deferred |

## Deliverables

| Finding | Status |
|---|---|
| P0-1 T-I06 contradictions | fixed |
| P0-2 scenario 8 not shown end to end | owner: record an MCP-backed agent answer in `artifacts/mcp-agent-demo.md` (to be recorded) |
| P0-3 fresh-clone build and plain `pytest` | narrowed: corpus tests skip when `data/` is absent; the three untracked snapshot directories are for the owner to commit |
| P1-1 corpus v2 versus v3 numbers | fixed (docs and site text); report counts follow `labourlens export` then `build-report` |
| P1-2 deployment status | fixed |
| P1-3 stale website strings | fixed |
| P1-4 innovation note length | fixed (about 840 words) |
| P1-5 README as changelog | fixed |
| P1-6 demo script | fixed (20:00 total) |
| P1-7 architecture diagram | narrowed: cross-check node and review box updated; no exported PNG |
| P2-1, P2-2, P2-3 | fixed (held-out v2 paragraph, review rubric, progress table) |
| P2-4 untracked screenshots | owner |
| P2-5 old "T-I06 open" string in copy audit | left as history |
| P2-6 private study notes | deferred (`study/` is private) |
| P2-7 repeated caveat blocks | deferred |
