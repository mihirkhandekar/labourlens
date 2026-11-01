// The report: one band per step of the story, in the order the deck tells it. Graphics, charts and
// tables are the presentation's own modules (same data, same copy); the paragraphs here are short
// summaries that read their numbers from report.json through the same model. Where a number is not
// in report.json, an adjacent note names where it comes from.
import {fmt, finite} from '../charts.js';
import {model, metricOf} from '../presentation/model.js';
import {answerCard, aboutMe, requirementGrid, domainChoice, taskAndLeftOut, architectureDiagram, twoSources, buildTimeline, flattening, hardParts, challengeGrid, modelTable, costBars, retrievalStaircase, keywordVsMeaning, agentLoop, experimentStaircase, freshQuestions, errorBars, toolFixBars, evidenceTrace, mcpDiagram, conceptGrid, threatPanels, plantedFlow, reviewStreams, measureCards, workbenchShot, cardRow, coverageMap} from '../presentation/graphics.js';
import {dataTable} from '../presentation/ui.js';
import {el, band, stage, chartBox, sub, more, group, rows, statRow, table, commands, link, note} from './report-kit.js';
import {buildPool} from './report-pool.js';
import {processLoop} from './report-process.js';

const MODELS = ['gpt-6-luna', 'gpt-5.6-luna', 'gpt-4.1-mini'];
const REPO = 'https://github.com/mihirkhandekar/labourlens/blob/master/';

/** The nav labels, in order. Each id is a band below. */
export const STEPS = [
  ['about', 'About me'], ['assignment', 'The assignment'], ['problem', 'Why this problem'], ['system', 'The system'], ['data', 'The data'],
  ['eda', 'What the data showed'], ['hard', 'Hard parts'], ['models', 'Models'], ['retrieval', 'Retrieval'], ['agent', 'The agent'],
  ['tools', 'Tools and MCP'], ['safety', 'Safety'], ['review', 'Human review'], ['ops', 'Cost and deployment'], ['process', 'How I built it'],
  ['limits', 'Limits'], ['coverage', 'Coverage'], ['run', 'Run it']
];

const missing = what => el('p', 'rp-missing', `${what} is not available in the report data.`);
/** Run a builder; a failure shows a plain notice for that graphic only. */
const safe = (what, build) => {
  try { return build() || missing(what); } catch (error) { console.error(`report: ${what}`, error); return missing(what); }
};
const pct = fmt.pct;
const rate = (row, key) => metricOf(row?.metrics?.[key]).rate;
const usd = value => finite(value) ? `$${value.toFixed(4)}` : 'not recorded';

export function heroCard(report) {
  const m = model(report);
  return stage(safe('The answer card', () => answerCard(m)), {design: 760, label: 'A sample answer with its citation'});
}

