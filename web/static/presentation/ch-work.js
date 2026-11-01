// Chapter 10: work log. Experiments, decisions, failures, review process and spend.
// Decision and milestone text comes from report.json > work (parsed from docs/decisions.md and
// docs/progress.md). Numbers come from the other report.json sections. The registry wording
// (question, factor, outcome) is curated here and cites the decision ids it follows.
import {el, fmt, finite, figure, dotPlot, reduced} from '../charts.js';
import {chapter, section, grid, stat, callout, evi, dataTable} from './ui.js';
import {metricOf, goldOf} from './model.js';

const pct = v => fmt.pct(v);
const ci = r => (r?.ci ? `, 95% CI ${pct(r.ci[0])} to ${pct(r.ci[1])}` : '');
const beh = row => { const v = metricOf(row?.metrics?.behaviour_accuracy); return {...v, text: finite(v.rate) ? `${pct(v.rate)}${ci(v)}, n=${row.metrics.n_cases}` : 'not recorded'}; };

function evalDetail(row) {
  if (!row) return [];
  const x = row.metrics, sp = row.scoring_provenance || {}, ph = sp.prompt_sha256 || {};
  const total = finite(x.cost_per_case_usd) && finite(x.n_cases) ? x.cost_per_case_usd * x.n_cases : null;
  return [`${row.label}: ${goldOf(row).label}, n=${x.n_cases}`,
    `latency median ${fmt.seconds(x.latency_p50_s)}, 95th percentile ${fmt.seconds(x.latency_p95_s)}`,
    `generation ${fmt.money(x.cost_per_case_usd)} per case${total !== null ? `, about $${total.toFixed(2)} for the run` : ''}`,
    Object.keys(ph).length ? `prompt hashes: ${Object.entries(ph).map(([k, v]) => `${k} ${v.slice(0, 8)}`).join(', ')}` : ''].filter(Boolean);
}

