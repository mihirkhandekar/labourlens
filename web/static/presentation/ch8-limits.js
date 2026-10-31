import {el, figure, shareBars, fmt} from '../charts.js';
import {chapter, section, callout, evi, list, details} from './ui.js';
import {goldOf, metricOf} from './model.js';

// Review counts come from docs/human-review/owner-review-summary.md, README.md and docs/system-card.md.
// They are not in report.json; the evidence toggle names the files.
function reviewFigure() {
  const rows = [
    {label: 'Owner decisions, 125 cards', sub: 'per card, not independent', segments: [
      {key: 'own', label: 'Own verdict', value: 30, cls: 'c1'}, {key: 'earlier', label: 'Agreed with earlier AI passes', value: 67, cls: 'c6'}, {key: 'tie', label: 'Agreed with the 3-pass tie-break', value: 28, cls: 'c5'}]},
    {label: 'Answer verdicts, 40 outputs', sub: 'owner', segments: [
      {key: 'c', label: 'Correct', value: 25, cls: 'c1'}, {key: 'p', label: 'Partly correct', value: 6, cls: 'c2'}, {key: 'i', label: 'Incorrect', value: 9, cls: 'c4'}]},
    {label: 'Gold cases, 268', sub: 'owner review of label, evidence, facts', segments: [
      {key: 'ok', label: 'Reviewed, no change', value: 43, cls: 'c1'}, {key: 'dis', label: 'Reviewed, label changed', value: 2, cls: 'c2'}, {key: 'dr', label: 'Still AI drafts', value: 223, cls: 'c6'}]},
    {label: 'Source cards, 30', sub: 'owner', segments: [
      {key: 'm', label: 'Match', value: 19, cls: 'c1'}, {key: 'mi', label: 'Minor difference', value: 11, cls: 'c2'}]},
    {label: 'Blind AI review, 40 outputs', sub: 'AI judgment, failure-enriched sample', segments: [
      {key: 'ac', label: 'AI: correct', value: 28, cls: 'c1'}, {key: 'ap', label: 'AI: partly correct', value: 6, cls: 'c2'}, {key: 'ai', label: 'AI: incorrect', value: 6, cls: 'c4'}]}
  ];
  return figure({
    id: 'fig-review', title: 'The owner reviewed 45 of 268 gold cases; 223 remain AI drafts', wide: true,
    takeaway: 'Of 125 owner decisions, 30 are own verdicts and 95 agree with an AI suggestion. That is not independent annotation.',
    summary: rows.map(r => `${r.label}: ${r.segments.map(s => `${s.label} ${s.value}`).join(', ')}`).join('. '),
    source: {data: 'docs/human-review/owner-review-summary.md · README.md · docs/system-card.md (not in report.json)', files: ['experiments/human-review-sample/independent-ai-review-2.md']},
    note: 'The owner review covers 45 gold, 40 answer, 30 source and 10 decision cards, not every gold record and not blanket source verification. The 17 manual answer verdicts all agree with the independent AI review: agreement, not accuracy. The blind AI sample was chosen to be rich in failures, so its counts are not a population accuracy estimate. No blinded annotation was run. No endorsed-without-review cards are active.',
    table: () => ({caption: 'Review counts', columns: ['Review', 'Group', 'Count'], rows: rows.flatMap(r => r.segments.map(s => [r.label, s.label, s.value]))}),
    draw: (host, c) => shareBars(host, c, {rows, label: 'Review counts by kind', rowH: c.compact ? 60 : 56})
  });
}

