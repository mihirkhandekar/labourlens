# Archived gold versions

Byte-exact copies of `experiments/gold/draft_cases.jsonl` as committed at each version, recovered from git history. Each hash is the value recorded in the gold changelog or in saved metrics. Use `--gold` to rescore frozen runs against the gold they were scored on.

| file | source commit | SHA-256 | used by |
|---|---|---|---|
| gold-v3.2.jsonl | b813274 | 647b26a2f0fa… | generation of H-hybrid; `dev-R*` retrieval study |
| gold-v3.3.jsonl | cf6a4fe | 96ec51baf05d… | held-out rescoring after HO-029 |
| gold-v3.4.jsonl | 43af8d5 | 050bb40b4863… | held-out rescoring after HO-027, HO-023, HO-004 |
| gold-v3.5.jsonl | 456ffa9 | aac4b405b51c… | published A1-A5 and H-* metrics (corpus v1 passage IDs) |

The live file is v3.6 (`6169a9de…`, corpus v3 passage IDs) and scores only the X1/X-* runs.