export function buildBands(report) {
  const pool = buildPool(report);
  const m = pool.m;
  const bands = {};
  const to = m.scope[1], from = m.scope[0];
  const nQuarters = m.periods().length;

  // ---------- numbers used in the copy ----------
  const dev = id => m.evalRow(id, 'gpt-6-luna');
  const nDev = dev('dev-A3')?.metrics?.n_cases;
  const a1 = rate(dev('dev-A1'), 'behaviour_accuracy'), a3 = rate(dev('dev-A3'), 'behaviour_accuracy');
  const L = m.ladder?.configs;
  const costs = MODELS.map(name => m.evalRow('dev-A3', name)?.metrics?.cost_per_case_usd).filter(finite);
  const v2 = m.section('evaluation').heldout_v2;
  const v2m = v2?.paired?.['gpt-6-luna'], v2s = v2?.paired?.['gpt-5.6-luna'];
  const ea = v2?.error_analysis;
  const registered = m.paired[0]?.models?.['gpt-6-luna'];
  const types = m.section('sources').metrics?.by_type || {};
  const nSources = m.section('sources').metrics?.sources;
  const nDecisions = Array.isArray(m.section('work').decisions) ? m.section('work').decisions.length : null;
  const nThreat = m.securityRow('gpt-6-luna')?.metrics?.n_scored;

  // ---------- eda first: it claims figures that the data details must not repeat ----------
  const eda = band({
    id: 'eda', title: 'What the data showed',
    lede: ['Three findings changed the design. A plain unemployment question has several official answers, split by population and seasonal adjustment, so every answer has to name its series. Retrenchments rose while resident unemployment barely moved, which invites a causal story the data cannot support: the agent may cite MOM\u2019s own stated reason, labelled as commentary, or decline. And advance and final figures for the same quarter differ, so every answer names its release.']
  });
  const unemployment = pool.fig('fig-unemployment');
  eda.visual.append(unemployment ? chartBox(unemployment) : missing('The unemployment chart'));
  const pair = el('div', 'rp-pair');
  ['fig-retrenchments', 'fig-revisions'].forEach(id => { const f = pool.fig(id); pair.append(f ? chartBox(f) : missing('This chart')); });
  eda.visual.append(pair);
  eda.node.append(more('How the reports were read, and the validation checks',
    group('Reading the reports', 'Extraction flattened tables: in a sample of 16 passages checked against the original pages, all four tables came out with adjacent rows merged. Some passages lost a note boundary. No number was transcribed wrongly, and the numbers I answer from come from the datasets, not from table text. The schematic below shows what flattening does.', stage(safe('The flattening schematic', flattening))),
    group('', pool.fig('fig-vacancy-ratio'), pool.fig('fig-vacancies'), pool.fig('fig-quality')),
    pool.rest('data')));
  bands.eda = eda;

  // ---------- about ----------
  const about = band({
    id: 'about', title: 'Who I am',
    lede: ['I am Mihir Khandekar. My recent work is on AI products in HR Tech. This is my take-home for a GenAI Engineer role: a research assistant that answers questions about Singapore labour statistics with a source you can check, and declines when the data does not support an answer. This page follows the project in the order the work happened, with every experiment, including the ones that failed.']
  });
  about.visual.append(stage(safe('The introduction', aboutMe)));
  bands.about = about;

  // ---------- assignment ----------
  const assignment = band({
    id: 'assignment', title: 'The assignment',
    lede: ['The brief asks for an evidence-grounded policy research assistant: it answers analytical questions from government statistics and reports, shows the evidence behind each answer and says how sure it is. Evaluation and error analysis carries the most weight, so most of this page is about how I measured and what failed.']
  });
  assignment.visual.append(
    statRow([['25%', 'Evaluation and error analysis'], ['20%', 'RAG and GenAI design'], ['15%', 'GenAI concepts and MCP'], ['10%', 'Problem framing and data science'], ['10%', 'Agent workflow'], ['10%', 'Responsible AI'], ['10%', 'Reproducibility and communication']].map(([value, label]) => ({value, label})), {cols: 7}),
    note('Weights from the assessment brief.'),
    stage(safe('The requirements', () => requirementGrid(false))),
    note('Plus written deliverables, an innovation note and a live demonstration.')
  );
  bands.assignment = assignment;

  // ---------- problem ----------
  const problem = band({
    id: 'problem', title: 'Why this problem', layout: 'split',
    lede: [`I compared three domains and chose the labour market. MOM publishes official quarterly statistics and reports that disagree in checkable ways, such as advance against final figures, so abstention, conflict handling and arithmetic can all be tested. The answer period is fixed at ${fmt.quarter(from)} to ${fmt.quarter(to)}${nQuarters ? `, ${nQuarters} quarters` : ''}, and an earlier figure has to be declined. It is also a Singapore role, and my recent work is AI in HR Tech.`]
  });
  problem.visual.append(stage(safe('The domain choice', domainChoice), {design: 1100}));
  problem.node.append(more('The task, and what I left out', stage(safe('The task', taskAndLeftOut))));
  bands.problem = problem;

  // ---------- system ----------
  const system = band({
    id: 'system', title: 'The system, end to end',
    lede: ['Data moves left to right: sources, processing, retrieval, one bounded agent, then an answer in which every claim is cited, or a question back, a decline or a refusal. Two things run across all of it. Guardrails treat retrieved text as data, keep tools read-only and cap steps, retries and time. Evaluation uses reference questions, fresh sets and attack tests. I kept to one agent because every extra agent is another failure I would have to trace and measure.']
  });
  system.visual.append(stage(safe('The architecture', architectureDiagram)));
  system.node.append(more('Scope, question families and the answer pipeline', pool.rest('scope')));
  bands.system = system;

  // ---------- data ----------
  const data = band({
    id: 'data', title: 'Choosing the data',
    lede: [`Statistics give the numbers and reports give the explanations, so the answer needs both.${finite(nSources) ? ` The store holds ${fmt.int(nSources)} source records: ${fmt.int(types.dataset_csv)} statistic snapshots, ${fmt.int(types.report_pdf)} report PDFs and ${fmt.int(types.release_html)} release pages.` : ''} Open-licence statistics can be committed. MOM report PDFs carry a copyright notice, so they stay on my machine and only dataset snapshots are redistributed. I built the document store three times, and a result is only valid for the build it ran on.`]
  });
  data.visual.append(stage(safe('The sources', () => twoSources(m))));
  data.visual.append(sub('Three document builds', 'Each build fixed a problem the earlier one had. Most registered results ran on the first build, and the live application runs the third.', stage(safe('The builds', buildTimeline)), {note: 'Passage counts come from the README and the decision log, not from the report data.'}));
  bands.data = data;

  // ---------- hard parts ----------
  const hard = band({
    id: 'hard', title: 'Hard parts, and what handles them', layout: 'split',
    lede: ['Each difficulty the data showed became a design decision. The right-hand column names the part of the agent or the answer pipeline that now handles it. The quote check matters most for the flattened tables: a mangled passage cannot silently supply a number, because every claim has to carry a quote that appears in the cited passage.']
  });
  hard.visual.append(stage(safe('The hard parts', hardParts), {design: 1100}));
  hard.node.append(more('Eight real problems and what I did about each', stage(safe('The challenges', challengeGrid))));
  bands.hard = hard;

  // ---------- models ----------
  const accuracyRows = MODELS.map(name => ({name, accuracy: rate(m.evalRow('dev-A1', name), 'behaviour_accuracy'), cost: m.evalRow('dev-A1', name)?.metrics?.cost_per_case_usd, seconds: m.evalRow('dev-A1', name)?.metrics?.latency_p50_s, falseRate: rate(m.evalRow('dev-A1', name), 'false_answer_rate')}));
  const pick = accuracyRows[0], mini = accuracyRows[2];
  const models = band({
    id: 'models', title: 'Choosing the models',
    lede: [
      finite(pick.accuracy) && finite(mini.cost) ? `I ran three models on the same development questions with the same retrieval and prompt. ${pick.name} scored ${pct(pick.accuracy)} at ${usd(pick.cost)} a question. ${mini.name} was the fastest, at ${finite(mini.seconds) ? `${mini.seconds.toFixed(1)} s` : 'a short time'} median, but cost ${usd(mini.cost)} a question and gave the most false answers (${pct(mini.falseRate)} against ${pct(pick.falseRate)}). A model rerank adds a call, so the final setup is slower at the tail, and I accepted that for the accuracy.` : 'I ran three models on the same development questions with the same retrieval and prompt.',
      'I did not vary reasoning effort. Every call sent the model, the messages, a maximum length and a strict output schema, and no effort or temperature setting, so each model ran at the provider default, which the runs do not record. What I did vary was the model, the prompts, retrieval, the document build and the tool set.'
    ]
  });
  models.visual.append(stage(safe('The model table', () => modelTable(m))));
  models.visual.append(note('Prices are OpenAI list prices read on 30 October 2026, with no cached-input discount, so costs are upper bounds. The judge is an AI model from the same provider as the answer models, so its errors may correlate; numbers are scored by code.'));
  models.node.append(more('Cost, speed and spend', stage(safe('The cost bars', () => costBars(m))), group('', pool.fig('fig-models'), pool.fig('fig-latency'), pool.fig('fig-cost'), pool.fig('fig-ledger'))));
  bands.models = models;

  // ---------- retrieval ----------
  const retrieval = band({
    id: 'retrieval', title: 'Does filtering help?', layout: 'split',
    lede: [L ? `Hybrid search, keyword plus embeddings fused by rank, was the baseline. Hit@8 is the share of questions whose right passage is among the top eight. On ${m.ladder.n_cases} development questions it rose from ${pct(L.R0['hit@8'])} to ${pct(L.R3['hit@8'])} when I filtered by the named period and release and then reranked the top 30. Filtering alone reached ${pct(L.R1a['hit@8'])} and reranking alone ${pct(L.R2['hit@8'])}, so filtering did most of the work.` : 'The retrieval ladder is not available in the report data.',
      'The labels were AI drafts and the development set was inspected many times, so I read this as a design result, not a held-out one.']
  });
  retrieval.visual.append(stage(safe('The retrieval ladder', () => retrievalStaircase(m)), {design: 1100}));
  retrieval.node.append(more('Early comparisons, intervals and every retrieval table',
    group('Keyword, meaning or both', 'On 24 early development questions with one chunking, both together did best and became the baseline. At that size one case is about four points, so I used it to choose a baseline and not to prove one best.', stage(safe('The early comparison', () => keywordVsMeaning(m)))),
    pool.rest('retrieval')));
  bands.retrieval = retrieval;

  // ---------- agent ----------
  const agent = band({
    id: 'agent', title: 'What the agent experiments said',
    lede: ['One bounded LangGraph loop, five development changes, a registered held-out test, a corpus change, a second fresh test with its rule signed in advance, an error analysis and a fix that failed its own criteria. Each step changed one thing, and every result is kept.']
  });
  agent.visual.append(
    sub('One bounded loop', 'A planner, three typed read-only tools (search reports, get a series, calculate a change), an evidence check, an answer step and a validator. Limits are enforced in code: two evidence rounds, six tool calls, ten seconds a call, one retry and one repair. A tool outage ends as an operational failure, which is not the same as missing evidence.', stage(safe('The agent loop', agentLoop))),
    sub('One change at a time', finite(a1) && finite(a3) ? `A1 is the baseline. A2 changed the answer prompt, A3 added filter then rerank, A4 widened the candidate pool and A5 changed the planner prompt. Only A3 moved accuracy beyond the intervals, from ${pct(a1)} to ${pct(a3)} for the main model on ${nDev} questions. A2, A4 and A5 moved it inside the intervals and were not adopted. The runs have unequal sizes and no paired test, so read the ladder as descriptive.` : 'The experiment ladder is not available in the report data.', stage(safe('The experiment ladder', () => experimentStaircase(m))))
  );
  const x1 = dev('dev-X1'), x2 = dev('dev-X2');
  agent.visual.append(sub('Corpus changes: X1 and X2', 'X1 reran the system on cleaner extracted text. X2 reran the final system on the third corpus, with the runtime fixes and the source cross-check. Neither moved a headline metric beyond overlapping intervals. X2 changed several things at once, so it is a regression check and not an ablation.',
    rows([['X1, cleaner text', finite(rate(x1, 'behaviour_accuracy')) ? `${pct(rate(x1, 'behaviour_accuracy'))} for the main model, against ${pct(a3)} in A3.` : 'Not recorded.'], ['X2, final system check', finite(rate(x2, 'behaviour_accuracy')) ? `${pct(rate(x2, 'behaviour_accuracy'))} for the main model, with the cross-check on.` : 'Not recorded.']])));
  agent.visual.append(sub('Held-out tests', v2m && v2s ? `The registered held-out set has ${m.paired[0]?.n ?? 'a few'} questions and reuses development evidence, and five of its labels changed after the run, disclosed with the original scores kept. Its gain for filter then rerank had an interval that touched zero. So I built a second fresh set of ${v2m.n_gold_cases} questions on six sources no earlier case cites, with the decision rule signed before the run. The main model gained ${v2m.better} cases (${fmt.pts(v2m.paired_difference)}). The second model showed ${v2s.better > v2s.worse ? 'a smaller gain' : 'no net gain'} (${v2s.better} better, ${v2s.worse} worse). I report it as a small effect that did not replicate.` : 'The held-out results are not available in the report data.', stage(safe('The fresh-question results', () => freshQuestions(m))), {note: 'The label history for the registered set is in the evaluation report.'}));
  agent.visual.append(sub('Why it missed', ea ? `On the fresh set the primary filtered arm missed ${ea.n_mismatches_primary_r3} of ${ea.n_cases} questions, and ${ea.over_abstentions_primary_r3} of those were over-abstentions. Most were a missing calculation tool: it only worked on dataset observations and could not do arithmetic on a figure printed in report text. The error analysis found no case where the scorer penalised a correct answer or the label was wrong.` : 'The error analysis is not available in the report data.', stage(safe('The error classes', () => errorBars(m)))));
  agent.visual.append(sub('A fix that failed its own criteria', 'Tool set v2 lets the calculation tool do arithmetic on a figure quoted in report text. I declared its adoption criteria before any run. On the development questions it failed for both models: false-answer cases rose from 6 to 7 against a limit of 6, and ungrounded numbers appeared where the new tool was used. On the fresh set the main model went from 3 to 12 of 14 number comparisons, but I designed the fix after studying the errors on exactly those questions, so that gain is optimistic by construction. It was not adopted.', stage(safe('The fix results', toolFixBars)), {note: 'These counts come from the tool-fix criteria file and the X3 report in the repository, not from the report data.'}));
  const toolTables = group('Calculation fix in detail',
    dataTable('Development questions, tool set v2, one run per model', ['Criterion', 'Main model', 'Second model'], [
      ['Right kind of response at least 205 and 209 of 237', '212 pass', '213 pass'],
      ['False-answer cases at most 6', '7 fail', '7 fail'],
      ['No ungrounded number where the new tool was used', '1 of 10 fail', '3 of 18 fail'],
      ['Cases with an ungrounded number at most 34 and 51', '27 pass', '30 pass'],
      ['Operational failures at most 0', '0 pass', '1 fail (provider error)'],
      ['Overall', 'Fail', 'Fail']]),
    dataTable('Second fresh set, 65 questions (diagnostic only)', ['Measure', 'Main model', 'Second model'], [
      ['Right kind of response', '.754 to .908', '.723 to .846'],
      ['Better and worse cases', '10 and 0', '9 and 1'],
      ['Number comparisons right, of 14', '3 to 12', '3 to 10'],
      ['Over-abstentions', '13 to 3', '14 to 7']]),
    note('Counts are from the tool-fix criteria file and the X3 report in the repository.'));
  agent.node.append(more('Every figure and table from the evaluation and the agent', toolTables, pool.rest('evaluation'), pool.rest('agent')));
  bands.agent = agent;

  // ---------- tools and MCP ----------
  const tools = band({
    id: 'tools', title: 'Evidence, tools and MCP',
    lede: ['An answer is one of four things: a cited answer, an abstention, a question back or a refusal, in a schema that is validated in code. Numbers come from read-only tools and decimal arithmetic, not from the model, and a validator checks that every quote appears in the cited passage. It cannot tell whether the quote supports the claim, which is a stated gap. The MCP server exposes the same statistics read-only behind a client that treats it as untrusted. The live app calls the data directly, because MCP adds latency per call.']
  });
  tools.visual.append(
    sub('Every claim has a source', 'The values below are the latest resident unemployment figure in the report data. The change is computed in code, and a claim without a source is rejected.', stage(safe('The evidence trace', () => evidenceTrace(m)))),
    sub('The MCP server', finite(m.section('mcp').metrics?.compared_datasets) ? `Nine read-only tools, two resources and one prompt over the statistics and the source catalogue, with no report text. Across ${fmt.int(m.section('mcp').metrics.compared_datasets)} datasets, ${fmt.int(m.section('mcp').metrics.identical_datasets)} came back identical to direct calls and ${fmt.int(m.section('mcp').metrics.matching_refusals)} returned the same refusal, with ${fmt.int(m.section('mcp').metrics.different_outputs)} different.` : 'Nine read-only tools, two resources and one prompt over the statistics and the source catalogue.', stage(safe('The MCP diagram', mcpDiagram)))
  );
  tools.node.append(more('MCP checks, latency and the GenAI concepts used', group('GenAI concepts, and where this build uses each', stage(safe('The concepts', conceptGrid))), pool.rest('mcp')));
  bands.tools = tools;

  // ---------- safety ----------
  const safety = band({
    id: 'safety', title: 'Attacks and defences',
    lede: [`I wrote ${finite(nThreat) ? nThreat : 'a set of'} attack cases in six groups: direct injection, a poisoned passage, sensitive-data requests, unsafe tool use, unsupported claims and a failing MCP server. Retrieved text is marked as untrusted data, tools are read-only and typed, and steps, retries and time are capped. With few cases per run, small differences prove nothing: the suite shows no defence effect for the main model. The failures were mostly one planted false figure, and the injection scanner missed all five paraphrased probes.`]
  });
  safety.visual.append(
    stage(safe('The threat results', () => threatPanels(m))),
    sub('A planted wrong figure', 'A false figure sits in a report passage and passes the quote and number checks. The cross-check compares passage figures with the statistics. It handled the case for both models in the first run after the fix, but in the final-code run one model failed it, so I call it not shown stable.', stage(safe('The planted figure', plantedFlow)))
  );
  safety.node.append(more('Threat results, intervals and canaries', pool.rest('safety')));
  bands.safety = safety;

  // ---------- review ----------
  const review = band({
    id: 'review', title: 'Who checked the answers',
    lede: ['Gold labels were drafted by AI. I went through them in the review interface and recorded a decision on every case, answer verdict and source check (403 items). Most were quick confirmations, so read the labels as AI-drafted and owner-confirmed. One reviewer, after AI pre-review and after the runs were scored.',
      'That is one person confirming AI drafts, not independent annotation. Key numbers are scored by code, an AI judge scores only claim support, and the sets are small, so every rate carries a 95% interval.']
  });
  review.visual.append(
    stage(safe('The review streams', reviewStreams)),
    stage(safe('The measures', () => measureCards(m)))
  );
  review.node.append(more('Review counts and the evaluation notices', group('', pool.fig('fig-review'))));
  bands.review = review;

  // ---------- cost, observability, deployment ----------
  const ops = band({
    id: 'ops', title: 'Cost, observability and deployment', layout: 'split',
    lede: [`${costs.length ? `A question costs about ${usd(Math.min(...costs))} to ${usd(Math.max(...costs))} in the final setup, on list prices.` : 'Cost per question is measured on development questions.'} The app reserves $0.05 and saves it before any paid call, and refuses the question if it cannot save it. Every run leaves a record of outcome, tool calls, cost and timings, with identifiers hashed and secrets redacted. One small server in Singapore serves the live app behind access codes. A spend cap on the provider account is not set.`]
  });
  ops.visual.append(
    el('div', 'rp-shot reveal'),
    rows([['Cost', 'A daily budget, a reserved amount per question, and a kill switch that blocks new questions but not calls already running.'], ['Observability', 'A record per run, a prune command for old logs and no hidden model reasoning in the interface.'], ['Deployment', 'One server, one process, no high availability, and a rate limit on login, session and address.']])
  );
  ops.visual.firstChild.append(safe('The workbench screenshot', workbenchShot));
  ops.node.append(more('What is logged, what is not, and the recorded spend',
    group('Operations', rows([
      ['Logged', 'A record per run with outcome, tool calls, cost and timings. Identifiers are hashed and secrets redacted.'],
      ['Not logged', 'Raw addresses, session ids and hidden model reasoning. Full evidence text is omitted by default.'],
      ['Limits', 'Login, session and address rate limits, a body size limit, a concurrency limit, a daily budget and a kill switch.']])),
    note('The budget figures are from the deployment notes. The daily budget is an estimate and not a billing guarantee.')));
  bands.ops = ops;

  // ---------- process ----------
  const process = band({
    id: 'process', title: 'How I built it, and kept control',
    lede: ['I worked with a coding agent under a written contract. For every decision it set out two to four options, including a plain baseline, with one recommendation, and then stopped. I approved, it built, we verified and recorded. No new phase started without my approval, and every decision went into a log with its alternatives and how to reverse it. State lives in files, so any agent can pick the work up. Before the fresh-question run I signed the rule and pinned the hashes; results stay frozen, and later work gets new experiment ids. When the calculation fix failed its criteria, I reported that.',
      'I made the calls that mattered: the scope, the sources and what may be committed, signing the fresh-question set, the supported period as a hard scope, and not applying four label changes that two AI reviewers agreed with, because the cases needed figures from 2023.']
  });
  process.visual.append(
    stage(safe('The development loop', processLoop), {design: 1500, label: 'The development loop and its guardrails'}),
    statRow([
      {value: finite(nDecisions) ? String(nDecisions) : 'not recorded', label: 'decisions logged', note: 'each with options and how to reverse it'},
      {value: '5', label: 'end-to-end reviews', note: 'AI reviewers, not human review'},
      {value: '75', label: 'review findings', note: 'each checked against the code before a fix'},
      {value: '0', label: 'rights-scan hits', note: 'no tracked file repeats MOM text'}
    ]),
    note('Decision count from report.json. Review and scan counts are from the review summary and the repository audit.')
  );
  process.node.append(more('Where each practice is recorded', table('Practice, what the record shows, and where', ['Practice', 'What the record shows', 'Where'], [
    ['Written contract', 'A standing instruction that sets the order explore, compare, recommend, discuss, approve, implement, verify, document, with two to four options, a plain baseline and one recommendation at each decision.', 'CLAUDE.md'],
    ['Milestone gates', 'Ingestion was approved by name before any code, and each later phase needed approval. Domain, scope and a single bounded agent were fixed in two architecture decision records.', 'docs/decisions.md, docs/decisions/'],
    ['Decision log', `${finite(nDecisions) ? nDecisions : 'Many'} entries with date, alternatives, why, who approved and how reversible. An entry with no approver recorded is labelled an assistant decision within the protocol.`, 'docs/decisions.md'],
    ['State in files', 'Progress, decisions and handoff notes are updated at each step, so an interrupted agent can resume.', 'docs/progress.md, docs/agent-logs.md'],
    ['Independent reviews', 'Blind AI reviewers checked the gold labels, the saved answers and the extracted sources. Five AI reviewers then traced the whole flow end to end: 75 findings across data, runtime, evaluation, security and deployment, and deliverables. Each was checked before a fix; some were narrowed, deferred with a reason or left to me.', 'docs/human-review/e2e-review-summary.md'],
    ['Pre-registration and frozen results', 'The fresh-question rule, code and data hashes were signed before the run. Experiment runs refuse to overwrite without a flag, and scoring refuses a gold file whose hash differs from the one recorded with the run.', 'experiments/heldout-v2/FREEZE.md, docs/agent-logs.md'],
    ['New ids for later work', 'Changing labels or overwriting runs alongside a data fix was rejected because it confounds the result. Later work got new ids: X1, X2, X3 and a diagnostic set.', 'docs/decisions.md'],
    ['Negative results', 'Tool set v2 failed its criteria and was not adopted. X1 was not claimed as an improvement. The fresh-set gain is called a small effect that did not replicate.', 'docs/decisions.md'],
    ['Secrets', 'Keys live in a gitignored .env; the templates hold empty values. A scan of the full history found no secret, only dataset identifiers that look like keys. Runtime output passes a redaction step. One AI reviewer\u2019s search printed the local .env into its own session; nothing was committed, and the report advises rotating the key if that transcript is kept.', 'SECURITY.md, docs/process/repository-audit.md, docs/agent-logs.md'],
    ['Rights and private folders', 'A scan fails if a tracked file repeats more than six consecutive words of local MOM text. Private notes and study notes are gitignored and were never in the history.', 'SECURITY.md, docs/process/repository-audit.md'],
    ['Least privilege', 'The agent\u2019s tools are read-only and typed. A $0.05 reservation is saved before any paid call, a persistent ledger tracks the daily budget, and a run deadline caps each question.', 'docs/audit-and-logging.md, docs/deploy.md'],
    ['Writes', 'The source manifest and hashes are written by one code path. There is no lock against two writers, which a review flagged and I deferred.', 'docs/agent-logs.md, docs/human-review/e2e-review-summary.md']
  ])), more('Work log: milestones, experiment registry, decisions and problems', pool.rest('work')));
  bands.process = process;

  // ---------- limits ----------
  const limits = band({
    id: 'limits', title: 'Limits, and what next',
    lede: ['Limits first, then what I would do about them. The labels are AI-drafted and confirmed by one person. The fresh-set gain is three cases for one model. The attack scanner missed every paraphrased probe. If I had one more week, I would redo a sample of the label review with a second reviewer, then retest the calculation fix on questions I have not seen.']
  });
  limits.visual.append(stage(safe('The limits', () => cardRow([{icon: 'warning', head: 'AI-drafted labels', line: 'One person confirmed them.'}, {icon: 'warning', head: 'Small fresh-set gain', line: 'Three cases, one model.'}, {icon: 'warning', head: 'Weak attack scanner', line: 'It missed all five paraphrased probes.'}, {icon: 'arrow-right', head: 'Redo the review', line: 'A sample, with a second reviewer.'}, {icon: 'arrow-right', head: 'Retest the fix', line: 'On questions I have not seen.'}, {icon: 'arrow-right', head: 'Cap the spend', line: 'A limit on the provider account.'}]))));
  limits.node.append(more('Every recorded limit, and the six next experiments', pool.rest('limits'), pool.rest('next'), pool.rest('summary')));
  bands.limits = limits;

  // ---------- coverage ----------
  const coverage = band({
    id: 'coverage', title: 'What I covered',
    lede: ['The bar lengths are the assessment weights. The last column is the first open item recorded for each area in my requirements matrix, not a full list. Open work is shown, not hidden.']
  });
  coverage.visual.append(stage(safe('The coverage map', coverageMap)));
  bands.coverage = coverage;

  // ---------- run it ----------
  const run = band({
    id: 'run', title: 'Run it, and read more',
    lede: ['Dependencies are pinned. The report server starts without a key or the private corpus, and the offline tests and the rights scan need no paid call. Live answers need an access code and make paid model calls.']
  });
  run.visual.append(
    commands(['uv sync', 'LABOURLENS_DEMO_ENABLED=false uv run labourlens serve', 'uv run pytest -q -m "not corpus"', 'uv run labourlens rights-scan', 'uv run labourlens build-report']),
    note('The same checks run as make setup, make verify and make serve.')
  );
  const links = el('ul', 'rp-links reveal');
  [['The presentation', 'The same story as slides, with speaker notes.', '/deck', false], ['The workbench', 'Ask a question and inspect the evidence, citations and activity trace.', '/workbench', false]].forEach(([label, text, href]) => {
    const li = el('li'); li.append(link(label, href), el('span', '', text)); links.append(li);
  });
  run.visual.append(links);
  const docs = el('ul', 'rp-doclist');
  [['README', 'README.md'], ['Architecture', 'docs/architecture.md'], ['Evaluation report', 'docs/evaluation-report.md'], ['System card', 'docs/system-card.md'], ['Data sheet', 'docs/data-sheet.md'], ['Threat model', 'docs/threat-model.md'], ['Innovation assessment', 'docs/innovation.md'], ['Demo script', 'docs/demo-script.md'], ['Requirements matrix', 'docs/requirements-matrix.md'], ['Decision log', 'docs/decisions.md'], ['How the agents were used', 'docs/agent-logs.md'], ['Reproduce each artefact', 'docs/reproduce.md']].forEach(([label, path]) => {
    const li = el('li'); li.append(link(label, `${REPO}${path}`, {external: true})); docs.append(li);
  });
  run.visual.append(group('In the repository', note('The repository is private and shared with reviewers.'), docs));
  bands.run = run;

  return STEPS.map(([id]) => bands[id]).filter(Boolean).map((b, i) => { b.node.classList.toggle('is-tint', i % 2 === 1); return b; });
}
