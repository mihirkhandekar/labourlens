# AI review by claude-agent (security-reviewer), 30 Oct 2026; status of each finding after fixes

The original AI review is preserved **in full and unchanged below**. Its source locations, line numbers and descriptions refer to the pre-fix snapshot, not the current implementation. This status table records the remediation contract and current file references without a commit identifier. It is not a new penetration test, human review, dependency scan or live-provider test.

| # | Original severity / finding | Status after fixes and residual limits | Current implementation / regression-test references |
|---|---|---|---|
| 1 | MEDIUM — uncharged failed runs | **Mitigated:** persist a $0.05 reservation before launch; retain it on failed outcome, exception or timeout (even late success), reconcile successful non-timed-out runs. This estimate is not a proven provider-billing upper bound; retain a provider-side project cap and verify whether it is enforced rather than only an alert. | `src/labourlens/report/app.py`; `tests/web/test_security_fixes.py` |
| 2 | MEDIUM — verbatim report copying | **Mitigated:** replace free-text fields sharing more than 12 consecutive evidence words; cap 12 claims, 3 citations per claim, 40 words per quote and 120 quoted words per answer/card; deduplicate globally. Paraphrase and repeated-question reconstruction remain rights risks, not permission to reproduce reports. | `src/labourlens/report/app.py`; `tests/web/test_security_fixes.py`; `tests/web/test_report_projection.py` |
| 3 | MEDIUM-LOW — redaction corrupts JSON | **Fixed:** recursively redact string values before JSON serialization in responses/audit records, preserve dictionary keys, ignore short secrets, and exclude backslashes in key-pattern matches. Protected agent trace serialization remains unchanged; the backslash stopgap applies there. | `src/labourlens/mcp/redact.py`; `src/labourlens/audit/log.py`; `src/labourlens/report/app.py`; `tests/test_audit_security_fixes.py`; `tests/web/test_security_fixes.py` |
| 4 | MEDIUM-LOW — Unicode log-record forgery | **Fixed:** physical-newline JSONL framing, ASCII-escaped writes, and counted/skipped corrupt records. | `src/labourlens/audit/log.py`; `tests/test_audit_security_fixes.py` |
| 5 | MEDIUM-LOW — unbounded rejection events | **Mitigated:** known-route filtering, bounded per-client sampling, a 1 MiB daily event-file cap and off-event-loop writes. Dropped events mean this is not a complete request ledger; retention still matters across days. | `src/labourlens/report/app.py`; `src/labourlens/report/audit.py`; `src/labourlens/audit/log.py`; `tests/test_audit_security_fixes.py`; `tests/web/test_security_fixes.py` |
| 6 | LOW-MEDIUM — public default audit salt | **Fixed:** HMAC pseudonyms with `LABOURLENS_AUDIT_SALT` or persisted random installation salt (0600); no public fallback. | `src/labourlens/audit/log.py`; `docs/audit-and-logging.md`; `docs/deploy.md`; `deploy/.env.example`; `tests/test_audit_security_fixes.py` |
| 7 | LOW — weak configured credentials | **Fixed:** require a session secret of at least 32 characters and every code of at least 16; globally lock after 50 failed logins per 10 minutes. Length does not ensure entropy; the lock can itself deny legitimate logins under attack. | `src/labourlens/report/app.py`; `tests/web/test_security_fixes.py`; `deploy/.env.example` |
| 8 | LOW — forwarded-header trust | **Mitigated:** explicit trusted-proxy configuration/logging, Caddy replacement of forwarded headers, Secure-cookie regression tests and Caddy HSTS. The operator must validate the real deployment/client address and prevent direct access to the app port. | `src/labourlens/report/serve.py`; `deploy/docker-compose.yml`; `deploy/Caddyfile`; `tests/web/test_deploy_edge.py`; `tests/web/test_security_fixes.py`; `docs/deploy.md` |
| 9 | LOW — session / defence-in-depth gaps | **Mitigated:** same-origin logout revokes one sid, restart revokes all sessions, access-code-bound rate identity survives re-login, login checks Origin, missing-client handling is safe, Caddy supplies HSTS, and web runs save redacted traces. Shared codes are not individual accounts. No app Host allow-list or audit-question anonymization is claimed; these remain accepted defence-in-depth/privacy limits. | `src/labourlens/report/app.py`; `tests/web/test_security_fixes.py`; `tests/web/test_audit.py`; `deploy/Caddyfile` |
| 10 | INFO — dependencies | **Accepted:** retain `uv.lock` and `uv sync --frozen`. No advisory scan was run and no CVE / vulnerability-free claim is made. | `uv.lock`; `pyproject.toml`; `Dockerfile`; `docs/deploy.md` |

