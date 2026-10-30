# ADR-003 — Expanded structured-data scope

**Status:** APPROVED by project owner, 30 October 2026
**Supersedes in part:** ADR-001 (which fixed four structured datasets). The domain, answer period (2024-Q1 to 2026-Q2) and unstructured scope are unchanged.

## Context
The four datasets in ADR-001 support the core questions but give limited ambiguity and revision material. The owner asked for a richer, more impressive structured layer, including the good-to-haves.

## Decision
1. **Tier 1 datasets are in scope**, in addition to the four approved ones. Dataset IDs and rationale are in `docs/decisions.md` D-003. They include overall and citizen unemployment, job vacancy rate and counts, retrenchments by industry, retrenched permanent and term-contract employees, re-entry into employment at 6 and 12 months, resignation and recruitment rates, and counts of unemployed.
2. **Six features are in scope:** cross-source reconciliation table, revision tracker over snapshots, derived indicators with lineage and consistency checks, data-contract tests, a provenance trace command, and at least two EDA figures.
3. **Spec-driven adapters.** Ordinary long-format datasets share one declarative adapter driven by a per-dataset spec file (columns, types, unit, population, adjustment, expected period range). The two special cases keep custom code: resident unemployment (`YYYY-MM` periods, two adjustment series) and the sector table (wide columns, hierarchy by whitespace).
4. **Admission rule.** A dataset stays only if M1.1 shows it reaches 2026-Q2 and its contract tests pass. A failing dataset is dropped and recorded in the data sheet; its adapter is never patched around the failure.
5. **Tier 2 is deferred** (annual wages and income, annual retrenchment incidence, short work-week/temporary layoff quarterly). **Excluded:** foreign-workforce datasets (stale since June 2024) and off-topic datasets.

## Alternatives considered
| Option | Why not chosen |
|---|---|
| Keep four datasets | Too little ambiguity and revision material for the evaluation set |
| Tier 1 core only, rest if time allows | Owner preferred the full Tier 1 plus features |
| Hand-written adapter per dataset | About 18 near-duplicate modules; slower and more error-prone than one spec-driven adapter |

## Risks and mitigations
- **Schedule:** more datasets cost time from M2 to M6 (60% of the rubric). Mitigation: spec-driven adapter; hard admission rule; M1 stops at its gate even if extras are unfinished, and unfinished extras are reported, not hidden.
- **Semantic mixing:** more series means more chances to mix populations or adjustments. Mitigation: `population`, `adjustment` and `unit` are required fields; comparison tools reject mismatches.
- **Unverified coverage:** per-dataset 2026-Q2 coverage is not yet checked. Mitigation: the admission rule.

## Approval boundary
Structured scope approved. **M1 implementation is not yet approved** (D-005).
