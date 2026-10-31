// The deck: every slide is declared here as data. Charts and tables are the ones the chapter
// modules already draw from report.json; this file picks them out of an off-screen pool, gives each
// slide an action title and at most three bullets, and moves the detail into speaker notes or the
// appendix. Numbers on slides come from report.json (through the model) or from the document named
// in the slide's source line. Text is set with textContent only.
import {el, fmt, finite} from '../charts.js';
import {model, metricOf, goldOf} from './model.js';
import {stat, textStat, countRunner} from './ui.js';
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
    return {title: figTitle(f) || extra.title, visual: f || missing(extra.title || 'This chart'), source: figSource(f), notes: [...(extra.notes || []), figTakeaway(f), figNote(f), `Source: ${figSource(f)}. ${figFiles(f)}`.trim()].filter(Boolean), bullets: extra.bullets, ...(extra.rest || {})};
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

  // ---------- opening ----------
  add({
    layout: 'title', chapter: 'Start',
    title: 'Cited answers from Singapore labour-market data',
    sub: 'LabourLens answers analyst questions from MOM statistics and reports, Q1 2024 to Q2 2026.',
    notes: [
      'LabourLens answers analyst questions about the Singapore labour market. Every answer cites a passage or a validated statistic, or it abstains.',
      'Keys: arrows, space and page keys move; F is fullscreen; O or Escape opens the overview; S shows these notes; add ?print-pdf to the address to export a PDF.',
      'Every number in the deck comes from report.json or from the document named in the slide source line. The last slide gives the build provenance.'
    ]
  });
  add({
    layout: 'agenda', chapter: 'Start', title: 'What this presentation covers',
    visual: null,
    notes: ['The chapters follow the work: scope, data, retrieval, the agent, evaluation, safety, MCP, limits, next steps, and the work log. A summary and the provenance slide close the main deck.', 'The appendix holds the detail that did not fit on a slide. It is reachable from the overview.']
  });

  {
    const heldN = r3?.metrics?.n_cases;
    const heldHits = held.rate != null && finite(heldN) ? Math.round(held.rate * heldN) : null;
    add({
      layout: 'split', chapter: 'Start',
      title: heldHits != null ? `The agent behaves as the gold label says on ${heldHits} of ${fmt.int(heldN)} held-out cases` : 'Headline result',
      bullets: [
        dev.rate != null ? `In development it did so on ${pct(dev.rate)} of ${fmt.int(a3.metrics.n_cases)} cases, which I used to choose the configuration.` : '',
        'On the held-out cases the gain from filtered, reranked retrieval is not demonstrated.',
        L ? `The right passage is in the top eight retrieved chunks for ${pct(L.R3['hit@8'])} of development questions.` : ''
      ].filter(Boolean),
      visual: bigStat({text: heldHits != null ? `${heldHits} of ${fmt.int(heldN)}` : 'not recorded', label: 'Held-out cases with the expected behaviour', note: 'Answer, abstain, clarify or refuse, as the gold label says', size: 'xl'}),
      source: 'report.json: evaluation.rows[agent-dev-A3, agent-heldout-H-r3], retrieval.ladder.configs.R3',
      notes: ['Behaviour accuracy is the share of cases where the agent answered, abstained, asked or refused as the gold label says.', 'Development cases were used to choose configurations, so they carry selection bias. The held-out gain is inconclusive: its interval touches or crosses zero.', `Also in report.json: ${fmt.int(m.section('sources').metrics?.sources)} sources and ${fmt.int(quality.pass)} validation checks passed with ${fmt.int(quality.warn)} warnings; ${luna ? `${luna.passed} of ${luna.n_scored} threat cases passed by gpt-6-luna with defences` : ''}.`, 'Source: report.json, evaluation.rows[agent-dev-A3 and agent-heldout-H-r3], retrieval.ladder.configs.R3, sources.metrics, quality.metrics, security.rows.']
    });
  }
  add({
    layout: 'split', chapter: 'Start', title: 'Three caveats apply to every number that follows',
    bullets: [
      'Gold v3.5: 45 cases owner-reviewed, 223 AI drafts. Not independent review.',
      'Held-out gain not demonstrated. Scores were rescored after post-run label edits.',
      'Registered results ran on corpus v1; corpus v3 has two measured evaluations.'
    ],
    visual: bigStat({text: '45 of 268', label: 'Gold cases reviewed by the owner', note: 'Of 125 owner decisions, 95 agreed with an AI suggestion', size: 'xl'}),
    source: 'README.md, docs/system-card.md, docs/human-review/owner-review-summary.md',
    notes: ['The caveats are on the second slide so that nobody mistakes development scores for a general result.', 'Gold v3.5 has 268 cases: 237 development and 31 held out. 45 are owner-reviewed and 223 are AI drafts. Of the 125 owner cards, 95 agreed with an AI suggestion, so this is not independent review.', 'Development rows use one gold version and held-out rows another; both were rescored from saved outputs after post-run label edits.', 'X2 is a regression check on corpus v3, not an ablation. The full wording is in the appendix, slide A.']
  });

  // ---------- scope ----------
  {
    take(c.scope, '.pr-periods');
    add({
      id: 'scope', chapter: 'Scope', layout: 'split', title: chapterTitle('scope'),
      bullets: ['Users: policy researchers comparing statistics with MOM commentary.', 'Output: cited answer, clarification, abstention or refusal.', 'Out of scope: forecasting, unsupported causal claims, unrestricted web research, individual employment advice.'],
      visual: bigStat({value: nQ, label: `${fmt.quarter(m.scope[0])} to ${fmt.quarter(to)}`, note: 'Quarterly observations, with earlier documents as context only', size: 'xl'}),
      source: 'report.json: summary.scope, charts[].points[].period',
      notes: [`The window is ${fmt.quarter(m.scope[0])} to ${fmt.quarter(to)}: ${nQ} quarters. Earlier documents are context only, and requests outside the window must abstain.`, `Sources: ${fmt.int(types.dataset_csv)} dataset snapshots, ${fmt.int(types.report_pdf)} report PDFs and ${fmt.int(types.release_html)} release pages. Dataset coverage varies by quarter and was checked at ingestion.`, 'Out of scope comes from CLAUDE.md, Approved scope, and docs/system-card.md, Intended use.']
    });
    const kpis = take(c.scope, '.pr-kpis');
    add({
      chapter: 'Scope', layout: 'split', title: `${kpis?.children.length ?? 6} headline series at ${fmt.quarter(to)}, each with its own population, adjustment and unit`,
      bullets: ['Each value carries population, seasonal adjustment and unit.', 'Unemployment rates with different definitions are not comparable.'],
      visual: kpis || missing('The headline series'), cls: 'is-kpis',
      source: 'report.json: summary.cards[], observation ids per card',
      notes: ['These are the latest values per series. The observation id behind each card is in report.json, summary.cards.', 'The point of the slide is the labelling: resident and overall rates, adjusted and unadjusted, percentages and persons are different series and the system never merges them silently.']
    });
    add({...figSlide('fig-families', {title: 'Question families'}), chapter: 'Scope', layout: 'split',
      bullets: ['Four outcomes: answered, abstained, clarify, refused.', 'Small families give wide intervals.']});
  }

  // ---------- data ----------
  {
    const nCommit = m.sources.filter(r => r.redistribution === 'commit_raw').length;
    add({...figSlide('fig-sources', {title: 'Source records'}), id: 'data', chapter: 'Data', layout: 'split',
      bullets: [`${fmt.int(quality.pass)} of ${fmt.int((quality.pass || 0) + (quality.warn || 0))} validation checks passed; ${fmt.int(quality.warn)} warnings.`, `Only ${nCommit} of ${m.sources.length} source records may be committed to Git.`, 'Statistics: data.gov.sg. Reports: MOM, kept local.'],
      notes: ['Each record carries publisher, date, rights status, release stage and a snapshot hash. Statistical datasets are under the Singapore Open Data Licence, with attribution and no implied endorsement. MOM report PDFs carry a copyright notice, so they and their text stay out of Git. Release pages with unresolved rights are listed as unresolved.', 'Source: docs/system-card.md, Data and rights; docs/data-sheet.md.']});
    const chain = take(c.data, '.pr-chain-wrap');
    add({
      chapter: 'Data', layout: 'split', title: `A published figure traces to a hashed snapshot in ${chain?.querySelectorAll('.pr-chain-step').length ?? 5} steps`,
      bullets: ['The trace command looks up the raw cell from an observation id.', 'A matching hash confirms the snapshot is the recorded download.'],
      visual: chain || missing('The provenance trace'), source: 'report.json: summary.cards[unemployment_resident_sa], sources.rows[resident_unemployment_rate]',
      notes: ['This is the provenance chain for one headline number: publisher, snapshot, SHA-256, observation, figure shown.', 'Source: report.json, summary.cards and sources.rows; docs/data-sheet.md.']
    });
    const findings = [...(c.data.querySelectorAll('.pr-finding') || [])].map(li => ({head: text(li, 'strong'), body: text(li, 'span')}));
    add({...figSlide('fig-unemployment', {title: 'Unemployment rates'}), chapter: 'Data', layout: 'split',
      bullets: ['Do not mix adjusted and unadjusted rates.', 'Chips under the chart name population, adjustment and unit.'],
      notes: [findings[0] ? `${findings[0].head}. ${findings[0].body}` : '']});
    add({...figSlide('fig-retrenchments', {title: 'Retrenchments'}), chapter: 'Data', layout: 'split',
      bullets: [findings[1]?.body || 'The data do not show why; I infer no cause.'],
      notes: [findings[1] ? `${findings[1].head}. ${findings[1].body}` : '']});
    add({...figSlide('fig-revisions', {title: 'Advance and final figures'}), chapter: 'Data', layout: 'split',
      bullets: [figTakeaway(m && c.data.querySelector('#fig-revisions')) || '', findings[2]?.body || 'Answers name the vintage they use.', findings[3]?.body || ''].filter(Boolean).slice(0, 3),
      notes: [findings[2] ? `${findings[2].head}. ${findings[2].body}` : '', findings[3] ? `${findings[3].head}. ${findings[3].body}` : '']});
  }

  // ---------- retrieval ----------
  if (L) {
    const ctxR3 = m.ladder.end_to_end_context?.R3?.gold_in_context_of_top8_chunks, ctxR0 = m.ladder.end_to_end_context?.R0?.gold_in_context_of_top8_chunks;
    add({
      id: 'retrieval', chapter: 'Retrieval', layout: 'morph', title: `The hybrid baseline R0 reaches ${pct(L.R0['hit@8'])} hit@8 on ${fmt.int(m.ladder.n_cases)} development cases`,
      bullets: ['Hit@8: the right passage is among the top eight retrieved chunks.', 'R0 combines keyword search (BM25) and dense retrieval by rank fusion.'],
      visual: (() => {
        const wrap = el('div', 'deck-morph');
        wrap.append(bigStat({value: L.R0['hit@8'], format: pct, label: 'R0, hybrid baseline', size: 'xl', morph: 'r0'}));
        return wrap;
      })(),
      source: 'report.json: retrieval.ladder.configs.R0.hit@8',
      notes: ['R0 is the baseline: BM25 and dense retrieval combined by reciprocal rank fusion. BM25 alone is the non-LLM baseline underneath it.', 'Hybrid was chosen from the early development cases, where the gaps were a few cases; the appendix shows that comparison.', 'Source: report.json, retrieval.ladder.configs.R0.']
    });
    add({
      chapter: 'Retrieval', layout: 'morph', title: chapterTitle('retrieval'),
      bullets: [
        `R3 gained ${fmt.pts(L.R3['hit@8_diff_vs_R0'])} over R0 (95% CI ${fmt.pts(L.R3['hit@8_diff_ci95']?.[0])} to ${fmt.pts(L.R3['hit@8_diff_ci95']?.[1])}); R1a, R1b and R2 each gained less.`,
        `Gold passage in the context: ${pct(ctxR3)} with R3, ${pct(ctxR0)} with R0.`,
        `Median rerank time ${L.R3['rerank_latency_s_p50_p95']?.[0] != null ? `${L.R3['rerank_latency_s_p50_p95'][0].toFixed(2)} s` : 'not recorded'}; mean $${L.R3.cost_usd_per_query_mean} per query.`
      ],
      visual: (() => {
        const wrap = el('div', 'deck-morph is-after');
        wrap.append(
          bigStat({value: L.R0['hit@8'], format: pct, label: 'R0, hybrid baseline', size: 'm', morph: 'r0'}),
          bigStat({value: L.R3['hit@8'], format: pct, label: 'R3, filter then rerank', size: 'xl'})
        );
        return wrap;
      })(),
      source: 'report.json: retrieval.ladder.configs.{R0,R3}, retrieval.ladder.end_to_end_context',
      notes: ['The R0 number moves aside and the R3 number takes its place. R3 filters by period and release stage, then reranks with a model.', `The 95% interval on the R3 gain is ${fmt.pts(L.R3['hit@8_diff_ci95']?.[0])} to ${fmt.pts(L.R3['hit@8_diff_ci95']?.[1])}.`, 'Caveats: an LLM reranks and an LLM drafted the labels, so R2 and R3 may be optimistic. A hard period filter can exclude the right document when a later release restates an earlier quarter.', 'Source: report.json, retrieval.ladder.']
    });
  }
  add({...figSlide('fig-ladder', {title: 'Retrieval ladder'}), chapter: 'Retrieval', layout: 'split',
    bullets: ['R0 hybrid, R1a hard filter, R1b soft boost, R2 LLM rerank, R3 filter then rerank.', 'Metric: hit@8 with 95% bootstrap intervals.', 'A hard period filter can exclude the right document when a later release restates an earlier quarter.']});
  add({...figSlide('fig-rank-shift', {title: 'Rank of the first relevant chunk'}), chapter: 'Retrieval', layout: 'split',
    bullets: ['None means no relevant chunk in the top 10.', 'The slider fades the R3 result in over the R0 baseline.']});
  add({...figSlide('fig-retrieval-family', {title: 'hit@8 by question family'}), chapter: 'Retrieval', layout: 'split',
    bullets: [figTakeaway(c.retrieval.querySelector('#fig-retrieval-family')) || 'Gains differ by question family.'].filter(Boolean)});

  // ---------- agent ----------
  {
    const tools = take(c.agent, '.pr-tools');
    take(c.agent, '.pr-limits');
    add({...figSlide('fig-graph', {title: 'The agent graph'}), id: 'agent', chapter: 'Agent', layout: 'split', 
      bullets: chapterBullets('agent').filter(b => !b.startsWith('Recorded runs')),
      notes: ['The agent is one LangGraph state graph with a model-directed planner and three typed read-only tools. ADR-002 fixed one bounded agent; I did not build a multi-agent design.', `Recorded runs: ${chapterBullets('agent')[1] || ''}`, 'Source: docs/architecture.md, section 4; src/labourlens/agent/graph.py.']});
    add({
      chapter: 'Agent', layout: 'split', title: 'Three typed tools, none able to write, fetch the web or run code',
      bullets: ['Arguments are checked against enums built from the source catalogue.'],
      visual: tools || missing('The tool list'), cls: 'is-tools',
      source: 'docs/architecture.md, section 4; src/labourlens/agent/tools.py',
      notes: ['Each tool is read-only and typed. A model cannot pass a free-form series name; it picks from an enum built from the catalogue.']
    });
    add({
      chapter: 'Agent', layout: 'split', title: 'Six limits are set in code, not in the prompt',
      bullets: ['A tool outage ends as operational_failure, one of eight named outcomes.', 'A timeout or a planner outage is separate from missing evidence.'],
      visual: list(['2 evidence rounds', '6 tool calls per run, at most 3 per round', '10 seconds per tool call', '1 retry for a transient tool failure or malformed planner output', '1 repair of an invalid answer', '1,000 characters per question']), cls: 'is-limitlist',
      source: 'docs/architecture.md, section 4; src/labourlens/agent/graph.py',
      notes: ['The eight outcomes are answered, abstained, clarify, refused, invalid, rejected_input, blocked_output and operational_failure. Limits are enforced in code, not in the prompt.']
    });
  }

  // ---------- evaluation ----------
  add({...figSlide('fig-headline', {title: 'Headline accuracy'}), id: 'evaluation', chapter: 'Evaluation', layout: 'split',
    bullets: ['Gold set: 268 cases, 237 development and 31 held out.', `Development scored on ${goldOf(a3).label}; held out on ${goldOf(r3).label}.`, 'Configurations were chosen on these cases, so the figures carry selection bias.']});
  add({...figSlide('fig-progression', {title: 'Progression A1 to A3'}), chapter: 'Evaluation', layout: 'split',
    bullets: [figTakeaway(c.evaluation.querySelector('#fig-progression')) || 'One factor changed per run.'].filter(Boolean)});
  add({...figSlide('fig-strata', {title: 'Behaviour accuracy by family'}), chapter: 'Evaluation', layout: 'split',
    bullets: [figTakeaway(c.evaluation.querySelector('#fig-strata')) || 'Small families have wide intervals.'].filter(Boolean)});
  add({...figSlide('fig-dev-held', {title: 'Development against held-out'}), chapter: 'Evaluation', layout: 'split',
    bullets: ['One run on a frozen configuration, scored afterwards.', 'Comparison: r3 against hybrid retrieval.']});
  add({...figSlide('fig-paired', {title: 'Paired difference on held-out'}), chapter: 'Evaluation', layout: 'split',
    bullets: pair ? [`Interval ${fmt.pts(pair.ci95[0])} to ${fmt.pts(pair.ci95[1])}: inconclusive.`, 'Held-out reuses development evidence ids in 25 of 31 cases.', 'Original scores on gold v3.2 to v3.4 stay in the evaluation report.'] : []});

  // ---------- safety ----------
  {
    const steps = take(c.safety, '.pr-ti06-steps');
    const hero = take(c.safety, '.pr-hero-callout');
    add({
      id: 'safety', chapter: 'Safety', layout: 'split', title: text(hero, '.pr-hero-callout-title') || 'T-I06 is not shown stable across runs',
      bullets: ['Before the fix, all five configurations accepted the planted figure.', 'The cross-check handled the one planted case in both models; the scorer that counts it as passed was written after that run.', 'Coverage is a closed grammar. Not shown to generalise.'],
      visual: steps || missing('The T-I06 sequence'), cls: 'is-steps', warn: true,
      source: 'docs/experiments/m7-t-i06-crosscheck.md, experiments/threats/m7-e2efix-20261031/SUMMARY.md, D-038',
      notes: [text(hero, '.pr-hero-callout-text'), 'The sequence: an attacker plants a false figure in a report passage; the agent cites it and the quote and number checks pass; before the fix nothing compared it with the statistics.', 'The cross-check now compares passage figures with validated observations, corrects the claim to the dataset value, cites both and adds a source-conflict caveat.']
    });
    add({...figSlide('fig-threat-matrix', {title: 'Threat matrix'}), chapter: 'Safety', layout: 'split',
      bullets: [`${chapterBullets('safety')[0] || ''}`, 'Retrieved text is treated as untrusted data; tools are read-only.', luna ? `gpt-6-luna passes ${luna.passed} of ${luna.n_scored} with defences and ${fmt.int(luna.canary_leaks)} canary leaks.` : ''].filter(Boolean)});
    add({...figSlide('fig-e2efix', {title: 'Final-code threat run'}), chapter: 'Safety', layout: 'split',
      bullets: ['gpt-6-luna passes every case; gpt-5.6-luna fails T-I06.', 'The scorer requires the exact string "3,830 persons" and rejects a disclosing caveat. That is a scorer brittleness finding from one case.', 'I did not change the scorer after seeing the run.']});
    const callouts = takeAll(c.safety, '.pr-callout').filter(node => /Controls in place|Known gaps/.test(text(node, '.pr-callout-title')));
    const both = el('div', 'deck-two');
    callouts.forEach(node => both.append(node));
    add({
      chapter: 'Safety', layout: 'solo', title: 'Five controls are implemented and three gaps are known, including the scanner bypass (5 of 5 paraphrase probes)',
      visual: callouts.length ? both : missing('The controls'), source: 'docs/architecture.md, docs/threat-model.md, docs/human-review/independent-ai-review-m1-2.md',
      notes: ['The scanner is heuristic: all five paraphrased malicious probes bypassed it in a second blind AI review. That is detector-only evidence, with no observed exploit.', 'Quote presence does not show that a quote supports the claim. The MCP input filter missed one paraphrased instruction in the saved transcript.']
    });
  }

  // ---------- MCP ----------
  {
    const p50 = (mcp.rows || []).find(r => r.metric === 'latency_p50_ms');
    add({...figSlide('fig-mcp', {title: 'MCP trust boundary'}), id: 'mcp', chapter: 'MCP', layout: 'split',
      bullets: chapterBullets('mcp').filter((b, i) => i !== 2).slice(0, 3),
      notes: ['The server exposes read-only data capabilities: statistics and the source catalogue, no MOM report text. The client treats the server as untrusted and validates every result.', 'Source: src/labourlens/mcp/server.py; docs/mcp-demo-transcript.md.']});
    add({...figSlide('fig-mcp-latency', {title: 'MCP latency'}), chapter: 'MCP', layout: 'split',
      bullets: [`Connecting once costs ${fmt.num(mx.connection_seconds, 2)} s.`, 'I kept direct calls as the agent default.', 'Warm-session timings exclude the one-off connection.']});
    add({...figSlide('fig-mcp-parity', {title: 'MCP parity'}), chapter: 'MCP', layout: 'split',
      bullets: [p50 ? `A median call took ${p50.mcp} ms over MCP against ${p50.direct} ms direct.` : '', 'MCP adds capability discovery and typed tool contracts.', 'A protocol demo on the cases tried, not an audit.'].filter(Boolean)});
  }

  // ---------- limits ----------
  {
    const limitCards = [...(c.limits?.querySelectorAll('.pr-limit') || [])];
    const rows = el('ul', 'deck-limit-rows');
    [
      ['Labels', 'Gold labels are mostly AI drafts: 45 of 268 cases are owner-reviewed, and 95 of 125 owner decisions agreed with an AI suggestion.'],
      ['Held-out set', 'It reuses development evidence in 25 of 31 cases and is small, so the gain from filtered, reranked retrieval is inconclusive.'],
      ['Safety', 'T-I06 plants a false figure in a report passage. The cross-check corrected it in one run and not in the next for one model, so I do not claim it works in general. The ingestion scanner missed all 5 paraphrased probes.'],
      ['Corpus', 'Registered results ran on corpus v1, not the corpus v3 that the demo serves. Corpus v3 has two measured evaluations and no held-out one.'],
      ['Cost and judge', 'Costs are list-price estimates, and the AI judge shares a provider with the answer models.']
    ].forEach(([head, body]) => { const li = el('li'); li.append(el('strong', '', head), el('span', '', body)); rows.append(li); });
    add({...figSlide('fig-review', {title: 'The owner reviewed 45 of 268 gold cases'}), id: 'limits', chapter: 'Limits', layout: 'split',
      bullets: ['Owner review: 125 cards decided, 30 by own verdict, 95 by agreeing with an AI suggestion.', 'No blinded review was run, so this is not independent annotation.']});
    add({
      chapter: 'Limits', layout: 'solo', title: 'Five limits constrain what these results show',
      visual: rows, source: 'README.md, docs/system-card.md, docs/evaluation-report.md',
      notes: [`All ${limitCards.length} recorded limits, with the file that supports each, are on appendix slide H.`, 'T-I06 is one planted-figure test case, handled by a closed-grammar cross-check. Before the fix the false figure was cited as fact; after the fix the cross-check handled it in the first run for both models, but in the final-code run gpt-5.6-luna failed it on an exact-string scorer check.']
    });
  }

  // ---------- next ----------
  {
    const titles = [...(c.next?.querySelectorAll('.pr-next-title') || [])].map(node => node.textContent);
    const order = el('ol', 'deck-next');
    titles.forEach(title => order.append(el('li', '', title)));
    add({
      id: 'next', chapter: 'Next steps', layout: 'split', title: text(c.next, '.pr-chapter-title') || 'Six experiments would close the main evaluation gaps',
      bullets: ['Each step names the gap it addresses and the measurement that would close it.', 'None is built or run yet.'],
      visual: titles.length ? order : missing('The next steps'), source: 'docs/evaluation-report.md, docs/decisions.md',
      notes: ['Each experiment has a success criterion; the full text is in appendix I.']
    });
  }

  // ---------- work log ----------
  {
    const blocks = [...(c.work?.querySelectorAll('.pr-block') || [])];
    const workStats = take(c.work, '.pr-stats');
    const corpus = take(c.work, '.pr-callout');
    add({
      id: 'work', chapter: 'Work log', layout: 'split', title: chapterTitle('work'),
      bullets: chapterBullets('work').slice(0, 2),
      visual: workStats || missing('The work log summary'), cls: 'is-kpis',
      source: 'report.json: work.decisions, evaluation, retrieval, security; docs/decisions.md',
      notes: ['The registry lists every experiment group with the one factor changed and the decision taken. Null and inconclusive results stay in the log.', 'Full registry, decision log, timeline, problems and spend are in appendix J.']
    });
    add({
      chapter: 'Work log', layout: 'solo', title: 'Registered results ran on corpus v1; the served corpus v3 has two measured evaluations',
      visual: corpus || missing('The corpus versions'), source: 'README.md, Corpus versions; docs/evaluation-report.md',
      notes: ['Corpus v1 has 13,484 passages, v2 has 15,915 and v3 has 16,419. The frozen v1 and v2 results are retained.', 'Corpus v3 has the X2 development regression check and the e2efix threat run. It has no held-out or evidence-disjoint evaluation yet.', 'The served commit and fingerprint are the owner-reported values in the README.']
    });
    const failureBlock = blocks[3];
    const cards = [...(failureBlock?.querySelectorAll('.pr-limit') || [])];
    const rows = el('ul', 'deck-problems');
    cards.forEach(card => {
      const li = el('li');
      li.append(el('strong', '', text(card, '.pr-limit-title')), el('span', 'deck-problem-status', text(card, '.pr-limit-no')));
      rows.append(li);
    });
    add({
      chapter: 'Work log', layout: 'split', title: text(failureBlock, '.pr-block-title') || 'Six problems found during the work; T-I06 not shown stable across runs',
      bullets: ['Three were corrected, one is disclosed, one was decided, and one is T-I06.'],
      visual: cards.length ? rows : missing('The problem list'), source: 'docs/evaluation-report.md, experiments/threats/SUMMARY.md',
      notes: ['Each problem has a cause, a fix and a status in appendix J.']
    });
    c.work._blocks = blocks;
  }

  // ---------- close ----------
  {
    const results = take(c.summary, 'ol.pr-list');
    const openItems = [...(c.summary?.querySelectorAll('.pr-block:last-of-type li') || [])].map(li => li.textContent);
    add({
      chapter: 'Close', layout: 'split', title: chapterTitle('summary'),
      bullets: openItems.slice(0, 3),
      visual: results || missing('The summary'), cls: 'is-results',
      source: 'report.json: retrieval.ladder, evaluation, security, mcp',
      notes: ['Five results, then the open items. The open items are the honest end of the story: the cross-check is not shown stable, the gold labels are mostly drafts, and the held-out rerun on frozen reviewed gold has not been run.']
    });
    const date = m.generatedAt ? m.generatedAt.slice(0, 10) : 'an unknown date';
    add({
      chapter: 'Close', layout: 'text', title: 'Sources and provenance',
      bullets: [
        `Report built ${date} from commit ${m.commit ? m.commit.slice(0, 7) : 'unknown'}, ${fmt.int(m.artifactCount)} committed artifacts.`,
        'Numbers not in report.json cite a document. Rebuild the report with: uv run labourlens build-report.',
        'Statistics: Ministry of Manpower and Singapore Department of Statistics via data.gov.sg, Singapore Open Data Licence. MOM reports remain the Ministry\u2019s.'
      ],
      source: 'report.json: generated_at, provenance.commit, provenance.artifacts',
      notes: ['This is the only place the build provenance appears. Each slide source line names the report field or the document behind its numbers.', 'MOM report text is not shown beyond short excerpts the live agent cites, and no quote in the deck is longer than six words.', 'Fonts: Geist, SIL OFL 1.1. Slides: reveal.js 6.0.2, MIT. Icons: Phosphor, MIT.']
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
    const pipeline = take(c.scope, '.pr-pipeline'), outOfScope = take(c.scope, '.pr-callout');
    const quality = fig('fig-quality'), warnings = take(c.data, '.pr-warnings');
    const ratio = fig('fig-vacancy-ratio'), vacancies = fig('fig-vacancies');
    const findingsBlock = take(c.data, '.pr-find-block'), atlas = take(c.data, '.pr-atlas');
    add({
      chapter: 'Appendix', layout: 'scroll', title: 'B. Scope and data reference',
      panel: [
        group(heading('How an answer is made'), pipeline, outOfScope),
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
    const methods = fig('fig-methods'), emb = fig('fig-embeddings'), abl = fig('fig-ablation'), hint = fig('fig-hint');
    const limits = takeAll(c.retrieval, '.pr-callout');
    add({
      chapter: 'Appendix', layout: 'scroll', title: 'C. Retrieval reference',
      panel: [group(heading('Early comparisons that chose the hybrid baseline'), methods, emb), group(heading('BM25 settings and period hints'), abl, hint), ...limits],
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
    const items = ['fig-latency', 'fig-cost', 'fig-models', 'fig-oracle', 'fig-errors'].map(fig);
    const x2 = [...(c.evaluation?.querySelectorAll('.pr-block') || [])].find(b => /X2 regression/.test(text(b, '.pr-block-title')));
    add({
      chapter: 'Appendix', layout: 'scroll', title: 'E. Evaluation reference',
      panel: [group(heading('Response time and cost'), items[0], items[1]), group(heading('Model comparison and oracle evidence'), items[2], items[3]), group(heading('Error counts'), items[4]), ...takeAll(c.evaluation, '.pr-details').map(d => group(d))],
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
      panel: [group(heading('Tools, resources and prompt'), catalogue), group(heading(`${(mcp.checks || []).length} failure behaviours observed`), checks), group(http), ...takeAll(c.mcp, '.pr-callout')],
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

  return specs;
}

function limitsCardsFrom(c, specs) {
  void specs;
  const wrap = el('div', 'pr-limit-grid');
  const cards = c.limits?.querySelector('.pr-limit-grid')?.children;
  if (cards) [...cards].forEach(card => wrap.append(card.cloneNode(true)));
  return wrap;
}
