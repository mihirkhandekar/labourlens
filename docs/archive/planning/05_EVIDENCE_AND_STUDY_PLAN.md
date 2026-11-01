> **Historical planning document (30 Oct 2026), written before implementation.** Statements such as "not yet approved" or "not executed" describe that date, not the current state. Current status is in [`docs/progress.md`](../../progress.md), decisions in [`docs/decisions.md`](../../decisions.md) and requirements evidence in [`docs/requirements-matrix.md`](../../requirements-matrix.md).

# Evidence ledger, evaluation design and interview learning plan

**Status:** planned process. No ingestion, tests, benchmarks or human reviews have yet been executed in this planning bundle. Never fill the following templates with invented pass/fail results.

## Purpose
The take-home should produce a system **and** a defensible engineering story: hypotheses, choices, failed alternatives, source facts, observed metrics and repeatable demonstrations. Maintain separate public submission artifacts and private learning notes.

## Evidence ledger — record after each authorized milestone

| Evidence type | Required details | Proposed durable location |
|---|---|---|
| Source provenance | Official URL, publisher, licence, publication/retrieval dates, version, hash, rights | `data/manifests/`, `docs/data-sheet.md` |
| Transform/quality | Raw column/row lineage, missing/invalid counts, schema drift, normalization version, source spot checks | `artifacts/data-quality/` |
| Code change | Commit ID, short diff summary, what changed and why, linked tests | `docs/progress.md`, `docs/decisions/` |
| Experiment configuration | Corpus snapshot ID, embedding model, retrieval top-k/fusion, prompt/model IDs, generation options, dependencies | `experiments/configs/` |
| Retrieval evaluation | Case ID, expected evidence, returned IDs and rank, Recall@k/MRR, errors | `experiments/runs/<run_id>/retrieval.*` |
| Generation evaluation | Raw answer, citations, gold answer/behavior, schema/result validation, groundedness review | `experiments/runs/<run_id>/answers.*` |
| Operational metrics | Tokens, provider/model, per-call duration, retries, estimated USD/SGD cost and assumptions, tool success/failures | `experiments/runs/<run_id>/telemetry.*` |
| Safety and MCP | Malicious input fixture, tool/resource payload, rejected arg, expected vs observed outcome, protocol traces | `tests/security/`, `artifacts/mcp/` |
| Human review | Reviewer role/name initials, date, rubric, cases reviewed, per-dimension rating, rationale | `experiments/human_review/` |
| Reproducibility | Command, environment (redacted), version hashes, start time, output/log path, exit code, clean-room steps | `artifacts/verification/` |

**Rule:** measured or verified outcomes require supporting files and exact command or review record. Hypotheses and illustrative figures must be marked as such. Avoid publishing personal identifiers, sensitive environment paths, secrets, or full copyrighted report text in traces.

## Evaluation split / anti-leakage rules
- Draft >=12–15 **development** cases for iterative debugging and >=30 **held-out** cases for final comparison; stratify by factual, synthesis, calculation, ambiguous/unanswerable, conflicting, adversarial.
- Seed questions from domain questions and direct verified sources; label correct observation/passage IDs after stable ingestion ID assignment.
- Assign `case_id`, source snapshot, approved gold evidence, required facts/calc, expected answer behavior and case-type label. Maintain a small rubric for allowable paraphrases.
- Store a hash or immutable version of held-out labels before using them for final benchmark. Do not edit holdout to rescue a poor score.
- Compare B0 non-LLM BM25 extractive baseline, E1 BM25 + fixed LLM, E2 dense + fixed LLM, E3 hybrid + fixed LLM; optional E4 changes only chunking. All other experimental factors held constant for each controlled comparison.
- Report retrieval Recall@5/MRR@5, accuracy by type, groundedness/citation correctness, numeric precision, abstention reliability, latency, costs and errors. If a metric cannot be measured rigorously, label it exploratory.
- Use deterministic grading for exact quantities/schema/citation existence; human-review actual supporting passages for semantic correctness. LLM judge is a supplement with fixed prompt/model, not a substitute for human review.

## Study material after each milestone
Every `study/<milestone>.md` should contain:
1. **In plain English:** What we built, why it exists and what assessment requirement it addresses.
2. **Technical mechanism:** Data flow and critical contracts, illustrated by real inputs/outputs.
3. **Rejected options:** 2–3 alternatives and meaningful pros/cons.
4. **Why our choice:** Practical trade-off based on observed project needs; clearly note any untested assumption.
5. **How we know it works:** Real tests, metrics, manual review and known limitations with file references.
6. **Failure cases:** At least one genuine example (without sanitizing errors away).
7. **Interview preparation:** Five probable questions, concise defensible answer, one deeper follow-up.
8. **Where to inspect code:** Entry points/modules/files and the exact command to reproduce demonstration.
9. **Self-test:** A short quiz; explain the difference between a source fact, model claim and interpretation.

## Suggested study headings
- `study/01-data-ingestion.md`: sourcing, provenance, revisions, licensing, quarter normalization, seasonality.
- `study/02-retrieval-baselines.md`: BM25, chunks, relevancy labels, Recall@5, MRR.
- `study/03-hybrid-rag.md`: embeddings, vector similarity, RRF, context and citation support.
- `study/04-langgraph.md`: state graph, model-directed tools, bounded execution, deterministic arithmetic, retries.
- `study/05-mcp-and-security.md`: host/client/server, tool/resource, schemas, untrusted content, prompt injection.
- `study/06-evaluation.md`: experimental controls, leakage, judge bias, confidence, errors, cost/latency.
- `study/07-production.md`: drift, data versioning, access control, observability, secure government considerations.
- `study/demo-qa.md`: critical design decisions and challenge questions with real project answers.

## 20-minute live demonstration — target outline
- Minutes 0–3: users, problem, approved domain, real official-source architecture.
- Minutes 3–7: factual answer + multi-source synthesis + original source locator.
- Minutes 7–10: deterministic calculation and revised preliminary/final conflict.
- Minutes 10–13: unanswerable and injection case; show trustworthy failure behavior.
- Minutes 13–17: held-out evaluation, baseline vs selected configuration, quality/latency/cost, errors.
- Minutes 17–19: MCP discovery/invocation and failure-handling demo.
- Minute 19–20: limitations, production controls and top two next experiments.

Bring local/replayable **actual** recorded execution traces for reliability, but label replay vs live; demonstrate one live request if reliable. The brief specifies a live 20-minute demonstration and subsequent questions; it does not explicitly mandate a submitted recording.

## Interview questions to practice from Milestone 1 onward
1. Why is a published statistical figure not enough without definition, unit and release date?
2. Why can a quarter be encoded as a month, and how do you prevent bad conversions?
3. What is the difference between immutable snapshot reproducibility and data freshness?
4. Why should PDF table extraction not be used as the sole source for calculations?
5. How do you know advance and final figures represent a revision, not different underlying indicators?
6. How does your pipeline distinguish a missing value from a true zero?
7. What exactly is published under each source's usage licence? Can you commit reports to GitHub?
8. What changes would permission-aware retrieval require in a government environment?
9. What would happen if a data.gov.sg schema changes tomorrow?
10. What exactly did you personally validate, rather than only ask an AI model to verify?