function registry(m) {
  const L = m.ladder?.configs || {};
  const r = (g, n) => m.retrievalRow(g, n)?.metrics || {};
  const dev = (s, n) => m.evalRow(`dev-${s}`, n), held = (k, n) => m.heldRow(k, n);
  const paired = m.paired[0]?.models || {};
  const pairText = n => paired[n] ? `${fmt.pts(paired[n].diff)} (95% CI ${fmt.pts(paired[n].ci95[0])} to ${fmt.pts(paired[n].ci95[1])})` : 'not recorded';
  const thr = n => m.securityRow(n)?.metrics;
  const th = n => thr(n) ? `${thr(n).passed}/${thr(n).n_scored}` : 'n/a';
  const compare = (n, key) => ['A3', 'X1', 'X2'].map(s => { const v = metricOf(m.evalRow(`dev-${s}`, n)?.metrics?.[key]); return `${s} ${finite(v.rate) ? pct(v.rate) : 'not recorded'}`; }).join(', ');
  const e2 = n => m.e2efixRow(n)?.metrics;
  const e2t = n => (e2(n) ? `${e2(n).passed}/${e2(n).n_scored}` : 'n/a');
  return [
    {id: 'E1', group: 'Retrieval', question: 'Which chunk size suits BM25?', factor: 'Chunking', dev: `merge200 hit@10 ${pct(r('dev-E1-chunking', 'merge200')['hit@10'])}; document blocks ${pct(r('dev-E1-chunking', 'blocks')['hit@10'])} (24 cases)`, held: '', outcome: 'Adopted', dec: ['D-015'], cfg: [`${fmt.int(r('dev-E1-chunking', 'merge200').n_chunks)} chunks at merge200`, 'n=24 text cases, one case is 4.2 points']},
    {id: 'E2', group: 'Retrieval', question: 'Do stemming, stopwords or period normalising help?', factor: 'Tokeniser', dev: `baseline hit@10 ${pct(r('dev-E2-tokenisation', 'baseline')['hit@10'])}; best variant ${pct(Math.max(...['period_norm_off', 'stem_on', 'stopwords_off'].map(k => r('dev-E2-tokenisation', k)['hit@10'])))} (24 cases)`, held: '', outcome: 'Inconclusive', dec: ['D-018'], cfg: ['n=24; changes of one or two cases']},
    {id: 'E3', group: 'Retrieval', question: 'Do BM25 k1 and b matter?', factor: 'k1 or b', dev: `baseline hit@10 ${pct(r('dev-E3-bm25-params', 'b=0.75')['hit@10'])}; range ${pct(Math.min(...['b=0.4', 'b=0.9', 'k1=0.9', 'k1=2.0'].map(k => r('dev-E3-bm25-params', k)['hit@10'])))} to ${pct(Math.max(...['b=0.4', 'b=0.9', 'k1=0.9', 'k1=2.0'].map(k => r('dev-E3-bm25-params', k)['hit@10'])))}`, held: '', outcome: 'Inconclusive', dec: ['D-018'], cfg: ['n=24']},
    {id: 'E5', group: 'Retrieval', question: 'Which embedding model for dense retrieval?', factor: 'Embedding model', dev: `hit@5: 3-large ${pct(r('dev-dense-E5', 'text-embedding-3-large')['hit@5'])}, 3-small ${pct(r('dev-dense-E5', 'text-embedding-3-small')['hit@5'])}, ada-002 ${pct(r('dev-dense-E5', 'text-embedding-ada-002')['hit@5'])}`, held: '', outcome: 'Adopted', dec: ['D-021', 'D-023'], cfg: ['text-embedding-3-large runs in production', 'n=24; spread is a few cases']},
    {id: 'E6', group: 'Retrieval', question: 'BM25, dense or hybrid?', factor: 'Retriever type', dev: `merge200 hit@10: BM25 ${pct(r('dev-dense-E6', 'merge200 bm25')['hit@10'])}, dense ${pct(r('dev-dense-E6', 'merge200 dense')['hit@10'])}, hybrid ${pct(r('dev-dense-E6', 'merge200 hybrid-rrf')['hit@10'])}`, held: '', outcome: 'Adopted', dec: ['D-023'], cfg: ['hybrid uses reciprocal rank fusion', 'n=24']},
    {id: 'R0-R3', group: 'Retrieval', question: 'Do a metadata filter and an LLM rerank help?', factor: 'Filter, rerank, then both', dev: L.R3 ? `hit@8 ${pct(L.R0['hit@8'])} \u2192 ${pct(L.R3['hit@8'])} (R3, 95% CI ${pct(L.R3['hit@8_ci95'][0])} to ${pct(L.R3['hit@8_ci95'][1])}), n=${m.ladder.n_cases}` : 'not recorded', held: 'no retrieval-only run', outcome: 'Adopted', dec: ['D-029', 'D-030'], cfg: L.R3 ? [`rerank median ${fmt.num(L.R3.added_latency_ms_p50 / 1000, 2)} s`, `$${L.R3.cost_usd_total} total for the run`] : []},
    {id: 'A1', group: 'Agent', question: 'Baseline agent: hybrid retrieval, answer_v3, planner_v1', factor: 'Baseline', dev: `gpt-6-luna ${beh(dev('A1', 'gpt-6-luna')).text}`, held: '', outcome: 'Baseline', dec: ['D-030'], cfg: evalDetail(dev('A1', 'gpt-6-luna')).concat(evalDetail(dev('A1', 'gpt-5.6-luna')))},
    {id: 'A2', group: 'Agent', question: 'Does answer_v4 beat answer_v3?', factor: 'Answer prompt', dev: `gpt-6-luna ${beh(dev('A2', 'gpt-6-luna')).text}`, held: '', outcome: 'Not adopted', dec: ['D-030'], cfg: evalDetail(dev('A2', 'gpt-6-luna'))},
    {id: 'A3', group: 'Agent', question: 'Does r3 retrieval beat hybrid?', factor: 'Retrieval (r3)', dev: `gpt-6-luna ${beh(dev('A3', 'gpt-6-luna')).text}`, held: `see H-r3`, outcome: 'Adopted, provisional', dec: ['D-030'], cfg: evalDetail(dev('A3', 'gpt-6-luna')).concat(evalDetail(dev('A3', 'gpt-5.6-luna')))},
    {id: 'A4', group: 'Agent', question: 'Does widening the r3 pool help?', factor: 'Pool widening (r3w)', dev: `gpt-6-luna ${beh(dev('A4', 'gpt-6-luna')).text}`, held: '', outcome: 'Not adopted', dec: ['D-030'], cfg: evalDetail(dev('A4', 'gpt-6-luna'))},
    {id: 'A5', group: 'Agent', question: 'Does planner_v2 beat planner_v1?', factor: 'Planner prompt', dev: `gpt-6-luna ${beh(dev('A5', 'gpt-6-luna')).text}`, held: '', outcome: 'Not adopted', dec: ['D-032'], cfg: evalDetail(dev('A5', 'gpt-6-luna'))},
    {id: 'H-r3 / H-hybrid', group: 'Held-out', question: 'Does r3 beat hybrid on unseen questions?', factor: 'Retrieval (r3 vs hybrid)', dev: `development A3 vs A1: ${beh(dev('A3', 'gpt-6-luna')).text.split(',')[0]} vs ${beh(dev('A1', 'gpt-6-luna')).text.split(',')[0]}`, held: `gpt-6-luna ${pairText('gpt-6-luna')}; gpt-5.6-luna ${pairText('gpt-5.6-luna')}`, outcome: 'Inconclusive', dec: ['D-033', 'D-034', 'D-035'], cfg: evalDetail(held('r3', 'gpt-6-luna')).concat(evalDetail(held('hybrid', 'gpt-6-luna')))},
    {id: 'T', group: 'Safety', question: 'Do the defences change threat-suite results?', factor: 'Defences on or off', dev: `gpt-6-luna ${th('gpt-6-luna')} defended, ${th('gpt-6-luna+naive')} without; gpt-4.1-mini ${th('gpt-4.1-mini')} vs ${th('gpt-4.1-mini+naive')}`, held: '', outcome: 'Inconclusive', dec: ['D-028'], cfg: ['36 handwritten cases, one run per configuration', thr('gpt-6-luna') ? `gpt-6-luna cost ${fmt.money(thr('gpt-6-luna').cost_usd)}` : '']},
    {id: 'X2', group: 'Regression check', question: 'Has the served system regressed on corpus v3 with the 14 runtime changes?', factor: 'Several at once: corpus v3, runtime changes B1-B14, cross-check, gold v3.6. Not an ablation.', dev: `behaviour accuracy, n=237: gpt-6-luna ${compare('gpt-6-luna', 'behaviour_accuracy')}; gpt-5.6-luna ${compare('gpt-5.6-luna', 'behaviour_accuracy')}. Ungrounded-number cases rose; the check was also widened, so the measurement changed too.`, held: 'held-out v2 is separate', outcome: 'Regression check', dec: ['D-043', 'D-044'], cfg: evalDetail(m.evalRow('dev-X2', 'gpt-6-luna')).concat(evalDetail(m.evalRow('dev-X2', 'gpt-5.6-luna')), ['Behaviour, false-answer, over-abstention, key-number recall and calculation intervals overlap those of A3. Ungrounded-number intervals for gpt-5.6-luna do not overlap (X2 against A3).', 'Development cases only. Held-out v2 is a separate corpus-v3 evaluation.'])},
    {id: 'T-e2efix', group: 'Safety', question: 'Do the defences change threat results on corpus v3, final code?', factor: 'Defences on or off, corpus v3, cross-check on (run m7-e2efix-20261031)', dev: `strict scorer, 36 cases: gpt-6-luna ${e2t('gpt-6-luna')} defended, ${e2t('gpt-6-luna+naive')} naive; gpt-5.6-luna ${e2t('gpt-5.6-luna')} defended, ${e2t('gpt-5.6-luna+naive')} naive. T-I06 not shown stable across runs.`, held: '', outcome: 'Inconclusive', dec: ['D-038', 'D-044'], cfg: ['One run per configuration, 36 handwritten cases, closed grammar.', 'The failing gpt-5.6-luna T-I06 run reported the dataset value and disclosed the planted figure in a caveat, but failed an exact-string scorer check. The scorer was not changed after seeing it: a brittleness finding on one case.', e2('gpt-6-luna') ? `gpt-6-luna cost ${fmt.money(e2('gpt-6-luna').cost_usd)}; gpt-5.6-luna cost ${fmt.money(e2('gpt-5.6-luna')?.cost_usd)}` : '']},
    {id: 'X', group: 'Models', question: 'Is a cheaper model enough?', factor: 'Model (gpt-4.1-mini)', dev: `A1 gpt-4.1-mini ${beh(dev('A1', 'gpt-4.1-mini')).text}`, held: 'unregistered extra runs excluded', outcome: 'Not adopted', dec: ['D-022'], cfg: evalDetail(dev('A1', 'gpt-4.1-mini'))}
  ];
}

