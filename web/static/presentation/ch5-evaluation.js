import {el, fmt, finite, quantile, figure, lineChart, dotPlot, dumbbell, heatmap, boxStrip, scatter} from '../charts.js';
import {chapter, section, grid, stat, details} from './ui.js';
import {FAMILIES, FAMILY_LABEL, metricOf, runLabel, goldOf} from './model.js';

const STEPS = [
  ['A1', 'Baseline: hybrid retrieval, answer prompt v3, planner v1.'],
  ['A2', 'Changes only the answer prompt (answer_v4).'],
  ['A3', 'Changes retrieval to r3: period and release filter, then rerank.'],
  ['A4', 'Widens the r3 candidate pool (r3w).'],
  ['A5', 'Changes only the planner prompt, from A3 (planner_v2).']
];
const MODEL_CLS = {'gpt-6-luna': 'c1', 'gpt-5.6-luna': 'c3', 'gpt-4.1-mini': 'c5'};

function headlineFigure(m) {
  const row = m.evalRow('dev-A3', 'gpt-6-luna');
  if (!row) return null;
  const x = row.metrics;
  const spec = [
    {group: true, label: 'Higher is better'},
    ['Behaviour accuracy', x.behaviour_accuracy, 'all cases'], ['Claim support', x.claim_supported_rate, 'judged claims'], ['Reference fact coverage', x.fact_coverage, 'reference facts'],
    ['Gold evidence cited', x.gold_cited_any, 'eligible cases'], ['Key-number recall', x.key_number_recall, 'eligible cases'], ['Calculation correct', x.calc_correct, 'calculation cases'],
    {group: true, label: 'Lower is better'},
    ['False-answer rate', x.false_answer_rate, 'eligible cases'], ['Over-abstention', x.over_abstention_rate, 'all cases'], ['Cases with ungrounded numbers', x.cases_with_ungrounded_numbers, 'all scored cases']
  ];
  const rows = spec.map(s => {
    if (!Array.isArray(s)) return s;
    const [label, raw, unit] = s, v = metricOf(raw);
    const adverse = /False|Over|ungrounded/.test(label);
    return {label, sub: finite(v.n) ? `n=${fmt.int(v.n)} ${unit}` : '', value: v.rate, ci: v.ci, cls: adverse ? 'c4' : 'c1', hl: label === 'Behaviour accuracy',
      lines: [label, `${fmt.pct(v.rate)}${v.ci ? `, 95% CI ${fmt.pct(v.ci[0])} to ${fmt.pct(v.ci[1])}` : ''}`, finite(v.n) ? `n=${fmt.int(v.n)} ${unit}` : '']};
  });
  const b = metricOf(x.behaviour_accuracy), calc = metricOf(x.calc_correct);
  return figure({
    id: 'fig-headline', title: `Run A3 with gpt-6-luna scores ${fmt.pct(b.rate)} behaviour accuracy on ${fmt.int(row.metrics.n_cases)} development cases`, wide: true,
    takeaway: `95% CI ${fmt.pct(b.ci[0])} to ${fmt.pct(b.ci[1])}. Calculation correct is ${fmt.pct(calc.rate)} on only ${calc.n} cases.`,
    summary: rows.filter(r => !r.group).map(r => `${r.label}: ${fmt.pct(r.value)}`).join('. '),
    source: {data: 'report.json › evaluation.rows[agent-dev-A3/gpt-6-luna].metrics', files: ['experiments/eval/agent-dev-A3/gpt-6-luna.metrics.json']},
    note: `Scored against ${goldOf(row).label} by an AI judge (gpt-6.1-terra). These are agreement figures, not independently validated accuracy. Denominators differ by metric.`,
    table: () => ({caption: 'Run A3, gpt-6-luna', columns: ['Metric', 'Rate', 'CI low', 'CI high', 'n'], rows: rows.filter(r => !r.group).map(r => [r.label, r.value, r.ci?.[0] ?? '', r.ci?.[1] ?? '', r.sub])}),
    draw: (host, c) => dotPlot(host, c, {rows, domain: [0, 1], label: 'Run A3 metrics with 95% intervals', rowH: c.compact ? 40 : 38, axisTitle: 'Rate, 95% interval'})
  });
}