## Observed offline verification — 30 Oct 2026

Command: `uv run pytest tests/web tests/test_security.py tests/test_audit_and_notes.py tests/test_audit_security_fixes.py tests/mcp/test_tools.py tests/mcp/test_mcp.py::test_discovery_exposes_only_read_only_tools_and_resources -q`

**Measured result (30 Oct 2026, superseded by later runs):** 164 passed in 139.60s. Includes web, security, audit, MCP tools and one real MCP subprocess discovery smoke. New regressions cover durable failure/timeout reservations, failed reservation blocking launch, verbatim overlap and quotation limits, JSON/Unicode integrity, persistent HMAC salt, bounded admission events, credential lengths/global lockout, logout/re-login limits, missing clients and trusted-proxy Secure cookies. Existing default-runner coverage now requires `save_trace=True`. No paid API calls, advisory scans, commits or deployments were performed by this remediation task.


## Original review (verbatim)

# Security review: live demo backend and MCP surface (AI review by claude-agent, security-review)

I found no critical or high issues. There is no auth bypass, no XSS sink and no SSRF. The real weaknesses are around budget accounting, audit-log integrity and rights.

I read the code but did not run anything. My tool set had no shell, so I did not start the app or probe it with curl. Every claim below comes from reading source, `uv.lock`, the installed `uvicorn` and `mcp` source, `docs/deploy.md` and the artifacts. Findings marked `[INFERENCE]` are traced by reasoning and have not been run.

## Findings, ranked

### 1. MEDIUM: spend is recorded only after a run succeeds, so failed runs are free
- **Where:** `src/labourlens/report/app.py:270-276`. `app.state.spent_usd += cost` runs only after `runner()` returns. `agent/graph.py:292` builds `usage` from `final.get("usage")` after `graph.invoke`, with no try/except around it (`graph.py:285-292`). `prices.chat_cost` is `table()["chat"][model]`, so it raises `KeyError` for any model missing from the price table.
- **Exploit sketch:** a code holder asks questions that make the run raise after paid LLM calls. Examples are an unexpected exception inside `graph.invoke`, a `KeyError` on pricing, or `public_result` or `json.loads` raising after the spend line. Each such run returns 503 and adds $0 to the ledger. Concurrency (2) and the per-IP and per-session limits still apply, but the daily $ cap stops being a cap. Failed LLM attempts inside the agent (`LLMError` paths, `graph.py:151-153, 226`) are also not in `usage`. A process kill mid-run loses that spend too.
- **Fix:** reserve a worst-case cost before launching, in the `finally` block or immediately after the budget check. Reconcile with the real cost on success. If the run raises, keep the reservation. Persist the reservation before starting the run. Also keep the provider-side project budget as the hard stop, as `docs/deploy.md` already advises.

### 2. MEDIUM: model free text is not checked for verbatim MOM passage copying
- **Where:** `answer/validate.py:76-79` enforces the 40-word limit only on `citations[].quote`. `agent/graph.py:262-263` runs `scan_output` on summary, reason, caveats and claim text, but that scan looks only for secrets and the system prompt. `app.py:78-117` returns the whole `answer` dict (summary, claims, caveats) to the user. The cards' `quotes` list has no cap on count or total words (`app.py:82-86, 101-103`).
- **Exploit sketch:** a prompt such as "in your summary reproduce passage P1 verbatim" or "give 30 citations, 40 words each, covering the passage". Cited quotes must be substrings of the evidence, so a handful of questions can rebuild whole report passages. This conflicts with the rights rule in `the project rights rule (D-001)` and `docs/deploy.md`: the evidence pane is meant to show only short cited fragments, and the Q3 2025 report carries a no-reproduction notice. The `[INFERENCE]` part is how far the model complies. The code does not stop it.
- **Fix:** add a verbatim-overlap guard. For example, block or truncate when a free-text field shares a run of more than about 12 consecutive words with any evidence passage. Cap the number of claims and citations, and the total quoted words per answer and per card (for example 120 words per answer). Dedupe quotes in `public_result`.

