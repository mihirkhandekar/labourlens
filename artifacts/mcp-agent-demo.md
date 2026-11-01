# MCP-backed agent answer (demo scenario 8)

Recorded 2026-11-01 04:05 UTC by `uv run labourlens mcp-agent-demo`. One question, one run: a demonstration that the agent can use the statistics server over MCP, not an evaluation. The live web app routes `get_series` the same way; the accuracy evaluations called the tools directly.

## Setup

- Question: How did the number of retrenched employees change from 2025-Q4 to 2026-Q1?
- Models: planner `gpt-6-luna`, answer `gpt-6-luna`; prompts `planner_v1` and `answer_v3`; retrieval `r3`.
- Statistics backend: `SyncStatsBackend` over stdio to `labourlens.mcp.server` (allow-listed server `labourlens-stats`, name, version and tool list verified at connect).
- Everything else (retrieval, planner, answer, validator) is the normal agent path.

## MCP calls made by the agent

| # | tool | source | period | dimension | ok | ms | quarantined rows |
|---|---|---|---|---|---|---|---|
| 1 | get_statistic | `retrenched_employees` | 2025-Q4 to 2026-Q1 | all | True | 2349.5 | 0 |

## Agent result

- Outcome: `answered`; 2 planning round(s), 2 tool call(s); 11.06 s; 3 model calls; cost $0.001048.
- Graph nodes visited: validate_question -> plan_research -> execute_tool -> assess_evidence -> generate_answer -> validate_answer -> finalize.

Structured answer as returned:

```json
{
  "status": "answered",
  "summary": "The number of retrenched employees increased by 140 persons, from 3,690 in 2025-Q4 to 3,830 in 2026-Q1.",
  "claims": [
    {
      "text": "For the all-employees series, the dataset snapshot reports 3,690 persons in 2025-Q4 and 3,830 persons in 2026-Q1, an increase of 140 persons.",
      "citations": [
        {
          "label": "O1",
          "quote": "2025-Q4 | establishments, not_applicable | 3,690 persons"
        },
        {
          "label": "O2",
          "quote": "2026-Q1 | establishments, not_applicable | 3,830 persons"
        },
        {
          "label": "C1",
          "quote": "3830 - 3690 = 140 persons"
        }
      ]
    }
  ],
  "caveats": [
    "These figures are from a dataset snapshot."
  ],
  "clarification_question": "",
  "reason": ""
}
```

## Deterministic check against the direct lookup

Each successful MCP query was repeated against the local observations table with no model and no MCP, and the figures compared with the answer text.

| source | period | value (direct) | appears in the answer |
|---|---|---|---|
| `retrenched_employees` | 2025-Q4 | 3,690 persons | yes |
| `retrenched_employees` | 2026-Q1 | 3,830 persons | yes |

Evidence items the agent held: O1=retrenched_employees, O2=retrenched_employees, C1=retrenched_employees. Cited labels: cf9bcacafabfda9f, af35147df5007250, calc:5287557a787d.

## Limits

- One question and one run; no claim about reliability or about MCP versus direct accuracy. The paired direct-versus-MCP latency comparison is section 17 of `docs/mcp-demo-transcript.md`.
- The agent uses the MCP path for `get_series` only; the other eight server tools are not wired into the agent.
- Model output is not deterministic; a rerun can word the answer differently.