function progressionFigure(m) {
  const ids = ['A1', 'A2', 'A3', 'A4', 'A5'];
  const series = Object.keys(MODEL_CLS).map(name => ({
    key: name, label: name, cls: MODEL_CLS[name], focus: name === 'gpt-6-luna',
    rows: ids.map(id => m.evalRow(`dev-${id}`, name)),
  })).map(s => ({...s, values: s.rows.map(r => r ? metricOf(r.metrics.behaviour_accuracy).rate : null), ci: s.rows.map(r => r ? metricOf(r.metrics.behaviour_accuracy).ci : null), ns: s.rows.map(r => r ? r.metrics.n_cases : null)}));
  const luna = series[0], luna56 = series[1];
  const a1 = luna.values[0], a3 = luna.values[2];
  const val = (name, i) => series.find(z => z.key === name).values[i];
  const promptMove = Math.max(...['gpt-6-luna', 'gpt-5.6-luna'].map(n => Math.abs(val(n, 1) - val(n, 0))));
  const flat = Math.max(...['gpt-6-luna', 'gpt-5.6-luna'].flatMap(n => [Math.abs(val(n, 3) - val(n, 2)), Math.abs(val(n, 4) - val(n, 2))]));
  const aside = el('ol', 'pr-steps');
  STEPS.forEach(([id, text]) => { const li = el('li'); li.append(el('strong', '', id), el('span', '', text)); aside.append(li); });
  return figure({
    id: 'fig-progression', title: `Changing retrieval to r3 raised gpt-6-luna behaviour accuracy from ${fmt.pct(a1)} to ${fmt.pct(a3)} (A1 to A3, ${luna.ns[2]} cases)`, wide: true,
    takeaway: `gpt-5.6-luna: ${fmt.pct(luna56.values[0])} to ${fmt.pct(luna56.values[2])}. Answer prompt (A2) moves either model by at most ${(100 * promptMove).toFixed(1)} points. I did not adopt the wider pool (A4) or planner v2 (A5): each stays within ${(100 * flat).toFixed(1)} points of A3.`,
    summary: series.map(s => `${s.label}: ${s.values.map((v, i) => finite(v) ? `${ids[i]} ${fmt.pct(v)}` : '').filter(Boolean).join(', ')}`).join('. '),
    source: {data: 'report.json › evaluation.rows[agent-dev-A1..A5/*].metrics.behaviour_accuracy', files: ['experiments/eval/agent-dev-A1..A5/*.metrics.json']},
    note: 'A1 and A2 scored 235 cases; A3 to A5 scored 237. The A1 to A3 gain is descriptive, not a paired significance test. Whiskers are 95% bootstrap intervals.',
    aside,
    table: () => ({caption: 'Behaviour accuracy by run', columns: ['Run', ...series.map(s => s.label)], rows: ids.map((id, i) => [id, ...series.map(s => finite(s.values[i]) ? `${s.values[i]} (CI ${s.ci[i]?.[0]} to ${s.ci[i]?.[1]}, n=${s.ns[i]})` : '')])}),
    draw: (host, c) => lineChart(host, c, {
      periods: ids, series: series.map(s => ({key: s.key, label: s.label, cls: s.cls, values: s.values, ci: s.ci, focus: s.focus})), yFormat: v => fmt.pct(v, 0), tipFormat: v => fmt.pct(v), domain: [0.6, 1],
      periodLabel: id => `${id}: ${STEPS.find(s => s[0] === id)[1]}`, label: 'Behaviour accuracy by run',
      yTitle: 'Behaviour accuracy', notes: [{index: 2, value: a3, text: `+${(100 * (a3 - a1)).toFixed(1)} pts vs A1`, dy: -22, side: 'left'}]
    })
  });
}

