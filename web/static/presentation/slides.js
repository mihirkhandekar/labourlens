// The deck: every slide is declared here as data. Charts and tables are the ones the chapter
// modules already draw from report.json; this file picks them out of an off-screen pool, gives each
// slide an action title and at most three bullets, and moves the detail into speaker notes or the
// appendix. Numbers on slides come from report.json (through the model) or from the document named
// in the slide's source line. Text is set with textContent only.
import {el, fmt, finite} from '../charts.js';
import {model, metricOf, goldOf} from './model.js';
import {stat, textStat, countRunner, dataTable} from './ui.js';
import {answerCard, threeAnswers, twoSources, buildTimeline, flattening, mcpDiagram, retrievalStaircase, experimentStaircase, agentLoop, evidenceTrace, errorBars, toolFixBars, requirementGrid, domainChoice, challengeGrid, plantedFlow, aboutMe, architectureDiagram, taskAndLeftOut, hardParts, keywordVsMeaning, modelTable, reviewStreams, threatPanels, workbenchShot, conceptGrid, coverageMap, measureCards, freshQuestions, cardRow} from './graphics.js';
import {renderScope} from './ch1-scope.js';
import {renderData} from './ch2-data.js';
import {renderRetrieval} from './ch3-retrieval.js';
import {renderAgent} from './ch4-agent.js';
import {renderEvaluation} from './ch5-evaluation.js';
import {renderSafety} from './ch6-safety.js';
import {renderMcp} from './ch7-mcp.js';
import {renderLimits, renderNext, renderSummary} from './ch8-limits.js';
import {renderWork} from './ch-work.js';
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
  run('evaluation', renderEvaluation); run('safety', renderSafety); run('mcp', renderMcp); run('limits', renderLimits);
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
  const ea = v2?.error_analysis;
  const work = m.section('work');
  c.work._blocks = [...(c.work?.querySelectorAll('.pr-block') || [])];
  const card0 = m.cards.find(x => x.card_id === 'unemployment_resident_sa') || m.cards[0];

  // ---------- opening ----------
  add({
    layout: 'title', chapter: 'Start', title: 'Singapore labour statistics, answered with a source you can check.',
    wordmark: 'LabourLens', author: 'Mihir Khandekar', role: 'GenAI Engineer assessment', card: answerCard(m), source: '',
    notes: ['The story: what problem I picked, what I built, which data and why, what the data showed, how I measured, what the experiments said, what it costs, how it holds up under attack, how I worked with AI agents, what went wrong, and what is next.', 'One-sentence version: a research assistant that answers labour-market questions from MOM data with a checkable source for every number, and declines when the data does not support an answer.', 'The card on the right is a real answer from the latest figure in the report data, with the citation the product would show.', 'Keys: arrows, space and page keys move; F is fullscreen; O or Escape opens the overview; S shows these notes; add ?print-pdf to the address to export a PDF.']
  });
  add({
    layout: 'solo', chapter: 'Introduction', title: 'About me', visual: aboutMe(), source: 'GenAI Engineer assessment',
    notes: ['I am Mihir Khandekar. My recent work is on AI products in the HR Tech space. That is the one background detail on this slide; say the rest in your own words.', 'The talk follows the system in the order the data moves through it: where the data comes from, how I processed it, retrieval, the agent and its tools, the answer, and then the checks around all of it: evaluation, attacks and review. The strip at the top of later slides shows where each one sits on that path.', qa('Why is so much of the talk about evaluation?', 'The assessment gives evaluation and error analysis the largest weight, 25%, so most of the talk is how I measured and what failed.')]
  });

  // ---------- the assignment ----------
  add({
    layout: 'solo', chapter: 'The problem', title: 'The assignment', visual: requirementGrid(false), caption: 'Plus written deliverables, an innovation note and a live demo.',
    source: 'GenAI Engineer technical challenge',
    notes: ['What was asked, from Tech Challenge - GenAI Engineer v1.0.pdf. The problem statement: build an evidence-grounded policy research assistant that answers analytical questions from government statistics and reports, produces traceable evidence and communicates uncertainty. It prioritises applied machine learning, experimentation, retrieval quality, evaluation and responsible AI over full-stack engineering.', 'Ten core requirements, shown on the grid: problem framing and experimental design; data preparation and exploratory analysis; retrieval-augmented generation; model experimentation; one bounded agent workflow; evaluation and error analysis; responsible AI, security and privacy; GenAI concepts; MCP and tool integration; reproducibility. Ten minimum demonstration scenarios, from a cited factual answer to ignoring an instruction embedded in MCP output.', 'Submission: source, prompts, configuration template, README, architecture diagram, data sheet, evaluation report, system card, a separate one-to-two-page innovation assessment, and a live demonstration with a walkthrough, an evaluation deep dive, a failure demonstration and a design discussion.', 'Rubric weights: framing and data 10%, RAG and GenAI design 20%, evaluation and error analysis 25%, agent workflow 10%, concepts and MCP 15%, responsible AI 10%, reproducibility and communication 10%. Not optimised for: a sophisticated frontend, many agents or providers, or novel training.', 'The closing requirement-coverage slide maps each of these ten to where the talk showed it and what is still open.', qa('Which part carries most weight?', 'Evaluation and error analysis, 25%. That is why most of the talk is about how I measured and what failed.')]
  });
  add({
    layout: 'solo', chapter: 'Why this problem', title: 'Why this problem', visual: domainChoice(), caption: 'Official data with real revisions. A Singapore role. My recent work is AI in HR Tech.',
    source: 'LabourLens scope record',
    notes: ['Recorded reasons (ADR-001, 30 Oct 2026, owner approved): three domains were compared. Labour market: official structured quarterly indicators and narrative reports, true publication revisions, useful calculations; risks are definition and seasonality differences and release-version mismatches. Housing affordability: accessible data and clear charts, but confounding variables and heterogeneous transaction-level data. Cost of living or inflation: time series and policy relevance, but index methodology, weights and causality complexity. The ADR also records that the project needs a small, coherent real-world corpus for a defensible 20-minute demonstration.', 'Scope that followed: users are policy researchers and labour-market analysts; supported answer period 2024 Q1 to 2026 Q2 (10 quarters); four MOM statistics series and five MOM report documents, later widened by owner-approved decisions (D-003 added structured datasets that create ambiguity and cross-check cases, D-006 added methodology and earlier-release documents). Out of scope: forecasting, unsupported causal claims, personal employment advice, unrestricted web research. D-001 keeps the repository private because MOM report PDFs are all rights reserved; D-002 keeps study notes out of the published documents.', qa('Why Singapore?', 'It is a Singapore role, so a Singapore problem is the natural fit. MOM publishes open quarterly data and reports with real advance-versus-final revisions.'), qa('Why not a topic with more data?', 'More data was not the constraint. I needed official data with definitions, revisions and reports that disagree in checkable ways, because the assignment grades abstention, conflict handling and calculation.')]
  });
  add({
    layout: 'solo', chapter: 'Why this problem', title: 'The task, and what I left out', visual: taskAndLeftOut(), caption: 'A small, checkable scope beat a broad one.',
    source: 'LabourLens scope record',
    notes: ['Users: Singapore policy researchers and labour-market analysts (ADR-001). Question families: factual lookup, numerical change between periods, cross-source synthesis, advance-versus-final revisions, ambiguity and insufficient evidence including causal overreach, and adversarial content. Supported answer period: 2024 Q1 to 2026 Q2, ten quarters, a hard scope (D-031): earlier documents stay as context, but a request for earlier figures must decline.', 'How I chose the data. ADR-001 approved four MOM series (resident unemployment rate, vacancy-to-unemployed ratio, retrenched employees, employment change by sector) and four report documents plus the Q2 2026 advance release. D-003 added datasets where the record says they create a distinct test: overall and citizen rates for population ambiguity, the vacancy rate and counts for rate versus ratio, retrenchment splits for a parts-versus-total check, re-employment for a freshness and revision case. D-006 added the methodology and earlier-release documents, because they answer what an indicator means. D-040 added six sources no earlier case cites, so a second fresh test set could be independent.', 'What I rejected, with the recorded reason. Housing affordability (confounding variables, transaction-level data) and cost of living (index methodology, weights, causality) were the alternative domains in ADR-001. Foreign workforce datasets: last updated June 2024. Wages, annual retrenchment incidence and short work-week data: lower fit with the quarterly scope, and the short work-week set may lack 2026 Q2. MTI GDP revision pairs: not labour evidence, rejected by the owner. MTI and MAS pages: no verified PDF links on the MTI page and a maintenance page at MAS. A dataset also had to reach 2026 Q2 and pass its contract at ingestion or it was dropped.', 'Out of scope by decision: forecasts, unsupported causal claims, personal employment advice, unrestricted web research.', qa('Why bound the period so tightly?', 'A bounded period makes out-of-scope questions testable. The system must decline a 2023 figure even when a context document mentions it, and the evaluation scores that.')]
  });
  add({
    layout: 'solo', chapter: 'The system', title: 'The system, end to end', stage: 'all', visual: architectureDiagram(), caption: 'Each later slide shows where it sits on this path.',
    source: 'LabourLens architecture',
    notes: ['Data moves left to right. Sources: the statistics series from data.gov.sg as CSV snapshots, and MOM reports as PDF and web pages. Processing: parse, clean, split into passages with metadata (publisher, release stage, period), and validate observations and passages. Retrieval: keyword and embedding search fused together, a hard filter on period and release, then a model rerank. Agent: one bounded LangGraph loop that plans, calls three read-only tools and does arithmetic in code. Answer: structured, schema-validated output in which every claim carries a quote from a cited passage, or the system asks a question back, declines or refuses.', 'Two things run across all of it. Guardrails: retrieved text is treated as untrusted data, tools are read-only, and steps, retries and time are capped. Evaluation: reference questions with expected evidence, fresh question sets, intervals, a human review and a handwritten attack suite.', 'ADR-002 fixed one bounded agent, not a multi-agent design. The full diagram is in docs/architecture.md.', qa('Why one agent?', 'Every extra agent is another place for a failure that I would have to trace and measure. One bounded graph with typed tools was enough for the questions in scope.')]
  });

  // ---------- problem ----------

  // ---------- scope and plan ----------

  // ---------- data ----------
  add({
    id: 'data', layout: 'solo', chapter: 'The data', title: 'Choosing the data', visual: twoSources(m), caption: 'Statistics give the numbers. Reports give the explanations.',
    source: 'Ministry of Manpower and SingStat via data.gov.sg',
    notes: ['ADR-001 approved four datasets: resident unemployment rate, vacancy-to-unemployed ratio, retrenched employees and employment change by sector. D-003 (30 Oct 2026) added others where the record says they create a distinct test: overall and citizen rates for population ambiguity, the vacancy rate and counts for rate versus ratio, retrenchment splits for a parts-versus-total check, re-entry for a freshness and revision case. D-006: the reports add the methodology and definitions that answer what an indicator means.', 'Left out (D-003, D-006, D-040): foreign workforce datasets, last updated June 2024; wages, annual retrenchment incidence and short work-week (tier 2, may lack 2026 Q2); MTI GDP revision pairs, rejected by the owner as not labour evidence; MTI and MAS pages without verified links.', 'Rights: 33 of the 85 source records are open licence and may be committed; MOM report PDFs carry a copyright notice and stay local. Only dataset snapshots are redistributed.', qa('Why these datasets?', 'The approved four came with the scope decision. The additions were chosen where the record names the test they enable.')]
  });
  add({
    layout: 'solo', chapter: 'The data', title: 'Three document builds', visual: buildTimeline(), caption: 'Each build fixed a problem the earlier one had.',
    source: 'LabourLens README, corpus versions',
    notes: ['Passage counts: 13,484, 15,915 and 16,419, from the README and the decision log; they are not in the report data. The first build is the one the registered results ran on. The second adds the extraction fixes after an audit (D-037, D-041). The third adds six sources that no earlier case cites, so a second fresh test set could be independent (D-040).', 'The served application runs the third build at commit c297146, as reported by the owner, with /healthz fingerprint d402120f6f8f and 1,847 chunks.', qa('Why does the build matter for results?', 'A result is only valid for the build it ran on. Registered results ran on the first build; the third has a development check and a threat run, and one independent fresh set.')]
  });

  add({
    layout: 'solo', chapter: 'What the data showed', title: 'Reading the reports', visual: flattening(), caption: 'Tables came out flattened. Numbers were intact.',
    source: 'AI review of 16 sampled passages (12 PDF, 4 web)',
    notes: ['In a 16-passage AI pre-review of the extracted text against the original pages (12 PDF passages, 4 web pages), all 4 sampled tables came out flattened: two adjacent rows merged into one passage with column context lost. Some passages lost a note boundary, and web passages flattened superscripts. No numerical transcription error turned up.', 'Extraction fixes produced the second document build; the measured effect on retrieval and answers was none (the cleaner-text run). There is no corpus-wide defect count. Source: docs/human-review/ai-pre-review-passage-spot-check.md.', qa('If extraction was flawed, why trust the results?', 'The sampled defects did not change numbers, and the run on cleaner text moved no headline metric. The missing corpus-wide count is a stated limit.')]
  });
  // ---------- EDA ----------
  add({...figSlide('fig-unemployment', {title: 'What the data showed'}), title: 'What the data showed', id: 'eda', chapter: 'What the data showed', layout: 'split', human: 'MOM unemployment rates via data.gov.sg',
    bullets: ['Unemployment has several official rates.', 'Every answer must name which one.'],
    notes: ['First required EDA finding: a plain unemployment rate question is ambiguous across population (overall, resident, citizen) and seasonal adjustment. Decision: series identifiers carry population and adjustment, and the agent asks a clarifying question when the series is open.', findings[0] ? `${findings[0].head}. ${findings[0].body}` : '', qa('What did EDA change in the design?', 'Typed series identifiers, a clarifying question when the series is open, and a scorer that counts a missing clarification as a behaviour error.')]});
  add({...figSlide('fig-retrenchments', {title: 'Retrenchments'}), title: 'Retrenchments rose, with no stated cause', chapter: 'What the data showed', layout: 'split', human: 'MOM retrenched employees via data.gov.sg',
    bullets: ['The data shows movement, not reasons.', 'Why-questions get report text or no answer.'],
    notes: [findings[1] ? `${findings[1].head}. ${findings[1].body}` : '', 'Second required EDA finding. Retrenchments and resident unemployment moved differently in the same period, which shows how easily a causal story gets attached. The agent may cite report commentary that states a reason, labelled as MOM commentary. It never infers a cause from two series.', qa('How does the agent handle a why question?', 'It cites report commentary that states a reason, labelled as such, or abstains.')]});
  add({...figSlide('fig-revisions', {title: 'Advance and final figures'}), title: 'Advance and final figures differ', chapter: 'What the data showed', layout: 'split', human: 'MOM advance and final reports, and the SingStat sector dataset',
    bullets: ['Every answer names its release.'],
    notes: [findings[2] ? `${findings[2].head}. ${findings[2].body}` : '', findings[3] ? `${findings[3].head}. ${findings[3].body}` : '', 'The vacancy ratio shows a similar caution: recomputing it from counts differs from the published ratio by up to 0.67 because the two come from different surveys, so I quote the published ratio (appendix B).', qa('Which figure is right, advance or final?', 'Both, for their release. The answer must name which one it uses, and the conflict cases in the gold set test exactly this.')]});
  add({
    layout: 'solo', chapter: 'What the data showed', title: 'Hard parts, and what handles them', stage: 1, visual: hardParts(), caption: 'Each finding about the data became a design decision.',
    source: 'LabourLens data findings and design notes',
    notes: ['Each row is a difficulty the data showed me and the part of the system that now handles it. Four unemployment rates: series identifiers carry population and adjustment, and the agent asks which one is meant when the question leaves it open. A rise with no stated cause: the agent may cite MOM commentary that states a reason, labelled as commentary, and otherwise declines to explain. Advance and final differ: retrieval filters on release stage and the answer names its release; conflicting releases are explained, not averaged. Tables flattened: every claim must carry a quote that appears in the cited passage, so a mangled passage cannot silently supply a number. Ratio does not recompute: recomputing the vacancy ratio from counts differs from the published ratio by up to 0.67 because the two come from different surveys, so the system quotes the published ratio. Figures before 2024: a scope guard declines.', qa('Which of these did you only realise from the data?', 'The ratio mismatch and the table flattening. The unemployment ambiguity and the revisions I expected; the numbers showed how large they were.')]
  });
  add({
    layout: 'solo', chapter: 'Retrieval', title: 'Keyword, meaning or both?', stage: 2, visual: keywordVsMeaning(m) || missing('The retriever comparison'), caption: 'Both together did best on 24 questions. It became the baseline.',
    source: 'LabourLens retrieval tests on 24 development questions',
    notes: ['Early comparison on 24 development questions with one chunking (merge120): hit@10, the share of questions whose right passage is among the top ten. BM25 keyword search 0.583, dense embeddings 0.667, hybrid with reciprocal rank fusion 0.708. With the larger merge200 chunking the same three scored 0.625, 0.667 and 0.792. At 24 questions one case is about 4 points, so these are noisy and I used them to choose a baseline, not to prove one best.', 'Chunking: block chunks scored 0.417 at hit@10, fixed 150-word windows 0.625, merge200 0.625; I used merge200. Embeddings: text-embedding-3-large is the model in use (chosen on development and not frozen); in the same noisy 24-question test the smaller model and the older ada model scored 0.75 and 0.875 at hit@10, so the embedding choice is not settled by this evidence. BM25 settings (stemming, stop words, k1 and b) moved hit@10 by at most 0.12.', 'Source: experiments/runs, dev-E1 to dev-E7 retrieval runs; appendix C.', qa('Why hybrid if dense alone scored close?', 'Keyword search catches exact terms such as series and release names, and dense search catches paraphrases. Hybrid was the best or tied on both chunkings, and the later period filter mattered far more than the choice among these.')]
  });

  // ---------- reading ----------

  // ---------- retrieval ----------
  add({
    id: 'retrieval', layout: 'solo', chapter: 'What I built', title: 'Does filtering help?', visual: retrievalStaircase(m) || missing('The retrieval ladder'), caption: 'Filtering by period helped most. Reranking added a little.',
    source: 'LabourLens retrieval tests on 128 development questions',
    notes: ['The ladder: R0 the hybrid baseline (BM25 plus dense, rank fusion), R1a a hard filter on period and release, R1b a soft boost, R2 an LLM rerank of the top 30, R3 the filter then the rerank. The bars show hit@8 with 95% bootstrap intervals on 128 development questions; R3 is the agent default. Hit@8 is the share of questions whose right passage is among the top eight.', 'The pre-registered H1 (the named period and release) is supported. Limits: the labels were AI drafts first (reviewed afterwards by one person) and an LLM both drafted them and reranks; the development set was inspected many times; a hard period filter can exclude the right document when a later release restates an earlier quarter, which is documented and not fixed; there is no retrieval-only held-out measurement. Embedding comparisons are in appendix C.', qa('Why a hard filter before reranking?', 'It removes the wrong-vintage passages a reranker would otherwise have to ignore, and it was the largest single gain.')]
  });

  // ---------- agent ----------
  add({
    id: 'agent', layout: 'solo', chapter: 'What I built', title: 'The agent loop', visual: agentLoop(), caption: 'At most two search rounds and one repair.',
    source: 'LabourLens agent design',
    notes: ['One bounded LangGraph state graph: a planner, three typed read-only tools (search reports, get a series, calculate a change), evidence assessment, answer generation and validation. ADR-002 fixed one bounded agent; I did not build a multi-agent design. Limits are enforced in code: 2 evidence rounds, 6 tool calls, 10 seconds per call, 1 retry, 1 repair, 1,000 characters per question. A tool outage ends as operational_failure, separate from missing evidence. Tool arguments are enums built from the source catalogue. The recorded-run stepper is in appendix D.', qa('Why one agent?', 'Every extra agent is another place for a failure that I would have to trace and measure. One bounded graph with typed tools was enough for the questions in scope.')]
  });
  add({
    layout: 'solo', chapter: 'What I built', title: 'Every claim has a source', visual: evidenceTrace(m) || missing('The trace'), caption: 'Code does the sums. A claim without a source is rejected.',
    source: 'MOM resident unemployment rate via data.gov.sg',
    notes: ['Structured output is schema-validated. The answer is one of an answer, an abstention, a question back or a refusal, and retrieved text that contains instructions is treated as data, not followed. A validator confirms the quote appears in the cited passage and the label matches the evidence. It cannot show the quote supports the claim, which is a stated gap.', 'Changes are computed in decimal arithmetic from validated observations; the model does not do the arithmetic. Calculation correctness was 75.0% on 24 calculation cases in the main development run, so one case is about 4 points.', 'The values in the trace are the latest resident figure in the report data.', qa('How do you know a citation is real?', 'The validator checks the quote against the cited passage and the label against the evidence. It cannot judge whether the quote supports the claim.')]
  });
  // ---------- measuring ----------
  add({
    layout: 'solo', chapter: 'Models', title: 'Choosing the models', stage: 3, visual: modelTable(m), caption: 'I varied model, prompt, retrieval and tools. Reasoning effort stayed at its default.',
    source: 'OpenAI list prices read on 30 October 2026; LabourLens baseline runs',
    notes: ['Prices per 1M tokens (specs/prices.yaml, read 2026-10-30, no cached-input discounts, so costs are upper bounds): gpt-6-luna $0.10 in and $0.50 out; gpt-5.6-luna $0.20 and $1.20; gpt-4.1-mini $0.40 and $1.60; judge gpt-6.1-terra $1.00 and $5.00; text-embedding-3-large $0.13 per 1M input. gpt-6-astra ($10 in, $50 out) was excluded by the owner as too expensive and never run.', 'Baseline development run, 235 questions, same retrieval and prompt for each model: right kind of response 0.779 (gpt-6-luna), 0.800 (gpt-5.6-luna), 0.757 (gpt-4.1-mini); cost per question $0.0014, $0.0027, $0.0047; median seconds 10.7, 9.6, 5.8. gpt-4.1-mini is the fastest but cost the most per question and had the highest false-answer rate (0.079 against 0.025 and 0.030). In the final filter-then-rerank setup the cost per question was $0.0021 for gpt-6-luna and $0.0036 for gpt-5.6-luna; the second fresh set cost $0.0033 per question for the main model. Reranking adds a model call, so it raised the 95th-percentile latency to about 37 s; I accepted that for the accuracy gain.', 'Effort levels. I did not vary reasoning effort. Every chat call sends the model, the messages, a maximum completion length (6,000 tokens for answers, 1,500 for the planner) and a strict JSON schema, and no reasoning-effort or temperature setting (src/labourlens/answer/llm.py; no caller passes extra parameters), so the provider default applied to every model, and that default is not recorded in the runs. What I did vary: the model (three), prompt versions (answer and planner prompts), retrieval (baseline, filter, rerank, both), the corpus build (three) and the tool set (base and v2). Say this plainly if asked about effort.', 'The judge is an AI model from the same provider as the answer models, so errors may correlate; numbers are scored by code.', qa('Why gpt-6-luna?', 'It matched the dearer luna model after the retrieval change (0.903 for both on 237 questions) at about 60 percent of the cost per question, and the smaller mini model was faster but cost more per question and gave more false answers.')]
  });
  add({
    layout: 'solo', chapter: 'How I measured', title: 'How I measured', stage: 5, visual: measureCards(m), caption: 'Small sets, so every rate carries a 95% interval.',
    source: 'LabourLens reference questions and review records',
    notes: ['Reference set: 268 cases, 237 development and 31 held out, drafted by an AI under a label policy I decided and confirmed by me afterwards. Development cases choose the configuration, so those numbers carry selection bias. The 31-case held-out set is one run on a frozen configuration but reuses development evidence in 25 of 31 cases, and five held-out cases had post-run label edits (HO-004, HO-022, HO-023, HO-027, HO-029), disclosed with the original scores kept. The second fresh set has 65 cases on six sources no earlier case cites, with the decision rule signed before the run.', 'Measures: hit@8 (right passage among the top eight); behaviour accuracy (right kind of response: answer, abstain, clarify, refuse); false-answer rate and over-abstention; claim support from an AI judge from the same provider as the answer models, so errors may correlate; key-number recall and calculation correctness scored by code. Intervals are 95% case-bootstrap intervals because the sets are small. A blind AI sample of 40 outputs was chosen to be rich in failures, so it is not an accuracy estimate.', 'Review: labels were drafted by AI. I went through them in the review interface and recorded a decision on every case, answer verdict and source check (403 items). Most were quick confirmations of the suggested label, so read the labels as AI-drafted and owner-confirmed. One reviewer, after AI pre-review and after the runs were scored. Detail on the next slide.', qa('Can you trust an AI judge?', 'Only for claim support, and I report its limit. Key numbers are scored by code, not by the judge.'), qa('What is the baseline?', 'BM25 keyword search with extractive passages, no model in the loop, and then the hybrid retriever as the baseline for every later comparison.')]
  });
  add({
    layout: 'solo', chapter: 'How I measured', title: 'Who checked the answers', stage: 5, visual: reviewStreams(), caption: 'AI drafted the labels. One person confirmed them. Not independent.',
    source: 'LabourLens review records',
    notes: ['Labels were drafted by AI. I went through them in the review interface and recorded a decision on every case, answer verdict and source check (403 items): 268 reference cases, 65 second-fresh-set cases, 40 saved answers and 30 source checks (final export of source checks: 18 match, 12 minor difference). Most were quick confirmations of the suggested label, so read the labels as AI-drafted and owner-confirmed. One reviewer, after AI pre-review and after the runs were scored. The review page stamps every decision as an owner decision whatever the input, so the stamp records a decision, not how long I spent on a card. Source: docs/human-review/numbers-audit.md section 3.', 'Agreement with the AI suggestion where one existed: 198 of 198 gold cases, 61 of 64 fresh-set cases, 38 of 39 answers, 29 of 30 source checks. That is agreement, not accuracy. Four change-clicks (DEV-034, DEV-202, DEV-626, DEV-627) were not applied under the out-of-period policy (D-047), so gold labels are unchanged in v3.7 (v3.6 plus review provenance). J10, acceptance of the disclosed extraction gaps, was recorded as accept-limits.', 'The strongest human evidence is the first pack of answer verdicts, the method decisions, the change-clicks, J10 and my written policy decisions. A defensible human-review claim needs a smaller sample re-done with a second reviewer. That is the first item in what I would do next.', qa('Is the gold set independent?', 'No. An AI drafted it, AI reviewers checked it, and one person confirmed it. I treat it as AI-drafted with owner confirmation.')]
  });
  add({
    layout: 'solo', chapter: 'What the experiments said', title: 'The experiment ladder', visual: experimentStaircase(m) || missing('The experiments'), caption: 'Only the retrieval change moved accuracy beyond the intervals.',
    source: 'LabourLens development runs, 237 questions',
    notes: ['Behaviour accuracy for the main model on 237 development questions. The ladder: baseline hybrid retrieval, a better answer prompt (A2), filter then rerank (A3, adopted provisionally), a wider candidate pool (A4) and a new planner prompt (A5). One factor changed per run; the three hatched steps moved accuracy inside the intervals and were not adopted. Outcomes are in the experiment registry (appendix J). The A runs have unequal sizes (235 against 237 questions) and no paired test, and the development set guided the choices, so read the ladder as descriptive.', 'Corpus changes: the cleaner-text run (X1) and the final system check (X2, corpus v3, 14 runtime changes, cross-check, new gold version) moved no headline metric. X2 changed several things at once so it is a regression check, not an ablation. Ungrounded-number cases rose for the second model, with the claim-support point estimate lower but not a demonstrated fall (the intervals overlap), and the check was widened at the same time, so measurement changed too. Source: docs/experiments/m7-e2e-fixes.md.', 'The registered 31-case held-out comparison gave a gain for the retrieval change with an interval that touched zero; it reuses development evidence and was rescored after post-run label edits (appendix E).', qa('Why did prompt changes not help?', 'The differences were inside the intervals. I kept the simpler prompt and logged the null results as decisions.')]
  });
  if (v2p) {
    add({
      layout: 'solo', chapter: 'What the experiments said', title: 'On fresh questions, the gain was small', visual: freshQuestions(m) || missing('The fresh-question results'), caption: 'Filtering helped the main model by three cases on 65 fresh questions. It did not help the second model.',
      source: 'LabourLens test sets and second fresh test set',
      notes: [v2.verdict, `Held-out v2: 65 cases on six sources no earlier case cites (D-040), scored once per arm and model. The decision rule, interval level (90%), 20,000 resamples and seed ${v2p.seed} were written into FREEZE.md and signed (owner export a428db90, 31 Oct 2026) before the run at code commit 89c51d7; results were committed afterwards in 6f80ec9. Main model: ${fmt.pct(v2p.behaviour_accuracy.candidate)} with filtering against ${fmt.pct(v2p.behaviour_accuracy.baseline)} without, ${fmt.pts(v2p.paired_difference)}, ${v2p.better} better and ${v2p.worse} worse, interval ${fmt.pts(v2p.case_bootstrap_interval[0])} to ${fmt.pts(v2p.case_bootstrap_interval[1])}, McNemar exact p ${v2p.mcnemar_exact_p}. Second model: ${v2q ? `${fmt.pct(v2q.behaviour_accuracy.candidate)} in both arms, ${v2q.better} better and ${v2q.worse} worse` : 'no difference'}.`, 'Limits recorded with the result: one run per arm, sampled models, two of the three cases were first-step planner decisions in the hybrid arm, and without the five MTI cases the lower bound is not above zero.', qa('Did you demonstrate that filtering helps?', 'The pre-registered rule was met for one model by three cases, and not for the second. I report it as a small effect that did not replicate.')]
    });
  }
  add({
    layout: 'solo', chapter: 'What the experiments said', title: 'Why it missed', visual: errorBars(m) || missing('The error classes'), caption: 'Most misses were a missing calculation tool.',
    source: 'LabourLens second fresh test set',
    notes: [ea ? `Primary filtered arm: ${ea.n_mismatches_primary_r3} of ${ea.n_cases} cases missed; ${ea.over_abstentions_primary_r3} were over-abstentions, ${ea.numerical_over_abstentions_primary_r3} of them numerical comparison questions. The error analysis found no case where the scorer penalised a correct answer or the gold label was wrong. Source: experiments/heldout-v2/error-analysis.json.` : '', 'Accuracy is lower than in development mainly because of a tool gap: the calculation tool only worked on dataset observations and could not do arithmetic on a figure in report text. The fix I tested is the following slide.', qa('Why not fix the tool and rerun straight away?', 'The second fresh-set result is frozen as run. A fix is a new experiment with its own stated rule.')]
  });
  add({
    layout: 'solo', chapter: 'What the experiments said', title: 'Fixing the calculation gap', visual: toolFixBars(), caption: 'Practice questions: no gain. Fresh questions: a gain, but optimistic. Not adopted.',
    source: 'LabourLens calculation-fix tests',
    notes: ['Tool set v2 lets the calculation tool do arithmetic on a figure quoted in report text, gives an actionable error when a dimension label is wrong, and adds one bonus search round. Its adoption criteria were declared before any run (D-046, section 4.1). Result (D-048, 1 Nov 2026, experiments/eval/agent-dev-X3-REPORT.md and experiments/tool-fix/criteria.json): on the 237 development questions it FAILED for both models. Behaviour accuracy .903 to .895 (main model) and .916 to .899 (second model), both inside the earlier intervals. False-answer cases 6 before, 7 after for both models, against a limit of 6. Ungrounded numbers appeared in 1 of 10 (main model) and 3 of 18 (second model) cases that used the new tool, against a limit of none. The second model also had one provider outage (HTTP 520), against a limit of none.', 'On the 65-case second fresh set (V2post) the main model went from 3 to 12 of 14 numerical comparisons, accuracy .754 to .908 (10 better, 0 worse) and over-abstentions 13 to 3; the second model went 3 to 10 of 14, .723 to .846. But I designed the tool set after analysing the errors on exactly those 65 cases, so every gain there is optimistic by construction and the set is a diagnostic, not a held-out test. The development set has few cases that need arithmetic on report text, so it cannot show the benefit either.', 'Decision: not adopted. The default tool set stays the base one; the code and prompts stay as an unadopted option. Adoption would need a fresh development pass and a threat run under v2, which has not been run. All figures on this slide are literals from those two documents; they are not in the report data. Cost of the retained runs about $3.45 plus about $1.5 for a first attempt that crashed in scoring and was discarded.', qa('Why not call the fresh-set gain a success?', 'The rule was written before the run and the development set failed it. The fresh set was used to design the fix, so it cannot also confirm it.')]
  });
  add({
    layout: 'solo', chapter: 'Concepts', title: 'GenAI concepts in this build', visual: conceptGrid(), caption: 'Each concept is used in the build, not only described.',
    source: 'LabourLens design and evaluation',
    notes: ['Tokens and context: questions are capped at 1,000 characters, the model is asked for at most 6,000 output tokens (1,500 for the planner), and evidence reaches the model as a bounded set of numbered passages, so the context never holds a whole report. Embeddings: text-embedding-3-large beside BM25 keyword search, fused by reciprocal rank; metadata filters on period and release do the heavy lifting. Reranking: a model reorders the top 30 candidate passages; on its own it gained less than the filter (hit@8 0.789 against 0.844), and together they reached 0.969. Prompts: versioned prompt files (planner and answer, plus a repair and a rerank prompt), trusted instructions kept apart from untrusted retrieved text, strict JSON output validated in code. Evaluators: code scores numbers and quotes, an AI judge from the answer models provider scores claim support (so its errors may correlate), and I reviewed labels. Agents: one bounded workflow with a model planner, at most two evidence rounds, six tool calls, ten seconds per call, one retry and one repair. MCP: nine read-only tools and two resources, covered on the next slide. Observability: a record per run with outcome, tool calls, cost and timings, identifiers hashed and secrets redacted.', 'Operational trade-offs I measured: cost per question about $0.002 to $0.005, median latency 14 to 16 s and 95th percentile 34 to 41 s for the full agent, a daily budget with a reserved per-question amount, and direct calls over MCP because they are about five times faster per call.', qa('Where does context engineering show up?', 'In keeping evidence short and numbered, filtering by period and release before ranking, and keeping retrieved instructions out of the instruction channel.')]
  });
  add({
    layout: 'solo', chapter: 'Concepts', title: 'The MCP server', stage: 3, visual: mcpDiagram(), caption: 'Read-only tools. The live app calls the data directly, not through MCP.',
    source: 'LabourLens MCP server and client design',
    notes: [`The server exposes nine read-only tools, two resources and one prompt over the statistics and the source catalogue, with no MOM report text. The client treats the server as untrusted: allow-listed launch, schema checks on arguments and results, deadlines and size limits; six scripted failure behaviours were observed against a hostile test server. Across ${fmt.int(mx.compared_datasets)} datasets, ${fmt.int(mx.identical_datasets)} came back identical to direct calls and ${fmt.int(mx.matching_refusals)} returned the same refusal, with ${fmt.int(mx.different_outputs)} different. Connecting once costs ${fmt.num(mx.connection_seconds, 2)} s; the median per call was 22.7 ms over MCP against 4.4 ms direct.`, 'The honest position: the web app and the agent in production do not route through MCP. Direct calls are the default and MCP is an optional route (D-028); an MCP-backed agent answer is recorded separately in the demo script. MCP earns its place when several hosts or teams need the same capability with a discoverable schema; for one app it is overhead. Roles: the host is the application, the client sits inside it, the server owns the tools; tools are model-invoked, resources are application-read data, prompts are user-invoked templates. The transport here is local and private and does not establish government-grade authentication.', qa('Then why build it?', 'The assessment asks for a working server, a client demonstration, trust boundaries and a comparison. I measured what MCP costs and kept direct calls as the default.')]
  });
  add({
    layout: 'solo', chapter: 'Safety', title: 'Attacks and defences', stage: 5, visual: threatPanels(m) || missing('The threat results'), caption: 'Few cases per run, so small differences prove nothing.',
    source: 'LabourLens threat tests, 36 attack cases',
    notes: ['36 handwritten attack cases in six categories: direct injection, poisoned passage, sensitive data, unsafe tool use, unsupported claims and a failing MCP server. Registered run on corpus v1: gpt-6-luna 35 of 36 with defences and 35 of 36 without; gpt-4.1-mini 34 with and 32 without. Final system on corpus v3 with the cross-check: gpt-6-luna 36 of 36 with defences and 35 without; gpt-5.6-luna 35 of 36 both ways. One run per configuration, so a pass rate is not a guarantee, and the intervals overlap: the suite does not show a defence effect for the main model, and the smaller-model difference is consistent with a benefit but not demonstrated.', 'Controls: retrieved text is marked as untrusted data in the model context, tools are read-only and enum-typed, steps, retries and time are capped, secrets stay server-side and are redacted in logs, and citations are validated before display. Gaps: the ingestion scanner is heuristic and all five paraphrased malicious probes bypassed it in a blind AI review; quote presence does not show a quote supports the claim; the MCP input filter missed one paraphrased instruction in the saved transcript.', qa('Did the defences work?', 'The suite does not show a defence effect for the main model; the failures were mostly the planted false figure. The scanner is the biggest known gap.')]
  });

  {
    take(c.safety, '.pr-ti06-steps');
    add({
      layout: 'solo', chapter: 'What I built', title: 'A planted wrong figure', visual: plantedFlow(), caption: 'The cross-check now catches it, but one model failed it once.', source: 'LabourLens threat tests',
      notes: [text(c.safety, '.pr-hero-callout-text'), 'T-I06 plants a false figure in a report passage. Before the fix, all five configurations cited it, and the quote and number checks passed. The cross-check compares passage figures with validated observations (closed grammar), corrects the claim to the dataset value, cites both and adds a source-conflict caveat. In the first run after the fix it handled the case in both models; in the final-code run gpt-5.6-luna failed it on an exact-string scorer check although its answer reported the dataset value and disclosed the planted figure in a caveat. I did not change the scorer after seeing the run. Decision D-038; files docs/experiments/m7-t-i06-crosscheck.md and experiments/threats/m7-e2efix-20261031/SUMMARY.md.', qa('Is this fixed?', 'One planted case with a closed-grammar cross-check passed in one run and not in the next for one model. The mechanism works sometimes. It does not show it generalises.')]
    });
  }
  // ---------- cost ----------
  add({
    layout: 'split', chapter: 'Product', title: 'The product, and how to run it', stage: 4,
    bullets: ['Pinned dependencies, and tests that need no corpus.', 'A $0.05 budget is reserved before any paid call.', 'README, data sheet, evaluation report, system card.'],
    visual: workbenchShot(), source: 'LabourLens workbench, shown without live answers',
    notes: ['Setup: uv sync installs pinned dependencies; the report-only server starts with LABOURLENS_DEMO_ENABLED=false uv run labourlens serve; tests that need no corpus run with uv run pytest -q -m "not corpus" (782 passed on 1 Nov 2026); uv run labourlens rights-scan fails if any tracked file quotes more than six consecutive words of a local MOM passage; uv run labourlens build-report rebuilds the report data from committed artifacts. README, data sheet, evaluation report, system card, architecture diagram, demo script and innovation assessment are in the repository; owner review and a fresh-checkout run are still pending.', 'The screenshot is the real workbench running in report-only mode, so it shows the question box, example questions, session history and activity timeline but no live answer. In live mode each answer has a status badge (answered, abstained, needs clarification, refused), citation chips that turn red when a label has no matching evidence, and an evidence drawer with the exact excerpt and source link. Live answers need an access code and make paid model calls.', 'Cost controls: $0.05 is reserved and persisted before any paid call starts and the question is refused if it cannot be saved; the daily budget is an estimate, default $2.00, and zero blocks new questions; a kill switch blocks new questions but not calls already running; a provider-side OpenAI spend cap is not set and not verified. Observability: a record per run with outcome, tool calls, cost and timings; identifiers hashed, secrets redacted, no hidden model reasoning, and a prune command for old logs. Rate limits cover login, session and address.', 'Close with the product: open the workbench and ask a question live.', qa('What would you add before real traffic?', 'A provider-side hard spend cap first, then per-user quotas, a backup procedure and a measured memory profile under load, none of which I have verified.')]
  });

  // ---------- process ----------
  add({
    id: 'process', layout: 'solo', chapter: 'How I worked', title: 'How I worked with AI agents', caption: 'Approval before every phase. Reviews caught real errors.',
    visual: cardRow([{icon: 'key', head: 'I decided', line: 'Scope, sources, label policy and the test rules.'}, {icon: 'wrench', head: 'Agents drafted', line: 'Code, first-pass labels and design options.'}, {icon: 'check-circle', head: 'Reviews caught', line: 'A stale judge cache, among other errors.'}]), source: 'LabourLens project instructions',
    notes: ['Operating model from the project instructions: explore, compare, recommend, discuss, approve, implement, verify, document. Agents proposed options with trade-offs and I chose. Independent blind AI reviews checked the gold labels, the answers and the extracted passages. Held-out runs were frozen and gold versions are hashed into every score. Tool arguments and answer output are strictly typed so a malformed result is rejected, not displayed.', 'I decided scope, sources, label policy, what counts as adopted and the held-out rule. Agents proposed designs, wrote code and drafted gold cases; I then recorded a decision on all 403 labelling items, mostly as quick confirmations of AI suggestions.', qa('What would an AI-only process have missed?', 'The judge cache keyed by case id survived gold changes. A human gate and an independent review found it.')]
  });

  // ---------- limits and next ----------
  add({
    id: 'limits', layout: 'solo', chapter: 'Next', title: 'Limits, and what next', caption: 'Limits first, then what I would do about them.',
    visual: cardRow([{icon: 'warning', head: 'AI-drafted labels', line: 'One person confirmed them.'}, {icon: 'warning', head: 'Small fresh-set gain', line: 'Three cases, one model.'}, {icon: 'warning', head: 'Weak attack scanner', line: 'It missed all five paraphrased probes.'}, {icon: 'arrow-right', head: 'Redo the review', line: 'A sample, with a second reviewer.'}, {icon: 'arrow-right', head: 'Retest the fix', line: 'On questions I have not seen.'}, {icon: 'arrow-right', head: 'Cap the spend', line: 'A limit on the provider account.'}]), source: 'LabourLens evaluation report',
    notes: [`Limits in full are in appendix H (${[...(c.limits?.querySelectorAll('.pr-limit') || [])].length} recorded). Labels: an AI drafted them and I recorded decisions on all 403 labelling items, one reviewer, mostly quick confirmations of AI suggestions, so not independent. Held-out sets: the 31-case set reuses development evidence; the second set shows three cases for one model. Safety: the planted figure passed once and failed once for one model; the scanner missed all 5 paraphrased probes. Corpus: registered results ran on the first build, not the third that the demo serves. Cost: list-price estimates, and the AI judge shares a provider with the answer models. Calculation fix: failed its pre-declared criteria on development and is not adopted.`, 'Next steps in full are in appendix I: redo a sample of the review with a minimum dwell time, a clean development pass and a threat run under the calculation fix before any adoption, test the cross-check beyond one planted case, count extraction defects corpus-wide, replace the scanner, and soften the period filter.', qa('If you had one more week?', 'Redo a sample of the label review properly, with a second reviewer, then redesign the calculation fix against a fresh set I had not looked at.')]
  });
  add({
    layout: 'solo', chapter: 'Close', title: 'What I covered', visual: coverageMap(), caption: 'Weights are the assessment. Open work is shown, not hidden.',
    source: 'Statistics: MOM and SingStat via data.gov.sg, under the Singapore Open Data Licence. MOM reports remain the Ministry\u2019s.',
    notes: ['Rubric weights from the assessment: evaluation and error analysis 25%, RAG and GenAI design 20%, GenAI concepts and MCP 15%, problem framing and data science 10%, agent workflow 10%, responsible AI 10%, reproducibility and communication 10%. The open item on each row is the first recorded remaining-work item from docs/requirements-matrix.md, not a full list. Every one of the ten core rows is marked partial there: implementation and evidence exist, acceptance work remains. Submission items (README, architecture diagram, data sheet, evaluation report, system card, innovation assessment, demo plan) exist; owner review, rehearsal, a fresh-checkout run and remote deployment checks are pending.', 'Summary in three lines. It answers with a checkable source or declines. Filtering by period and release moved retrieval most (hit@8 0.570 to 0.969 on 128 development questions), while the gain on fresh questions was small. The labels are AI-drafted with one reviewer, which is the main thing I would fix first.', 'Sources and licences. Statistics: MOM and SingStat via data.gov.sg, Singapore Open Data Licence. MOM reports remain the Ministry copyright and no quote in the deck is longer than six words. Model prices were read on 30 October 2026. Fonts: Geist, SIL OFL 1.1. Slides: reveal.js 6.0.2, MIT. Icons: Phosphor, MIT. Report built from committed artifacts with uv run labourlens build-report.', qa('What would you do first with another week?', 'Redo a sample of the review with a minimum dwell time and a second reviewer, then retest the calculation fix against a fresh set I have not looked at.')]
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
        group(heading('Gold labels and review'), list(['Labels were drafted by AI. I went through them in the review interface and recorded a decision on every case, answer verdict and source check (403 items). Most were quick confirmations of the suggested label, so read the labels as AI-drafted and owner-confirmed. One reviewer, after AI pre-review and after the runs were scored. Four change-clicks were not applied under the out-of-period policy, so labels are unchanged in v3.7.', `Development rows use ${goldOf(a3).label}; held-out rows use ${goldOf(r3).label}. Both were rescored from saved outputs after post-run label edits.`, 'Registered results ran on corpus v1 and the X1 runs on corpus v2. Corpus v3 (85 sources) has three measured evaluations: the X2 development regression check, the e2efix threat run and held-out v2 (65 questions, evidence-disjoint at source level only), plus the tool set v2 runs (X3 and V2post, not adopted).'])),
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
    add({
      chapter: 'Appendix', layout: 'scroll', title: 'E. Evaluation reference',
      panel: [group(heading('Response time and cost'), items[0], items[1]), group(heading('Model comparison and oracle evidence'), items[2], items[3]), group(heading('Error counts'), items[4]), group(heading('Experiment progression and registered held-out'), items[7], items[8]), group(heading('Review counts'), items[9]), group(heading('Development against held-out, and by family'), items[5], items[6]), ...takeAll(c.evaluation, '.pr-details').map(d => group(d))],
      source: 'report.json: evaluation.rows, answers.rows, evaluation.errors',
      notes: ['Latency and cost, the model comparison on answer-only cases with oracle evidence, and the pooled error counts. The X2 regression table is on slide A.']
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
      notes: ['The tool catalogue, the scripted failure behaviours against a hostile test server, the loopback HTTP hardening attempts and the limits.']
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
      notes: ['Milestones, the experiment registry, the searchable decision log, the six problems in full, the review process and the recorded spend.']
    });
  });

  appendix('K', 'Planning, data choices and operations', () => {
    add({
      chapter: 'Appendix', layout: 'scroll', title: 'K. Planning, data choices and operations',
      panel: [
        group(heading('Hypotheses as written'), rows([
          ['Retrieval, before any R1 or R2 number', 'H1: the named quarter and release raise hit@8. H2: an LLM rerank of the top 30 fixes ordering among near-duplicates. H3: the combination gains at least the larger single change. Null: nothing separates from the baseline beyond noise.'],
          ['Agent end to end, not a timestamped pre-registration', 'H1: filter plus rerank reduces missing-evidence abstentions. H2: explicit missing-data instructions help. H3: widening a weak pool helps. H4: a pricier generator is worth the price. H5: the planner should research the legitimate part of a rules-override question.'],
          ['BM25 held-out run, before the run', 'Three configurations named in advance and all reported whatever the outcome.']])),
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

  appendixIndex.push(['M', 'Slides cut from the talk']);
  add({
    layout: 'split', chapter: 'Appendix', title: 'M. Cut from the talk: why not a chatbot or search?',
    bullets: ['A chatbot recalls figures without sources.', 'Search finds text but never does the sums.', 'Neither knows when to say no.'],
    visual: bigStat({text: 'Three gaps', label: 'that the design has to close', size: 'xl'}), source: 'LabourLens design notes',
    notes: ['This is the reasoning behind the architecture, not a measured comparison. The retrieval ladder and the evaluation later put numbers on the parts that can be measured.', 'The brief asks for two source types, retrieval, a bounded agent, an MCP server and an evaluation. My reading is that it tests judgement as much as code, and the project instructions rank retrieval quality, evaluation, security and reproducibility above interface polish.', qa('Why not a long context window with the reports?', 'It would still not choose a series or release, would not compute changes exactly, and gives no stable citation. I wanted each of those to be a checkable step.')]
  });
  add({
    id: 'framing', layout: 'split', chapter: 'Appendix', title: 'M. Cut from the talk: what it covers',
    bullets: ['Four MOM series, quarterly.', 'Five MOM reports for context.', 'Outside 2024 to 2026, it declines. No forecasts, causes or personal advice.'],
    visual: bigStat({value: nQ, label: `quarters, ${fmt.quarter(m.scope[0])} to ${fmt.quarter(to)}`, size: 'xl'}), source: 'Ministry of Manpower via data.gov.sg',
    notes: ['The scope is recorded in docs/decisions/ADR-001 and docs/archive/planning/01_REQUIREMENTS_AND_SCOPE.md. Out of scope: forecasting, unsupported causal claims (the requirements name the case of AI causing a retrenchment trend), personal employment advice and unrestricted web research with restricted source hosts.', 'D-003 set a per-dataset drop rule: a dataset must reach 2026 Q2 and pass its contract at ingestion.', qa('Is refusing a feature or a limitation?', 'A designed behaviour. Refusal and abstention are scored in the gold set, and over-abstention is measured separately so refusing cannot hide weak retrieval.')]
  });
  add({
    layout: 'split', chapter: 'Appendix', title: 'M. Cut from the talk: how I planned to test it',
    bullets: ['A keyword-search baseline, no AI.', 'Reference questions with expected sources.', 'Predictions written down before each run.'],
    visual: bigStat({text: 'Baseline first', label: 'one change at a time', size: 'xl'}), source: 'Project requirements and experiment notes',
    notes: ['Requirements (docs/archive/planning/01_REQUIREMENTS_AND_SCOPE.md): at least 30 evaluation cases and a separate development set; gold ids labelled after ingestion; an explicit non-LLM baseline (BM25 with extractive passages); controlled configurations with model, prompt and corpus fixed; retrieval, correctness, groundedness, citation, abstention, calculation and security metrics with latency and cost; a human-review sample actually reviewed by a human; every negative result kept. docs/05_EVIDENCE_AND_STUDY_PLAN.md adds that hypotheses must be marked as such.', 'Hypotheses as written. Retrieval (docs/experiments/m6-retrieval-improvements.md, written before any R1 or R2 number): H1 using the named quarter and release raises hit@8; H2 an LLM rerank of the top 30 fixes ordering among near-duplicates; H3 the combination gains at least the larger single change; null: nothing separates from the baseline beyond noise. Agent (docs/experiments/m6-agent-end-to-end.md, not a timestamped pre-registration): H1 filter plus rerank reduces missing-evidence abstentions; H2 explicit missing-data instructions help; H3 widening a weak pool helps; H4 a pricier generator is worth the price; H5 the planner should research the legitimate part of a rules-override question. BM25 held-out (docs/experiments/m2-bm25-baseline.md): three configurations named before the held-out run.', qa('What would have falsified the retrieval hypotheses?', 'The null: no configuration separating from the hybrid baseline beyond noise. The note says a negative result would be reported as such.')]
  });
  add({
    id: 'product', layout: 'split', chapter: 'Appendix', title: 'M. Cut from the talk: running it live',
    bullets: ['Every answer links to its source passage.', 'A budget is reserved before any paid call.', 'No spend cap is set on the provider account yet.'],
    visual: bigStat({text: '$0.05', label: 'reserved per question, under a $2 daily budget', size: 'xl'}), source: 'LabourLens deployment notes',
    notes: ['Workbench: status badges (answered, abstained, needs clarification, refused), citation chips that turn red when a label has no matching evidence, and an evidence drawer with the exact excerpt and source link. One server in Singapore serves the live app behind access codes, on the third build at commit c297146, as reported by the owner.', 'Budget: $0.05 is reserved and persisted before any paid call starts, and the question is refused if it cannot be saved; the daily budget is an estimate, default $2.00, and zero blocks new questions; a kill switch blocks new questions but not calls already running. A provider-side OpenAI spend cap is not set and not verified. Source: docs/deploy.md.', 'Logging: a record per run with outcome, tool calls, cost and timings; identifiers hashed, secrets redacted, no hidden model reasoning, and a prune command for old logs. Source: docs/audit-and-logging.md.', qa('What would you add before real traffic?', 'A provider-side hard spend cap first, then per-user quotas, a backup procedure and a measured memory profile under load, none of which I have verified.')]
  });
  add({
    id: 'wrong', layout: 'solo', chapter: 'Appendix', title: 'M. Cut from the talk: what went wrong',
    visual: rows([['Stale judge cache', 'Key caches by what can change.'], ['Scorer too strict', 'Test the scorer first.'], ['A test that never ran', 'A pass needs proof it ran.'], ['Labels edited late', 'Freeze first, disclose edits.'], ['Flattened tables', 'Audit data before measuring.'], ['One lucky pass', 'One run is not stability.']]),
    source: 'LabourLens experiment log',
    notes: ['Each item has a cause, a fix and a status in the work log (appendix J): a judge cache keyed by case id that survived gold changes; a calculation scorer that over-constrained prose and units; a threat fixture that passed vacuously under the filtered retrieval; five held-out gold edits after the held-out run, disclosed with the original scores kept; extraction defects; and the planted figure that passed once and failed once.', qa('Which mistake are you least comfortable with?', 'The post-run gold edits. I disclosed them and kept the original scores beside the rescored ones, which is why I relied on the second fresh set.')]
  });
  add({
    layout: 'solo', chapter: 'Appendix', title: 'M. Cut from the talk: challenges', visual: challengeGrid(), caption: 'Real problems from the record, and what I did about each.',
    source: 'LabourLens project record',
    notes: ['Tables flattened: in a 16-passage AI pre-review all 4 sampled tables came out flattened and no number was wrong; the extraction fixes made the second document build and moved no headline metric (D-037, D-041). Series ambiguity: unemployment is published overall, resident and citizen, adjusted and not; series ids carry both and the agent asks when the series is open. Advance versus final: the same quarter has different figures by release; answers must name the release. Rights: MOM report PDFs are all rights reserved, so they stay out of the public repository (D-001) and rights stay unresolved per source until its notice is read. Small AI-drafted gold set: 268 reference cases drafted by an AI; I then recorded a decision on every item, mostly quick confirmations, one reviewer; intervals everywhere because the sets are small. Leakage: the 31-case held-out set reuses development evidence in 25 of 31 cases, so I built a second fresh set on six sources no earlier case cites (D-040). Calculation gap: the tool could not do arithmetic on figures in report text; the fix I tested failed its pre-declared rule (D-048). Scope boundary: questions needing figures before 2024 must decline even when the corpus holds context documents (D-031).', 'Process mistakes that also taught rules (work log, appendix J): a judge cache keyed by case id that survived gold changes; a calculation scorer that over-constrained prose; a threat test that passed vacuously; five held-out gold edits after the held-out run, disclosed with the original scores kept; one planted-figure pass that did not repeat.', qa('Which challenge is least solved?', 'The reference set. One reviewer confirming AI drafts is still not independent annotation, and I say so.')]
  });
  add({
    layout: 'solo', chapter: 'Appendix', title: 'M. Cut from the talk: why one number is not enough', visual: threeAnswers(m), caption: 'Same quarter, same question. Three correct numbers.',
    source: 'MOM unemployment rates via data.gov.sg',
    notes: ['These are three real series in the data, each correct for a different question. A reader handed one of them without its label cannot tell which question was answered. A fourth, citizen unemployment, is also published.', 'Values are the last observation of each series in the report data.', qa('Is that a real failure of language models?', 'I did not measure a plain model on this question. It is the design problem: the system must name the series or ask which one is meant, and the evaluation later measures how often it does.')]
  });
  // Appendix index lists the lettered slides.
  const idx = el('ul', 'deck-index');
  appendixIndex.forEach(([letter, title]) => idx.append(el('li', '', `${letter}. ${title}`)));
  indexSpec.visual = idx;
  indexSpec.indexItems = appendixIndex;

  // The slide face shows a plain-language source; report fields and file paths go to the speaker notes.
  specs.forEach(spec => {
    const stages = {'Choosing the data': 0, 'Three document builds': 0, 'Reading the reports': 1, 'Why one number is not enough': 1, 'What the data showed': 1, 'Retrenchments rose, with no stated cause': 1, 'Advance and final figures differ': 1,
      'Does filtering help?': 2, 'The agent loop': 3, 'Every claim has a source': 4, 'The experiment ladder': 5, 'On fresh questions, the gain was small': 5, 'Why it missed': 5, 'Fixing the calculation gap': 3, 'A planted wrong figure': 5, 'The product, and how to run it': 4};
    if (spec.chapter !== 'Appendix' && spec.stage == null && stages[spec.title] != null) spec.stage = stages[spec.title];
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
