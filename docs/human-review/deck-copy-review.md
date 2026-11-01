# Deck and home page copy review (edit list)

Scope: `web/static/presentation/slides.js` (all slide specs), `deck.js` (layouts), `ch*.js` (figure titles that become slide titles), `web/static/js/home.js`, `web/static/app.js`, `web/index.html`, `web/deck.html`. Read-only review; nothing outside this file was changed.

## 0. How the slide face is built (what a builder must know)

- Slide face = `title` + `bullets` OR `visual` + `deck-source` line ("Source: ...").
- `figSlide()` sets `title: figTitle(f) || extra.title`. Unless a spec overrides `title` AFTER the spread, the slide title is the chart's computed sentence from `ch*.js` (for example `fig-ladder`, `fig-paired`, `fig-e2efix`, `fig-unemployment`). To retitle, add `title: '...'` after `...figSlide(...)` as `fig-ladder`, `fig-review` and `fig-threat-matrix` already do.
- The figure also prints its own `.pr-fig-title`, `.pr-fig-takeaway` and `.pr-fig-note` inside the visual. These repeat the slide title and carry identifiers (R3, A3, hit@8, gpt-6-luna, T-I06). Deck-only fix: in `presentation.css` hide `.deck-page .pr-fig-title` and `.deck-page .pr-fig-note`, keep `.pr-fig-takeaway` as the one caption line and rewrite takeaways (list in section 5).
- `withSoWhat(visual, line)` adds a second sentence under every `rows()` slide. Drop it everywhere (the title already says it) except where noted.
- `rows([...])` slides are paragraphs in a table. They exceed any budget. Replace each with the bullets or graphic below.
- 57 main slides today. A 20-minute talk fits about 25. Section 2 merges and cuts to 26.

### Body budget (applies to every main slide)
- Either max 3 bullets, each under 12 words, no semicolons; or ONE graphic plus ONE caption line (under 14 words).
- No `withSoWhat` line, no bridge sentence ("The next slide shows...").
- Numbers on the face come from `report.json` via the model as today. Anything hardcoded (13,484 / 15,915 / 16,419 passages, "45 of 268", "$0.05", "$2") is not in report.json (only one of the passage counts appears there). Show it only in the graphic that already states it, or move to notes.

### Vocabulary map (replace everywhere on faces, figures and bullets)
| Today | Say |
|---|---|
| R0 / R1a / R2 / R3 / r3 / hybrid | Baseline / Filter by period / AI rerank / Filter then rerank / Filter then rerank / Baseline |
| A1..A5 | Baseline, Better prompt, Filter then rerank, Wider pool, New planner (name the change, no code) |
| X1 / X2 / "regression check" | Cleaner text / Final system check |
| T-I06 | The planted wrong figure |
| hit@8 | Right passage in the top 8 |
| held-out, held-out v2, "gold" | Fresh test questions, second fresh set, reference answers |
| corpus v1 / v2 / v3 | First, second, third document build |
| behaviour accuracy | Right kind of response (answer, abstain, ask, refuse) |
| operational_failure, planner_v1, merge120, canary | cut from faces |
| gpt-6-luna etc. | Keep only on the cost slide; elsewhere "the main model" / "the second model" |

## 1. Flags: identifiers on slide faces (all must go to notes or appendix)

Titles and bullets:
- ADR-001: slide "framing" bullet 3 ("Approved: ... (ADR-001)"), source line "Project scope decision (ADR-001); ...", slide "data" TITLE ("ADR-001 approved four datasets, and D-003 added..."), "Out of scope" rows ("Out of scope in ADR-001." x2), source line of that slide.
- D-numbers: "data" slide rows (D-003 x3, D-006), "left out" slide rows (D-003, D-006, D-040) and source line "Project decision log (D-003, D-006, D-040)", corpus slide row "(D-037)" and "(D-040)", T-I06 slide none on face but figure note carries "D-038" in appendix, "wrong" slide none, work-log appendix fine.
- Experiment tags: titles/bullets with R0..R3, A1..A5, X1, X2, H1/H2/H3, T-I06: "retrieval" title ("hit@8"), "fig-ladder" bullets (R1a, R2, R3, "pre-registered H1", "appendix C"), "hypotheses" slide (R1/R2, H1..H5, "BM25 held-out run"), "parsing" row ("(X1)"), "fig-progression" bullets (A2, A3, A4, A5), "X1/X2" slide title and rows, "contract/T-I06" slide title and bullets, "calc" slide visual note ("Run A3, gpt-6-luna"), cost slides row labels ("A3 development", "X2 regression check", "Held-out v2 r3"), "held-out v2" slides (r3, hybrid, `FREEZE.md`, "owner export a428db90", seed number).
- Paths and hashes: "held-out v2" decision-rule row (`FREEZE.md`, `a428db90`), cost slide source "(specs/prices.yaml)", product slide row "commit c297146", "corpus v3", final slide "commit abc1234" line (`uv run labourlens build-report`), every `deck-source` for appendix (already rewritten generically by the final loop; fine).
- Code identifiers: "operational_failure" (calc slide bullet 3), "report.json" in `missing()` text ("needs data that report.json does not contain"), final slide ("committed artifacts", "build-report"), agent graph figure labels (`plan_research`, `execute_tool`, `validate_answer`, `generate_answer`) in `fig-graph` node labels.
- Figure internals that surface identifiers: `fig-graph` title ("seven nodes and three guards"), `fig-ladder`, `fig-rank-shift`, `fig-hint`, `fig-ablation` (merge120), `fig-e2efix`, `fig-postfix`, `fig-paired` (all titles include R3/hybrid/gpt names).