function familyHeat(m) {
  const cols = [['dev-A1', 'A1', 'dev'], ['dev-A3', 'A3', 'dev'], ['dev-A5', 'A5', 'dev']].map(([exp, label, split]) => ({label, sub: 'development', row: m.evalRow(exp, 'gpt-6-luna')}))
    .concat([{label: 'Hybrid', sub: 'held-out', row: m.heldRow('hybrid', 'gpt-6-luna')}, {label: 'r3', sub: 'held-out', row: m.heldRow('r3', 'gpt-6-luna')}]);
  const rows = FAMILIES.map(f => ({
    label: FAMILY_LABEL[f],
    cells: cols.map(c => { const e = c.row?.strata?.[f]; return e ? {value: e.behaviour_accuracy, n: e.n, lines: [`${FAMILY_LABEL[f]}, ${c.label} (${c.sub})`, `Behaviour accuracy: ${fmt.pct(e.behaviour_accuracy)}`, `${e.n} cases`, `False answers: ${e.false_answer}`, `Over-abstentions: ${e.over_abstain}`]} : null; })
  }));
  const weak = rows.map((r, i) => ({label: r.label, v: r.cells[1]?.value, n: r.cells[1]?.n})).filter(r => finite(r.v)).sort((a, b) => a.v - b.v)[0];
  return figure({
    id: 'fig-strata', title: weak ? `${weak.label} is the weakest family in A3 at ${fmt.pct(weak.v)} (${weak.n} cases, gpt-6-luna)` : 'Behaviour accuracy by question family, gpt-6-luna', wide: true,
    takeaway: 'Held-out cells hold 2 to 8 cases each. Family estimates are uncertain.',
    summary: rows.map(r => `${r.label}: ${r.cells.map((c, i) => c ? `${cols[i].label} ${cols[i].sub} ${fmt.pct(c.value)} (n=${c.n})` : '').filter(Boolean).join(', ')}`).join('. '),
    source: {data: 'report.json › evaluation.rows[agent-dev-A1|A3|A5, agent-heldout-H-hybrid|r3 / gpt-6-luna].strata', files: ['experiments/eval/*/gpt-6-luna.metrics.json']},
    note: 'Darker cells are higher. Each cell shows its own case count; strata are descriptive, not tested.',
    table: () => ({caption: 'Behaviour accuracy by family', columns: ['Family', ...cols.map(c => `${c.label} (${c.sub})`)], rows: rows.map(r => [r.label, ...r.cells.map(c => c ? `${c.value} (n=${c.n})` : '')])}),
    draw: (host, c) => heatmap(host, c, {cols: cols.map(x => ({label: x.label, sub: x.sub})), rows, label: 'Behaviour accuracy by family and run', cellH: c.compact ? 44 : 50})
  });
}

function devHeldFigure(m) {
  const mk = (name, label, row, cls, hl) => {
    const v = metricOf(row?.metrics?.behaviour_accuracy);
    return {label, sub: `n=${row?.metrics?.n_cases}`, value: v.rate, ci: v.ci, cls, hl, lines: [`${name}: ${label}`, `${fmt.pct(v.rate)}, 95% CI ${fmt.pct(v.ci?.[0])} to ${fmt.pct(v.ci?.[1])}`, `n=${row?.metrics?.n_cases}`]};
  };
  const rows = [];
  const summary = [];
  ['gpt-6-luna', 'gpt-5.6-luna'].forEach(name => {
    rows.push({group: true, label: name});
    const dev = mk(name, 'Development, A3', m.evalRow('dev-A3', name), 'c1', false), r3 = mk(name, 'Held-out, r3', m.heldRow('r3', name), 'c1', true), hy = mk(name, 'Held-out, hybrid', m.heldRow('hybrid', name), 'c6', false);
    rows.push(dev, r3, hy);
    summary.push(`${name}: development ${fmt.pct(dev.value)}, held-out r3 ${fmt.pct(r3.value)}, held-out hybrid ${fmt.pct(hy.value)}`);
  });
  const lunaDev = rows[1], lunaH = rows[2];
  return figure({
    id: 'fig-dev-held', title: `gpt-6-luna with r3 scores ${fmt.pct(lunaH.value)} on ${m.heldRow('r3', 'gpt-6-luna')?.metrics?.n_cases} held-out cases against ${fmt.pct(lunaDev.value)} in development`, wide: true,
    takeaway: `Held-out interval ${fmt.pct(lunaH.ci[0])} to ${fmt.pct(lunaH.ci[1])} overlaps the development interval.`,
    summary: summary.join('. '),
    source: {data: 'report.json › evaluation.rows[agent-dev-A3/*, agent-heldout-H-r3|hybrid/*].metrics.behaviour_accuracy', files: ['experiments/eval/agent-dev-A3', 'experiments/eval/agent-heldout-H-r3', 'experiments/eval/agent-heldout-H-hybrid']},
    note: `Development is scored against ${goldOf(m.evalRow('dev-A3', 'gpt-6-luna')).label}; held-out against ${goldOf(m.heldRow('r3', 'gpt-6-luna')).label}, after three owner-approved post-run edits. Held-out is question-held-out, not evidence-independent: 25 of 31 cases reuse a development evidence id.`,
    table: () => ({caption: 'Behaviour accuracy, development and held-out', columns: ['Run', 'Rate', 'CI low', 'CI high', 'n'], rows: rows.filter(r => !r.group).map(r => [r.label, r.value, r.ci?.[0], r.ci?.[1], r.sub])}),
    draw: (host, c) => dotPlot(host, c, {rows, domain: [0.4, 1], ticks: [0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1], label: 'Behaviour accuracy with 95% intervals', axisTitle: 'Behaviour accuracy', rowH: c.compact ? 38 : 36})
  });
}

