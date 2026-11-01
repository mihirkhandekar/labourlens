# Deploying LabourLens on one DigitalOcean Droplet

**Status: operator runbook for a Droplet that exists.** The site is live at <https://labourlens.navig.me> on one Droplet (`labourlens`, `sgp1`), deployed by `.github/workflows/deploy.yml`. Live research is switched on (`/api/status` reported `enabled: true` when the end-to-end review read it on 31 Oct 2026). The earlier sslip.io hostname is retired. **Verified on the Droplet:** bootstrap, workflow run, GHCR pull, certificate, `/healthz`, HSTS and CSP headers (`docs/progress.md`, "Droplet deployed"). **Not verified:** a provider-side OpenAI spend cap (only the application's own estimated budget is in place), restart rollback, the backup procedure, snapshot cost and memory under load. Sections below that say "verified locally" refer to the author's Mac, not the Droplet.

**DECISION (owner, 30 Oct 2026):** host on one DigitalOcean Droplet (Ubuntu LTS, Singapore region `sgp1`) with Docker Compose and Caddy, deployed by GitHub Actions. Not approved: App Platform, Kubernetes, managed Postgres, public MCP exposure, OAuth.

**Why one Droplet.** The app keeps state in one process: the daily budget ledger and the audit and feedback logs are files, and rate limits are in memory. The MOM report passages are not in Git (they are gitignored for rights reasons, decision D-001), so the corpus has to live on the server's persistent disk and never in the image or the repository.

**Prices (VERIFIED, DigitalOcean pricing page, read 30 Oct 2026):** Droplet with 1 GiB memory $6 per month; with 2 GiB memory $12 per month. This runbook targets the 2 GiB size. Snapshot and bandwidth costs were not verified.

## 1. What runs where

```
Internet --80/443--> Caddy (HTTPS, headers, body limit, access log)
                       |  private Docker network 172.30.0.0/24
                       v
                     app container (uvicorn, one worker, port 8000, not published)
                       |  bind mount /srv/labourlens/data -> /app/data
                     [mcp sidecar, optional, shares the app's loopback, not published]
```

| Path on the Droplet | Contents |
|---|---|
| `/srv/labourlens/.env` | Runtime secrets and settings (mode 600). Read by compose, only the app container receives it. |
| `/srv/labourlens/mcp.env` | Optional. `LABOURLENS_MCP_TOKEN` for the MCP sidecar only. |
| `/srv/labourlens/data/` | The minimal runtime data set (section 6). Writable by the app (audit log, budget ledger, query-embedding cache). |
| `/srv/labourlens/deploy/` | `docker-compose.yml`, `Caddyfile`, `deploy.sh`, copied by the deploy job. |
| `/srv/labourlens/state/` | `current_tag` and `previous_tag`, written by `deploy.sh`. |
| `/srv/labourlens/backups/` | Target for the data backup in section 10. |

The image contains code, `specs/`, `prompts/`, `web/` and the locked Python dependencies. It never contains `data/`, PDFs, env files, `study/` or `private/`. `.dockerignore` is an allow-list, and `scripts/check-build-context.sh` proves the result (CI runs it and also inspects the built image).

## 2. Create the Droplet

1. In the DigitalOcean control panel create a Droplet: Ubuntu LTS (24.04), region Singapore `sgp1`, Basic plan with 2 GiB memory ($12 per month). Choose SSH key authentication and add your public key. Do not enable password login. IPv6 is optional; leave it off unless you need it (see section 11).
2. Note the public IPv4 address.
3. Create a **DigitalOcean Cloud Firewall** and attach it to the Droplet: inbound TCP 22 (restrict the source to your own address if it is stable), TCP 80 and TCP 443 from anywhere; all outbound allowed. This is a second layer. The on-host firewall (ufw) does not filter ports that Docker publishes, because Docker writes its own iptables rules; the cloud firewall does.
4. Create a DNS **A record** for your domain pointing at the Droplet's IPv4 address, and wait for it to resolve (`dig +short your.domain`) **before the first deploy**. Caddy requests the certificate on first start and needs ports 80 and 443 reachable and the name resolving to this machine.

## 3. One-time bootstrap

From your machine:

```sh
scp scripts/droplet-bootstrap.sh root@<droplet-ip>:/root/
ssh root@<droplet-ip> 'bash /root/droplet-bootstrap.sh'
```

