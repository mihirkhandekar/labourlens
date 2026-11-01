// The deck: every slide is declared here as data. Charts and tables are the ones the chapter
// modules already draw from report.json; this file picks them out of an off-screen pool, gives each
// slide an action title and at most three bullets, and moves the detail into speaker notes or the
// appendix. Numbers on slides come from report.json (through the model) or from the document named
// in the slide's source line. Text is set with textContent only.
import {el, fmt, finite} from '../charts.js';
import {model, metricOf, goldOf} from './model.js';
import {stat, textStat, countRunner, dataTable} from './ui.js';
import {answerCard, threeAnswers, twoSources, buildTimeline, flattening, mcpDiagram, retrievalStaircase, experimentStaircase, agentLoop, evidenceTrace, costBars, costCaption, errorBars} from './graphics.js';
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

  // ---------- problem ----------
  add({
    id: 'problem', layout: 'split', chapter: 'The problem', title: 'The problem',
    bullets: ['Analysts need one figure they can check.', 'The right period, series and release matter.', 'A wrong or unsourced number is worse than none.'],
    visual: bigStat({text: 'One number', label: 'with its period, series and source', size: 'xl'}), source: 'MOM and SingStat via data.gov.sg',
    notes: ['The users are Singapore policy researchers and labour-market analysts, as recorded in the approved scope (ADR-001, CLAUDE.md). The needs on this slide are my framing of what they require.', qa('Why not build for the general public?', 'The approved scope names policy researchers and analysts. A narrower user makes the reference cases easier to define and check.')]
  });
  add({
    layout: 'solo', chapter: 'The problem', title: 'Why one number is not enough', visual: threeAnswers(m), caption: 'Same quarter, same question. Three correct numbers.',
    source: 'MOM unemployment rates via data.gov.sg',
    notes: ['These are three real series in the data, each correct for a different question. A reader handed one of them without its label cannot tell which question was answered. A fourth, citizen unemployment, is also published.', 'Values are the last observation of each series in the report data.', qa('Is that a real failure of language models?', 'I did not measure a plain model on this question. It is the design problem: the system must name the series or ask which one is meant, and the evaluation later measures how often it does.')]
  });
  add({
    layout: 'split', chapter: 'The problem', title: 'Why not a chatbot or search?',
    bullets: ['A chatbot recalls figures without sources.', 'Search finds text but never does the sums.', 'Neither knows when to say no.'],
    visual: bigStat({text: 'Three gaps', label: 'that the design has to close', size: 'xl'}), source: 'LabourLens design notes',
    notes: ['This is the reasoning behind the architecture, not a measured comparison. The retrieval ladder and the evaluation later put numbers on the parts that can be measured.', 'The brief asks for two source types, retrieval, a bounded agent, an MCP server and an evaluation. My reading is that it tests judgement as much as code, and the project instructions rank retrieval quality, evaluation, security and reproducibility above interface polish.', qa('Why not a long context window with the reports?', 'It would still not choose a series or release, would not compute changes exactly, and gives no stable citation. I wanted each of those to be a checkable step.')]
  });

  // ---------- scope and plan ----------
  add({
    id: 'framing', layout: 'split', chapter: 'What I built', title: 'What it covers',
    bullets: ['Four MOM series, quarterly.', 'Five MOM reports for context.', 'Outside 2024 to 2026, it declines. No forecasts, causes or personal advice.'],
    visual: bigStat({value: nQ, label: `quarters, ${fmt.quarter(m.scope[0])} to ${fmt.quarter(to)}`, size: 'xl'}), source: 'Ministry of Manpower via data.gov.sg',
    notes: ['The scope is recorded in docs/decisions/ADR-001 and docs/01_REQUIREMENTS_AND_SCOPE.md. Out of scope: forecasting, unsupported causal claims (the requirements name the case of AI causing a retrenchment trend), personal employment advice and unrestricted web research with restricted source hosts.', 'D-003 set a per-dataset drop rule: a dataset must reach 2026 Q2 and pass its contract at ingestion.', qa('Is refusing a feature or a limitation?', 'A designed behaviour. Refusal and abstention are scored in the gold set, and over-abstention is measured separately so refusing cannot hide weak retrieval.')]
  });
  add({
    layout: 'split', chapter: 'What I built', title: 'How I planned to test it',
    bullets: ['A keyword-search baseline, no AI.', 'Reference questions with expected sources.', 'Predictions written down before each run.'],
    visual: bigStat({text: 'Baseline first', label: 'one change at a time', size: 'xl'}), source: 'Project requirements and experiment notes',
    notes: ['Requirements (docs/01_REQUIREMENTS_AND_SCOPE.md): at least 30 evaluation cases and a separate development set; gold ids labelled after ingestion; an explicit non-LLM baseline (BM25 with extractive passages); controlled configurations with model, prompt and corpus fixed; retrieval, correctness, groundedness, citation, abstention, calculation and security metrics with latency and cost; a human-review sample actually reviewed by a human; every negative result kept. docs/05_EVIDENCE_AND_STUDY_PLAN.md adds that hypotheses must be marked as such.', 'Hypotheses as written. Retrieval (docs/experiments/m6-retrieval-improvements.md, written before any R1 or R2 number): H1 using the named quarter and release raises hit@8; H2 an LLM rerank of the top 30 fixes ordering among near-duplicates; H3 the combination gains at least the larger single change; null: nothing separates from the baseline beyond noise. Agent (docs/experiments/m6-agent-end-to-end.md, not a timestamped pre-registration): H1 filter plus rerank reduces missing-evidence abstentions; H2 explicit missing-data instructions help; H3 widening a weak pool helps; H4 a pricier generator is worth the price; H5 the planner should research the legitimate part of a rules-override question. BM25 held-out (docs/experiments/m2-bm25-baseline.md): three configurations named before the held-out run.', qa('What would have falsified the retrieval hypotheses?', 'The null: no configuration separating from the hybrid baseline beyond noise. The note says a negative result would be reported as such.')]
  });

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

  // ---------- reading ----------
  add({
    layout: 'solo', chapter: 'What the data showed', title: 'Reading the reports', visual: flattening(), caption: 'Tables came out flattened. Numbers were intact.',
    source: 'Independent review of 16 sampled passages',
    notes: ['In a 16-passage audit against the original PDFs, all 4 sampled tables came out flattened: two adjacent rows merged into one passage with column context lost. Some passages lost a note boundary, and HTML passages flattened superscripts. No numerical transcription error turned up.', 'Extraction fixes produced the second document build; the measured effect on retrieval and answers was none (the cleaner-text run). There is no corpus-wide defect count. Source: docs/human-review/ai-pre-review-passage-spot-check.md.', qa('If extraction was flawed, why trust the results?', 'The sampled defects did not change numbers, and the run on cleaner text moved no headline metric. The missing corpus-wide count is a stated limit.')]
  });

  // ---------- retrieval ----------
  add({
    id: 'retrieval', layout: 'solo', chapter: 'What I built', title: 'Does filtering help?', visual: retrievalStaircase(m) || missing('The retrieval ladder'), caption: 'Filtering by period helped most. Reranking added a little.',
    source: 'LabourLens retrieval tests on 128 development questions',
    notes: ['The ladder: R0 the hybrid baseline (BM25 plus dense, rank fusion), R1a a hard filter on period and release, R1b a soft boost, R2 an LLM rerank of the top 30, R3 the filter then the rerank. The bars show hit@8 with 95% bootstrap intervals on 128 development questions; R3 is the agent default. Hit@8 is the share of questions whose right passage is among the top eight.', 'The pre-registered H1 (the named period and release) is supported. Limits: most labels are AI drafts and an LLM both drafted them and reranks; the development set was inspected many times; a hard period filter can exclude the right document when a later release restates an earlier quarter, which is documented and not fixed; there is no retrieval-only held-out measurement. Embedding comparisons are in appendix C.', qa('Why a hard filter before reranking?', 'It removes the wrong-vintage passages a reranker would otherwise have to ignore, and it was the largest single gain.')]
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
  {
    const steps = take(c.safety, '.pr-ti06-steps');
    add({
      layout: 'split', chapter: 'What I built', title: 'A planted wrong figure',
      bullets: ['A fake number in a report passage was cited.', 'A cross-check against the data now catches it.', 'One model still failed it once.'],
      visual: steps || missing('The sequence'), cls: 'is-steps', source: 'LabourLens threat tests',
      notes: [text(c.safety, '.pr-hero-callout-text'), 'T-I06 plants a false figure in a report passage. Before the fix, all five configurations cited it, and the quote and number checks passed. The cross-check compares passage figures with validated observations. In the first run after the fix it handled the case in both models; in the final-code run gpt-5.6-luna failed it on an exact-string scorer check although its answer reported the dataset value and disclosed the planted figure in a caveat. I did not change the scorer after seeing the run. Decision D-038; files docs/experiments/m7-t-i06-crosscheck.md and experiments/threats/m7-e2efix-20261031/SUMMARY.md.', qa('Is this fixed?', 'One planted case with a closed-grammar cross-check passed in one run and not in the next for one model. The mechanism works sometimes. It does not show it generalises.')]
    });
  }

  // ---------- measuring ----------
  add({
    id: 'measure', layout: 'split', chapter: 'How I measured', title: 'How I measured',
    bullets: ['Practice questions for tuning, fresh ones for scoring.', 'Right passage in the top 8, right kind of response.', 'I reviewed 45 of 268 reference answers.'],
    visual: bigStat({value: 45, label: 'of 268 reference answers reviewed by me', size: 'xl'}), source: 'LabourLens reference questions and review records',
    notes: ['Gold set: 268 cases, 237 development and 31 held out. An AI drafted the labels under a label policy I decided. Of 125 review cards, 30 are my own verdicts and 95 agreed with an AI suggestion, so this is not independent annotation; 43 reviewed cases stayed and 2 labels changed. A blind AI sample of 40 outputs was chosen to be rich in failures, so it is not an accuracy estimate. Source: docs/human-review/owner-review-summary.md.', 'Development cases choose the configuration, so those numbers carry selection bias. The 31-case held-out set is one run on a frozen configuration but reuses development evidence in 25 of 31 cases. The second fresh set has 65 cases on new sources.', 'Measures: hit@8 (right passage in the top eight); behaviour accuracy (right kind of response: answer, abstain, clarify, refuse); false-answer rate; over-abstention; claim support from an AI judge from the same provider as the answer models, so errors may correlate; key-number recall. Intervals are 95% bootstrap intervals because the sets are small.', qa('Can you trust an AI judge?', 'Only for claim support, and I report its limit. Key numbers are scored by code, not by the judge.')]
  });
  add({
    layout: 'solo', chapter: 'What the experiments said', title: 'The experiment ladder', visual: experimentStaircase(m) || missing('The experiments'), caption: 'Retrieval was the only change that mattered.',
    source: 'LabourLens development runs, 237 questions',
    notes: ['Behaviour accuracy for the main model on 237 development questions. The ladder: baseline hybrid retrieval, a better answer prompt (A2), filter then rerank (A3, adopted provisionally), a wider candidate pool (A4) and a new planner prompt (A5). One factor changed per run; the three hatched steps moved accuracy inside the intervals and were not adopted. Outcomes are in the experiment registry (appendix J).', 'Corpus changes: the cleaner-text run (X1) and the final system check (X2, corpus v3, 14 runtime changes, cross-check, new gold version) moved no headline metric. X2 changed several things at once so it is a regression check, not an ablation. Ungrounded-number cases rose for the second model and claim support fell for both, and the check was widened at the same time, so measurement changed too. Source: docs/experiments/m7-e2e-fixes.md.', 'The registered 31-case held-out comparison gave a gain for the retrieval change with an interval that touched zero; it reuses development evidence and was rescored after post-run label edits (appendix E).', qa('Why did prompt changes not help?', 'The differences were inside the intervals. I kept the simpler prompt and logged the null results as decisions.')]
  });
  if (v2p) {
    add({
      layout: 'split', chapter: 'What the experiments said', title: 'On fresh questions, the gain was small',
      bullets: ['Filtering helped the main model by a few cases.', 'It did not help the second model.'],
      visual: bigStat({value: v2p.better, label: 'more questions answered correctly with filtering, main model', note: `${v2p.n_gold_cases} fresh questions`, size: 'xl'}), source: 'LabourLens second fresh test set',
      notes: [v2.verdict, `Held-out v2: 65 cases on six sources no earlier case cites (D-040), scored once per arm and model. The decision rule, interval level (90%), 20,000 resamples and seed ${v2p.seed} were written into FREEZE.md and signed (owner export a428db90, 31 Oct 2026) before the run at code commit 89c51d7; results were committed afterwards in 6f80ec9. Main model: ${fmt.pct(v2p.behaviour_accuracy.candidate)} with filtering against ${fmt.pct(v2p.behaviour_accuracy.baseline)} without, ${fmt.pts(v2p.paired_difference)}, ${v2p.better} better and ${v2p.worse} worse, interval ${fmt.pts(v2p.case_bootstrap_interval[0])} to ${fmt.pts(v2p.case_bootstrap_interval[1])}, McNemar exact p ${v2p.mcnemar_exact_p}. Second model: ${v2q ? `${fmt.pct(v2q.behaviour_accuracy.candidate)} in both arms, ${v2q.better} better and ${v2q.worse} worse` : 'no difference'}.`, 'Limits recorded with the result: one run per arm, sampled models, two of the three cases were first-step planner decisions in the hybrid arm, and without the five MTI cases the lower bound is not above zero.', qa('Did you demonstrate that filtering helps?', 'The pre-registered rule was met for one model by three cases, and not for the second. I report it as a small effect that did not replicate.')]
    });
  }
  add({
    layout: 'solo', chapter: 'What the experiments said', title: 'Why it missed', visual: errorBars(m) || missing('The error classes'), caption: 'Most misses were a missing calculation tool.',
    source: 'LabourLens second fresh test set',
    notes: [ea ? `Primary filtered arm: ${ea.n_mismatches_primary_r3} of ${ea.n_cases} cases missed; ${ea.over_abstentions_primary_r3} were over-abstentions, ${ea.numerical_over_abstentions_primary_r3} of them numerical comparison questions. The error analysis found no case where the scorer penalised a correct answer or the gold label was wrong. Source: experiments/heldout-v2/error-analysis.json.` : '', 'Accuracy is lower than in development mainly because of a tool gap: the calculation tool only worked on dataset observations and could not do arithmetic on a figure in report text. The fix is the next step; I will not quote a number until it has been run.', qa('Why not fix the tool and rerun straight away?', 'The second fresh-set result is frozen as run. A fix is a new experiment with its own stated rule.')]
  });

  // ---------- cost ----------
  add({
    id: 'cost', layout: 'solo', chapter: 'Cost', title: 'Choosing the model', visual: costBars(m) || missing('The cost comparison'), caption: costCaption(m),
    source: 'OpenAI list prices read on 30 October 2026; LabourLens baseline runs',
    notes: ['Prices per 1M tokens (specs/prices.yaml, read 2026-10-30, without cached-input discounts, so costs are upper bounds): gpt-6-luna $0.10 in and $0.50 out; gpt-5.6-luna $0.20 and $1.20; gpt-4.1-mini $0.40 and $1.60; judge gpt-6.1-terra $1.00 and $5.00; text-embedding-3-large $0.13 per 1M input. gpt-6-astra ($10 and $50) was excluded by the owner as too expensive and never run.', 'Bars are the baseline development run for each model: cost per question and median seconds. Measured per question in other runs: main model $0.00212, median 15.4 s, 95th percentile 37.0 s in the filter-then-rerank run; $0.00334 in the second fresh set. Total recorded spend is in the work-log ledger (appendix J); embedding calls and corpus builds are not in it. Tokens per case are not recorded.', 'Reranking adds a model call, so it raised the 95th percentile latency; I accepted that for the accuracy gain.', qa('Why this model, and what changes at 10 times the traffic?', 'gpt-6-luna matched the more expensive models on my development set at a fraction of the cost. At 10 times the traffic the daily ceiling and rate limits matter more than cost per question, so I would add a provider-side spend cap, cache the planner prompt, keep reranking for questions that need it, and re-run the comparison on the second fresh set before changing anything.')]
  });
  add({
    id: 'product', layout: 'split', chapter: 'Cost', title: 'Running it live',
    bullets: ['Every answer links to its source passage.', 'A budget is reserved before any paid call.', 'No spend cap is set on the provider account yet.'],
    visual: bigStat({text: '$0.05', label: 'reserved per question, under a $2 daily budget', size: 'xl'}), source: 'LabourLens deployment notes',
    notes: ['Workbench: status badges (answered, abstained, needs clarification, refused), citation chips that turn red when a label has no matching evidence, and an evidence drawer with the exact excerpt and source link. One server in Singapore serves the live app behind access codes, on the third build at commit c297146, as reported by the owner.', 'Budget: $0.05 is reserved and persisted before any paid call starts, and the question is refused if it cannot be saved; the daily budget is an estimate, default $2.00, and zero blocks new questions; a kill switch blocks new questions but not calls already running. A provider-side OpenAI spend cap is not set and not verified. Source: docs/deploy.md.', 'Logging: a record per run with outcome, tool calls, cost and timings; identifiers hashed, secrets redacted, no hidden model reasoning, and a prune command for old logs. Source: docs/audit-and-logging.md.', qa('What would you add before real traffic?', 'A provider-side hard spend cap first, then per-user quotas, a backup procedure and a measured memory profile under load, none of which I have verified.')]
  });

  // ---------- safety ----------
  add({...figSlide('fig-threat-matrix', {title: 'Safety tests'}), title: 'Safety tests', id: 'safety', chapter: 'Safety', layout: 'solo', human: 'LabourLens threat tests, 36 attack cases',
    caption: 'Most failures were poisoned report passages.',
    notes: ['36 handwritten attack cases in six categories: direct injection, poisoned passage, sensitive data, unsafe tool use, unsupported claims and a failing MCP server. One run per configuration, so a pass rate is not a guarantee. Retrieved text is treated as untrusted data and tools are read-only. The defences did not change the result: the same failures appear with and without them, mostly the poisoned passage that T-I06 describes. In the final-code run on corpus v3 the main model passed 36 of 36 and the second model 35 of 36.', qa('Did the defences work?', 'The suite does not show a defence effect. The same failures appear with and without them.')]});
  add({
    layout: 'solo', chapter: 'Safety', title: 'What protects it, and what does not',
    visual: two('Protects it', ['Retrieved text is treated as data.', 'Tools are read-only.', 'Hard step and time limits.'], 'Does not', ['The attack scanner is weak.', 'Quotes are not checked for meaning.', 'One MCP filter missed an attack.']),
    source: 'LabourLens threat model and independent reviews',
    notes: ['Controls in place: untrusted-data marking in the model context, read-only enum-typed tools, step, retry and time caps, secrets kept server-side and redacted in logs, and citations validated before display.', 'Gaps: the ingestion scanner is heuristic, and all five paraphrased malicious probes bypassed it in a second blind AI review (detector-only evidence, no observed exploit); quote presence does not show a quote supports the claim; the MCP input filter missed one paraphrased instruction in the saved transcript.', qa('What is your biggest security gap?', 'The scanner. A model-assisted screen tested on a larger, human-written set is the next step I would take.')]
  });
  add({id: 'mcp', chapter: 'Safety', layout: 'solo', title: 'The MCP server', visual: mcpDiagram(), source: 'LabourLens MCP server and client design',
    caption: 'Read-only tools. Direct calls are faster, so the app uses them by default.',
    notes: [`The server exposes nine read-only tools, 2 resources and 1 prompt over statistics and the source catalogue, with no MOM report text. The client treats the server as untrusted: allow-listed launch, schema checks, deadlines and size limits. The web app does not route through MCP; direct calls are the default and MCP is an optional route (D-028). Median per call ${mx.compared_datasets != null ? 'was 22.7 ms over MCP against 4.4 ms direct' : ''}; connecting once costs ${fmt.num(mx.connection_seconds, 2)} s; output differed from direct calls on ${fmt.int(mx.different_outputs)} of ${fmt.int(mx.compared_datasets)} datasets. Six scripted failure behaviours were observed against a hostile test server. Latency chart in appendix G.`, qa('Then why build it?', 'The assessment asks for a working server and client with trust boundaries and a comparison. I measured what MCP costs and kept direct calls as the default.')]
  });

  // ---------- process ----------
  add({
    id: 'process', layout: 'split', chapter: 'How I worked', title: 'How I worked with AI agents',
    bullets: ['I made the scope and design decisions.', 'Agents drafted code and first-pass labels.', 'Independent reviews caught errors.'],
    visual: bigStat({text: 'Gates', label: 'approval before every phase', size: 'xl'}), source: 'LabourLens project instructions',
    notes: ['Operating model from the project instructions: explore, compare, recommend, discuss, approve, implement, verify, document. Agents proposed options with trade-offs and I chose. Independent blind AI reviews checked the gold labels, the answers and the extracted passages. Held-out runs were frozen and gold versions are hashed into every score. Tool arguments and answer output are strictly typed so a malformed result is rejected, not displayed.', 'I decided scope, sources, label policy, what counts as adopted and the held-out rule. Agents proposed designs, wrote code and drafted gold cases; I reviewed 45 of those cases.', qa('What would an AI-only process have missed?', 'The judge cache keyed by case id survived gold changes. A human gate and an independent review found it.')]
  });
  add({
    id: 'wrong', layout: 'solo', chapter: 'How I worked', title: 'What went wrong',
    visual: rows([['Stale judge cache', 'Key caches by what can change.'], ['Scorer too strict', 'Test the scorer first.'], ['A test that never ran', 'A pass needs proof it ran.'], ['Labels edited late', 'Freeze first, disclose edits.'], ['Flattened tables', 'Audit data before measuring.'], ['One lucky pass', 'One run is not stability.']]),
    source: 'LabourLens experiment log',
    notes: ['Each item has a cause, a fix and a status in the work log (appendix J): a judge cache keyed by case id that survived gold changes; a calculation scorer that over-constrained prose and units; a threat fixture that passed vacuously under the filtered retrieval; four gold edits after the held-out run, disclosed with the original scores kept; extraction defects; and the planted figure that passed once and failed once.', qa('Which mistake are you least comfortable with?', 'The post-run gold edits. I disclosed them and kept the original scores beside the rescored ones, which is why I relied on the second fresh set.')]
  });

  // ---------- limits and next ----------
  add({
    id: 'limits', layout: 'solo', chapter: 'Next', title: 'Limits, and what next',
    visual: two('Limits', ['Most reference answers were drafted by an AI.', 'The fresh-question gain is small.', 'The attack scanner is weak.'], 'Next', ['Fix the calculation gap.', 'Independent human review of labels.', 'A spend cap on the provider account.']),
    source: 'LabourLens evaluation report',
    notes: [`Limits in full are in appendix H (${[...(c.limits?.querySelectorAll('.pr-limit') || [])].length} recorded). Labels: 45 of 268 reviewed, 95 of 125 review cards agreed with an AI suggestion. Held-out sets: the 31-case set reuses development evidence; the second set shows three cases for one model. Safety: the planted figure passed once and failed once for one model; the scanner missed all 5 paraphrased probes. Corpus: registered results ran on the first build, not the third that the demo serves. Cost: list-price estimates, and the AI judge shares a provider with the answer models.`, 'Next steps in full are in appendix I: run the fix for the calculation gap as a new experiment with its rule stated first, test the cross-check beyond one planted case, add independent review, count extraction defects corpus-wide, replace the scanner, and soften the period filter.', qa('If you had one more week?', 'Fix the calculation gap and retest on the second fresh set, then add blinded independent review of the draft labels.')]
  });

  // ---------- close ----------
  add({
    layout: 'split', chapter: 'Close', title: 'Summary',
    bullets: ['It answers with a source, or declines.', 'Filtering by period moved retrieval most.', 'The fresh-question gain is small.'],
    visual: bigStat({value: hitNow, format: pct, text: 'not recorded', label: `right passage in the top 8, up from ${hitBase}`, size: 'xl'}), source: 'LabourLens retrieval and evaluation results',
    notes: [`Five findings behind these lines: hit@8 from ${L ? pct(L.R0['hit@8']) : ''} to ${L ? pct(L.R3['hit@8']) : ''} on ${fmt.int(m.ladder?.n_cases)} development questions; ${pct(dev.rate)} behaviour accuracy on ${fmt.int(a3?.metrics?.n_cases)} development cases, used to choose the configuration; ${v2p ? v2p.better : ''} cases of gain on the second fresh set for the main model, none for the second; ${luna ? `${luna.passed} of ${luna.n_scored}` : ''} threat cases passed in the first suite with the planted figure not shown stable; ${fmt.int(mx.different_outputs)} of ${fmt.int(mx.compared_datasets)} datasets differing between MCP and direct calls.`, qa('What is the headline?', 'Filtering by period and series before ranking is what moved retrieval. Numbers from code and cited quotes make answers checkable. The independent evidence for the retrieval gain is small.')]
  });
  {
    const date = m.generatedAt ? m.generatedAt.slice(0, 10) : 'an unknown date';
    add({
      layout: 'text', chapter: 'Close', title: 'Sources',
      bullets: ['Statistics: Ministry of Manpower and SingStat via data.gov.sg, under the Singapore Open Data Licence.', 'MOM reports remain the Ministry\u2019s.', 'Model prices read on 30 October 2026.'],
      source: '',
      notes: [`Build provenance: report built ${date} from commit ${m.commit ? m.commit.slice(0, 7) : 'unknown'}, ${fmt.int(m.artifactCount)} committed artifacts; numbers not in the report data cite a document, and the report is rebuilt with uv run labourlens build-report.`, 'MOM report text is not shown beyond short excerpts the live agent cites, and no quote in the deck is longer than six words.', 'Fonts: Geist, SIL OFL 1.1. Slides: reveal.js 6.0.2, MIT. Icons: Phosphor, MIT.']
    });
  }

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
        group(heading('Gold labels and review'), list(['Gold v3.5: 45 cases owner-reviewed, 223 AI drafts. Of 125 owner cards, 95 agreed with an AI suggestion. Not independent review.', `Development rows use ${goldOf(a3).label}; held-out rows use ${goldOf(r3).label}. Both were rescored from saved outputs after post-run label edits.`, 'Registered results ran on corpus v1 and the X1 runs on corpus v2. Corpus v3 (85 sources) has two measured evaluations, the X2 development regression check and the e2efix threat run, and no held-out or evidence-disjoint evaluation.'])),
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
      source: 'docs/01_REQUIREMENTS_AND_SCOPE.md, docs/experiments/, docs/decisions.md, docs/audit-and-logging.md',
      notes: ['Full text of the planning, data-choice and operations material that the main slides summarise.']
    });
  });

  // Appendix index lists the lettered slides.
  const idx = el('ul', 'deck-index');
  appendixIndex.forEach(([letter, title]) => idx.append(el('li', '', `${letter}. ${title}`)));
  indexSpec.visual = idx;
  indexSpec.indexItems = appendixIndex;

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
