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

MOM and MTI documents, text extracted from them and raw model outputs are not in this repository. `uv run labourlens rights-scan` fails if a tracked file repeats more than six consecutive words of the local copies. It needs the private corpus and reports `NOT CHECKED` without it. See `docs/data-sheet.md` section 9 for what it does not cover.
