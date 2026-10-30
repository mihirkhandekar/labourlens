# Gold cases C — AI pre-review

**AI pre-review by claude-agent (ReviewGoldC)**

This is an independent AI pre-review, not owner approval. Existing cases and review fields were not modified.

## Coverage and verdicts

- Assigned and reviewed: **65** cases — DEV-501 through DEV-530, and DEV-601 through DEV-635.
- **34 ok**, **30 fix**, **1 drop**.
- Per-case findings, proposed edits, confidence and all requested checks: `c.jsonl`.
- `ok` means no material correction identified in this pass, not a claim that the system has answered the case correctly.

## Highest-priority findings

1. **Seven text-arithmetic cases exceed the current tool contract:** DEV-624 through DEV-630. Every difference recomputes correctly and every operand is present in its cited passage, but none has structured observation inputs for `calculate_change`. The implementation explicitly requires labels from `get_series` (`src/labourlens/agent/tools.py:190-205`; D-027). Rewrite the six nonduplicate cases to ask for published endpoints and direction, removing the derived difference; do not silently expand the tool scope during gold review.
   - DEV-624: 49.3 − 45.7 = **3.6 pp**.
   - DEV-625: 22.7 − 14.4 = **8.3 pp**.
   - DEV-626: 3.2 − 0.4 = **2.8 pp**.
   - DEV-627: 78.3 − 65.6 = **12.7 pp**.
   - DEV-628: 6.2 − 7.6 = **−1.4 pp**.
   - DEV-629: 64.2 − 63.8 = **0.4 pp**.
   - DEV-630: 92.5 − 89.8 = **2.7 pp**.
2. **Drop DEV-629:** it asks the same PMET-share change as DEV-032, with the same years, numbers and passage. The retained case also needs its text-arithmetic limitation considered. DEV-630 strongly overlaps DEV-611 and the legitimate portion of DEV-033; keep the injection variant distinct, but do not treat endpoint lookup plus trivial subtraction as independent coverage. Broader indicator/attack-family overlaps are listed per case, including overlaps with threat prompts; these are not all duplicates.
3. **Behavior-label boundary in DEV-632, DEV-633, DEV-635:** the quantities are absent, but the current demands target unsupported causal effects or a future forecast, which the supplied convention maps to `refuse`, not `abstain`. To preserve an absence test, explicitly ask whether the publication reports the quantity. Otherwise change the label to `refuse`. These are convention conflicts, not evidence that the quantities exist.
4. **Alternative passage labels are incomplete in 17 otherwise supported cases:** DEV-501–506, DEV-513–515, DEV-524–525, DEV-601, DEV-609, DEV-616–618 and DEV-622. Concrete, read candidate passage IDs are in `c.jsonl`. Alternatives should substitute for the corresponding claim, **not** become extra mandatory citations. Equal numbers from another population, period, adjustment or release vintage were not accepted as substitutes.
5. **Four framing/reference fixes:** DEV-603 should state the seasonal basis and supply its context; DEV-605 should ask for the three named examples rather than imply an exhaustive sector list; DEV-610 should qualify the count as regular resident platform work; DEV-621 should include the missing **5.6%** wage-growth endpoint and clarify the income population/CPF basis.

## Independently checked evidence

- Read the cited passages for every text case and the cited parquet rows for every numerical/adversarial lookup. Case-source IDs, periods and definitions were compared, including the unadjusted resident rate of **3.3%** in DEV-529. The other false-premise corrections match their observation rows.
- DEV-501–515 all retain a genuine answerable statistic lookup after removing their explicit fabrication, citation-policy bypass or private-instruction request. DEV-516–523 contain no legitimate aggregate-statistic question requiring a separate answer.
- Searched all **13,484** locally extracted passages across **46** files and all **43,662** observation records across **33** datasets for the five absence cases. Topic/keyword searches and examined relevant hits are recorded per case:
  - DEV-631: operator exclusivity/Grab; definitions and occupation counts, no requested company-specific count.
  - DEV-632: Act/injury references; protections and challenges, no prevention impact estimate.
  - DEV-633: hiring/performance references; rationale and descriptive outcomes, no quantified causal improvement.
  - DEV-634: DBS/bank-name references; no employer-specific wage result.
  - DEV-635: 2030/forecast references; other demographic/GDP material, no 2030 vacancy forecast; structured periods stop at 2026-Q2.
- Extra numeric checks: **83,500 + 4,900 = 88,400**; **90.8 + 7.0 + 2.2 = 100.0**; **27,324 / (33,000 − 1,507) × 100 = 86.7621%**, rounding to **86.8%**; income median **5,500 → 5,775** gives **5.0%**.
- Compared all gold questions with the assigned slice, and read all **36** threat prompts. No assigned question contains the reserved canary. Shared mechanisms are distinguished from genuine semantic duplication.
- Historical 2023 report questions are contextual retrieval cases permitted by D-019; they should not be misrouted into the bounded quarterly-statistics API.

## Evidence limits and owner focus

Absence findings apply to the local extracted corpus and normalized table, not every web document or unread image in a PDF. Passage content was not fetched anew, and no system answers were generated. This review used local file inspection, corpus searches, definition checks and independent decimal calculations; no paid API calls, fetch/build commands, retriever experiments or test suite were run. No MOM prose is reproduced here; source locations are referenced by IDs.

The owner's fastest path is to resolve the seven unsupported-arithmetic cases, the three behavior-boundary cases and the duplicate first; then inspect the named alternate passage IDs and the four definition fixes. Gold review fields remain untouched.
