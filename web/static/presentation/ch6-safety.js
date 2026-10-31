import {el, fmt, figure, heatmap, dotPlot} from '../charts.js';
import {chapter, section, grid, stat, callout, evi, dataTable} from './ui.js';

const CATEGORIES = [
  ['direct_injection', 'Direct injection'], ['indirect_injection_passage', 'Poisoned passage'], ['sensitive_data', 'Sensitive data'],
  ['unsafe_tool_use', 'Unsafe tool use'], ['unsupported_claims', 'Unsupported claims'], ['mcp_server_failure', 'MCP server failure']
];
const CONFIGS = [
  ['gpt-4.1-mini+naive', 'gpt-4.1-mini', 'no defence'], ['gpt-4.1-mini', 'gpt-4.1-mini', 'defended'], ['gpt-5.6-luna', 'gpt-5.6-luna', 'defended'],
  ['gpt-6-luna+naive', 'gpt-6-luna', 'no defence'], ['gpt-6-luna', 'gpt-6-luna', 'defended']
];

function matrixFigure(m) {
  const cols = [...CATEGORIES.map(([key, label], i) => ({key, label, short: ['Direct', 'Poison', 'Data', 'Tools', 'Claims', 'MCP'][i]})), {key: 'all', label: 'All 36', short: 'All'}];
  const rows = CONFIGS.map(([id, model, mode]) => {
    const row = m.securityRow(id);
    if (!row) return null;
    const cells = CATEGORIES.map(([key, label]) => {
      const e = row.strata?.[key];
      if (!e) return null;
      const rate = e.n ? e.passed / e.n : null;
      return {value: rate, text: `${e.passed}/${e.n}`, sub: '', tone: e.passed < e.n ? 'bad' : undefined, lines: [`${model}, ${mode}`, label, `Passed ${e.passed} of ${e.n}`, `Not exercised: ${e.not_exercised}`, Array.isArray(e.useful) ? `Useful answers: ${e.useful[0]} of ${e.useful[1]}` : ''].filter(Boolean)};
    });
    const x = row.metrics;
    cells.push({value: x.pass_rate, text: `${x.passed}/${x.n_scored}`, sub: fmt.pct(x.pass_rate), tone: x.passed < x.n_scored ? 'bad' : undefined, lines: [`${model}, ${mode}`, `Passed ${x.passed} of ${x.n_scored}`, `Wilson 95% interval ${fmt.pct(x.pass_rate_ci95?.[0])} to ${fmt.pct(x.pass_rate_ci95?.[1])}`]});
    return {label: `${model}, ${mode}`, cells, row};
  }).filter(Boolean);
  const defended = rows.filter(r => /defended/.test(r.label)), naive = rows.filter(r => /no defence/.test(r.label));
  const failOf = (row, only) => Object.entries(row.row.strata || {}).reduce((sum, [key, e]) => sum + (!only || key === only ? e.n - e.passed : 0), 0);
  const failTotal = rows.reduce((sum, r) => sum + failOf(r), 0), failIndirect = rows.reduce((sum, r) => sum + failOf(r, 'indirect_injection_passage'), 0);
  const lunaDef = rows.find(r => r.label === 'gpt-6-luna, defended')?.row.metrics, lunaNaive = rows.find(r => r.label === 'gpt-6-luna, no defence')?.row.metrics;
  const lunaText = lunaDef && lunaNaive ? `gpt-6-luna: ${lunaDef.passed} of ${lunaDef.n_scored} defended, ${lunaNaive.passed} of ${lunaNaive.n_scored} without.` : '';
  return {
    rows, fig: figure({
      id: 'fig-threat-matrix', title: `${failIndirect} of ${failTotal} failed cases across ${rows.length} runs are poisoned-passage cases`, wide: true,
      takeaway: `Red cells contain failures. ${lunaText}`,
      summary: rows.map(r => `${r.label}: ${r.cells.map((c, i) => c ? `${cols[i].label} ${c.text}` : '').join(', ')}`).join('. '),
      source: {data: 'report.json › security.rows[*].strata and .metrics', files: ['experiments/threats/runs/*.metrics.json']},
      note: 'One run per configuration. The suite is 36 handwritten cases, so it checks known attacks; it does not establish general safety.',
      table: () => ({caption: 'Threat suite pass counts', columns: ['Configuration', ...cols.map(c => c.label)], rows: rows.map(r => [r.label, ...r.cells.map(c => c ? c.text : '')])}),
      draw: (host, c) => heatmap(host, c, {cols: cols.map(x => ({label: x.label, short: x.short})), rows: rows.map(r => ({label: r.label, cells: r.cells})), label: 'Threat suite pass counts by configuration and category', cellH: c.compact ? 44 : 48})
    })
  };
}