function pairedFigure(m) {
  const entries = m.paired;
  if (!entries.length) return null;
  const current = entries[0];
  const rows = [];
  const names = Object.keys(current.models);
  names.forEach(name => {
    rows.push({group: true, label: name});
    entries.forEach((entry, i) => {
      const x = entry.models[name];
      if (!x) return;
      const cross = x.ci95[0] <= 0;
      rows.push({
        label: `Gold ${entry.gold_version}`, sub: i === 0 ? 'current scoring' : 'earlier scoring', value: x.diff, ci: x.ci95, cross, hl: i === 0, cls: i === 0 ? 'c1' : 'c6',
        lines: [`${name}, gold ${entry.gold_version}`, `r3 minus hybrid: ${fmt.pts(x.diff)}`, `95% CI ${fmt.pts(x.ci95[0])} to ${fmt.pts(x.ci95[1])}`, `Better in ${x.better} cases, worse in ${x.worse}`, `n=${entry.n}, ${fmt.int(entry.resamples)} case-bootstrap resamples, seed ${entry.seed}`]
      });
    });
  });
  const a = current.models['gpt-6-luna'], b = current.models['gpt-5.6-luna'];
  return figure({
    id: 'fig-paired', title: `r3 minus hybrid is ${fmt.pts(a.diff)} for gpt-6-luna on ${current.n} held-out cases: ${a.ci95[0] <= 0 ? 'not demonstrated' : 'interval excludes zero'}`, wide: true,
    takeaway: `gpt-6-luna interval ${fmt.pts(a.ci95[0])} to ${fmt.pts(a.ci95[1])}. gpt-5.6-luna ${fmt.pts(b.diff)}, interval ${fmt.pts(b.ci95[0])} to ${fmt.pts(b.ci95[1])}. Registered rule: inconclusive. I make no claim that r3 improves held-out accuracy.`,
    summary: rows.filter(r => !r.group).map(r => `${r.lines[0]}: ${fmt.pts(r.value)}, CI ${fmt.pts(r.ci[0])} to ${fmt.pts(r.ci[1])}`).join('. '),
    source: {data: 'report.json › evaluation.paired[*].models', files: ['experiments/heldout/paired.txt', 'experiments/heldout/paired-v3.3.txt', 'experiments/heldout/paired-v3.2.txt']},
    note: `Same ${current.n} cases for both retrievers, ${fmt.int(current.resamples)} case-bootstrap resamples. Brass whiskers touch or cross zero. Grey rows show the same comparison under earlier gold versions.`,
    table: () => ({caption: 'Paired difference in behaviour accuracy (r3 minus hybrid)', columns: ['Model and gold version', 'Difference', 'CI low', 'CI high', 'Better', 'Worse'], rows: entries.flatMap(entry => Object.entries(entry.models).map(([name, x]) => [`${name}, gold ${entry.gold_version}`, x.diff, x.ci95[0], x.ci95[1], x.better, x.worse]))}),
    draw: (host, c) => dotPlot(host, c, {
      rows, domain: [-0.1, 0.4], ticks: [-0.1, 0, 0.1, 0.2, 0.3, 0.4], baseline: 0, refs: [{value: 0, label: 'no difference'}], format: (v, d) => `${v < 0 ? '\u2212' : ''}${Math.abs(100 * v).toFixed(0)}`, valueText: r => `${fmt.pts(r.value)}`,
      axisTitle: 'Points, r3 minus hybrid', label: 'Paired bootstrap differences', rowH: c.compact ? 38 : 36
    })
  });
}

