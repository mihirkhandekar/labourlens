Report of the security, privacy and deployment area of the end-to-end review (31 Oct 2026). The reviewer was an AI agent with read, search and glob tools only; it made three GET requests to the live site and ran no shell commands, so the checks it could not do are listed under Limits. This is AI review, not human review. Nothing from MOM or MTI is quoted. Finding status is tracked in [`e2e-review-summary.md`](e2e-review-summary.md).

# E2E review: security, privacy, deployment

> AI review (not human review). State as of 31 Oct 2026, before the final owner review of 1 Nov: counts such as "45 owner-reviewed" or "125 cards" describe that day. Status of each finding: [`e2e-review-summary.md`](e2e-review-summary.md).

**Counts:** P0 0, P1 4, P2 9.

## 1. Flow as traced

| Step | Code path | Input → output / where state lives |
|---|---|---|
| Edge | Caddy (`deploy/Caddyfile`) | Terminates TLS. Replaces `X-Forwarded-For` with the TCP peer address. 16 KB body cap. The access log drops the query string, cookies and the forwarded-for header. Adds HSTS, COOP and CORP. |
| App | `report/serve.py` → `report/app.py:create_app` | One uvicorn worker. Trusts proxy headers only from 172.30.0.2. |
| Middleware | `app.py` `security()` | 8 KiB body cap (`app.py:~296`). Sets CSP, nosniff, no-referrer, X-Frame-Options, Permissions-Policy. API responses get `no-store`. Rejections go to `web_audit.log_event`. |
| Login | `/api/login` | Origin check, per-IP limit 5/min, 50 global failures per 10 min. Compares SHA-256 digests with `compare_digest`. Issues an HMAC-signed cookie (HttpOnly, SameSite=Strict, Secure when the proxy reports https). Sessions live in memory. |
| Ask | `/api/ask` | `authorize` (cookie + Origin) → per-code limit 10/min and per-IP 20/min → 1000-character cap → budget check → persist a $0.05 reservation to `data/audit/budget.json` → active-run cap of 2 → `run_agent` in a thread → `public_result` → `redact_values` → reconcile cost. |
| Projection | `_bounded_answer`, `public_result` | Withholds free text sharing a 13-word window with evidence. Caps 12 claims, 3 citations per claim, 40 words per quote, 120 quoted words per answer. Cards show only cited quotes that are substrings of the evidence. The trace detail keys are whitelisted. |
| Feedback | `/api/feedback` | Strips tags, requires 12-hex `run_id`, tag enum, redacts, writes `data/audit/feedback.jsonl`. |
| Audit | `audit/log.py` | `runs-DATE.jsonl` holds the redacted question and answer summary, with HMAC-hashed session and IP. `data/runs/agent/<id>.json` holds the trace without evidence text unless `LABOURLENS_DEBUG_EVIDENCE=true`. `prune` is manual. |
| Static | `/static` (StaticFiles), `/`, `/workbench` | `web/` only. `report.json` has no quote or text fields (grep). Rendering uses `textContent`; no `innerHTML`, `eval` or `document.write` in the JS (grep). Links go through `safeLink`, which allows https only. |
| MCP HTTP | `mcp/http_server.py` | Bearer token ≥24 characters, constant-time compare, bare 401, loopback only, DNS-rebinding protection, 64 KiB cap. In compose it is a sidecar in the app's network namespace with its own env file. |
| Deploy | `.github/workflows/deploy.yml` → `deploy/deploy.sh up <sha>` | Tests → build context check → image content check → push to GHCR → ssh deploy with a pinned host key → compose up with `--wait` → edge `/healthz` check → automatic rollback to the previous tag. |
| Host | `scripts/droplet-bootstrap.sh` | Key-only ssh, fail2ban, ufw 22/80/443, unattended upgrades, 1 GiB swap. |
| Container | `Dockerfile`, `deploy/docker-compose.yml` | Non-root uid 10001, read-only root, cap_drop ALL, no-new-privileges, memory and pids limits. The corpus is bind-mounted, not baked into the image. |