Home page (`home.js`): "T-I06" in the limits list item 3, "corpus v1 / v3", "held-out", "gold labels", "report.json did not load" in the hero fallback, "Activity" wording is fine.

## 2. Slide-by-slide edit list (main deck)

Verdict key: KEEP, SHORTEN, REWRITE, CUT, MERGE (into the named slide). "Final #" is the order in the 26-slide deck; titles in quotes are the new slide titles.

### Opening
1. Title "Cited answers from Singapore labour-market data". REWRITE. See section 4 (title slide designs). New title: **LabourLens**. Remove the long sub.
2. Agenda "What I will cover, in the order I did it" (17 items incl. "framing", "contract"). CUT. The progress bar and slide titles carry orientation. If a roadmap is wanted, one line of 5 words on slide 3: none needed.

### The problem
3. "Policy researchers need one number, with its period, series and a source they can check". REWRITE. Final 2. Title: **The problem**. Body, 3 bullets:
   - Analysts need one figure they can check.
   - The right period, series and release matter.
   - A wrong or unsourced number is worse than none.
   Cut the three-row table and the "next slide" line. Source line: "MOM, SingStat via data.gov.sg".
4. "One question, three published answers: 1.9%, 2.9% and 3.5%". REWRITE with graphic. Final 3. Title: **Why one number is not enough**. Graphic G1 (section 3). Caption: "Same quarter, same question. Three correct numbers."
5. "A plain language model or a keyword search each fails in a different way". SHORTEN. Final 4. Title: **Why not a chatbot or search?** Body, 3 bullets:
   - A chatbot recalls figures without sources.
   - Search finds text but never does the sums.
   - Neither knows when to say no.
6. "The brief asks for evidence and evaluation, not a chatbot". CUT. Notes already carry it; it reads as justifying the assignment.

### Scope and plan
7. "I bounded the scope to N quarters, four MOM series and the MOM reports". REWRITE. Final 5. Title: **What it covers**. Visual: keep `bigStat` ("10 quarters, 2024 Q1 to 2026 Q2"). Bullets, 3:
   - Four MOM statistics series, quarterly.
   - Five MOM reports for context and explanations.
   - Outside that window, it declines to answer.
8. "Out of scope by decision: forecasts, causal claims, personal advice and open web research". REWRITE. Final 6. Title: **What it will not do**. Bullets, 3:
   - No forecasts.
   - No claims about causes.
   - No personal advice, no open web search.
9. "Before coding the retrievers, the requirements fixed how I would evaluate". MERGE into 10. Notes only.
10. "The hypotheses are written in the experiment notes, with a null for retrieval" (H1/H2/H3 paragraphs, "BM25 held-out run, written before the run", "Agent end to end, not a timestamped pre-registration"). REWRITE as one slide. Final 7. Title: **How I planned to test it**. Bullets, 3:
   - A keyword-search baseline, no AI.
   - Reference questions with expected sources.
   - Predictions written down before each run.
   Move H1..H5 text, "pre-registered" wording and file names to notes. Delete the bridge sentence "The data came next, because the hypotheses depend on what the series look like." (this is the owner-flagged line).

### The data
11. "ADR-001 approved four datasets, and D-003 added the ones that create ambiguity and cross-checks". REWRITE with graphic. Final 8. Title: **Choosing the data**. Graphic G2 (sources: two columns, statistics and reports). Caption: "Statistics give the numbers. Reports give the explanations."
12. "I left out stale, off-topic and non-labour sources". MERGE into 11 as notes. (Holds D-003/D-006/D-040.) CUT from face.
13. "The statistics measure, and N report PDFs and N release pages explain". MERGE into 11 (same graphic, counts from `sources.metrics.by_type`).
14. "Source records" (`fig-sources`, computed title "85 source records: N open licence, N all rights reserved..."). SHORTEN. Final 9. Title: **Where each source stands**. Keep chart, caption: "Report PDFs stay out of the public repository." Hide the computed figure title.
15. "The corpus grew three times, each time for a stated reason". REWRITE with graphic. Final 10. Title: **Three document builds**. Graphic G3 (timeline). Caption: "Each build fixed a problem the earlier one had."

