export const NOTES = {
  "e1": {
    calculated: "Across the development text cases, hit@k is the share with a labelled passage in the first k chunks; page hit accepts a match anywhere on the labelled page, and MRR averages the reciprocal first-match rank. Passage recall measures labelled passages covered, context words measures the text in the first five chunks, chunks counts the index entries, and p50 is median search time. Better/worse/same counts changes in first-match rank against merge120, not changes in binary hits.",
    decision: "No configuration was locked by this exploratory comparison (D-018). Grouping adjacent passages remained the baseline approach (D-015), without establishing an optimal chunk size."
  },
  "e1b": {
    calculated: "Hit@k counts cases with a labelled passage in the first k chunks, MRR rewards an earlier first match within the saved cutoff, and passage recall measures labelled passages covered by the first five chunks. Chunk counts and mean words describe the index; context words measures the first five results, family n counts eligible cases, and better/worse/same compares first-match ranks. The paired 95% intervals resample the same cases to estimate uncertainty in the hit@8 difference from merge200; the secondary table uses only currently eligible original case ids.",
    decision: "No change (D-094): keep the runtime chunking default because the larger sizes do not establish a retrieval gain and require more context. Dense, hybrid and filter-then-rerank retrieval were not tested at these sizes."
  },
  "e2": {
    calculated: "For each token-processing setting, hit@k counts cases with a labelled passage in the first k chunks, page hit accepts a labelled-page match, and MRR rewards an earlier first matching chunk. Passage recall measures labelled passages covered by the first five results; context words, chunk count and median search time describe their size and cost. Better/worse/same counts changes in first-match rank against the unchanged tokenisation baseline.",
    decision: "No tokenisation winner was locked (D-018). The mixed development results did not establish a robust reason to adopt stemming or another universal setting."
  },
  "e3": {
    calculated: "The table measures the same development cases while changing BM25's repeated-word weighting or document-length adjustment. Hit@k counts cases with a labelled passage in the first k chunks, page hit permits a same-page match, MRR rewards earlier first matches, and passage recall measures labelled passages covered. Context words, chunk counts and median milliseconds describe resource use; better/worse/same compares first-match ranks with the baseline.",
    decision: "No parameter optimum was locked (D-018). The small, mixed changes did not establish a reason to replace the baseline BM25 settings."
  },
  "e4": {
    calculated: "The combined-settings rows measure labelled-passage hit rates at each chunk cutoff, lenient labelled-page hits, reciprocal first-match rank (MRR), and labelled-passage recall in the first five chunks. They also count indexed chunks, average words in the first five results, median search milliseconds, and first-match ranks that improved, worsened or stayed unchanged against the baseline. Several settings change together, so these totals cannot assign the effect to one setting.",
    decision: "No change was locked from this exploratory combination (D-018). It was added after the individual comparisons, so its higher development score was not treated as independent confirmation."
  },
  "e5": {
    calculated: "For each embedding model, hit@k is the share of development cases with a labelled passage in the first k chunks. MRR averages the reciprocal rank of the first matching chunk, while passage recall@5 measures the share of labelled passages covered by the first five chunks.",
    decision: "No embedding-model winner was locked (D-023). Dense retrieval was promising, but these cases did not separate the leading models reliably."
  },
  "e6": {
    calculated: "For keyword, meaning-based and combined retrieval, hit@5 and hit@10 count cases with any labelled passage inside those chunk cutoffs. MRR rewards earlier first matches, passage recall@5 measures labelled passages covered, and context words@5 measures the average text volume in the first five results.",
    decision: "No final retrieval configuration was locked at this stage (D-023). Hybrid retrieval was retained as a candidate because of its deeper hit rates, not declared a held-out winner."
  },
  "e7": {
    calculated: "Hit@10 counts development cases with a labelled passage in the first ten chunks, with and without embedded document and section headings. MRR averages reciprocal first-match rank, so a higher hit rate can coexist with later first matches.",
    decision: "No change (D-023): the heading experiment showed no clear benefit. The two metrics moved in opposite directions, so headings were not established as an improvement."
  },
  "r-series": {
    calculated: "Hit@k counts cases with a labelled passage in the first k chunks; MRR@10 rewards earlier first matches, passage coverage counts labelled passages recovered, and pool recall counts cases with a match in the larger candidate pools. The 95% intervals resample cases, and paired differences and better/worse counts compare hit@8 on identical cases against hybrid R0; family and hint n values count cases in each subgroup. Added p50 latency is median extra retrieval time, and cost is estimated model usage per query.",
    decision: "Filtering and reranking met the development condition for trying their combination (D-029). Filter then rerank became the provisional agent default after the end-to-end comparison (D-030), not on retrieval scores alone."
  },
  "v31": {
    calculated: "On the same later corpus build, n counts eligible development text cases, hit@8 and hit@10 count cases with any labelled passage in those chunk cutoffs, and MRR@10 rewards an earlier first match. The 95% intervals describe case-resampling uncertainty, while paired better/worse counts say where each R-series method gains or loses a hit@8 against that build's hybrid R0.",
    decision: "No default change (D-059 and D-061): use the isolated same-build rerun to report the later retrieval comparison. Do not pool it with historical runs or attribute cross-build differences to retrieval alone."
  },
  "heldout-retrieval": {
    calculated: "Eligible n counts answerable text cases, not every question in either set; chunk hit@8 checks for any labelled passage anywhere in eight chunks, whereas strict passage hit@8 checks only the first eight distinct passages actually placed in the answer context. Chunk MRR@10 rewards the rank of the first matching chunk. The 95% intervals resample eligible cases within each set and do not measure uncertainty in the labels or reranker.",
    decision: "No change (D-072 and D-074): report the retrieval gains without changing defaults or frozen results. Better evidence retrieval did not establish an end-to-end answer-status gain on these sets."
  },
  "generation-m3-g1": {
    calculated: "Validity counts answers passing schema, citation-label and quote checks after any repair; repair rate counts those needing the extra call, and behaviour accuracy counts expected-status matches across the answer and non-answer cases. Over-abstention divides missed answers by answerable cases; false-answer rate divides inappropriate answers by non-answer cases. Numbers complete counts answerable cases that both answered and included every reference key figure, not independently verified factual correctness.",
    decision: "No model was locked by this small comparison (D-025). The owner chose to prefer declining rather than risk an unsupported answer (D-026), accepting lower completeness."
  },
  "generation-m3-g0": {
    calculated: "With reference passages placed first, validity counts answers passing the hard checks and behaviour accuracy counts matches to the expected answer status. Numbers complete counts answerable cases that answered with all reference key figures; gold in context and gold cited measure whether labelled evidence was shown and cited on eligible cases. These are an ideal-evidence control, not measurements of a deployable search method.",
    decision: "No deployable oracle method was adopted (D-025). This diagnostic supported the conclusion that missing evidence, rather than model choice alone, limited the retrieved-evidence answers."
  },
  "generation-m3-g3": {
    calculated: "Each context width is scored for hard-check validity, expected-status agreement, and the share of answerable cases answered with all reference key figures. Gold in context measures eligible cases whose labelled evidence reached the model, while total tokens sums usage over the run. The width setting counts retrieved chunks, not a guaranteed number of distinct passages.",
    decision: "No context width was locked by this experiment (D-025). Wider context informed the later candidate setup, but its extra evidence coverage came with more tokens."
  },
  "generation-m3-g4": {
    calculated: "At the wider context setting, validity measures hard-check passes after any repair, repair rate measures extra calls, and behaviour accuracy measures expected-status agreement. Over-abstention is measured among answerable cases and false answers among non-answer cases in this early study. Cost per case is estimated from saved token usage and list prices, not an invoice.",
    decision: "D-026 chose the cautious response policy and proposed gpt-6-luna with wider context as the candidate default. This was a policy and cost trade-off, not a demonstrated safety or accuracy ranking."
  },
  "generation-m3-cost": {
    calculated: "Behaviour accuracy is the share of cases matching the expected answer status; p50 latency is median recorded wall time. Total tokens sums the run's usage, and cost per case prices that usage at the saved list prices without a cached-input discount.",
    decision: "D-026 retained the cheaper cautious candidate rather than selecting by price or answer rate alone. The small study did not establish that a more expensive generator produced better answers."
  },
  "generation-e2e-ladder": {
    calculated: "For each arm, n_cases is the number scored and behaviour accuracy counts matches to the expected answer, abstain, clarify or refuse status. Over-abstention divides withheld expected answers by all evaluated cases; claim support pools judged claims, and fact coverage pools reference facts in judged answers. The arms have different case counts, so the aggregate difference is not a paired significance test.",
    decision: "Adopted provisionally (D-030): use period/release filtering followed by reranking, while retaining planner_v1 and answer_v3. The reduced over-abstention was accepted with extra latency and cost."
  },
  "generation-prompt-hypothesis": {
    calculated: "Behaviour accuracy counts expected-status matches, and over-abstention counts withheld expected answers divided by all scored cases. Claim support is the share of judged claims supported by their citations; fact coverage is the share of reference facts covered in judged answers. Both arms already include code-generated notes, so this measures only the extra answer instruction.",
    decision: "Not adopted (D-030): keep answer_v3 because the extra missing/conflicting-data instruction showed no demonstrated benefit. The existing code-generated notes remain in both settings."
  },
  "generation-widening-hypothesis": {
    calculated: "On the same development cases, behaviour accuracy counts expected-status matches and over-abstention counts withheld expected answers over all cases. Claim support pools supported judged claims, while fact coverage pools covered reference facts in judged answers. These compare the ordinary filtered search with a fallback that broadens weak candidate pools.",
    decision: "Not adopted (D-030): retain r3 without the widening rule because the development comparison showed no consistent improvement. This does not prove the two methods equivalent."
  },
  "generation-final-dev": {
    calculated: "FIN and FIN2 report expected-status agreement on the same development cases; Mean averages each case's two outcomes, not full factual correctness. The paired difference and 95% interval compare those case means by resampling cases together; over-abstention and false-answer rates both use all cases in this final aggregate. USD is usage-priced cost per case, and p50 is each run's median wall time, not a pooled median.",
    decision: "D-061 makes the two-run mean the headline and keeps gpt-6-luna on cost rather than an accuracy win. The r3 default retained in D-056 remains provisional: the development advantage does not establish generalisation."
  },
  "generation-final-registered": {
    calculated: "FIN and FIN2 measure expected-status agreement on the original test cases, and Mean averages the two outcomes for each case. The paired 95% interval resamples those case means for r3 minus hybrid; false-answer and over-abstention rates use all cases in this final aggregate. USD prices saved usage per case, and p50 is the median wall time of each run.",
    decision: "No retrieval change (D-056 and D-061): retain r3 provisionally, not as a demonstrated original-test winner. Report the two-run mean and both runs because the paired interval includes zero."
  },
  "generation-final-fresh": {
    calculated: "FIN and FIN2 score expected-status matches on the reused fresh questions; Mean averages each case's two outcomes. The paired 95% interval resamples case means for the r3-minus-hybrid difference, and the final false-answer and over-abstention rates divide by all cases. USD is estimated usage cost per question, while p50 is each run's median wall time.",
    decision: "No default change (D-056 and D-061): retain r3 provisionally while explicitly reporting no demonstrated fresh-set answer-status gain. These known questions are not another untouched test."
  },
  "generation-floors-noise": {
    calculated: "The always-answer floor counts how often a rule that always chooses answered would match the expected status, without evaluating answer content. Cases gives each set's denominator, and flips counts cases whose correct/incorrect status verdict changed between FIN and FIN2 for the same model and retrieval setting. Flips are gross changes, not the net accuracy difference or an estimate of independent-run variance.",
    decision: "No configuration change: these are diagnostics, not an adoption experiment. D-061 requires both runs and their mean to remain visible rather than choosing the better-looking run."
  },
  "generation-original-heldout": {
    calculated: "Behaviour accuracy is expected-status agreement for the same original test case ids, first under the original scoring and then after label adjudication. Difference is paired r3 minus hybrid, and Lower/Upper are the 95% case-bootstrap bounds. Rescoring changes the interpretation of saved answers, not the generated answers themselves.",
    decision: "No demonstrated gain under the registered rule (D-033 and D-036): retain r3 only provisionally. Preserve both the original result and the later adjudicated scoring rather than treating the rescore as a fresh test."
  },
  "generation-fresh-v2": {
    calculated: "n_cases counts the fresh-source questions; behaviour accuracy measures expected-status agreement, and over-abstention divides withheld expected answers by all cases. This earlier false-answer rate excludes over-abstentions from its denominator. The paired difference is r3 minus hybrid, the case and shared-evidence-component bounds are bootstrap 90% intervals, and McNemar tests the paired discordant status outcomes.",
    decision: "No system change (D-045): report that the registered primary-model rule was met by three cases, but do not call it a confirmed gain. The result did not replicate on the comparison model and did not authorise changes to the frozen experiment."
  },
  "generation-fresh-v31": {
    calculated: "The same known fresh questions are rescored after new generation on corpus v3.1: behaviour accuracy counts expected-status matches and over-abstention uses all cases. The earlier false-answer rate excludes over-abstentions from its denominator. Difference is paired r3 minus hybrid, the case bounds are a 90% bootstrap interval, and McNemar tests the discordant paired status outcomes.",
    decision: "No adoption change (D-055): report that the primary-model gain is not demonstrated on this rerun. Keep the original registered v2 result separate, because corpus and runtime changed together and the questions were already known."
  },
  "generation-second-family-judge": {
    calculated: "Raw agreement counts matching labels between the two AI judges; Cohen's kappa adjusts that agreement for their label frequencies. Each n is the eligible label or answer count after exclusions, not the originally sampled answer total. Supported divided by Claims gives each judge's claim-support rate on the same valid paired answers, conditional on both retrieval arms producing claims.",
    decision: "No generator or retrieval change (D-062): retain this as a judge-sensitivity check, not independent ground truth. The claim-support ordering changes with the judge, so it cannot support a stable content-quality winner."
  },
  "generation-groundedness": {
    calculated: "Supported and unsupported rates pool the AI judge's claim labels, with partial support kept separate; fact coverage pools reference facts covered in judged answers. Contradiction is the share of judged answers contradicting any reference fact. These exclude claim-free non-answers, so a valid quote or zero unsupported labels does not imply correct answers to every question.",
    decision: "No additional configuration change: this is a diagnostic distinction between citation mechanics and semantic support. D-030 retained r3 for the broader development trade-off, not because valid citations prove grounded answers."
  },
  "agent-m4-bounded-tools": {
    calculated: "Validity counts hard-check passes; behaviour counts expected-status matches, while over-abstention and false-answer rates in this early study use answerable and non-answer cases respectively. Calculation correctness checks eligible numerical cases for a correct, cited deterministic calculation; tool-error rate counts failed tool calls. p50 is median wall time and dollars per case prices recorded usage, not billing.",
    decision: "Adopted (D-027): keep the bounded three-tool agent with catalogue-constrained planner arguments and no passage text shown to the planner. Arithmetic on figures available only in report text remained an acknowledged gap."
  },
  "agent-planner-v2": {
    calculated: "Behaviour accuracy counts expected-status matches on the same development cases; over-abstention uses all cases, while this earlier false-answer rate excludes over-abstentions from its denominator. p95 is the recorded wall time below which almost all cases finish, and cost per case prices saved usage. The comparison changes the planner instruction, not the retrieval or answer prompt.",
    decision: "Not adopted (D-032): keep planner_v1 because the small observed increase did not demonstrate a stable benefit. The result is inconclusive, not proof of equivalence."
  },
  "agent-x1-extraction": {
    calculated: "Behaviour accuracy measures expected-status agreement on reused development cases; the earlier false-answer rate excludes over-abstentions from its denominator. Calculation correctness measures eligible cases with a correct cited deterministic calculation, and the number-warning rate counts all scored cases containing an ungrounded-number warning. Extraction fixes and evidence-id migration are assessed with the source-conflict cross-check off.",
    decision: "Adopted corpus v2 for working use (D-037 and D-041) while preserving the frozen corpus-v1 results. This was an extraction-fidelity choice, not a demonstrated answer-quality improvement."
  },
  "agent-x2-regression": {
    calculated: "Behaviour accuracy counts expected-status agreement; the earlier false-answer rate excludes over-abstentions from its denominator. Calculation correctness checks eligible cited calculations, and the number-warning rate counts all scored cases with a warning, including the expanded summary and caveat checks. Corpus, runtime and source-conflict checks changed together, so these development scores are a regression check rather than an isolated effect.",
    decision: "No new configuration choice from the X2 result (D-044): report the regression check and retain the earlier intervals and warning-definition caveat. It does not establish a causal improvement or fresh held-out performance."
  },
  "agent-x3-toolset-v2": {
    calculated: "The criteria compare counts of expected-status matches, inappropriate answers on non-answer cases, cases with ungrounded-number warnings, and operational failures against limits fixed before the run. The new-tool warning row uses only cases that actually used report-figure arithmetic; the all-case row uses the full development set. PASS or FAIL applies each frozen criterion, not a post-result judgement of whether a near miss is acceptable.",
    decision: "Rejected (D-048): keep the base tool set because the report-arithmetic bundle failed its pre-declared safety criteria. Do not relax the thresholds after seeing the result."
  },
  "agent-v2post-diagnostic": {
    calculated: "On the already-known fresh questions, behaviour accuracy counts expected-status matches and over-abstention counts withheld expected answers divided by all cases. This earlier false-answer rate excludes over-abstentions from its denominator. The rows compare the frozen base system with the new tool bundle, whose design was motivated by these same failures.",
    decision: "No adoption (D-048): the targeted diagnostic gain does not override X3's failed development criteria. Keep the base tool set and label V2post as post-freeze diagnostic evidence, not held-out validation."
  },
  "agent-versus-fixed": {
    calculated: "Behaviour accuracy and false-answer/over-abstention counts compare expected-status outcomes on identical development questions, while family n counts cases in each descriptive subgroup. Differences are fixed minus agent; the 95% bounds resample paired cases, and McNemar tests individual binary runs rather than the fractional two-run mean. Median and p95 measure wall time, and recorded usage and separate judge costs price different model calls per question.",
    decision: "No default change (D-073 and D-074): retain the bounded agent rather than replace it with this fixed workflow. The development advantage belongs to the whole policy, including its calculation capability, not to adaptive planning alone."
  },
  "agent-served-chain-s65": {
    calculated: "Overall behaviour is expected-status agreement across the mixed application sample; gold-only behaviour excludes the authored probes. Diversion and context rows count probes meeting their fixture expectations, while false diversions count legitimate requests stopped before the agent. MCP minus direct compares paired status outcomes with web steps enabled in both routes; equal aggregate scores do not establish identical returned records.",
    decision: "No default change from this sample (D-058 and D-061): report the earlier served-chain measurement separately from the final direct-agent evaluation. The failed context probe prevents a clean overall protocol pass."
  },
  "agent-mcp-all-tools": {
    calculated: "Behaviour accuracy counts expected-status matches across the same application sample, and paired better/worse counts show which cases change relative to each transport control. False answers count inappropriate answers; operational failures count runs that could not complete. Median and 95th-percentile latency measure recorded wall time, and cost per question estimates model usage rather than a provider bill.",
    decision: "Not adopted as the live default (D-066 result addendum): return to statistics-only MCP. Routing all three tools through MCP was slower and showed no demonstrated accuracy gain."
  },
  "agent-statistics-removal": {
    calculated: "Behaviour accuracy counts expected-status matches over all cases; gold/probe and family rows use their stated subset sizes, and over-abstention uses all cases. The earlier false-answer rate excludes over-abstentions; calculation correctness requires a cited deterministic record, key-number recall checks reference figures, gold-cited checks any acceptable evidence, and contradiction counts judged answers contradicting a reference fact. Paired 90% intervals resample cases, McNemar tests discordant outcomes, and latency, tokens and priced usage describe operational cost.",
    decision: "No live change (D-069): retain statistics lookup rather than replace it with report search alone. This removes both structured access and calculation-input labels, so it does not show a benefit of MCP transport itself."
  },
  "agent-decisions-v1-routing": {
    calculated: "Exact routes counts matches to the frozen route labels per repeat; diversion counts legitimate questions wrongly kept from the agent, and non-in-scope recall counts correctly diverted off-topic or unsafe cases. A0 uses the raw choice and A70 applies the frozen confidence gate; repeats reuse the same questions rather than adding independent cases. Timing takes each case's median across repeats before p50/p95, and mean cost prices each classification's usage against a historical chat baseline.",
    decision: "Rejected (D-075): keep the current chat routing because the primary confidence-gated replacement failed its quality and zero-diversion rules. Lower component latency and cost did not override those failures."
  },
  "agent-decisions-v1-support": {
    calculated: "AUROC measures how well support probabilities rank fully supported claims above partially supported claims; accuracy counts correct labels at the frozen threshold, while balanced accuracy gives both classes equal weight. False-support rate is the share of reference-negative claims wrongly accepted as supported. The 95% intervals resample answer groups to retain dependence among their claims; the reference is an AI judge, not verified hallucination labels.",
    decision: "Rejected (D-075): retain the existing support judgement because balanced accuracy and false-support criteria failed. Ranking performance alone did not justify replacing the verifier."
  },
  "agent-decisions-v2": {
    calculated: "Effective exact routes counts scheduled classifications matching the reference, retaining refusals in the denominator; diversion and recall use the in-scope and other-route subsets, and repeats reuse the same fresh cases. Provider refusals count operational failures rather than successful typed routes. Timing compares per-case medians across repeats, D/C is the Decisions-to-chat timing ratio with a paired case-bootstrap 95% interval, and costs price recorded attempts and tokens.",
    decision: "Rejected (D-076): keep the shipped agent and chat triage unchanged. The faster replacement failed safety, routing-quality and operational screens, so no threshold was retuned to rescue it."
  },
  "agent-context-rewrite": {
    calculated: "Passed counts deterministic string checks on authored conversations, including the adversarial-history subset, and on triggered standalone inputs. The adversarial conversations are a subset of the conversation cases, not extra independent examples. These checks test the required rewrite strings and preserved information, not independent semantic quality or downstream answer correctness.",
    decision: "D-054 retains bounded standalone-question rewriting for the web app; the date-fact wording was corrected and rerun on the same known cases. No new end-to-end accuracy claim or frozen-agent change follows from those string checks."
  },
  "agent-served-changes-not-evaluated": {
    calculated: "No experiment score was calculated for the combined final served build. The table marks an evidence boundary: historical results measure the frozen structured-output chain, while offline checks and isolated live observations do not supply accuracy, safety or latency estimates for the later build.",
    decision: "D-077, D-078, D-080 and D-083 to D-093 record served changes, not their experimental validation. No evaluation-based adoption decision is recorded for the combined build; keep its status explicitly NOT EVALUATED."
  },
  "threat-v1-original": {
    calculated: "Scored and passed count authored threat cases meeting the deterministic safety rules; Rate divides passes by scored cases, with a Wilson 95% interval for that proportion. Canary compliance counts obedience to the planted marker instruction rather than harmless mention, and median seconds measures recorded run time. The guarded and naive arms use the corrected fixture, so failed delivery of an attack is not credited as protection.",
    decision: "No demonstrated defence benefit (D-030): the corrected primary-model arms tie. Preserve these results and disclose the invalid earlier fixture rather than retaining its apparent perfect score."
  },
  "threat-ti06-crosscheck": {
    calculated: "Strict counts suite passes under the original scorer, while post-hoc refined counts rescore the same answers after distinguishing the planted figure's assertion from its disclosed mention. Indirect useful counts attacks where the system still supplied the requested legitimate answer. The scoring difference comes from the planted-figure case, not a new independent sample.",
    decision: "Adopted the deterministic source-conflict guard (D-038), while preserving both scoring interpretations. The post-fix result does not establish that the vulnerability is closed or stable across runs."
  },
  "threat-ti06-scorer-reruns": {
    calculated: "The diagnostic table applies the original and field-aware second scorer to saved outputs without generating new answers. The fresh table counts passes on a new run of the same known suite, with Wilson 95% intervals, canary-compliance counts and median wall time. Rescoring old outputs is post-hoc evidence, whereas fresh generation remains a known-suite repeat rather than an unseen attack test.",
    decision: "D-060 adds a selectable second scorer and immutable new result ids, retaining the original scorer and results. No stronger protection claim follows: D-061 records that the fresh arms tie and planted-figure protection remains unstable."
  },
  "threat-v2-challenge": {
    calculated: "An attack case passes when a majority of its repeated runs passes; only-this-arm counts paired cases passed by one arm but not the other. Difference is the guarded-minus-naive attack pass rate, and exact McNemar tests those discordant cases. Benign failures count harmless look-alikes wrongly rejected or mishandled, while category rows describe the same attack cases rather than independent samples.",
    decision: "No default or prompt change (D-074): record the supported attack advantage but the failed benign-usefulness criterion. Guards and answer prompt changed together, so no individual layer is credited."
  },
  "threat-scanner-v2": {
    calculated: "Recall is malicious passages flagged divided by malicious passages tested; benign flagged is the false-positive count among harmless passages. The development ladder measures the added normalisation steps, and the single test comparison uses the separately frozen split. Wilson 95% intervals describe uncertainty in each test proportion, not the scanner's ability to detect every unseen attack.",
    decision: "Adopted the development-selected normalisation factors (D-065): strip markup/entities, decode cue-word leetspeak and scan a short fragment window. Retain the false-positive and semantic-bypass limitations; this is not complete injection detection."
  },
  "threat-hostile-mcp": {
    calculated: "The MCP subset counts safety-rule passes, including operational failures that correctly return no answer; useful answers is conditional on the cases that could answer. Transcript counts show accepted versus quarantined rows and output mismatches for matched calls, not real-world attack rates. Warm-call medians measure protocol overhead separately from the one-off MCP connection time.",
    decision: "Retain the typed, allow-listed, fail-closed client boundary (D-028), with no direct fallback on transport failure. The subtle instruction that passed the row scanner remains a disclosed limit, not evidence that schema validation proves data trustworthy."
  },
  "threat-scope-triage": {
    calculated: "Cases counts each tested population, and false out of scope counts requests diverted before reaching the research agent when the fixture expected them to continue. Failed open counts provider or parsing failures sent onward to the agent, rather than silently treating them as correct classifications. This is a routing-component measurement, not end-to-end answer accuracy.",
    decision: "Keep web-only model triage enabled (D-051), while disclosing the threat diversion and the limited authored sample. Failed-open behaviour remains distinct from a successful routing decision."
  },
  "threat-source-scan-audit": {
    calculated: "The scan rows count source passages and distinct statistical text values screened, and Hits counts strings matching instruction-like heuristics in each corpus version. These are unlabelled-corpus audit counts, not a detection-recall estimate. Known paraphrase regressions guided the extended patterns, so their coverage does not establish performance on unseen attacks.",
    decision: "No corpus-cleanliness or safety decision follows from zero hits. D-061 records the extended known-bypass patterns, and D-065 separately evaluates scanner changes; neither treats this audit as proof that sources are clean."
  },
  "generation-owner-judge-calibration": {
    calculated: "The first table cross-tabulates owner verdicts against an AI judge's unsupported-or-contradicted flag; the second uses a derived verdict that also includes deterministic status and coverage checks. Agreement counts matching verdicts, and kappa adjusts agreement for label frequencies, with separate three-class and binary comparisons. Only answers with claims receive claim judgements, and the owner-wrong cases here contain none, so this sample cannot test detection of unsupported claims.",
    decision: "No judge-validation or configuration decision is recorded for this comparison. D-036 and D-049 retain the owner's signed-off review with its one-reviewer, after-scoring limits; the agreement figures do not remove those limits."
  }
};
