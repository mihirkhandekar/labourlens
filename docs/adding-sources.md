# Adding and reprocessing sources

How a new report, dataset or agency enters LabourLens, and how it is reprocessed. Part 1 is how it works **today** (built in M1). Part 2 is what production systems usually add (**PROPOSAL**, not built).

## 1. Today
1. **Register.** Add an entry to `specs/sources.yaml`: publisher, title, canonical URL, download URL, release stage, period, and **rights status with the evidence** (quote the notice you read).
2. **Allow the host.** A new publisher host must be added to the fetch allow-list in `data/acquire.py` (a deliberate code change, reviewed).
3. **Datasets only:** add `specs/datasets/<id>.yaml` (columns, measures, unit, population, adjustment, missing tokens, plausible range). A schema change fails the build loudly.
4. **Fetch** (`labourlens fetch --only <id>`). The file is stored in a new hash-addressed snapshot and the manifest and its history are updated. Existing snapshots are never overwritten.
5. **Build** (`labourlens build`). Normalise, extract passages, run all checks. Today this reprocesses everything; it is deterministic, so unchanged inputs give identical outputs (tested).
6. **Review and test.** Quality report, spot-check sheet rows for the new source, tests for any new adapter behaviour.
7. **Record** in `docs/data-sheet.md` and `docs/decisions.md` if it changes scope.

**A revised report** (for example MOM republishes a final report) is a new snapshot of the same `source_id`. `labourlens revisions` diffs the old and new CSVs. Old answers remain reproducible because their snapshot id is still stored.

## 2. What production systems usually do (PROPOSAL)
| Practice | What it means | Why |
|---|---|---|
| Source registry | A catalog of every source with owner, licence, refresh cadence, parser and trust level | Different agencies have different formats, licences and reliability; the registry is the single place to see this |
| Per-source connectors behind one interface | `fetch -> snapshot -> parse -> normalise` with the same output schema | New agency means a new connector, not a new pipeline |
| Common canonical schema | Observations and passages look the same whatever the source; source-specific quirks stay in adapters | Retrieval and agent code never branches on agency |
| Content hashing and incremental builds | Reprocess only sources whose hash changed; version the parser | Cheaper and traceable; today's full rebuild is fine at 33 sources but does not scale |
| Versioned indexes | Index names carry corpus hash and parser version (D-012) | Stale index fails loudly |
| Per-source trust and rights metadata enforced in code | `rights_status`, `commit_text`, and allowed use travel with every record | Mixed licences are the norm for government content |
| Definition crosswalks | An explicit table mapping similar-sounding measures across agencies (for example MOM versus SingStat unemployment) with the difference stated | The main risk when mixing agencies is comparing things that are not the same |
| Freshness and drift monitoring | Scheduled fetch, alert on schema change, on missing quarter, on large revision | Sources change without notice |
| Re-evaluation on change | Re-run the evaluation set after any corpus or parser change; compare to the previous run | Catches regressions caused by data, not code |
| Human gate for new sources | Owner approves licence and scope before a source reaches answers | Same as our approval gates |

## How to explain it (interview)
"Each source goes through the same four stages and lands in two canonical tables, observations for numbers and passages for text. Anything source-specific lives in a spec file. Every record carries its source, snapshot, parser version and rights status, so I can reprocess one source without touching the rest, and I can say what an old answer was based on. For multiple agencies the real risk is definitions, so I'd add a crosswalk and refuse to merge series that don't match."