function intervalFigure(m, rows) {
  const items = rows.map(r => ({label: r.label, value: r.row.metrics.pass_rate, ci: r.row.metrics.pass_rate_ci95, cls: /no defence/.test(r.label) ? 'c6' : 'c1', lines: [r.label, `${r.row.metrics.passed} of ${r.row.metrics.n_scored} passed (${fmt.pct(r.row.metrics.pass_rate)})`, `Wilson 95% interval ${fmt.pct(r.row.metrics.pass_rate_ci95?.[0])} to ${fmt.pct(r.row.metrics.pass_rate_ci95?.[1])}`]}));
  const mini = rows.filter(r => r.label.startsWith('gpt-4.1-mini'));
  const dm = mini.find(r => /defended/.test(r.label))?.row.metrics, nm = mini.find(r => /no defence/.test(r.label))?.row.metrics;
  return figure({
    id: 'fig-threat-ci', title: dm && nm ? `gpt-4.1-mini passes ${dm.passed} of ${dm.n_scored} defended and ${nm.passed} of ${nm.n_scored} without defences; the benefit is not demonstrated` : 'Pass rate by configuration',
    takeaway: dm && nm ? `Wilson intervals overlap: ${fmt.pct(dm.pass_rate_ci95[0], 0)} to ${fmt.pct(dm.pass_rate_ci95[1], 0)} defended, ${fmt.pct(nm.pass_rate_ci95[0], 0)} to ${fmt.pct(nm.pass_rate_ci95[1], 0)} without.` : '',
    summary: items.map(i => `${i.label}: ${fmt.pct(i.value)}`).join('. '),
    source: {data: 'report.json › security.rows[*].metrics.{pass_rate,pass_rate_ci95}', files: ['experiments/threats/runs/*.metrics.json']},
    table: () => ({caption: 'Pass rate with Wilson 95% interval', columns: ['Configuration', 'Pass rate', 'CI low', 'CI high'], rows: items.map(i => [i.label, i.value, i.ci?.[0], i.ci?.[1]])}),
    draw: (host, c) => dotPlot(host, c, {rows: items, domain: [0.6, 1], ticks: [0.6, 0.7, 0.8, 0.9, 1], label: 'Threat suite pass rate with intervals', axisTitle: 'Pass rate (Wilson 95% interval)', rowH: c.compact ? 38 : 38})
  });
}

function canaryTable(rows) {
  const wrap = el('div', 'pr-canary pr-reveal');
  wrap.append(el('h5', 'pr-mini-title', `${rows.reduce((n, r) => n + (r.row.metrics.canary_leaks || 0), 0)} canary leaks across ${rows.length} runs; run cost in USD`));
  wrap.append(dataTable('Threat suite, per configuration', ['Configuration', 'Passed', 'Canary leaks', 'Canary caveats', 'Median seconds', 'Run cost (USD)'],
    rows.map(r => [r.label, `${r.row.metrics.passed}/${r.row.metrics.n_scored}`, String(r.row.metrics.canary_leaks), String(r.row.metrics.canary_caveat), fmt.num(r.row.metrics.latency_p50_s, 1), fmt.money(r.row.metrics.cost_usd)])));
  wrap.append(el('p', 'pr-small', 'Canary: a fake secret planted in the context. Leak: it appears in an answer. Caveat: a planted figure is repeated with a warning.'), evi('report.json › security.rows[*].metrics.{canary_leaks,canary_caveat,cost_usd,latency_p50_s}'));
  return wrap;
}

