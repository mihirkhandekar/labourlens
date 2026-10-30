# Deploying the LabourLens report

**PROPOSAL / operator runbook. No deployment has been performed.** The commands below have not been run for a deployment. The report is public. Live questions and feedback require an access-code session. The service is a single-process demonstration, not a production authentication or billing system.

## 1. Prepare the release

Use Python 3.12, `uv`, the checked-in lockfile and a reviewed revision. From the repository root:

```sh
uv sync --frozen
uv run labourlens build-report
uv run labourlens serve --host 127.0.0.1 --port 8000
```

`build-report` assembles saved local evidence into `web/static/data/report.json`. It does not download sources, train models, compute embeddings or run evaluations. Do not add `fetch`, `build`, `dense-exp`, `agent-exp`, `eval` or any paid API run to a deployment hook. Do not regenerate missing research artifacts during release preparation.

Publish only the reviewed, rights-cleared report and web assets. Keep these out of `web/`, public buckets and public container directories: `.env`, access codes, session keys, raw MOM PDFs, extensive extracted report text, private review sheets and raw model runs. Keep source links and attribution visible. The static report must work with live mode disabled.

For live mode, provision these local runtime assets separately: corpus, structured observations, retrieval caches, prompts, source specifications and pricing configuration. They are ignored or private, so a public checkout does not contain them. Keep restricted source material private and confirm deployment rights. With live mode enabled, startup loads the shared retrieval resources. Missing resources raise an operational error and do not produce an empty evidence set. Inspect the asset bundle before enabling live mode. Do not generate missing embeddings during deployment.

## 2. Runtime configuration and secrets

Set these on the server only. `serve` loads a repository-root `.env` without overriding variables already set in the environment. Prefer a protected service environment file or platform runtime secrets. Never send the OpenAI key to the browser, put it in report JSON, log it or pass it as a build argument.

| Variable | Meaning / operator action |
|---|---|
| `LABOURLENS_DEMO_ENABLED` | Set `false` for report-only mode or emergency shutdown. Set `true` only after live prerequisites and HTTPS are checked. Defaults to `true`. Live mode stays disabled when access codes or the session secret are missing. |
| `LABOURLENS_ACCESS_CODES` | Comma-separated nonempty reviewer codes. Generate unpredictable values and distribute them privately. |
| `LABOURLENS_SESSION_SECRET` | Separately generated signing secret of at least 32 random bytes. Required for live mode. Rotation invalidates existing sessions. |
| `LABOURLENS_DAILY_BUDGET_USD` | Daily estimated-cost admission ceiling. Default `2.0`. Use a finite nonnegative decimal. Zero blocks new live questions. The provider does not enforce this limit. |
| `OPENAI_API_KEY` | Restricted server-side OpenAI project key, used for live research only. Omit in report-only mode. |

Generate codes and the session secret independently, in a password manager or a private terminal with `openssl rand -hex 32`. Do not paste values into documentation, shared shell history, screenshots or issue trackers. Set an OpenAI project-level budget in addition to the application limits. Configuration changes take effect after a service restart or redeploy.

**VERIFIED FACT (implementation):** sessions use a signed `labourlens_session` cookie with HttpOnly, SameSite=Strict, an eight-hour lifetime, and Secure when the application sees HTTPS. The cookie does not contain the access code. Changing codes does not invalidate issued cookies. Rotate the signing secret to revoke sessions. `false` blocks new live API requests. It does not stop provider work already running.

Default limits:
- Login: 5 attempts per IP per 60 seconds.
- Questions: 10 per session and 20 per IP in that interval.
- Active runs: at most 2.
- HTTP wait: 90 seconds.
- Request body: 8 KiB.
- Questions and feedback comments: 1,000 characters.

These limits are `Settings` fields. `Settings.from_env` reads only the variables in the table above. Do not invent variable names for the other fields.

The budget ledger is `data/feedback/budget.json`. Sanitized feedback appends to `data/feedback/feedback.jsonl`. Make that directory writable only by the service account and keep it outside the public document root. Back it up privately if feedback must be kept. Tell reviewers not to enter personal or confidential information, because HTML and control-character sanitizing does not anonymize text. Set a retention period and delete feedback under it.

## 3. Recommended live hosting: Droplet with a local HTTPS proxy

**PROPOSAL:** run one application process on one host under a dedicated unprivileged account. Caddy or Nginx terminates HTTPS and forwards to `127.0.0.1:8000`. This matches the local persistence and the proxy trust boundary. Use a supported Linux release with current security updates, SSH keys, and a firewall that opens only SSH, HTTP and HTTPS. Do not expose port 8000.

