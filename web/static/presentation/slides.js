// The deck: every slide is declared here as data. Charts and tables are the ones the chapter
// modules already draw from report.json; this file picks them out of an off-screen pool, gives each
// slide an action title and at most three bullets, and moves the detail into speaker notes or the
// appendix. Numbers on slides come from report.json (through the model) or from the document named
// in the slide's source line. Text is set with textContent only.
import {el, fmt, finite} from '../charts.js';
import {model, metricOf, goldOf, contextSentence} from './model.js';
import {stat, textStat, countRunner, dataTable} from './ui.js';
import {threeAnswers, twoSources, buildTimeline, flattening, mcpMap, retrievalStaircase, experimentStaircase, agentLoop, assignmentBrief, challengeGrid, architectureDiagram, myProject, hardParts, keywordVsMeaning, modelChoice, RESPONSIBLE_AI, HYPOTHESES, contentMetricsText, workbenchShot, conceptGrid, threatLayerTable, threatRuns, buildProcess, rowsAffordance, finalComparison, finalFacts, finalSentence, finalCostFacts, provenanceTable, secondJudgeFacts, secondJudgeNote, secondJudgeQa, secondJudgeSentence, SUPPORT_LABEL} from './graphics.js';
import {retrievalTuning, metricComparison, threatComparison, unseenRetrieval, retrievalLadder, agentOverview, fixedPipeline, assumptionsScope} from './graphics.js';
import {exampleRuns, answerChecks, evaluationDesign, threatGains, nextSteps, improvementPlan} from './graphics-flows.js';
import {agentSummary} from './graphics.js';
import {decisionsExperiment} from './graphics.js';
import {productionArchitecture} from './production.js';
import {failureResults, FAILURE_NOTES} from './failure-results.js';
import {renderScope} from './ch1-scope.js';
import {renderData} from './ch2-data.js';
import {renderRetrieval} from './ch3-retrieval.js';
import {renderAgent} from './ch4-agent.js';
import {renderEvaluation} from './ch5-evaluation.js';
import {renderSafety} from './ch6-safety.js';
import {renderMcp} from './ch7-mcp.js';
import {renderLimits, renderNext, renderSummary} from './ch8-limits.js';
import {renderWork} from './ch-work.js';
import {renderServing} from './ch-serving.js';
import {evaluationNotices} from '../evaluation.js';

const pct = v => fmt.pct(v);
const text = (node, selector) => node?.querySelector(selector)?.textContent?.trim() || '';
const figTitle = fig => text(fig, '.pr-fig-title');
const figTakeaway = fig => text(fig, '.pr-fig-takeaway');
const figSource = fig => text(fig, '.pr-source code').replaceAll(' · ', '; ');
const figFiles = fig => text(fig, '.pr-source .pr-evi');
const figNote = fig => text(fig, '.pr-fig-note');
const take = (root, selector) => { const node = root?.querySelector(selector) || null; node?.remove(); return node; };
const takeAll = (root, selector) => [...(root?.querySelectorAll(selector) || [])].map(node => { node.remove(); return node; });
const missing = what => el('p', 'deck-missing', `${what} is not available in the report data.`);
const list = (items, cls = 'deck-list') => { const ul = el('ul', cls); items.forEach(item => ul.append(el('li', '', item))); return ul; };

/** A headline number. Counts up on entry when it has a numeric value; `morph` pairs it with the same id on the next slide. */
function bigStat({value, format = fmt.int, text: fixed, label, note, size = 'm', morph}) {
  const root = el('div', `deck-stat is-${size}`);
  const number = el('div', 'deck-num num');
  if (finite(value)) number._run = countRunner(number, value, format);
  else number.textContent = fixed ?? 'not recorded';
  root.append(number, el('p', 'deck-stat-label', label));
  if (note) root.append(el('p', 'deck-stat-note', note));
  if (morph) root.dataset.morph = morph;
  return root;
}

function renderPool(m, ctx) {
  const roots = {};
  const run = (key, render) => {
    try { roots[key] = render(m, ctx); } catch (error) {
      console.error(`presentation chapter ${key}`, error);
      roots[key] = el('section');
    }
  };
  run('scope', renderScope); run('data', renderData); run('retrieval', renderRetrieval); run('agent', renderAgent);
  run('evaluation', renderEvaluation); run('safety', renderSafety); run('mcp', renderMcp); run('serving', renderServing); run('limits', renderLimits);
  run('next', renderNext); run('work', renderWork); run('summary', renderSummary);
  return roots;
}