The script is idempotent. It creates the `deploy` user (uid 10001, the same uid the container runs as, so the app can write the bind-mounted data directory), copies root's authorized key to it, creates `/srv/labourlens`, installs Docker Engine and the compose plugin from Docker's apt repository, enables unattended security upgrades, configures ufw for ports 22, 80 and 443 only, installs fail2ban for sshd, switches ssh to key-only login (`PermitRootLogin prohibit-password`), and adds a 1 GiB swap file. Before closing the root session, open a second terminal and confirm `ssh deploy@<droplet-ip>` works.

The `deploy` user is in the `docker` group, which is root-equivalent on the host. Treat its ssh key as a root credential.

## 4. Server configuration (`/srv/labourlens/.env`)

Create it as the deploy user and restrict it. `deploy/.env.example` holds the same template (and `deploy/mcp.env.example` the MCP one):

```sh
ssh deploy@<droplet-ip>
umask 077
cat > /srv/labourlens/.env <<'EOF'
DOMAIN=labourlens.example.org
OPENAI_API_KEY=sk-REPLACE-WITH-A-RESTRICTED-PROJECT-KEY
LABOURLENS_ACCESS_CODES=REPLACE-WITH-RANDOM-CODE-1,REPLACE-WITH-RANDOM-CODE-2
LABOURLENS_SESSION_SECRET=REPLACE-64-HEX-CHARACTERS
LABOURLENS_AUDIT_SALT=REPLACE-64-HEX-CHARACTERS
LABOURLENS_DAILY_BUDGET_USD=2.0
LABOURLENS_DEMO_ENABLED=false
EOF
```

Replace every `REPLACE-...` value. Generate the random ones privately, each independently:

```sh
openssl rand -hex 32   # run once per value: session secret, audit salt, each access code
```

Do not paste real values into documentation, shell history shared with others, screenshots or issue trackers. Compose reads the file verbatim, so do not wrap values in quotes.

| Variable | Meaning |
|---|---|
| `DOMAIN` | Public host name. Used by Caddy for the certificate and by `deploy.sh` for its edge health check. |
| `OPENAI_API_KEY` | Restricted server-side OpenAI project key for live research and query embeddings. Omit while live mode is off. |
| `LABOURLENS_ACCESS_CODES` | Comma-separated reviewer codes; **every code must be at least 16 characters**, otherwise live mode is disabled. Generate independently at random and distribute privately. |
| `LABOURLENS_SESSION_SECRET` | Signing secret for session cookies; code enforces at least **32 characters**, and operators should generate 32 random bytes or more (for example 64 hex characters). Rotating it revokes all sessions. |
| `LABOURLENS_AUDIT_SALT` | Secret HMAC key for audit pseudonyms. If unset, a random per-installation key is persisted locally with mode `0600`, not a public default. Keep it stable and protect its backup: changing it breaks pseudonym joins. |
| `LABOURLENS_DAILY_BUDGET_USD` | Daily estimated-cost admission ceiling, default `2.0`. Zero blocks new live questions. A $0.05 conservative per-run reservation is persisted before launch; it is not a provider-enforced billing cap. |
| `LABOURLENS_DEMO_ENABLED` | `false` for report-only mode and the kill switch. Defaults to `true` when unset. Live mode also stays off if any code is shorter than 16 characters or the session secret is shorter than 32 characters. |

`LABOURLENS_FORWARDED_ALLOW_IPS` is set by `docker-compose.yml`, not by you (section 8). Set an OpenAI project-level budget in addition to the application limit. Start with `LABOURLENS_DEMO_ENABLED=false`, verify the site, then enable live mode.