function runQuantiles(m) {
  const by = new Map();
  m.trace.forEach(r => { if (!by.has(r.run_id)) by.set(r.run_id, []); by.get(r.run_id).push(r); });
  return [...by.entries()].map(([id, recs]) => {
    const {step, model} = runLabel(id);
    const q = key => { const v = recs.map(r => r[key]).filter(finite).sort((a, b) => a - b); return {p5: quantile(v, 0.05), p25: quantile(v, 0.25), p50: quantile(v, 0.5), p75: quantile(v, 0.75), p95: quantile(v, 0.95), max: v[v.length - 1], n: v.length}; };
    return {id, step, model, seconds: q('seconds'), cost: q('cost_usd')};
  }).sort((a, b) => a.step.localeCompare(b.step) || a.model.localeCompare(b.model));
}

function costLatencyFigures(m) {
  const runs = runQuantiles(m);
  if (!runs.length) return [];
  const a3 = runs.find(r => r.step === 'A3' && r.model === 'gpt-6-luna'), a1 = runs.find(r => r.step === 'A1' && r.model === 'gpt-6-luna');
  const rowsFor = (key, fmtv) => runs.map(r => ({label: `${r.step} \u00b7 ${r.model}`, q: r[key], hl: r === a3, cls: MODEL_CLS[r.model] || 'c6', lines: [`${r.step}, ${r.model}`, `Median ${fmtv(r[key].p50)}`, `Middle half ${fmtv(r[key].p25)} to ${fmtv(r[key].p75)}`, `5th to 95th percentile ${fmtv(r[key].p5)} to ${fmtv(r[key].p95)}`, `Slowest or costliest ${fmtv(r[key].max)}`, `${r[key].n} cases`]}));
  const secFmt = v => `${v.toFixed(1)} s`, costFmt = v => `$${v.toFixed(4)}`;
  const pairs = ['A1', 'A2', 'A3', 'A4', 'A5'].map(s => [runs.find(r => r.step === s && r.model === 'gpt-5.6-luna'), runs.find(r => r.step === s && r.model === 'gpt-6-luna')]).filter(([a, b]) => a && b);
  const pricier = pairs.length > 0 && pairs.every(([a, b]) => a.cost.p50 > b.cost.p50);
  const lat = figure({
    id: 'fig-latency', title: a3 && a1 ? `Median response time for gpt-6-luna rises from ${secFmt(a1.seconds.p50)} in A1 to ${secFmt(a3.seconds.p50)} in A3, because reranking adds a model call` : 'Response time per case',
    takeaway: a3 ? `Slowest 5% of A3 cases: ${secFmt(a3.seconds.p95)} or more.` : '',
    summary: runs.map(r => `${r.step} ${r.model}: median ${secFmt(r.seconds.p50)}, 95th percentile ${secFmt(r.seconds.p95)}`).join('. '),
    source: {data: 'report.json › agent.trace[*].seconds, grouped by run_id', files: ['experiments/runs/agent-dev-A1..A5/*.scores.jsonl']},
    note: 'Box: middle half of cases. Whiskers: 5th to 95th percentile. Tick: median.',
    table: () => ({caption: 'Seconds per case', columns: ['Run', 'p5', 'p25', 'median', 'p75', 'p95', 'max', 'cases'], rows: runs.map(r => [`${r.step} ${r.model}`, ...['p5', 'p25', 'p50', 'p75', 'p95', 'max', 'n'].map(k => r.seconds[k])])}),
    draw: (host, c) => boxStrip(host, c, {rows: rowsFor('seconds', secFmt), format: v => `${Math.round(v)}s`, axisTitle: 'Seconds per case', label: 'Response time distribution by run'})
  });
  const cost = figure({
    id: 'fig-cost', title: a3 && a1 ? `Median cost for gpt-6-luna goes from ${costFmt(a1.cost.p50)} per case in A1 to ${costFmt(a3.cost.p50)} in A3` : 'Estimated cost per case',
    takeaway: pricier ? 'gpt-5.6-luna costs more per case than gpt-6-luna in the compared runs.' : '',
    summary: runs.map(r => `${r.step} ${r.model}: median ${costFmt(r.cost.p50)}`).join('. '),
    source: {data: 'report.json › agent.trace[*].cost_usd, grouped by run_id', files: ['experiments/runs/agent-dev-A1..A5/*.scores.jsonl', 'specs/prices.yaml']},
    note: 'Estimates from list prices dated 30 October 2026, excluding cached-input discounts. Judge cost is separate.',
    table: () => ({caption: 'Estimated USD per case', columns: ['Run', 'p5', 'p25', 'median', 'p75', 'p95', 'max', 'cases'], rows: runs.map(r => [`${r.step} ${r.model}`, ...['p5', 'p25', 'p50', 'p75', 'p95', 'max', 'n'].map(k => r.cost[k])])}),
    draw: (host, c) => boxStrip(host, c, {rows: rowsFor('cost', costFmt), format: v => `$${v.toFixed(3)}`, axisTitle: 'US dollars per case (estimate)', label: 'Cost distribution by run'})
  });
  return [lat, cost];
}