/** All slide specifications, in presentation order. */
export function slideSpecs(report) {
  const m = model(report);
  const ctx = {disclosures: evaluationNotices(report)};
  const c = renderPool(m, ctx);
  const chapterTitle = key => text(c[key], '.pr-chapter-title');
  const chapterBullets = key => [...(c[key]?.querySelectorAll('.pr-lede li') || [])].map(li => li.textContent);
  const fig = id => {
    for (const root of Object.values(c)) { const node = root.querySelector(`#${id}`); if (node) { node.remove(); return node; } }
    return null;
  };
  const figSlide = (id, extra = {}) => {
    const f = fig(id);
    return {title: figTitle(f) || extra.title, visual: f || missing(extra.title || 'This chart'), srcPath: figSource(f), source: extra.human || '', notes: [...(extra.notes || []), figTakeaway(f), figNote(f), `Source: ${figSource(f)}. ${figFiles(f)}`.trim()].filter(Boolean), bullets: extra.bullets, ...(extra.rest || {})};
  };

  const L = m.ladder?.configs;
  const a3 = m.evalRow('dev-A3', 'gpt-6-luna'), r3 = m.heldRow('r3', 'gpt-6-luna');
  const dev = metricOf(a3?.metrics?.behaviour_accuracy), held = metricOf(r3?.metrics?.behaviour_accuracy);
  const pair = m.paired[0]?.models?.['gpt-6-luna'];
  const luna = m.securityRow('gpt-6-luna')?.metrics;
  const mcp = m.section('mcp'), mx = mcp.metrics || {};
  const mcpLat = (mcp.rows || []).find(r => r.metric === 'latency_p50_ms') || {};
  const a1row = m.evalRow('dev-A1', 'gpt-6-luna');
  const overA1 = metricOf(a1row?.metrics?.over_abstention_rate), overA3 = metricOf(a3?.metrics?.over_abstention_rate);
  const serving = m.section('serving'), tri = serving.triage || {}, triCl = tri.cost_and_latency || {};
  const quality = m.section('quality').metrics || {};
  const types = m.section('sources').metrics?.by_type || {};
  const nQ = m.periods().length;
  const to = m.scope[1];
  const hitNow = L ? L.R3['hit@8'] : null, hitBase = L ? pct(L.R0['hit@8']) : 'the baseline';
  const specs = [];
  const add = (spec) => specs.push(spec);

  // ---------- story helpers ----------
  const rows = (items) => {
    const ul = el('ul', 'deck-limit-rows');
    items.filter(Boolean).forEach(([head, body]) => { const li = el('li'); li.append(el('strong', '', head), el('span', '', body)); ul.append(li); });
    return ul;
  };
  const two = (leftTitle, left, rightTitle, right) => {
    const wrap = el('div', 'deck-two2');
    [[leftTitle, left], [rightTitle, right]].forEach(([t, items]) => { const col = el('div', 'deck-col'); col.append(el('h3', '', t), list(items, 'deck-list')); wrap.append(col); });
    return wrap;
  };
  const findings = [...(c.data.querySelectorAll('.pr-finding') || [])].map(li => ({head: text(li, 'strong'), body: text(li, 'span')}));
  const v2 = m.section('evaluation').heldout_v2;
  const v2p = v2?.paired?.['gpt-6-luna'], v2q = v2?.paired?.['gpt-5.6-luna'];
  const v31 = m.heldoutV31, v31p = v31?.paired?.['gpt-6-luna'], v31q = v31?.paired?.['gpt-5.6-luna'];
  const ff = finalFacts(m), ffSet = id => ff?.sets.find(s => s.id === id), ffModel = (id, model) => ffSet(id)?.models.find(x => x.model === model);
  const ffCost = finalCostFacts(m);
  const exact = (share, n) => Math.round(share * n) / n;
  const pctN = (share, n) => fmt.pct(n ? exact(share, n) : share);
  const work = m.section('work');
  c.work._blocks = [...(c.work?.querySelectorAll('.pr-block') || [])];
  const card0 = m.cards.find(x => x.card_id === 'unemployment_resident_sa') || m.cards[0];

  // ---------- opening ----------
  add({
    layout: 'title', chapter: 'Start', title: 'Singapore AI Agent for Workforce Policy Researchers',
    wordmark: 'LabourLens', author: 'Mihir Khandekar', source: '',
    notes: ['This is LabourLens, a bounded assistant for Singapore workforce-policy research.', 'The title names the intended users, not a claim of policy expertise. This is a technical assessment prototype, not a government service.', 'Not shown: a reliability or accuracy result. The deployed build differs from the evaluated build; independent review, source rights and operating controls remain open.']
  });

  // ---------- the assignment ----------
  add({
    layout: 'solo', chapter: 'Problem', title: 'Assignment', visual: assignmentBrief(),
    source: 'GenAI Engineer technical challenge',
    notes: ['This slide states the assessment brief and the capabilities the submission must demonstrate.', 'Traceable means a reader can follow an answer back to its evidence, called provenance. Retrieval selects evidence; evaluation checks behaviour and errors; responsible AI covers uncertainty, misuse and rights. MCP provides a typed client-server interface to tools.', 'Not shown: proof that every requirement is met, a user study, or a comparison with an existing research workflow.']
  });
  add({
    layout: 'solo', chapter: 'Why this problem', title: 'My project', visual: myProject(),
    source: 'LabourLens scope and data records',
    notes: ['This slide defines the project, its users and the questions it will or will not answer.', 'The live answer window is Q1 2020 to Q2 2026. The evaluated window was Q1 2024 to Q2 2026. Facts and quarter-to-quarter changes are supported tasks; a missing population, adjustment or year may require clarification. Unsupported causal attribution is outside scope, although attributed publisher commentary may be cited.', 'Not shown: forecasts, causal estimates, personal advice or demonstrated accuracy for the newly added 2020 to 2023 coverage. Sources: scope decision, source catalogue and system card.']
  });
  add({
    layout: 'solo', chapter: 'Scope', title: 'Scope', visual: assumptionsScope(m),
    source: 'Scope and orchestration decisions; data sheet; system card; README; evaluation report',
    notes: ['This slide shows five delivered scope items: the answer period, official sources, retrieval and agent tools, evaluation and workbench, and excluded tasks.', 'The current 142 sources comprise 36 datasets and 106 documents. They are inventory counts, not independent studies. The live window is Q1 2020 to Q2 2026; evaluated questions start in 2024. Public-source rights remain limited, tools are read only and bounded, and generation settings use provider defaults.', 'Not shown: blanket redistribution permission, independent human validation or production readiness. The 2020 to 2023 coverage and current serving changes have not been re-evaluated.'],
  });
  add({
    layout: 'solo', chapter: 'System', title: 'System architecture', visual: architectureDiagram(),
    source: 'LabourLens architecture',
    notes: ['This diagram shows how two evidence stores feed one bounded research agent and its checked answer.', 'Statistics become validated rows; reports become searchable text chunks. The planner chooses tools, the answer model writes claims, and code checks citations and numbers. This is retrieval-augmented generation: evidence is fetched at question time rather than learned into model weights.', 'Not shown: training, fine-tuning or evidence gathered before the loop. Served get_series and annual_average use the read-only MCP statistics service; report search and calculate_change stay in process. Source: served.py, graph and tool implementations.']
  });

  add({
    id: 'agent-overview', layout: 'solo', chapter: 'System', title: 'How the agent answers a question', visual: agentOverview(),
    caption: 'A bounded loop: plan, gather evidence, then write and check one cited answer. Later slides open each step, including the full loop.',
    source: 'Agent design and answer validation',
    notes: ['This slide illustrates five stages for a question about unemployment trends in 2025 and 2026, through the available Q2 2026 boundary.', 'The illustrated plan selects quarterly unemployment statistics and may search reports for context. It is not a saved run and presents no numerical result. Because the question names no population, the answer states which series it uses, such as overall seasonally adjusted unemployment. Each claim cites gathered evidence.', 'Code checks citations, quotes and numbers with one repair allowed. These checks do not prove semantic support or guarantee a successful answer. The planner sees the question and catalogue, not report text; the writer sees evidence.'],
  });

  // ---------- problem ----------

  // ---------- scope and plan ----------

  // ---------- data ----------
  add({
    id: 'data', layout: 'solo', chapter: 'Sources', title: 'Data sources', visual: twoSources(m),
    source: 'MOM and SingStat via data.gov.sg; MOM reports and an MTI article',
    notes: ['This slide shows separate ingestion paths for structured statistics and report text.', 'Corpus v4 inventory contains 52,020 observation rows across 36 datasets, including 11,228 rows in the live Q1 2020 to Q2 2026 window. Historical storage starts in 1980 but does not widen answering scope. Statistics stay as rows, without chunking or embeddings.', 'The report store contains 106 documents, 29,760 passages and 3,632 eligible chunks. Table-like PDF passages are flagged table_unreliable and excluded from default chunks, not repaired. These are current inventory counts, not evaluated v3.1 counts. Raw MOM and MTI material and report indexes remain local; this slide does not establish reliable PDF table reconstruction or redistribution permission.']
  });
  // ---------- EDA ----------
  add({...figSlide('fig-unemployment', {title: 'Data findings'}), title: 'Data findings', id: 'eda', chapter: 'Sources', layout: 'split', human: 'MOM unemployment rates via data.gov.sg',
    bullets: ['Multiple unemployment rates, depending on the type of population.'], rows: rowsAffordance(m.excerpts.unemployment, 'Show the real rows'),
    detail: {label: 'How to read this', content: 'Quarterly unemployment rates by population and seasonal adjustment.\nPopulation: overall, resident, citizen.\nAdjustment: seasonally adjusted and resident unadjusted.\n26 observations from Q1 2020 to Q2 2026; no confidence intervals in the published series.'},
    notes: ['This chart shows four official unemployment series whose definitions produce different values.', 'The horizontal axis covers 26 quarters from Q1 2020 to Q2 2026; the vertical axis is per cent of the relevant labour force. Solid lines distinguish resident, overall and citizen seasonally adjusted rates. The dashed resident line is unadjusted. Adjustment removes recurring seasonal patterns; it does not change who counts as resident.', 'At Q2 2026 the resident adjusted rate is 2.9%, overall 1.9%, citizen 3.0% and resident unadjusted 3.5%. Each point is a published observation, not a model estimate. The annotation marks the largest absolute adjusted-versus-unadjusted resident gap in the displayed window. Source: report.json charts and observation export.',]});
  add({...figSlide('fig-retrenchments', {title: 'Retrenchments'}), title: 'Retrenchment counts and their causes', chapter: 'Sources', layout: 'split', human: 'MOM retrenched employees via data.gov.sg',
    bullets: ['The datasets give counts, not reasons.', 'Where MOM commentary gives a reason, the answer attributes it to MOM.'], rows: rowsAffordance(m.excerpts.retrenchments, 'Show the real rows'),
    detail: {label: 'How to read this', content: 'Stacked quarterly counts of permanent and term-contract retrenchments, with the total compared in the source table.\nUnit: persons.\n26 quarters; no confidence intervals in the published series.'},
    notes: ['This chart shows quarterly retrenchment counts, not the reasons for retrenchment.', 'Each stacked bar is one of 26 quarters from Q1 2020 to Q2 2026. The segments count permanent and term-contract employees in persons; their sum is the total. The highlighted bar marks the largest total in the window. Totals start at 3,220, peak at 9,120 in Q3 2020 and end at 4,620. Source: report.json charts and dataset rows.', 'Not shown: causal variables, employee identities, a forecast or confidence intervals. Hovering the row affordance reveals source rows and the permanent/term-contract split, not report text.']
  });
  add({...figSlide('fig-revisions', {title: 'Advance and final figures'}), title: 'Advance and final figures differ', chapter: 'Sources', layout: 'split', human: 'MOM advance and final reports, and the SingStat sector dataset',
    bullets: ['Each figure comes from an advance or a final release.'], rows: rowsAffordance(m.excerpts.revisions, 'Show the same quarter in each release'),
    detail: {label: 'How to read this', content: 'Each row compares the advance release, final MOM report and sector dataset total for one quarter.\nUnit: persons.\nFour quarters in the reconciliation export; this is a source-vintage comparison, not a confidence interval.'},
    notes: ['This chart compares employment-change figures for the same quarter across release vintages and the sector dataset.', 'Each row is one quarter, with markers for advance, final and sector-dataset totals in persons. The four advance/final/dataset triples are Q3 2025: 24,800/25,100/30,200; Q4 2025: 19,600/17,700/20,800; Q1 2026: 5,000/9,400/13,000; Q2 2026: 10,700/11,400/14,700. Connecting marks show numerical distance, not uncertainty. Source: report.json reconciliation and linked release and observation records.', 'Not shown: confidence intervals, a revision-detection service or proof all three measures have identical coverage. The four rows are a source-vintage comparison, not four agent test cases.']});
  add({
    layout: 'solo', chapter: 'Sources', title: 'Challenges with the data', visual: hardParts(m), caption: 'Each finding about the data became a design decision. Rows that rest on data show the real rows on hover or focus.',
    source: 'LabourLens data findings and design notes',
    notes: ['This slide maps six data difficulties to the design choices they motivated.', 'Four unemployment rates require typed population and adjustment; absent definitions trigger clarification. Counts without causes require attributed commentary or a decline. Advance/final differences require release labels, not averaging. Flattened tables require exclusion and checks. A published vacancy ratio can differ by up to 0.67 from the ratio rebuilt from counts because survey bases differ; use the published ratio. Before-2020 requests are outside live scope.', 'Not shown: six independently measured fixes, a reliable PDF table parser or a causal analysis. The scope example is schematic; the statistical popovers show actual source rows.']
  });
  add({
    layout: 'solo', chapter: 'Processing', title: 'Processing reports', visual: flattening(m),
    source: 'Current corpus metadata, parser, chunking and retrieval implementation',
    detail: {label: 'Current document build', content: 'Corpus v4, the live build, has 142 sources, including 106 documents, 29,760 extracted passages and 3,632 runtime chunks; it adds the 2020 to 2022 reports and the 2020 to 2023 annual reports to v3.1 and has not been evaluated. Corpus v3.1, the build the final evaluation ran on, has 85 sources, including 49 documents, 16,419 extracted passages and 1,847 runtime chunks. Compared with v3, v3.1 relabelled 40 MTI passages after refining the garbled-text rule; the source, passage and chunk counts stayed unchanged. These are extraction and quality-label facts, not measured retrieval gains.'},
    notes: ['This slide follows a report from local extraction to two indexes over the same eligible chunks.', 'Current corpus v4 has 142 sources, including 106 documents, 29,760 passages and 3,632 chunks. Evaluated v3.1 had 85 sources, 49 documents, 16,419 passages and 1,847 chunks. These count different units and builds. Runtime merge200 targets about 200 words with 40 words of whole-passage overlap; only quality_flag=ok enters default chunking.', 'BM25 indexes words; dense embeddings represent meaning as 3,072-number vectors. The worked eligible chunk has 216 words and nine source passages on pages 2 to 3 of the Q1 2026 final report. A table-like block on page 28 is excluded, not repaired. This is an extraction illustration, not a retrieval score. Source: runtime.py, chunk metadata and local cached vector metadata.',]
  });
  add({
    layout: 'solo', chapter: 'Retrieval', title: 'Retrieval Strategies', visual: keywordVsMeaning(m) || missing('Retrieval methods'), caption: 'These 128 are development questions that report text can answer. Hit@8 means a relevant passage is in one of the first eight chunks.',
    source: 'BM25, dense embeddings and hybrid on the same 128 cases, corpus v3.1',
    detail: {label: 'Retrieval methods', content: 'BM25 is keyword search. Meaning search uses dense text-embedding-3-large vectors. Hybrid combines them by reciprocal rank fusion, c=60 over the top 50 of each list. All three use merge200 chunks and the same 128 cases from corpus v3.1. Hit@8 means a relevant passage appears in one of the top eight chunks. Period/release filtering and reranking are not part of this methods comparison.'},
    notes: ['This chart compares keyword, meaning and combined search on the same development questions.', 'The bars are the share of 128 answerable report-text questions with a relevant passage inside one of the first eight chunks, called chunk hit@8. BM25 scores 47.7%, dense 36.7%, hybrid 53.9%, on 1,847 merge200 chunks from corpus v3.1. A chunk can contain several passages, so this is not first-eight-distinct-passages accuracy.', 'Keyword search is BM25; meaning search uses text-embedding-3-large vectors with 3,072 dimensions. Hybrid adds rank-based scores from the top 50 of each list, called reciprocal rank fusion with c=60. Its gain over BM25 is 6.2 percentage points with a 95% paired case-bootstrap interval of -2.3 to 14.8, so superiority over BM25 is not demonstrated. Source: dev-R-V31-methods metrics through report.json.',]
  });

  // ---------- reading ----------

  // ---------- retrieval ----------
  add({
    id: 'retrieval', layout: 'solo', chapter: 'Retrieval', title: 'Does filtering help?', visual: retrievalLadder(), caption: 'Filter then rerank has the highest chunk hit@8 on both sets (tied with rerank alone on fresh questions). End-to-end answer gains remain unproven.',
    source: 'Development: corpus v3.1 re-run of 128 questions. Fresh questions: frozen retrieval-only results, 3 November 2026',
    detail: {label: 'Retrieval steps', content: 'Each group compares hybrid, filter only, rerank only, and filter plus rerank on its own questions. Development uses the same 128 questions as the previous slide, so its first bar is the same 53.9%. Fresh questions have their own baseline. All use corpus v3.1 and merge200.\nHybrid combines BM25 and dense rankings by reciprocal rank fusion, c=60 over the top 50 of each. BM25 uses k1=1.5, b=0.75, stop words and quarter normalisation, with no stemming. Dense uses text-embedding-3-large. The period/release filter restricts candidates to matching documents. gpt-6-luna ranks the top 30 and returns up to 10 chunks; remaining candidates retain incoming order.\nChunk hit@8 means an acceptable passage appears in one of the first eight chunks. Development chunk hit@8: .539/.852/.742/.969. Fresh: .882/.912/.971/.971. Strict passage hit@8 counts the first eight distinct passages: development hybrid .258; fresh .500/.500/.941/.941.\nChunk MRR@10 averages reciprocal rank of the first acceptable chunk within ten, with zero for a miss. Fresh hybrid scores .618 and both steps .887. It measures rank, not answer correctness.\nDevelopment shaped the design and fresh questions have been reused. One reranker run does not establish variation or end-to-end answer gains.'},
    notes: ['This chart compares four retrieval configurations using chunk hit@8 on two question sets.', 'Within each group the order is hybrid, hybrid plus period/release filter, hybrid plus rerank, then both. Development uses 128 text questions: 53.9%, 85.2%, 74.2%, 96.9%. Fresh uses 34: 88.2%, 91.2%, 97.1%, 97.1%. All use corpus v3.1 and merge200. The first development bar matches Retrieval Strategies; fresh questions have their own baseline.', 'Development questions shaped the design and fresh questions have been reused. Chunk hit@8 asks whether any of the first eight chunks contains an acceptable passage. Distinct-passage scoring is stricter. These retrieval-only results do not establish answer improvements.'],
  });

  // ---------- agent ----------
  add({
    id: 'agent', layout: 'solo', chapter: 'Agent', title: 'Agent loop', visual: agentLoop(), caption: 'The planner chooses tools or stops.',
    source: 'LangGraph agent and planner/answer prompts',
    detail: {label: 'Planner and answer prompts', content: 'PLANNER\nGather evidence in round 1. Use round 2 only for a calculation or another lookup after an error or gap. Then stop gathering.\n\nANSWER\nEach claim cites supplied evidence and includes an exact quote. Quote existence is not proof of semantic support.\n\nEvaluated/default limits: 2 rounds, 6 calls total, 3 per round, 10 seconds per tool call, 1 transient retry and 1 answer repair. The unadopted report-arithmetic experiment allowed one bonus round after a bad dimension label, keeping the six-call budget.\nCurrent serving: report search has 25 seconds plus one conditional timeout retry of at most 12 seconds within the run deadline; other tools keep ten seconds. This served exception was not evaluated.'},
    // Transport choices are implementation facts; hypothetical memory costs are not measurements.
    notes: ['This diagram shows a bounded feedback loop from a question to a validated answer or explicit failure.', 'The planner chooses search_reports for passages, get_series for typed rows, calculate_change for arithmetic on earlier rows, or stop. Tool results can trigger another plan. After gathering, evidence assessment marks conflicts, then writing and validation run, with one repair. Two rounds, six calls and three per round are graph limits. The evaluated/default timeout is ten seconds; served search now gets 25 seconds and one conditional retry up to 12 seconds within its run deadline. Malformed native arguments count as tool errors.', 'The comparison is response-status accuracy on 237 development questions: one fixed-pipeline run scored 81.4%, versus agent two-run mean 89.7%. Fixed minus agent is -8.2 points, 95% case interval -13.1 to -3.4. Control policies, lookup coverage and calculation access differ, so it does not isolate planning intelligence. Source: agent-vs-fixed-pipeline.json.',]
  });
  add({
    layout: 'solo', chapter: 'Agent', title: 'Three example runs', visual: exampleRuns(),
    source: 'Saved development runs of the agent, gpt-6-luna',
    notes: ['This slide shows three selected saved runs: a numerical change, a definition and an unsupported request.', 'DEV-005 looks up resident unemployment for two quarters and calls calculate_change; the change comes from code, not model arithmetic. DEV-002 uses report search for a definition. DEV-415 seeks a count not held by the data and declines instead of substituting a broader total. Each row lists actual tool calls and the resulting response status.', 'Not shown: a success rate, a complete distribution of paths, live latency or performance of annual averaging. No publisher passage text is reproduced.']
  });
  add({
    layout: 'solo', chapter: 'Answer', title: 'Checking the answer', visual: answerChecks(),
    caption: 'Code checks the answer before release. The checks cover form and provenance, not meaning.',
    source: 'Agent answer validation and calculation tools',
    detail: {label: 'Evidence validation', content: '1. Validate the structured answer schema and status.\n2. Confirm each citation label was in the supplied evidence.\n3. Confirm the quote appears verbatim in the cited passage.\n4. Check reported numbers are present in cited evidence.\n5. Calculate changes in Decimal arithmetic from validated observations.\nThese checks do not prove that a quote semantically supports its claim.'},
    notes: ['This slide separates what the model writes from six checks performed by code.', 'The example moves from 2.7% to 2.9%, a 0.2 percentage-point change, not a 0.2% relative increase. It is a shortened illustrative answer schema, not a scored case. Checks cover schema/status, known citation labels, exact quotes, evidence numbers, status/content agreement and output secrets. Quotes are capped at 40 words; that internal validation limit is not permission to republish report text.', 'Not shown: proof of meaning, universal secret detection or perfect numerical accuracy. The primary historical development calculation score was 75% on 24 cases, not 100%, despite deterministic arithmetic.']
  });
  // ---------- measuring ----------
  add({
    layout: 'solo', chapter: 'Agent', title: 'Choosing models', visual: modelChoice(m) || missing('The model screen'), caption: 'gpt-4.1-mini had the highest early accuracy but most false answers. I chose gpt-6-luna: no false answers and the lowest cost among these five.',
    source: 'Early model screen; final evaluation; fixed-pipeline comparison, 3 November 2026',
    detail: {label: 'Early screening method', content: 'Retrieved evidence: 30 development questions, five chunks. Oracle comparison: the same models with reference passages placed first. Behaviour accuracy is response-status agreement; plotted cost is USD per case.\nThe five models shown include gpt-6.1-terra as a generator; it was later used as the judge. Early false-answer rates use the six non-answerable questions; final-system rates use all 237 development questions.\nOne model family. Labels were AI drafts then. Sampling and reasoning settings stayed at provider defaults. One repeat also changed the context header, so it was not a pure repeat.'},
    notes: ['This slide contrasts an early five-model screen with the final system and a fixed workflow.', 'Early bars split 30 questions into right status, wrongly declined answerable questions, false answers on six non-answerable questions, and other wrong statuses. In displayed order the counts are 18/10/0/2, 17/10/0/3, 21/6/1/2, 18/9/1/2 and 25/3/2/0. Costs per question are $0.00051, $0.00432, $0.00335, $0.00912 and $0.00161. These are recorded-token list-price estimates, not invoices; tooltip intervals are 95% Wilson intervals. gpt-4.1-mini has 25/30 (83.3%) right and 2/6 (33.3%) false answers.', 'The final gpt-6-luna bar uses 237 development questions and two-run means: 89.7% right, 3.2% wrongly declined, 2.9% false answer and 4.2% other wrong status, rounded to sum to 100%. False answer means answering a reference non-answer, not necessarily stating a false fact. Cost is $0.002845 before display rounding. Final error shares use all 237 cases, not early denominators of 24 and six. Fixed scores 81.4% versus agent 89.7%, with policy and arithmetic access also differing.', 'The early selection prioritised no false answers at the lowest cost, accepting more declines rather than choosing the highest status accuracy. This was a small screening result, not an independent model ranking. The final agent uses a different workflow and larger question set, so the comparison does not establish improvement in the model itself. Sources: answer-dev-G1 metrics, final-mean.json and the fixed-pipeline artefact.']
  });
  add({
    layout: 'solo', chapter: 'Checks', title: 'How I evaluated', visual: evaluationDesign(m),
    source: 'Evaluation artefacts and review records',
    detail: {label: 'Rules, judges and review timing', content: 'Behaviour accuracy is exact expected-status matching: answer, abstain, clarify or refuse. Neither judge sets this score.\nThe primary judge, gpt-6.1-terra, sees the question, answer claims, cited evidence and reference facts. It labels claim support, fact coverage and contradictions without independent evidence search.\nA second-family claude-sonnet-5-5 check reused the same prompt and saved inputs on a first-run sample: 240 answers sampled, 234 retained in 117 valid pairs after three omissions. Claim support remains judge-dependent.\nAI drafted the questions and reference labels. I approved them after saved runs had been scored, following AI pre-review. The numbered steps show responsibilities rather than strict chronology. I was the only human reviewer; the 40-answer sample was failure-enriched.'},
    notes: ['This slide shows the question sets and separates deterministic scoring from AI judgement and owner review.', 'Development has 237 questions used for tuning; original test has 31; fresh has 65 authored against six newer sources and audited disjoint at first use. The original 268 total is 237 plus 31, not an extra set. Original-test overlap is 25/31 with any development evidence. For whole-set reuse the primary evidence-audit.json says 14/31; evaluation-report text says 15/31. The primary audit takes precedence.', 'Code scores whether the response takes the expected action, called behaviour accuracy: answer, abstain, clarify or refuse. The primary AI judge scores claim support, reference-fact coverage and contradictions from supplied evidence, without independent search. A second-family check sampled 240 answers and retained 234 in 117 pairs after omissions. It tests judge sensitivity, not human truth.', 'Human reviewed means owner sign-off on four streams: 268 gold questions, 65 fresh questions, 40 failure-enriched saved answers and 30 source checks. These total 403 items, not 403 questions. AI drafted the labels; three AI review passes from the same model family preceded sign-off by one human reviewer after the saved runs were scored. Five post-run label edits remain disclosed. This is not independent inter-rater validation. The fresh set was unseen at first use, not after repeated runs and diagnostics. Sources: gold/audit files and human-review records.']
  });
  add({
    layout: 'solo', chapter: 'Checks', title: 'Does better retrieval improve answers?', visual: finalComparison(m, {includeFresh: false, showDifference: false, showHistory: false}) || missing('The final comparison'), caption: 'Complete system, hybrid against filter then rerank. Mean of two runs. Gain on development questions only.',
    source: 'Final evaluation, corpus v3.1; two runs per arm',
    detail: {label: 'What each bar measures', content: 'Grey: hybrid keyword-plus-embedding retrieval. Green: period/release filtering followed by model reranking. The answer model, tool set and prompts stay fixed.\nThese are complete-system behaviour scores, not retrieval hit rates or a continuous improvement ladder. Development: 82.7% against 89.7%, paired +7.0 points [3.6,10.6]. Original test: 80.6% against 83.9%, +3.2 [-3.2,11.3]. Fresh questions, kept in notes: 74.6% against 71.5%, -3.1 [-7.7,.8]. No demonstrated answer gain on either test set.\nEach bar is a mean of two runs; two runs do not estimate model variance. Earlier prompt, retrieval and planner experiments remain in the appendix and report, with their own denominators and builds.'},
    notes: ['This chart compares final complete-system response-status accuracy with hybrid retrieval against filter then rerank.', 'Grey and green bars are means of two runs per arm on corpus v3.1, with gpt-6-luna, structured-output planning, planner_v1/answer_v3 and three direct tools held fixed. Development has 237 questions: 82.7% versus 89.7%. Original test has 31: 80.6% versus 83.9%. This is exact expected-status agreement, called behaviour accuracy, not retrieval hit rate or claim correctness.', 'Paired gains are +7.0 percentage points on development, 95% case-bootstrap interval 3.6 to 10.6, and +3.2 on original test, -3.2 to 11.3. The 65 fresh questions, not plotted, score 74.6% versus 71.5%, a -3.1-point difference, -7.7 to 0.8. Intervals resample cases using their mean outcomes; two runs do not estimate model variation. Source: experiments/eval/final-mean.json.',]
  });
  add({
    layout: 'solo', chapter: 'Retrieval', title: 'Statistics lookup through MCP', visual: mcpMap(m, {showMeasurements: false}), caption: 'Two server tools serve statistics lookup and annual averaging. The server also exposes two resources.',
    source: 'MCP implementation and protocol checks',
    detail: {label: 'Agent request and server reply', content: 'The MCP client sends typed get_statistic or annual_average requests. The server validates them and returns provenance-backed rows or calculation evidence.\nThe client checks advertised schemas and typed responses, screens untrusted content and enforces size and time limits. Invalid replies and timeouts remain operational failures. The default server now has ten tools; the served agent uses two of them. Historical measurements used nine server tools and one planner-facing statistics tool. Annual averaging is unevaluated.'},
    notes: ['This diagram shows how the agent reads validated statistics through a typed MCP client and server.', 'MCP is a standard tool-and-resource protocol, not an accuracy model. The server offers ten tools and two resources; serving reaches get_statistic and annual_average. Its four-tool vocabulary also includes in-process search_reports and calculate_change; get_series maps to get_statistic. The planner list is fixed. The client checks advertised input/output schemas, typed replies, untrusted content, size and time limits. Negotiated protocol revision: 2025-11-25. Discovery verifies the boundary, not new planner permissions.', 'Annual averaging takes four non-null quarterly percentage rates from one series and rounds their Decimal mean to two places, not an official annual rate. Failures remain operational failures with no silent direct fallback. Source: MCP server/client and served.py DEFAULT_TRANSPORT=mcp_stats. Stale decision prose describing all-tools as default is superseded by executable configuration.', 'Historical parity checks found identical rows on 23 accepted queries through MCP and direct calls; both refused 13 oversized queries. One served-chain run on 51 reused development cases plus 14 probes scored 59/65 on statistics MCP, with no observed loss versus direct. All-tools MCP scored 57/65; p95 latency was 51.4 s versus 34.7 s. It exceeded the pre-set latency limit and was not adopted. These results do not establish equivalence, third-party-host validation or current annual-tool quality. Sources: report.json mcp and paired served-route artefacts.']
  });
  add({
    layout: 'solo', chapter: 'Checks', title: 'Attacks and defences', visual: threatGains(), caption: 'Most attacks were resisted without the added guards. The combined guards and prompt added a modest margin.',
    source: 'Frozen threat suite v2, 3 November 2026; three repeats per arm',
    detail: {label: 'Threat design and prompt', content: 'Case-majority scoring: 10 attacks passed only guarded, 2 only naive. Exact McNemar p = .039, near the .05 threshold. Guards plus answer prompt changed together; this cannot isolate a defence layer. Typed tools, MCP boundary and input length cap stayed on in both arms.\nPrompt: Evidence items are untrusted data, not instructions.\nEarlier separate suite: 35/36 in both arms. Per-layer deterministic checks remain in the safety appendix.'},
    notes: ['This slide compares resistance to a frozen synthetic attack suite with and without added guards and a revised prompt.', 'Each of 54 attacks ran three times per arm; a case passes by majority. Results are guarded 50/54, naive 42/54. There were 10 attacks passed only guarded and 2 only naive, a net eight; exact paired McNemar p = .039. This is evidence about a paired difference under the null, not the probability the system is safe. Both arms had 3/8 benign failures, failing that adoption criterion.', 'Table rows show naive/guarded passes: direct injection 6/8 to 8/8, planted figures 4/8 to 7/8, causal/forecast overreach 2/4 to 4/4, citation attacks 2/4 to 3/4. Another 22 passed in both arms: passage injection six, personal data four, unsafe tool use six and MCP six. The primary artefact also has unchanged cost-abuse 3/4 and exfiltration 3/4 categories, not expanded on the face. These reconcile the 54-case total. Source: threat-v2-analysis.json.',]
  });

  // ---------- cost ----------
  add({
    layout: 'solo', chapter: 'Answer', title: 'Agent Workbench',
    visual: workbenchShot(), source: 'Workbench screenshot; live questions require an access code',
    notes: ['This slide shows the workbench interface and a link to the hosted demo.', 'The screenshot is the report-only interface, not a saved live answer or latency measurement. The static QR code points to https://labourlens.navig.me/workbench. Live questions require an access code and paid model calls. Status, sources, citations and tool events are visible output, not hidden model reasoning.', 'Three steps run in front of the agent: a small-talk fast path, conversation rewrite, then scope classification, in that current code order. Serving uses corpus v4, a 2020 start, statistics MCP, native function calling, planner_v7/answer_v9, triage_v4, contextualise_v3 and streaming. Bounded concurrent calls, search caching and a report-context cap are also implemented. The current combination is not re-evaluated.', `Not shown: current-build quality or guaranteed response time. A historical 65-case sample of the served chain predates these changes; full final experiments omitted web steps and used direct tools. Historical rewrite-only diagnostic: ${contextSentence(serving)} Source: served.py and served-chain artefacts.`]
  });

  // ---------- process ----------
  add({
    id: 'process', layout: 'solo', chapter: 'How I worked', title: 'How I built it',
    visual: buildProcess(work.decisions?.length), source: 'LabourLens project record, README and reproduction notes',
    notes: ['This slide summarises the planning, implementation, measurement and review process.', 'The decision count comes from report.json work.decisions, not a quality score. A frozen run keeps configuration, prompts, gold identity, usage and scores. A paired comparison measures the same questions under two conditions. Registration records intentions but cannot enforce good design by itself. The three harnesses are coding-agent gates, evaluation, and synthetic threats/MCP fixtures.', 'The try-it row separates offline and paid work. LABOURLENS_DEMO_ENABLED=false make serve opens the report locally. make verify runs project gates; labourlens rights-scan needs the private corpus and otherwise reports NOT CHECKED, not clearance. scripts/final_mean.py recomputes saved scores; labourlens mcp-demo exercises the protocol. The live workbench needs a code and paid calls.', 'Not shown: independent review of every change, certification or complete model replay from a public clone. Full model replay needs the rights-restricted corpus and paid credentials. Offline reproducibility of saved scores is a narrower claim.']
  });
  add({
    layout: 'solo', chapter: 'Next', title: 'Improve the system', visual: improvementPlan(m),
    source: 'Final evaluation and native-planner smoke; proposals need new measurements',
    notes: ['This slide separates the measured latency starting point from proposed and newly shipped optimisation work.', 'About 14 seconds is the rounded 14.35-second mean of two development run medians for filter then rerank, not a pooled median or live-app target. The 237 questions are development cases. p50 is the median; p95 is the time below which 95% finish. The native-planner smoke took 29.8, 7.8 and 9.1 seconds versus structured 53.1, 8.6 and 12.8 on three once-only questions, not a controlled experiment.', 'Overlapping triage, broader revision/access-aware series, prompt and response caches, and smaller models remain proposals. D-089 implements concurrent independent calls within the three-per-round cap and a 300-second corpus-keyed query/search cache; D-088 caps report context at 20 passages. Native calling and streaming are also implemented. Current code supersedes the older proposal wording on the slide, but the quality and live speed effects remain unmeasured.', 'Not shown: a controlled speed-up from these changes. Speculation can cost money; stale or cross-user caches can be incorrect; streaming does not prove faster completion. A controlled comparison would measure status accuracy, p50/p95 and cost, followed by new blind questions. Sources: final-mean.json, native-planner smoke and D-088/D-089.']
  });
  add({
    layout: 'solo', chapter: 'Next', title: 'Deploy in production', visual: productionArchitecture(),
    source: 'Proposed architecture; current deployment is one Droplet with Caddy and Docker',
    notes: ['This diagram separates the single-machine deployment built today from a proposed production architecture.', 'The top bar is one Droplet with Caddy and Docker. The four proposed request-path boxes are protected access, API replicas, queued workers and a model gateway. Authentication and rate limits control entry; replicas hold no local job state; bounded workers execute jobs; the gateway enforces budgets, redaction and evaluated-model failover. Arrows show responsibilities, not measured throughput.', 'The three lower boxes are read-only versioned sources, search/statistics and an isolated MCP service. They preserve rights, checksums, evidence versions and typed access. The surrounding strip applies secrets management, audit/tracing, evaluation release gates and backups across all services. It is not another step in answering a question.',]
  });
  add({
    layout: 'solo', chapter: 'Next', title: 'Next steps', visual: nextSteps(),
    source: 'Innovation assessment, deployment notes and project decision log',
    notes: ['This slide proposes three directions: narrower routing, fresh data and wider source coverage.', 'A two-way scope gate would decide only whether a question belongs to the domain. It is a third proposed Decisions API attempt, not a shipped classifier. The two earlier four-way trials were faster but failed registered safety, routing or operational rules. Faster classification is not automatically faster or safer end-to-end answering.', 'Not shown: an adopted accuracy gain, scheduled refresh reliability, multilingual evaluation or permission to ingest every government source. The fuller discussion is at /innovation; references can be revealed with A twice.']
  });

  // ---------- limits and next ----------
  const sjFacts = secondJudgeFacts(m), sjSentence = secondJudgeSentence(m);
  add({
    layout: 'solo', chapter: 'Close', title: 'Summary', visual: agentSummary(m) || missing('The agent summary'),
    source: 'Assessment PDF and LabourLens evaluation records',
    notes: ['This slide summarises what the agent is, what it can do and six improvements ranked by the confidence they would add.', 'The left column describes a bounded planner and checked answer. Two rounds and six calls are budgets, not averages. Ten seconds per tool is the evaluated/default limit; current served search gets 25 seconds plus one conditional retry up to 12 seconds within the run deadline. The middle mixes measured evidence and serving: chunk hit@8 rose from 53.9% to 96.9% on 128 development text questions; guarded attacks passed 50/54 versus 42/54. MCP, annual averages and streaming are current functionality, not re-evaluated system quality. Annual averages are simple means of four quarterly rates.', 'The ranked actions are re-test serving, independent review, semantic support checks, new blind questions, known attack/arithmetic gaps, then measured speed and cost work. Evaluated v3.1 used structured planning, planner_v1/answer_v3 and three direct tools. Served v4 uses native function calling, planner_v7/answer_v9 and four tools, not re-evaluated. Labels were signed off by one human reviewer after scoring; the fresh 65 have been reused.', 'Filtering and reranking improved development retrieval, with no demonstrated gain in answer status on either test set. The separate detector test reached 23/30 attacks flagged with unchanged 9/30 benign flags; semantic and non-English bypasses remain. Report arithmetic failed its adoption rules. A provider-side spend cap and some source rights remain unresolved. Next: live-build re-evaluation, independent review and new blind questions.', 'Not shown: production readiness, stable resistance to every planted figure or proof that a quote supports a claim. Sources: final evaluation, threat/scanner artefacts, served.py, graph.py and the decision record.']
  });

  // ---------- appendix ----------
  const appendixIndex = [];
  const appendix = (letter, title, build) => { appendixIndex.push([letter, title]); build(letter, title); };
  const group = (...nodes) => { const g = el('div', 'deck-ref'); nodes.filter(Boolean).forEach(n => g.append(n)); return g; };
  const heading = (title) => el('h3', 'deck-ref-title', title);

  add({layout: 'appendix', chapter: 'Appendix', id: 'appendix', title: 'Appendix', index: appendixIndex,
    notes: ['Reference slides are hidden by default. The appendix toggle uses A twice within 400 ms; hiding references returns to the last main slide. Appendix links reveal their targets automatically. Reference slides support internal scrolling. The public notes panel is toggled with X twice.']});
  const indexSpec = specs[specs.length - 1];

  appendix('A', 'Caveats and evaluation limits in full', () => {
    const callouts = [];
    const headline = take(c.safety, '.pr-callout'); // unused safety callouts are dropped below if absent
    ['retrieval', 'evaluation'].forEach(key => takeAll(c[key], '.pr-callout').forEach(node => callouts.push(node)));
    const x2 = [...(c.evaluation?.querySelectorAll('.pr-block') || [])].find(b => /X2 regression/.test(text(b, '.pr-block-title')));
    add({
      chapter: 'Appendix', layout: 'scroll', title: 'A. Caveats and evaluation limits in full',
      panel: [
        group(heading('Gold labels and review'), list(['Labels were drafted by AI. I signed off every case, answer verdict and source check (403 items in four separate streams). I went through them after three separate AI review passes and after the saved runs were scored. One human reviewer; this is owner review, not independent inter-rater evidence. Four change-clicks were not applied under the out-of-period policy, so labels are unchanged in v3.7.', `Development rows use ${goldOf(a3).label}; original-test rows use ${goldOf(r3).label}. Both were rescored from saved outputs after post-run label edits.`, 'Registered results ran on corpus v1 and the X1 runs on corpus v2. Corpus v3 (85 sources) has three measured evaluations: the X2 development regression check, the e2efix threat run and the fresh set (65 questions, evidence-disjoint at source level only), plus the tool set v2 runs (X3 and V2post, not adopted). The final evaluation of all three question sets, both models, ran on v3.1.'])),
        ...callouts,
        x2 ? group(heading('X2 regression check'), ...[...x2.children].filter(n => !n.classList.contains('pr-block-head'))) : null,
        headline
      ].filter(Boolean),
      source: 'README.md, docs/system-card.md, docs/evaluation-report.md, docs/experiments/m7-e2e-fixes.md',
      notes: ['The caveats stated in the main deck, with their full wording. The retrieval limits and the evaluation limits are listed as the chapters recorded them.']
    });
  });

  appendix('B', 'Scope and data reference', () => {
    const pipeline = take(c.scope, '.pr-pipeline'), outOfScope = take(c.scope, '.pr-callout'), families = fig('fig-families'), sourcesFig = fig('fig-sources');
    const quality = fig('fig-quality'), warnings = take(c.data, '.pr-warnings');
    const ratio = fig('fig-vacancy-ratio'), vacancies = fig('fig-vacancies');
    const findingsBlock = take(c.data, '.pr-find-block'), atlas = take(c.data, '.pr-atlas');
    add({
      chapter: 'Appendix', layout: 'scroll', title: 'B. Scope and data reference',
      panel: [
        group(heading('How an answer is made'), pipeline, outOfScope), group(heading('Question families'), families), group(heading('Where each source stands'), sourcesFig),
        group(heading(figTitle(quality) || 'Validation checks'), quality, warnings),
        group(heading('Vacancy series'), ratio, vacancies),
        group(findingsBlock),
        group(atlas)
      ],
      source: 'report.json: quality, charts, eda; docs/data-sheet.md, docs/system-card.md',
      notes: ['Scope and data detail: the six-step answer pipeline, what is out of scope, the validation outcomes and their warnings, two more series, the four findings and the series catalogue.']
    });
  });

  appendix('C', 'Retrieval reference', () => {
    const ladderFig = fig('fig-ladder'), rankShift = fig('fig-rank-shift'), methods = fig('fig-methods'), emb = fig('fig-embeddings'), abl = fig('fig-ablation'), hint = fig('fig-hint');
    const limits = takeAll(c.retrieval, '.pr-callout');
    add({
      chapter: 'Appendix', layout: 'scroll', title: 'C. Retrieval reference',
      panel: [group(heading('Original test and fresh questions'), unseenRetrieval()), group(heading('Retrieval ladder with intervals'), ladderFig), group(heading('Early comparisons that chose the hybrid baseline'), methods, emb), group(heading('BM25 settings and period hints'), abl, hint), group(heading('Rank of the first relevant chunk'), rankShift), ...limits],
      source: 'docs/evaluation-report.md, Expanded retrieval study; docs/experiments/m6-retrieval-improvements.md',
      notes: ['The early comparisons are noisy: one case is about 4.2 points. Hybrid was chosen from them as the baseline, not proved best.']
    });
  });

  appendix('D', 'Agent reference', () => {
    const calls = fig('fig-calls'), errors = fig('fig-tools'), graphFig = fig('fig-graph'), tools = take(c.agent, '.pr-tools');
    add({
      chapter: 'Appendix', layout: 'scroll', title: 'D. Agent reference',
      panel: [group(heading('Fixed pipeline comparison'), fixedPipeline()), group(heading('Recorded run, step by step'), graphFig), group(heading('Historical three-tool set'), tools), group(heading(figTitle(calls) || 'Recorded tool calls'), calls), group(heading(figTitle(errors) || 'Tool errors'), errors)],
      source: 'report.json: agent.trace; docs/architecture.md, section 4',
      notes: ['Recorded runs against the set limits, and the operational failures and repaired answers. This appendix table describes the historical three-tool evaluated set, not the current four-tool served set. Current served prompts are planner_v7, answer_v9, triage_v4 and contextualise_v3; annual averaging, context repair and reasons/abstention changes have not been re-evaluated.']
    });
  });

  appendix('E', 'Evaluation reference', () => {
    const items = ['fig-latency', 'fig-cost', 'fig-models', 'fig-oracle', 'fig-errors', 'fig-dev-held', 'fig-strata', 'fig-progression', 'fig-paired', 'fig-review'].map(fig);
    const x2 = [...(c.evaluation?.querySelectorAll('.pr-block') || [])].find(b => /X2 regression/.test(text(b, '.pr-block-title')));
    const sjNode = take(c.evaluation, '.sj');
    add({
      chapter: 'Appendix', layout: 'scroll', title: 'E. Evaluation reference',
      panel: [group(heading('Where each headline number comes from'), provenanceTable(m) || el('p', '', 'The provenance table is not available in the report data.')), group(heading('The final system, in one sentence'), el('p', '', finalSentence(m))), group(heading('Response time and cost'), items[0], items[1]), group(heading('Model comparison and oracle evidence'), items[2], items[3]), group(heading('Error counts'), items[4]), group(heading('Experiment progression and registered original test'), items[7], items[8]), group(heading('Review counts'), items[9]), ...(sjNode ? [group(heading('Second judge check on claim support'), sjNode)] : []), group(heading('Development against original test, and by family'), items[5], items[6]), ...takeAll(c.evaluation, '.pr-details').map(d => group(d))],
      source: 'report.json: evaluation.rows, answers.rows, evaluation.errors, evaluation.second_judge',
      notes: ['The first card is the provenance table: for each question set, the document build, the code, the gold file and its hash, the models, the number of runs per arm and the judge. Then latency and cost, the model comparison on answer-only cases with oracle evidence, and the pooled error counts. The X2 regression table is in appendix A. Older tables below the first two cards are history from earlier builds.', ...(secondJudgeNote(m) ? [secondJudgeNote(m)] : [])]
    });
    void x2;
  });

  appendix('F', 'Safety reference', () => {
    const ci = fig('fig-threat-ci'), e2e = fig('fig-e2efix'), canary = take(c.safety, '.pr-canary'), post = fig('fig-postfix');
    const callouts = takeAll(c.safety, '.pr-callout');
    add({
      chapter: 'Appendix', layout: 'scroll', title: 'F. Safety reference',
      panel: [group(heading('Three-repeat threat comparison'), threatComparison()), group(heading('Per-layer checks and earlier suite'), threatLayerTable(m)), group(heading('Earlier pass rates by configuration'), ci, canary), group(heading('Final-code run'), e2e), group(heading('First post-fix run'), post), ...callouts],
      source: 'report.json: security; experiments/threats/*/SUMMARY.md; docs/experiments/m7-t-i06-crosscheck.md',
      notes: ['Intervals and canary results for the threat suite, the first post-fix run with its two scorers, and what the failing final-code run shows.']
    });
  });

  appendix('G', 'MCP reference', () => {
    const catalogue = take(c.mcp, '.pr-mcp-cat'), checks = take(c.mcp, '.pr-checks'), http = take(c.mcp, '.pr-http');
    add({
      chapter: 'Appendix', layout: 'scroll', title: 'G. MCP reference',
      panel: [group(heading('Trust boundary'), fig('fig-mcp')), group(heading('Latency'), fig('fig-mcp-latency')), group(heading('Parity of direct and MCP results'), fig('fig-mcp-parity')), group(heading('Tools, resources and prompt'), catalogue), group(heading(`${(mcp.checks || []).length} failure behaviours observed`), checks), group(http), ...takeAll(c.mcp, '.pr-callout')],
      source: 'report.json: mcp; docs/mcp-demo-transcript.md; src/labourlens/mcp/server.py',
      notes: ['The tool catalogue, the recorded real-call refusal behaviours against a hostile test server, the loopback HTTP hardening attempts and the limits.']
    });
  });

  appendix('H', 'Limits in full', () => {
    const cards = limitsCardsFrom(c, specs);
    add({
      chapter: 'Appendix', layout: 'scroll', title: 'H. Limits in full',
      panel: [group(cards), ...[...(c.limits?.querySelectorAll('.pr-details') || [])].map(d => { d.remove(); d.open = true; return group(d); })],
      source: 'README.md, docs/system-card.md, docs/evaluation-report.md, docs/human-review/',
      notes: ['Every limit with its supporting file. T-I06 is highlighted.']
    });
  });

  appendix('I', 'Next steps in full', () => {
    const next = take(c.next, '.pr-next');
    add({
      chapter: 'Appendix', layout: 'scroll', title: 'I. Next steps in full',
      panel: [group(heading('Six experiments'), next), ...takeAll(c.next, '.pr-callout')],
      source: 'docs/evaluation-report.md, README.md, docs/deploy.md',
      notes: ['The six experiments with the measurement that would close each gap.']
    });
  });

  appendix('J', 'Work log reference', () => {
    const blocks = c.work?._blocks || [];
    const [timeline, registry, decisions, problems, review, spend] = blocks;
    add({
      chapter: 'Appendix', layout: 'scroll', title: 'J. Work log reference',
      panel: [timeline, registry, decisions, problems, review, spend].filter(Boolean).map(b => group(...[...b.children])),
      source: 'report.json: work, evaluation, security; docs/decisions.md, docs/progress.md',
      notes: ['Milestones, the experiment registry, the searchable decision log, the problems in full, the review process and the recorded spend.']
    });
  });

  appendix('K', 'Planning, data choices and operations', () => {
    add({
      chapter: 'Appendix', layout: 'scroll', title: 'K. Planning, data choices and operations',
      panel: [
        group(heading('Hypotheses as written'), rows([
          ['Retrieval, before any R1 or R2 number', 'H1: the named quarter and release raise hit@8. H2: an LLM rerank of the top 30 fixes ordering among near-duplicates. H3: the combination gains at least the larger single change. Null: nothing separates from the baseline beyond noise.'],
          ['Agent end to end, not a timestamped pre-registration', 'H1: filter plus rerank reduces missing-evidence abstentions. H2: explicit missing-data instructions help. H3: widening a weak pool helps. H4: a pricier generator is worth the price. H5: the planner should research the legitimate part of a rules-override question.'],
          ['BM25 original-test run, before the run', 'Three configurations named in advance and all reported whatever the outcome.']])),
        group(heading('Evaluation commitments from the requirements'), rows([
          ['Cases', 'At least 30 evaluation cases and a separate development set. Gold ids labelled after ingestion.'],
          ['Baseline', 'An explicit non-LLM baseline: BM25 with extractive passages.'],
          ['Comparisons', 'Controlled configurations, with model, prompt and corpus fixed.'],
          ['Metrics', 'Retrieval, correctness, groundedness, citations, abstention, calculation and security, with latency and cost.'],
          ['Review', 'A sample really reviewed by a human, and every negative result kept.']])),
        group(heading('Sources left out (D-003, D-006, D-040)'), rows([
          ['Foreign workforce datasets', 'Last updated June 2024, so stale.'],
          ['Wages, annual retrenchment incidence, short work-week', 'Lower fit with the quarterly scope; the short work-week dataset may lack 2026 Q2.'],
          ['MTI GDP revision pairs', 'Not labour evidence. Rejected by the owner.'],
          ['MTI and MAS pages without verified links', 'No PDF links found on the MTI page and a maintenance page at MAS.']])),
        group(heading('Operations'), rows([
          ['Logged', 'A record per run with outcome, tool calls, cost and timings. Identifiers are hashed and secrets redacted.'],
          ['Not logged', 'Raw addresses, session ids and hidden model reasoning. Full evidence text is omitted by default.'],
          ['Limits', 'Login, session and address rate limits, a body size limit, concurrency limit, a daily budget and a kill switch.']]))
      ],
      source: 'docs/requirements-matrix.md, docs/experiments/, docs/decisions.md, docs/audit-and-logging.md; detailed planning notes now kept locally',
      notes: ['Full text of the planning, data-choice and operations material that the main slides summarise.']
    });
  });

  appendix('L', 'Calculation fix in detail', () => {
    add({
      chapter: 'Appendix', layout: 'scroll', title: 'L. Calculation fix in detail',
      panel: [
        group(heading('Rule declared before the run, and what happened'), dataTable('Development questions (237), tool set v2, one run per model', ['Criterion', 'Main model', 'Second model'], [
          ['Right kind of response at least 205 and 209 of 237', '212 pass', '213 pass'],
          ['False-answer cases at most 6', '7 fail', '7 fail'],
          ['No ungrounded number where the new tool was used', '1 of 10 fail', '3 of 18 fail'],
          ['Cases with an ungrounded number at most 34 and 51', '27 pass', '30 pass'],
          ['Operational failures at most 0', '0 pass', '1 fail (provider error)'],
          ['Overall', 'Fail', 'Fail']])),
        group(heading('Second fresh set, 65 questions (diagnostic only)'), dataTable('Before and after, same questions', ['Measure', 'Main model', 'Second model'], [
          ['Right kind of response, fresh 65 post-fix (not the served-chain sample)', '.754 to .908', '.723 to .846'],
          ['Better and worse cases', '10 and 0', '9 and 1'],
          ['Number comparisons right, of 14', '3 to 12', '3 to 10'],
          ['Over-abstentions', '13 to 3', '14 to 7']])),
        group(heading('How to read it'), list(['The fix was designed after studying errors on these 65 questions, so the gains are optimistic.', 'The development set has few questions that need arithmetic on report text.', 'Not adopted. A clean development pass and a threat run are needed first.']))
      ],
      source: 'experiments/eval/agent-dev-X3-REPORT.md, experiments/tool-fix/criteria.json, docs/decisions.md D-048, docs/experiments/m7-tool-fix.md',
      notes: ['Counts come from the criteria file and the two evaluation reports named in the source path; they are not in the report data. The first table is the pre-declared rule for the development run; the second is the post-freeze diagnostic. Cost about $3.45 retained, about $4.95 in total with a discarded first attempt.']
    });
  });

  appendix('M', 'Live app against the evaluated system', () => {
    const ch = c.serving;
    const blocks = [...(ch?.querySelectorAll('.pr-block') || [])];
    blocks.forEach(b => b.remove());
    add({
      id: 'served-versus-evaluated', chapter: 'Appendix', layout: 'scroll', title: 'M. Live app against the evaluated system',
      panel: blocks.map(b => { const whole = el('div'); whole.append(heading(text(b, '.pr-block-title')), ...[...b.children].filter(n => !n.classList.contains('pr-block-head'))); return group(whole); }).concat(takeAll(c.serving, '.pr-callout').map(n => group(n))),
      source: 'report.json: serving, mcp; docs/decisions.md; experiments/triage; experiments/corpus-snapshots',
      notes: [`Serving uses corpus v4, a Q1 2020 start, native function calling with reasoning off, planner_v7/answer_v9, triage_v4 and contextualise_v3, four tools including annual_average, and streaming. The code order is small talk, follow-up rewrite, scope classification, then agent. Final evaluation used v3.1, a Q1 2024 start, structured planning, planner_v1/answer_v3 and three direct tools, without web steps. The current combination is not re-evaluated. ${contextSentence(serving)}`, 'The served default is mcp_stats: get_series and annual_average reach the ten-tool statistics server, while search and change calculation stay in process. Historical all-tools MCP was slower and not adopted. A separate historical 65-case served-chain sample, 51 reused development cases plus 14 probes, scored 90.8% with no observed loss against direct calls, not proof of equivalence.', 'Current serving also caps report context at 20 passages, runs independent calls within a round concurrently and caches identical successful searches for 300 seconds. Default/evaluated tools have ten-second limits; served report search has 25 seconds plus one conditional timeout retry of at most 12 seconds within the run deadline. These additions have offline checks, not new live quality or latency measurements. Source: served.py, graph.py and D-083 to D-092.']
    });
  });

  appendix('N', 'Concepts and where they appear', () => {
    add({
      chapter: 'Appendix', layout: 'scroll', title: 'N. Concepts and where they appear',
      panel: [group(conceptGrid())],
      source: 'LabourLens prompts and system design',
      notes: ['Planner prompt excerpt: \u201cRound 1: gather evidence. Round 2 (only if needed): a calculation, or one more lookup after an error or a gap.\u201d The answer prompt requires citations and forbids model arithmetic. The reranker ranks exact evidence by period, population, measure and release. A judge scores claim support against cited evidence; code scores deterministic figures.', 'Embedding vectors use text-embedding-3-large. BM25 and dense rankings combine with reciprocal rank fusion. Questions and evidence are bounded; structured answers are validated. Historical experiments did not vary sampling or reasoning controls and used provider defaults. The served native function-calling planner explicitly sends reasoning_effort none (D-078).']
    });
  });

  appendix('O', 'Trying the Decisions API', () => {
    add({
      id: 'decisions-api', chapter: 'Appendix', layout: 'solo', title: 'Trying the Decisions API',
      visual: decisionsExperiment(),
      caption: 'Two trials, different populations. Faster v2 routing, but neither trial passed. Not adopted.',
      source: 'experiments/eval/decisions-api-results.json; experiments/eval/decisions-api-v2-results.json',
      notes: [
        'Two frozen completed trials, not a shipped agent change. The API model was gpt-6-luna only. v1 primary A70 used a .7 confidence threshold: 397/409 in each repeat, below the preregistered 407/409 minimum. A0 diagnostic scored 405/409 each repeat. Historical C baseline was 408/409, recoverable from stored paired accuracy deltas. v2 D scored 138/150 each repeat against contemporaneous C at 150/150, 150/150 and 149/150. The v2 preregistered minimum was 148/150, an absolute two-error allowance, not a scaled v1 threshold. Different denominators and populations mean no paired cross-trial gain.',
        'v2 used 150 AI-authored and AI-labelled questions, not human-reviewed truth. Three repeats of each question are dependent, not 450 independent questions. D threshold .7 and iteration 1 were selected on development only before the fresh trial. In-scope diversions were D 6/270, F2-070 and F2-072 in each repeat, versus C 1/270, F2-065 in the third repeat. All 30/30 serious-harm D calls were provider refusals. Refusals produced no predicted unsafe route and the configured fallback failed open to the agent. This is a structural routing failure, not successful unsafe classification or evidence that the downstream agent caused harm.',
        'The main latency bars use v2 contemporaneous case-paired timings: median of case medians C 1.3915125001 s versus D .3623366251 s across 150 questions. C generates a reply; D returns classification with no generated reply. Contemporaneous does not establish pure endpoint causality or an end-to-end swap. v1 timing was historical, not contemporaneous: 1.563 s versus .3593592921 s on 409 questions. No judge-latency comparison was made and there was no live adoption.',
        'The claim-support screen used 441 selected dependent claims from saved answers from both generator models, gpt-6-luna and gpt-5.6-luna, across development, original test and fresh questions and both retrieval arms. These are not 441 independent questions. Three judge-omitted records were excluded before the frozen selection; this is not a subset-only verifier metric.',
        'The primary reference is a second-family AI judge, not human ground truth. Primary AUROC .8296794814, accuracy .8798185941 and balanced accuracy .6089403079 are compared with preregistered minima .80, .85 and .70. Coverage was 441/441. False support was 44/58 (.7586206897), exceeding the .20 maximum; the negatives here are AI-labelled partial claims, not verified unsupported negatives.',
        'Same-family original-judge labels are a sensitivity analysis, not the primary reference: AUROC .7857487767, accuracy .8163265306, balanced accuracy .5738958280. There are no verified unsupported negatives, so neither reference establishes unsupported-claim detection. AI reference errors, selection, dependent claims and repeated questions limit generalisation. Cluster-bootstrap intervals and strata remain in the immutable results; the face shows point estimates, not independent-sample confidence claims.',
        'Both trials failed their preregistered rules; v1 routing and support screens failed, and v2 D failed safety, quality and operational guards. Faster classification alone does not justify changing the live scope check, evaluator or agent. A two-way gate separating domain eligibility from unsafe intent is only an untested idea, not preregistered and not adopted.'
      ]
    });
  });

  appendix('P', 'Where the system still fails', () => {
    add({
      id: 'where-it-fails', chapter: 'Appendix', layout: 'solo', title: 'P. Where the system still fails', visual: failureResults(m),
      source: 'Final two-run evaluation, corpus v3.1; scored response-status mismatches',
      notes: FAILURE_NOTES
    });
  });

  // Appendix index lists the lettered slides.
  const idx = el('ul', 'deck-index');
  appendixIndex.forEach(([letter, title]) => idx.append(el('li', '', `${letter}. ${title}`)));
  indexSpec.visual = idx;
  indexSpec.indexItems = appendixIndex;

  // The order of the main deck, with each slide's place in the top navigation (stage index into FLOW_STAGES in deck.js:
  // 0 Sources, 1 Processing, 2 Retrieval, 3 Agent, 4 Answer, 5 Checks). Reordering a slide means moving its row here.
  const FLOW = [
    ['Singapore AI Agent for Workforce Policy Researchers', null, 'Start'],
    ['Assignment', null, 'Problem'],
    ['My project', null, 'Project'],
    ['Scope', null, 'Scope'],
    ['System architecture', 'all', 'System'],
    ['How the agent answers a question', 'all', 'System'],
    ['Data sources', 0, 'Sources'],
    ['Data findings', 0, 'Sources'],
    ['Retrenchment counts and their causes', 0, 'Sources'],
    ['Advance and final figures differ', 0, 'Sources'],
    ['Challenges with the data', 0, 'Sources'],
    ['Processing reports', 1, 'Processing'],
    ['Retrieval Strategies', 2, 'Retrieval'],
    ['Does filtering help?', 2, 'Retrieval'],
    ['Statistics lookup through MCP', 2, 'Retrieval'],
    ['Agent loop', 3, 'Agent'],
    ['Three example runs', 3, 'Agent'],
    ['Checking the answer', 4, 'Answer'],
    ['How I evaluated', 5, 'Checks'],
    ['Choosing models', 5, 'Checks'],
    ['Does better retrieval improve answers?', 5, 'Checks'],
    ['Attacks and defences', 5, 'Checks'],
    ['Agent Workbench', null, 'Workbench'],
    ['How I built it', null, 'How I worked'],
    ['Next steps', null, 'Next'],
    ['Improve the system', null, 'Next'],
    ['Deploy in production', null, 'Next'],
    ['Summary', null, 'Close'],
  ];
  const main = specs.filter(s => s.chapter !== 'Appendix' && s.layout !== 'appendix');
  main.forEach(s => {
    const at = FLOW.findIndex(f => f[0] === s.title);
    if (at < 0) throw new Error(`Slide "${s.title}" has no row in the flow table`);
    [, s.stage, s.chapter] = FLOW[at];
    s.flowAt = at;
  });
  main.sort((a, b) => a.flowAt - b.flowAt);
  specs.splice(0, main.length, ...main);
  const loop = main.find(s => s.id === 'agent');
  specs.find(s => s.title === 'L. Calculation fix in detail').notes.push('The original 65-question error review found 11 mismatches from missing report-text calculation, 3 other abstentions, 1 retrieval miss and 1 reasoning error. Report-only arithmetic was right on 3 of 14 cases. The extra tool experiment preserved that original result and failed two pre-set development criteria; the fresh diagnostic reused inspected questions and was not confirmation.');
  specs.find(s => s.title === 'L. Calculation fix in detail').notes.push('The change bundle added a fourth read-only tool, calculate_from_text_values, which does exact arithmetic on two figures printed in report passages; the existing change tool works only on dataset rows. It checks that each figure appears in the cited passage and refuses mixed units or bases. A wrong dimension label now returns the list of valid labels, and the graph grants one bonus search round after that error. The adoption criteria were declared before the run.', 'The development result failed for gpt-6-luna: behaviour accuracy fell from .903 to .895; false-answer cases rose from 6 to 7, above the limit of 6. Cases with an ungrounded number went from 25 to 27, and 1 of 10 cases that used the new tool had one, against a threshold of zero. Two criteria failed, so the tool set was not adopted.', 'The measurements show it did not help but do not establish why; whether the extra ungrounded numbers are the new tool\u2019s fault was not investigated per case. On the 65-case fresh set the model went from 3 to 12 correct of 14 number comparisons, but I designed the bundle after inspecting these cases, so this is an optimistic diagnostic, not confirmation.');


  // The slide face shows a plain-language source; report fields and file paths go to the speaker notes.
  specs.forEach(spec => {
    if (spec.chapter === 'Appendix') {
      if (spec.source) spec.notes = [...(spec.notes || []), `Source path: ${spec.source}`];
      spec.source = 'LabourLens project documents and evaluation runs';
    }
    if (spec.human) spec.source = spec.human;
    if (spec.srcPath) spec.notes = [...(spec.notes || []), `Source path: ${spec.srcPath}`];
    if (!spec.source && spec.layout !== 'title') spec.source = 'LabourLens report';
  });

  return specs;
}

function limitsCardsFrom(c, specs) {
  void specs;
  const wrap = el('div', 'pr-limit-grid');
  const cards = c.limits?.querySelector('.pr-limit-grid')?.children;
  if (cards) [...cards].forEach(card => wrap.append(card.cloneNode(true)));
  return wrap;
}