const scrollTo = id => { const n = document.getElementById(id); if (n) { n.scrollIntoView({behavior: reduced() ? 'auto' : 'smooth', block: 'center'}); if (n.tagName === 'DETAILS') n.open = true; } };

function registryTable(rows, decisionIds) {
  const wrap = el('div', 'pr-reg');
  const state = {key: 'id', dir: 1};
  const cols = [['id', 'ID'], ['question', 'Question'], ['factor', 'One factor changed'], ['dev', 'Development result'], ['held', 'Held-out'], ['outcome', 'Decision'], ['dec', 'Decision id']];
  const scroll = el('div', 'pr-table-scroll');
  const table = el('table', 'pr-table pr-reg-table');
  table.append(el('caption', '', 'Experiment registry. Select a column to sort. Select a row to open its configuration.'));
  const thead = el('thead'), headRow = el('tr');
  const tbody = el('tbody');
  const buttons = cols.map(([key, label]) => {
    const th = el('th'); th.scope = 'col';
    const b = el('button', 'pr-sort', label); b.type = 'button';
    b.addEventListener('click', () => { state.dir = state.key === key ? -state.dir : 1; state.key = key; draw(); });
    th.append(b); headRow.append(th); return [key, th];
  });
  thead.append(headRow);
  const draw = () => {
    buttons.forEach(([key, th]) => th.setAttribute('aria-sort', key === state.key ? (state.dir > 0 ? 'ascending' : 'descending') : 'none'));
    tbody.textContent = '';
    [...rows].sort((a, b) => String(state.key === 'dec' ? a.dec[0] : a[state.key]).localeCompare(String(state.key === 'dec' ? b.dec[0] : b[state.key]), 'en', {numeric: true}) * state.dir).forEach(row => {
      const tr = el('tr'), open = el('button', 'pr-sort pr-row-toggle', row.id); open.type = 'button'; open.setAttribute('aria-expanded', 'false');
      const th = el('th'); th.scope = 'row'; th.append(open); tr.append(th);
      [row.question, row.factor, row.dev, row.held || 'not run', null, null].forEach((t, i) => { if (t !== null) tr.append(el('td', 'pr-wrap', t)); else if (i === 4) tr.append(el('td', `pr-wrap pr-outcome-cell is-${row.outcome.split(/[ ,]/)[0].toLowerCase()}`, row.outcome)); else { const td = el('td', 'pr-wrap'); row.dec.forEach(d => { if (decisionIds.has(d)) { const a = el('button', 'pr-link-btn', d); a.type = 'button'; a.addEventListener('click', () => scrollTo(`pr-work-dec-${d}`)); td.append(a, document.createTextNode(' ')); } else td.append(el('span', '', `${d} `)); }); tr.append(td); } });
      const detailRow = el('tr', 'pr-reg-detail'); detailRow.hidden = true;
      const td = el('td'); td.colSpan = cols.length;
      const ul = el('ul', 'pr-list'); (row.cfg.length ? row.cfg : ['no further configuration recorded']).forEach(c => ul.append(el('li', '', c)));
      td.append(el('p', 'pr-small', `Group: ${row.group}`), ul); detailRow.append(td);
      open.addEventListener('click', () => { detailRow.hidden = !detailRow.hidden; open.setAttribute('aria-expanded', String(!detailRow.hidden)); });
      tbody.append(tr, detailRow);
    });
  };
  table.append(thead, tbody); scroll.append(table); wrap.append(scroll);
  draw();
  return wrap;
}