### What the data showed
16. `fig-unemployment` ("Unemployment rates, by population and adjustment"). KEEP chart, REWRITE. Final 11. Title: **What the data showed**. Bullets, 2 (current bullet 1 comes from `findings[0].head`; check it is under 12 words, otherwise replace):
   - Unemployment has several official rates.
   - Every answer must name which one.
17. "Four unemployment series answer four different questions". MERGE into 4 (the G1 graphic carries the four series). CUT.
18. `fig-retrenchments` ("Retrenched employees: permanent and term contract" or the computed "Retrenchments peaked at ..."). SHORTEN. Final 12. Title: **Retrenchments rose, with no stated cause**. Bullets, 2:
   - The data shows movement, not reasons.
   - Why-questions get report text or no answer.
19. `fig-revisions` ("One quarter, three employment-change numbers"). KEEP title wording, rewrite title to: **Advance and final figures differ**. Final 13. Bullet, 1: "Every answer names its release." Chart caption: the three values for the latest reconciled quarter.
20. `fig-vacancy-ratio`. SHORTEN. Final 14. Title: **Why I did not recompute the ratio**. Bullets, 2:
   - Published ratio and counts come from different surveys.
   - I quote the published ratio.
   Drop "up to 0.67" from the face.
21. "Four findings from the data each changed the design". CUT (it repeats the four slides above). If kept, as one table row per finding: no.

### Reading and retrieval
22. "In a 16-passage audit, all 4 sampled tables came out flattened". REWRITE with graphic. Final 15. Title: **Reading the reports**. Graphic G4 (one PDF table beside its flattened extraction, as two small mock panels with the real sample text if available, otherwise labelled schematic). Caption: "Tables came out flattened. Numbers were intact."
23. Retrieval ladder rows "I climbed a ladder of retrievers: hit@8 went from X% to Y%". MERGE with 24 as ONE slide. CUT this one.
24. `fig-ladder` ("Filtering then reranking (R3) raised hit@8 ..." overridden by "With intervals, filtering gained more than reranking, and both together gained most"). REWRITE. Final 16. Title: **Does filtering help?** Graphic: existing ladder chart relabelled with plain step names (G5 staircase, section 3). Caption: "Filtering by period helped most. Reranking added a little."
25. "What the retrieval study cannot show". MOVE to the limits slide (notes + appendix C). CUT here.

### The agent
26. `fig-graph` ("The agent is one graph of seven nodes and three guards; the recorded run took N steps"). REWRITE. Final 17. Title: **The agent loop**. Graphic G6. Caption: "At most two search rounds and one repair."
27. "Three typed tools, none able to write, fetch the web or run code". SHORTEN. Final 18. Title: **Three read-only tools**. Visual: keep `.pr-tools` list only if each tool is a one-line row; drop the so-what. Caption: "No writing, no web, no code execution."
28. "Numbers come from code, and the loop has hard limits". REWRITE. Final 19. Title: **Code does the arithmetic**. Visual: `bigStat` (calculations correct) is only 24 cases and invites a bad question. Replace with a worked example (G7 trace), bullets none. Move limits ("10 seconds", "1,000 characters") to the loop graphic G6 as small labels. Remove `operational_failure`.
29. "Every claim carries a quote, and the answer takes one of five forms". REWRITE. Final 20. Title: **Every claim has a source**. Graphic G7 (evidence-to-answer trace). Caption: "An answer, a refusal, a question back, or no answer."
30. "A planted wrong figure was cited as fact; a cross-check now catches it in some runs". REWRITE. Final 21. Title: **A planted wrong figure**. Bullets, 3:
   - A fake number in a report passage was cited.
   - A cross-check against the data now catches it.
   - One model still failed it once.
   Keep the steps visual but remove "T-I06" from the step labels (ch6 `.pr-ti06-steps`).

### Measuring
31. `fig-review` "I reviewed 45 of 268 gold cases; 223 remain AI drafts". SHORTEN. Final 22. Title: **Who checked the answers**. Caption: "I reviewed 45 of 268 reference cases. An AI drafted the rest." Remove the three bullets (the "30 own, 95 agreed" detail goes to notes).
32. "Development cases choose the configuration; held-out cases only score it". REWRITE. Merge with 33 into one slide. Final 23. Title: **How I measured**. Bullets, 3:
   - Practice questions for tuning, fresh ones for scoring.
   - Right passage in the top 8, right kind of response.
   - Intervals, because the sets are small.
