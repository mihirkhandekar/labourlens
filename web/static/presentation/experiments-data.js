// Rights-safe projections of cited immutable artifacts; integrity checked in tests/web/test_deck_experiments.py.
export default {
  "definitions": "Hit@k: share of questions with at least one labelled passage in the first k chunks. MRR: average reciprocal rank of the first matching chunk (zero when absent from the saved cutoff; MRR@10 uses ten). Passage recall: share of labelled passages covered. Context words: average words in the first five chunks. Page hit is a lenient same-page match, not a passage match. Chunk hit@8 checks all passages in eight chunks; strict distinct-passage hit@8 instead builds the real answer context and checks only its first eight passages, after source/snapshot/text deduplication. A chunk can hold several passages, so the two cutoffs are not interchangeable. Better/worse compares the same cases, not independent samples. MEASURED denotes saved results; interpretations are INFERENCE, not proof.",
  "experiments": [
    {
      "title": "E1 · BM25 chunking",
      "question": "Does grouping adjacent passages improve retrieval?",
      "changed": "blocks; merge120 (120 words/30 overlap); merge200 (200/40); fixed150; merge120+tables. Merge overlap uses whole passages under one heading.",
      "fixed": "BM25 k1=1.5, b=0.75; stopwords on, stemming off, quarter normalisation on; merge120 unless changed. Same cases and corpus within each comparison.",
      "measurement": "24 development text-evidence cases; 46 documents. AI-drafted labels at scoring time; later owner sign-off is not an independent review or a rescore. Tables use the 46-document dev-SUMMARY, not the different numbers in the early 16-document m2-bm25-baseline.md write-up.",
      "tables": [
        {
          "source": "experiments/runs/dev-SUMMARY.md",
          "tableIndex": 0,
          "section": null,
          "columns": [
            "config",
            "hit@1",
            "hit@3",
            "hit@5",
            "hit@10",
            "page_hit@5 (lenient)",
            "MRR",
            "passage_recall@5",
            "ctx words@5",
            "chunks",
            "p50 ms",
            "vs baseline (rank of first relevant)"
          ],
          "rows": [
            [
              "blocks",
              "0.125",
              "0.1667",
              "0.3333",
              "0.4167",
              "0.375",
              "0.1939",
              "0.2292",
              "169.1",
              "6360",
              "0.218",
              "1 better / 10 worse / 13 same"
            ],
            [
              "merge120",
              "0.2083",
              "0.4167",
              "0.4167",
              "0.5833",
              "0.4583",
              "0.3131",
              "0.2917",
              "456.3",
              "2468",
              "0.183",
              "0 better / 0 worse / 24 same"
            ],
            [
              "merge200",
              "0.25",
              "0.4583",
              "0.5417",
              "0.625",
              "0.5833",
              "0.3627",
              "0.375",
              "633.0",
              "2106",
              "0.183",
              "5 better / 1 worse / 18 same"
            ],
            [
              "fixed150",
              "0.2083",
              "0.4167",
              "0.5",
              "0.625",
              "0.5",
              "0.3362",
              "0.3403",
              "742.5",
              "1514",
              "0.164",
              "6 better / 6 worse / 12 same"
            ],
            [
              "merge120+tables",
              "0.2083",
              "0.4167",
              "0.4167",
              "0.5833",
              "0.4583",
              "0.3131",
              "0.2917",
              "479.6",
              "3379",
              "0.185",
              "2 better / 2 worse / 20 same"
            ]
          ]
        }
      ],
      "examples": [
        {
          "source": "experiments/runs/dev-E1-chunking/blocks.cases.jsonl",
          "label": "blocks.cases",
          "case_id": "DEV-001",
          "first_relevant_rank": 1,
          "ranked": [
            {
              "chunk_id": "9cd803de5a517b89",
              "score": 10.9853,
              "relevant": 1,
              "words": 22,
              "source_id": "mom-2026-q2-final",
              "locator": "p.6"
            },
            {
              "chunk_id": "68c1bdeba6d93168",
              "score": 8.9684,
              "relevant": 1,
              "words": 94,
              "source_id": "mom-2026-q2-final-release",
              "locator": "section: Labour Market Report - Second Quarter 2026, item 4"
            },
            {
              "chunk_id": "912e66f13fadec71",
              "score": 6.9258,
              "relevant": 0,
              "words": 40,
              "source_id": "mom-2026-q2-final",
              "locator": "p.24"
            }
          ]
        },
        {
          "source": "experiments/runs/dev-E1-chunking/fixed150.cases.jsonl",
          "label": "fixed150.cases",
          "case_id": "DEV-001",
          "first_relevant_rank": 1,
          "ranked": [
            {
              "chunk_id": "6ded2f8c5ac466a8",
              "score": 9.6092,
              "relevant": 1,
              "words": 150,
              "source_id": "mom-2026-q2-final",
              "locator": "pp.6-7"
            },
            {
              "chunk_id": "4670e2c960cc952f",
              "score": 9.3768,
              "relevant": 1,
              "words": 150,
              "source_id": "mom-2026-q2-final-release",
              "locator": "section: Labour Market Report - Second Quarter 2026, item 2 to section: Labour Market Report - Second Quarter 2026, item 4"
            },
            {
              "chunk_id": "67e600562e0619fe",
              "score": 9.1688,
              "relevant": 1,
              "words": 150,
              "source_id": "mom-2026-q2-final-release",
              "locator": "section: Labour Market Report - Second Quarter 2026, item 4 to section: Labour Market Report - Second Quarter 2026, item 5"
            }
          ]
        }
      ],
      "exampleNote": "Read the saved first-relevant rank against the three candidates below. Relevant means that the chunk contains a labelled gold passage; an absent top-three match is not necessarily a top-ten miss.",
      "takeaway": "On the original 24-case run merge200 led merge120; the later 128-case E1b comparison ties them on hit@8, so the early result is not a robust chunk-size win.",
      "limit": "An optimal size above 200, independent test performance or answer quality.",
      "id": "e1",
      "group": "retrieval"
    },
    {
      "title": "E1b · Larger chunk sizes",
      "question": "Do 300- or 400-word targets improve over merge120 and merge200?",
      "changed": "merge120/30 overlap; merge200/40; merge300/60; merge400/80, with blocks and fixed150 controls.",
      "fixed": "BM25 k1=1.5, b=.75; stopwords on; no stemming; quarter normalisation on. Same frozen v3.1 documents, gold and evaluator; no dense retrieval, rerank or paid calls.",
      "measurement": "Primary: 128 current development text cases, corpus v3.1 (49 documents). Secondary: 23 currently eligible cases from the original 24 ids; DEV-034 now abstains without text gold and is excluded, not counted as a miss. Paired hit@8 intervals: 10,000 case-bootstrap samples, seed 20261110. Better/worse/same columns compare first relevant rank, not binary hit.",
      "tables": [
        {
          "source": "experiments/runs/dev-E1b-chunk-size-SUMMARY.md",
          "tableIndex": 0,
          "section": null,
          "columns": [
            "config",
            "chunks",
            "mean words",
            "hit@1",
            "@3",
            "@5",
            "@8",
            "@10",
            "MRR",
            "passage recall@5",
            "ctx words@5",
            "vs merge200 B/W/S",
            "vs merge120 B/W/S",
            "hit@8 delta vs 200 [95% CI]"
          ],
          "rows": [
            [
              "blocks",
              "9052",
              "25.09",
              "0.0781",
              "0.1562",
              "0.2188",
              "0.2812",
              "0.3203",
              "0.1389",
              "0.196",
              "126.6",
              "8/53/67",
              "7/52/69",
              "-0.1953 [-0.2734, -0.1172]"
            ],
            [
              "merge120",
              "2494",
              "96.39",
              "0.1797",
              "0.3281",
              "0.4062",
              "0.4766",
              "0.5156",
              "0.2753",
              "0.3626",
              "573.7",
              "31/24/73",
              "0/0/128",
              "0.0 [-0.0625, 0.0625]"
            ],
            [
              "merge200",
              "1847",
              "127.89",
              "0.1406",
              "0.3359",
              "0.4062",
              "0.4766",
              "0.5391",
              "0.2589",
              "0.3496",
              "832.1",
              "0/0/128",
              "24/31/73",
              "0.0 [0.0, 0.0]"
            ],
            [
              "fixed150",
              "1900",
              "148.74",
              "0.1719",
              "0.3359",
              "0.4141",
              "0.4922",
              "0.5156",
              "0.2729",
              "0.3639",
              "732.4",
              "26/30/72",
              "22/30/76",
              "0.0156 [-0.0391, 0.0703]"
            ],
            [
              "merge300",
              "1598",
              "147.41",
              "0.1406",
              "0.3438",
              "0.4062",
              "0.4688",
              "0.5",
              "0.2584",
              "0.3483",
              "1058.7",
              "23/19/86",
              "26/29/73",
              "-0.0078 [-0.0469, 0.0312]"
            ],
            [
              "merge400",
              "1494",
              "157.15",
              "0.1641",
              "0.3359",
              "0.4297",
              "0.5",
              "0.5312",
              "0.2733",
              "0.3553",
              "1246.7",
              "28/21/79",
              "28/27/73",
              "0.0234 [-0.0234, 0.0703]"
            ]
          ]
        },
        {
          "source": "experiments/runs/dev-E1b-chunk-size-SUMMARY.md",
          "tableIndex": 1,
          "section": null,
          "columns": [
            "config",
            "chunks",
            "mean words",
            "hit@1",
            "@3",
            "@5",
            "@8",
            "@10",
            "MRR",
            "passage recall@5",
            "ctx words@5",
            "vs merge200 B/W/S",
            "vs merge120 B/W/S",
            "hit@8 delta vs 200 [95% CI]"
          ],
          "rows": [
            [
              "blocks",
              "9052",
              "25.09",
              "0.0435",
              "0.1739",
              "0.2609",
              "0.3043",
              "0.3478",
              "0.1393",
              "0.1884",
              "125.2",
              "0/9/14",
              "0/9/14",
              "-0.2174 [-0.3913, -0.087]"
            ],
            [
              "merge120",
              "2494",
              "96.39",
              "0.1304",
              "0.3913",
              "0.4348",
              "0.4783",
              "0.4783",
              "0.2678",
              "0.3333",
              "578.1",
              "2/4/17",
              "0/0/23",
              "-0.0435 [-0.1304, 0.0]"
            ],
            [
              "merge200",
              "1847",
              "127.89",
              "0.1739",
              "0.3913",
              "0.4783",
              "0.5217",
              "0.5217",
              "0.3094",
              "0.3406",
              "833.3",
              "0/0/23",
              "4/2/17",
              "0.0 [0.0, 0.0]"
            ],
            [
              "fixed150",
              "1900",
              "148.74",
              "0.1739",
              "0.3478",
              "0.3913",
              "0.4783",
              "0.5217",
              "0.2828",
              "0.3043",
              "730.6",
              "3/6/14",
              "4/5/14",
              "-0.0435 [-0.1304, 0.0]"
            ],
            [
              "merge300",
              "1598",
              "147.41",
              "0.1739",
              "0.3913",
              "0.4783",
              "0.5217",
              "0.5217",
              "0.2928",
              "0.3333",
              "1072.9",
              "3/4/16",
              "5/3/15",
              "0.0 [0.0, 0.0]"
            ],
            [
              "merge400",
              "1494",
              "157.15",
              "0.2174",
              "0.4348",
              "0.5652",
              "0.5652",
              "0.5652",
              "0.3471",
              "0.3576",
              "1268.2",
              "5/2/16",
              "7/2/14",
              "0.0435 [0.0, 0.1304]"
            ]
          ]
        },
        {
          "source": "experiments/runs/dev-E1b-chunk-size-SUMMARY.md",
          "tableIndex": 2,
          "section": null,
          "columns": [
            "family",
            "n",
            "blocks",
            "merge120",
            "merge200",
            "fixed150",
            "merge300",
            "merge400"
          ],
          "rows": [
            [
              "adversarial",
              "13",
              "0.1538",
              "0.3846",
              "0.4615",
              "0.3846",
              "0.4615",
              "0.4615"
            ],
            [
              "ambiguity_insufficient_causal",
              "2",
              "0.0",
              "0.5",
              "0.0",
              "0.0",
              "0.0",
              "0.0"
            ],
            [
              "cross_source_synthesis",
              "34",
              "0.1765",
              "0.3235",
              "0.3235",
              "0.3529",
              "0.3235",
              "0.3235"
            ],
            [
              "factual_lookup",
              "50",
              "0.4",
              "0.54",
              "0.6",
              "0.6",
              "0.58",
              "0.66"
            ],
            [
              "numerical_comparison",
              "10",
              "0.5",
              "1.0",
              "0.9",
              "0.9",
              "0.9",
              "0.9"
            ],
            [
              "revision_conflict",
              "19",
              "0.1579",
              "0.3684",
              "0.2632",
              "0.3684",
              "0.2632",
              "0.2632"
            ]
          ]
        }
      ],
      "examples": [
        {
          "source": "experiments/runs/dev-E1b-chunk-size/merge200.cases.jsonl",
          "label": "merge200.cases",
          "case_id": "DEV-004",
          "first_relevant_rank": 2,
          "ranked": [
            {
              "chunk_id": "7d9069d9a4c2e90c",
              "score": 7.9315,
              "relevant": 0,
              "words": 205,
              "source_id": "mom-2026-q2-final",
              "locator": "p.22"
            },
            {
              "chunk_id": "ccd1331952a1dd77",
              "score": 7.3974,
              "relevant": 1,
              "words": 106,
              "source_id": "mom-2026-q2-final",
              "locator": "p.6"
            },
            {
              "chunk_id": "3898789c5a30f4be",
              "score": 7.2118,
              "relevant": 0,
              "words": 191,
              "source_id": "mom-2026-q2-final",
              "locator": "pp.21-22"
            }
          ]
        },
        {
          "source": "experiments/runs/dev-E1b-chunk-size/merge400.cases.jsonl",
          "label": "merge400.cases",
          "case_id": "DEV-004",
          "first_relevant_rank": 2,
          "ranked": [
            {
              "chunk_id": "6d32131c06010fe1",
              "score": 8.596,
              "relevant": 0,
              "words": 411,
              "source_id": "mom-2026-q2-final",
              "locator": "pp.22-23"
            },
            {
              "chunk_id": "e041d64e80197bcd",
              "score": 7.84,
              "relevant": 1,
              "words": 323,
              "source_id": "mom-2026-q2-final-release",
              "locator": "section: Main Findings, item 1 to section: Main Findings, item 4"
            },
            {
              "chunk_id": "cd969a40acea313e",
              "score": 7.5905,
              "relevant": 0,
              "words": 401,
              "source_id": "mom-2026-q1-final",
              "locator": "pp.22-23"
            }
          ]
        }
      ],
      "exampleNote": "DEV-004 first relevant ranks are merge120 4, merge200 2, merge300 2 and merge400 2. The larger matching chunks contain more words, not a better first-match rank.",
      "takeaway": "There is no convincing gain above 200; merge400 uses about 50% more context words.",
      "limit": "An R3 or answer-quality gain, optimal chunk size, or a controlled comparison with the historical 24-case scores. Larger chunks can make the target easier to hit. Protocol and interpretation: docs/experiments/chunk-size-300-400.md.",
      "id": "e1b",
      "group": "retrieval"
    },
    {
      "title": "E2 · Tokenising",
      "question": "Which token processing helps lexical matching?",
      "changed": "Stemming on; stopwords off; period normalisation off, each against the baseline.",
      "fixed": "BM25 k1=1.5, b=0.75; stopwords on, stemming off, quarter normalisation on; merge120 unless changed. Same cases and corpus within each comparison.",
      "measurement": "24 development text-evidence cases; 46 documents. AI-drafted labels at scoring time; later owner sign-off is not an independent review or a rescore. Tables use the 46-document dev-SUMMARY, not the different numbers in the early 16-document m2-bm25-baseline.md write-up.",
      "tables": [
        {
          "source": "experiments/runs/dev-SUMMARY.md",
          "tableIndex": 1,
          "section": null,
          "columns": [
            "config",
            "hit@1",
            "hit@3",
            "hit@5",
            "hit@10",
            "page_hit@5 (lenient)",
            "MRR",
            "passage_recall@5",
            "ctx words@5",
            "chunks",
            "p50 ms",
            "vs baseline (rank of first relevant)"
          ],
          "rows": [
            [
              "baseline",
              "0.2083",
              "0.4167",
              "0.4167",
              "0.5833",
              "0.4583",
              "0.3131",
              "0.2917",
              "456.3",
              "2468",
              "0.183",
              "0 better / 0 worse / 24 same"
            ],
            [
              "stem_on",
              "0.2917",
              "0.3333",
              "0.375",
              "0.5417",
              "0.4167",
              "0.3439",
              "0.2986",
              "475.5",
              "2468",
              "0.193",
              "3 better / 4 worse / 17 same"
            ],
            [
              "stopwords_off",
              "0.25",
              "0.375",
              "0.4583",
              "0.625",
              "0.5",
              "0.347",
              "0.3333",
              "481.9",
              "2468",
              "0.212",
              "5 better / 1 worse / 18 same"
            ],
            [
              "period_norm_off",
              "0.1667",
              "0.4167",
              "0.4167",
              "0.625",
              "0.4583",
              "0.2895",
              "0.2917",
              "454.8",
              "2468",
              "0.163",
              "2 better / 2 worse / 20 same"
            ]
          ]
        }
      ],
      "examples": [
        {
          "source": "experiments/runs/dev-E2-tokenisation/baseline.cases.jsonl",
          "label": "baseline.cases",
          "case_id": "DEV-001",
          "first_relevant_rank": 1,
          "ranked": [
            {
              "chunk_id": "696c57219d676cc0",
              "score": 10.2118,
              "relevant": 1,
              "words": 94,
              "source_id": "mom-2026-q2-final-release",
              "locator": "section: Labour Market Report - Second Quarter 2026, item 4"
            },
            {
              "chunk_id": "527a2a735dc40034",
              "score": 10.1441,
              "relevant": 1,
              "words": 40,
              "source_id": "mom-2026-q2-final",
              "locator": "p.6"
            },
            {
              "chunk_id": "b23f9c2b34bf62ea",
              "score": 6.8316,
              "relevant": 0,
              "words": 64,
              "source_id": "mom-2026-q2-final",
              "locator": "p.24"
            }
          ]
        },
        {
          "source": "experiments/runs/dev-E2-tokenisation/period_norm_off.cases.jsonl",
          "label": "period_norm_off.cases",
          "case_id": "DEV-001",
          "first_relevant_rank": 1,
          "ranked": [
            {
              "chunk_id": "696c57219d676cc0",
              "score": 10.4474,
              "relevant": 1,
              "words": 94,
              "source_id": "mom-2026-q2-final-release",
              "locator": "section: Labour Market Report - Second Quarter 2026, item 4"
            },
            {
              "chunk_id": "527a2a735dc40034",
              "score": 10.1511,
              "relevant": 1,
              "words": 40,
              "source_id": "mom-2026-q2-final",
              "locator": "p.6"
            },
            {
              "chunk_id": "b23f9c2b34bf62ea",
              "score": 6.8352,
              "relevant": 0,
              "words": 64,
              "source_id": "mom-2026-q2-final",
              "locator": "p.24"
            }
          ]
        }
      ],
      "exampleNote": "Read the saved first-relevant rank against the three candidates below. Relevant means that the chunk contains a labelled gold passage; an absent top-three match is not necessarily a top-ten miss.",
      "takeaway": "The metrics disagree; there is no clear universal tokenising winner.",
      "limit": "A robust gain from stemming, or an independently validated setting.",
      "id": "e2",
      "group": "retrieval"
    },
    {
      "title": "E3 · BM25 parameters",
      "question": "Does term saturation or length normalisation improve ranking?",
      "changed": "k1 = 0.9, 1.2, 1.5, 2.0 with b=.75; b=.4, .75, .9 with k1=1.5.",
      "fixed": "BM25 k1=1.5, b=0.75; stopwords on, stemming off, quarter normalisation on; merge120 unless changed. Same cases and corpus within each comparison.",
      "measurement": "24 development text-evidence cases; 46 documents. AI-drafted labels at scoring time; later owner sign-off is not an independent review or a rescore. Tables use the 46-document dev-SUMMARY, not the different numbers in the early 16-document m2-bm25-baseline.md write-up.",
      "tables": [
        {
          "source": "experiments/runs/dev-SUMMARY.md",
          "tableIndex": 3,
          "section": null,
          "columns": [
            "config",
            "hit@1",
            "hit@3",
            "hit@5",
            "hit@10",
            "page_hit@5 (lenient)",
            "MRR",
            "passage_recall@5",
            "ctx words@5",
            "chunks",
            "p50 ms",
            "vs baseline (rank of first relevant)"
          ],
          "rows": [
            [
              "k1=0.9",
              "0.2083",
              "0.375",
              "0.4167",
              "0.5",
              "0.4583",
              "0.3067",
              "0.2917",
              "482.0",
              "2468",
              "0.172",
              "1 better / 3 worse / 20 same"
            ],
            [
              "k1=1.2",
              "0.2083",
              "0.4167",
              "0.4167",
              "0.5833",
              "0.5",
              "0.3126",
              "0.2917",
              "468.6",
              "2468",
              "0.17",
              "0 better / 1 worse / 23 same"
            ],
            [
              "k1=1.5",
              "0.2083",
              "0.4167",
              "0.4167",
              "0.5833",
              "0.4583",
              "0.3131",
              "0.2917",
              "456.3",
              "2468",
              "0.183",
              "0 better / 0 worse / 24 same"
            ],
            [
              "k1=2.0",
              "0.2083",
              "0.4167",
              "0.4167",
              "0.5833",
              "0.4583",
              "0.3047",
              "0.2917",
              "434.7",
              "2468",
              "0.176",
              "1 better / 3 worse / 20 same"
            ],
            [
              "b=0.4",
              "0.2083",
              "0.3333",
              "0.4583",
              "0.5",
              "0.5",
              "0.2972",
              "0.3125",
              "578.7",
              "2468",
              "0.179",
              "2 better / 5 worse / 17 same"
            ],
            [
              "b=0.75",
              "0.2083",
              "0.4167",
              "0.4167",
              "0.5833",
              "0.4583",
              "0.3131",
              "0.2917",
              "456.3",
              "2468",
              "0.183",
              "0 better / 0 worse / 24 same"
            ],
            [
              "b=0.9",
              "0.1667",
              "0.4167",
              "0.4583",
              "0.5833",
              "0.5",
              "0.2963",
              "0.3333",
              "390.2",
              "2468",
              "0.188",
              "3 better / 2 worse / 19 same"
            ]
          ]
        }
      ],
      "examples": [
        {
          "source": "experiments/runs/dev-E3-bm25-params/b=0.4.cases.jsonl",
          "label": "b=0.4.cases",
          "case_id": "DEV-001",
          "first_relevant_rank": 1,
          "ranked": [
            {
              "chunk_id": "696c57219d676cc0",
              "score": 10.5561,
              "relevant": 1,
              "words": 94,
              "source_id": "mom-2026-q2-final-release",
              "locator": "section: Labour Market Report - Second Quarter 2026, item 4"
            },
            {
              "chunk_id": "527a2a735dc40034",
              "score": 9.5309,
              "relevant": 1,
              "words": 40,
              "source_id": "mom-2026-q2-final",
              "locator": "p.6"
            },
            {
              "chunk_id": "f04befa7516d5305",
              "score": 6.9895,
              "relevant": 0,
              "words": 127,
              "source_id": "mom-2024-q3-final-release",
              "locator": "section: Labour Market in 3Q 2024, item 15 to section: Labour Market in 3Q 2024, item 17"
            }
          ]
        },
        {
          "source": "experiments/runs/dev-E3-bm25-params/b=0.75.cases.jsonl",
          "label": "b=0.75.cases",
          "case_id": "DEV-001",
          "first_relevant_rank": 1,
          "ranked": [
            {
              "chunk_id": "696c57219d676cc0",
              "score": 10.2118,
              "relevant": 1,
              "words": 94,
              "source_id": "mom-2026-q2-final-release",
              "locator": "section: Labour Market Report - Second Quarter 2026, item 4"
            },
            {
              "chunk_id": "527a2a735dc40034",
              "score": 10.1441,
              "relevant": 1,
              "words": 40,
              "source_id": "mom-2026-q2-final",
              "locator": "p.6"
            },
            {
              "chunk_id": "b23f9c2b34bf62ea",
              "score": 6.8316,
              "relevant": 0,
              "words": 64,
              "source_id": "mom-2026-q2-final",
              "locator": "p.24"
            }
          ]
        }
      ],
      "exampleNote": "Read the saved first-relevant rank against the three candidates below. Relevant means that the chunk contains a labelled gold passage; an absent top-three match is not necessarily a top-ten miss.",
      "takeaway": "Parameter changes were small and mixed on these cases.",
      "limit": "A globally optimal k1 or b; this is not a full interaction grid.",
      "id": "e3",
      "group": "retrieval"
    },
    {
      "title": "E4 · Combined settings",
      "question": "Do promising BM25 changes work together?",
      "changed": "merge200 + stopwords off; also b=.4. Compared with merge120 baseline.",
      "fixed": "BM25 k1=1.5, b=0.75; stopwords on, stemming off, quarter normalisation on; merge120 unless changed. Same cases and corpus within each comparison.",
      "measurement": "24 development text-evidence cases; 46 documents. AI-drafted labels at scoring time; later owner sign-off is not an independent review or a rescore. Tables use the 46-document dev-SUMMARY, not the different numbers in the early 16-document m2-bm25-baseline.md write-up.",
      "tables": [
        {
          "source": "experiments/runs/dev-SUMMARY.md",
          "tableIndex": 2,
          "section": null,
          "columns": [
            "config",
            "hit@1",
            "hit@3",
            "hit@5",
            "hit@10",
            "page_hit@5 (lenient)",
            "MRR",
            "passage_recall@5",
            "ctx words@5",
            "chunks",
            "p50 ms",
            "vs baseline (rank of first relevant)"
          ],
          "rows": [
            [
              "merge200+stopwords_off",
              "0.25",
              "0.5",
              "0.5417",
              "0.6667",
              "0.5833",
              "0.3781",
              "0.3611",
              "684.5",
              "2106",
              "0.197",
              "7 better / 3 worse / 14 same"
            ],
            [
              "merge200+stopwords_off+b=0.4",
              "0.3333",
              "0.5",
              "0.5",
              "0.7083",
              "0.5417",
              "0.4222",
              "0.3542",
              "899.1",
              "2106",
              "0.202",
              "7 better / 3 worse / 14 same"
            ]
          ]
        }
      ],
      "examples": [
        {
          "source": "experiments/runs/dev-E4-combined/merge200+stopwords_off+b=0.4.cases.jsonl",
          "label": "merge200+stopwords_off+b=0.4.cases",
          "case_id": "DEV-001",
          "first_relevant_rank": 1,
          "ranked": [
            {
              "chunk_id": "96865ef598482ec2",
              "score": 12.4017,
              "relevant": 1,
              "words": 210,
              "source_id": "mom-2026-q2-final-release",
              "locator": "section: Labour Market Report - Second Quarter 2026, item 4 to section: Labour Market Report - Second Quarter 2026, item 6"
            },
            {
              "chunk_id": "c66a4ad9f53fb0d2",
              "score": 11.6645,
              "relevant": 1,
              "words": 40,
              "source_id": "mom-2026-q2-final",
              "locator": "p.6"
            },
            {
              "chunk_id": "37a670da2f5dea3e",
              "score": 9.8554,
              "relevant": 0,
              "words": 225,
              "source_id": "mom-2024-q3-final-release",
              "locator": "section: Labour Market in 3Q 2024, item 9 to section: Labour Market in 3Q 2024, item 16"
            }
          ]
        },
        {
          "source": "experiments/runs/dev-E4-combined/merge200+stopwords_off.cases.jsonl",
          "label": "merge200+stopwords_off.cases",
          "case_id": "DEV-001",
          "first_relevant_rank": 1,
          "ranked": [
            {
              "chunk_id": "c66a4ad9f53fb0d2",
              "score": 12.8502,
              "relevant": 1,
              "words": 40,
              "source_id": "mom-2026-q2-final",
              "locator": "p.6"
            },
            {
              "chunk_id": "96865ef598482ec2",
              "score": 11.0844,
              "relevant": 1,
              "words": 210,
              "source_id": "mom-2026-q2-final-release",
              "locator": "section: Labour Market Report - Second Quarter 2026, item 4 to section: Labour Market Report - Second Quarter 2026, item 6"
            },
            {
              "chunk_id": "37a670da2f5dea3e",
              "score": 8.3748,
              "relevant": 0,
              "words": 225,
              "source_id": "mom-2024-q3-final-release",
              "locator": "section: Labour Market in 3Q 2024, item 9 to section: Labour Market in 3Q 2024, item 16"
            }
          ]
        }
      ],
      "exampleNote": "Read the saved first-relevant rank against the three candidates below. Relevant means that the chunk contains a labelled gold passage; an absent top-three match is not necessarily a top-ten miss.",
      "takeaway": "The combined setting raised MRR, but several factors changed together.",
      "limit": "Which individual factor caused the gain, or generalisation beyond the tuned cases.",
      "id": "e4",
      "group": "retrieval"
    },
    {
      "title": "E5 · Embedding models",
      "question": "Which embedding model retrieves useful evidence?",
      "changed": "text-embedding-3-small; text-embedding-3-large; text-embedding-ada-002; BM25 reference.",
      "fixed": "Dense cosine ranking; merge120; same corpus and questions.",
      "measurement": "24 development text-evidence cases; 46 documents. AI-drafted labels at scoring time; later owner sign-off is not an independent review or a rescore.",
      "tables": [
        {
          "source": "docs/experiments/m3-dense-hybrid.md",
          "tableIndex": 0,
          "section": null,
          "columns": [
            "config",
            "hit@1",
            "hit@5",
            "hit@10",
            "MRR",
            "passage_recall@5"
          ],
          "rows": [
            [
              "BM25 baseline",
              "0.21",
              "0.42",
              "0.58",
              "0.31",
              "0.29"
            ],
            [
              "text-embedding-3-small",
              "0.25",
              "0.63",
              "0.75",
              "0.43",
              "0.38"
            ],
            [
              "text-embedding-3-large",
              "0.46",
              "0.58",
              "0.67",
              "0.53",
              "0.33"
            ],
            [
              "text-embedding-ada-002",
              "0.42",
              "0.71",
              "0.88",
              "0.53",
              "0.41"
            ]
          ]
        }
      ],
      "examples": [
        {
          "source": "experiments/runs/dev-dense-E5/bm25_baseline.cases.jsonl",
          "label": "bm25_baseline.cases",
          "case_id": "DEV-001",
          "first_relevant_rank": 1,
          "ranked": [
            {
              "chunk_id": "696c57219d676cc0",
              "score": 10.2118,
              "relevant": 1,
              "words": 94,
              "source_id": "mom-2026-q2-final-release",
              "locator": "section: Labour Market Report - Second Quarter 2026, item 4"
            },
            {
              "chunk_id": "527a2a735dc40034",
              "score": 10.1441,
              "relevant": 1,
              "words": 40,
              "source_id": "mom-2026-q2-final",
              "locator": "p.6"
            },
            {
              "chunk_id": "b23f9c2b34bf62ea",
              "score": 6.8316,
              "relevant": 0,
              "words": 64,
              "source_id": "mom-2026-q2-final",
              "locator": "p.24"
            }
          ]
        },
        {
          "source": "experiments/runs/dev-dense-E5/text-embedding-3-large.cases.jsonl",
          "label": "text-embedding-3-large.cases",
          "case_id": "DEV-001",
          "first_relevant_rank": 1,
          "ranked": [
            {
              "chunk_id": "527a2a735dc40034",
              "score": 0.7101,
              "relevant": 1,
              "words": 40,
              "source_id": "mom-2026-q2-final",
              "locator": "p.6"
            },
            {
              "chunk_id": "127ba4cc973e76e7",
              "score": 0.7024,
              "relevant": 0,
              "words": 149,
              "source_id": "mom-2026-q2-final",
              "locator": "p.55"
            },
            {
              "chunk_id": "696c57219d676cc0",
              "score": 0.6861,
              "relevant": 1,
              "words": 94,
              "source_id": "mom-2026-q2-final-release",
              "locator": "section: Labour Market Report - Second Quarter 2026, item 4"
            }
          ]
        }
      ],
      "exampleNote": "Read the saved first-relevant rank against the three candidates below. Relevant means that the chunk contains a labelled gold passage; an absent top-three match is not necessarily a top-ten miss.",
      "takeaway": "Dense models improved over BM25; the model ordering is uncertain.",
      "limit": "That 3-large is best: its MRR lead over ada-002 was only .001.",
      "id": "e5",
      "group": "retrieval"
    },
    {
      "title": "E6 · Dense and hybrid",
      "question": "Does combining lexical and semantic rankings help?",
      "changed": "BM25, dense and hybrid for merge120 and merge200.",
      "fixed": "3-large embeddings; hybrid reciprocal rank fusion c=60 of top 50 from each list; same 24 cases.",
      "measurement": "24 development text-evidence cases; 46 documents. AI-drafted labels at scoring time; later owner sign-off is not an independent review or a rescore.",
      "tables": [
        {
          "source": "docs/experiments/m3-dense-hybrid.md",
          "tableIndex": 1,
          "section": null,
          "columns": [
            "config",
            "hit@5",
            "hit@10",
            "MRR",
            "passage_recall@5",
            "context words@5"
          ],
          "rows": [
            [
              "merge120 bm25",
              "0.42",
              "0.58",
              "0.31",
              "0.29",
              "456"
            ],
            [
              "merge120 dense",
              "0.58",
              "0.67",
              "0.53",
              "0.33",
              "376"
            ],
            [
              "merge120 hybrid",
              "0.67",
              "0.71",
              "0.52",
              "0.42",
              "412"
            ],
            [
              "merge200 bm25",
              "0.54",
              "0.63",
              "0.36",
              "0.38",
              "633"
            ],
            [
              "merge200 dense",
              "0.54",
              "0.67",
              "0.44",
              "0.29",
              "436"
            ],
            [
              "merge200 hybrid",
              "0.63",
              "0.79",
              "0.46",
              "0.42",
              "507"
            ]
          ]
        }
      ],
      "examples": [
        {
          "source": "experiments/runs/dev-dense-E6/merge120 bm25.cases.jsonl",
          "label": "merge120 bm25.cases",
          "case_id": "DEV-001",
          "first_relevant_rank": 1,
          "ranked": [
            {
              "chunk_id": "696c57219d676cc0",
              "score": 10.2118,
              "relevant": 1,
              "words": 94,
              "source_id": "mom-2026-q2-final-release",
              "locator": "section: Labour Market Report - Second Quarter 2026, item 4"
            },
            {
              "chunk_id": "527a2a735dc40034",
              "score": 10.1441,
              "relevant": 1,
              "words": 40,
              "source_id": "mom-2026-q2-final",
              "locator": "p.6"
            },
            {
              "chunk_id": "b23f9c2b34bf62ea",
              "score": 6.8316,
              "relevant": 0,
              "words": 64,
              "source_id": "mom-2026-q2-final",
              "locator": "p.24"
            }
          ]
        },
        {
          "source": "experiments/runs/dev-dense-E6/merge120 dense.cases.jsonl",
          "label": "merge120 dense.cases",
          "case_id": "DEV-001",
          "first_relevant_rank": 1,
          "ranked": [
            {
              "chunk_id": "527a2a735dc40034",
              "score": 0.7101,
              "relevant": 1,
              "words": 40,
              "source_id": "mom-2026-q2-final",
              "locator": "p.6"
            },
            {
              "chunk_id": "127ba4cc973e76e7",
              "score": 0.7024,
              "relevant": 0,
              "words": 149,
              "source_id": "mom-2026-q2-final",
              "locator": "p.55"
            },
            {
              "chunk_id": "696c57219d676cc0",
              "score": 0.6861,
              "relevant": 1,
              "words": 94,
              "source_id": "mom-2026-q2-final-release",
              "locator": "section: Labour Market Report - Second Quarter 2026, item 4"
            }
          ]
        }
      ],
      "exampleNote": "Read the saved first-relevant rank against the three candidates below. Relevant means that the chunk contains a labelled gold passage; an absent top-three match is not necessarily a top-ten miss.",
      "takeaway": "Hybrid improved deeper hit rates; dense sometimes ranked the first match earlier.",
      "limit": "An optimal fusion constant, fusion depth, or a held-out win.",
      "id": "e6",
      "group": "retrieval"
    },
    {
      "title": "E7 · Embedded headers",
      "question": "Do title and section headings help embeddings distinguish evidence?",
      "changed": "Header off versus document title and section heading prepended.",
      "fixed": "Dense 3-large; merge120; same cases and corpus.",
      "measurement": "24 development text-evidence cases; 46 documents. AI-drafted labels at scoring time; later owner sign-off is not an independent review or a rescore.",
      "tables": [
        {
          "source": "docs/experiments/m3-dense-hybrid.md",
          "prose": true,
          "columns": [
            "Header",
            "hit@10",
            "MRR"
          ],
          "rows": [
            [
              "off",
              "0.67",
              "0.53"
            ],
            [
              "on",
              "0.71",
              "0.50"
            ]
          ]
        }
      ],
      "examples": [
        {
          "source": "experiments/runs/dev-dense-E7/text-embedding-3-large+hdr.cases.jsonl",
          "label": "text-embedding-3-large+hdr.cases",
          "case_id": "DEV-001",
          "first_relevant_rank": 1,
          "ranked": [
            {
              "chunk_id": "527a2a735dc40034",
              "score": 0.7781,
              "relevant": 1,
              "words": 40,
              "source_id": "mom-2026-q2-final",
              "locator": "p.6"
            },
            {
              "chunk_id": "1ba848e95c3b7ab6",
              "score": 0.7606,
              "relevant": 0,
              "words": 26,
              "source_id": "mom-2026-q2-final",
              "locator": "p.7"
            },
            {
              "chunk_id": "cef65257b292a36f",
              "score": 0.7439,
              "relevant": 0,
              "words": 28,
              "source_id": "mom-2025-q2-final",
              "locator": "p.6"
            }
          ]
        },
        {
          "source": "experiments/runs/dev-dense-E7/text-embedding-3-large.cases.jsonl",
          "label": "text-embedding-3-large.cases",
          "case_id": "DEV-001",
          "first_relevant_rank": 1,
          "ranked": [
            {
              "chunk_id": "527a2a735dc40034",
              "score": 0.7101,
              "relevant": 1,
              "words": 40,
              "source_id": "mom-2026-q2-final",
              "locator": "p.6"
            },
            {
              "chunk_id": "127ba4cc973e76e7",
              "score": 0.7024,
              "relevant": 0,
              "words": 149,
              "source_id": "mom-2026-q2-final",
              "locator": "p.55"
            },
            {
              "chunk_id": "696c57219d676cc0",
              "score": 0.6861,
              "relevant": 1,
              "words": 94,
              "source_id": "mom-2026-q2-final-release",
              "locator": "section: Labour Market Report - Second Quarter 2026, item 4"
            }
          ]
        }
      ],
      "exampleNote": "Read the saved first-relevant rank against the three candidates below. Relevant means that the chunk contains a labelled gold passage; an absent top-three match is not necessarily a top-ten miss.",
      "takeaway": "Adding headers moved hit rate and MRR in opposite directions.",
      "limit": "A clear gain from headers; hit@10 differs by only one case.",
      "id": "e7",
      "group": "retrieval"
    },
    {
      "title": "R0 to R3 · Filter, boost and rerank",
      "question": "Is the problem candidate generation, ordering, or both?",
      "changed": "R0 hybrid; R1a hard period/release filter; R1b soft bonus .5/61 per matching hint; sensitivities .25/61 (R1b_x0.5) and 1/61 (R1b_x2); R2 gpt-6-luna listwise rerank top 30; R3 hard filter then rerank.",
      "fixed": "merge200; 3-large; top 50 per list; RRF c=60. R3 precondition: both individual components improve hit@8 by at least .05.",
      "measurement": "128 answerable development text cases, gold v3.2 scope correction. Historical 46-document corpus, 2,106 chunks; NOT corpus v3.1. The v3.2 label is a gold version. 2,000 case-bootstrap resamples, seed 0. Paired better/worse counts use hit@8, unlike the early rank-based comparisons.",
      "tables": [
        {
          "source": "docs/experiments/m6-retrieval-improvements.md",
          "tableIndex": 0,
          "section": "## Current results",
          "columns": [
            "config",
            "hit@3",
            "hit@5",
            "hit@8 [95% CI]",
            "hit@10",
            "MRR@10",
            "gold-passage coverage@8",
            "pool recall@30 / @50",
            "hit@8 diff vs R0 [95% CI]",
            "paired hit@8 better/worse",
            "added latency p50 ms",
            "cost $/query"
          ],
          "rows": [
            [
              "R0",
              "0.3984",
              "0.4922",
              "0.570 [0.492, 0.656]",
              "0.5859",
              "0.3244",
              "0.485",
              "0.7891 / 0.8594",
              "-",
              "-",
              "0.0",
              "0"
            ],
            [
              "R1a",
              "0.6406",
              "0.75",
              "0.844 [0.781, 0.906]",
              "0.8828",
              "0.5421",
              "0.7539",
              "0.9688 / 0.9844",
              "+0.273 [+0.195, +0.359]",
              "37 / 2",
              "0.67",
              "0"
            ],
            [
              "R1b",
              "0.5156",
              "0.5859",
              "0.719 [0.648, 0.797]",
              "0.75",
              "0.4567",
              "0.6302",
              "0.8828 / 0.9219",
              "+0.148 [+0.086, +0.211]",
              "19 / 0",
              "0.2",
              "0"
            ],
            [
              "R2",
              "0.7891",
              "0.7891",
              "0.789 [0.726, 0.859]",
              "0.7891",
              "0.7643",
              "0.7333",
              "0.7891 / 0.8594",
              "+0.219 [+0.148, +0.289]",
              "28 / 0",
              "3826.28",
              "0.000876"
            ],
            [
              "R3",
              "0.9609",
              "0.9688",
              "0.969 [0.938, 0.992]",
              "0.9688",
              "0.9121",
              "0.9182",
              "0.9688 / 0.9844",
              "+0.398 [+0.312, +0.484]",
              "52 / 1",
              "3193.23",
              "0.00075"
            ],
            [
              "R1b_x0.5",
              "0.5",
              "0.5469",
              "0.656 [0.578, 0.734]",
              "0.6953",
              "0.4162",
              "0.5677",
              "0.875 / 0.9141",
              "+0.086 [+0.039, +0.133]",
              "11 / 0",
              "0.21",
              "0"
            ],
            [
              "R1b_x2",
              "0.5781",
              "0.6953",
              "0.797 [0.734, 0.867]",
              "0.8125",
              "0.4983",
              "0.707",
              "0.8906 / 0.9219",
              "+0.227 [+0.148, +0.305]",
              "30 / 1",
              "0.22",
              "0"
            ]
          ]
        },
        {
          "source": "docs/experiments/m6-retrieval-improvements.md",
          "tableIndex": 1,
          "section": "## Current results",
          "columns": [
            "config",
            "adversarial",
            "ambiguity_insufficient_causal",
            "cross_source_synthesis",
            "factual_lookup",
            "numerical_comparison",
            "revision_conflict"
          ],
          "rows": [
            [
              "R0",
              "0.462 (n=13)",
              "0.0 (n=2)",
              "0.5 (n=34)",
              "0.72 (n=50)",
              "0.8 (n=10)",
              "0.316 (n=19)"
            ],
            [
              "R1a",
              "0.923 (n=13)",
              "1.0 (n=2)",
              "0.824 (n=34)",
              "0.9 (n=50)",
              "0.8 (n=10)",
              "0.684 (n=19)"
            ],
            [
              "R1b",
              "0.692 (n=13)",
              "0.0 (n=2)",
              "0.706 (n=34)",
              "0.84 (n=50)",
              "0.9 (n=10)",
              "0.421 (n=19)"
            ],
            [
              "R2",
              "0.692 (n=13)",
              "1.0 (n=2)",
              "0.676 (n=34)",
              "0.92 (n=50)",
              "0.9 (n=10)",
              "0.632 (n=19)"
            ],
            [
              "R3",
              "1.0 (n=13)",
              "1.0 (n=2)",
              "0.912 (n=34)",
              "1.0 (n=50)",
              "0.9 (n=10)",
              "1.0 (n=19)"
            ],
            [
              "R1b_x0.5",
              "0.538 (n=13)",
              "0.0 (n=2)",
              "0.618 (n=34)",
              "0.78 (n=50)",
              "0.9 (n=10)",
              "0.421 (n=19)"
            ],
            [
              "R1b_x2",
              "0.769 (n=13)",
              "0.5 (n=2)",
              "0.765 (n=34)",
              "0.92 (n=50)",
              "0.8 (n=10)",
              "0.579 (n=19)"
            ]
          ]
        },
        {
          "source": "docs/experiments/m6-retrieval-improvements.md",
          "tableIndex": 2,
          "section": "## Current results",
          "columns": [
            "config",
            "has_hint",
            "no_hint"
          ],
          "rows": [
            [
              "R0",
              "0.458 (n=96)",
              "0.906 (n=32)"
            ],
            [
              "R1a",
              "0.823 (n=96)",
              "0.906 (n=32)"
            ],
            [
              "R1b",
              "0.656 (n=96)",
              "0.906 (n=32)"
            ],
            [
              "R2",
              "0.729 (n=96)",
              "0.969 (n=32)"
            ],
            [
              "R3",
              "0.969 (n=96)",
              "0.969 (n=32)"
            ],
            [
              "R1b_x0.5",
              "0.573 (n=96)",
              "0.906 (n=32)"
            ],
            [
              "R1b_x2",
              "0.76 (n=96)",
              "0.906 (n=32)"
            ]
          ]
        }
      ],
      "examples": [
        {
          "source": "experiments/runs/dev-R0/scores.jsonl",
          "label": "scores",
          "case_id": "DEV-006",
          "first_relevant_rank": 3,
          "ranked": [
            {
              "chunk_id": "c66a4ad9f53fb0d2",
              "relevant": 0
            },
            {
              "chunk_id": "7e8c1994495544f5",
              "relevant": 0
            },
            {
              "chunk_id": "96865ef598482ec2",
              "relevant": 1
            }
          ]
        },
        {
          "source": "experiments/runs/dev-R3/scores.jsonl",
          "label": "scores",
          "case_id": "DEV-006",
          "first_relevant_rank": null,
          "ranked": [
            {
              "chunk_id": "d6a6958443413bee",
              "relevant": 0
            },
            {
              "chunk_id": "4137601b5c600a19",
              "relevant": 0
            },
            {
              "chunk_id": "7e568bb5969b1c3a",
              "relevant": 0
            }
          ]
        }
      ],
      "exampleNote": "DEV-006 is the documented hard-filter loss: the question names an earlier quarter, but the labelled evidence lives in a later report. Compare the saved ranks rather than quoting report text.",
      "takeaway": "Filtering improved the candidate pool; reranking improved order, at added model latency.",
      "limit": "Answer accuracy, independent human relevance judgements, or a general family-level effect in tiny strata. DEV-006 exposes the hard-filter blind spot: evidence can sit in a later report.",
      "id": "r-series",
      "group": "retrieval"
    },
    {
      "title": "v3.1 · Same-build methods rerun",
      "question": "Does hybrid still help when the methods share the later evaluation build?",
      "changed": "BM25, dense, hybrid; no filters or reranking.",
      "fixed": "merge200; 3-large; depth 50; RRF c=60.",
      "measurement": "128 development text cases, corpus v3.1: 49 documents, 1,847 chunks. Gold and code recorded in the artifact. Protocol: docs/experiments/retrieval-v31-rerun.md.",
      "tables": [
        {
          "source": "experiments/runs/dev-R-V31-methods/metrics.json",
          "jsonMetrics": true,
          "columns": [
            "Method",
            "n",
            "hit@8",
            "95% interval",
            "hit@10",
            "MRR@10"
          ],
          "rows": [
            [
              "bm25",
              128,
              0.4766,
              "[0.3906, 0.5625]",
              0.5312,
              0.258
            ],
            [
              "dense",
              128,
              0.3672,
              "[0.2891, 0.4531]",
              0.3984,
              0.2234
            ],
            [
              "hybrid",
              128,
              0.5391,
              "[0.4531, 0.625]",
              0.5547,
              0.3116
            ]
          ]
        },
        {
          "title": "Later R-series, corpus v3.1 (not the historical gold-v3.2 table)",
          "source": "experiments/runs/dev-R-V31/summary.json",
          "v31Series": true,
          "columns": [
            "Config",
            "hit@8",
            "95% interval",
            "Paired better/worse vs R0"
          ],
          "rows": [
            [
              "R0",
              0.5391,
              "[0.4531, 0.625]",
              "baseline"
            ],
            [
              "R1a",
              0.8516,
              "[0.7891, 0.9141]",
              "[41, 1]"
            ],
            [
              "R1b",
              0.6641,
              "[0.5859, 0.7424]",
              "[16, 0]"
            ],
            [
              "R2",
              0.7422,
              "[0.6641, 0.8127]",
              "[26, 0]"
            ],
            [
              "R3",
              0.9688,
              "[0.9375, 0.9922]",
              "[56, 1]"
            ],
            [
              "R1b_x0.5",
              0.5859,
              "[0.5078, 0.6719]",
              "[6, 0]"
            ],
            [
              "R1b_x2",
              0.8047,
              "[0.7344, 0.875]",
              "[34, 0]"
            ]
          ]
        }
      ],
      "examples": [
        {
          "source": "experiments/runs/dev-R-V31-R0/scores.jsonl",
          "label": "scores",
          "case_id": "DEV-001",
          "first_relevant_rank": 1,
          "ranked": [
            {
              "chunk_id": "7b6e8f4832f18a55",
              "relevant": 1
            },
            {
              "chunk_id": "66465afd86181926",
              "relevant": 1
            },
            {
              "chunk_id": "1edb739887c2252a",
              "relevant": 0
            }
          ]
        }
      ],
      "exampleNote": "Read the saved first-relevant rank against the three candidates below. Relevant means that the chunk contains a labelled gold passage; an absent top-three match is not necessarily a top-ten miss.",
      "takeaway": "On v3.1, hit@8 was BM25 .477, dense .367 and hybrid .539.",
      "limit": "A causal comparison with the early 24-case study: corpus, gold, code and cutoff changed.",
      "id": "v31",
      "group": "retrieval"
    },
    {
      "title": "Held-out · Original 31 and fresh 65",
      "question": "Does the selected retrieval design find labelled evidence on held-out questions?",
      "changed": "BM25, dense, hybrid, hard filter, soft boost and sensitivities, rerank-only and filter-then-rerank.",
      "fixed": "Frozen corpus v3.1; merge200; 3-large; depth 50; RRF c=60; existing hints and rerank prompt.",
      "measurement": "18 eligible text cases of original 31, and 34 of fresh 65; other cases excluded by the predeclared eligibility rule. 2,000 percentile case-bootstrap resamples, seed 0. Literal gold questions, not planner rewrites. Protocol: docs/experiments/heldout-retrieval-metrics.md.",
      "tables": [
        {
          "source": "experiments/eval/heldout-retrieval-20261103-paid/metrics.json",
          "jsonHeldout": "registered31",
          "title": "registered31",
          "columns": [
            "Method",
            "Eligible n",
            "Chunk hit@8 [95% CI]",
            "Strict passage hit@8 [95% CI]",
            "Chunk MRR@10 [95% CI]"
          ],
          "rows": [
            [
              "bm25",
              18,
              "0.388889 [0.166667, 0.611111]",
              "0.166667 [0.0, 0.388889]",
              "0.230556 [0.077778, 0.427778]"
            ],
            [
              "dense",
              18,
              "0.277778 [0.111111, 0.5]",
              "0.111111 [0.0, 0.277778]",
              "0.149691 [0.046296, 0.283951]"
            ],
            [
              "hybrid",
              18,
              "0.444444 [0.222222, 0.666667]",
              "0.166667 [0.0, 0.333333]",
              "0.265961 [0.117196, 0.448078]"
            ],
            [
              "R1a",
              18,
              "0.777778 [0.555556, 0.944444]",
              "0.166667 [0.0, 0.333333]",
              "0.341667 [0.20463, 0.509282]"
            ],
            [
              "R1b",
              18,
              "0.666667 [0.444444, 0.888889]",
              "0.166667 [0.0, 0.333333]",
              "0.327315 [0.186088, 0.497697]"
            ],
            [
              "R1b_x0.5",
              18,
              "0.666667 [0.444444, 0.888889]",
              "0.166667 [0.0, 0.333333]",
              "0.300992 [0.155686, 0.477391]"
            ],
            [
              "R1b_x2",
              18,
              "0.722222 [0.5, 0.888889]",
              "0.166667 [0.0, 0.333333]",
              "0.343364 [0.205999, 0.508507]"
            ],
            [
              "R2",
              18,
              "0.722222 [0.5, 0.888889]",
              "0.555556 [0.333333, 0.777778]",
              "0.657407 [0.444444, 0.851852]"
            ],
            [
              "R3",
              18,
              "0.888889 [0.722222, 1.0]",
              "0.777778 [0.611111, 0.944444]",
              "0.777778 [0.611111, 0.916667]"
            ]
          ]
        },
        {
          "source": "experiments/eval/heldout-retrieval-20261103-paid/metrics.json",
          "jsonHeldout": "fresh65",
          "title": "fresh65",
          "columns": [
            "Method",
            "Eligible n",
            "Chunk hit@8 [95% CI]",
            "Strict passage hit@8 [95% CI]",
            "Chunk MRR@10 [95% CI]"
          ],
          "rows": [
            [
              "bm25",
              34,
              "0.911765 [0.794118, 1.0]",
              "0.5 [0.323529, 0.647794]",
              "0.544643 [0.411484, 0.670607]"
            ],
            [
              "dense",
              34,
              "0.823529 [0.676471, 0.941176]",
              "0.5 [0.323529, 0.647059]",
              "0.497059 [0.3725, 0.619681]"
            ],
            [
              "hybrid",
              34,
              "0.882353 [0.764706, 0.970588]",
              "0.5 [0.323529, 0.647059]",
              "0.617554 [0.479987, 0.742237]"
            ],
            [
              "R1a",
              34,
              "0.911765 [0.794118, 1.0]",
              "0.5 [0.323529, 0.647059]",
              "0.623926 [0.483763, 0.745627]"
            ],
            [
              "R1b",
              34,
              "0.911765 [0.794118, 1.0]",
              "0.5 [0.323529, 0.647059]",
              "0.625397 [0.485202, 0.747097]"
            ],
            [
              "R1b_x0.5",
              34,
              "0.911765 [0.794118, 1.0]",
              "0.5 [0.323529, 0.647059]",
              "0.625397 [0.485202, 0.747097]"
            ],
            [
              "R1b_x2",
              34,
              "0.911765 [0.794118, 1.0]",
              "0.5 [0.323529, 0.647059]",
              "0.625397 [0.485202, 0.747097]"
            ],
            [
              "R2",
              34,
              "0.970588 [0.911765, 1.0]",
              "0.941176 [0.852941, 1.0]",
              "0.887255 [0.794118, 0.965686]"
            ],
            [
              "R3",
              34,
              "0.970588 [0.911765, 1.0]",
              "0.941176 [0.852941, 1.0]",
              "0.887255 [0.794118, 0.965686]"
            ]
          ]
        }
      ],
      "examples": [
        {
          "source": "experiments/eval/heldout-retrieval-20261103-paid/scores.jsonl",
          "label": "hybrid",
          "case_id": "HO-001",
          "method": "hybrid",
          "set": "registered31",
          "first_relevant_rank": 1,
          "ranked": [
            {
              "chunk_id": "d47180da202fbce5",
              "relevant": 1
            },
            {
              "chunk_id": "8c7f2c8903f34817",
              "relevant": 0
            },
            {
              "chunk_id": "b1f69907896f39dd",
              "relevant": 0
            }
          ]
        },
        {
          "source": "experiments/eval/heldout-retrieval-20261103-paid/scores.jsonl",
          "label": "R3",
          "case_id": "HO-001",
          "method": "R3",
          "set": "registered31",
          "first_relevant_rank": 1,
          "ranked": [
            {
              "chunk_id": "b9a6b850ca005149",
              "relevant": 1
            },
            {
              "chunk_id": "d47180da202fbce5",
              "relevant": 1
            },
            {
              "chunk_id": "8c7f2c8903f34817",
              "relevant": 0
            }
          ]
        }
      ],
      "exampleNote": "The tables are worked set-level calculations: strict hit@8 counts 3/18 to 14/18 original, and 17/34 to 32/34 fresh. Per-case worked ranks are shown below once projected from the immutable scores.",
      "takeaway": "Strict hit@8 improved hybrid to R3: .167 to .778 original, .500 to .941 fresh.",
      "limit": "A pristine confirmatory test or answer-quality gain. Original questions share evidence with development; fresh questions are only partly independent. Intervals do not cover gold or reranker uncertainty.",
      "id": "heldout-retrieval",
      "group": "retrieval"
    }
  ]
};
