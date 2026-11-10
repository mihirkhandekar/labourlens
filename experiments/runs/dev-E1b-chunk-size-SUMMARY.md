# E1b chunk-size BM25 (MEASURED, dev only)

Primary n=128; secondary eligible original E1 id subset n=23 of 24, using current gold and v3.1 corpus, not historical scores. Excluded ids with no current answerable text gold: ['DEV-034']. DEV-034 is now abstain with no evidence_text; no fabricated relevance or miss is assigned.

Paired columns = first-relevant-rank better/worse/same; missing top10 = rank 99. Intervals = paired hit@8 difference, 10,000 case bootstrap samples, seed 20261110.

## Primary current dev text cases

| config | chunks | mean words | hit@1 | @3 | @5 | @8 | @10 | MRR | passage recall@5 | ctx words@5 | vs merge200 B/W/S | vs merge120 B/W/S | hit@8 delta vs 200 [95% CI] |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| blocks | 9052 | 25.09 | 0.0781 | 0.1562 | 0.2188 | 0.2812 | 0.3203 | 0.1389 | 0.196 | 126.6 | 8/53/67 | 7/52/69 | -0.1953 [-0.2734, -0.1172] |
| merge120 | 2494 | 96.39 | 0.1797 | 0.3281 | 0.4062 | 0.4766 | 0.5156 | 0.2753 | 0.3626 | 573.7 | 31/24/73 | 0/0/128 | 0.0 [-0.0625, 0.0625] |
| merge200 | 1847 | 127.89 | 0.1406 | 0.3359 | 0.4062 | 0.4766 | 0.5391 | 0.2589 | 0.3496 | 832.1 | 0/0/128 | 24/31/73 | 0.0 [0.0, 0.0] |
| fixed150 | 1900 | 148.74 | 0.1719 | 0.3359 | 0.4141 | 0.4922 | 0.5156 | 0.2729 | 0.3639 | 732.4 | 26/30/72 | 22/30/76 | 0.0156 [-0.0391, 0.0703] |
| merge300 | 1598 | 147.41 | 0.1406 | 0.3438 | 0.4062 | 0.4688 | 0.5 | 0.2584 | 0.3483 | 1058.7 | 23/19/86 | 26/29/73 | -0.0078 [-0.0469, 0.0312] |
| merge400 | 1494 | 157.15 | 0.1641 | 0.3359 | 0.4297 | 0.5 | 0.5312 | 0.2733 | 0.3553 | 1246.7 | 28/21/79 | 28/27/73 | 0.0234 [-0.0234, 0.0703] |

## Secondary original E1 case-id subset

| config | chunks | mean words | hit@1 | @3 | @5 | @8 | @10 | MRR | passage recall@5 | ctx words@5 | vs merge200 B/W/S | vs merge120 B/W/S | hit@8 delta vs 200 [95% CI] |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| blocks | 9052 | 25.09 | 0.0435 | 0.1739 | 0.2609 | 0.3043 | 0.3478 | 0.1393 | 0.1884 | 125.2 | 0/9/14 | 0/9/14 | -0.2174 [-0.3913, -0.087] |
| merge120 | 2494 | 96.39 | 0.1304 | 0.3913 | 0.4348 | 0.4783 | 0.4783 | 0.2678 | 0.3333 | 578.1 | 2/4/17 | 0/0/23 | -0.0435 [-0.1304, 0.0] |
| merge200 | 1847 | 127.89 | 0.1739 | 0.3913 | 0.4783 | 0.5217 | 0.5217 | 0.3094 | 0.3406 | 833.3 | 0/0/23 | 4/2/17 | 0.0 [0.0, 0.0] |
| fixed150 | 1900 | 148.74 | 0.1739 | 0.3478 | 0.3913 | 0.4783 | 0.5217 | 0.2828 | 0.3043 | 730.6 | 3/6/14 | 4/5/14 | -0.0435 [-0.1304, 0.0] |
| merge300 | 1598 | 147.41 | 0.1739 | 0.3913 | 0.4783 | 0.5217 | 0.5217 | 0.2928 | 0.3333 | 1072.9 | 3/4/16 | 5/3/15 | 0.0 [0.0, 0.0] |
| merge400 | 1494 | 157.15 | 0.2174 | 0.4348 | 0.5652 | 0.5652 | 0.5652 | 0.3471 | 0.3576 | 1268.2 | 5/2/16 | 7/2/14 | 0.0435 [0.0, 0.1304] |

## Family hit@8 (primary)

| family | n | blocks | merge120 | merge200 | fixed150 | merge300 | merge400 |
|---|---:|---:|---:|---:|---:|---:|---:|
| adversarial | 13 | 0.1538 | 0.3846 | 0.4615 | 0.3846 | 0.4615 | 0.4615 |
| ambiguity_insufficient_causal | 2 | 0.0 | 0.5 | 0.0 | 0.0 | 0.0 | 0.0 |
| cross_source_synthesis | 34 | 0.1765 | 0.3235 | 0.3235 | 0.3529 | 0.3235 | 0.3235 |
| factual_lookup | 50 | 0.4 | 0.54 | 0.6 | 0.6 | 0.58 | 0.66 |
| numerical_comparison | 10 | 0.5 | 1.0 | 0.9 | 0.9 | 0.9 | 0.9 |
| revision_conflict | 19 | 0.1579 | 0.3684 | 0.2632 | 0.3684 | 0.2632 | 0.2632 |

## Worked example (no passage text)

```json
[
  {
    "case_id": "DEV-004",
    "selection": "first input case with top10 relevance for all four and differing ranks",
    "configs": {
      "merge120": {
        "rank": 4,
        "chunk_id": "3f5cf8a4118d03f7",
        "score": 7.2955,
        "relevant": 1,
        "words": 106,
        "source_id": "mom-2026-q2-final",
        "locator": "p.6"
      },
      "merge200": {
        "rank": 2,
        "chunk_id": "ccd1331952a1dd77",
        "score": 7.3974,
        "relevant": 1,
        "words": 106,
        "source_id": "mom-2026-q2-final",
        "locator": "p.6"
      },
      "merge300": {
        "rank": 2,
        "chunk_id": "0c6e5ad352ea92ea",
        "score": 7.6985,
        "relevant": 1,
        "words": 323,
        "source_id": "mom-2026-q2-final-release",
        "locator": "section: Main Findings, item 1 to section: Main Findings, item 4"
      },
      "merge400": {
        "rank": 2,
        "chunk_id": "e041d64e80197bcd",
        "score": 7.84,
        "relevant": 1,
        "words": 323,
        "source_id": "mom-2026-q2-final-release",
        "locator": "section: Main Findings, item 1 to section: Main Findings, item 4"
      }
    }
  }
]
```

## Provenance and cost estimates

Full provenance: `dev-E1b-chunk-size/provenance.json`; per-config metrics include identities, deterministic rebuild, easier-target counts, token/cost estimates and both paired comparisons. Cost assumptions: 1.33 tokens/word; cached specs/prices.yaml, not live-verified. Fresh embedding estimate includes all chunk words (including overlap); no cache reuse assumed. R3 scenario uses 30 corpus-average chunks × n cases and gpt-6-luna input price; excludes metadata, prompt, query embeddings, output/reasoning and generation, so is not an all-in forecast. No paid calls ran.