function decisionLog(m, rows) {
  const items = m.section('work').decisions || [];
  const wrap = el('div', 'pr-declog');
  const search = el('input', 'pr-search'); search.type = 'search'; search.placeholder = 'Search decisions'; search.setAttribute('aria-label', 'Search decisions by id, title or text');
  const count = el('p', 'pr-small', `${items.length} decisions`);
  const list = el('div', 'pr-declist');
  const nodes = items.map(d => {
    const det = el('details', 'pr-dec'); det.id = `pr-work-dec-${d.id}`;
    const sum = el('summary'); sum.append(el('span', 'pr-dec-id', d.id), el('span', 'pr-dec-title', d.title), el('span', 'pr-dec-meta', [d.date, d.status].filter(Boolean).join(', ')));
    const linked = rows.filter(r => r.dec.includes(d.id));
    det.append(sum, el('p', 'pr-small', d.summary || 'See docs/decisions.md.'), el('p', 'pr-small', d.alternatives ? `Alternatives: ${d.alternatives}` : 'Alternatives: not summarised here; see docs/decisions.md.'));
    if (linked.length) det.append(el('p', 'pr-small', `Experiments: ${linked.map(r => r.id).join(', ')}`));
    det.append(evi(`report.json \u203a work.decisions[${d.id}] \u00b7 docs/decisions.md`));
    list.append(det);
    return {det, text: `${d.id} ${d.title} ${d.summary} ${d.alternatives} ${d.status}`.toLowerCase()};
  });
  search.addEventListener('input', () => { const q = search.value.trim().toLowerCase(); let n = 0; nodes.forEach(({det, text}) => { const hit = !q || text.includes(q); det.hidden = !hit; if (hit) n++; }); count.textContent = `${n} of ${items.length} decisions`; });
  wrap.append(search, count, list);
  return wrap;
}