33. "Six measures, in plain words". MERGE into 32. CUT.
34. `fig-progression` ("Progression A1 to A5"). REWRITE. Final 24. Title: **The experiment ladder** if the staircase graphic G8 is built, else **What each change did**. Graphic G8. Caption: "Retrieval was the only change that mattered."
35. `fig-paired` ("Paired difference on held-out"). MERGE into 38 (fresh-set result). CUT.
36. "Corpus changes moved no headline metric, and X2 is a regression check, not an ablation". CUT from face (notes + appendix A). "Not an ablation" is the owner-flagged mechanism language.
37. "Held-out v2: 65 new cases, a rule written before the run". MERGE into 38. CUT.
38. Held-out v2 result "r3 beat hybrid on N cases and lost on M..." Final 25. REWRITE. Title: **On fresh questions, the gain was small**. Visual: `bigStat` ("+3 cases"? keep value from `v2p.paired_difference`, formatted in points). Bullets, 2:
   - Filtering helped the main model by a few cases.
   - It did not help the second model.
39. "N of M cases missed, and K of them are a tool gap, not retrieval". REWRITE. Final 26. Title: **Why it missed**. Graphic: bar of error classes from `heldout_v2.error_analysis.classes` (G9 optional) or bullets, 2:
   - Most misses were a missing tool, not retrieval.
   - A fix is being tested. No result yet.

### Cost
40. Price table "I chose the cheapest models that held up, and excluded the one at $10 per 1M input tokens". REWRITE. Final 27. Title: **Choosing the model**. Graphic G9 cost bars. Caption: "The cheaper model scored as well on my questions."
41. Measured cost per case table. MERGE into 40 (same graphic, second panel for latency). CUT.
42. "Accuracy bought with retrieval cost more time than money". MERGE into 40. CUT; one caption line: "Reranking cost time, not money."
43. "The live app reserves $0.05 per question under a $2 daily budget, and has no provider cap yet". SHORTEN. Final 28 (or fold into the product slide). Title: **Spend limits on the live app**. Bullets, 3:
   - A per-question budget is reserved before any paid call.
   - A daily limit blocks new questions at zero.
   - No cap is set on the provider account yet.

### Safety and MCP
44. `fig-threat-matrix` (override title "N of M failed cases ... are poisoned-passage cases"). REWRITE. Final 29. Title: **Safety tests**. Bullets, 3:
   - 36 attack cases in six categories.
   - One case failed: a poisoned report passage.
   - Defences made no measurable difference.
   Hide the computed figure title; keep the matrix.
45. `fig-e2efix`. MERGE into 30/44 as a note. CUT from face.
46. "Five controls are in place and three gaps are known, including a scanner that missed all 5 paraphrased probes". REWRITE. Final 30. Title: **What protects it, and what does not**. Two columns, 3 short items each (controls: untrusted text, read-only tools, hard limits; gaps: weak scanner, quotes not checked for meaning, one MCP filter miss).
47. `fig-mcp` ("A client treats the N-tool MCP server as untrusted..."). REWRITE. Final 31. Title: **The MCP server**. Graphic: existing four-box diagram. Caption: "Read-only tools. The client treats the server as untrusted."
48. `fig-mcp-latency`. SHORTEN. Final 32. Title: **What MCP costs**. Caption: "Direct calls are faster, so the app uses them by default."

### Product, process, close
49. "The workbench shows the evidence behind every answer". REWRITE. Final 33. Title: **The workbench**. Visual: a real screenshot of an answer card with the evidence drawer open (static image captured from the live app; see title-slide option B for the data). Caption: "Every answer links to its exact source passage."
50. "Each run is logged without secrets, and each session is rate limited". MOVE to appendix. CUT.
51. "I ran the work as gates: explore, compare, recommend, approve, implement, verify, document". REWRITE. Final 34. Title: **How I worked with AI agents**. Bullets, 3:
   - I made the scope and design decisions.
   - Agents drafted code and first-pass labels.
   - Independent reviews caught errors.