function modelFigures(m) {
  const names = ['gpt-4.1-mini', 'gpt-5.4-mini', 'gpt-5.6-luna', 'gpt-6-luna', 'gpt-6-sol', 'gpt-6.1-terra'];
  const g0 = names.map(n => ({name: n, x: m.answerRow('G0', n)?.metrics, g1: m.answerRow('G1', n)?.metrics})).filter(r => r.x);
  if (!g0.length) return [];
  const top = g0.reduce((a, r) => r.x.behavior_accuracy > a.x.behavior_accuracy ? r : a, g0[0]);
  const costly = g0.reduce((a, r) => r.x.cost_per_case_usd > a.x.cost_per_case_usd ? r : a, g0[0]);
  const scat = figure({
    id: 'fig-models', title: `${top.name} scores highest at ${fmt.pct(top.x.behavior_accuracy)} on 30 answer-only cases, at $${top.x.cost_per_case_usd} per case`,
    takeaway: `${costly.name} costs $${costly.x.cost_per_case_usd} per case and scores ${fmt.pct(costly.x.behavior_accuracy)}. One case is 3.3 points.`,
    summary: g0.map(r => `${r.name}: ${fmt.pct(r.x.behavior_accuracy)} at $${r.x.cost_per_case_usd} per case`).join('. '),
    source: {data: 'report.json › answers.rows[answer-dev-G0/*].metrics.{behavior_accuracy,cost_per_case_usd}', files: ['experiments/runs/answer-dev-G0-SUMMARY.md']},
    note: 'Answer-only study: the right evidence is placed first (oracle context), 30 development cases, earlier metric definitions. It compares models, not the full agent.',
    table: () => ({caption: 'Answer-only study G0', columns: ['Model', 'Behaviour accuracy', 'Cost per case (USD)', 'Median seconds', 'Valid output rate'], rows: g0.map(r => [r.name, r.x.behavior_accuracy, r.x.cost_per_case_usd, r.x.latency_p50_s, r.x.valid_rate])}),
    draw: (host, c) => scatter(host, c, {
      points: g0.map(r => ({label: r.name, x: r.x.cost_per_case_usd, y: r.x.behavior_accuracy, hl: r === top, cls: MODEL_CLS[r.name] || 'c6', lines: [r.name, `Behaviour accuracy: ${fmt.pct(r.x.behavior_accuracy)}`, `Cost per case: $${r.x.cost_per_case_usd}`, `Median latency: ${fmt.seconds(r.x.latency_p50_s)}`, `Valid output: ${fmt.pct(r.x.valid_rate)}`]})),
      logX: true, xDomain: [0.0003, 0.02], xTicks: [0.0005, 0.001, 0.002, 0.005, 0.01, 0.02], xFormat: v => `$${v}`, yDomain: [0.6, 1], yFormat: v => fmt.pct(v, 0), xTitle: 'Cost per case, US dollars (log scale)', yTitle: 'Behaviour accuracy', label: 'Cost against behaviour accuracy by model'
    })
  });
  const gap = g0.filter(r => r.g1).map(r => ({r, d: r.x.behavior_accuracy - r.g1.behavior_accuracy}));
  const lo = Math.min(...gap.map(g => g.d)), hi = Math.max(...gap.map(g => g.d));
  const dumb = figure({
    id: 'fig-oracle', title: `Oracle evidence lifts behaviour accuracy by ${(100 * lo).toFixed(1)} to ${(100 * hi).toFixed(1)} points across ${gap.length} models on 30 development cases`,
    takeaway: 'The spread between models is smaller than this gap.',
    summary: gap.map(g => `${g.r.name}: retrieved ${fmt.pct(g.r.g1.behavior_accuracy)}, oracle ${fmt.pct(g.r.x.behavior_accuracy)}`).join('. '),
    source: {data: 'report.json › answers.rows[answer-dev-G0|G1/*].metrics.behavior_accuracy', files: ['experiments/runs/answer-dev-G0-SUMMARY.md', 'experiments/runs/answer-dev-G1-SUMMARY.md']},
    note: '30 development cases, answer-only study. This study motivated the retrieval work in chapter 3.',
    table: () => ({caption: 'Behaviour accuracy: retrieved vs oracle evidence', columns: ['Model', 'Retrieved (G1)', 'Oracle (G0)', 'Gain'], rows: gap.map(g => [g.r.name, g.r.g1.behavior_accuracy, g.r.x.behavior_accuracy, +g.d.toFixed(3)])}),
    draw: (host, c) => dumbbell(host, c, {
      rows: gap.map(g => ({label: g.r.name, points: [{key: 'g1', label: 'Retrieved', value: g.r.g1.behavior_accuracy, cls: 'c6'}, {key: 'g0', label: 'Oracle evidence', value: g.r.x.behavior_accuracy, cls: 'brass'}], lines: [g.r.name, `Retrieved: ${fmt.pct(g.r.g1.behavior_accuracy)}`, `Oracle evidence: ${fmt.pct(g.r.x.behavior_accuracy)}`, `Gain: ${fmt.pts(g.d)}`]})),
      domain: [0.4, 1], format: v => fmt.pct(v, 0), label: 'Retrieved against oracle evidence'
    })
  });
  return [scat, dumb];
}

