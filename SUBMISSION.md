# LabourLens submission

I built a Singapore labour-market research assistant for the GenAI Engineer take-home. The workbench answers questions with citations to official statistics and reports. Start with the saved results, then run the local report and MCP demo.

## Read first

1. [README](README.md)
2. [Architecture](docs/architecture.md)
3. [Evaluation report](docs/evaluation-report.md)
4. [AI-assisted development](docs/ai-assisted-development.md)
5. [Requirements matrix](docs/requirements-matrix.md). `partial` there means my sign-off or an external check is still open, not that work is missing.

## Run it

You need Git, uv and make. uv can install Python 3.12. From the repository root:

```bash
make setup
make verify && uv run labourlens mcp-demo
LABOURLENS_DEMO_ENABLED=false make serve
```

Open <http://127.0.0.1:8000>, `/deck` or `/workbench`. These commands make no paid calls. The deck has 30 main slides and 44 including the appendix; press X twice quickly for speaker notes. Full commands are in [Reproduce](docs/reproduce.md).

## Inputs

| Available inputs | What runs |
|---|---|
| Public clone only | Offline checks, report and deck, MCP statistics demo, aggregation of committed scores |
| Private corpus, no API key | Corpus build, EDA, keyword retrieval, corpus tests and rights scan; rescoring also needs private saved answers |
| Private corpus and API key | Live answers, embeddings, reranked retrieval and new experiments; these cost money |

## Live demo

<https://labourlens.navig.me> has the report and deck. The workbench needs an access code; codes sent separately. Only statistics lookup uses MCP in the live app. The all-three-tools MCP option was tested and is not live.

## Limits

- AI drafted the reference answers. I reviewed them after scoring, as the only reviewer.
- The main judge is from the same model family. A second-family check did not reproduce every gain.
- The headline averages two runs: 0.897 versus 0.827 on 237 development questions for matching answer status. Two runs do not estimate variance, but identical reruns flip 11 to 18 of 237 development cases and 1 to 3 of 65 fresh cases. A rule that always answers would score 0.768, 0.774 and 0.738 on the three sets, so the fresh-set results are within about three points of it.
- Neither test set demonstrates a gain: 0.839 versus 0.806 on the original 31 questions, 0.715 versus 0.746 on 65 fresh questions.
- Test sets are partly independent. Original questions share development evidence; fresh questions were later reused for diagnostics.
- The served chain scored 90.8% on 65 cases, mostly reused development questions. The full evaluation bypasses web stages and MCP.
- Report-only arithmetic remains weak. PDF tables can extract poorly, and the tested tool extension was not adopted.
- The scanner is a warning layer. Detection rose from 10/30 to 23/30; it still misses attacks. The fresh 36-case attack suite scored 35/36 with and without defences.
- Reports and raw answers are not in the repo. Three dataset licences are unverified; 23 document rights are unresolved. A clone's rights scan reports `NOT CHECKED`.
- This is a single-process prototype. Live calls cost money; the provider-side spend cap is unverified. Do not submit confidential or personal information.

## Packaging

Hand over the GitHub URL or a tracked-files archive made with `git archive HEAD`. Never zip the working folder: ignored secrets, private source text and assessment material sit beside the submission.