const limitsFor = m => [
  ['Gold labels are mostly AI drafts', 'Gold v3.5 has 268 cases (237 development, 31 held-out); 45 are owner-reviewed and 223 are AI drafts. Review left 43 unchanged and changed 2 labels: HO-022 (clarify to answer) and DEV-018 (refuse to clarify).', 'README.md · docs/system-card.md · experiments/gold/CHANGELOG.md'],
  ['Owner review is per card and partly circular', 'The owner decided 125 cards: 30 with their own verdict, 95 by agreeing with an AI suggestion. No blinded annotation was run.', 'docs/human-review/owner-review-summary.md · docs/system-card.md'],
  ['Held-out reuses development evidence', '31 cases; 25 of 31 reuse a development evidence id and 15 of 31 reuse their whole set. The interval on the r3 gain touches or crosses zero.', 'docs/system-card.md · report.json › evaluation.paired'],
  ['Some scores sit on earlier gold versions', `Development rows use ${goldOf(m.evalRow('dev-A3', 'gpt-6-luna')).label}; held-out rows use ${goldOf(m.heldRow('r3', 'gpt-6-luna')).label}, after three post-run edits that lowered or kept scores. Rows not yet on v3.5 need rescoring for the HO-022 and DEV-018 label changes, from saved outputs with no new generation.`, 'experiments/heldout/FREEZE.md · README.md · experiments/gold/CHANGELOG.md'],
  ['T-I06: handled once, not shown to generalise', 'Before the fix, a planted false figure was cited and passed the quote and number checks. The deterministic cross-check handled that one case in both models. The scorer that counts it as passed was written after the run. Coverage is a closed grammar.', 'docs/experiments/m7-t-i06-crosscheck.md · D-038'],
  ['The scanner missed all 5 paraphrase probes', 'Zero scanner hits does not certify a source as safe.', 'docs/human-review/independent-ai-review-m1-2.md'],
  ['Extraction has known defects', 'In sampled passages, 1 of 16 lost a note boundary and 2 of 4 HTML passages flattened superscripts; some feedback-form blocks are garbled. No corpus-wide count exists, and a fix on an unmerged branch is unevaluated.', 'docs/human-review/ai-pre-review-passage-spot-check.md'],
  ['The sector dataset total sits above MOM\u2019s final figure', 'Migrant domestic workers may explain it, but that is an inference.', 'docs/data-sheet.md › section 5'],
  ['The judge shares a provider with the generators', 'Their errors may correlate. A zero unsupported-claim rate on a selected sample does not show the answers are safe.', 'docs/evaluation-report.md › Judge and uncertainty'],
  ['Costs are list-price estimates', 'List prices dated 30 October 2026, without cached-input discounts. Latency is saved wall time from the recorded runs.', 'docs/system-card.md › Architecture and models']
];

function limitCards(m) {
  const wrap = el('div', 'pr-limit-grid');
  limitsFor(m).forEach(([title, text, src], i) => {
    const card = el('article', `pr-limit pr-reveal${i === 4 ? ' is-open' : ''}`);
    card.append(el('span', 'pr-limit-no', String(i + 1).padStart(2, '0')), el('h5', 'pr-limit-title', title), el('p', '', text), evi(src));
    wrap.append(card);
  });
  return wrap;
}

export function renderLimits(m, ctx) {
  const ch = chapter({
    id: 'limits', no: 8, eyebrow: 'Human review and limits', title: 'The owner reviewed 45 of 268 gold cases; the other 223 labels are AI drafts',
    bullets: [
      'Owner review: 125 cards decided, 30 by own verdict, 95 by agreeing with an AI suggestion.',
      'Not independent annotation; no blinded review was run.',
      `${limitsFor(m).length} limits below constrain what the results show, including the single T-I06 result and the scanner bypass.`
    ]
  });
  const review = section('Owner review covers 45 gold, 40 answer and 30 source cards');
  review.append(reviewFigure().root);
  ch.body.append(review);
  const limits = section(`${limitsFor(m).length} limits on the conclusions`);
  limits.append(limitCards(m));
  const rec = [...(m.report?.limitations || []), ...(m.section('evaluation').limitations || [])];
  if (rec.length) limits.append(details('Limitations recorded in report.json', list(rec), evi('report.json › limitations · evaluation.limitations')));
  ch.body.append(limits);
  return ch.root;
}