52. "I decided the questions; agents drafted the work; review caught four mistakes". MERGE into 51. CUT.
53. "Six things went wrong, and each taught me a rule" (rows with "Stale judge cache" etc.). REWRITE. Final 35. Title: **What went wrong**. Keep the 6 lesson lines but cut the left column to 3 to 4 words and drop `withSoWhat`; or show 3 of 6 (judge cache, planted figure, label edits) and send the rest to the appendix.
54. "Five limits constrain what these results show". SHORTEN. Final 36. Title: **Limits**. 3 bullets (labels mostly AI drafted; fresh-set gain is small; scanner and cost estimates are weak). Full list stays in appendix H.
55. "Next: finish the tool-fix experiment, then close the evaluation gaps". REWRITE. Final 37. Title: **What I would fix next**. 3 bullets: test the tool fix; get independent human review of labels; add a provider spend cap.
56. "Five findings, and the one thing I would not claim". REWRITE. Final 38 (last content slide). Title: **Summary**. 3 bullets (what it does; what moved retrieval; what is not proven). Delete `withSoWhat`.
57. "Sources and provenance". SHORTEN. Title: **Sources**. Bullets, 3: statistics from MOM and SingStat via data.gov.sg (Singapore Open Data Licence); MOM reports remain the Ministry's; model prices read 30 Oct 2026. Delete the commit, the artifact count and `uv run labourlens build-report` from the face (notes or appendix).

Count after merges/cuts: 38 listed above are still too many for 20 minutes. To reach ~26 also fold: Final 9 (source rights) into 8 notes, Final 14 into 13, Final 18+19 stay, Final 24 and 25 kept, Final 27/28 into one cost slide, Final 30 into 29, Final 32 into 31 (one slide, caption mentions the latency), Final 33 workbench kept, Final 35 into 36 (limits). Result: Title, Problem, One number, Chatbot/search, Covers, Will not do, How I tested, Data, Three builds, What data showed, Retrenchments, Advance/final, Vacancy ratio, Reading the reports, Does filtering help, Agent loop, Tools, Code does the sums, Every claim has a source, Planted figure, Who checked, How I measured, Experiment ladder, Fresh questions, Why it missed, Model and cost, Safety, MCP, Workbench, How I worked, Limits and next, Summary, Sources = 33. The builder SHOULD cut Vacancy ratio, Tools and Retrenchments to appendix to reach about 30 and run the talk at 40 seconds per slide. Final target: 30 or fewer.

## 3. Graphics to build (HTML/CSS/SVG, existing modules)

Existing helpers: `charts.js` (`el`, `fmt`, `finite`), `ui.js` (`stat`, `bigStat`, `dataTable`), `ch*.js` figure() factory for SVG charts, `model.js` (`m.charts`, `m.ladder`, `m.evalRow`, `m.paired`, `v2arm`).

**G1. Three answers to one question** (replaces slides 4 and 17).
- Layout: question line top ("What was the unemployment rate in 2026 Q2?"), then three equal cards in a row, each with a big number (`.num`, 120px), a two-line label, and a small pill under it. Cards: Overall, seasonally adjusted | Resident, seasonally adjusted | Resident, not adjusted. Optional fourth faded card for Citizen.
- Data: `charts` ids `unemployment_overall_sa`, `unemployment_resident_sa`, `unemployment_resident_nsa`, `unemployment_citizen_sa`; last non-null point via `latest(id)` (already in slides.js). Do not hardcode 1.9/2.9/3.5.
- Motion: count-up (`countRunner`) in sequence; no extra copy. Caption: "Same quarter, same question. Three correct numbers."

**G2. Two source types** (slide 11).
- Left block "Statistics" with a table icon and a row of four short names (unemployment, vacancies per unemployed person, retrenchments, employment change by sector) and the count `types.dataset_csv` snapshots. Right block "Reports" with a document icon and "MOM labour market reports Q3 2025 to Q2 2026" with `types.report_pdf` PDFs and `types.release_html` release pages. A thin arrow from each to a shared box "One answer, each part cited".
- Data: `sources.metrics.by_type`.

**G3. Document builds timeline** (slide 15).
- Horizontal line with three nodes, node label = "First / Second / Third build", under each the passage count (13,484 / 15,915 / 16,419) and a 5 to 6 word reason ("Original extraction", "Table and note fixes", "Six new sources added"). Node size proportional to passage count. A small bracket over the first node: "Registered results ran here".
- Data: only `retrieval.ladder.corpus_version` strings exist in report.json; passage counts are hardcoded in slides.js today. Add the three counts to report.json (build-report) or keep them as literals in this graphic only.

**G4. Table flattening example** (slide 22).
- Two panels with a arrow: left a 3-column, 3-row table rendered with HTML table in the original layout; right the same cells as a single wrapped line of text ("Q1 2.9 Q2 3.0 ..."). Label left "In the PDF", right "After extraction". Source: first flattened sample from `docs/human-review/ai-pre-review-passage-spot-check.md`. If a real passage cannot be quoted under the rights notice, label the graphic "Schematic".