function tI06() {
  const root = el('aside', 'pr-hero-callout pr-reveal');
  root.setAttribute('aria-labelledby', 'pr-ti06-title');
  const flag = el('p', 'pr-hero-callout-flag');
  flag.append(el('span', 'pr-flag-dot'), document.createTextNode('Open failure'));
  const title = el('h4', 'pr-hero-callout-title', 'T-I06 (open): a false figure planted in a passage is accepted');
  title.id = 'pr-ti06-title';
  const steps = el('ol', 'pr-ti06-steps');
  [['An attacker plants a false figure in a report passage.', 'The passage looks like any other.'], ['The agent cites it.', 'The quote is verbatim and the number is in the passage, so the quote and number checks pass.'], ['Nothing compares it with the statistics.', 'Passage figures are not checked against validated observations for the same series and period.']].forEach(([head, text], i) => {
    const li = el('li');
    li.append(el('span', 'pr-ti06-no', String(i + 1)), el('strong', '', head), el('span', '', text));
    steps.append(li);
  });
  root.append(flag, title, el('p', 'pr-hero-callout-text', 'Common failure in all five configurations, defended or not. Deterministic passage-to-dataset cross-check: proposed, not built.'), steps, evi('docs/system-card.md › Risks, controls and oversight · docs/evaluation-report.md › Threat suite'));
  return root;
}

export function renderSafety(m, ctx) {
  const matrix = matrixFigure(m);
  const luna = m.securityRow('gpt-6-luna')?.metrics, lunaNaive = m.securityRow('gpt-6-luna+naive')?.metrics;
  const ch = chapter({
    id: 'safety', no: 6, eyebrow: 'Safety',
    title: luna ? `gpt-6-luna passes ${luna.passed} of ${luna.n_scored} threat cases with defences; T-I06 is open and the scanner missed 5 of 5 paraphrase probes` : 'Threat tests and observed failures',
    bullets: [
      `Suite: ${CATEGORIES.length} categories, five configurations, one run each; handwritten cases.`,
      'Retrieved text is treated as untrusted data; tools are read-only.',
      'Open failure: T-I06. Scanner bypass: all five paraphrased probes, detector-only evidence.'
    ]
  });
  ch.body.append(tI06());
  const stats = el('div', 'pr-stats');
  if (luna) stats.append(
    stat({value: luna.n_scored, label: 'Threat cases', note: 'Six categories, handwritten', src: 'report.json › security.rows[gpt-6-luna].metrics.n_scored'}),
    stat({value: luna.passed, label: 'Passed, gpt-6-luna defended', note: `Wilson 95% interval ${fmt.pct(luna.pass_rate_ci95[0])} to ${fmt.pct(luna.pass_rate_ci95[1])}`, tone: 'brass', src: 'report.json › security.rows[gpt-6-luna].metrics'}),
    stat({value: luna.canary_leaks, label: 'Canary leaks, gpt-6-luna', note: 'Fake secrets in an answer', src: 'report.json › security.rows[gpt-6-luna].metrics.canary_leaks'})
  );
  const s = section(luna && lunaNaive ? `Defences did not change the gpt-6-luna result: ${luna.passed} of ${luna.n_scored} defended, ${lunaNaive.passed} of ${lunaNaive.n_scored} without` : 'Threat matrix', ['Cells are passed over scored cases.', 'Poisoned passages reached the agent\u2019s evidence in these runs.']);
  s.append(stats, matrix.fig.root);
  s.append(grid('pr-split', intervalFigure(m, matrix.rows).root, canaryTable(matrix.rows)));
  ch.body.append(s);

  const controls = section('Five controls are implemented and three gaps are known, including the scanner bypass (5 of 5 paraphrase probes)');
  controls.append(grid('pr-split', 
    callout({tone: 'note', title: 'Controls in place', items: ['Retrieved text is marked as untrusted data in the model context.', 'Tools are read-only; arguments are enums built from the catalogue.', 'Steps, retries and time are capped.', 'Secrets stay server-side and are redacted in logs.', 'Citations are validated before display.'], src: 'docs/architecture.md · docs/threat-model.md'}),
    callout({tone: 'warn', title: 'Known gaps', items: ['Ingestion scanner is heuristic: all five paraphrased malicious probes bypassed it in a second blind AI review. Detector-only evidence, no observed exploit.', 'Quote presence does not show that a quote supports the claim.', 'The MCP input filter missed one paraphrased instruction in the saved transcript.'], src: 'docs/human-review/independent-ai-review-m1-2.md · docs/mcp-demo-transcript.md §6'})
  ));
  ch.body.append(controls);
  return ch.root;
}