### 3. MEDIUM-LOW: `redact()` applied to serialised JSON can corrupt the JSON, which crashes audit readers and 503s a response
- **Where:** `mcp/redact.py:12` uses `[^&\s"']{6,}`, which allows a backslash. `audit/log.py:64` and `app.py:282` run `redact` on the JSON text.
- **Exploit sketch** `[INFERENCE]`: a question or model output containing `token=abcdefgh"` serialises to `token=abcdefgh\"`. The regex consumes `abcdefgh\` and leaves a bare `"`, so the string ends early and the JSON is invalid.
  - Audit path: `_append` writes a broken line. `read_runs` and `read_feedback` (`log.py:113-120`) then raise `JSONDecodeError`, so `audit report/show` is unusable until the line is removed. The question is stored for every run, so an authenticated user controls this.
  - Response path: `json.loads(...)` at `app.py:282` raises, and the user gets 503 after the spend was already counted. This one is self-inflicted.
- **Fix:** redact the string values before serialising, with a recursive walk over the dict. Do not redact the encoded JSON. Exclude backslash from the pattern class as a stopgap.

### 4. MEDIUM-LOW: log-record forgery through U+2028, U+2029 and U+0085 in the audit JSONL
- **Where:** `log.py:64` uses `ensure_ascii=False`, which escapes only control characters below 0x20. The readers at `log.py:114` and `:120` use `str.splitlines()`, which also splits on U+2028, U+2029 and U+0085, among others. `/api/ask` accepts any characters in `question` (`app.py:~257`). The graph's `sanitize_text` strips only `Cf` and `Cc` categories, so U+2028 and U+2029 (category `Zl` and `Zp`) survive. The feedback comment path filters them via `isprintable`, so it is not affected.
- **Exploit sketch** `[INFERENCE]`: a question like `x\u2028{"schema":1,...,"outcome":"answered",...}` is stored as one physical line but read back as two records. This forges run records that skew the `audit report` statistics, or breaks the reader (see 3).
- **Fix:** read with `for line in f` or `split("\n")`, not `splitlines()`. Alternatively, write with `ensure_ascii=True`.

### 5. MEDIUM-LOW: unauthenticated requests can grow the audit log without bound
- **Where:** `app.py:210-218` appends one line to `events-<date>.jsonl` for every 4xx or 5xx response on any `/api/*` path. That includes 404 for a random path and 401 on `/api/ask`. None of these are rate limited, because `hit()` is only called by login, ask and feedback. The write is synchronous: file open under a `threading.Lock` inside the async middleware, which blocks the event loop.
- **Exploit sketch:** `for i in ...; curl /api/x$i` grows the log by about 250 bytes per request, and each write stalls the loop. A disk-fill or latency DoS needs sustained traffic, and the proxy limits may mitigate it.
- **Fix:** rate-limit or sample rejection events per client hash. Log only for known routes. Rotate or size-cap the file. Run the write in a thread or a queue.

### 6. LOW-MEDIUM: the audit pseudonym uses a public default salt
- **Where:** `audit/log.py:41` falls back to `"labourlens-dev-salt"`. `LABOURLENS_AUDIT_SALT` is documented in `docs/audit-and-logging.md:14` but is absent from the `docs/deploy.md` env table (grep found no match). A SHA-256 over `salt|ip`, truncated to 16 hex characters, is a trivial rainbow table over the IPv4 space.
- **Fix:** add the variable to the deploy env table and refuse live mode, or generate a random per-install salt, when it is unset. Use HMAC.

### 7. LOW: weak secrets are not enforced in code
- **Where:** `Settings.enabled` (`app.py:~57`) checks only that the codes and the secret are non-empty. The 32-byte secret rule is only in docs, and the access codes have no minimum length. Cookie forgery or login brute force is feasible only if an operator picks weak values. The login limit is per client address, so IPv6 /64 rotation sidesteps it.
- **Fix:** require a session secret of at least 32 characters and codes of at least 16 characters, else `enabled=False`. Add a global login-failure counter.