function timeline(m) {
  const ms = m.section('work').milestones || [], dates = (m.section('work').decisions || []).map(d => d.date).filter(Boolean);
  const ol = el('ol', 'pr-timeline');
  ms.forEach(x => { const li = el('li', 'pr-tl-item'); li.append(el('span', 'pr-tl-id', x.id), el('strong', '', x.name), el('span', 'pr-small', x.status)); ol.append(li); });
  const wrap = el('div');
  wrap.append(ol, el('p', 'pr-small', `The progress table has no per-milestone dates. Decisions are dated ${dates[0]} to ${dates[dates.length - 1]}.`), evi('report.json \u203a work.milestones \u00b7 docs/progress.md'));
  return wrap;
}

function failures(m) {
  const dec = id => (m.section('work').decisions || []).find(d => d.id === id);
  const a3 = m.evalRow('dev-A3', 'gpt-6-luna');
  const fixed = [
    ['Stale judge cache', 'Cached judgments were keyed by case id and survived gold changes (DEV-034, DEV-202, DEV-626).', 'Cache now keyed by a fingerprint of question, facts, expected behaviour, answer, cited evidence, judge and prompt. A1-A5 were rejudged.', 'Fixed', 'docs/evaluation-report.md'],
    ['Calculation scorer too strict', 'The first replacement scorer over-constrained prose and units and misparsed a negated formula.', `Corrected before publishing. Only calc_correct changed. A3 gpt-6-luna now ${metricOf(a3?.metrics?.calc_correct).rate !== null ? pct(metricOf(a3.metrics.calc_correct).rate) : 'not recorded'} on ${metricOf(a3?.metrics?.calc_correct).n ?? '?'} cases, replacing an earlier 87.5%.`, 'Fixed', 'docs/evaluation-report.md'],
    ['Threat fixture passed vacuously under r3', 'An earlier r3 fixture omitted candidate lists, so indirect-injection passes were invalid.', 'Rerun on the corrected fixture; every poisoned passage reached evidence and none was left unexercised. The rerun supersedes the earlier results.', 'Fixed', 'experiments/threats/SUMMARY.md'],
    ['Gold edits after the held-out run', 'Five post-run label or evidence edits (HO-029, HO-027, HO-023, HO-004, HO-022).', 'Scores moved down or stayed flat; the original freeze is preserved. Table below.', 'Disclosed', 'docs/evaluation-report.md, experiments/gold/CHANGELOG.md'],
    ['Extraction defects', 'Review found control-bearing blocks, lost note boundaries and flattened superscripts.', dec('D-037') ? `${dec('D-037').title}. Corpus-v2 is evaluated separately from the frozen runs.` : 'Corrections sit on a separate branch and are not evaluated.', dec('D-037') ? 'Decided' : 'Open', 'docs/human-review/ai-pre-review-passage-spot-check.md'],
    ['T-I06: planted false figure', 'A false figure planted in a passage was cited and passed the quote and number checks in all five configurations.', 'Deterministic cross-check (D-038). First post-fix run, 36 cases, one run per configuration: strict scorer 35/36 for both defended models (the caveat quotes the planted figure); refined scorer 36/36, written after seeing the run. Final-code run m7-e2efix-20261031 (corpus v3): gpt-6-luna 36/36 strict, gpt-5.6-luna 35/36 under both scorers, naive 35/36 for both models. T-I06 is not shown stable across runs. The failing gpt-5.6-luna run reported the dataset value and disclosed the planted figure in a caveat, but failed an exact-string scorer check; the scorer was not changed, which is a brittleness finding. One case, closed grammar.', 'Handled once, post hoc', 'docs/system-card.md'],
  ];
  const wrap = el('div', 'pr-limit-grid');
  fixed.forEach(([title, what, fix, status, src], i) => {
    const c = el('article', `pr-limit${status === 'Open' || status === 'Handled once, post hoc' ? ' is-open' : ''}`);
    c.append(el('span', 'pr-limit-no', status), el('h5', 'pr-limit-title', title), el('p', '', what), el('p', '', fix), evi(src));
    wrap.append(c);
  });
  const table = [['r3 / gpt-6-luna', '83.9%', '83.9%', '83.9%', '87.1%'], ['r3 / gpt-5.6-luna', '87.1%', '83.9%', '80.6%', '83.9%'], ['hybrid / gpt-6-luna', '67.7%', '67.7%', '67.7%', '71.0%'], ['hybrid / gpt-5.6-luna', '74.2%', '71.0%', '71.0%', '74.2%']];
  const out = el('div');
  out.append(wrap, el('h5', 'pr-mini-title', 'Held-out behaviour accuracy by gold version'), dataTable('n=31 cases per row', ['Run', 'v3.2 (as run)', 'v3.3', 'v3.4', 'v3.5 (current)'], table));
  const pe = m.paired;
  if (pe.length) out.append(dataTable('Paired difference, r3 minus hybrid, by gold version', ['Version', 'gpt-6-luna', 'gpt-5.6-luna'], pe.map(e => [e.gold_version, ...['gpt-6-luna', 'gpt-5.6-luna'].map(n => `${fmt.pts(e.models[n].diff)} [${fmt.pts(e.models[n].ci95[0])}, ${fmt.pts(e.models[n].ci95[1])}]`)])));
  out.append(el('p', 'pr-small', 'Gold v3.5 applies HO-022 and DEV-018. Development runs A1-A5 and the four registered held-out arms were rescored on v3.5 from saved outputs, with no new answer generation. v3.6 migrates evidence ids for corpus v2 only.'), evi('report.json \u203a evaluation.paired \u00b7 docs/evaluation-report.md \u00b7 README.md'));
  return out;
}

