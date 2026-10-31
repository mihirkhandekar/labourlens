# Corpus v3 (= corpus v2 + heldout-v2 labour sources): preparation and ordered commands

**DECISION (D-040, owner 31 Oct 2026):** build an evidence-disjoint held-out v2 from new, labour-relevant sources only. **No MTI advance/Economic Survey GDP pairs.** This document records what was prepared offline and the exact commands the parent runs after the credentialed evaluation job releases `data/`. **Nothing below has been fetched, built, indexed or embedded.** Every number marked `TBD` is filled only from observed output of the run.

## What was prepared (code and specs only; no `data/` access except two read-only fingerprints)

| Item | Where |
|---|---|
| 3 documents, 3 datasets promoted to the live catalog (additive file) | `specs/sources.d/heldout-v2-expansion.yaml` |
| Dataset adapter specs with exact first/last periods | `specs/datasets/{unit_labour_cost_index_quarterly,value_added_per_worker_quarterly,avg_weekly_paid_hours_quarterly}.yaml` |
| MTI PDF host on the allow-list (`https` only; look-alike and `www.mti.gov.sg` page hosts refused) | `src/labourlens/data/acquire.py` |
| `Unit` literal extended (`index_2015_100`, `chained_2015_dollars`, `hours_per_week`) so the new rows validate | `src/labourlens/models.py` |
| Per-dataset licence caveat (`rights_note_extra`: "to verify on dataset page") written into the manifest note | `src/labourlens/data/fetch.py` (`dataset_rights_note`), spec entries |
| Fingerprint helper (passage files, per-source observation hashes, chunks) | `src/labourlens/data/fingerprint.py` |
| v2 baselines: passage hashes (46 files) and per-source observation hashes (33 sources, 43,662 rows) | `experiments/corpus-snapshots/v2.json`, `v2-observations.json` |
| Tests (20 pass, 1 corpus test skipped until fetch) | `tests/data/test_corpus_v3_additive.py` |

The proposed file `specs/sources-heldout-v2.proposed.yaml` was promoted and removed; its rationale stays in `docs/experiments/m7-heldout-v2-sources.md`.

### The batch

| Source id | Kind | Publisher | Published | Stage | Rights recorded (local-only for all documents) |
|---|---|---|---|---|---|
| `mom-wage-practices2025` | PDF | MOM MRSD | 2026-05-28 | annual | all rights reserved (notice read by SourceScout; re-confirm after fetch) |
| `mom-nwc-lower-wage2025` | PDF | MOM MRSD | 2026-10-23 (PDF creation date; confirm vs newsroom) | annual | all rights reserved (as above) |
| `mti-2026-q2-feature-ai-employment` | PDF (`isomer-user-content.by.gov.sg`) | MTI | 2026-08-11 | not_applicable | **unresolved** (own notice not read) |
| `unit_labour_cost_index_quarterly` | dataset `d_f9fc9b5420d96bcab45bc31eeb8ae3c3` | SingStat | lastUpdated from API | snapshot | Open Data Licence **assumed; to verify on dataset page** |
| `value_added_per_worker_quarterly` | dataset `d_fa4dcbefadf3e93e99c7d88de0f53406` | SingStat | as above | snapshot | as above |
| `avg_weekly_paid_hours_quarterly` | dataset `d_aebf156556c15c9c312ff23d24bf7278` | MOM | as above | snapshot | as above |

Exact first periods (validator already demands equality for every source except `employment_change_by_sector`): 1980-Q1, 1991-Q1, 1998-Q1; last 2026-Q2. A table that starts later, ends earlier, leaves an in-scope series with a missing quarter row, or has a total row outside the plausible range fails the build check; a published `na` inside scope warns and is stored as null, never zero. Unit tests prove each of these on synthetic fixtures (`tests/data/test_corpus_v3_additive.py`). The sector hierarchy-sum check does not apply to the new tables (parent/child sums are not asserted in their specs).

### Additivity argument and proof

Passage ids derive from source, snapshot, locator and text hash, observation ids from source id plus content, chunk ids per source; nothing global enters. The synthetic test builds passages and `merge200` chunks for one PDF alone and beside a second PDF and asserts byte-identical passage files, ids, hashes and chunk ids; another test shows observation ids cannot collide across sources. After the real build, the corpus test `test_corpus_v2_passages_and_observations_unchanged_after_v3_build` compares the 46 v2 passage files and the 33 v2 per-source observation hashes with the saved baselines.