### 8. LOW: the proxy-header trust model fails open if the proxy does not overwrite forwarded headers
- **Where:** `report/serve.py:21-22` uses `proxy_headers=True, forwarded_allow_ips="127.0.0.1"`. I verified the installed uvicorn takes the rightmost untrusted `X-Forwarded-For` entry (`uvicorn/middleware/proxy_headers.py:180-183`), which is correct for Caddy and nginx. If the proxy forwards a client-supplied XFF unchanged, the client's value is used as the rate-limit key and the audit hash.
- **Related:** the cookie `Secure` flag depends on `request.url.scheme` (`app.py:245`). Without `X-Forwarded-Proto` from a trusted peer, the cookie is issued without `Secure`.
- **Fix:** keep the deploy-doc caveats. Add a startup self-check or a test that asserts the `Secure` flag when `X-Forwarded-Proto: https` arrives from 127.0.0.1.

### 9. LOW: session handling and defence-in-depth gaps
- The cookie is stateless. There is no logout and no server-side revocation, so a stolen cookie is valid for 8 hours (rotate the secret to revoke, as documented). A new `sid` per login also bypasses the per-session limit (`app.py:~250`). The per-IP limit still binds.
- `/api/login` has no Origin check (`app.py:233`). `SameSite=Strict` and the need for a valid code make this negligible.
- The login limiter runs `request.client.host` with no None guard (`app.py:233`), so a missing client gives a 500.
- No HSTS and no Host allow-list in the app. DNS rebinding cannot reuse the cookie because it is host-scoped.
- The audit log stores the user's question (clipped to 1200 characters) and the feedback comment. The deploy doc covers the privacy handling.
- `redact` with a short access code replaces that substring everywhere in the JSON response (`app.py:282`). A code like `demo` would corrupt keys and values.

### 10. INFO: dependencies
- `uv.lock` pins `fastapi` 0.162.0, `starlette` 1.10.0, `uvicorn` 0.54.0, `mcp` 2.3.0, `httpx` 0.28.1, `h11` 0.16.0 and `pymupdf` 1.28.2. `pyproject.toml` has only lower bounds, so `uv sync --frozen` (deploy step 3) is what protects reproducibility.
- I did not run an advisory scan (`pip-audit` or `uv audit`). I make no CVE statement for these versions.
- `pymupdf` parses PDFs only in the offline pipeline, not in the web path. `cryptography<49` has no visible use in the scoped files.

## Controls I verified as working
- **XSS:** `web/static/*.js` has no `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `eval` or `srcdoc` sink. The only grep hits were English words such as "marked". Everything uses `textContent` or `append`.
  - Links are built from `new URL` and limited to http or https, with `rel="noopener noreferrer"` (`app.js:66-74`). The server further restricts evidence URLs to https (`_safe_url`, `app.py:~62`).
  - Error text from the server is rendered as text.
  - CSP is `default-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'`. There are no inline scripts in `index.html` and no inline `style=` writes in `app.js`.
  - The other headers are present: nosniff, `Referrer-Policy: no-referrer`, X-Frame-Options and `Cache-Control: no-store` on `/api`.
