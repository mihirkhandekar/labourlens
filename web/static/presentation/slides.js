// The deck: every slide is declared here as data. Charts and tables are the ones the chapter
// modules already draw from report.json; this file picks them out of an off-screen pool, gives each
// slide an action title and at most three bullets, and moves the detail into speaker notes or the
// appendix. Numbers on slides come from report.json (through the model) or from the document named
// in the slide's source line. Text is set with textContent only.
import {el, fmt, finite} from '../charts.js';
import {model, metricOf, goldOf} from './model.js';
import {stat, textStat, countRunner, dataTable} from './ui.js';
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
const missing = what => el('p', 'deck-missing', `${what} needs data that report.json does not contain.`);
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
  const specs = [];
  const add = (spec) => specs.push(spec);

  // ---------- story helpers ----------
  const rows = (items) => {
    const ul = el('ul', 'deck-limit-rows');
    items.filter(Boolean).forEach(([head, body, picked]) => { const li = el('li', picked ? 'is-pick' : ''); li.append(el('strong', '', head), el('span', '', body)); ul.append(li); });
    return ul;
  };
  const withSoWhat = (visual, line) => { const box = el('div', 'deck-stackv'); box.append(visual, el('p', 'deck-sowhat', line)); return box; };
  const qa = (q, a) => `Likely question: ${q} Model answer: ${a}`;
  const periods = m.periods();
  const latest = id => m.values(id, periods).filter(finite).pop();
  const pctS = v => `${v.toFixed(1)}%`;
  const findings = [...(c.data.querySelectorAll('.pr-finding') || [])].map(li => ({head: text(li, 'strong'), body: text(li, 'span')}));
  const ledgerTitle = text(c.work, '#fig-ledger .pr-fig-title');
  const v2 = m.section('evaluation').heldout_v2;
  const v2arm = (arm, model) => v2?.arms?.find(a => a.arm === arm && a.model === model)?.metrics;
  const v2p = v2?.paired?.['gpt-6-luna'], v2q = v2?.paired?.['gpt-5.6-luna'];
  const ea = v2?.error_analysis;
  const work = m.section('work');
  c.work._blocks = [...(c.work?.querySelectorAll('.pr-block') || [])];

  // ---------- opening ----------
  add({
    layout: 'title', chapter: 'Start',
    title: 'Cited answers from Singapore labour-market data',
    sub: 'I built LabourLens to answer analyst questions from MOM statistics and reports with a source for every number, or to say that nothing is published.',
    source: '',
    notes: ['I will tell this as the story of how I thought about the problem, what I built, what I measured and where it fell short.', 'Keys: arrows, space and page keys move; F is fullscreen; O or Escape opens the overview; S shows these notes; add ?print-pdf to the address to export a PDF.', 'Every number comes from report.json or from the document named under the slide. The last slide gives the build provenance.', qa('What is the one-sentence version?', 'A research assistant that answers labour-market questions from MOM data with a checkable source for every number, and refuses or abstains when the data does not support an answer.')]
  });
  add({
    layout: 'agenda', chapter: 'Start', title: 'What I will cover, in the order I did it',
    items: [['problem', 'The problem'], ['framing', 'How I framed it'], ['data', 'The data I chose'], ['eda', 'What the data told me'], ['parsing', 'Reading the reports'], ['retrieval', 'Retrieval'], ['agent', 'The agent'], ['contract', 'The answer contract'], ['measure', 'How I measured'], ['experiments', 'What the experiments said'], ['cost', 'Models and cost'], ['safety', 'Safety'], ['mcp', 'MCP'], ['product', 'The product'], ['process', 'Working with AI agents'], ['wrong', 'What went wrong'], ['limits', 'Limits and next steps']],
    notes: ['The order follows the questions a reader would ask next: what problem, what did you decide to build, what data, what did you learn from it, how did you retrieve, how did the agent behave, how did you measure, what did it cost, what went wrong.', 'The appendix holds the detail that did not fit on a slide and is reachable from the overview.']
  });

  // ---------- problem ----------
  add({
    id: 'problem', layout: 'solo', chapter: 'The problem',
    title: 'Policy researchers need one number, with its period, series and a source they can check',
    visual: withSoWhat(rows([
      ['Who asks', 'Singapore policy researchers and labour-market analysts comparing MOM statistics with MOM commentary.'],
      ['What they need', 'A figure for the right period, series, population and release, and a link to where it was published.'],
      ['What they cannot accept', 'A confident number that is stale, from the wrong series, or has no source.']
    ]), 'The next slide shows how a simple question already has several right-looking answers.'),
    source: 'MOM and SingStat via data.gov.sg; project scope notes',
    notes: ['The research users are recorded in the approved scope: Singapore policy researchers and labour-market analysts (ADR-001, CLAUDE.md). The needs on this slide are my framing of what they require.', qa('Why not build for the general public?', 'The approved scope names policy researchers and analysts. A narrower user makes the cases in the gold set easier to define and check.')]
  });
  {
    const a = latest('unemployment_resident_sa'), b = latest('unemployment_overall_sa'), n = latest('unemployment_resident_nsa');
    add({
      layout: 'solo', chapter: 'The problem',
      title: finite(a) && finite(b) && finite(n) ? `One question, three published answers: ${pctS(b)}, ${pctS(a)} and ${pctS(n)}` : 'One question, several published answers',
      visual: withSoWhat(rows([
        ['Question', `"What was the unemployment rate in ${fmt.quarter(to)}?"`],
        ['Overall, seasonally adjusted', finite(b) ? pctS(b) : 'not recorded'],
        ['Resident, seasonally adjusted', finite(a) ? pctS(a) : 'not recorded'],
        ['Resident, not adjusted', finite(n) ? pctS(n) : 'not recorded']
      ]), 'A system that picks one without naming the series gives an answer nobody can check.'),
      source: 'MOM resident and overall unemployment rates via data.gov.sg',
      notes: ['These are three real series in the data. Each is correct for a different question. A reader who is handed one of them without its label cannot tell which question was answered.', `Values from report.json charts: unemployment_resident_sa, unemployment_overall_sa, unemployment_resident_nsa, ${fmt.quarter(to)}.`, qa('Is that a real failure of language models?', 'I did not measure a plain model on this question. It is the design problem: the system must name the series, or ask which one is meant. The evaluation later measures how often it does.')]
    });
  }
  add({
    layout: 'solo', chapter: 'The problem', title: 'A plain language model or a keyword search each fails in a different way',
    visual: withSoWhat(rows([
      ['Plain language model', 'Can state figures from memory, mix up series, quote stale numbers, give no citation, and has no way to say a figure is not published.'],
      ['Keyword search', 'Finds passages, but does not choose the period, series or release, does not calculate, and does not say when nothing matches.'],
      ['Both', 'Neither refuses a request that the data cannot support, such as a forecast or a cause.']
    ]), 'So the system needs retrieval, typed tools, code for arithmetic and a rule for when to stop.'),
    source: 'LabourLens design notes and system card',
    notes: ['This is the reasoning behind the architecture, not a measured comparison. The retrieval ladder and the evaluation later put numbers on the parts that can be measured.', qa('Why not just use a long context window with the reports?', 'It would still not choose a series or release for the user, would not compute changes exactly, and gives no stable citation. I wanted each of those to be a checkable step.')]
  });
  add({
    layout: 'solo', chapter: 'The problem', title: 'The brief asks for evidence and evaluation, not a chatbot',
    visual: withSoWhat(rows([
      ['What I was asked for', 'A research assistant over two kinds of source, with retrieval, a bounded agent, an MCP server and an evaluation.'],
      ['How I read it', 'The assessment tests judgement as much as code: framing, baselines, honest measurement and what I would do next.']
    ]), 'That reading shaped the scope I chose.'),
    source: 'Assessment brief; project requirements notes',
    notes: ['Two source types are required: structured statistics and unstructured reports. My reading of the brief is that it tests judgement as much as code.', qa('What did you prioritise?', 'The project instructions rank retrieval quality, evaluation, security and reproducibility above interface polish.')]
  });

  // ---------- framing ----------
  add({
    id: 'framing', layout: 'split', chapter: 'How I framed it',
    title: `I bounded the scope to ${nQ} quarters, four MOM series and the MOM reports`,
    bullets: ['Window: ' + `${fmt.quarter(m.scope[0])} to ${fmt.quarter(to)}. Earlier documents are context only.`, 'Requests outside the window must abstain.', 'Approved: the Singapore labour-market domain, four datasets and five MOM publications (ADR-001).'],
    visual: bigStat({value: nQ, label: `${fmt.quarter(m.scope[0])} to ${fmt.quarter(to)}`, note: 'Quarterly observations', size: 'xl'}),
    source: 'Project scope decision (ADR-001); data.gov.sg dataset periods',
    notes: ['The scope is recorded in docs/decisions/ADR-001 and docs/01_REQUIREMENTS_AND_SCOPE.md. Coverage varies by dataset and quarter; D-003 set a per-dataset drop rule: a dataset must reach 2026 Q2 and pass its contract at ingestion.', qa('Why this window?', 'ADR-001 fixed Q1 2024 to Q2 2026 as the bounded answer scope. It is not a guarantee that every dataset has every quarter, which is why coverage was checked at ingestion.')]
  });
  add({
    layout: 'solo', chapter: 'How I framed it', title: 'Out of scope by decision: forecasts, causal claims, personal advice and open web research',
    visual: withSoWhat(rows([
      ['Forecasting', 'Out of scope in ADR-001.'],
      ['Causal claims', 'The system must refuse an unsupported inference, for example that AI caused a retrenchment trend.'],
      ['Personal employment advice', 'Out of scope in ADR-001.'],
      ['Unrestricted web research', 'Out of scope. Allowed source hosts are restricted.']
    ]), 'Refusing is one of the behaviours the gold set tests.'),
    source: 'Project scope decision (ADR-001); requirements and scope notes',
    notes: ['Recorded in docs/decisions/ADR-001, CLAUDE.md (approved scope) and docs/01_REQUIREMENTS_AND_SCOPE.md, which lists the unsupported-causal case and the injection case as required behaviours.', qa('Is refusing a feature or a limitation?', 'A designed behaviour. Refusal and abstention are scored in the gold set, and over-abstention is measured separately so that refusing cannot hide weak retrieval.')]
  });
  add({
    layout: 'solo', chapter: 'How I framed it', title: 'Before coding the retrievers, the requirements fixed how I would evaluate',
    visual: withSoWhat(rows([
      ['Cases', 'At least 30 evaluation cases and a separate development set. Gold ids labelled after ingestion.'],
      ['Baseline', 'An explicit non-LLM baseline: BM25 with extractive passages.'],
      ['Comparisons', 'Controlled configurations, with model, prompt and corpus fixed.'],
      ['Metrics', 'Retrieval, correctness, groundedness, citations, abstention, calculation and security, with latency and cost.'],
      ['Review and reporting', 'A sample really reviewed by a human, and every negative result kept.']
    ]), 'Within that frame I wrote hypotheses down before running the experiments.'),
    source: 'Project requirements and scope notes',
    notes: ['These are the evaluation design commitments in docs/01_REQUIREMENTS_AND_SCOPE.md, section "Evaluation design commitments to establish before coding retrievers". The success statement there reads: requirements implemented and traceable, conclusions backed by verifiable passages or observations, actual metrics with error analysis, and a creator who can explain trade-offs and failures.', 'docs/05_EVIDENCE_AND_STUDY_PLAN.md adds the rule that measured outcomes need supporting files and a command or review record, and that hypotheses must be marked as such.', qa('Where is the success definition?', 'In the requirements note, as above. I did not define a numeric target before building; the criteria are about traceability and honest measurement.')]
  });
  add({
    layout: 'solo', chapter: 'How I framed it', title: 'The hypotheses are written in the experiment notes, with a null for retrieval',
    visual: withSoWhat(rows([
      ['Retrieval, written before any R1 or R2 number', 'H1: using the quarter and release named in a question raises hit@8 on questions that name one. H2: an LLM rerank of the top 30 fixes ordering among near-duplicates. H3: the combination gains at least as much as the larger single change. Null: nothing separates from the baseline beyond noise.'],
      ['Agent end to end, not a timestamped pre-registration', 'H1: filter plus rerank reduces missing-evidence abstentions. H2: explicit missing-data instructions help. H3: widening a weak pool helps. H4: a pricier generator is worth the price. H5: the planner should research the legitimate part of a rules-override question.'],
      ['BM25 held-out run, written before the run', 'Three configurations named in advance, and all three reported whatever the outcome.']
    ]), 'The data came next, because the hypotheses depend on what the series look like.'),
    source: 'Experiment notes: BM25 baseline, retrieval improvements and agent end to end',
    notes: ['Sources: docs/experiments/m6-retrieval-improvements.md (section Pre-registered design, written before any R1/R2 number), docs/experiments/m6-agent-end-to-end.md (states that its hypotheses are not claimed to be a timestamped pre-registration), docs/experiments/m2-bm25-baseline.md (Pre-registered held-out run).', 'Rule: a keyword search (BM25) is the non-LLM baseline and each run changes one factor, except X2, which I label a regression check.', qa('What would have falsified the retrieval hypotheses?', 'The null: no configuration separating from the hybrid baseline beyond noise. The pre-registered note says a negative result would be reported as such.')]
  });

  // ---------- data ----------
  add({
    id: 'data', layout: 'solo', chapter: 'The data I chose',
    title: 'ADR-001 approved four datasets, and D-003 added the ones that create ambiguity and cross-checks',
    visual: withSoWhat(rows([
      ['The approved four', 'Resident unemployment rate, vacancy-to-unemployed ratio, retrenched employees, and employment change by sector, all quarterly (ADR-001).'],
      ['Population definitions', 'Overall and citizen unemployment rates create resident versus overall ambiguity, a strong disambiguation test (D-003).'],
      ['Rate versus ratio', 'The vacancy rate and vacancy counts test that a ratio is not a rate (D-003).'],
      ['Cross-checks', 'Retrenchment splits by contract type give a parts-versus-total check; re-entry into employment supports a freshness and revision case (D-003).']
    ]), 'The reports add the methodology and definitions that the datasets lack (D-006).'),
    source: 'Ministry of Manpower and SingStat via data.gov.sg',
    notes: ['Recorded in docs/decisions/ADR-001 (the four approved datasets) and docs/decisions.md D-003, 30 Oct 2026 (the table "Why it earns its place"). The data.gov.sg listing probe found about 190 MOM-managed datasets; the shortlist came from it. The corpus grew to 36 dataset snapshots.', qa('Why these datasets?', 'The approved four came with the scope decision. The additions were chosen where the record says they create a distinct test: a population ambiguity, a rate versus ratio confusion, a parts-versus-total check or a revision case.')]
  });
  add({
    layout: 'solo', chapter: 'The data I chose', title: 'I left out stale, off-topic and non-labour sources',
    visual: withSoWhat(rows([
      ['Foreign workforce datasets', 'Last updated June 2024, so stale, and they would not resolve the 2026 employment-growth question (D-003).'],
      ['Wages, annual retrenchment incidence, short work-week', 'Lower fit with the quarterly scope; the short work-week dataset may lack 2026 Q2 (D-003, tier 2).'],
      ['MTI GDP revision pairs', 'Not labour evidence; the labour chapters repeat MOM figures. Rejected by the owner (D-040).'],
      ['MTI and MAS pages without verified links', 'No PDF links found on the MTI page and a maintenance page at MAS, so skipped (D-006).']
    ]), 'What stayed in needed provenance and rights recorded for every record.'),
    source: 'Project decision log (D-003, D-006, D-040)',
    notes: ['Recorded in docs/decisions.md: D-003 (excluded for now, tier 2), D-006 (probe results of 30 Oct 2026) and D-040 (alternatives table, 31 Oct 2026). Holidays, leave, trade unions and arbitration datasets were dropped as off topic.', qa('Did you reject anything because of licence?', 'MOM report PDFs carry a copyright notice, so they stay local rather than in the repository. That is a handling rule, not an exclusion from the analysis.')]
  });
  add({
    layout: 'solo', chapter: 'The data I chose', title: `The statistics measure, and ${fmt.int(types.report_pdf)} report PDFs and ${fmt.int(types.release_html)} release pages explain`,
    visual: withSoWhat(rows([
      ['Datasets', `${fmt.int(types.dataset_csv)} snapshots. A number for a quarter, in a defined series.`],
      ['MOM reports', 'Methodology and definitions, which answer what an indicator means (D-006), and the advance and final figures that disagree.'],
      ['A cross-source question', 'Needs the figure from the dataset and the explanation from the report, each cited separately.']
    ]), 'Both sides need a record of where they came from.'),
    source: 'LabourLens source register, MOM labour market reports',
    notes: [`Source counts from report.json sources.metrics.by_type: ${types.dataset_csv} dataset snapshots, ${types.report_pdf} report PDFs, ${types.release_html} release pages.`, 'D-006 records that the annual MOM report adds methodology and definitions. docs/01_REQUIREMENTS_AND_SCOPE.md lists the preliminary versus final case (Q2 2026, 10,700 versus 11,400).', qa('Why not use only the datasets?', 'The requirements include questions about revisions and definitions, and those are answered from report text.')]
  });
  add({...figSlide('fig-sources', {title: 'Source records'}), id: undefined, chapter: 'The data I chose', layout: 'split',
    bullets: [`Every record carries publisher, date, rights status, release stage and a snapshot hash.`, `Only ${m.sources.filter(r => r.redistribution === 'commit_raw').length} of ${m.sources.length} records may be committed to Git. Report PDFs stay local.`],
    human: 'LabourLens source register'});
  add({
    layout: 'solo', chapter: 'The data I chose', title: 'The corpus grew three times, each time for a stated reason',
    visual: withSoWhat(rows([
      ['Version 1, 13,484 passages', 'The corpus the registered results ran on.'],
      ['Version 2, 15,915 passages', 'Extraction fixes after an audit found flattened tables and lost notes (D-037).'],
      ['Version 3, 16,419 passages, 85 sources', 'Six sources no earlier case cites, added so a second held-out set could be independent (D-040).']
    ]), 'With the data in place, I looked at it before designing anything else.'),
    source: 'README, corpus versions; LabourLens decision log',
    notes: ['Frozen v1 and v2 results are kept, not overwritten. The served application runs corpus v3 and commit c297146, as reported by the owner, with /healthz fingerprint d402120f6f8f and 1,847 chunks.', qa('Why does the corpus version matter for results?', 'A result is only valid for the corpus it ran on. Registered results ran on v1; v3 has two measured evaluations and no registered held-out result.')]
  });

  // ---------- EDA ----------
  add({...figSlide('fig-unemployment', {title: 'Unemployment rates'}), id: 'eda', chapter: 'What the data told me', layout: 'split', human: 'MOM resident, overall and citizen unemployment rates via data.gov.sg',
    bullets: [findings[0] ? `${findings[0].head}.` : 'Adjusted and unadjusted rates are different series.', 'So I decided that every answer names population, adjustment and unit, and asks which one when the question does not.'],
    notes: ['This is the first required EDA finding. A plain unemployment rate question is ambiguous across population and seasonal adjustment.', qa('What did EDA change in the design?', 'Series identifiers carry population and adjustment, the agent asks a clarifying question when the series is open, and the scorer counts a missing clarification as a behaviour error.')]});
  {
    const ids = [['unemployment_overall_sa', 'Overall, adjusted'], ['unemployment_resident_sa', 'Resident, adjusted'], ['unemployment_citizen_sa', 'Citizen, adjusted'], ['unemployment_resident_nsa', 'Resident, not adjusted']];
    const POP = {resident: 'resident', overall: 'overall', citizen: 'citizen'}, ADJ = {seasonally_adjusted: 'seasonally adjusted', not_adjusted: 'not adjusted'};
    add({
      layout: 'solo', chapter: 'What the data told me', title: 'Four unemployment series answer four different questions',
      visual: withSoWhat(rows(ids.filter(([id]) => m.charts[id]).map(([id, label]) => [label, `${POP[m.charts[id].population] || m.charts[id].population}, ${ADJ[m.charts[id].adjustment] || m.charts[id].adjustment}, ${fmt.quarter(to)}: ${finite(latest(id)) ? pctS(latest(id)) : 'not recorded'}`])),
        'So I decided to store each series under its own identifier and never merge them silently.'),
      source: 'MOM and SingStat unemployment datasets via data.gov.sg',
      notes: ['This is the population and definition finding: overall, resident and citizen are different populations, and adjusted and unadjusted are different treatments of the same quarter.', 'Values from report.json charts for the latest quarter.', qa('Why not pick the headline series and ignore the rest?', 'Analysts use all of them. Picking one silently is exactly the failure I set out to prevent.')]
    });
  }
  add({...figSlide('fig-retrenchments', {title: 'Retrenchments'}), chapter: 'What the data told me', layout: 'split', human: 'MOM retrenched employees via data.gov.sg',
    bullets: [findings[1] ? `${findings[1].head}.` : 'Retrenchments rose.', 'So I decided that the system describes movements and does not claim a cause. A why question gets the report text, or an abstention.'],
    notes: ['This is the second required EDA finding. Retrenchments and resident unemployment moved differently in the same period, which shows how easily a causal story gets attached.', findings[1] ? findings[1].body : '', qa('How does the agent handle a why question?', 'It can cite report commentary that states a reason, and it must label that as MOM commentary. It will not infer a cause from two series.')]});
  add({...figSlide('fig-revisions', {title: 'Advance and final figures'}), chapter: 'What the data told me', layout: 'split', human: 'MOM advance and final labour market reports, and the SingStat sector dataset',
    bullets: [findings[2] ? `${findings[2].head}.` : 'Advance and final releases differ.', 'So I decided that every answer carries its release stage, advance or final, and never merges them.'],
    notes: [findings[2] ? `${findings[2].head}. ${findings[2].body}` : '', findings[3] ? `${findings[3].head}. ${findings[3].body}` : '', qa('Which figure is right, advance or final?', 'Both, for their release. The answer must name which one it uses. The conflict cases in the gold set test exactly this.')]});
  add({...figSlide('fig-vacancy-ratio', {title: 'Vacancies per unemployed person'}), chapter: 'What the data told me', layout: 'split', human: 'MOM job vacancy to unemployed person ratio via data.gov.sg',
    bullets: ['A ratio recomputed from the published counts differs from the published ratio by up to 0.67, because the two come from different surveys.', 'So I decided to use the published ratio and never recompute it.'],
    notes: ['The validation report flags this as a warning, not an error. Source: docs/data-sheet.md, section 5.', qa('Why not recompute from counts to be consistent?', 'It would produce a number MOM never published. A cited figure must be one the publisher stands behind.')]});
  add({
    layout: 'solo', chapter: 'What the data told me', title: 'Four findings from the data each changed the design',
    visual: withSoWhat(rows([
      ['Ambiguous rate', 'Series identifiers carry population and adjustment, and the agent asks when they are open.'],
      ['Series that rise without a stated cause', 'Causal questions are refused or answered with cited commentary only.'],
      ['Advance and final differ', 'Answers name the release stage.'],
      ['Ratio from different surveys', 'Use the published value and do not recompute.']
    ]), 'The reports needed the same care, starting with how they were read.'),
    source: 'LabourLens data analysis, report.json charts',
    notes: ['This slide is the bridge from analysis to design. Each finding is a constraint that the agent and the scorer both enforce.', qa('What would you do with more time on EDA?', 'Count the revisions across more quarters and check whether the sector dataset total consistently sits above the MOM final figure. I only infer that migrant domestic workers explain it, which I have not verified.')]
  });

  // ---------- parsing ----------
  add({
    id: 'parsing', layout: 'solo', chapter: 'Reading the reports', title: 'In a 16-passage audit, all 4 sampled tables came out flattened',
    visual: withSoWhat(rows([
      ['What went wrong', 'PDF tables became newline-separated text: two adjacent rows merged into one passage, with column context lost. Some passages lost a note boundary, and HTML passages flattened superscripts.'],
      ['How I found it', 'Independent AI reviews sampled 16 passages and compared them with the original PDFs and rendered pages. No numerical transcription error turned up.'],
      ['What I fixed', 'Extraction fixes for control characters, note boundaries and superscripts produced corpus v2. The measured effect on retrieval and answers was none (X1).'],
      ['What I did not', 'There is no corpus-wide count of remaining defects, and table structure is still flattened.']
    ]), 'Reading was only the first half of retrieval. Next, how I found the right passage.'),
    source: 'Independent AI reviews of 16 sampled passages; MOM labour market reports',
    notes: ['The audit used PyMuPDF to read original blocks and rendered crops of the pages. Four of the 16 were table samples and all four flattened adjacent rows.', 'Source: docs/human-review/ai-pre-review-passage-spot-check.md, docs/evaluation-report.md.', qa('If extraction was flawed, why trust the results?', 'The sampled defects did not change numbers, and the X1 run on the fixed corpus moved no headline metric. I state the missing corpus-wide count as a limit.')]
  });

  // ---------- retrieval ----------
  if (L) {
    const ladder = [['R0', 'Hybrid baseline', 'Keyword search (BM25) plus dense embeddings, combined by rank fusion.'], ['R1a', 'Hard filter', 'Keep only passages from the requested period and release stage.'], ['R1b', 'Soft boost', 'Prefer matching passages without excluding others.'], ['R2', 'Model rerank', 'Reorder the top 30 candidates with a language model.'], ['R3', 'Filter, then rerank', 'The hard filter first, then the rerank.']];
    add({
      id: 'retrieval', layout: 'solo', chapter: 'Retrieval',
      title: `I climbed a ladder of retrievers: hit@8 went from ${pct(L.R0['hit@8'])} to ${pct(L.R3['hit@8'])}`,
      visual: withSoWhat(rows(ladder.map(([k, name, what]) => [`${k}: ${name}`, `${pct(L[k]['hit@8'])}. ${what}`, k === 'R3'])), 'Hit@8 is the share of questions whose right passage is among the top eight retrieved. The next slide shows the ladder with intervals.'),
      source: `LabourLens retrieval experiments on ${m.ladder.n_cases} development questions`,
      notes: ['One factor changes at each rung. R0 is the baseline from the early comparisons of BM25, dense retrieval and hybrid, where gaps were a few cases on 24 questions, so I treat the choice of hybrid as a baseline and not as a proved best.', `Source: report.json retrieval.ladder.configs, ${m.ladder.n_cases} development cases.`, qa('Why a hard filter before reranking?', 'A hard filter on period and release stage removes the wrong-vintage passages that a reranker would otherwise have to ignore. It was the largest single gain in the ladder.')]
    });
  }
  add({...figSlide('fig-ladder', {title: 'Retrieval ladder'}), title: 'With intervals, filtering gained more than reranking, and both together gained most', chapter: 'Retrieval', layout: 'split', human: 'LabourLens retrieval experiments on 128 development questions',
    bullets: [L ? `The hard filter alone (R1a) reached ${pct(L.R1a['hit@8'])}, the rerank alone (R2) ${pct(L.R2['hit@8'])}, so the pre-registered H1, using the named period and release, is supported.` : 'Filtering mattered more than reranking.', 'Embedding models differed by a few cases on 24 early questions (appendix C).', 'I chose R3, filter then rerank, as the agent default.']});
  add({
    layout: 'solo', chapter: 'Retrieval', title: 'What the retrieval study cannot show',
    visual: withSoWhat(rows([
      ['Labels', 'Most gold labels are AI drafts, and an LLM both drafted them and reranks.'],
      ['Development set', 'I inspected it many times, so it is not an unbiased estimate for new questions.'],
      ['Restated quarters', 'A hard period filter can exclude the right document when a later release restates an earlier quarter. This is documented and not fixed.'],
      ['Held-out', 'No retrieval-only measurement exists on the held-out set. It was compared end to end.']
    ]), 'So I put retrieval inside an agent and measured the whole.'),
    source: 'LabourLens evaluation report, expanded retrieval study',
    notes: ['The ladder tells me which rung helps on the development set. It does not tell me how it generalises.', qa('What would you test next on retrieval?', 'A soft period filter that widens when the candidate pool is weak, with a measured effect on restated quarters.')]
  });

  // ---------- agent ----------
  add({...figSlide('fig-graph', {title: 'The agent graph'}), id: 'agent', chapter: 'The agent', layout: 'split', human: 'LabourLens architecture notes and a recorded agent run',
    bullets: ['One bounded agent, not several: a model plans up to three read-only tool calls, then code checks the result.', 'The stepper replays a recorded run. It is a statistics-only smoke run with no report passages.'],
    notes: ['The agent is one LangGraph state graph with a planner, typed tools, evidence assessment, answer generation and validation. ADR-002 fixed one bounded agent; I did not build a multi-agent design.', qa('Why one agent?', 'Every extra agent is another place for a failure that I would have to trace and measure. One bounded graph with typed tools was enough for the questions in scope.')]});
  take(c.agent, '.pr-limits');
  add({
    layout: 'solo', chapter: 'The agent', title: 'Three typed tools, none able to write, fetch the web or run code',
    visual: withSoWhat(take(c.agent, '.pr-tools') || missing('The tool list'), 'The model chooses; code validates the arguments and does the arithmetic.'),
    source: 'LabourLens architecture notes and agent trace', cls: 'is-tools',
    notes: ['Arguments are checked against enums built from the source catalogue, so a model cannot invent a series name. Call counts are from the recorded runs in report.json.', qa('What stops the model from calling something dangerous?', 'There is no dangerous tool. The three tools are read-only, typed, and time-limited.')]
  });
  {
    const calc = metricOf(a3?.metrics?.calc_correct);
    add({
      layout: 'split', chapter: 'The agent', title: 'Numbers come from code, and the loop has hard limits',
      bullets: ['Changes are computed in decimal arithmetic from validated observations. The model does not do the arithmetic.', 'Limits: 2 evidence rounds, 6 tool calls, 10 seconds per call, 1 retry, 1 repair, 1,000 characters per question.', 'A tool outage ends as operational_failure, which is separate from missing evidence.'],
      visual: bigStat({value: calc.rate, format: pct, label: 'Calculations correct', note: `Run A3, gpt-6-luna, ${fmt.int(calc.n)} calculation cases`, size: 'xl'}),
      source: 'LabourLens evaluation run A3 and agent architecture notes',
      notes: ['The scorer requires a cited deterministic calculation. The 75.0% is on 24 cases, so one case is about 4 points.', 'Limits are enforced in code, not in the prompt. Source: docs/architecture.md, section 4; src/labourlens/agent/graph.py.', qa('Why not let the model compute and then verify?', 'A verifier needs the same arithmetic. Doing it once in code is simpler and exact.')]
    });
  }

  // ---------- contract ----------
  add({
    id: 'contract', layout: 'solo', chapter: 'The answer contract', title: 'Every claim carries a quote, and the answer takes one of five forms',
    visual: withSoWhat(rows([
      ['Answer', 'Cited claims, with a verbatim quote or an observation id, plus a calculation where needed.'],
      ['Abstain', 'The evidence does not support an answer, so no figure is given.'],
      ['Clarify', 'The series or period is open, so the agent asks which one is meant.'],
      ['Refuse', 'The request is out of bounds, such as a forecast or an edit to a published figure.'],
      ['Ignore an injected instruction', 'Retrieved text is data. An instruction inside a passage is not followed.']
    ]), 'A validator checks that quotes exist and labels match before anything is shown. It confirms a quote is there, not that it supports the claim.'),
    source: 'LabourLens system card and architecture notes',
    notes: ['Structured output is schema-validated. The status is one of eight named outcomes internally; these five are the behaviours a reader sees.', qa('How do you know a citation is real?', 'The validator confirms the quote appears in the cited passage and that the label matches the evidence. It cannot show the quote supports the claim, which is a stated gap.')]
  });
  {
    const steps = take(c.safety, '.pr-ti06-steps');
    add({
      layout: 'split', chapter: 'The answer contract', title: 'A planted wrong figure was cited as fact; a cross-check now catches it in some runs',
      bullets: ['T-I06 plants a false figure in a report passage. Before the fix, all five configurations cited it, and the quote and number checks passed.', 'A cross-check now compares passage figures with validated observations. It handled the case in both models in the first run after the fix.', 'In the final-code run gpt-5.6-luna failed it on an exact-string scorer check, so I do not call it solved.'],
      visual: steps || missing('The T-I06 sequence'), cls: 'is-steps', warn: true,
      source: 'LabourLens threat suite, T-I06 case and cross-check runs',
      notes: [text(c.safety, '.pr-hero-callout-text'), 'The failing run reported the dataset value and disclosed the planted figure in a caveat, but the scorer required an exact string. I did not change the scorer after seeing the run, which is itself a finding about scorer brittleness.', 'Decision D-038. Files: docs/experiments/m7-t-i06-crosscheck.md, experiments/threats/m7-e2efix-20261031/SUMMARY.md.', qa('Is this fixed?', 'One planted case with a closed-grammar cross-check passed in one run and not in the next for one model. It shows the mechanism works sometimes. It does not show it generalises.')]
    });
  }

  // ---------- measure ----------
  add({...figSlide('fig-review', {title: 'Gold set review'}), title: 'I reviewed 45 of 268 gold cases; 223 remain AI drafts', id: 'measure', chapter: 'How I measured', layout: 'split', human: 'LabourLens gold set and review records',
    bullets: ['The gold set has 268 cases: 237 development and 31 held out.', 'An AI drafted the labels. I reviewed 45 cases; 223 are still AI drafts.', 'Of 125 review cards, 30 are my own verdict and 95 agreed with an AI suggestion, so this is not independent annotation.'],
    notes: ['The review count is per card. A blind AI sample of 40 outputs is a separate check and was chosen to be rich in failures, so it is not an accuracy estimate.', 'No blinded second human annotator was used. Source: docs/human-review/owner-review-summary.md, README.md.', qa('Who wrote the gold set?', 'An AI drafted it under a label policy I decided. I reviewed 45 cases; 43 stayed and 2 labels changed. The rest are drafts, and I say so wherever a number depends on them.')]});
  add({
    layout: 'solo', chapter: 'How I measured', title: 'Development cases choose the configuration; held-out cases only score it',
    visual: withSoWhat(rows([
      ['Development, 237 cases', 'Used to compare configurations. Because I chose on them, the numbers carry selection bias.'],
      ['Held-out, 31 cases', 'One run on a frozen configuration, scored afterwards. It reuses development evidence in 25 of 31 cases, so it is not independent.'],
      ['Held-out v2, 65 cases', 'Written later on sources no earlier case cites, with the decision rule fixed first.']
    ]), 'The metrics themselves need plain definitions.'),
    source: 'LabourLens evaluation report and held-out freeze record',
    notes: ['Gold hashes are recorded with every score, so each result names the gold version it used. Registered held-out scores were rescored on later gold versions after post-run label edits, and the originals are kept.', qa('Why is the first held-out set not enough?', 'It shares evidence with development. That is why I redesigned it as v2 on new sources.')]
  });
  add({
    layout: 'solo', chapter: 'How I measured', title: 'Six measures, in plain words',
    visual: withSoWhat(rows([
      ['Hit@8', 'The right passage is among the top eight retrieved.'],
      ['Behaviour accuracy', 'The agent answered, abstained, asked or refused as the gold label says.'],
      ['False-answer rate', 'It answered when it should not have.'],
      ['Over-abstention', 'It declined when an answer was available.'],
      ['Claim support', 'An AI judge says the cited evidence supports the claim.'],
      ['Key-number recall', 'The figure the question needed appears in the answer.']
    ]), 'The judge is from the same provider as the answer models, so their errors may correlate. A zero unsupported rate on a sample does not show the answers are safe.'),
    source: 'LabourLens evaluation report, metric definitions',
    notes: ['Intervals are 95% bootstrap intervals; the interval matters as much as the rate on 31 or 65 cases, where one case is several points.', qa('Can you trust an AI judge?', 'Only for a limited purpose. It checks claim support. I report its limit, and the key numbers are scored by code, not by the judge.')]
  });

  // ---------- experiments ----------
  add({...figSlide('fig-progression', {title: 'Progression A1 to A5'}), id: 'experiments', chapter: 'What the experiments said', layout: 'split', human: 'LabourLens development runs A1 to A5 on 237 cases',
    bullets: ['A2 changed the answer prompt, A4 widened the candidate pool and A5 changed the planner prompt. None was adopted.', 'A3 changed retrieval to filter then rerank. I adopted it provisionally.', 'These are development results, so they carry selection bias.'],
    notes: ['One factor changed per run. Intervals are shown on the chart. Outcomes come from the experiment registry in the work log (appendix J).', qa('Why did prompt changes not help?', 'The differences were inside the intervals. I kept the simpler prompt, and logged the null results as decisions.')]});
  add({...figSlide('fig-paired', {title: 'Paired difference on held-out'}), chapter: 'What the experiments said', layout: 'split', human: 'LabourLens registered held-out runs on 31 cases',
    bullets: pair ? [`On the registered 31-case held-out set the gain from r3 over hybrid was ${fmt.pts(pair.diff)}, with an interval from ${fmt.pts(pair.ci95[0])} to ${fmt.pts(pair.ci95[1])}. Not demonstrated.`, 'The set reuses development evidence, so I treated it as weak evidence at best.', 'Scores were rescored after post-run label edits; the original scores are kept (appendix E).'] : []});
  add({
    layout: 'solo', chapter: 'What the experiments said', title: 'Corpus changes moved no headline metric, and X2 is a regression check, not an ablation',
    visual: withSoWhat(rows([
      ['X1, corpus v2', 'Extraction fixes only. No measurable change in retrieval or answer quality.'],
      ['X2, corpus v3', 'Corpus, 14 runtime changes, the cross-check and a new gold version changed together. Behaviour, false-answer, over-abstention, key-number recall and calculation intervals overlap A3.'],
      ['What did move', 'Cases with ungrounded numbers rose for gpt-5.6-luna and claim support fell for both models. The check was also widened, so measurement changed too.']
    ]), 'The registered held-out set could not settle the question, so I designed one that could.'),
    source: 'LabourLens runs X1 and X2; experiments log',
    notes: ['X2 is a check that the served system has not regressed. It cannot say which change caused any difference. Source: docs/experiments/m7-e2e-fixes.md, experiments/eval/agent-dev-X2-REPORT.md.', qa('Why call it a regression check?', 'Because several things changed at once. Calling it an ablation would claim a causal attribution that the design cannot support.')]
  });
  add({
    layout: 'solo', chapter: 'What the experiments said', title: 'Held-out v2: 65 new cases, a rule written before the run',
    visual: withSoWhat(rows([
      ['Evidence', 'Six sources that no earlier case cites, added in corpus v3 for this purpose.'],
      ['Cases', `${fmt.int(v2arm('r3', 'gpt-6-luna')?.n_cases)} cases, scored once per arm and model: r3 against hybrid retrieval, two models.`],
      ['Decision rule', 'The case and component bootstrap lower bounds must be above zero, with enough evidence components and no added false answers. I wrote it in FREEZE.md and signed it (owner export a428db90, 31 Oct 2026) before the run.'],
      ['Statistics', `${fmt.pct(v2p?.level ?? 0.9, 0)} intervals, ${fmt.int(v2p?.n_boot)} resamples, seed ${v2p?.seed}. Not pooled with the registered 31 cases.`]
    ]), 'Then I ran it once.'),
    source: 'LabourLens held-out v2 pre-registration and paired analysis',
    notes: ['The point of v2 is that the rule could fail. The rule and the seed were written down before any result. The signed approval block is in experiments/heldout-v2/FREEZE.md: owner export a428db90, signed 2026-10-31. The run used code commit 89c51d7, and the results were committed afterwards in 6f80ec9.', 'Source: report.json evaluation.heldout_v2; docs/decisions.md D-039 and D-040.', qa('What does pre-registered mean here?', 'The decision rule, the interval level and the seed were fixed in writing before the run, so I could not choose a favourable analysis afterwards.')]
  });
  if (v2p) {
    add({
      layout: 'split', chapter: 'What the experiments said',
      title: `r3 beat hybrid on ${v2p.better} cases and lost on ${v2p.worse} for gpt-6-luna; gpt-5.6-luna showed no difference`,
      bullets: [`gpt-6-luna: ${fmt.pct(v2p.behaviour_accuracy.candidate)} with r3 against ${fmt.pct(v2p.behaviour_accuracy.baseline)} with hybrid, ${fmt.pts(v2p.paired_difference)}, ${fmt.pct(v2p.level, 0)} interval ${fmt.pts(v2p.case_bootstrap_interval[0])} to ${fmt.pts(v2p.case_bootstrap_interval[1])}. The rule is met.`, `The effect is ${v2p.better} cases and the exact test gives p = ${v2p.mcnemar_exact_p}, so I would not call it a confirmed gain.`, v2q ? `gpt-5.6-luna: ${fmt.pct(v2q.behaviour_accuracy.candidate)} in both arms, ${v2q.better} better and ${v2q.worse} worse.` : ''].filter(Boolean),
      visual: bigStat({text: fmt.pts(v2p.paired_difference), label: 'r3 minus hybrid, gpt-6-luna', note: `${v2p.n_gold_cases} cases, held-out v2`, size: 'xl'}),
      source: 'LabourLens held-out v2 runs, paired analysis',
      notes: [v2.verdict, 'Limits recorded with the result: one run per arm, sampled models, two of the three cases were first-step planner decisions in the hybrid arm, and without the five MTI cases the lower bound is not above zero.', 'Source: report.json evaluation.heldout_v2.paired and condition_flags.', qa('Did you demonstrate that r3 helps?', 'The pre-registered rule was met for one model by three cases, and not for the second model. I report that as a small effect that did not replicate, not a result I would lean on.')]
    });
  }
  if (ea) {
    const cls = Object.fromEntries((ea.classes || []).map(x => [x.class, x.count]));
    add({
      layout: 'solo', chapter: 'What the experiments said', title: `${ea.n_mismatches_primary_r3} of ${ea.n_cases} cases missed, and ${(cls.tool_gap_text_figure_arithmetic || 0) + (cls.tool_gap_dataset_dimension_label_and_round_budget || 0)} of them are a tool gap, not retrieval`,
      visual: withSoWhat(rows([
        ['Tool gap, arithmetic on a figure in report text', `${cls.tool_gap_text_figure_arithmetic ?? 0} cases. The calculation tool only worked on dataset observations.`],
        ['Tool gap, dimension labels and round budget', `${cls.tool_gap_dataset_dimension_label_and_round_budget ?? 0} cases.`],
        ['Everything else', `${cls.answer_status_choice_non_answer ?? 0} answer-status choices, ${cls.retrieval_miss_both_arms ?? 0} retrieval miss, ${cls.model_reasoning_false_premise ?? 0} false premise, and ${(cls.scorer_penalised_correct_answer ?? 0) + (cls.gold_label_judged_wrong ?? 0)} scorer or gold-label errors.`]
      ]), `Accuracy is lower than in development mainly because of the tool gap. A tool-fix experiment on this frozen set is in progress, and I have no result from it yet.`),
      source: 'LabourLens held-out v2 error analysis',
      notes: [`Over-abstentions for the primary r3 arm: ${ea.over_abstentions_primary_r3}, of which ${ea.numerical_over_abstentions_primary_r3} are numerical comparison questions.`, 'The error analysis found no case where the scorer penalised a correct answer or the gold label was wrong. Source: experiments/heldout-v2/error-analysis.json.', qa('Why not fix the tool and rerun straight away?', 'The v2 result is frozen as run. A fix is a new experiment with its own pre-stated rule. It is being prepared, and I will not quote a number until it is run.')]
    });
  }

  // ---------- cost ----------
  {
    const table = dataTable('Standard list prices, short context', ['Model', 'Role', 'Input per 1M tokens', 'Output per 1M tokens'], [
      ['gpt-6-luna', 'Primary answer and planner model', '$0.10', '$0.50'],
      ['gpt-5.6-luna', 'Second model, for replication', '$0.20', '$1.20'],
      ['gpt-4.1-mini', 'Cheaper comparison, not adopted', '$0.40', '$1.60'],
      ['gpt-6.1-terra', 'AI judge', '$1.00', '$5.00'],
      ['text-embedding-3-large', 'Dense retrieval embeddings', '$0.13', 'not applicable'],
      ['gpt-6-astra', 'Excluded by me as too expensive', '$10.00', '$50.00']
    ]);
    add({
      id: 'cost', layout: 'solo', chapter: 'Models and cost', title: 'I chose the cheapest models that held up, and excluded the one at $10 per 1M input tokens',
      visual: withSoWhat(table, 'The prices are list prices without cached-input discounts, so every cost I quote is an upper bound.'),
      source: 'OpenAI list prices read on 2026-10-30 (specs/prices.yaml)',
      notes: ['Price table from specs/prices.yaml, retrieved 2026-10-30 from the OpenAI pricing page; prices change, so re-read before quoting.', 'gpt-6-astra is excluded from every comparison because I judged it too expensive for the project; it was never run.', 'Tokens per case are not recorded in report.json, so I quote cost per case and latency instead.', qa('Why this model, and what changes at 10 times the traffic?', 'gpt-6-luna matched the more expensive models on my development set at a small fraction of the cost. At 10 times the traffic the order changes: cost per question matters less than the daily ceiling and rate limits, so I would add a provider-side spend cap, cache the planner prompt, keep reranking for the questions that need it, and re-run the model comparison on held-out v2 before moving anything.')]
    });
  }
  {
    const costRow = (label, row) => { const x = row?.metrics; return x ? [label, fmt.money(x.cost_per_case_usd), fmt.seconds(x.latency_p50_s), fmt.seconds(x.latency_p95_s)] : [label, 'not run', '', '']; };
    const tbl = dataTable('Measured per case, from saved runs', ['Run and model', 'Cost per case', 'Median latency', '95th percentile latency'], [
      costRow('A3 development, gpt-6-luna', m.evalRow('dev-A3', 'gpt-6-luna')),
      costRow('A3 development, gpt-5.6-luna', m.evalRow('dev-A3', 'gpt-5.6-luna')),
      costRow('X2 regression check, gpt-6-luna', m.evalRow('dev-X2', 'gpt-6-luna')),
      costRow('X2 regression check, gpt-5.6-luna', m.evalRow('dev-X2', 'gpt-5.6-luna')),
      v2arm('r3', 'gpt-6-luna') ? ['Held-out v2 r3, gpt-6-luna', fmt.money(v2arm('r3', 'gpt-6-luna').cost_per_case_usd), fmt.seconds(v2arm('r3', 'gpt-6-luna').latency_p50_s), fmt.seconds(v2arm('r3', 'gpt-6-luna').latency_p95_s)] : null,
      v2arm('hybrid', 'gpt-6-luna') ? ['Held-out v2 hybrid, gpt-6-luna', fmt.money(v2arm('hybrid', 'gpt-6-luna').cost_per_case_usd), fmt.seconds(v2arm('hybrid', 'gpt-6-luna').latency_p50_s), fmt.seconds(v2arm('hybrid', 'gpt-6-luna').latency_p95_s)] : null
    ].filter(Boolean));
    add({
      layout: 'solo', chapter: 'Models and cost', title: `A question costs a fraction of a cent and takes about ${fmt.seconds(m.evalRow('dev-A3', 'gpt-6-luna')?.metrics?.latency_p50_s)} at the median`,
      visual: withSoWhat(tbl, `${ledgerTitle || 'Total spend recorded in the work log'}, across every phase. Embedding calls and corpus builds are not in that total.`),
      source: 'LabourLens saved evaluation runs; work log cost ledger',
      notes: ['Generation cost per case is from the metrics files, at list prices without cached-input discounts. Latency is saved wall time from the recorded runs.', ledgerTitle ? `${ledgerTitle}. The ledger lists agent runs, the AI judge, threat suites, answer-only studies and rerank experiments. Not counted: embedding calls, corpus-building runs and any run whose usage was not saved. The owner reports about $3 for X2 and the e2efix runs; that figure is owner-reported.` : '', 'Tokens per case are not in report.json, so I do not quote them.', qa('What does the median question cost, and what dominates the cost?', 'Under a cent for generation at list prices. The rerank model call and the planner rounds dominate, which is why latency rises with r3 and why I cap rounds and calls.')]
    });
  }
  {
    const pick = (s, mdl) => m.evalRow(`dev-${s}`, mdl);
    const trade = ['A1', 'A2', 'A3', 'A4', 'A5'].map(s => { const r = pick(s, 'gpt-6-luna'); const x = r?.metrics; return x ? [`${s}, gpt-6-luna`, pct(metricOf(x.behaviour_accuracy).rate), fmt.money(x.cost_per_case_usd), fmt.seconds(x.latency_p95_s)] : null; }).filter(Boolean);
    const mini = pick('A1', 'gpt-4.1-mini')?.metrics;
    if (mini) trade.unshift(['A1, gpt-4.1-mini', pct(metricOf(mini.behaviour_accuracy).rate), fmt.money(mini.cost_per_case_usd), fmt.seconds(mini.latency_p95_s)]);
    add({
      layout: 'solo', chapter: 'Models and cost', title: 'Accuracy bought with retrieval cost more time than money',
      visual: withSoWhat(dataTable('Development runs, 237 cases each', ['Run and model', 'Behaviour accuracy', 'Cost per case', '95th percentile latency'], trade), 'The adopted configuration is A3. It raised accuracy and p95 latency, because reranking adds a model call.'),
      source: 'LabourLens development runs A1 to A5',
      notes: ['The controlled configurations change one factor each: A2 the answer prompt, A3 retrieval, A4 the candidate pool, A5 the planner prompt. Source: report.json evaluation.rows agent-dev-A1 to A5.', 'gpt-4.1-mini is the cheaper comparison. It was not adopted (D-022).', qa('How did cost and latency drive the choice?', 'I accepted the extra p95 latency of A3 because it bought the largest accuracy gain at a cost per case that stayed well below a cent. I rejected configurations that cost more and did not move accuracy outside the interval.')]
    });
  }
  add({
    layout: 'solo', chapter: 'Models and cost', title: 'The live app reserves $0.05 per question under a $2 daily budget, and has no provider cap yet',
    visual: withSoWhat(rows([
      ['Per-run reservation', '$0.05 is reserved and persisted before any paid call starts. If it cannot be saved, the question is refused.'],
      ['Daily budget', 'An estimated ceiling, default $2.00. At zero, new live questions are blocked.'],
      ['Kill switch', 'Turning the demo off blocks new questions. It does not stop calls already running.'],
      ['Provider-side spend cap', 'Not set. I have not verified one on the provider account.']
    ]), 'The estimate is not a billing guarantee. The provider cap is the missing control.'),
    source: 'LabourLens deployment runbook, budget controls',
    notes: ['The daily budget is an estimate, not a billing guarantee. Source: docs/deploy.md, environment table and limits.', qa('What would you add before real traffic?', 'A provider-side hard spend cap first, then per-user quotas, a backup procedure and a measured memory profile under load, none of which I have verified.')]
  });

  // ---------- safety ----------
  add({...figSlide('fig-threat-matrix', {title: 'Threat matrix'}), id: 'safety', chapter: 'Safety', layout: 'split', human: 'LabourLens threat suite, 36 handwritten cases',
    bullets: ['Six categories: direct injection, poisoned passage, sensitive data, unsafe tool use, unsupported claims and a failing MCP server.', luna ? `gpt-6-luna passed ${luna.passed} of ${luna.n_scored} with defences and had ${fmt.int(luna.canary_leaks)} canary leaks.` : '', 'Defences did not change the result: the single failure is a poisoned passage.'].filter(Boolean),
    notes: ['Retrieved text is treated as untrusted data; tools are read-only. One run per configuration, handwritten cases, so a pass rate is not a guarantee.', qa('Did the defences work?', 'The suite does not show a defence effect. The same failure appears with and without them, and it is the poisoned passage that T-I06 describes.')]});
  add({...figSlide('fig-e2efix', {title: 'Final-code threat run'}), chapter: 'Safety', layout: 'split', human: 'LabourLens final-code threat run on corpus v3',
    bullets: ['On corpus v3 with the final code, gpt-6-luna passed every case and gpt-5.6-luna failed T-I06.', 'The scorer needs the exact string "3,830 persons" and rejects a caveat that quotes the planted figure. That is a scorer brittleness finding.', 'I did not change the scorer after seeing the run.']});
  {
    const both = el('div', 'deck-two');
    takeAll(c.safety, '.pr-callout').filter(n => /Controls in place|Known gaps/.test(text(n, '.pr-callout-title'))).forEach(n => both.append(n));
    add({
      layout: 'solo', chapter: 'Safety', title: 'Five controls are in place and three gaps are known, including a scanner that missed all 5 paraphrased probes',
      visual: both.children.length ? both : missing('The controls'), source: 'LabourLens threat model and independent AI reviews',
      notes: ['The ingestion scanner is heuristic. In a second blind AI review all five paraphrased malicious probes bypassed it. That is detector-only evidence, with no observed exploit.', 'Quote presence does not show a quote supports the claim, and the MCP input filter missed one paraphrased instruction in the saved transcript.', qa('What is your biggest security gap?', 'The scanner. A model-assisted screen tested on a larger, human-written set is the next step I would take.')]
    });
  }

  // ---------- MCP ----------
  add({...figSlide('fig-mcp', {title: 'MCP trust boundary'}), id: 'mcp', chapter: 'MCP', layout: 'split', human: 'LabourLens MCP server and client design',
    bullets: [`The server exposes ${mx.compared_datasets != null ? '9' : 'nine'} read-only tools, 2 resources and 1 prompt over statistics and the source catalogue. It has no MOM report text.`, 'The client treats the server as untrusted: allow-listed launch, schema checks, deadlines and size limits.', 'The web app does not route through MCP. Direct calls are the default, and MCP is an optional route.'],
    notes: ['Read-only on purpose: a protocol demo should show typed capability discovery, not new risk. Direct calls are faster and MCP adds a failure mode (D-028).', 'Six scripted failure behaviours were observed against a hostile test server: slow server, server dies mid-call, unexpected version, broken schema, oversized result and secrets.', qa('Then why build it?', 'The assessment asks for a working server and client with trust boundaries and a comparison. I measured what MCP costs and kept direct calls as the default.')]});
  add({...figSlide('fig-mcp-latency', {title: 'MCP latency'}), chapter: 'MCP', layout: 'split', human: 'LabourLens MCP demo, saved transcript',
    bullets: [`Connecting once costs ${fmt.num(mx.connection_seconds, 2)} s.`, mx.compared_datasets != null ? `MCP output differed from direct calls on ${fmt.int(mx.different_outputs)} of ${fmt.int(mx.compared_datasets)} datasets.` : '', 'A protocol demo on the cases tried, not an audit.'].filter(Boolean)});

  // ---------- product ----------
  add({
    id: 'product', layout: 'solo', chapter: 'The product', title: 'The workbench shows the evidence behind every answer',
    visual: withSoWhat(rows([
      ['Workbench', 'Ask a question, then read the answer with its status, citations and an evidence drawer with the exact excerpt and source link.'],
      ['Honest states', 'Answered, abstained, needs clarification and refused each look different. A citation turns red when its label has no matching evidence.'],
      ['Live deployment', 'One server in Singapore serves the live app behind access codes. It serves corpus v3 and commit c297146, as reported by the owner.'],
      ['Overview and this deck', 'The overview explores the series. This deck is built from the same report.json.']
    ]), 'A live service needs logging and limits, which is the next slide.'),
    source: 'LabourLens workbench and deployment runbook',
    notes: ['The workbench shows tool calls and outcomes, not hidden model reasoning. Access is gated and the live demo can be switched off.', qa('Can I try it?', 'The live demo needs an access code because each question makes paid model calls. The workbench works in report-only mode without one, with example questions.')]
  });
  add({
    layout: 'solo', chapter: 'The product', title: 'Each run is logged without secrets, and each session is rate limited',
    visual: withSoWhat(rows([
      ['What is logged', 'A record per run with the question outcome, tool calls, cost and timings. Identifiers are hashed and secrets are redacted.'],
      ['What is not', 'Raw addresses, session ids and hidden model reasoning. Full evidence text is omitted by default.'],
      ['Limits', 'Login, session and address rate limits, a body size limit, concurrency limit, a daily budget and a kill switch.'],
      ['Retention', 'A prune command deletes run logs and traces older than a set number of days.']
    ]), 'The logs are how I would debug one bad answer, and how the feedback ratings attach to runs.'),
    source: 'LabourLens audit and logging notes, deployment runbook',
    notes: ['Source: docs/audit-and-logging.md, docs/deploy.md. Feedback attaches only to runs the same session started.', qa('How do you protect user questions?', 'Identifiers are hashed with a salt, secrets are redacted by value and by key shape, and a prune job removes old logs.')]
  });

  // ---------- process ----------
  add({
    id: 'process', layout: 'solo', chapter: 'Working with AI agents', title: 'I ran the work as gates: explore, compare, recommend, approve, implement, verify, document',
    visual: withSoWhat(rows([
      ['Approval gates', 'No new phase or architecture decision without my approval. Agents proposed options with trade-offs, and I chose.'],
      ['Independent reviews', 'Blind AI reviews of the gold labels, the answers and the extracted passages, each with the files it checked.'],
      ['Frozen results', 'Held-out runs were frozen. Gold versions are hashed into every score. Nothing was overwritten.'],
      ['Strict schemas', 'Typed tool arguments and validated answer output, so a malformed result is rejected, not displayed.']
    ]), 'The process caught mistakes, and the next slide lists them.'),
    source: 'LabourLens project instructions and decision log',
    notes: ['This is how I used AI agents as engineers: with a written contract. Decisions and alternatives are in the decision log.', qa('What did you decide and what did the agents propose?', 'I decided scope, sources, label policy, what counts as adopted and the held-out rule. Agents proposed designs, wrote code and drafted gold cases. I reviewed 45 of those cases myself.')]
  });
  add({
    layout: 'solo', chapter: 'Working with AI agents', title: 'I decided the questions; agents drafted the work; review caught four mistakes',
    visual: withSoWhat(rows([
      ['I decided', 'Scope, sources, label policy, the held-out rule, what counts as adopted.'],
      ['Agents proposed or drafted', 'Designs, code, the first gold labels, the pre-review passes.'],
      ['Review caught', 'A stale judge cache, an over-strict calculation scorer, a threat fixture that passed vacuously, and gold edits made after the held-out run, which I disclosed.']
    ]), 'Those are the mistakes worth learning from.'),
    source: 'LabourLens evaluation report and decision log',
    notes: ['The four review catches are in the work log problems list (appendix J). Each was corrected before publishing and the originals are kept where scores moved.', qa('What would an AI-only process have missed?', 'The judge cache keyed by case id survived gold changes, and nobody would have seen it without a rejudge. A human gate and an independent review found it.')]
  });

  // ---------- what went wrong ----------
  {
    const blocks = c.work._blocks;
    const cards = [...(blocks[3]?.querySelectorAll('.pr-limit') || [])];
    const lessons = {'Stale judge cache': 'Key every cache by what could change it.', 'Calculation scorer too strict': 'Test the scorer before trusting the score.', 'Threat fixture passed vacuously under r3': 'A pass needs a check that the test ran.', 'Gold edits after the held-out run': 'Freeze labels before the run, disclose edits after.', 'Extraction defects': 'Audit the data before evaluating on it.', 'T-I06: planted false figure': 'A pass in one run is not stability.'};
    add({
      id: 'wrong', layout: 'solo', chapter: 'What went wrong', title: 'Six things went wrong, and each taught me a rule',
      visual: withSoWhat(rows(cards.map(card => [text(card, '.pr-limit-title'), lessons[text(card, '.pr-limit-title')] || ''])), 'The same honesty applies to the limits of the results, which come next.'),
      source: 'LabourLens evaluation report, experiments log',
      notes: ['Each item has a cause, a fix and a status in appendix J.', qa('What is the mistake you are least comfortable with?', 'The post-run gold edits. I disclosed them and kept the original scores beside the rescored ones, but they are a reason to rely on held-out v2 instead.')]
    });
  }

  // ---------- limits ----------
  add({
    id: 'limits', layout: 'solo', chapter: 'Limits and next steps', title: 'Five limits constrain what these results show',
    visual: rows([
      ['Labels', 'Gold labels are mostly AI drafts: 45 of 268 cases are reviewed by me, and 95 of 125 review cards agreed with an AI suggestion.'],
      ['Held-out sets', 'The 31-case set reuses development evidence. Held-out v2 is independent, but its gain is three cases for one model.'],
      ['Safety', 'T-I06 is one planted case, handled in one run and not the next for one model. The ingestion scanner missed all 5 paraphrased probes.'],
      ['Corpus', 'Registered results ran on corpus v1, not the corpus v3 that the demo serves.'],
      ['Cost and judge', 'Costs are list-price estimates, and the AI judge shares a provider with the answer models.']
    ]),
    source: 'LabourLens README, system card and evaluation report',
    notes: [`All ${[...(c.limits?.querySelectorAll('.pr-limit') || [])].length} recorded limits, with the file behind each, are on appendix slide H. This is the only slide where the limits are stated in full; elsewhere I give each limit once, where it applies.`, qa('What is the biggest limit?', 'That most gold labels are AI drafts. Every accuracy number depends on them, and independent human annotation is the first thing I would add.')]
  });
  {
    const titles = [...(c.next?.querySelectorAll('.pr-next-title') || [])].map(n => n.textContent);
    const nextRows = [['In progress', 'A tool-fix experiment on frozen held-out v2, with its rule stated first. No result yet.'], ...titles.map(t => ['Next', t])];
    add({
      layout: 'solo', chapter: 'Limits and next steps', title: 'Next: finish the tool-fix experiment, then close the evaluation gaps',
      visual: rows(nextRows), source: 'LabourLens evaluation report',
      notes: ['The six next steps each name the gap and the measurement that would close it, in appendix I. None except the tool-fix experiment has started.', qa('If you had one more week?', 'Finish the tool-fix experiment, then add blinded independent review for the draft gold cases.')]
    });
  }

  // ---------- close ----------
  {
    const findingsRows = [
      L ? [`${pct(L.R0['hit@8'])} to ${pct(L.R3['hit@8'])}`, `hit@8 from the hybrid baseline to filter then rerank on ${fmt.int(m.ladder.n_cases)} development questions.`] : null,
      dev.rate != null ? [`${pct(dev.rate)}`, `behaviour accuracy on ${fmt.int(a3.metrics.n_cases)} development cases, which I used to choose the configuration.`] : null,
      v2p ? [`${v2p.better} cases`, `is the held-out v2 gain for gpt-6-luna. The rule is met, the second model shows none, and I do not call it confirmed.`] : null,
      luna ? [`${luna.passed} of ${luna.n_scored}`, 'threat cases passed by gpt-6-luna with defences. T-I06 is not shown stable.'] : null,
      mx.compared_datasets != null ? [`${fmt.int(mx.different_outputs)} of ${fmt.int(mx.compared_datasets)}`, 'datasets whose output differed between MCP and direct calls.'] : null
    ];
    add({
      layout: 'solo', chapter: 'Close', title: 'Five findings, and the one thing I would not claim',
      visual: withSoWhat(rows(findingsRows), 'I would not claim that filtered, reranked retrieval is proven to help. Its development gain is large and its independent gain is small.'),
      source: 'LabourLens report: retrieval, evaluation, safety and MCP results',
      notes: ['The five findings are the numbers I would stand behind, with the caveats that travel with them.', qa('What is the headline?', 'Filtering by period and series before ranking is what moved retrieval. Numbers from code and cited quotes make answers checkable. The agent behaves well on development questions and the independent evidence for the retrieval gain is small. The system is honest about what it cannot yet show.')]
    });
    const date = m.generatedAt ? m.generatedAt.slice(0, 10) : 'an unknown date';
    add({
      layout: 'text', chapter: 'Close', title: 'Sources and provenance',
      bullets: [
        `Report built ${date} from commit ${m.commit ? m.commit.slice(0, 7) : 'unknown'}, ${fmt.int(m.artifactCount)} committed artifacts.`,
        'Numbers not in report.json cite a document. Rebuild the report with: uv run labourlens build-report.',
        'Statistics: Ministry of Manpower and Singapore Department of Statistics via data.gov.sg, Singapore Open Data Licence. MOM reports remain the Ministry\u2019s.',
        'Model prices: OpenAI list prices read on 2026-10-30.'
      ],
      source: 'report.json: generated_at, provenance.commit, provenance.artifacts',
      notes: ['This is the only place the build provenance appears. Each slide source line names the data behind its numbers, and the speaker notes name the file or report field.', 'MOM report text is not shown beyond short excerpts the live agent cites, and no quote in the deck is longer than six words.', 'Fonts: Geist, SIL OFL 1.1. Slides: reveal.js 6.0.2, MIT. Icons: Phosphor, MIT.']
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
    const pipeline = take(c.scope, '.pr-pipeline'), outOfScope = take(c.scope, '.pr-callout'), families = fig('fig-families');
    const quality = fig('fig-quality'), warnings = take(c.data, '.pr-warnings');
    const ratio = fig('fig-vacancy-ratio'), vacancies = fig('fig-vacancies');
    const findingsBlock = take(c.data, '.pr-find-block'), atlas = take(c.data, '.pr-atlas');
    add({
      chapter: 'Appendix', layout: 'scroll', title: 'B. Scope and data reference',
      panel: [
        group(heading('How an answer is made'), pipeline, outOfScope), group(heading('Question families'), families),
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
    const rankShift = fig('fig-rank-shift'), methods = fig('fig-methods'), emb = fig('fig-embeddings'), abl = fig('fig-ablation'), hint = fig('fig-hint');
    const limits = takeAll(c.retrieval, '.pr-callout');
    add({
      chapter: 'Appendix', layout: 'scroll', title: 'C. Retrieval reference',
      panel: [group(heading('Early comparisons that chose the hybrid baseline'), methods, emb), group(heading('BM25 settings and period hints'), abl, hint), group(heading('Rank of the first relevant chunk'), rankShift), ...limits],
      source: 'docs/evaluation-report.md, Expanded retrieval study; docs/experiments/m6-retrieval-improvements.md',
      notes: ['The early comparisons are noisy: one case is about 4.2 points. Hybrid was chosen from them as the baseline, not proved best.']
    });
  });

  appendix('D', 'Agent reference', () => {
    const calls = fig('fig-calls'), errors = fig('fig-tools');
    add({
      chapter: 'Appendix', layout: 'scroll', title: 'D. Agent reference',
      panel: [group(heading(figTitle(calls) || 'Recorded tool calls'), calls), group(heading(figTitle(errors) || 'Tool errors'), errors)],
      source: 'report.json: agent.trace; docs/architecture.md, section 4',
      notes: ['Recorded runs against the set limits, and the operational failures and repaired answers.']
    });
  });

  appendix('E', 'Evaluation reference', () => {
    const items = ['fig-latency', 'fig-cost', 'fig-models', 'fig-oracle', 'fig-errors', 'fig-dev-held', 'fig-strata'].map(fig);
    const x2 = [...(c.evaluation?.querySelectorAll('.pr-block') || [])].find(b => /X2 regression/.test(text(b, '.pr-block-title')));
    add({
      chapter: 'Appendix', layout: 'scroll', title: 'E. Evaluation reference',
      panel: [group(heading('Response time and cost'), items[0], items[1]), group(heading('Model comparison and oracle evidence'), items[2], items[3]), group(heading('Error counts'), items[4]), group(heading('Development against held-out, and by family'), items[5], items[6]), ...takeAll(c.evaluation, '.pr-details').map(d => group(d))],
      source: 'report.json: evaluation.rows, answers.rows, evaluation.errors',
      notes: ['Latency and cost, the model comparison on answer-only cases with oracle evidence, and the pooled error counts. The X2 regression table is on slide A.']
    });
    void x2;
  });

  appendix('F', 'Safety reference', () => {
    const ci = fig('fig-threat-ci'), canary = take(c.safety, '.pr-canary'), post = fig('fig-postfix');
    const callouts = takeAll(c.safety, '.pr-callout');
    add({
      chapter: 'Appendix', layout: 'scroll', title: 'F. Safety reference',
      panel: [group(heading('Pass rate by configuration'), ci, canary), group(heading('First post-fix run'), post), ...callouts],
      source: 'report.json: security; experiments/threats/*/SUMMARY.md; docs/experiments/m7-t-i06-crosscheck.md',
      notes: ['Intervals and canary results for the threat suite, the first post-fix run with its two scorers, and what the failing final-code run shows.']
    });
  });

  appendix('G', 'MCP reference', () => {
    const catalogue = take(c.mcp, '.pr-mcp-cat'), checks = take(c.mcp, '.pr-checks'), http = take(c.mcp, '.pr-http');
    add({
      chapter: 'Appendix', layout: 'scroll', title: 'G. MCP reference',
      panel: [group(heading('Parity of direct and MCP results'), fig('fig-mcp-parity')), group(heading('Tools, resources and prompt'), catalogue), group(heading(`${(mcp.checks || []).length} failure behaviours observed`), checks), group(http), ...takeAll(c.mcp, '.pr-callout')],
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
