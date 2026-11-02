# Security

This is a research project, not a service with a support contract. The live demonstration is a single small server behind access codes.

## Reporting

Please report a vulnerability privately to the repository owner (GitHub: `mihirkhandekar`) rather than opening a public issue. Include what you tried and what happened. Do not include real credentials or any text that is not public.

## How secrets are handled

- No secret is committed. `.env` is gitignored; `.env.example` and `deploy/.env.example` hold empty values and describe every variable. A scan of the full git history (`gitleaks`, config in `.gitleaks.toml`) finds no secret; its only allowlisted matches are public data.gov.sg dataset identifiers.
- `make secrets-scan` checks that no private corpus, PDF or `.env` file is tracked and runs gitleaks when it is installed. CI runs the same check on every pull request.
- At runtime, responses, audit lines and traces pass through a redaction step covering environment secret values and key-shaped strings. IP addresses and session ids are stored only as keyed hashes (`docs/audit-and-logging.md`).
- Live access codes and the session secret are server-side environment values and are never published in this repository. Deployment secrets are GitHub Actions secrets (`docs/deploy.md`).

## How untrusted text is handled

Retrieved passages, dataset text and MCP tool output are treated as data, never as instructions. The controls (ingestion scanning, quote and number validation, output screening, tool allow-lists and schema checks, step and time bounds, a read-only tool set) and the measured results, including the ones that failed, are in [`docs/threat-model.md`](docs/threat-model.md). The planted-figure case T-I06 is not shown stable across runs; the injection scanner missed all five paraphrased probes. These are stated limits, not fixed issues.

## Rights

Full MOM/MTI documents, extracted passage stores and raw answer transcripts are absent from the current tracked tree. This is not a history-wide absence claim: pre-truncation section headings and a few review-note sentences remain in Git history; the 1,031 shortened runs in 35 files are recorded in `experiments/rights-truncation-sidecar.json`. `uv run labourlens rights-scan` detects exact overlap within its exclusions, not permission or complete copyright compliance. Without the private passage corpus it reports `NOT CHECKED`, normally exits zero, and is not a pass; see [data-sheet section 9](docs/data-sheet.md#9-open-licence-items-and-what-the-rights-scan-covers).

## Historical disclosure and packaging

Published data.gov.sg officer addresses remain unredacted in history, although current metadata uses replacement addresses. A dashed `sslip.io` hostname encoding the first deployment IP remains in commits `c297146` and `d835e6f`; no hostname or address is reproduced here. Local `/Users` paths and historical `prompts/meta/` authoring prompts also remain in history. Current test artefacts replace local paths with `<repo>`; this is a path-only scrub, not a rerun.

The reviewer-session `.env` exposure is recorded in [the historical security review](docs/human-review/e2e-review-security-deploy.md). That record does not establish key rotation; rotation status remains an owner action, not a claimed completed control. Share only a repository URL, fresh clone or `git archive HEAD`, not the working folder with ignored private data.