## Consequences the parent must know

1. **Live catalog changed now.** Any process started after this edit reads the three new documents and datasets from specs. Until the build, the agent's enums come from `data/processed` (unchanged) and the new documents have no chunks, so retrieval behaviour is unchanged; the MCP source catalogue resource already lists the new entries (regenerating `docs/mcp-demo-transcript.md` would differ). `labourlens build` or `validate` **fails the manifest checks until the fetch below has run**. A run in progress keeps its in-memory catalog.
2. After the build, `retrieval/period.py` includes the new documents in period/stage hint filtering (R1a/R3 pools). Corpus-v3 dev numbers are therefore not comparable to the corpus-v2 X1 runs without saying so.
3. The T-I06 guard (`answer/crosscheck.py`) cross-checks only its fixed alias set of existing series; it will not check figures from the three new datasets. `agent/tools.py` and `reconcile.py` key vintage logic to `mom-YYYY-qN-*` ids (the one MTI document is not a MOM release).
4. The MTI article is two-column; `pdf_extract` was tuned on MOM layouts. Inspect extraction before authoring (step 5). A poor extraction needs a parser fix and a new parser version before cases are written.
5. Checks expected after the build: 255 existing + 7 per new dataset = **276 [INFERENCE from `check_datasets`; confirm]**, zero failures. The unresolved-rights warning lists the MTI article (and the three datasets only if their pages disagree).

## Ordered commands (single writer; run only when no `agent-exp`, `eval`, embedding or `build` process is active)

Credentials: only step 1 needs network (no API key) and only step 11 needs `OPENAI_API_KEY`; every other step is offline and free.

```sh
# 0. preserve corpus v2 (data/ is mutated below); keep alongside the v1 copy
mkdir -p private/corpus-v2-frozen && cp -R data/passages data/manifests data/processed data/index private/corpus-v2-frozen/
cp data/manifests/manifest.json /tmp/manifest-v2.json

# 1. fetch ONLY the new sources (network; datasets are throttled to ~13 s per request)
uv run labourlens fetch --kind documents --only mom-wage-practices2025 mom-nwc-lower-wage2025 mti-2026-q2-feature-ai-employment
uv run labourlens fetch --kind datasets --only unit_labour_cost_index_quarterly value_added_per_worker_quarterly avg_weekly_paid_hours_quarterly

# 2. prove the 79 existing manifest entries are untouched and the 6 new ones are ok
uv run python -c "import json;from labourlens import paths;L=lambda f:{e['source_id']:e for e in json.load(open(f))['entries']};s=L('/tmp/manifest-v2.json');t=L(paths.MANIFESTS/'manifest.json');print('changed existing:',[k for k in s if s[k]!=t.get(k)]);print('new:',{k:t[k]['retrieval_status'] for k in t if k not in s})"
```

If step 2 lists a changed existing entry or a non-`ok` new one, stop and report.