**G5. Retrieval ladder as a staircase** (slide 16).
- Four steps ascending left to right, step height = hit@8, value label on top, plain label under each (Baseline, Filter by period, AI rerank, Filter then rerank), whisker = `hit@8_ci95`. Highlight the last step in `--accent`. Reuse the `fig-ladder` SVG and only relabel via a label map in `ch3-retrieval.js` (ids R0, R1a, R2, R3 stay in data; labels change). Data: `retrieval.ladder.configs.{R0,R1a,R2,R3}['hit@8']`.

**G6. The agent loop** (slide 26).
- Redraw `fig-graph` with plain labels: Question check, Plan, Tool call, Check evidence, Write answer, Check answer, Done. Two loop arrows: "up to 2 rounds" (Tool call back to Plan) and "1 repair" (Check answer back to Write answer). Guards are the three check boxes in the accent outline. Replace node names `plan_research`, `execute_tool`, etc. with these in `ORDER` display labels. Small chips under it: "6 tool calls", "10 s per call", "1 retry". Data: static design; limits constants only.

**G7. Evidence-to-answer trace** (slides 28 and 29).
- Vertical card: Question (one line) -> Tool call "get series: resident unemployment, 2026 Q2" -> returned row (value, unit, source link) -> calculation "2.9% minus 2.9% = 0.0 points" (decimal) -> Answer sentence with superscript [1] -> citation chip "[1] MOM resident unemployment rate, data.gov.sg, observation id" with a green check "quote found". Use real values from `summary.cards[0]` (`value`, `change`, `period`, `observation_id`, `source_id`) and `agent.events`.

**G8. Experiment ladder** (slide 34).
- Same staircase style as G5 but for behaviour accuracy across Baseline, Better prompt, Filter then rerank, Wider pool, New planner. Bars with intervals from `evaluation.rows[agent-dev-A1..A5/gpt-6-luna].metrics.behaviour_accuracy`. Draw the adopted step solid and the three rejected ones hatched with the label "no change". Fixes the long title of `fig-progression`.

**G9. Model cost as bars** (slide 40).
- Two small horizontal bar panels sharing the model labels: "Cost per case" (from `evaluation.rows[*].metrics.cost_per_case_usd`) and "Median seconds" (`latency_p50_s`). Rows: main model, second model, cheaper comparison model; show the excluded model as a text row with its price in a footnote only. Replace the two tables.

**G10. Error classes** (slide 39, optional). Horizontal stacked bar from `evaluation.heldout_v2.error_analysis.classes` grouped into "tool gap", "answer status", "retrieval", "reasoning", "scorer or label".

## 4. Title slide (slide 1)

Constraints: no logo or brand mark, text wordmark only. Author name on the slide. One-line pitch under 12 words.

**Option A: The number strip.**
- On slide: `LabourLens` (small label), author name "Mihir Khandekar", pitch "One question. Three published numbers. Which is right?" (9 words), and the three real unemployment figures as big numerals with their labels (G1 without the question).
- Visual: the three numerals counting up.
- Cost: low (reuse G1). Risk: repeats slide 3.

**Option B: The answer card (recommended).**
- On slide: pitch "Singapore labour statistics, answered with a source you can check." (10 words) in the headline position, `LabourLens` as small wordmark above, "Mihir Khandekar" and "GenAI Engineer assessment" below.
- Visual: one real answer card on the right: question "What was resident unemployment in 2026 Q2?", answer "2.9%, resident, seasonally adjusted [1]", citation chip "[1] MOM, resident unemployment rate, via data.gov.sg", status badge "Answered". Values from `summary.cards[0]`.
- Why: it shows the product and the citation behaviour in one glance, so slide 3 can introduce the problem without repeating the hook. Reuses the home page specimen styling.

**Option C: The pipeline strip.**
- On slide: `LabourLens`, "Mihir Khandekar", pitch "Ask a labour question. Get a cited answer or a refusal." (10 words).
- Visual: a four-box strip: Question, Search, Calculate, Cited answer, with MOM data and reports feeding in.
- Cost: medium. Risk: reads as architecture, which is the register the owner objected to.

Recommendation: B. Notes keep the keyboard help, the story and the one-sentence version (they are fine in notes).

## 5. Figure captions and takeaways that carry identifiers (rewrite when a figure appears on a face)