Existing behaviour that matters to operators: sessions are signed `labourlens_session` cookies (HttpOnly, SameSite=Strict, eight hours, Secure when the app sees HTTPS) and require an active in-memory session. Same-origin `POST /api/logout` revokes that session and clears the cookie; restarting the app revokes all sessions. Login also checks Origin. Default limits: login 5 attempts per IP per 60 seconds **and 50 failed logins globally per 10 minutes**; questions 10 per access-code-bound identity and 20 per IP per 60 seconds (logging in again does not reset the code's question allowance); at most 2 active runs; 90-second HTTP wait; 8 KiB request body; questions and feedback comments up to 1,000 characters. Audit session hashes still identify distinct sessions. These are `Settings` fields; `Settings.from_env` reads only the variables above.

## 5. GitHub secrets and repository settings

In the private repository `mihirkhandekar/labourlens`, branch `master`, add Actions secrets (repository-level, or on the `production` environment that the deploy job uses; an environment can also require a manual approval):

| Secret | Value |
|---|---|
| `DROPLET_HOST` | The Droplet's IPv4 address or host name. |
| `DROPLET_USER` | `deploy` |
| `DROPLET_SSH_KEY` | Private key of a dedicated deploy key pair (generate one just for this: `ssh-keygen -t ed25519 -f labourlens-deploy -N ''`; put the `.pub` in `/home/deploy/.ssh/authorized_keys`). |
| `DROPLET_KNOWN_HOSTS` | The Droplet's host key line, obtained on a trusted path: `ssh-keyscan -t ed25519 <droplet-ip>` run from your machine, then compare its fingerprint with `ssh-keygen -lf` of `/etc/ssh/ssh_host_ed25519_key.pub` seen over the DigitalOcean console. The job uses `StrictHostKeyChecking yes` with this file, so there is no blind trust of the host. |

The workflow (`.github/workflows/deploy.yml`) has three jobs.

1. **test** installs the locked dependencies with `uv sync --frozen` and runs the test suite in a checkout that has no gitignored corpus. One test is deselected because it re-hashes raw files that exist only on the author's machine (`tests/data/test_provenance_and_packaging.py::test_every_ok_entry_has_matching_file_hash`). It first fails if git tracks any corpus path, PDF or env file.
2. **build-push** checks the build context, builds the image, fails if `/app/data` is not empty or the image contains a PDF (outside the Python dependency tree) or an env file, then pushes `ghcr.io/mihirkhandekar/labourlens:<commit sha>` and `:latest`.
3. **deploy** copies `deploy/` to the Droplet, logs the Droplet into GHCR with the job's short-lived `GITHUB_TOKEN` (logged out again afterwards), and runs `deploy.sh up <sha>`, which pulls the image, starts it, waits for container health (up to 240 seconds) and for `https://DOMAIN/healthz` through Caddy, and returns to the previous tag automatically if either fails.

A concurrency group serialises runs; a queued run waits rather than cancelling one in progress. Workflow permissions are empty by default, and each job requests only what it needs (`packages: write` only to push, `packages: read` only to deploy). The third-party actions are pinned to full commit SHAs, each the commit of the tag in the adjacent comment, checked with `git ls-remote` on 30 Oct 2026; re-verify them when you bump a version. The base images (`python:3.12-slim`, `caddy:2-alpine`, the `uv` image) are pinned by tag, not digest, because no digest was verified. Pull access for the package is assumed to follow repository access for a package published by the same repository's workflow; this was not verified, and if the pull is denied, grant the repository access in the package settings.

## 6. Runtime data

The live app reads these files at startup (the list is `deploy/runtime-data.txt`, 2 structured files, 46 passage files and 2 embedding files, about 39 MB):

- `data/processed/observations.parquet`: structured observations (`StatsData`).
- `data/manifests/manifest.json`: source provenance shown in answers, and the manifest hash in audit records.
- `data/passages/*.jsonl`: extracted MOM report passages (`load_passages`). Not redistributable publicly (D-001); server disk only.
- `data/index/embeddings/text-embedding-3-large/{keys.json,vectors.npy}`: cached chunk embeddings. Only the user's question is embedded at runtime. Each new question appends to this cache and to `usage.jsonl`, so the directory must stay writable; the files that exist at start stay valid.

Everything else under `data/` (raw PDFs and HTML, other embedding models, `runs/`, `export/`, `snapshots/`) is not needed by the web app and stays off the server, with one optional exception: the MCP sidecar's `get_revisions` tool reads `data/snapshots`, and without it that tool reports no history, which is not evidence that nothing was revised. Upload them with `--with-mcp-snapshots` if you run the sidecar.

**VERIFIED (local, 30 Oct 2026; corpus v1, historical: the live site serves corpus v3):** starting `Shared()` and then the web app against a `data/` directory containing exactly this set loaded 2,106 chunks, 13,484 passages and 3,790 in-scope observations without a network call or API key use, in about 2.5 seconds on the author's machine with a warm file cache. The container reported healthy about 9 seconds after start. The earlier estimate of 30 seconds for startup was not reproduced; no on-disk BM25 cache exists and none is needed at this size. Allow for slower cold-disk reads on the Droplet; the compose health check allows 120 seconds.

**Corpus on the Droplet.** The live site now serves corpus v3.1; the commit it runs is shown by `/healthz`, which also reports the passage and chunk counts (16,419 and 1,847) and the corpus fingerprints (`passage_set_sha256` `d402120f6f8f`, unchanged between v3 and v3.1, and `content_sha256` `242e2b284fbc` for v3.1). The local figures in the VERIFIED paragraph above (2,106 chunks, 13,484 passages, 3,790 in-scope observations) are corpus v1, measured on 30 Oct 2026 and kept as history of the startup check. Corpus v3 has 4,300 in-scope observations; see the corpus-versions statement in the [README](../README.md#corpus-versions). Four measured evaluations exist on v3 (the X2 development regression check, the `m7-e2efix-20261031` threat run, held-out v2 and the tool-set diagnostic), and the 65 fresh questions were re-run once on v3.1 (D-055).

Upload from your machine (dry run first, then transfer):

```sh
scripts/upload-corpus.sh deploy@<droplet-ip>            # lists what would be sent
scripts/upload-corpus.sh deploy@<droplet-ip> --go       # transfers exactly the files in deploy/runtime-data.txt
```

The script refuses to run if any listed file is missing locally, never uses `--delete`, and uses `StrictHostKeyChecking=yes`, so connect once by hand first to record the host key.

## 7. First deploy

Do the steps in order; there is no image until the workflow has run once.

1. Push to `master` (or run the workflow from the Actions tab with `workflow_dispatch`). The test and build jobs run; the deploy job will fail the first time if `/srv/labourlens/.env` or the data directory is missing, which is expected if you skipped sections 4 or 6.
2. After the deploy job succeeds, on the Droplet: `/srv/labourlens/deploy/deploy.sh status` shows the current tag, container state and `/healthz`.

To enable live mode: edit `/srv/labourlens/.env`, set `LABOURLENS_DEMO_ENABLED=true`, then run `/srv/labourlens/deploy/deploy.sh restart`.

## 8. How the client address and HTTPS are handled

The rate limiter keys on the client address. Behind a proxy that address comes from `X-Forwarded-For`, which a client can forge, so two things work together:

- Caddy **replaces** the header: `header_up X-Forwarded-For {remote_host}` discards whatever the client sent and passes the TCP peer address that Caddy sees. It also sets `X-Forwarded-Proto` and drops `X-Real-IP` and `Forwarded`.
- The app trusts the forwarded headers **only from Caddy's address**. `docker-compose.yml` fixes Caddy at `172.30.0.2` on a private network and sets `LABOURLENS_FORWARDED_ALLOW_IPS=172.30.0.2` for the app (read by `labourlens serve`, passed to uvicorn as `forwarded_allow_ips`, with `proxy_headers=True`). A request that reaches the app from any other address cannot change its client address or scheme. The setting refuses `*`. Without the variable the default stays `127.0.0.1`, as for local use.

**VERIFIED (local, real Caddy and the built image, 30 Oct 2026):** seven login attempts with seven different forged `X-Forwarded-For` values were limited after the fifth (`401 401 401 401 401 429 429`), so the forged header did not change the key. `tests/web/test_deploy_edge.py` shows the same at unit level: from an untrusted peer a forged header is ignored; from the proxy address it is used.

**Not verified:** the real client address a Droplet receives through Docker's published ports on IPv4. Docker's IPv4 NAT path normally preserves the source address; the IPv6 userland proxy may not. Keep IPv6 off on the Droplet, or check the address in the Caddy log before relying on per-IP limits (section 11).

Caddy sends HSTS (`max-age=31536000`), `Cross-Origin-Opener-Policy`, `Cross-Origin-Resource-Policy`, and removes `Server` and `Via`. The app already sends the CSP, nosniff, referrer policy, frame denial, permissions policy and API `no-store`; Caddy does not repeat them, so the policy has one owner. HTTP/3 is switched off because UDP 443 is not open. Caddy compresses responses, rejects bodies over 16 KB (the app's own cap is 8 KiB), waits up to 100 seconds for the app (the app waits 90), and writes a JSON access log to stdout with the query string, `Cookie`, `Authorization`, forwarded-for and `Set-Cookie` removed. There is no WAF and no Caddy-level rate limit.

The server logs its explicit trusted-proxy setting without secrets. Regression coverage for ignored untrusted forwarding, trusted HTTPS forwarding and the cookie's `Secure` flag is in `tests/web/test_deploy_edge.py` and `tests/web/test_security_fixes.py`; this documentation update did not run it. Caddy's HSTS is the deployed transport policy, not an app-level Host allow-list. Never expose the app port directly or broaden proxy trust to arbitrary peers.

## 9. Verify a deployment

On the Droplet and from your machine:

1. `curl -fsS https://<domain>/healthz` returns `{"status":"ok","version":"0.1.0+<commit sha>"}`. It is unauthenticated and returns nothing else.
2. `curl -sI http://<domain>/` redirects to HTTPS; the HTTPS response carries the CSP and `strict-transport-security`.
3. In a browser: the report, figures and source links load with live mode off and no OpenAI key.
4. `/api/status` shows the disabled, signed-out and signed-in states correctly; a wrong code is rejected, repeated attempts get a 429; a right code sets an HttpOnly, Secure, SameSite cookie.
5. With live mode on, ask one question as a signed-in reviewer. This makes a paid call and is a manual operator action, never a deployment hook. Check that the answer, evidence, chart and trace appear.
6. Send feedback once; confirm a sanitized record in `/srv/labourlens/data/audit/feedback.jsonl`.
7. Kill switch: set `LABOURLENS_DEMO_ENABLED=false`, run `deploy.sh restart`, and confirm new questions are rejected while the report stays up.

`uv run pytest tests/web` runs the offline acceptance tests with injected fake research and needs no corpus, network or key.

## 10. Operations

**Logs.** Docker rotates container logs (10 MB, 3 files each). On the Droplet: `/srv/labourlens/deploy/deploy.sh logs app 200`, or `caddy` or `mcp` in place of `app`. The app's uvicorn access log is off and error logs pass through the redaction filter; Caddy's access log omits query strings and cookies. Application records (runs, feedback, admission events) are JSONL in `/srv/labourlens/data/audit`, with HMAC-pseudonymised session and client identifiers. Rejection events include known routes only, are sampled per client, capped at 1 MiB per day and written off the event loop; they are not an exhaustive access log. String values are redacted before JSON serialization and JSONL readers preserve physical-line framing. Web runs use `save_trace=True` and save redacted traces under `data/runs/agent/`; retain/protect those files as private operational data too.

**Rollback by image tag.** Automatic: a failed `deploy.sh up` returns to the previous tag. Manual: `deploy.sh rollback` starts the recorded previous tag; or `deploy.sh up <sha>` for any earlier commit's tag that is still in GHCR. Rollback restores code only; the data directory and `.env` are untouched.

**Kill switch.** Set `LABOURLENS_DEMO_ENABLED=false` in `.env` and run `deploy.sh restart`. This blocks new live questions; it does not stop provider calls already running. To stop provider work immediately, revoke the OpenAI key.

**Rotating the API key.** Create a new restricted project key, put it in `.env`, run `deploy.sh restart`, then revoke the old key.

**Rotating access codes and the session secret.** Edit the values, run `deploy.sh restart`. The restart revokes all in-memory sessions, including when only access codes changed. `POST /api/logout` revokes the current session without a restart. After a suspected disclosure, rotate both and the API key. Fresh logins with the same code share a code-bound question-rate identity; shared codes are not individual accounts.

**Updating the corpus.** Run `scripts/upload-corpus.sh deploy@<ip> --go` from the machine that holds the new files, then `deploy.sh restart` so the app reloads them. If the file set changes, update `deploy/runtime-data.txt` first. The embedding cache must contain vectors for every chunk of the new passages; the app does not generate missing embeddings at startup, and a missing vector would be requested from the embeddings API on first use. Do not run `fetch`, `build`, `dense-exp`, `agent-exp` or `eval` on the server.

**Updating the corpus to v3.1 (D-052; not yet done on the Droplet).** Prerequisites on the machine that holds `data/`: the local rebuild is done (`experiments/corpus-snapshots/v3.1.json`) and the 10 new vectors are embedded (`labourlens` step in `docs/experiments/m7-corpus-v3-runbook.md`, "Applied: corpus v3.1"). Then, with the deploy key described in section 5 (the same key that `DROPLET_SSH_KEY` holds; no new secret):
1. `scripts/upload-corpus.sh deploy@<ip>` (dry run), then `--go`. The file list in `deploy/runtime-data.txt` is unchanged. Two groups of files differ: `data/passages/mti-2026-q2-feature-ai-employment.jsonl` (the only file with changed flags; required for correct retrieval) and the other 48 passage files, which differ only in the `parser_version` value (`extract-0.3`; optional for behaviour, recommended so the server holds the exact bytes of the local build; about 20 MB in all). `data/index/embeddings/text-embedding-3-large/cache.npz` (about 64 MB) must also be uploaded: it now holds the 10 new vectors, and the container refuses to start without a vector for every chunk. The upload replaces the Droplet's copy, which also drops cached question vectors added since the last upload; they are re-embedded on demand. `data/manifests/manifest.json` and `observations.parquet` are unchanged.
2. `ssh deploy@<ip> '/srv/labourlens/deploy/deploy.sh restart'`. No image rebuild is needed for the data, but the `/healthz` field `content_sha256` exists only in code from this change, so deploy the commit (push to `master`) before or together with the restart; with older code the restart still works and `/healthz` shows the old fields only.
3. Check `curl -fsS https://labourlens.navig.me/healthz`: expect `passage_set_sha256` **unchanged** `d402120f6f8f` (it hashes passage ids only and no id changed), `passages` 16419, `chunks` 1847, and, with the new code, `content_sha256` `242e2b284fbc` (v3 recomputed for comparison: `1c0f864650f2`; never served). If `content_sha256` is absent the old code is running. Local value: the command in section 11a (it now prints `content_sha256` too).
4. If the app exits at start with "embedding cache incomplete", `cache.npz` was not uploaded or lacks the 10 vectors; `deploy.sh` rolls back to the previous tag.

**Updating the application.** Merge to `master`; the workflow does the rest. Docs-only pushes do not deploy.

**Backups.** Two layers. (a) DigitalOcean Droplet snapshots or backups, taken from the control panel; **the snapshot cost was not verified here**, so check the current price before enabling scheduled backups. (b) A copy of the state that cannot be rebuilt, from your machine: `rsync -a deploy@<ip>:/srv/labourlens/data/audit/ ./backups/audit-$(date +%F)/`. The budget ledger (`data/audit/budget.json`) and feedback live there. Caddy's certificates live in the `caddy_data` Docker volume; they are re-issued automatically if lost, subject to Let's Encrypt rate limits. The corpus itself is reproduced from the author's machine with the upload script.

**Disk and memory.** The app container is limited to 1.25 GiB and Caddy to 192 MiB, on a 2 GiB Droplet with 1 GiB swap. The app's measured memory under load was not measured; check `docker stats --no-stream` after the first real use.

**Privacy.** Tell reviewers not to enter personal or confidential information: HTML and control-character stripping does not anonymise text. Set a retention period for `data/audit` and delete under it.

## 11. Limits

- **Single instance, no high availability.** One Droplet, one app process. A reboot, a failed deploy or a host fault means downtime. Rate counters and active-run admission are per process; the budget file is not a distributed ledger and has no cross-process lock.
- **The daily budget is estimated, not a billing guarantee.** Admission persists a conservative $0.05 run reservation before launching paid work and refuses admission when it cannot persist the ledger or fit the reservation. A successful, non-timed-out run reconciles to its reported cost; errors and HTTP timeouts keep the reservation, even if the worker later completes. A timeout does not stop provider calls. The $0.05 value is not a measured worst-case bound for all context sizes, model settings, retries or provider billing; a successful run can cost more. Keep the provider-side project budget/cap as the backstop and check whether the provider actually enforces a hard cap rather than only an alert. An unreadable ledger counts as exhausted. The day rolls over on the server's local date; the Droplet starts in UTC.
- **No WAF.** Caddy provides TLS, a body limit and header hygiene only. There is no bot filtering, no IP reputation and no Caddy-side rate limit; the app's per-client, code-bound and global login-failure limits provide the throttles. Per-client limits are only as good as the forwarded client address (section 8), and global login throttling may block legitimate reviewers during an attack.
- **Docker and ufw.** ufw does not filter published container ports. Only Caddy publishes ports; the DigitalOcean cloud firewall is the second layer.
- **Deploy user is root-equivalent** through the docker group.
- **Rollback does not restore data.**
- **Authentication is shared access codes**, not accounts. There is no OAuth and no per-user authorisation.
- **Report rights are still restrictive.** The web projection replaces free-text fields containing more than 12 consecutive evidence words, allows at most 12 claims and 3 citations per claim, caps each quotation at 40 words and total quotations at 120 words per answer, and deduplicates evidence-card quotes (also capped at 120 words per card). These controls reduce verbatim disclosure, not confer a reproduction licence. Paraphrase and accumulation across repeated questions remain residual rights risks; do not publicly package full reports or extensive extracts.
- **Dependency review is informational.** `uv.lock` and `uv sync --frozen` preserve the reviewed resolution. No advisory scan was run as part of this security documentation update; no CVE or vulnerability-free claim is made. See the full AI review and all ten finding statuses in `docs/security-review-web.md`.
- **Not verified on the Droplet:** a provider-side OpenAI spend cap, restart rollback, the backup procedure, the real client address behind Docker's published ports, memory under load, and the snapshot cost. Bootstrap, the Actions run, the GHCR pull and certificate issuance did succeed on 31 Oct 2026 (`docs/progress.md`).

## 11a. Operations added after the end-to-end review (D-043)

**Corpus identity.** `GET /healthz` returns `{"status","version","corpus"}`. `corpus.passage_set_sha256` is a hash of the sorted
passage ids (each id embeds a content hash), with `passages` and `chunks` counts. After an upload, compare it with the local value
(on the machine that built the corpus: `uv run python -c 'from labourlens.retrieval import chunk as c, runtime as r; p=c.load_passages(); k=c.build_chunks(c.CONFIGS[r.CHUNK_CONFIG], p); print(r.corpus_fingerprint({x["passage_id"]:x for x in p}, {y.chunk_id:y for y in k}))'`; it printed `d402120f6f8f`, 16,419 passages, 1,847 chunks on 31 Oct 2026; on corpus v3.1 it prints the same `passage_set_sha256` plus `content_sha256` `242e2b284fbc`, because a re-flag changes no passage id) before
assuming which corpus is served. Per the owner (not verifiable from files), the Droplet's `/healthz` reports the same fingerprint, 16,419 passages and 1,847 chunks (corpus v3). Audit records carry the same value under `version.corpus`.

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

**Login lock.** The lock is per client address: 10 failed logins in 10 minutes lock that address. A global threshold (200 failures) still refuses invalid codes, but a valid code is never refused by either lock, so one address cannot lock everyone out. The per-address request limit (5 a minute) is unchanged.

**Feedback.** Feedback is accepted only for run ids that the same session started, and `feedback.jsonl` is capped at 2 MiB.

## 12. What was verified locally (30 Oct 2026)

Run on the author's Mac with Docker Desktop (Docker 29.5.3), not on Ubuntu or a Droplet:

- `scripts/check-build-context.sh` against the repository: the context holds 125 files with top level `prompts pyproject.toml specs src uv.lock web`; run against a copy without `.dockerignore` it fails and lists `data/`, PDFs and corpus files.
- `docker build` succeeded; a container started with the minimal data set, read-only root filesystem, all capabilities dropped and a fake key became healthy and answered `/healthz`, `/api/status`, `/` and an unauthenticated `/api/ask` (401). The image's `/app/data` was empty.
- `docker compose config` parsed the file; with a local override (data path and unprivileged ports only) the full stack, including the `mcp` profile, started healthy; Caddy served HTTPS for `localhost`, redirected HTTP, compressed, rejected a 20 KB body with 413, and kept query strings and cookies out of its log. The MCP port answered 401 inside the app's network namespace and was unreachable from the host.
- `/api/ask` with a fake agent against the real `Shared()` over the minimal data set returned 200.
- `actionlint` on the workflow; `shellcheck` at warning level on the scripts; `caddy validate` on the Caddyfile.
- A checkout with no corpus (tracked and untracked non-ignored files copied to a temporary directory, `git init`, `uv sync --frozen`): 287 tests passed and 1 was deselected (`test_every_ok_entry_has_matching_file_hash`, which needs the raw files), in about 4 minutes. That run also fixed an existing failure: `test_no_pdfs_or_mom_text_visible_to_git` flagged the application's own `web/index.html`; it now exempts `web/`. Whether the same suite passes on a GitHub runner (network, clock, Python download) was not tested.

## 13. Optional: MCP statistics server as a loopback sidecar

**What this is.** The read-only MCP statistics server can run over streamable HTTP on the loopback interface, protected by a bearer token. It is for a second local process (for example an MCP client on the same machine or in the same container) and is **not** a public endpoint. Not built: OAuth, per-client authorisation, TLS termination. The web app does not need it: it starts its own stdio server subprocess for the agent's `get_series` (D-053; `LABOURLENS_MCP=false` disables that). stdio stays the tested default (`uv run python -m labourlens.mcp.server`).

**Rules.** Same container network namespace as its client, bound to `127.0.0.1`, token supplied by the environment, never published through Caddy or the host, never on `0.0.0.0`. The server refuses to start without a token of at least 24 characters and refuses a non-loopback `--host` unless `--allow-nonloopback` is given (that flag prints a warning: it then needs TLS and a real authentication layer, which this server does not provide). It reads only the observations table, the manifest, the snapshot CSVs and the dataset adapter specs; it holds no API key and serves no MOM report text.

**Enable it with the compose profile.** The `mcp` service in `deploy/docker-compose.yml` joins the app container's network namespace (`network_mode: "service:app"`), so port 8765 exists only on that loopback and nothing publishes it. It has its own env file so the app never receives the token and the sidecar never receives the OpenAI key.

```sh
ssh deploy@<droplet-ip>
umask 077
python3 -c "import secrets; print('LABOURLENS_MCP_TOKEN=' + secrets.token_urlsafe(32))" > /srv/labourlens/mcp.env
/srv/labourlens/deploy/deploy.sh restart      # deploy.sh adds --profile mcp when mcp.env exists
```

`deploy.sh` enables the profile whenever `/srv/labourlens/mcp.env` exists. To remove the sidecar, delete the file and run `docker rm -f labourlens-mcp-1`. Upload the snapshot files once with `scripts/upload-corpus.sh deploy@<ip> --go --with-mcp-snapshots`.

**Health probe.** There is no unauthenticated health route on purpose. An unauthenticated request to `/mcp` must return 401 with an empty body; that proves the process is up and the token check is on. The compose health check uses exactly this.

**Client.** Set `LABOURLENS_MCP_TOKEN` in the client's environment and use the allow-listed `labourlens-stats-http` entry (`http://127.0.0.1:8765/mcp`). The client refuses non-loopback URLs and sends the token only there. Rotate by changing `mcp.env` and restarting.

**Verification.** Locally verified: the profile started healthy and answered 401 inside the app's namespace, and the port was unreachable from the host (section 12), in addition to `tests/mcp/test_http.py`. On the Droplet: `docker exec labourlens-app-1 python -c ...` as in the health check returns 401, `ss -ltn` on the host shows nothing on 8765, and `docker logs labourlens-mcp-1` contains no token.

## 14. The workbench MCP tab (read-only endpoints)

The Workbench right rail has an MCP tab that shows the local MCP server the agent reads statistics through. Both endpoints need the signed session cookie and the same origin check as `/api/ask`; neither calls a model.

- `GET /api/mcp` returns `{enabled, connected, message, server {name, version, protocol_version, capabilities, transport}, tools [{name, title, description, read_only, input_schema (property names, types, enums, descriptions only)}], resources, prompts, used_by_agent, not_given_to_agent, recent_calls, examples}`. `protocol_version` and `capabilities` are what the client and server negotiated at initialize. Discovery (`list_tools`, plus `list_resources`, `list_resource_templates` and `list_prompts` only for capabilities the server declared) runs once through the app's existing client connection and is cached. `recent_calls` are the newest 20 lookups made in the caller's own session (tool, non-empty arguments, milliseconds, ok, quarantined rows); other visitors' calls are never returned. The server keeps one bounded in-memory deque for the operator, each entry tagged internally with the session that caused it; the tag is not part of the response. If MCP is off (`LABOURLENS_MCP=false`) or not connected it answers 200 with the flags and a message, never 500. Limit: six times the per-session limit per window.
- `POST /api/mcp/try` takes `{"example": id}` where `id` is one of three fixed server-side read-only examples (`latest_resident_unemployment`, `retrenched_2025q1_to_2026q1`, `list_datasets`). Any other value is 422; tool names and arguments are never taken from the request. The call runs through the MCP client (argument validation, size cap, quarantine apply) and returns `{tool, arguments, ms, ok, reply | error}`. The reply is capped at 8,000 characters and passed through the same value redaction as `/api/ask`. It counts against the per-session and per-address request limits; there is no cost.
