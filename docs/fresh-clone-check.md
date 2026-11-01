# Fresh-clone check

How a clone of this repository behaves without the private corpus, and what was observed.

Procedure: `git clone <this repository> /tmp/<dir>`, check out the branch, then `make setup && make verify` in the clone. No `.env`, no `data/raw`, `data/passages` or `data/index`, no API key.

## Observed result (2 Nov 2026, clone of commit `ab56fcd`, macOS, Python 3.12.12)

The clone was taken at `ab56fcd`, the HEAD at the time, and the uncommitted fixes of 2 Nov 2026 were applied to it with `git diff | git apply` before running (the unused import in `src/labourlens/mcp/client.py`, the call timeout in `tests/mcp/test_negotiation.py`, the `mcp-demo --out` change, and documentation edits). Run again on a clone of the commit that contains them if you need the exact commit.

| Command | Observed |
|---|---|
| `make setup` | locked environment installed from `uv.lock` (needs the package index) |
| `make lint` | `All checks passed!` |
| `make test` | `1027 passed, 1 skipped, 57 deselected, 5 warnings in 160.51s`. The skip is a test that needs local passages. The 5 warnings are SWIG deprecation notices from a dependency. In the working tree with the corpus, the same command gave `1028 passed, 57 deselected in 92s`. |
| `make docs-check` | `docs-check: 0 problem(s) in 185 Markdown files` |
| `make rights-scan` | `NOT CHECKED. .../data/passages is absent, so there is no source text to compare against.` Exit 0; with `RIGHTS_FLAGS=--require-corpus` it exits 2. This is not a pass. In the working tree with the corpus: `0 hit(s) in 0 file(s) with hits; allowlisted globs: 19`. |
| `make secrets-scan` | no private corpus, PDF or `.env` file tracked; `gitleaks`: `120 commits scanned ... no leaks found` |
| `make verify` as a whole | passed; 3 min 0 s wall time in the clone (1 min 52 s in the working tree) |

Before the fixes, the same clone failed `make lint` (unused import) and two tests in `tests/mcp/test_negotiation.py` failed under CPU load (the 5 s call timeout includes starting the server process). After raising that timeout to 30 s the file passed three times in a row (25 passed each time, about 23 s).

Not checked in the clone: the live workbench (needs the corpus, an API key and server secrets), the 57 corpus-marked tests, the rights scan against source text, the GitHub Actions run of `ci.yml` (no run existed at the time of writing, so no CI result is claimed).

Superseded: the earlier record of 1 Nov 2026 (commit `71c6482`, 785 passed) is replaced by the table above.