- `fig-graph` takeaway: "Two loops: evidence gathering ... Brass outlines mark the guards." -> "At most two search rounds and one repair."
- `fig-ladder` note: hit@k definition, "R2 and R3 may be optimistic" -> "Labels are AI drafts, so the gain may be overstated." (remove ids).
- `fig-progression` takeaway: "A2 ... A4 ... A5 ... planner v2" -> "Only the retrieval change moved accuracy."
- `fig-paired` takeaway and title: "r3 minus hybrid is ... not demonstrated", "Registered rule: inconclusive" -> removed from face (slide cut).
- `fig-e2efix`, `fig-postfix`: slide cut from face; titles stay for the appendix.
- `fig-threat-matrix` title: "N of M failed cases across K runs are poisoned-passage cases" -> hidden; slide title replaces it.
- `fig-review` takeaway: "30 are own verdicts and 95 agree with an AI suggestion" -> notes.
- `fig-mcp` title: "A client treats the 9-tool MCP server as untrusted and validates every result" -> hidden; caption above.

## 6. LLM tells to scrub

- Performative honesty and hedging: "I do not call it solved", "I would not call it a confirmed gain", "I would not claim that ...", "I do not claim it works in general", "honest" (`withSoWhat` of "wrong", "The same honesty applies..."), "honest measurement" (brief slide), "I state the missing ... as a limit", "weak evidence at best". On slides state the finding once, plainly ("The gain was three cases."). Keep the caveat in notes.
- Rule-of-three lists: "stale, off-topic and non-labour", "forecasts, causal claims, personal advice and open web research", "Cases, Baseline, Comparisons", "answer, abstain, clarify, refuse, ignore", "Decided / drafted / caught", "Window / Requests / Approved", "Statistics / Reports / A cross-source question". Use two items or one graphic.
- "Not X but Y" and negation pairs: "Not an ablation", "not a regression", "a tool gap, not retrieval", "A system that picks one ... gives an answer nobody can check", "not an unbiased estimate", "Out of scope by decision". Rewrite as a positive statement.
- Abstract nouns to remove from faces: framing ("How I framed it", "my framing"), contract ("The answer contract"), surface, "pre-registration", "selection bias", "provenance", "disambiguation", "stratified", "oracle", "judgement", "constraints".
- Mechanism titles: "Retrieval, written before any R1 or R2 number", "Agent end to end, not a timestamped pre-registration", "BM25 held-out run, written before the run", "The data came next, because the hypotheses depend...", "I climbed a ladder of retrievers", "I ran the work as gates: explore, compare, recommend, approve, implement, verify, document". All removed in section 2.
- Bridge sentences ("The next slide shows...", "Then I ran it once.", "So I put retrieval inside an agent and measured the whole.", "The reports needed the same care...", "With the data in place, I looked at it..."): all are `withSoWhat` lines. Delete all.
- Dashes: no em or en dashes were found in `slides.js`, `ch*.js` or `home.js` copy (checked). Keep it that way. Semicolons in titles ("...; gpt-5.6-luna showed no difference", "...; 223 remain AI drafts") become two short sentences or are cut.
- Hedge pile-ups to rewrite: "Held-out v2 ... The effect is 3 cases and the exact test gives p = ..., so I would not call it a confirmed gain" (title of 38 and its bullets), "T-I06 is one planted case, handled in one run and not the next for one model" (limits), "Costs are list-price estimates, and the AI judge shares a provider with the answer models".
- "I" as subject on titles: acceptable in a talk, but 14 titles begin with "I" ("I bounded", "I climbed", "I left out", "I chose", "I reviewed", "I ran"). Use noun phrases (section 2 titles).

## 7. Home page (`home.js`, `app.js`, `index.html`)

### Problems
- Brand mark: `app.js` `brandMark()` draws an SVG logo in the nav; `.brand-mark` and `.bm-*` in `components.css`; `.footer-brand .brand-mark` rule; `web/static/favicon.svg` (magnifier with chart line) is linked from `index.html`, `deck.html`, `workbench.html`. Remove `brandMark()` and its `add(brand, brandMark(), ...)` call (keep the text "LabourLens" only), delete the `.brand-mark`, `.bm-bg`, `.bm-ring`, `.bm-handle`, `.footer-brand .brand-mark` rules, and drop the `<link rel="icon">` lines and `favicon.svg`. `workbench-page.js` already uses text only.
- Author name appears nowhere on the home page. Add "Mihir Khandekar" in the hero (line under the lead) and in the footer.
- Hero lead is a feature list: "Cited answers to questions about Singapore unemployment, vacancies and retrenchments, Q1 2024 to Q2 2026." and the `heroHeadline()` loop for a one-word array is dead scaffolding (remove the `words`/`emphasised` machinery).
- Section titles are mechanism: "One bounded agent answers each question with three read-only tools", "The agent returns one of four statuses", "Five limits on what these results show". Subtitles state limits ("at most 6 tool calls in 2 evidence rounds, and one repair").
- Limits section has "T-I06", "corpus v1/v3", "held-out", "gold labels" (identifiers, see section 1). `limits()` item 3 is a hedge pile-up (two sentences, 40+ words).
- Fallback text "report.json did not load." exposes a filename; change to "The figures could not be loaded."
- Home also carries four large sections after the hero (how, outcomes, series explorer, sources, limits = five). Too many.

