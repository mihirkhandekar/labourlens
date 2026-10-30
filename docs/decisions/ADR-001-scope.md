# ADR-001 — LabourLens research scope

**Status:** APPROVED by project owner, 30 October 2026  
**Decision category:** Product/domain and evaluation boundaries

## Context
The GenAI Engineer technical challenge asks for an evidence-grounded policy research assistant using mixed-format data, numerical tools, cited synthesis, ambiguity and conflict handling, and experimental evaluation. It explicitly does not prioritize a heavy backend or polished frontend. The project needs a small, coherent real-world corpus suitable for a defensible 20-minute demonstration.

## Alternatives discussed
| Option | Benefits | Risks |
|---|---|---|
| Labour market intelligence | Official structured quarterly indicators and narrative reports; true publication revisions; useful calculations | Definition/seasonality and release-version mismatches |
| Housing affordability | Accessible datasets, clear visualizations | Confounding variables and heterogeneous transaction-level data |
| Cost of living / inflation | Time-series data, policy relevance | Index methodology, weights and causality complexities |

## Approved decision
- Product: **LabourLens — Singapore Labour Market Intelligence**.
- Intended users: policy researchers and labour-market analysts.
- Supported answer period: **2024 Q1 through 2026 Q2**, inclusive. Older values may exist in downloaded datasets; scope filters and corpus snapshot must control which observations are answerable.
- Four structured datasets: resident unemployment rate; vacancy-to-unemployed ratio; quarterly retrenchments; employment changes by sector.
- Five unstructured/publication sources: MOM full labour-market reports for 2025 Q3, 2025 Q4, 2026 Q1, 2026 Q2; and Q2 2026 advance release (PDF/HTML depending on verified access and reuse conditions).
- Question types: factual; numerical change; cross-source synthesis; preliminary/final revision; ambiguity/unanswerability; adversarial/injection.
- Explicit non-goals: forecasting, causal-policy-impact estimation without evidence, unrestricted internet research, individual job advice, production-scale identity infrastructure.
- Official-source evidence and licensing are mandatory; evaluate at least 30 held-out cases, with human review and real measured metrics.
- Visual ambition: sleek policy-research workbench with citations, provenance, interactive figures, execution evidence, and experiment comparison. UI polish must not compromise rubric-critical evaluation.

## Evidence and warnings
- Scope approval is **not** confirmation that every data source can be downloaded or parsed without issues.
- Data availability, quarter completeness, PDF publication links, publisher terms, and exact row schemas must be tested during ingestion. Distinguish planned facts from observed facts.
- Approved corpus does not imply a right to redistribute original MOM PDF report files in a public repository.

## Revisit criteria
Only revisit scope with the owner's approval if a core government dataset is inaccessible, rights prevent legitimate usage, or quality is insufficient for mandatory demonstrations. First try a transparent official-source alternative with similar definitions.