**Live site (GET only):**
- `/healthz` returns `{"status":"ok","version":"0.1.0+f7cab827…"}`, which equals the local HEAD and `origin/master`.
- `/api/status` returns `{"enabled":true,"authenticated":false}`.
- `/openapi.json` returned an empty body, consistent with `docs_url`/`openapi_url=None`.
- I could not read response headers with my tools.

## 2. Findings

| # | Sev | Finding | Evidence | Impact | Fix |
|---|---|---|---|---|---|
| 1 | P1 | The runtime-data list is stale against the local corpus. The next upload plus restart can crash the app or trigger paid embedding calls at startup. | `deploy/runtime-data.txt` lists `keys.json` and `vectors.npy` only. Local `data/index/embeddings/text-embedding-3-large/` now holds `cache.npz` (43.7 MB, 41 min old) beside `keys.json`/`vectors.npy` (15 h old). `dense.py:_load` prefers `cache.npz`. Three local passage files are not in the list: `mti-2026-q2-feature-ai-employment`, `mom-nwc-lower-wage2025`, `mom-wage-practices2025`. `Shared()` runs `DenseIndex(chunks)` → `embed()` at startup (`runtime.py:18`, `dense.py:~160`). Any chunk missing from the cache is requested from the OpenAI API. `tests/web/test_deploy_files.py` checks list hygiene, not completeness. | **Fact:** the list and local data disagree. **Inference:** uploading v2 data with only the v1 vector files makes startup embed the missing chunks. With no key that is `EmbeddingError`, an unhealthy container and a failed compose `--wait`. `deploy.sh` rolls the image back, but the data directory is shared, so rollback does not help. | Add `cache.npz` and the new passage files to the list. Add a test that rebuilds the chunk set and asserts every chunk hash is in the shipped cache. Fail startup with an explicit "cache incomplete" message instead of calling the API. |
| 2 | P1 | Nothing in the live API or in audit records identifies which corpus is served. | `/healthz` returns only the code version. `audit/log.py:_VERSION` hashes `manifest.json` only, which is the structured-data manifest, not the passages. `docs/deploy.md` §6 describes the live data as 13,484 passages (v1). Architecture §1 says local passages are v2 (15,915). | Eval numbers are tagged "frozen corpus v1". An assessor cannot tell whether live answers come from v1 or v2. | Put a passage-set hash and chunk count in `/healthz` and in the audit `version`. State the served corpus in README and `docs/deploy.md`. |
| 3 | P1 | One IP can lock every login indefinitely. | `app.py` login: `hit(("login", ip), 5)` per 60 s, then `if len(login_failures) >= 50 → 429` over a 600 s window, and the check runs before the code compare. 5 failures/min × 10 min = 50. | **Inference from the arithmetic, not exercised:** an anonymous script from one address blocks even valid codes, which stops assessors signing in. | Apply the lock per client address. Raise the global threshold. Let a valid code through while locked; with codes ≥16 characters the lock adds little. |
| 4 | P1 | The rights boundary is a heuristic and is probably evadable. | `_bounded_answer`: `casefold().split()` and a 13-word exact window, applied to claim, summary and caveat text. A model told to space, hyphenate or change the punctuation of a passage produces different tokens. One search returns up to 8 chunks, a run allows 6 calls, and each code gets 10 runs/min. | **Inference; untested because I made no model calls:** a signed-in user can pull large parts of the MOM corpus through free-text fields. `docs/deploy.md` §11 admits paraphrase and accumulation, but not trivial obfuscation. The no-redistribution rule (D-001) is the hardest constraint. | Normalise by stripping non-alphanumerics before windowing. Add a character n-gram or difflib similarity test. Lower the window to about 8 words. Add a per-code daily output-word cap. Log suppression events. |
| 5 | P2 | The planner and answer LLM calls have no total deadline, so an abandoned run keeps its slot for minutes. | `graph.py:156` and `:256` call `llm.chat` without `timeout_s`. `llm.py`: `TIMEOUT_S=180`, `MAX_RETRIES=3`, backoff `2**attempt`. The HTTP side returns 504 at 90 s but `active` is only released in `execute()`'s `finally`. | One signed-in user can hold both active slots for several minutes and make the demo return "busy". The cost stays bounded by the budget. | Pass a run-level deadline into `llm.chat`, for example 80 s total. |
| 6 | P2 | Every unique query rewrites and reloads the whole embedding cache. | `dense.py`: `embed()` builds `VectorCache(model)`, which loads `cache.npz` (43.7 MB). Each cache miss calls `put_many`, which re-saves all vectors. `r3` runs up to 6 searches per run. The cache grows without limit. Query-embedding cost is not in the budget ledger. | Latency and memory pressure against the 1280 MB limit, plus disk growth from user queries. User question hashes persist on disk. | Keep the matrix in memory. Do not persist query vectors in production, or use a small LRU. |
| 7 | P2 | The feedback endpoint has no size cap and accepts any run id. | `app.py` feedback: `run_id` is only regex-checked. It is not tied to the session. `_append(...)` for feedback has no `max_bytes`, unlike events (1 MiB). | A signed-in session can write about 10 records/min (about 14,000/day) of up to 1,000 characters, and can attach feedback to other users' runs. | Verify the run id belongs to the session. Add a `max_bytes` cap. |
| 8 | P2 | Retention is manual and incomplete. | `audit-prune` (`log.py:205`) covers `runs-*.jsonl` and the trace JSONs only. It leaves feedback, events and the budget file. No cron or timer exists in `scripts/` or `deploy/`. The CLI is not reachable through the image entrypoint without `--entrypoint`, and `docs/deploy.md` does not show how. | Questions and feedback comments accumulate indefinitely on the server. | Document the exact `docker compose run --rm --entrypoint labourlens app audit-prune --days N` command. Add a systemd timer or cron job. Extend prune to feedback and events. |
| 9 | P2 | Audit records likely carry no git commit in production. | `log.py:_version` shells out to `git rev-parse`. The `python:3.12-slim` image has no git, and the exception is swallowed. `LABOURLENS_BUILD` does carry the sha. | **Inference:** docs claim each record carries the code version, and in production it is probably `None`. | Use `LABOURLENS_BUILD` as a fallback. |
| 10 | P2 | Per-IP limits depend on the real client address, and that is unverified. | `docs/deploy.md` §8 says it is not verified. | If the app sees the Docker gateway address, every user shares one bucket (login 5/min, ask 20/min), a self-inflicted outage. | Check the live Caddy log once. |
| 11 | P2 | Documentation conflicts with the live site. | `docs/progress.md` says live mode is OFF, there is no OpenAI key, and the host is an sslip.io name. The live site is `labourlens.navig.me` and `/api/status` reports `enabled:true`. A grep of the repo finds no mention of `navig.me`. | An assessor reading the docs gets the wrong state, and the live URL appears in no repo document. | Update `progress.md`, README and the demo script. Record whether a provider-side spend cap was verified. |
| 12 | P2 | Supply chain is only partly pinned. | Base images `python:3.12-slim` and `caddy:2-alpine` are pinned by tag, not digest. `pyproject.toml` uses `>=` bounds, though `uv.lock` plus `--frozen` fixes the resolution. `deploy.sh` runs `docker image prune -f`, which removes only dangling images, so old tagged images accumulate. | Rebuilds are not bit-reproducible, and disk fills slowly with each deploy. | Pin digests. Run `docker image prune -af --filter until=…` while keeping the current and previous tags. |
| 13 | P2 | Small privacy and log-hygiene gaps. | The Caddy JSON log keeps `remote_ip` (10 MB × 3). Architecture §6 says raw IPs are not stored, which is true only of the audit log. `redact.secret_values()` name hints (KEY, TOKEN, SECRET, PASSWORD, CREDENTIAL) do not match `LABOURLENS_AUDIT_SALT`. | Documentation overstates the privacy position slightly. The salt is not exposed through any answer path I traced. | Qualify the claim in the docs. Add `SALT` to the hints. |