function reviewProcess() {
  const steps = [
    ['AI pre-review', 'Three separate review passes came from the same model family, not three different models.'],
    ['Blind AI checks', 'The checks covered a 71-case gold review and a failure-enriched 40-answer sample. A third pass broke ties.'],
    ['Adjudication', 'The owner decided label policy and the post-run edits (D-031, D-034, D-035) in writing.'],
    ['Human reviewed', 'I signed off every case, answer verdict and source check, in four separate streams. This was one human reviewer, after the AI passes and saved runs; it is not inter-rater evidence.']
  ];
  const ol = el('ol', 'pr-pipeline');
  steps.forEach(([t, x], i) => { const li = el('li', 'pr-pipe-step'); li.append(el('span', 'pr-pipe-no', String(i + 1)), el('strong', '', t), el('span', '', x)); ol.append(li); });
  const wrap = el('div');
  wrap.append(ol, grid('pr-split', callout({tone: 'note', title: 'What it shows', items: ['Where an AI suggestion existed, my decision matched it in 198 of 198 gold cases, 61 of 64 held-out v2 cases, 38 of 39 answers and 29 of 30 source checks.', 'Labels are unchanged in v3.7. Four change-clicks (DEV-034, DEV-202, DEV-626, DEV-627) are recorded and not applied under the out-of-period policy.', '30 source checks: 18 match, 12 minor differences.']}),
    callout({tone: 'warn', title: 'What it does not show', items: ['One human reviewer confirmed AI-drafted labels after the runs; three AI review passes came from the same model family. This is not independent inter-rater evidence.', 'Agreement with the AI suggestion is not accuracy.', 'No second human reviewer or blinded human annotation.']})), evi('docs/human-review/owner-review-final-summary.md · docs/human-review/review-inventory.md'));
  return wrap;
}