```sh
# 3. rights confirmation before anything is committed (no network): read the notices in the fetched PDFs, then edit the spec entries
#    - MTI article notice, MOM wage reports' notices, NWC publication date vs MOM newsroom; each dataset page's licence
#    Datasets stay local (do not `git add` data/snapshots/<new ids>) until the dataset-page licence is verified.

# 4. build (deterministic; extraction version unchanged: extract-0.2)
uv run labourlens build

# 5. extraction quality of the new documents BEFORE authoring
uv run python -c "import json;from labourlens import paths;[print(s['source_id'],s.get('pages'),s.get('passages'),s.get('flags')) for s in json.load(open(paths.ARTIFACTS/'extraction_stats.json')) if s['source_id'] in ('mom-wage-practices2025','mom-nwc-lower-wage2025','mti-2026-q2-feature-ai-employment')]"
#    then open 3 passages of the MTI file via `uv run labourlens trace <passage_id>` and check that columns are not interleaved

# 6. determinism: rebuild and compare every passage/Parquet file byte for byte
uv run python -c "
import hashlib,json
from labourlens import paths
from labourlens.data import build
fs=lambda:{str(f.relative_to(paths.ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(list(paths.PASSAGES.glob('*.jsonl'))+list(paths.PROCESSED.glob('*.parquet')))}
a=fs();rc=build.run();b=fs()
(paths.ARTIFACTS/'determinism-v3.json').write_text(json.dumps({'build_exit_code':rc,'files_checked':len(a),'byte_identical':a==b,'changed':[k for k in a if a[k]!=b[k]]},indent=2)+'\n')
print(rc,len(a),a==b);raise SystemExit(rc or int(a!=b))"

# 7. counts and checks (expected: 255 existing + 21 new dataset checks; all new observations in answer scope per series = 10 quarters)
uv run python -c "
import json,collections;from labourlens import paths
r=json.load(open(paths.ARTIFACTS/'validation.json'));print(collections.Counter(c['status'] for c in r['checks']),len(r['checks']))
print([c for c in r['checks'] if c['status']!='pass' and any(s in c['name'] for s in ('unit_labour','value_added','paid_hours','rights','manifest'))])"
uv run labourlens scan-sources

# 8. additivity proof on real outputs (reads data/; corpus-marked)
uv run pytest -q -m corpus tests/data/test_corpus_v3_additive.py

# 9. persisted BM25 index for corpus v3
uv run python -c "from labourlens.retrieval import chunk as c, runtime as r; from labourlens.retrieval.bm25_index import BM25Index, BM25Config; ch=c.build_chunks(c.CONFIGS[r.CHUNK_CONFIG], c.load_passages()); print(len(ch), BM25Index.build(ch, BM25Config()).save(r.CHUNK_CONFIG))"

# 10. embedding plan with exact token count and cost (offline; needs tiktoken in the uv cache)
uv run --with tiktoken python -c "
import json,tiktoken,yaml
from labourlens import paths
from labourlens.retrieval import chunk as c, dense as d, runtime as r
chunks=c.build_chunks(c.CONFIGS[r.CHUNK_CONFIG], c.load_passages()); m=r.EMBEDDING_MODEL; cache=d.VectorCache(m)
texts={d._h(m,x.text):x.text for x in chunks}; miss={k:t for k,t in texts.items() if k not in cache.keys}
enc=tiktoken.get_encoding('cl100k_base'); n=sum(len(enc.encode(t,disallowed_special=())) for t in miss.values())
rate=yaml.safe_load((paths.ROOT/'specs/prices.yaml').read_text())['embedding'][m]['input']
out=dict(model=m,chunks=len(chunks),unique_inputs=len(texts),cached=len(texts)-len(miss),new_vectors=len(miss),new_input_tokens=n,usd_per_million=rate,estimated_usd=n*rate/1e6)
(paths.ARTIFACTS/'embedding-plan-v3.json').write_text(json.dumps(out,indent=2)+'\n');print(out)"

# 11. CREDENTIALED: fill only the missing vectors (cost = step 10 estimated_usd; content-keyed cache, existing vectors reused)
uv run python -c "from labourlens.retrieval import chunk as c, dense as d, runtime as r; ch=c.build_chunks(c.CONFIGS[r.CHUNK_CONFIG], c.load_passages()); print(d.DenseIndex(ch, d.DenseConfig(r.EMBEDDING_MODEL)).matrix.shape)"

# 12. freeze the corpus-v3 fingerprint BEFORE any held-out case is authored or any run is made
uv run python -c "from labourlens.data import fingerprint; print(fingerprint.write('v3'))"      # -> experiments/corpus-snapshots/v3.json

# 13. verification (main agent, once)
uv run labourlens gold-check
uv run pytest -q -m 'not corpus'
uv run pytest -q tests/data -m corpus
```

## Results to record after the run (placeholders; do not pre-fill)

| Quantity | Value |
|---|---|
| New documents extracted / pages / passages (each of 3) | TBD |
| New observations per dataset; in-scope rows | TBD |
| Total passages / chunks / sources (expected sources 79 + 6 = 85; documents 49, datasets 36) | TBD |
| Checks total / pass / warn / fail | TBD |
| Build determinism (`determinism-v3.json`) | TBD |
| v2 passage files and v2 per-source observation hashes unchanged | TBD (step 8) |
| New vectors / tokens / exact estimated cost / billed cost | TBD (steps 10 and 11) |
| BM25 index directory and corpus hash | TBD |
| Fingerprint SHA of `experiments/corpus-snapshots/v3.json` | TBD |

Rollback: delete `specs/sources.d/heldout-v2-expansion.yaml`, the three adapter specs and the new manifest/data entries (or restore `private/corpus-v2-frozen/`). Frozen v1 and v2 results and `experiments/corpus-snapshots/{v1,v2}.json` are never edited.