## 3. Verified OK (read directly, not exercised)

- **CSRF and session:**
  - Cookie flags are right, the signature check uses `compare_digest`, and expiry is enforced.
  - Origin is checked on every mutating route when the header is present; a cross-site browser POST always sends it.
- **Login:** code checks are constant-time and cover all configured codes. Weak secrets disable live mode.
- **Budget:**
  - The ledger is written atomically and survives restart.
  - An unreadable ledger counts as exhausted, and a write failure blocks the run.
  - The active-run cap holds across HTTP timeouts.
  - By my own arithmetic from `specs/prices.yaml` and the token caps, the worst-case run at `gpt-6-luna` prices is about a few cents, so the $0.05 reservation is plausible. This is an estimate, not a measurement.
- **Injection and exfiltration paths:**
  - Tool arguments are enums and patterns. There is no file, shell, network or SQL tool, and no user-supplied path reaches the filesystem.
  - The planner never sees passage text.
  - The web response whitelists trace keys and omits `errors`.
  - No `innerHTML` or inline script exists in the frontend, and the CSP is strict.
  - The Origin and Host handling for static paths relies on Starlette's `StaticFiles`.
- **Secrets:**
  - A grep of the tracked tree finds only fake test keys and `REPLACE-…` placeholders.
  - `.env`, `.env.*` and `data/audit/` are gitignored, and `.env` is not in the file listing of tracked paths.
  - `.dockerignore` is an allow-list and CI checks the built image for PDFs, env files and data.
  - GitHub Actions are pinned to full SHAs, permissions default to `{}`, the SSH host key is pinned, and the registry token is short-lived and removed afterwards.