- **Session cookie:** HMAC-SHA256 over `sid:expiry`, compared with `compare_digest`. Bad or non-ASCII signatures are caught and return no session. HttpOnly, `SameSite=Strict`, `Secure` when the app sees https, 8-hour expiry, random 192-bit `sid`.
- **Login:** each candidate and each configured code are SHA-256 hashed before a constant-time compare, and every code is checked. Login is limited to 5 per minute per client.
- **CSRF:** `SameSite=Strict` plus an Origin match on `/api/ask` and `/api/feedback`. A cross-site Origin gets 403, including the string `null`.
- **Body size:** the middleware streams the body and cuts it off at 8192 bytes (413), before any parsing.
- **Concurrency race:** the busy check and the increment at `app.py:261-263` have no `await` between them, so the cap of 2 holds on the single event loop. `finally` decrements even when the HTTP request times out, so a detached run keeps its slot.
- **Budget and fail-closed:** the ledger persists across restart and is written via tmp file plus rename. An unreadable ledger counts as fully spent. A non-finite or negative cost is charged as the full budget. Day rollover resets the in-memory total. Overshoot is limited to the two in-flight runs, apart from finding 1.
- **Evidence projection:** `evidence_text` and `passages_by_id` are never returned. The card metadata is a whitelist of fields. Per-card quotes must be at most 40 words and an actual substring of the fetched evidence (`app.py:101-103`). `trace.detail` is whitelisted by key. The residual leak is finding 2.
- **Redaction:** responses, feedback comments and audit lines go through `redact()`, which covers environment values (KEY/TOKEN/SECRET/PASSWORD/CREDENTIAL, length 8 or more), `sk-` keys, bearer tokens, `key=` pairs and emails. The access codes and session secret are passed explicitly. The uvicorn loggers carry `RedactingFilter` and access logging is off (`serve.py`). Audit events store no question, code or raw IP, only a salted hash, route, status and reason. I found no `labourlens_session`, `sk-` key, bearer token or `SESSION_SECRET=` value in `experiments/`, `artifacts/tests/`, `docs/`, `data/audit/` or `web/static/data/report.json`. The report contains no `/Users/` paths and no long text field (300 or more characters).
- **Static serving and traversal:** only `web/static` is mounted, and the Starlette `StaticFiles` default is used. The directory holds only JS, CSS, the favicon and `data/report.json`. API docs and OpenAPI are off. The report builder reads only git-tracked files from the HEAD commit and rejects `..` (`report/build.py:77-81`). No path built from request data reaches the filesystem. The feedback `run_id` is constrained to `[0-9a-f]{12}`, tags to an enum, the comment to 1000 characters with control characters and tags stripped.
- **MCP HTTP server:**
  - It refuses to start without a token of at least 24 characters and refuses a non-loopback bind unless `--allow-nonloopback` is passed.
  - Bearer middleware is first in the chain, with a constant-time compare and a bare 401.
  - DNS-rebinding protection is on, with an allowed Host list and `allowed_origins=[]`.
  - The request body is capped at 64 KB, WebSocket connections are closed, and `access_log` is off.
- **MCP client:**
  - The server allow-list is fixed. The token is read from the environment and sent only to a URL whose host passes `is_loopback`, with credentials in the URL rejected (`client.py:138-143`).
  - Redirects are not followed across origins: I read the installed SDK (`mcp/shared/_httpx_utils.py:121-134`, `follow_redirects=False` and same-origin only). The token cannot be redirected to another host.
  - A stdio subprocess gets the SDK's safe default environment, so no `OPENAI_API_KEY`.
  - After connecting, the client checks the server name, version and tool allow-list, validates arguments against the advertised schema, caps response size and time, and sanitises and quarantines instruction-like strings (`client.py:96-136`).
- **MCP server surface:** the tools and resources are read-only, with annotations set. Arguments are pydantic-constrained (patterns, `Literal`, `max_length`). The `labourlens://source/{source_id}` resource looks up the catalogue by key and does no file access, so there is no path traversal.
- **Prompt-injection consequences:** the agent has no write, network or shell tool, and its limits are 2 rounds, 6 calls and 3 calls per round, plus a 10 s tool timeout and a 40-step recursion limit. Output is scanned for secret values, secret shapes and system-prompt text (`guards.scan_output`). The reachable harms are therefore wasted budget (finding 1) and passage disclosure (finding 2), not host compromise or key exposure. I did not re-run the threat-suite results.

## Coverage
Read fully: `report/app.py`, `report/audit.py`, `report/serve.py`, `audit/log.py` (lines 19-123), `mcp/redact.py`, `mcp/http_server.py`, `mcp/client.py` (lines 19-203), `security/guards.py`, `web/index.html`, and the `mcp/server.py` tool and resource declarations. I did a pattern sweep of all of `web/static` for HTML sinks, inline styles and fetch paths. I also looked at the `agent/graph.py` usage and error paths, `answer/validate.py`, `report/build.py:59-133, 455-463`, `docs/deploy.md`, `pyproject.toml` and `uv.lock`.

Not reviewed in depth: `mcp/analysis.py`, `mcp/models.py`, `security/threat_suite.py`, `report/build.py` beyond what is listed above, and `presentation-data.js`, `evaluation.js` and `answer-audit.js` beyond the sink grep.