### Proposed outline (target: one screen of hero, three sections)
1. Hero
   - Wordmark: "LabourLens" (text, no mark).
   - Hero line (H1): "Singapore labour statistics, with a source for every number."
   - One sentence: "Ask about unemployment, vacancies and retrenchments, 2024 to 2026. Answers cite MOM data or say nothing is published."
   - By-line: "Built by Mihir Khandekar" (a GenAI Engineer assessment project).
   - Buttons: "Open the workbench" (`/workbench`), "Watch the presentation" (`/deck`).
   - Right side: keep the live specimen (latest figure, tile selector, small chart). It is real data and works.
2. "How an answer is made" (replace the four-item `dl`): a four-step strip, each step three or four words: Question, Search, Calculate, Cited answer. One caption: "Tools are read-only. Arithmetic is done in code."
3. "Four possible outcomes" (merge with 2 if space): one row of four badges (Answered, No answer, Needs clarification, Refused) with a 6-word line each. Button "Try an example question".
4. "The data" (keep explorer + sources as one section): title "Explore the data". Series picker + chart as today; replace the sources bezel by one sentence "85 source records from MOM and SingStat via data.gov.sg." Move the long licence sentence into the footer.
5. "Limits": keep as the last small section, 3 bullets, plain language (labels were drafted by an AI; the fresh-test gain is small; the attack scanner is weak). The `details` with all additional limitations stays.
Footer: "Statistics: Ministry of Manpower and Singapore Department of Statistics via data.gov.sg, under the Singapore Open Data Licence. MOM reports remain the Ministry's. A research prototype by Mihir Khandekar, not an official source."

Edits by line (home.js, current text -> new):
- Lead `el('p','lead', ...)` -> the one sentence in outline item 1; add `el('p','byline','Built by Mihir Khandekar')`.
- `section('how', 'One bounded agent ...', ...)` -> `section('how', 'How an answer is made', null)`; steps -> Question: "Checks the period and series are clear." Search: "Finds report passages and statistics." Calculate: "Changes are computed in code." Cited answer: "Every claim shows its source."
- `section('outcomes', 'The agent returns one of four statuses', ...)` -> `'Four possible outcomes'` with lede removed; bodies: "Answer with citations." / "The data does not cover it." / "The question has more than one reading." / "The request is out of scope, such as a forecast."
- `explorer` title 'Unemployment, vacancies and retrenchments by quarter' -> 'Explore the data'; lede -> 'Each series keeps its own population and adjustment.'
- `sources()` title `${n} source records, each with release stage and licence status` -> `${n} sources`; lede -> 'Advance and final releases are kept apart.'
- `limits()` title 'Five limits on what these results show' -> 'Limits'; items rewritten:
  1. "Most reference answers were drafted by an AI. I reviewed 45 of 268."
  2. "On fresh questions, filtering helped by a few cases only."
  3. "A planted wrong figure was caught once and missed once. The attack scanner is weak."
  4. "The live system uses a newer document build than most results."
  5. "Covers 2024 Q1 to 2026 Q2. No forecasts, no claims about causes."

## 8. Speaker notes

Notes may keep ADR/D-numbers, paths, commits and tags (owner allows). Fix only these: the title slide notes put the keyboard help first ("Keys: arrows...") which is fine for the presenter but should be last; several notes begin "This is ..." or "Recorded in docs/..."; the final-slide note repeats the build provenance. The `qa()` strings ("Likely question: ... Model answer: ...") are good practice; keep. When a slide is merged, move the notes of the merged slides into the survivor so nothing is lost. Appendix slides keep their identifiers.

## 9. Order of work for the builder

1. Remove brand mark, favicon links, add author name (home, title slide, footer).
2. Replace titles per section 2 (set `title:` after each `...figSlide(...)`), delete `withSoWhat` lines, convert `rows()` slides to bullets within budget.
3. Delete the cut slides and move their text to the notes of the survivor or the appendix.
4. Add CSS to hide `.pr-fig-title`/`.pr-fig-note` in the deck; relabel ladder and agent figures per the vocabulary map.
5. Build G1, G5, G6, G7, G9 first (highest value); G2, G3, G4, G8, G10 next.
6. Title slide Option B.
7. Rewrite home page per section 7.
8. Run the existing deck checks and check no face text contains `ADR`, `D-0`, `R0..R3`, `A1..A5`, `X1`, `X2`, `T-I06`, `.js`, `.md`, `report.json`, a commit hash (a grep over rendered slide text, excluding `.notes` and the appendix).