- **MCP HTTP:** the token logic, loopback refusal, 401 health probe and separate env file are consistent with the docs, and `test_http.py` exists.
- **Deploy script:** tag validation, rollback on failed health, edge health through Caddy and `previous_tag` bookkeeping read correctly.
- **Public JSON:** `web/static/data/report.json` has no `quote`, `excerpt` or `passage_text` keys, and its only long string is the evaluation summary.
- **Committed experiments:** the grep found no `evidence_text` or `"text":` fields in them.

## Limits

- Git history was not searched. The repository-wide secret search is recorded separately in [`docs/process/repository-audit.md`](../process/repository-audit.md).
- The reviewer's search of `.git/index` for `.env` could not tell `.env` from `.env.example`, so it is inconclusive; the later history check found `.env` was never tracked.
- A search by the reviewer displayed the contents of the local, untracked `.env` in its own session output. Nothing was committed. The key should be rotated if that transcript is retained, and the server should use its own restricted key, as `docs/deploy.md` advises.
- Not checked, because they need the provider control panels: the DigitalOcean firewall, the GitHub `production` environment rules and the OpenAI project spend cap.

## 4. Three improvements by value for effort

1. **Fix the data-shipping contract (findings 1, 2).** Update `runtime-data.txt`, add a test that every chunk has a cached vector, put a corpus hash in `/healthz`, and make startup fail fast without calling the API. This is a few lines and avoids the one failure that can break the live demo after the next upload.
2. **Harden the login lockout and run deadline (findings 3, 5).** Make the lock per-IP, let valid codes through, and give `llm.chat` a run-level deadline. Both fixes are small and protect the assessor's path.
3. **Make the rights projection robust (finding 4).** Normalise punctuation before windowing, add a similarity test and a per-code output-word cap. Add one test with obfuscated text, so the claim "reduces verbatim disclosure" has evidence behind it.

## Top 5 findings

1. The runtime-data list omits `cache.npz` and three new passage files, so the next upload plus restart can break startup or trigger paid embeddings (P1).
2. No corpus-version marker in `/healthz` or audit, so v1 and v2 results cannot be tied to what the live site serves (P1).
3. A single IP can keep all logins locked at 5 failed attempts per minute (P1).
4. The 13-word whitespace overlap check is a weak rights boundary against obfuscated reproduction (P1).
5. The docs describe a live-off, sslip.io deployment while the live site is on at `labourlens.navig.me`, and no repo document names that URL (P2).