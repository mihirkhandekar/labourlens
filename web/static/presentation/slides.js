// The deck: every slide is declared here as data. Charts and tables are the ones the chapter
// modules already draw from report.json; this file picks them out of an off-screen pool, gives each
// slide an action title and at most three bullets, and moves the detail into speaker notes or the
// appendix. Numbers on slides come from report.json (through the model) or from the document named
// in the slide's source line. Text is set with textContent only.
import {el, fmt, finite} from '../charts.js';
import {model, metricOf, goldOf, contextSentence} from './model.js';
import {stat, textStat, countRunner, dataTable} from './ui.js';
import {threeAnswers, twoSources, buildTimeline, flattening, mcpMap, retrievalStaircase, experimentStaircase, agentLoop, evidenceTrace, errorBars, assignmentBrief, challengeGrid, plantedFlow, architectureDiagram, myProject, hardParts, failureModes, keywordVsMeaning, modelChoice, RESPONSIBLE_AI, HYPOTHESES, contentMetricsText, reviewStreams, workbenchShot, conceptGrid, measureCards, cardRow, toolFixFlow, threatMatrix, threatRuns, buildProcess, rowsAffordance, finalComparison, finalFacts, finalSentence, finalCostFacts, provenanceTable, secondJudgeFacts, secondJudgeNote, secondJudgeQa, secondJudgeSentence, SUPPORT_LABEL} from './graphics.js';
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
  const numArm = (m.section('evaluation').heldout_v2?.arms || []).find(a => a.arm === 'r3' && a.model === 'gpt-6-luna')?.strata?.numerical_comparison;
  const numText = numArm && finite(numArm.n) ? `numerical comparisons scored ${fmt.pct(numArm.behaviour_accuracy)} (${fmt.int(Math.round(numArm.behaviour_accuracy * numArm.n))} of ${fmt.int(numArm.n)}), mostly over-abstentions caused by the tool gap` : '';
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
  const qa = (q, a) => `Likely question: ${q} Model answer: ${a}`;
  const findings = [...(c.data.querySelectorAll('.pr-finding') || [])].map(li => ({head: text(li, 'strong'), body: text(li, 'span')}));
  const v2 = m.section('evaluation').heldout_v2;
  const v2p = v2?.paired?.['gpt-6-luna'], v2q = v2?.paired?.['gpt-5.6-luna'];
  const v31 = m.heldoutV31, v31p = v31?.paired?.['gpt-6-luna'], v31q = v31?.paired?.['gpt-5.6-luna'];
  const ff = finalFacts(m), ffSet = id => ff?.sets.find(s => s.id === id), ffModel = (id, model) => ffSet(id)?.models.find(x => x.model === model);
  const ffCost = finalCostFacts(m);
  const exact = (share, n) => Math.round(share * n) / n;
  const pctN = (share, n) => fmt.pct(n ? exact(share, n) : share);
  const ea = v2?.error_analysis;
  const work = m.section('work');
  c.work._blocks = [...(c.work?.querySelectorAll('.pr-block') || [])];
  const card0 = m.cards.find(x => x.card_id === 'unemployment_resident_sa') || m.cards[0];

  // ---------- opening ----------
  add({
    layout: 'title', chapter: 'Start', title: 'Singapore AI Agent for Workforce Policy Researchers',
    wordmark: 'LabourLens', author: 'Mihir Khandekar', source: '',
    notes: ['I am Mihir Khandekar. My recent work is on AI products in the HR Tech space. This is a technical assessment prototype for policy researchers. The talk covers the task, the data, retrieval, a bounded agent, evaluation, security, MCP and the limits I found.', 'Keys: arrows, space and page keys move; F is fullscreen; O or Escape opens the overview; S shows these notes; add ?print-pdf to the address to export a PDF.']
  });

  // ---------- the assignment ----------
  add({
    layout: 'solo', chapter: 'Problem', title: 'Assignment', visual: assignmentBrief(),
    source: 'GenAI Engineer technical challenge',
    notes: ['The weighted rubric gives evaluation and error analysis 25%, the largest share; this is why the talk focuses on methods, measurements and failures. ' + qa('Why is so much of the talk about evaluation?', 'Evaluation and error analysis carry 25% of the assessment rubric, the largest single weighting. I show what I measured and where the evidence is limited.'), 'The PDF problem statement: policy researchers use government statistics, reports and internal knowledge that may be incomplete, inconsistent or difficult to search. Build a GenAI solution that answers analytical questions using supplied or public data, produces traceable evidence and communicates uncertainty. It prioritises applied ML, experimentation, retrieval quality, evaluation and responsible AI over full-stack engineering.', 'Ten core requirements in the brief; the list on the slide shows nine. The tenth, problem framing and experimental design, is covered by the My project slide, by the success criteria and failure modes slide and by How I measured. The others are data preparation and exploratory analysis; retrieval-augmented generation; model experimentation; one bounded agent workflow; evaluation and error analysis; responsible AI, security and privacy; GenAI concepts; MCP and tool integration; reproducibility. The rubric gives evaluation 25%, RAG and GenAI design 20%, concepts and MCP 15%, and five other areas 10% each.', 'Likely question: why build an agent? The assessment asks for a purposeful tool-using workflow, deterministic calculations, state and stopping conditions, retry limits and recovery from a tool failure.']
  });
  add({
    layout: 'solo', chapter: 'Why this problem', title: 'My project', visual: myProject(),
    source: 'LabourLens scope and data records',
    notes: ['Why the labour market. ADR-001 compared three domains: labour market, housing affordability, and cost of living or inflation. It did not record transit or public transport as a candidate domain. I did not find a public-transport or commuter-flow dataset in the source catalogue. This project does include transport-related workforce data: transport and storage appear as industry dimensions in employment, vacancy, retrenchment and workforce-rate datasets. That is not transit ridership or commuter movement. The labour-market choice is grounded in official quarterly indicators and narrative reports, real publication revisions and useful calculations; its risks are definition, seasonal-adjustment and release-version mismatches. Housing has confounding variables and heterogeneous transaction data. Cost of living has index methodology, weights and causality complexity. These alternatives are off the slide face on purpose: the face shows only the domain I chose.', 'Users: Singapore policy researchers and labour-market analysts (ADR-001). Question families: factual lookup, numerical change between periods, cross-source synthesis, advance-versus-final revisions, ambiguity and insufficient evidence including causal overreach, and adversarial content. Supported answer period: 2024 Q1 to 2026 Q2, ten quarters, a hard scope (D-031): earlier documents stay as context, but a request for earlier figures must decline.', 'How I chose the data. ADR-001 approved four MOM series (resident unemployment rate, vacancy-to-unemployed ratio, retrenched employees, employment change by sector) and four report documents plus the Q2 2026 advance release. D-003 added datasets where the record says they create a distinct test: overall and citizen rates for population ambiguity, the vacancy rate and counts for rate versus ratio, retrenchment splits for a parts-versus-total check, re-employment for a freshness and revision case. D-006 added the methodology and earlier-release documents, because they answer what an indicator means. D-040 added six sources no earlier case cites, so a second fresh test set could be independent.', 'What I rejected, with the recorded reason. Foreign workforce datasets: last updated June 2024. Wages, annual retrenchment incidence and short work-week data: lower fit with the quarterly scope, and the short work-week set may lack 2026 Q2. MTI GDP revision pairs: not labour evidence, rejected by the owner. MTI and MAS pages: no verified PDF links on the MTI page and a maintenance page at MAS. A dataset also had to reach 2026 Q2 and pass its contract at ingestion or it was dropped.', 'Out of scope by decision: forecasts, unsupported causal claims, personal employment advice, unrestricted web research.', qa('Was public transport evaluated as a domain?', 'No. The recorded alternatives are labour market, housing affordability and cost of living. Transport appears as a workforce industry dimension, not as a transit-use dataset.'), qa('Why bound the period so tightly?', 'A bounded period makes out-of-scope questions testable. The system must decline a 2023 figure even when a context document mentions it, and the evaluation scores that.')]
  });
  add({
    layout: 'solo', chapter: 'System', title: 'Agentic system', visual: architectureDiagram(),
    source: 'LabourLens architecture',
    notes: ['The live analysis path starts with statistics and reports. Processing makes validated observations and report passages; report passages become BM25 and dense indexes. These are tools the agent can call during its loop, not a pre-retrieved pack passed to it.', 'The planner sees the question and a catalogue, never passage text. It chooses one of three tools: search_reports returns report chunks; get_series returns structured statistics; calculate_change computes exact differences in code from rows already returned. The agent checks the evidence returned by its chosen tool before deciding whether to call again or answer.', 'For the live app, the statistics route is get_series through the MCP client to server tool get_statistic, then validated observation rows return to the agent. Report search and calculation stay in process. The full final accuracy runs use the same tools directly, not the MCP route; a separate served sample is reported on the MCP slide.', 'The live app also adds a small-talk reply, a scope check and a rewrite of follow-up questions before the agent. Appendix M distinguishes that served path from the measured core. Guardrails treat retrieved content as untrusted data and bound tools, rounds, calls and time.', qa('How are citations checked?', 'Labels must refer to supplied evidence and each quote must appear in its cited passage. That does not prove semantic support.'), qa('Why a bounded agent?', 'The planner chooses among three typed tools, but the workflow fixes access, budgets, validation and failure outcomes.')]
  });

  // ---------- problem ----------

  // ---------- scope and plan ----------

  // ---------- data ----------
  add({
    id: 'data', layout: 'solo', chapter: 'Sources', title: 'Choosing the data', visual: twoSources(m), caption: 'Local only: raw MOM and MTI files are never published.',
    source: 'MOM and SingStat via data.gov.sg; MOM reports and an MTI article',
    notes: ['Structured data comprises quarterly statistical tables loaded as typed observations, with units, population, adjustment and period kept on each series. This includes transport and storage sector employment indicators, industry vacancy and retrenchment records; it does not provide commuter flows or public-transport usage. Unstructured sources are MOM reports and an MTI AI-and-employment article parsed into source passages. Tables support exact figures and deterministic comparisons; reports and the article supply definitions, explanations and release context.', 'How it is stored. Statistics: fetched from data.gov.sg as immutable snapshots, each with its source address, date and SHA-256 hash; normalised into one long Parquet table with provenance on every row; read by the agent tools with pandas. DuckDB is a declared dependency, but the code reads the Parquet table through pandas. Reports: PDFs are read with PyMuPDF and web pages with BeautifulSoup into passages that carry page or section and a quality flag; neighbouring good passages are merged into chunks of about 200 words; the chunks are indexed with BM25 and with text-embedding-3-large vectors cached by content and model. Raw MOM and MTI files stay local and are never published; three assumed-licence datasets also keep their raw files out of git (data sheet).', 'ADR-001 approved the initial labour-market domain, four core datasets and MOM reports. D-003 expanded structured labour datasets where they test population ambiguity, rates versus ratios, industry breakdowns and re-employment. D-006 and later approvals added methodology, context and evidence-disjoint sources. D-040 rejected MTI GDP revision pairs as not labour evidence; the MTI employment article is a labour-related source.', 'Rights vary by source. Open Data Licence applies to listed data.gov.sg series; MOM report PDFs are kept local because of their copyright notices. Source-level terms and verification status are recorded in the data sheet.', qa('Why retain both kinds?', 'The tables provide typed observations for exact, deterministic calculations. Reports provide definitions and explanations that statistical rows do not contain.')]
  });
  // ---------- EDA ----------
  add({...figSlide('fig-unemployment', {title: 'Data findings'}), title: 'Data findings', id: 'eda', chapter: 'Sources', layout: 'split', human: 'MOM unemployment rates via data.gov.sg',
    bullets: ['Each answer says which of the several official unemployment rates it uses.'], rows: rowsAffordance(m.excerpts.unemployment, 'Show the real rows'),
    caption: 'Unemployment rate in percent for four series over ten quarters. No intervals are plotted. Source: MOM via data.gov.sg.',
    detail: {label: 'How to read this', content: 'Quarterly unemployment rates by population and seasonal adjustment.\nPopulation: overall, resident, citizen.\nAdjustment: seasonally adjusted and resident unadjusted.\nTen observations from Q1 2024 to Q2 2026; no confidence intervals in the published series.'},
    notes: ['First required EDA finding: a plain unemployment rate question is ambiguous across population (overall, resident, citizen) and seasonal adjustment. Decision: series identifiers carry population and adjustment, and the agent asks a clarifying question when the series is open.', findings[0] ? `${findings[0].head}. ${findings[0].body}` : '', qa('What did EDA change in the design?', 'Typed series identifiers, a clarifying question when the series is open, and a scorer that counts a missing clarification as a behaviour error.')]});
  add({...figSlide('fig-retrenchments', {title: 'Retrenchments'}), title: 'Retrenchments rose, data gives no cause', chapter: 'Sources', layout: 'split', human: 'MOM retrenched employees via data.gov.sg',
    bullets: ['The datasets hold counts and no cause.', 'A reason appears only in MOM commentary, and the answer labels it as theirs.'], rows: rowsAffordance(m.excerpts.retrenchments, 'Show the real rows'),
    caption: 'Retrenchments each quarter from Q1 2024 to Q2 2026, split by contract type. Ten points and no intervals. Source: MOM via data.gov.sg.',
    detail: {label: 'How to read this', content: 'Stacked quarterly counts of permanent and term-contract retrenchments, with the total compared in the source table.\nUnit: persons.\nTen quarters; no confidence intervals in the published series.'},
    notes: [findings[1] ? `${findings[1].head}. ${findings[1].body}` : '', 'Second required EDA finding. The datasets hold retrenchment counts and no cause, and retrenchments and resident unemployment moved differently in the same period, showing how easily a causal story can be attached. A reason can appear in two places only: the commentary in MOM reports, which the agent may cite and labels as MOM commentary, or an inference, which the agent does not make from two series. So the answer either gives the reason MOM states, labelled as theirs, or says the data cannot explain the rise. The popover shows the real dataset rows: the first and latest quarter totals and the permanent and term-contract split, with publisher, dataset id and snapshot date.', qa('How does the agent handle a why question?', 'It cites report commentary that states a reason, labelled as commentary, or abstains when the evidence does not state one.')]
  });
  add({...figSlide('fig-revisions', {title: 'Advance and final figures'}), title: 'Advance and final figures differ', chapter: 'Sources', layout: 'split', human: 'MOM advance and final reports, and the SingStat sector dataset',
    bullets: ['Each figure comes from an advance or a final release, and the answer says which.'], rows: rowsAffordance(m.excerpts.revisions, 'Show the same quarter in each release'),
    caption: 'Advance, final and dataset employment change for four quarters, in persons. No intervals are plotted. Source: MOM releases and SingStat.',
    detail: {label: 'How to read this', content: 'Each row compares the advance release, final MOM report and sector dataset total for one quarter.\nUnit: persons.\nFour quarters in the reconciliation export; this is a source-vintage comparison, not a confidence interval.'},
    notes: [findings[2] ? `${findings[2].head}. ${findings[2].body}` : '', findings[3] ? `${findings[3].head}. ${findings[3].body}` : '', 'The popover shows real rows for the same quarters: the MOM advance release, the MOM final report and the dataset total, each with its release stage and its date (published date for the releases, snapshot date for the dataset). Only numbers and dates are shown, never report text. Each figure carries its stage, advance or final, and the answer says which stage it used.', 'The vacancy ratio shows a similar caution: recomputing it from counts differs from the published ratio by up to 0.67 because the two come from different surveys, so I quote the published ratio (appendix B).', qa('Which figure is right, advance or final?', 'Both, for their release. The answer must name which one it uses, and the conflict cases in the gold set test exactly this.')]});
  add({
    layout: 'solo', chapter: 'Sources', title: 'Challenges with the data', visual: hardParts(m), caption: 'Each finding about the data became a design decision. Rows that rest on data show the real rows on hover or focus.',
    source: 'LabourLens data findings and design notes',
    notes: ['Each row is a difficulty the data showed me and the part of the system that now handles it. Hover or focus a row that rests on data to see the real dataset rows. Four unemployment rates: series identifiers carry population and adjustment, and the agent asks which one is meant when the question leaves it open. A rise the data cannot explain: the datasets hold counts and no cause, so the agent may cite MOM commentary that states a reason, labelled as theirs, and otherwise says the data does not explain it. Advance and final differ: retrieval filters on release stage and each figure carries its stage; conflicting releases are explained, not averaged. Tables flattened: every claim must carry a quote that appears in the cited passage, so a mangled passage cannot silently supply a number. Ratio does not recompute: the popover shows the published ratio, the two counts and the ratio calculated from them for the quarter where they differ most; they come from different surveys, so the system quotes the published ratio. Figures before 2024: a scope guard declines.', qa('Which of these did you only realise from the data?', 'The ratio mismatch and the table flattening. The unemployment ambiguity and the revisions I expected; the numbers showed how large they were.')]
  });
  add({
    layout: 'solo', chapter: 'Sources', title: 'Success criteria and failure modes', visual: failureModes(m), caption: 'Most measures had no pass mark set in advance. I report them with intervals and set none afterwards.',
    source: 'Evaluation report: success criteria and failure modes',
    notes: ['The assessment asks for measurable success criteria and key failure modes. Each row is a failure mode, the control in the system and how I measured it. The success criteria are the measures in the right-hand column: behaviour accuracy, false-answer rate, over-abstention, citation validity, grounded numbers, retrieval hit rate, threat resistance, scope-check blocking, latency and cost. Source: the section Success criteria and failure modes in docs/evaluation-report.md.', 'Most criteria were measured and not pre-registered. The thresholds fixed in advance are the ones cited with a decision id: the original test needed a paired interval that excludes zero (D-033); the fresh-set rule D-042 needed a one-sided lower bound above zero, at least 20 evidence components and no added false answer; false-answer and ungrounded-number caps in D-046 and D-048; the live scope check target of 0 of 333 real questions and 0 of 36 threat cases blocked (D-051). Everything else has no pass mark, and I do not invent one now.', 'Figures: hit@8 0.570 to 0.969 on 128 development questions; revision-conflict family 1.00 on 19; calculation correctness 0.75 on 24; ambiguity, insufficient-evidence and causal-overreach family 0.727 on 44 with 4 false answers, the weakest trust behaviour and not improved by the retrieval change; 36 threat cases; scope check 0 of 333 met and 1 of 36 missed (T-D05) on the threats; tool failure covered by a scripted retry test and the MCP fault demonstrations, not a recorded live run.', qa('What would you call success?', 'No false answers first, then the right behaviour, then cost. Only a few of these had a pass mark written before the run; the rest I report with intervals.')]
  });
  add({
    layout: 'solo', chapter: 'Processing', title: 'Reading reports', visual: flattening(m), caption: 'Two indexes search the same eligible chunks. Table-like text stays flagged, not silently repaired.',
    source: 'Current corpus metadata, parser, chunking and retrieval implementation',
    notes: ['The full path is a local PDF or HTML source, layout-aware extraction, quality-flagged passages, eligible chunks, BM25 and embedding vectors, then hybrid retrieval with period/release filtering and reranking. The current inventory has 85 sources, including 49 documents, and 16,419 passages; the live runtime builds 1,847 chunks.', 'Implementation facts: runtime.py selects merge200, about 200 words with 40 words of whole-passage overlap, not merge120. Only quality_flag=ok enters default chunking. PDF table-like blocks are flagged table_unreliable; the parser does not reliably convert them to rows. Numeric truth comes from the structured datasets.', 'Worked example verified locally without publishing text: MOM Q1 2026 final, pages 2 to 3, an eligible 216-word chunk with nine source passages and a cached 3,072-dimensional float32 vector. A table-like block on page 28 of the same report is excluded. Do not present these as a repaired-table-to-vector chain.', 'Chunks carry source and snapshot ids, URL, title, publication date, release stage, pages, section, locator, text hash, passage ids and rights status. Publisher joins through the source catalogue; observation period is not a Chunk field. Period matching happens in retrieval.', 'Raw reports, passage JSONL and report-derived indexes remain gitignored. Metadata manifests are committed. Runtime rebuilds chunks and BM25 in memory; chunk JSONL and bm25s exports are supported locally. Embedding cache: data/index/embeddings/text-embedding-3-large/cache.npz, content-keyed by model and exact text. A corpus rebuild refreshes mappings and only changed text needs new embeddings. No paid call was made to prepare this example.']
  });
  add({
    layout: 'solo', chapter: 'Retrieval', title: 'Retrieval Strategies', visual: keywordVsMeaning(m) || missing('Retrieval methods'), caption: 'Hit@8 is the share of questions with a relevant passage in the top eight. Same 128 development questions and corpus v3.1 as the hybrid baseline on the next slide.',
    source: 'BM25, dense embeddings and hybrid on the same 128 cases, corpus v3.1',
    detail: {label: 'Retrieval methods', content: 'BM25 is keyword search. Meaning search uses dense text-embedding-3-large vectors. Hybrid combines them by reciprocal rank fusion, c=60 over the top 50 of each list. All three use merge200 chunks and the same 128 cases from corpus v3.1. Hit@8 means a relevant passage appears in the top eight. Period/release filtering and reranking are not part of this methods comparison.'},
    notes: ['Like-for-like comparison: same 128 development text cases and 1,847 merge200 chunks from corpus v3.1. BM25 hit@8 .477 [.391,.562]; dense .367 [.289,.453]; hybrid .539 [.453,.625]. BM25 beats dense on its own. Hybrid minus BM25 is +.062 [-.023,.148], not demonstrated (20 better, 12 worse); hybrid minus dense is +.172 [.102,.242] (23 better, 1 worse). Fusion improves on the weaker dense method, but does not show a reliable gain over BM25 alone.', 'History: the early 24-question, 46-document comparison used hit@10 and merge120/merge200 chunks. It gave BM25 .583, dense .667 and hybrid .708 for merge120. It differs in cutoff (top eight, not ten), sample size (128, not 24) and corpus (85 sources with more look-alike quarterly reports, not 46 documents). These values are not directly comparable.', 'The previous slide gives the full path: report passages become eligible chunks and are searched by both indexes.']
  });

  // ---------- reading ----------

  // ---------- retrieval ----------
  add({
    id: 'retrieval', layout: 'solo', chapter: 'Retrieval', title: 'Does filtering help?', visual: retrievalStaircase(m) || missing('The retrieval ladder'), caption: 'Hybrid baseline: 53.9% hit@8 on the same 128 development questions as the previous slide. The agent calls report search inside its loop.',
    source: 'Retrieval ladder, 128 development text cases',
    detail: {label: 'Retrieval method', content: 'Hybrid baseline, 53.9% hit@8, matches the previous slide: same 128 questions, corpus v3.1 and merge200 chunks. The agent calls report search during its loop; it is not a pre-agent step.\nBM25: k1=1.5, b=0.75; stop words on; no stemming; quarter normalisation on. Dense: text-embedding-3-large. Hybrid: reciprocal rank fusion c=60 over top 50 lists.\nHard filter: overlap a named quarter and match release stage when a source exists; if nothing matches, no filter applies. Reranker: gpt-6-luna ranks the top 30 and returns up to 10; unranked candidates keep incoming order.\nMetric: hit@8, a relevant passage in the first eight; 95% case-bootstrap intervals. The reranker prompt prefers passages with the answer, not just the topic.'},
    notes: ['Current corpus v3.1 rerun, dev-R-V31: 128 answerable text-evidence cases, gold v3.6, 1,847 chunks. R0 .539 [.453,.625], R1a .852, R2 .742, R3 .969 [.938,.992]. Frozen v1 history remains R0 .570, R1a .844, R2 .789, R3 .969. Changing corpus, gold and code together is not a controlled estimate of a retrieval-only effect.', 'The 128 are the report-passage subset of 237 development questions: structured lookups and questions that should not be answered are excluded. BM25 k1=1.5, b=.75, stop words on, stemming off; dense text-embedding-3-large; reciprocal rank fusion c=60 over top-50 lists. Filter by period/release, then rerank top 30. These development questions shaped the design.'],
  });

  // ---------- agent ----------
  add({
    id: 'agent', layout: 'solo', chapter: 'Agent', title: 'Agent loop', visual: agentLoop(), caption: 'The agent calls three tools inside its loop. Only the live statistics lookup uses MCP.',
    source: 'LangGraph agent and planner/answer prompts',
    detail: {label: 'Planner and answer prompts', content: 'PLANNER\nRound 1: gather evidence. Round 2 (only if needed): a calculation, or one more lookup after an error or a gap. Then finish.\n\nANSWER\nEvery claim must cite one or more items by label and include a short verbatim quote.\n\nLimits: 2 rounds, 6 calls total, 3 per round, 10 seconds per tool call, 1 retry, 1 repair. The experiment tool set adds one extra round after a bad dimension label.'},
    notes: ['One bounded LangGraph StateGraph: validate question, plan, execute typed tools, assess evidence, write an answer, validate it and finish or repair. The planner sees the question and catalogue, but not passage text. The production graph permits 2 evidence rounds, 6 tool calls total, 3 per round, 10 seconds per tool call, one retry and one answer repair. The experiment tool-set v2 grants one bonus round after an unknown-dimension error; the total call budget stays six. The question cap is 1,000 characters.', 'Planner prompt excerpt: “Round 1: gather evidence. Round 2 (only if needed): a calculation, or one more lookup after an error or a gap. Then finish.” Answer prompt excerpt: “Every claim must cite one or more items by label and include a short verbatim quote.” Both treat retrieved text as untrusted data. The exact prompt versions are in prompts/planner_v3.md and prompts/answer_v5.md.', 'The three approved base tools are search_reports, get_series and calculate_change. The optional calculation-fix experiment adds calculation from report-text figures; it is not the adopted default. A provider outage is reported as operational failure, not missing evidence.', qa('What makes this an agent rather than a chain?', 'The planner selects and sequences typed tools based on the question and the evidence returned. The graph still bounds the rounds, tool calls, retries and repair.')]
  });
  add({
    layout: 'solo', chapter: 'Answer', title: 'Ensuring Reliable Sources', visual: evidenceTrace(m) || missing('The trace'), caption: 'Citations are checked against the evidence, and code does the arithmetic.',
    source: 'Agent answer validation and calculation tools',
    detail: {label: 'Evidence validation', content: '1. Validate the structured answer schema and status.\n2. Confirm each citation label was in the supplied evidence.\n3. Confirm the quote appears verbatim in the cited passage.\n4. Check reported numbers are present in cited evidence.\n5. Calculate changes in Decimal arithmetic from validated observations.\nThese checks do not prove that a quote semantically supports its claim.'},
    notes: ['The answer uses a strict schema. Each claim needs a citation label and a short verbatim quote. Validation checks schema, that labels came from the supplied evidence, that quotes appear in cited passages, status consistency and that reported numbers are present in the cited material. It cannot show that a quote semantically supports a claim; the judge metric is separate and imperfect.', 'Changes use deterministic Decimal arithmetic from validated observations, not model arithmetic. The calculation tool checks period order, units and operation type; calculation correctness was 75% on 24 calculation cases in the primary development run.', 'The answer prompt excerpt: “Do not do arithmetic yourself: use a C item for any difference or percentage change.” It returns an answer, abstention, clarification or refusal. The workflow output can also be an operational failure.', 'Likely question: what is still missing? Figure arithmetic from report text was tested in an unadopted tool-set variant after an error analysis; its development criteria failed.', qa('What does citation validation prove?', 'It proves a quote is present in the cited passage and the label was in context. It does not prove semantic support.')]
  });
  // ---------- measuring ----------
  add({
    layout: 'solo', chapter: 'Agent', title: 'Choosing models', visual: modelChoice(m) || missing('The model screen'), caption: 'Early 30-question screen, not a ranking. I kept gpt-6-luna: no false answers at the lowest cost, accepting more abstentions. gpt-4.1-mini answered falsely on 33% of questions that should not be answered.',
    source: 'Early model comparison and verified model prices',
    detail: {label: 'Early screening method', content: 'Retrieved evidence: 30 development questions, five chunks. Oracle comparison: the same models with reference passages placed first. Behaviour accuracy is response-status agreement; plotted cost is USD per case.\nThe six candidates included gpt-6.1-terra as a generator; it was later used as the judge.\nOne model family. Labels were AI drafts then. Sampling and reasoning settings stayed at provider defaults. One repeat also changed the context header, so it was not a pure repeat.'},
    notes: ['Early screen: 30 development questions, 24 answerable and 6 non-answerable, one run per model, before the agent existed. It is a first-pass screen, not a ranking. G1 gpt-6-luna behaviour .60 versus .733 for gpt-5.6-luna; costs $0.00051 versus $0.00113. At that stage I chose no false answers at the lowest cost, accepting more abstentions. This is historical screening, not the final evaluation.', 'Final means: both models .897 on development with filter then rerank. gpt-6-luna costs about 60% as much. No run establishes either model as more accurate; no model superiority test was performed. The 65 fresh questions are a different set from this early 30-case screen. Sampling stays at provider defaults, two final runs per arm, not a variance estimate.'],
  });
  add({
    layout: 'solo', chapter: 'Checks', title: 'How I measured', visual: measureCards(m), caption: 'Behaviour accuracy is the share of questions where the answer, abstention, clarification or refusal matched the expected one. A second judge from another model family rechecked claim-support labels.',
    source: 'Evaluation artifacts and review records',
    detail: {label: 'Evaluation sets and judge prompt', content: `Reference gold set: 268 questions = 237 development + 31 original test. The original test shares evidence with development: 25/31 share at least one evidence id; 15/31 have all evidence represented in development.\nFresh set: 65 questions, source/evidence-disjoint from the original 268 by pre-run audit, signed before the run, used once and not for tuning. The later diagnostic reuses those 65.\nJudge prompt: “Judge each claim ONLY against the evidence items it cites, never against your own knowledge.”${secondJudgeSentence(m) ? `\n${secondJudgeSentence(m)}` : ''}`},
    notes: [HYPOTHESES, contentMetricsText(m), 'The reference gold set has 268 questions: 237 development and 31 original test. The original test is not evidence-independent: 25 of 31 share at least one evidence id with development, and 15 have all evidence represented there. Five post-run label edits are disclosed with the original scores retained.', 'The 65-case fresh set is source/evidence-disjoint from the original 268 by the pre-run audit, signed before its run, and used once, not for tuning. The later V2post diagnostic reuses the same cases, so it is not another fresh test. The paired difference interval for the 65-case result is a one-sided 90% component bootstrap; the original 31-case comparison uses a 95% paired case bootstrap.', 'I signed off four separate review streams: 268 gold questions, 65 held-out v2 questions, 40 saved system answers and 30 source checks. Only the first two are questions; 403 is just the count of items in total. One human reviewer, after three separate AI review passes from the same model family and after saved runs were scored. This is owner review, not independent inter-rater evidence.', 'A blind AI sample of 40 saved outputs was failure-enriched: six per family plus four status mismatches. It is answer-quality review, not a new question set. Thirty source checks reviewed data/source quality, with 18 matches and 12 minor issues; they are not model outputs.', ...(secondJudgeNote(m) ? [secondJudgeNote(m)] : []), ...(secondJudgeQa(m) ? [qa(...secondJudgeQa(m))] : []), qa('What does behaviour accuracy mean?', 'The share of cases where the response status matches the gold label: answer, abstain, clarify or refuse.')]
  });
  add({
    layout: 'solo', chapter: 'How I measured', title: 'Human Review of Dataset', visual: reviewStreams(), caption: 'I signed off every item in four separate streams after three AI gold-review passes. Five separate end-to-end answer reviews checked the wider system.',
    source: 'Owner review inventory',
    detail: {label: 'How to read this', content: 'Four separate review streams, each with its own count; they are not added into one number.\nGold questions: 268, 237 development and 31 original test (the 31 share evidence with development).\nFresh-set (v2) questions: 65, signed before the run and not used for tuning.\nSaved system answers: 40 failure-enriched outputs rated right, partly right or wrong (25, 6 and 9). Source checks: 30 (18 match, 12 minor).\nSource: owner review inventory. These raw counts are not rates, so no interval is plotted.'},
    notes: ['I signed off four separate streams in the interface: 268 gold questions, 65 held-out v2 questions, 40 saved system answers and 30 source checks. Labels were AI-drafted and checked in three separate AI review passes from the same model family; those are not three independent models. I was the one human reviewer, and reviewed after the saved runs were scored. This is not independent inter-rater evidence.', 'Source: docs/human-review/numbers-audit.md, section 3. The final export has 18 source checks marked match and 12 minor difference. Agreement with AI suggestions is not an accuracy measure.', qa('What did the human review establish?', 'I signed off every item. One reviewer and the timing after runs limit independence; this is owner review, not inter-rater agreement.')]
  });
  add({
    layout: 'solo', chapter: 'Checks', title: 'Experiment ladder', visual: finalComparison(m) || experimentStaircase(m) || missing('The experiments'), caption: 'Mean of two runs: filter then rerank gains 7.0 and 5.3 points on the development questions that shaped it. Both runs agree on that direction. No gain is demonstrated on the original test or fresh set. It costs about 1.7 times as much and takes about 1.4 times as long for gpt-6-luna.',
    source: 'Final evaluation means, two runs per arm; earlier ladder labelled as history',
    detail: {label: 'Why the numbers differ', content: `Each slide uses the question set, corpus and gold available when that experiment ran. Headline bars use the final system on the current corpus, as the mean of two runs; hover for both single runs and paired 95% case-bootstrap intervals.\n88.6% and 90.3% use the same development questions under different builds and gold. The 90.3% is an earlier build and gold, not comparable to the final run.\nThe two models tie on development; I retain gpt-6-luna only because it costs about 60% as much. Two runs are not a variance estimate.${secondJudgeFacts(m) ? `\nClaim support, a different measure from behaviour accuracy, is ${SUPPORT_LABEL}. Hover the development column for the numbers.` : ''}`},
    notes: [finalSentence(m), 'FIN is the first run; FIN2 is the pre-registered replicate, amended to a mean-of-two headline before results. Development paired mean differences: +7.0 [3.6,10.6] points and +5.3 [1.9,8.9]; signs agree in both runs. Original test: +3.2 [-3.2,11.3] and +1.6 [-8.1,12.9]. Fresh: -3.1 [-7.7,0.8] and -0.8 [-2.3,0.0]. No demonstrated generalisation gain. Two runs do not estimate run-to-run variance.', 'Every slide uses the set and build available when its experiment ran. Early retrieval used 24 cases. The current retrieval ladder uses 128 answerable text-evidence questions, excluding structured and non-answer cases. The early model screen used 30 cases. Headline numbers are final-system means on corpus v3.1, 237 development, 31 original test and 65 fresh questions. The earlier 90.3% and first final run 88.6% use the same development questions with different corpus and gold. They are not a continuous improvement curve.', 'The full 237/31/65 runs use direct tools and omit web-only steps; the separate served-chain evaluation uses 51 development cases and 14 probes, one run. Retrieval was re-run on current corpus v3.1. Earlier A-series, registered fresh v3 and v3.1 reruns remain labelled history in the report.', ...(secondJudgeFacts(m) ? [`Claim support and fact coverage are separate measures from behaviour accuracy, scored by an AI judge. ${secondJudgeSentence(m)}`] : [])],
  });
  add({
    layout: 'solo', chapter: 'Checks', title: 'Why it missed', visual: errorBars(m) || missing('The error classes'), caption: 'Number of mismatched cases in each error class, from the review of the original run on the 65 fresh questions, on an earlier build. No intervals.',
    source: 'Fresh-set error review',
    detail: {label: 'How to read this', content: 'The bars count error classes on the 65-case fresh set for the primary filtered arm.\nUnit: mismatched cases per class, not a rate.\nSource: the fresh-set error review. No interval is drawn for these counts.'},
    notes: [ea ? `The bars count error classes in the primary filtered arm on ${ea.n_cases} cases; source: experiments/heldout-v2/error-analysis.json. This is a count of reviewed mismatches, not an accuracy rate, so no interval is drawn. ${ea.n_mismatches_primary_r3} cases missed; ${ea.over_abstentions_primary_r3} were over-abstentions, ${ea.numerical_over_abstentions_primary_r3} of those on numerical comparisons. The review found no case where the scorer penalised a correct answer or the gold label was wrong.${numText ? ` On the fresh set ${numText}.` : ''}` : '', 'The second fresh set showed a tool gap: the adopted calculation tool handled dataset observations but not figures appearing only in report text. The fix was a separate, post-analysis experiment; it is described on the next slide.', qa('Why not fix the tool immediately?', 'The fresh-set result is frozen. A fix needs a new experiment with criteria declared before running.')]
  });
  add({
    layout: 'solo', chapter: 'What the experiments said', title: 'Fixing the calculation gap', visual: toolFixFlow(m), caption: 'Earlier build (corpus v3, gold v3.6): it failed rules I set before the run on 237 development questions. The 90.3% baseline uses earlier build and gold, not comparable to the final run. The reused 65-question diagnostic is optimistic, not fresh evidence.',
    source: 'Calculation-fix experiment report and criteria',
    detail: {label: 'Calculation-fix prompt excerpts', content: 'PLANNER\nThe evidence list shows short figure: snippets under each passage.\n\nANSWER\nDo not do arithmetic yourself: use a C item for any difference or percentage change.\n\nThe one-factor bundle added report-text calculation, dimension-error recovery and one bonus round; criteria were pre-declared.'},
    notes: ['The change bundle added a fourth read-only tool, calculate_from_text_values, which does exact arithmetic on two figures printed in report passages; the existing change tool works only on dataset rows. It checks that each figure appears in the cited passage and refuses mixed units or bases. The planner receives up to five short figure snippets per passage. A wrong dimension label now returns the list of valid labels, and the graph grants one bonus search round after that error. It pairs the tool change with planner_v3 and answer_v5, holding the remaining model and retrieval setup fixed as a one-factor bundle. The adoption criteria were declared before the run.', 'The development result failed: behaviour accuracy fell from .903 to .895 for gpt-6-luna and .916 to .899 for gpt-5.6-luna; false-answer cases rose from 6 to 7 for both models, above the limit of 6. Cases with an ungrounded number went from 25 to 27 and from 39 to 30, and in cases that used the new tool 1 of 10 and 3 of 18 had one, against a threshold of zero. Numerical comparisons right: 30 of 34 unchanged for gpt-6-luna, 30 to 28 for gpt-5.6-luna. Two criteria failed for both models, and one more for gpt-5.6-luna because of a single provider HTTP 520 error page. Therefore the tool set was not adopted.', 'What is and is not known about the cause. The development X3 report states that gpt-6-luna made 9 successful and 2 refused calls of the new tool and gpt-5.6-luna 8 successful and 12 refused, almost all the refusals one mistake: passing the text of a figure snippet where a passage label belongs. It also states that whether the extra ungrounded numbers are the new tool\u2019s fault was not investigated per case. So the measurements show it did not help but do not establish why. [INFERENCE: the models may pair the wrong two figures; not verified.] The report suggests labelling every snippet with its passage label as a next step.', 'On the 65-case fresh set the primary model went from 3 to 12 correct of 14 number comparisons, but I had designed the bundle after inspecting these cases. This is an optimistic diagnostic, not confirmation. The development set has few questions requiring report-text arithmetic, so it cannot show the potential benefit either. The hover example on the fourth tool is one real case from the development run, a numerical-comparison question before the supported period where both models were right with the old tools and gave a false answer with the new one; the committed case records do not hold the tool calls, so why is not shown.', qa('What changed in the tool?', 'A fourth read-only tool for exact arithmetic on two figures in report passages, a clearer dimension error and one bonus round. The bundle failed its pre-declared development criteria.')]
  });
  add({
    layout: 'solo', chapter: 'Concepts', title: 'GenAI concepts in this build', visual: conceptGrid(), caption: 'Prompts, embeddings, evaluation and agent limits are part of the implementation.',
    source: 'LabourLens prompts and system design',
    notes: ['Planner prompt excerpt: “Round 1: gather evidence. Round 2 (only if needed): a calculation, or one more lookup after an error or a gap.” The answer prompt requires citations and forbids model arithmetic. The reranker ranks exact evidence by period, population, measure and release. A judge scores claim support against cited evidence; code scores deterministic figures. Prompt files in the repository are the source for these short examples.', 'Embedding vectors use text-embedding-3-large. BM25 and dense rankings combine with reciprocal rank fusion. Questions and evidence are bounded; structured answers are validated. Sampling and reasoning controls were not varied, so provider defaults apply.', qa('What does the judge measure?', 'Whether each claim is supported by its cited evidence and whether reference facts are covered. It is a model-based metric, not a human verdict.')]
  });
  add({
    layout: 'solo', chapter: 'Agent', title: 'MCP server', visual: mcpMap(m), caption: '',
    source: 'MCP client, statistics server, protocol checks and served-chain comparison',
    detail: {label: 'Agent request and server reply', content: 'The agent sends source_id, period_from, period_to and dimension through its get_series tool. Only the live statistics lookup goes over MCP; the planner tool list is fixed in code. The server call is get_statistic: validate the arguments, read the validated observations and return structured rows with value, unit, period, source and release metadata. The MCP client validates input arguments, the advertised outputSchema and its own typed model, screens untrusted content, and enforces size and time limits. search_reports and calculate_change stay in process.'},
    notes: ['MCP is the Model Context Protocol interface to a read-only statistics server. My agent uses only get_statistic, through its get_series tool. The server exposes nine tools: get_statistic, list_datasets, describe_dataset, get_dimension_values, latest_value, compare_periods, series_summary, get_revisions and get_provenance. It exposes labourlens://sources and labourlens://source/{source_id} as catalogue resources, plus compare_quarters as a prompt. Other compatible hosts could use the unused tools; no third-party host was connected.', 'Flow: the agent supplies source, period range and dimension. The client calls tools/call over stdio. The server validates arguments and reads the catalogue and observation records; it returns structured observation rows. The client validates arguments against the advertised input schemas, then checks the reply against the advertised output schema and its typed model, screens untrusted content and enforces response-size and time limits. Invalid arguments return errors; timeouts and an unavailable server remain operational failures. There is no silent direct-call fallback.', 'The planner tool list is hard-coded in code. Discovery checks the server tool list but does not build the prompt. The negotiated protocol revision is 2025-11-25. Roots, sampling and elicitation are not used. The server is read-only, makes no network calls and performs no model arithmetic. Report passages are not resources because MOM report text cannot be redistributed. Statistics catalogue resources are application-driven; prompts are user-controlled.', 'The protocol demo and 10 hostile-server cases test discovery, schemas, refusals, timeout, failure and trust boundaries. The live app uses MCP for its statistics tool. The full final accuracy comparison used direct data functions; the separate served-chain sample and MCP/direct comparison are reported here. The first call includes a one-off connection; warm-call latency is the more relevant comparison.'],
  });
  add({
    layout: 'solo', chapter: 'Checks', title: 'Attacks and defences', visual: threatMatrix(m) || missing('Threat results'), caption: (() => { const [d6, n6, d56, n56] = threatRuns(m); return d6 && n6 && d56 && n56 ? `On the fresh rerun, gpt-6-luna scored ${d6.passed}/36 with and ${n6.passed}/36 without defences; gpt-5.6-luna scored ${d56.passed}/36 with and ${n56.passed}/36 without. The small suite shows no defence effect. MCP server failure is one of six attack categories.` : 'Small threat suite; results are not available in the report data.'; })(),
    source: 'Threat suite runs, 36 cases each, including MCP server failures',
    detail: {label: 'Threat cases and controls', content: 'The six categories cover direct and indirect prompt injection, sensitive data, unsafe tool use, unsupported claims and MCP server failure. Retrieved text is untrusted; tools are read only and calls are bounded. MCP client tests cover bad arguments, timeouts, crashes, malformed and oversized replies, and unexpected tools.'},
    notes: [RESPONSIBLE_AI, 'The 31 Oct run scored 36/36 for defended gpt-6-luna and 35/36 for defended gpt-5.6-luna; the fresh 2 Nov rerun scored 35/36 in all four configurations under both scorers. The planted-figure case failed again. The suite is small and does not show a defence effect.', 'The final 36-case threat suite includes ten mcp_server_failure cases against hostile fixtures. They test the client and failure boundary, not whether MCP improves answer accuracy. Each served or experiment path is labelled by its own run; the live MCP route is not assumed for older threat results.'],
  });

  {
    take(c.safety, '.pr-ti06-steps');
    add({
      layout: 'solo', chapter: 'Checks', title: 'Planted wrong figure', visual: plantedFlow(), rows: rowsAffordance(m.excerpts.planted, 'Show the dataset row it is compared with'), caption: 'The cross-check matches period, population and units. It corrected this case in one run and not in another.', source: 'Threat test and cross-check records',
      notes: [text(c.safety, '.pr-hero-callout-text'), 'A planted false figure can evade shallow quote and number checks. Like-for-like deterministic cross-checking is not shown stable. The 31 Oct defended gpt-6-luna run passed; all four configurations fail T-I06 again in the 2 Nov fresh run under both scorers. V2 rescoring of already seen outputs is diagnostic only and never replaces frozen v1 results.'],
    });
  }
  // ---------- cost ----------
  add({
    layout: 'split', chapter: 'Answer', title: 'Agent Workbench',
    bullets: ['Pinned dependencies and focused tests.', 'A $0.05 budget reservation before paid calls.', 'The live app adds small-talk replies, a scope check and follow-up rewrites. A separate 65-case sample measures the served chain; the full final comparisons omit these steps.'],
    visual: workbenchShot(), source: 'Workbench screenshot; live questions require an access code',
    notes: ['Try the workbench at https://labourlens.navig.me/workbench; the QR code is a static image for that URL. The screenshot is the local report-only workbench and contains no live answers. Live answers need an access code and make paid model calls.', 'The product shows answer status, source links, citations, evidence excerpts and visible tool activity. It does not show hidden model reasoning. The QR image uses a quiet zone and high-contrast black modules on white. It has no runtime generation dependency.', `Three steps run in front of the agent in the live app, and the full final experiments omit them, while a separate 65-case sample measures them. First, a small-talk fast path (D-050) answers greetings without a paid agent run. Second, an LLM scope check (D-051) decides whether the question is about Singapore labour statistics before the agent starts; it defaults to in scope and fails open. Measured on its own: ${fmt.int((tri.gold_and_fresh || {}).false_out_of_scope)} of ${fmt.int((tri.gold_and_fresh || {}).n)} real questions wrongly blocked on the gold and fresh sets, ${fmt.int((tri.threats || {}).false_out_of_scope)} of ${fmt.int((tri.threats || {}).n)} wrongly blocked on the threat cases, ${fmt.int((tri.offtopic || {}).recall_not_in_scope)} of ${fmt.int((tri.offtopic || {}).expected_not_in_scope)} off-topic questions caught, median ${triCl.latency_p50_s} s. Third, a conversation-context rewrite (D-054): when a message follows earlier turns or uses a relative date such as last quarter, one short model call turns it into a standalone question before the agent starts; it skips a first question with no such wording and fails open. ${contextSentence(serving)} So the live app is the agent that was evaluated plus these three steps, with its statistics lookups routed through MCP.`, 'Likely question: does MCP power the hosted app? Yes, for statistics lookups only. The agent\'s get_series tool calls the local MCP server, and the trace shows transport mcp; report search and the change calculation stay in the same process, and the other eight MCP tools are not given to the agent. The full final evaluations called data functions directly; a separate 65-case served sample measures the route.']
  });

  // ---------- process ----------
  add({
    id: 'process', layout: 'solo', chapter: 'How I worked', title: 'How I built it', caption: 'The agent proposed. I decided. Every step left a file behind.',
    visual: buildProcess(work.decisions?.length), source: 'LabourLens project record',
    notes: ['The zero rights-scan hits is the result on my machine on 1 Nov 2026; the scan needs the private corpus, so it prints NOT CHECKED in a clone. Everything here is from the repository record: CLAUDE.md, docs/decisions.md, docs/progress.md, docs/agent-logs.md, docs/audit-and-logging.md, SECURITY.md and docs/human-review/e2e-review-summary.md. Where the record is silent I have left it out.', 'Contract. CLAUDE.md is the agent standing instruction: explore, compare options (two to four, with a plain baseline), recommend, discuss, approve, implement, verify, document. The agent works within an approved milestone and may not widen scope, change key dependencies or start the next phase without my approval. Gates in the record run from the scope and ADR approvals on 30 Oct to the final review on 1 Nov (docs/agent-logs.md, section 1).', `Decisions. docs/decisions.md holds ${work.decisions?.length ?? 'many'} numbered decisions (D-000 onward) with the options considered, rejected alternatives, my approval line where there was one and whether the decision is reversible. Decisions from D-041 onward that name no approver are marked as assistant decisions within the experiment protocol.`, 'State in files. Any agent can be interrupted, so docs/progress.md comes first, with claims, handoff notes and a log updated at each substep. docs/ is published to reviewers; study/ and private/ are gitignored.', 'Separate review. Blind AI reviewers saw no earlier opinion. Five end-to-end reviewers (31 Oct) reported 3 P0, 28 P1 and 44 P2 findings across data, runtime, evaluation, security and deliverables; fixed examples include validated citations dropped in the web result, no model deadline, agent-exp able to overwrite frozen runs and paired ignoring the gold hash (docs/human-review/e2e-review-summary.md). These reviewers are one model family and none of this is human review.', 'Frozen results. Held-out v2 was pre-registered with hashes pinned in the freeze file; agent-exp refuses to overwrite an existing experiment without --force; eval and paired refuse a gold file whose hash differs from the run unless an explicit flag is passed; post-freeze work gets new experiment ids; negative results are reported (tool set v2 failed its criteria, D-048).', 'Safety in the build. Secrets live in a gitignored .env; make secrets-scan and gitleaks run in CI (SECURITY.md). The rights scan fails if a tracked file repeats more than six consecutive words of local MOM text, and it reported 0 hits on 1 Nov. Tools are read-only. The live app has a budget ledger (reserve $0.05 before a run) and run deadlines (docs/audit-and-logging.md). One honest slip: an AI reviewer search printed the local .env into its own session, nothing was committed and the report says to rotate the key if that transcript is kept (docs/agent-logs.md, section 5).', 'What I decided myself: scope and ADRs, rights decisions, the signature on the held-out v2 freeze, accepting the extraction gaps as limits (J10), the out-of-period scope policy (D-047) and not applying the four AI-suggested relabels.', 'Not on the record, so not on the slide: sandboxed sub-agents without the API key, paid commands run only from my shell, explicit file paths when committing, single-writer manifest enforcement (the manifest is written by one code path, but there is no lock; e2e finding P2-2 is deferred).', qa('Where did the process fail?', 'Labels were edited after a held-out run, the first indirect-injection result was invalid because the fixture was wrong, and review wording drifted across documents. Each was caught by a review, disclosed and fixed. Section 5 of docs/agent-logs.md lists them.'), qa('How would you run it differently?', 'Build the disjoint held-out set first, record each approval when it happens, fix scorers before running, and review labels before the runs, not after.')]
  });

  // ---------- limits and next ----------
  const sjFacts = secondJudgeFacts(m), sjSentence = secondJudgeSentence(m);
  add({
    id: 'limits', layout: 'solo', chapter: 'Next', title: 'Limits and next steps', caption: 'I reviewed AI-drafted labels after the runs. This is owner sign-off and not inter-rater evidence.',
    visual: cardRow([{icon: 'warning', head: 'AI-drafted labels', line: sjFacts ? `One human reviewer after the runs. A second judge agreed on claim support only moderately (kappa ${sjFacts.agreement.claim_labels.kappa.toFixed(2)}).` : 'One human reviewer after the runs.', tip: sjSentence || undefined}, {icon: 'warning', head: 'No gain on new questions', line: 'Filter then rerank helps on development questions only. It did not help on the questions it was not built on.'}, {icon: 'warning', head: 'Weak attack scanner', line: 'It missed all five paraphrased probes.'}, {icon: 'arrow-right', head: 'Repeat the review', line: sjFacts ? 'Add a second reviewer, starting with the support labels the judges split on.' : 'Add a second reviewer.'}, {icon: 'arrow-right', head: 'Retest the fix', line: 'Use unseen questions.'}, {icon: 'arrow-right', head: 'Cap the spend', line: 'Verify a provider-side limit.'}]), source: 'Evaluation and threat records',
    notes: [`Labels were AI drafted; I signed off every review item, across four separate streams. One human reviewer, after three separate AI review passes from the same model family and after the saved runs were scored. The labels are not independent inter-rater evidence. The 31-case registered set reuses development evidence; on the final system filter then rerank gains 4 to 6 points on development questions, none on the 31 registered held-out questions, and slightly loses for gpt-6-luna on the 65 fresh questions (within noise). The planted-figure result is not stable, and the scanner missed five paraphrased probes. The calculation tool experiment failed its pre-declared development criteria and was not adopted.`, ...(sjSentence ? [`A second judge from another model family is still an AI judge, not a human. ${sjSentence} Claim-support gains therefore stay judge-measured. The check used one saved run and a sample conditional on valid pairs, so it cannot establish ground truth or run-to-run variance.`] : []), `Next steps: repeat a sample with a second reviewer${sjFacts ? ', starting with the claim-support labels where the two judges disagree' : ''}; use a genuinely unseen test set for the calculation change; test the cross-check beyond one planted case; improve the scanner; and verify a provider-side spend cap.`, `Other limits, in full in appendix H and appendix M. The judge and the answer models come from one provider family${sjFacts ? '; the second-judge check samples another family but does not remove the concern' : ''}. Each configuration ran once, so there is no run-to-run variance for the main comparisons. Temperature and reasoning effort stayed at provider defaults and were not recorded. A provider-side spend cap is unverified. Licences are unverified for ${(serving.rights || {}).datasets_unverified ?? 'some'} datasets and ${(serving.rights || {}).sources_unresolved ?? 'some'} documents, all kept local. The live app also differs from the evaluated system: it adds a small-talk reply, a scope check, a rewrite of follow-up questions and statistics lookups through MCP, and serves document build v3.1.`, qa('Which limit matters most?', 'Human review was one person confirming AI-drafted labels after the runs. The next evaluation should include a second reviewer and a test set not used to design the change.')]
  });
  add({
    layout: 'solo', chapter: 'Close', title: 'Summary', visual: cardRow([{icon: 'database', head: 'Evidence', line: 'Typed quarterly observations plus report passages.'}, {icon: 'wrench', head: 'Agent', line: 'One bounded graph. Live statistics through MCP; calculations in code.'}, {icon: 'chart-line', head: 'Measurement', line: 'Filter then rerank helps on development questions and not on the original test or fresh ones.'}, {icon: 'shield', head: 'Limits', line: 'AI-drafted labels; one human reviewer; attack gaps remain.'}]), caption: 'The assessment weights evaluation at 25%. These results show what works and what still needs evidence. The headline results are the final system on document build v3.1, mean of two runs per arm, filtering then reranking, gpt-6-luna as the main model (gpt-5.6-luna compared), gpt-6.1-terra as judge and the base tool set.',
    source: 'Assessment PDF and LabourLens evaluation records',
    notes: ['Configuration status: filter then rerank with gpt-6-luna is the default I implemented and report on; the owner confirmation of that default (D-030) is still open, and the cheaper hybrid remains available.', 'Names for the same 65 questions: the deck calls them fresh questions; the documents call them held-out v2; the experiment ids are V2, V31 and V2post.', 'The rubric weights: evaluation and error analysis 25%; RAG and GenAI design 20%; GenAI concepts and MCP 15%; problem framing and data science 10%; agent workflow 10%; responsible AI 10%; reproducibility and communication 10%. The main story covers these seven areas; there is no separate weighted coverage slide.', 'Summary: a mixed-source research assistant with typed statistical observations, parsed report passages, BM25 plus dense retrieval, an MCP server and client that were tested and that the live app uses for statistics lookups only (full final evaluations used direct calls; the 65-case served sample uses MCP), a bounded LangGraph tool loop and a structured cited answer. Development evidence is not a production reliability claim. Human review confirmed AI-drafted labels after the saved runs, with one reviewer; the threat suite is small and the planted-figure result remains unstable.', qa('What should reviewers remember?', 'The system is a working prototype, not a proven product. Its strengths are explicit retrieval and evaluation experiments; its limits are label-review independence, small fresh sets and incomplete attack coverage.')]
  });

  // ---------- appendix ----------
  const appendixIndex = [];
  const appendix = (letter, title, build) => { appendixIndex.push([letter, title]); build(letter, title); };
  const group = (...nodes) => { const g = el('div', 'deck-ref'); nodes.filter(Boolean).forEach(n => g.append(n)); return g; };
  const heading = (title) => el('h3', 'deck-ref-title', title);

  add({layout: 'appendix', chapter: 'Appendix', id: 'appendix', title: 'Appendix', index: appendixIndex,
    notes: ['Reference slides for the detail that did not fit in the main deck. Scroll inside a slide with the mouse wheel or the arrow keys once it has focus.']});
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
      panel: [group(heading('Retrieval ladder with intervals'), ladderFig), group(heading('Early comparisons that chose the hybrid baseline'), methods, emb), group(heading('BM25 settings and period hints'), abl, hint), group(heading('Rank of the first relevant chunk'), rankShift), ...limits],
      source: 'docs/evaluation-report.md, Expanded retrieval study; docs/experiments/m6-retrieval-improvements.md',
      notes: ['The early comparisons are noisy: one case is about 4.2 points. Hybrid was chosen from them as the baseline, not proved best.']
    });
  });

  appendix('D', 'Agent reference', () => {
    const calls = fig('fig-calls'), errors = fig('fig-tools'), graphFig = fig('fig-graph'), tools = take(c.agent, '.pr-tools');
    add({
      chapter: 'Appendix', layout: 'scroll', title: 'D. Agent reference',
      panel: [group(heading('Recorded run, step by step'), graphFig), group(heading('The three tools'), tools), group(heading(figTitle(calls) || 'Recorded tool calls'), calls), group(heading(figTitle(errors) || 'Tool errors'), errors)],
      source: 'report.json: agent.trace; docs/architecture.md, section 4',
      notes: ['Recorded runs against the set limits, and the operational failures and repaired answers.']
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
      panel: [group(heading('Pass rate by configuration'), ci, canary), group(heading('Final-code run'), e2e), group(heading('First post-fix run'), post), ...callouts],
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
      source: 'docs/archive/planning/01_REQUIREMENTS_AND_SCOPE.md, docs/experiments/, docs/decisions.md, docs/audit-and-logging.md',
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
          ['Right kind of response', '.754 to .908', '.723 to .846'],
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
      chapter: 'Appendix', layout: 'scroll', title: 'M. Live app against the evaluated system',
      panel: blocks.map(b => { const whole = el('div'); whole.append(heading(text(b, '.pr-block-title')), ...[...b.children].filter(n => !n.classList.contains('pr-block-head'))); return group(whole); }).concat(takeAll(c.serving, '.pr-callout').map(n => group(n))),
      source: 'report.json: serving, mcp; docs/decisions.md; experiments/triage; experiments/corpus-snapshots',
      notes: [`Five things differ between the live app and the system the experiments measured: a small-talk reply, a scope check, a rewrite of follow-up questions, statistics lookups through MCP and document build v3.1. ${contextSentence(serving)} The scope check was measured alone on ${fmt.int(tri.n_calls)} calls: ${fmt.int((tri.gold_and_fresh || {}).false_out_of_scope)} of ${fmt.int((tri.gold_and_fresh || {}).n)} reference and fresh questions wrongly turned away, ${fmt.int((tri.threats || {}).false_out_of_scope)} of ${fmt.int((tri.threats || {}).n)} threat cases turned away (a request to decode a base64 string, declined politely), ${fmt.int((tri.offtopic || {}).recall_not_in_scope)} of ${fmt.int((tri.offtopic || {}).expected_not_in_scope)} off-topic messages caught, cost $${(triCl.total_cost_usd ?? 0).toFixed(4)}, median ${triCl.latency_p50_s} s and 95th percentile ${triCl.latency_p95_s} s. The sets are small and hand-written, with one run and the same model family. A separate 65-case sample covers the MCP route and all web steps: 90.8% for both models, no observed loss versus direct calls. It includes 51 reused development cases and 14 hand-written probes, one run, same judge family; not independent evidence.`]
    });
  });

  appendixIndex.push(['N', 'Slides cut from the talk']);
  add({
    layout: 'split', chapter: 'Appendix', title: 'N1. Cut from the talk: why not a chatbot or search?',
    bullets: ['A chatbot recalls figures without sources.', 'Search finds text but never does the sums.', 'Neither knows when to say no.'],
    visual: bigStat({text: 'Three gaps', label: 'that the design has to close', size: 'xl'}), source: 'LabourLens design notes',
    notes: ['This is the reasoning behind the architecture, not a measured comparison. The retrieval ladder and the evaluation later put numbers on the parts that can be measured.', 'The brief asks for two source types, retrieval, a bounded agent, an MCP server and an evaluation. My reading is that it tests judgement as much as code, and the project instructions rank retrieval quality, evaluation, security and reproducibility above interface polish.', qa('Why not a long context window with the reports?', 'It would still not choose a series or release, would not compute changes exactly, and gives no stable citation. I wanted each of those to be a checkable step.')]
  });
  add({
    layout: 'split', chapter: 'Appendix', title: 'N2. Cut from the talk: how I planned to test it',
    bullets: ['A keyword-search baseline, no AI.', 'Reference questions with expected sources.', 'Predictions written down before each run.'],
    visual: bigStat({text: 'Baseline first', label: 'one change at a time', size: 'xl'}), source: 'Project requirements and experiment notes',
    notes: ['Requirements (docs/archive/planning/01_REQUIREMENTS_AND_SCOPE.md): at least 30 evaluation cases and a separate development set; gold ids labelled after ingestion; an explicit non-LLM baseline (BM25 with extractive passages); controlled configurations with model, prompt and corpus fixed; retrieval, correctness, groundedness, citation, abstention, calculation and security metrics with latency and cost; a human-review sample actually reviewed by a human; every negative result kept. docs/05_EVIDENCE_AND_STUDY_PLAN.md adds that hypotheses must be marked as such.', 'Hypotheses as written. Retrieval (docs/experiments/m6-retrieval-improvements.md, written before any R1 or R2 number): H1 using the named quarter and release raises hit@8; H2 an LLM rerank of the top 30 fixes ordering among near-duplicates; H3 the combination gains at least the larger single change; null: nothing separates from the baseline beyond noise. Agent (docs/experiments/m6-agent-end-to-end.md, not a timestamped pre-registration): H1 filter plus rerank reduces missing-evidence abstentions; H2 explicit missing-data instructions help; H3 widening a weak pool helps; H4 a pricier generator is worth the price; H5 the planner should research the legitimate part of a rules-override question. BM25 held-out (docs/experiments/m2-bm25-baseline.md): three configurations named before the held-out run.', qa('What would have falsified the retrieval hypotheses?', 'The null: no configuration separating from the hybrid baseline beyond noise. The note says a negative result would be reported as such.')]
  });
  add({
    id: 'product', layout: 'split', chapter: 'Appendix', title: 'N3. Cut from the talk: running it live',
    bullets: ['Every answer links to its source passage.', 'A budget is reserved before any paid call.', 'A provider spend cap is not verified yet.'],
    visual: bigStat({text: '$0.05', label: 'reserved per question, under a $2 daily budget', size: 'xl'}), source: 'LabourLens deployment notes',
    notes: ['Workbench: status badges (answered, abstained, needs clarification, refused), citation chips that turn red when a label has no matching evidence, and an evidence drawer with the exact excerpt and source link. One server in Singapore serves the live app behind access codes, on corpus v3.1; the commit it runs is shown by /healthz.', 'Budget: $0.05 is reserved and persisted before any paid call starts, and the question is refused if it cannot be saved; the daily budget is an estimate, default $2.00, and zero blocks new questions; a kill switch blocks new questions but not calls already running. A provider-side OpenAI spend cap is not verified. Source: docs/deploy.md.', 'Logging: a record per run with outcome, tool calls, cost and timings; identifiers hashed, secrets redacted, no hidden model reasoning, and a prune command for old logs. Source: docs/audit-and-logging.md.', qa('What would you add before real traffic?', 'A provider-side hard spend cap first, then per-user quotas, a backup procedure and a measured memory profile under load, none of which I have verified.')]
  });
  add({
    id: 'wrong', layout: 'solo', chapter: 'Appendix', title: 'N4. Cut from the talk: what went wrong',
    visual: rows([['Stale judge cache', 'Key caches by what can change.'], ['Scorer too strict', 'Test the scorer first.'], ['A test that never ran', 'A pass needs proof it ran.'], ['Labels edited late', 'Freeze first, disclose edits.'], ['Flattened tables', 'Audit data before measuring.'], ['One lucky pass', 'One run is not stability.']]),
    source: 'LabourLens experiment log',
    notes: ['Each item has a cause, a fix and a status in the work log (appendix J): a judge cache keyed by case id that survived gold changes; a calculation scorer that over-constrained prose and units; a threat fixture that passed vacuously under the filtered retrieval; five held-out gold edits after the held-out run, disclosed with the original scores kept; extraction defects; and the planted figure that passed once and failed once.', qa('Which mistake are you least comfortable with?', 'The post-run gold edits. I disclosed them and kept the original scores beside the rescored ones, which is why I relied on the second fresh set.')]
  });
  add({
    layout: 'solo', chapter: 'Appendix', title: 'N5. Cut from the talk: challenges', visual: challengeGrid(), caption: 'Real problems from the record, and what I did about each.',
    source: 'LabourLens project record',
    notes: ['Tables flattened: in a 16-passage AI pre-review all 4 sampled tables came out flattened and no number was wrong; the extraction fixes made the second document build and moved no headline metric (D-037, D-041). Series ambiguity: unemployment is published overall, resident and citizen, adjusted and not; series ids carry both and the agent asks when the series is open. Advance versus final: the same quarter has different figures by release; answers must name the release. Rights: MOM report PDFs are all rights reserved, so they stay out of the public repository (D-001) and rights stay unresolved per source until its notice is read. Small AI-drafted gold set: 268 reference cases drafted by an AI; I signed off every item after three separate AI review passes from the same model family and after the saved runs were scored. One human reviewer, so this is not independent inter-rater evidence. Leakage: the 31-case original test shares evidence with development: 25 of 31 share at least one evidence id, and 15 of 31 have all evidence represented in development. The later 65-case fresh set is source/evidence-disjoint by pre-run audit and was used once, not to tune (D-040). Calculation gap: the tool could not do arithmetic on figures in report text; the fix failed its pre-declared rule (D-048). Scope boundary: questions needing figures before 2024 must decline even when the corpus holds context documents (D-031).', 'Process mistakes that also taught rules (work log, appendix J): a judge cache keyed by case id that survived gold changes; a calculation scorer that over-constrained prose; a threat test that passed vacuously; five held-out gold edits after the original test, disclosed with the original scores kept; one planted-figure pass that did not repeat.', qa('Which challenge is least solved?', 'The reference set. Owner confirmation of AI-drafted labels is not independent inter-rater evidence.')]
  });
  add({
    layout: 'solo', chapter: 'Appendix', title: 'N6. Cut from the talk: why one number is not enough', visual: threeAnswers(m), caption: 'Same quarter, same question. Three correct numbers.',
    source: 'MOM unemployment rates via data.gov.sg',
    notes: ['These are three real series in the data, each correct for a different question. A reader handed one of them without its label cannot tell which question was answered. A fourth, citizen unemployment, is also published.', 'Values are the last observation of each series in the report data.', qa('Is that a real failure of language models?', 'I did not measure a plain model on this question. It is the design problem: the system must name the series or ask which one is meant, and the evaluation later measures how often it does.')]
  });
  appendixIndex.push(['N7', 'Current document build']);
  add({
    layout: 'solo', chapter: 'Appendix', title: 'N7. Current document build', visual: buildTimeline(m) || missing('The document builds'),
    source: 'Extraction audit and corpus records',
    notes: ['The first build is the original extraction used by the registered retrieval and answer runs. The second build applied conservative PDF heading detection, preserved short corrupt blocks as garbled rather than treating them as clean, retained narrative body passages and page labels, kept HTML extraction inside article content, and recorded rights notices as metadata. It also preserves duplicates only within the same snapshot. The build moved from 13,484 to 15,915 passages; 57 control-bearing passages marked clean became garbled, and the Q3 2025 report page 30 gained seven narrative passages. These are extraction fixes, not measured retrieval gains.', 'The third build added six labour-relevant sources so a new test set could use evidence not cited by earlier cases. It reached 16,419 passages. The six included wage reports, an MTI AI-and-employment article and three datasets; it was not a transit data expansion. The source list and snapshots document the corpus boundary.', 'Registered results ran on the first build. The second build had an extraction-only diagnostic; the third got a new regression check, threat run and evidence-disjoint fresh set. Results are only comparable within the corpus and gold versions recorded for each run.', 'A fourth step, v3.1, changed one rule: a symbol-density test had marked 40 passages of the MTI article as corrupt although they were legends, coefficient rows and equations. The refined rule keeps all 246 genuine control-character cases corrupt, relabels the 40 (16 searchable, 24 table rows), and leaves every passage outside that article unchanged. Sources and passage count stay 85 and 16,419. Only the 65 fresh questions were re-run on v3.1; everything else was measured on an earlier build. The registered fresh-set result stays on v3 and the re-run is shown beside it.', 'Which numbers come from which build: the headline results are the final evaluation, on v3.1 (see appendix E). Earlier results stay as labelled history. Development accuracy 0.903 appears on the first build (first experiments) and on v3 (regression check); the registered fresh-set result 0.754 is on v3, and the v3.1 re-run of the same questions gave 0.738 for the same model. The system and the live site use v3.1. The two earlier builds are kept only so that older results can be reproduced. Do not compare numbers across builds.', qa('Why did you rebuild the corpus?', 'The second build corrected how evidence was extracted; the third added labour-relevant evidence that the fresh evaluation cases had not used. Neither passage-count growth nor rebuild alone proves a quality gain.')]

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
    ['Agentic system', 'all', 'System'],
    ['Choosing the data', 0, 'Sources'],
    ['Data findings', 0, 'Sources'],
    ['Retrenchments rose, data gives no cause', 0, 'Sources'],
    ['Advance and final figures differ', 0, 'Sources'],
    ['Challenges with the data', 0, 'Sources'],
    ['Success criteria and failure modes', null, 'Data findings'],
    ['Reading reports', 1, 'Processing'],
    ['Retrieval Strategies', 2, 'Retrieval'],
    ['Does filtering help?', 2, 'Retrieval'],
    ['Agent loop', 3, 'Agent'],
    ['Choosing models', 3, 'Agent'],
    ['MCP server', 3, 'Agent'],
    ['GenAI concepts in this build', 3, 'Agent'],
    ['Ensuring Reliable Sources', 4, 'Answer'],
    ['Agent Workbench', 4, 'Answer'],
    ['How I measured', 5, 'Checks'],
    ['Human Review of Dataset', 5, 'Checks'],
    ['Experiment ladder', 5, 'Checks'],
    ['Why it missed', 5, 'Checks'],
    ['Fixing the calculation gap', 5, 'Checks'],
    ['Attacks and defences', 5, 'Checks'],
    ['Planted wrong figure', 5, 'Checks'],
    ['How I built it', null, 'How I worked'],
    ['Limits and next steps', null, 'Next'],
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