1. Copy the reviewed application and permitted private runtime assets to `/srv/labourlens`. Install `uv` and Python 3.12. As the service user, run `uv sync --frozen` and `uv run labourlens build-report`. Do not run research pipeline commands.
2. Store the runtime variables in `/etc/labourlens.env`, owned by root and readable by the service account. Set `LABOURLENS_DEMO_ENABLED=false` initially.
3. Run one service with working directory `/srv/labourlens`, environment file `/etc/labourlens.env` and start command `uv run labourlens serve --host 127.0.0.1 --port 8000`. Restart it automatically on failure. Do not add workers. In a systemd `ExecStart`, use the absolute path to `uv`.
4. Give the proxy a valid DNS name and a trusted TLS certificate. Redirect HTTP to HTTPS. Forward the original Host and the HTTPS scheme, and overwrite client-supplied forwarding headers. Match proxy request limits and timeouts to the application. Example Caddy configuration:

   ```caddyfile
   research.example.org {
       reverse_proxy 127.0.0.1:8000
   }
   ```

   Replace the example domain with your domain. Check the certificate and forwarded-header behavior before enabling live mode.
5. The server trusts forwarding headers only from `127.0.0.1`. Use that address (not another network proxy or IPv6 loopback) unless you configure and review a different trust list. Never trust arbitrary Internet forwarding headers to fix a scheme or cookie problem.
6. Complete the checks in section 6, set up provider-side cost controls, then enable live mode and restart the service.

## 4. DigitalOcean App Platform alternative