function errorFigure(m) {
  const counts = m.section('evaluation').errors?.counts;
  if (!counts) return null;
  const total = m.trace.length;
  const label = {behavior_mismatch: 'Behaviour mismatch', n_ungrounded_numbers: 'Ungrounded number warnings', tool_errors: 'Tool errors', invalid_output: 'Invalid output', operational_failure: 'Operational failure'};
  const rows = Object.entries(label).map(([key, name]) => ({label: name, value: counts[key] ?? 0, cls: key === 'operational_failure' ? 'c1' : 'c4', hl: key === 'behavior_mismatch', lines: [name, `${fmt.int(counts[key] ?? 0)} across ${fmt.int(total)} case records`]}));
  return figure({
    id: 'fig-errors', title: `Behaviour mismatches are ${fmt.int(counts.behavior_mismatch)} of ${fmt.int(total)} case records pooled over all runs; operational failures are ${fmt.int(counts.operational_failure ?? 0)}`,
    takeaway: 'A mismatch means the status differed from the label, not that the answer was wrong.',
    summary: rows.map(r => `${r.label}: ${r.value}`).join('. '),
    source: {data: 'report.json › evaluation.errors.counts', files: ['experiments/eval/agent-dev-A1..A5/*.cases.jsonl']},
    note: 'Counts pool all eleven runs, including the early ones, so they overstate the current agent. Warnings can repeat inside one case.',
    table: () => ({caption: 'Pooled score-record counts', columns: ['Category', 'Count'], rows: rows.map(r => [r.label, r.value])}),
    draw: (host, c) => dotPlot(host, c, {rows, mode: 'bar', domain: [0, 500], ticks: [0, 100, 200, 300, 400, 500], format: v => fmt.int(v), valueText: r => fmt.int(r.value), axisTitle: 'Case records', label: 'Pooled error counts'})
  });
}