const NEXT = [
  ['Rescore on gold v3.5, then rerun held-out on frozen gold', 'I would rescore the saved outputs on v3.5 with no new generation, then rerun held-out on frozen, reviewed gold. The current r3 comparison is inconclusive and was scored after post-run edits.', 'Success: a paired interval for r3 minus hybrid that excludes zero, or a clear null.'],
  ['Test the cross-check beyond one planted case', 'The cross-check handles the one planted figure. I would write more planted-figure cases before seeing results, score them with a scorer fixed in advance, and measure false conflicts on the development set.', 'Success: planted figures corrected at a measured rate with a pre-fixed scorer, and no new false conflicts.'],
  ['Add independent review', 'I would add blinded, independent annotation for the 223 draft gold cases, then promote reviewed gold from draft. 95 owner decisions agreed with an AI suggestion.', 'Success: named independent reviewers on every gold case used in a reported metric.'],
  ['Evaluate the extraction fixes', 'I would run retrieval and answer evaluation on the extraction branch. It lifts passage counts and removes garbled blocks, and 61 gold passage ids need migration.', 'Success: retrieval and answer metrics on the migrated gold, reported next to the current ones.'],
  ['Replace the heuristic scanner', 'I would add model-assisted screening and test it on a larger, human-written set. The current scanner missed all 5 paraphrase probes.', 'Success: paraphrase probes caught at a measured rate, with the false-positive cost reported.'],
  ['Soften the period filter', 'I would test a filter that widens when the candidate pool is weak. A later release can restate an earlier quarter, and a hard filter can exclude it.', 'Success: fewer filter-related misses with the R3 gain kept.']
];

export function renderNext(m, ctx) {
  const ch = chapter({
    id: 'next', no: 9, eyebrow: 'Next', title: 'Six experiments would close the main evaluation gaps',
    bullets: [
      'Each step names the gap it addresses and the measurement that would close it.',
      'None is built or run yet.'
    ]
  });
  const ol = el('ol', 'pr-next');
  NEXT.forEach(([title, text, success], i) => {
    const li = el('li', 'pr-next-item pr-reveal');
    li.append(el('span', 'pr-next-no', String(i + 1)), el('h5', 'pr-next-title', title), el('p', '', text), el('p', 'pr-next-success', success));
    ol.append(li);
  });
  ch.body.append(ol);
  const reproduce = callout({
    tone: 'note', title: 'Report provenance',
    text: 'Turn on \u201cShow the evidence\u201d to see the report field or file behind each number. Rebuild the report from committed artifacts with: uv run labourlens build-report.',
    src: 'README.md · docs/deploy.md'
  });
  ch.body.append(reproduce);
  return ch.root;
}

const olist = items => { const ol = el('ol', 'pr-list'); items.forEach(t => ol.append(el('li', '', t))); return ol; };
const ciText = ci => ci ? `95% CI ${fmt.pct(ci[0])} to ${fmt.pct(ci[1])}` : '';

export function renderSummary(m, ctx) {
  const L = m.ladder?.configs, a3 = m.evalRow('dev-A3', 'gpt-6-luna'), held = m.heldRow('r3', 'gpt-6-luna');
  const dev = metricOf(a3?.metrics?.behaviour_accuracy), ho = metricOf(held?.metrics?.behaviour_accuracy);
  const pair = m.paired[0]?.models?.['gpt-6-luna'], pairN = m.paired[0]?.n;
  const luna = m.securityRow('gpt-6-luna')?.metrics, x = m.section('mcp').metrics || {};
  const crosses = pair && pair.ci95[0] <= 0;
  const title = ho.rate != null
    ? `On ${ho.n ?? 31} held-out cases r3 scored ${fmt.pct(ho.rate)}${ho.ci ? ` (${ciText(ho.ci)})` : ''}, and its gain over hybrid is ${crosses ? 'not demonstrated' : 'above zero'}`
    : 'Held-out result not recorded';
  const ch = chapter({id: 'summary', no: 11, eyebrow: 'Summary', title});
  const findings = [
    L?.R0 && L?.R3 ? `${fmt.pct(L.R0['hit@8'])} to ${fmt.pct(L.R3['hit@8'])}: hit@8 from R0 to R3 on ${fmt.int(m.ladder.n_cases)} development cases.` : null,
    dev.rate != null ? `${fmt.pct(dev.rate)}: behaviour accuracy of A3 with gpt-6-luna on ${fmt.int(dev.n ?? a3.metrics.n_cases)} development cases${dev.ci ? ` (${ciText(dev.ci)})` : ''}.` : null,
    pair ? `${fmt.pts(pair.diff)}: held-out r3 minus hybrid for gpt-6-luna on ${fmt.int(pairN)} cases, interval ${fmt.pts(pair.ci95[0])} to ${fmt.pts(pair.ci95[1])}${crosses ? ', not demonstrated' : ''}.` : null,
    luna ? `${fmt.int(luna.passed)} of ${fmt.int(luna.n_scored)}: threat-suite cases passed by gpt-6-luna with defences.` : null,
    x.compared_datasets != null ? `${fmt.int(x.different_outputs)} of ${fmt.int(x.compared_datasets)}: datasets whose output differed between MCP and direct calls.` : null
  ].filter(Boolean);
  const block = section('Five results');
  block.append(olist(findings));
  const open = section('Open items');
  open.append(olist([
    'T-I06: a deterministic cross-check handled the one planted-figure case post fix. The scorer that passes it was written after the run.',
    'Gold labels are mostly AI drafts: 45 of 268 are owner-reviewed.',
    'The held-out rerun on frozen, reviewed gold has not been run.'
  ]));
  ch.body.append(block, open);
  return ch.root;
}