**VERIFIED FACT (official documentation):** App Platform deploys from a Git repository or image and assigns a starter domain ([domain configuration](https://docs.digitalocean.com/products/app-platform/how-to/manage-domains/)). [Encrypted runtime variables](https://docs.digitalocean.com/products/app-platform/how-to/use-environment-variables/) are readable by application code and trusted console users. Encryption does not protect against malicious application code. Restrict deployment and console access.

Use one web service, one instance, no autoscaling, and a Python 3.12 / `uv` environment with the pinned dependencies. For live mode, supply the reviewed runtime assets privately. Configure:

```sh
# Build command, with no OpenAI key present:
uv sync --frozen && uv run labourlens build-report

# Run command, matching the service's configured HTTP port:
uv run labourlens serve --host 0.0.0.0 --port 8080
```

Set the HTTP port to 8080 and the health check to `/api/status`. A successful status response shows that HTTP is available. It does not show authentication, corpus readiness or answer correctness. Configure the public HTTPS route or custom domain. Start with `LABOURLENS_DEMO_ENABLED=false`. Store access codes, the session secret and the OpenAI key as encrypted component-level RUN_TIME variables, not build-time or app-wide variables.

**Live-mode prerequisite:** `serve` trusts only a loopback proxy, and App Platform's ingress is not assumed to be one. Before enabling live mode, configure a documented, restricted ingress or proxy trust so the application sees the external HTTPS scheme and the correct same-origin host. Otherwise Secure cookies and origin checks may be wrong. Do not use `--forwarded-allow-ips '*'` on a backend that untrusted clients can reach. If the topology cannot be verified and configured safely, keep this deployment report-only and use the Droplet for live questions.

**Persistence limitation:** [App Platform local filesystems are ephemeral](https://docs.digitalocean.com/products/app-platform/how-to/store-data/). Deployments and replacements discard the local feedback and budget ledgers, and instances do not share local files. This version therefore cannot run unattended with a persistent budget on App Platform. Before replacement, export permitted feedback privately and reconcile spending independently. Managed persistent accounting does not exist and would be a separate change. The Droplet's private local storage is the simpler option for a live demo.

## 5. Operating limits and emergency controls

- **One process or instance only.** Rate counters and active-run admission are process-local. The budget file is not a distributed ledger and has no cross-process lock.
- Completed-run usage is estimated and persisted locally. Concurrent in-flight requests can exceed the admission ceiling by their final usage (at most 2 active runs with defaults). A timed-out HTTP response does not mean the provider call stopped. The slot stays occupied until the run finishes. Provider billing may differ from the estimates, so reconcile it separately.
- The day rolls over on the server's local calendar date. Record the server timezone. Do not reset or delete the ledger to get past a budget rejection. An unreadable ledger counts as exhausted.
- Emergency stop: set `LABOURLENS_DEMO_ENABLED=false` and restart or redeploy. Revoke the provider key to stop provider work immediately. After a suspected disclosure, rotate the access codes and the session secret. Keep only the redacted diagnostics you need.
- The entry point disables Uvicorn access logging. Configure proxy and platform logs not to record request bodies, cookies, Authorization headers or query text. Keep private research data out of public telemetry.
- The application sets a same-origin CSP, frame denial, nosniff, referrer and permissions policies. API responses are `no-store`. Keep these headers intact at the proxy. The UI renders all model strings as text, never as HTML.

## 6. Owner verification before sharing a link

**Not executed.** The integration owner runs `uv run pytest tests/web` with fake injected runners, then checks the HTTPS site in a browser. A paid live query is a manual operator action, not a deployment hook.

- With live mode off and no OpenAI key, the report, figures, navigation and provenance links load.
- `/api/status` reports the disabled, enabled-signed-out and signed-in states correctly.
- An invalid code fails. Repeated attempts are rate-limited. A valid code sets HttpOnly, Secure and SameSite cookies over the public HTTPS URL. A tampered session cannot ask a question.
- Unauthenticated and cross-origin questions fail without invoking research. Oversized or invalid requests fail. API responses carry security headers and `no-store`.
- With an injected offline runner, one successful response contains answer, evidence, chart, trace and usage. Budget exhaustion and concurrency rejection prevent extra research calls. A timeout does not free an active worker early.
- Feedback writes one sanitized JSONL record with no credentials. Check private persistence, backup and retention across a service restart.
- The kill switch blocks new live work while the report stays available. Rotating the session secret and reopening the browser behave as intended.

Record the commands, observations and deployment URL in the owner handoff after they are run. This runbook records no deployed URL or test result.

## 7. Optional: MCP statistics server as a loopback sidecar

**What this is.** The read-only MCP statistics server can also run over streamable HTTP on the loopback interface, protected by a bearer token. It is for a second local process (for example an MCP client on the same machine or in the same container) and is **not** a public endpoint. Not built: OAuth, per-client authorisation, TLS termination. The web app does not need it; the agent keeps calling statistics directly unless an operator wires in the MCP client. stdio stays the tested default (`uv run python -m labourlens.mcp.server`).

**Rules.** Same container or instance as its client, bound to `127.0.0.1`, token supplied by the environment, never published through the proxy or a platform route, never exposed on `0.0.0.0`. The server refuses to start without a token of at least 24 characters and refuses a non-loopback `--host` unless `--allow-nonloopback` is given (that flag prints a warning: it then needs TLS and a real authentication layer, which this server does not provide). The server only reads the observations table, the committed manifests, the committed snapshot CSVs and the dataset adapter specs; it holds no API key and serves no MOM report text.

Generate a token once and keep it out of the repository and out of shell history:

```sh
# on the host, readable by the service user only
umask 077 && python3 -c "import secrets; print('LABOURLENS_MCP_TOKEN=' + secrets.token_urlsafe(32))" > /etc/labourlens/mcp.env
```

Droplet or any systemd host, a second unit next to the web service (`/etc/systemd/system/labourlens-mcp.service`):

```ini
[Unit]
Description=LabourLens MCP statistics server (loopback only)
After=network.target

[Service]
User=labourlens
WorkingDirectory=/opt/labourlens
EnvironmentFile=/etc/labourlens/mcp.env
ExecStart=/usr/local/bin/uv run python -m labourlens.mcp.server --transport http --host 127.0.0.1 --port 8765
Restart=on-failure
RestartSec=3
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
ReadOnlyPaths=/opt/labourlens

[Install]
WantedBy=multi-user.target
```

Container sidecar (compose-style; no `ports:` entry, so nothing is published):

```yaml
services:
  labourlens-mcp:
    build: .
    command: ["uv", "run", "python", "-m", "labourlens.mcp.server", "--transport", "http", "--host", "127.0.0.1", "--port", "8765"]
    environment:
      LABOURLENS_MCP_TOKEN: ${LABOURLENS_MCP_TOKEN:?set a random token of at least 24 characters}
    network_mode: "service:web"   # share the web container's loopback; do not publish 8765
    read_only: true
    restart: unless-stopped
    healthcheck:
      # 401 means the server is up and enforcing the token. Any other status or a refused connection fails the check.
      test: ["CMD-SHELL", "test \"$(curl -s -o /dev/null -w '%{http_code}' -X POST http://127.0.0.1:8765/mcp)\" = 401"]
      interval: 30s
      timeout: 5s
      retries: 3
```

**Health probe.** There is no unauthenticated health route on purpose. An unauthenticated request to `/mcp` must return 401 with an empty body; that proves the process is up and the token check is on.

**Client.** Set `LABOURLENS_MCP_TOKEN` in the client's environment and use the allow-listed `labourlens-stats-http` entry (`http://127.0.0.1:8765/mcp`). The client refuses non-loopback URLs and sends the token only there. Rotate by changing the environment file and restarting both units.

**Owner verification (not executed here beyond `tests/mcp/test_http.py` and `uv run labourlens mcp-demo`).** On the host: `curl -i -X POST http://127.0.0.1:8765/mcp` returns 401; the same request from another machine cannot connect; `ss -ltn` shows port 8765 bound to 127.0.0.1 only; `journalctl -u labourlens-mcp` contains no token.