export function renderEvaluation(m, ctx) {
  const a3 = m.evalRow('dev-A3', 'gpt-6-luna'), r3 = m.heldRow('r3', 'gpt-6-luna');
  const ch = chapter({
    id: 'evaluation', no: 5, eyebrow: 'Answers and evaluation',
    title: a3 && r3 ? `gpt-6-luna scores ${fmt.pct(metricOf(a3.metrics.behaviour_accuracy).rate)} behaviour accuracy on ${fmt.int(a3.metrics.n_cases)} development cases and ${fmt.pct(metricOf(r3.metrics.behaviour_accuracy).rate)} on ${fmt.int(r3.metrics.n_cases)} held-out cases` : 'Answer evaluation',
    bullets: [
      'Gold set: 268 cases, 237 development and 31 held out.',
      `Development scored on ${goldOf(a3).label}; held-out on ${goldOf(r3).label}.`,
      'Most labels began as AI drafts; the owner reviewed 45 gold cases.',
      'An AI judge scores claim support.'
    ]
  });
  const stats = el('div', 'pr-stats');
  if (a3) stats.append(stat({value: metricOf(a3.metrics.behaviour_accuracy).rate, format: v => fmt.pct(v), label: 'Behaviour accuracy, development', note: `Run A3, gpt-6-luna, n=${a3.metrics.n_cases}`, tone: 'brass', src: 'report.json › evaluation.rows[agent-dev-A3/gpt-6-luna].metrics.behaviour_accuracy'}));
  if (r3) stats.append(stat({value: metricOf(r3.metrics.behaviour_accuracy).rate, format: v => fmt.pct(v), label: 'Behaviour accuracy, held-out r3', note: `gpt-6-luna, n=${r3.metrics.n_cases}. Interval ${fmt.pct(metricOf(r3.metrics.behaviour_accuracy).ci?.[0])} to ${fmt.pct(metricOf(r3.metrics.behaviour_accuracy).ci?.[1])}.`, src: 'report.json › evaluation.rows[agent-heldout-H-r3/gpt-6-luna]'}));
  if (m.paired[0]) stats.append(stat({value: m.paired[0].models['gpt-6-luna'].diff, format: v => fmt.pts(v), label: 'r3 minus hybrid, held-out', note: `Interval ${fmt.pts(m.paired[0].models['gpt-6-luna'].ci95[0])} to ${fmt.pts(m.paired[0].models['gpt-6-luna'].ci95[1])}. Inconclusive.`, tone: 'warn', src: 'report.json › evaluation.paired[0].models[gpt-6-luna]'}));
  if (a3) stats.append(stat({value: a3.metrics.latency_p50_s, format: v => `${v.toFixed(1)} s`, label: 'Median response time', note: `95th percentile ${fmt.seconds(a3.metrics.latency_p95_s)}. ${fmt.money(a3.metrics.cost_per_case_usd)} per case.`, src: 'report.json › evaluation.rows[agent-dev-A3/gpt-6-luna].metrics.{latency_p50_s,latency_p95_s,cost_per_case_usd}'}));
  ch.body.append(stats);

  const dev = section(a3 ? `I chose configurations on ${fmt.int(a3.metrics.n_cases)} development cases, so these figures carry selection bias` : 'Development results', ['Development results do not estimate performance on unseen questions.']);
  const hl = headlineFigure(m), pr = progressionFigure(m);
  if (hl) dev.append(hl.root);
  dev.append(pr.root, familyHeat(m).root);
  ch.body.append(dev);

  const pa = m.paired[0]?.models?.['gpt-6-luna'];
  const held = section(r3 ? `Held-out: r3 scores ${fmt.pct(metricOf(r3.metrics.behaviour_accuracy).rate)} on ${fmt.int(r3.metrics.n_cases)} cases${pa ? `, and the gain over hybrid is ${pa.ci95[0] <= 0 ? 'not demonstrated' : 'outside the interval around zero'}` : ''}` : 'Held-out results', ['One run on a frozen configuration, scored afterwards.', 'Comparison: r3 against hybrid retrieval.']);
  held.append(devHeldFigure(m).root);
  const paired = pairedFigure(m);
  if (paired) held.append(paired.root);
  const notes = ctx.disclosures || [];
  if (notes.length) held.append(details('Gold versions, post-run edits and held-out limits', ...notes.map(text => el('p', 'pr-small', text))));
  ch.body.append(held);

  const cl = costLatencyFigures(m);
  const ops = section(a3 ? `A3 with gpt-6-luna costs ${fmt.money(a3.metrics.cost_per_case_usd)} per case at a median ${fmt.seconds(a3.metrics.latency_p50_s)}` : 'Cost, latency and models', ['Cost from list prices; latency is measured per case.', 'Model comparison is answer-only, with oracle evidence.']);
  
  if (cl.length) ops.append(grid('pr-split', cl[0].root, cl[1].root));
  const mf = modelFigures(m);
  if (mf.length) ops.append(grid('pr-split', mf[0].root, mf[1].root));
  const err = errorFigure(m);
  if (err) ops.append(err.root);
  ch.body.append(ops);
  return ch.root;
}