function ledger(m) {
  const sum = a => a.reduce((s, v) => s + (finite(v) ? v : 0), 0);
  const ev = m.rows('evaluation');
  const gen = rows => sum(rows.map(r => r.metrics.cost_per_case_usd * r.metrics.n_cases));
  const entries = [
    ['Agent development runs A1-A5, X1, X2 (generation)', gen(ev.filter(r => r.split !== 'heldout'))],
    ['Registered held-out runs (generation)', gen(ev.filter(r => r.split === 'heldout' && !r.diagnostic))],
    ['Post-freeze diagnostic runs (generation)', gen(ev.filter(r => r.split === 'heldout' && r.diagnostic))],
    ['AI judge, all agent runs', sum(ev.map(r => r.metrics.judge_cost_total_usd))],
    ['Threat suite, five configurations', sum(m.rows('security').map(r => r.metrics.cost_usd))],
    ['Threat suite, e2efix run (four configurations)', sum(m.e2efixThreats.map(r => r.metrics.cost_usd))],
    ['Answer-only studies G0-G4', sum(m.rows('answers').map(r => r.metrics.cost_per_case_usd * r.metrics.n))],
    ['Rerank experiments R2 and R3', sum(['R2', 'R3'].map(k => m.ladder?.configs?.[k]?.cost_usd_total))],
    ['Held-out v2 runs (generation and judge)', sum((m.section('evaluation').heldout_v2?.arms || []).map(r => r.metrics.cost_per_case_usd * r.metrics.n_cases + (r.metrics.judge_cost_total_usd || 0)))],
    ['Tool set v2 runs, X3 and V2post (generation and judge)', sum([...(m.section('evaluation').tool_set_v2?.dev_x3?.rows || []), ...(m.section('evaluation').tool_set_v2?.v2post?.rows || [])].map(r => r.metrics.cost_per_case_usd * r.metrics.n_cases + (r.metrics.judge_cost_total_usd || 0)))],
  ].filter(e => e[1] > 0);
  const total = sum(entries.map(e => e[1]));
  const fig = figure({
    id: 'fig-ledger', title: `Recorded spend: about $${total.toFixed(2)}`,
    takeaway: `${entries.sort((a, b) => b[1] - a[1])[0][0]} is the largest line at $${entries[0][1].toFixed(2)}. Total across the recorded lines is $${total.toFixed(2)}.`,
    summary: entries.map(e => `${e[0]}: $${e[1].toFixed(2)}`).join('. '),
    source: {data: 'report.json \u203a evaluation.rows, security.rows, answers.rows, retrieval.ladder (cost fields)', files: ['experiments/eval/*', 'experiments/threats/runs/*', 'experiments/runs/answer-*', 'experiments/runs/dev-R-summary.json']},
    note: 'Estimates from saved usage at list prices dated 30 October 2026 (specs/prices.yaml), without cached-input discounts, so they are upper bounds. Not recorded, so not counted: embedding calls, corpus-building runs, and any run whose usage was not saved. Agent runs are cost per case times cases. The owner reports about $3 in total for the X2 and e2efix experiments; that figure is owner-reported, and the lines above come from the metrics files.',
    table: () => ({caption: 'Recorded spend by phase (USD)', columns: ['Phase', 'USD'], rows: entries.map(e => [e[0], +e[1].toFixed(4)]).concat([['Total recorded', +total.toFixed(4)]])}),
    draw: (host, c) => dotPlot(host, c, {rows: entries.map((e, i) => ({label: e[0], value: e[1], cls: 'c1', hl: i === 0, lines: [e[0], `$${e[1].toFixed(4)}`]})), mode: 'bar', domain: [0, Math.ceil(entries[0][1] * 1.15)], format: v => `$${v}`, valueText: r => `$${r.value.toFixed(2)}`, axisTitle: 'US dollars', label: 'Recorded spend by phase'})
  });
  return fig;
}