export function renderQuestions(m, ctx) {
  const L = m.ladder?.configs, mcp = m.section('mcp'), x = mcp.metrics || {};
  const p50 = (mcp.rows || []).find(r => r.metric === 'latency_p50_ms');
  const calc = metricOf(m.evalRow('dev-A3', 'gpt-6-luna')?.metrics?.calc_correct);
  const r3 = L?.R3 || {};
  const qa = [
    ['Why is hybrid retrieval with RRF the baseline?',
      `BM25 is the non-LLM baseline and dense retrieval finds paraphrases. RRF combines ranks, so raw scores on different scales are not compared directly${L?.R0 ? `; R0 reaches hit@8 ${fmt.pct(L.R0['hit@8'])} on ${fmt.int(m.ladder.n_cases)} development cases` : ''}.`],
    ['Why rerank, and what did it cost?',
      L?.R0 && L?.R3 ? `R3 filters by period and release stage, then reranks: hit@8 goes from ${fmt.pct(L.R0['hit@8'])} to ${fmt.pct(L.R3['hit@8'])}, at a median ${fmt.seconds(r3.rerank_latency_s_p50_p95?.[0])} and a mean $${r3.cost_usd_per_query_mean} per query.` : 'Ladder not recorded.'],
    ['How do you know the agent does no arithmetic?',
      `The model chooses tools and arguments; application code validates them and runs the calculations. The scorer requires a cited deterministic calculation, and calculation correctness is ${fmt.pct(calc.rate)} on ${fmt.int(calc.n)} cases.`],
    ['What happens today if a passage contains a planted false figure?',
      'Before the fix the luna models repeated it and the quote and number checks passed (T-I06). A deterministic cross-check now corrects the claim to the dataset value, cites both, and adds a source-conflict caveat. It handled the one planted case in both models; the scorer that passes it was written after the run; coverage is a closed grammar; not shown to generalise.'],
    ['Why one agent and not several?',
      'ADR-002 fixes one bounded StateGraph agent with a model-directed planner and three typed read-only tools. I did not build a multi-agent design.'],
    ['What did the MCP layer cost, and what did it add?',
      p50 ? `A median call takes ${p50.mcp} ms over MCP against ${p50.direct} ms direct, plus ${fmt.num(x.connection_seconds, 2)} s to connect once. It adds capability discovery and typed tool contracts; ${fmt.int(x.different_outputs)} of ${fmt.int(x.compared_datasets)} datasets gave different output.` : 'Latency rows not recorded.']
  ];
  const ch = chapter({id: 'questions', no: 12, eyebrow: 'Questions', title: 'Six questions I expect, with short answers'});
  const dl = el('dl', 'pr-qa');
  qa.forEach(([q, a]) => {
    const wrap = el('div', 'pr-qa-item pr-reveal');
    wrap.append(el('dt', '', ''), el('dd', '', a));
    wrap.firstChild.append(el('strong', '', q));
    dl.append(wrap);
  });
  ch.body.append(dl);
  return ch.root;
}