export function renderWork(m, ctx) {
  const rows = registry(m), ids = new Set((m.section('work').decisions || []).map(d => d.id));
  const decisions = (m.section('work').decisions || []).length;
  const count = test => rows.filter(r => test(r.outcome)).length;
  const adopted = count(o => o.startsWith('Adopted')), notAdopted = count(o => o === 'Not adopted'), inconclusive = count(o => o === 'Inconclusive');
  const ch = chapter({id: 'work', title: `${rows.length} experiment groups: ${adopted} adopted, ${notAdopted} not adopted, ${inconclusive} inconclusive, ${count(o => o === 'Regression check')} regression check`,
    bullets: ['One factor changed per run, except X2, which is a regression check; configurations chosen on development cases only.', `${decisions} logged decisions, including null results.`, 'Results come from report.json; decision wording follows the decision log.']});
  const stats = el('div', 'pr-stats');
  stats.append(stat({value: decisions, label: 'Decisions', note: 'From D-000', src: 'report.json \u203a work.decisions'}),
    stat({value: rows.length, label: 'Experiment groups', note: 'Retrieval, agent, held-out, safety, models', src: 'report.json \u203a evaluation, retrieval, security'}),
    stat({value: notAdopted, label: 'Not adopted', note: 'Retained in the log', src: 'registry in ch-work.js'}),
    stat({value: inconclusive, label: 'Inconclusive', tone: 'warn', src: 'registry in ch-work.js'}));
  ch.body.append(callout({tone: 'warn', title: 'Document builds', items: ['The system, the live site and the final held-out test all use the current document build (v3: 85 sources, 16,419 passages). Earlier builds are kept only so older results can be reproduced; do not compare numbers across builds.', 'Registered results (A1-A5, held-out, pre-guard threat suites) ran on corpus v1, 13,484 passages. The frozen v1 and v2 results are retained.', 'The X1 extraction experiments and the T-I06 post-fix run used corpus v2, 15,915 passages.', 'Corpus v3 (85 sources, 52,020 observations, 16,419 passages) has three measured evaluations: the X2 development regression check, the e2efix threat run and held-out v2 (65 questions, evidence-disjoint at source level only), plus the tool set v2 runs (X3 and V2post, not adopted).', 'The Droplet serves corpus v3 and post-fix code (commit c297146; /healthz fingerprint d402120f6f8f; 16,419 passages; 1,847 chunks), as reported by the owner.'], src: 'README.md \u203a Corpus versions \u00b7 docs/evaluation-report.md'}));
  ch.body.append(stats);
  const s1 = section('Milestones recorded in the progress log'); s1.append(timeline(m)); ch.body.append(s1);
  const s2 = section(`${rows.length} experiment groups; one factor changed in each, except the X2 regression check`, ['Sort by any column. Open a row for its configuration.']); s2.append(registryTable(rows, ids)); ch.body.append(s2);
  const s3 = section(`${decisions} decisions, searchable by id or text`, ['Alternatives appear only where the decision recorded them.']); s3.append(decisionLog(m, rows)); ch.body.append(s3);
  const s4 = section('Six problems found during the work; T-I06 not shown stable across runs'); s4.append(failures(m)); ch.body.append(s4);
  const s5 = section('Human review: four separate streams'); s5.append(reviewProcess()); ch.body.append(s5);
  const s6 = section('Cost: recorded spend by phase'); s6.append(ledger(m).root); ch.body.append(s6);
  return ch.root;
}
