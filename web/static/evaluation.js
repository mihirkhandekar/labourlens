// Offline presentation only: render the builder's curated numeric projection.
const node = (tag, className, text) => {
  const result = document.createElement(tag);
  if (className) result.className = className;
  if (text !== undefined) result.textContent = text;
  return result;
};
const finite = value => typeof value === 'number' && Number.isFinite(value);
const number = value => finite(value) ? value.toLocaleString(undefined, {maximumFractionDigits: 3}) : 'Not recorded';
const percent = value => finite(value) ? `${(100 * value).toFixed(1)}%` : 'Not recorded';
const money = value => finite(value) ? `$${value.toFixed(5)}` : 'Not recorded';
const human = value => String(value).replaceAll('_', ' ').replace(/^./, c => c.toUpperCase());
const rowsOf = section => Array.isArray(section?.rows) ? section.rows : [];
const svgNode = (tag, attrs = {}, text) => {
  const result = document.createElementNS('http://www.w3.org/2000/svg', tag);
  Object.entries(attrs).forEach(([key, value]) => result.setAttribute(key, String(value)));
  if (text !== undefined) result.textContent = text;
  return result;
};
const metric = (value, fallbackN, fallbackCI) => {
  if (finite(value)) return {rate: value, n: fallbackN, ci95: fallbackCI};
  if (value && typeof value === 'object') return {
    rate: value.rate ?? value.value,
    n: value.n ?? fallbackN,
    ci95: value.ci95 ?? fallbackCI
  };
  return {rate: null, n: fallbackN};
};
const validCI = ci => Array.isArray(ci) && ci.length === 2 && ci.every(finite) && ci[0] >= 0 && ci[1] <= 1 && ci[0] <= ci[1];

function rateBar(label, measurement, adverse = false, unit = 'cases') {
  const root = node('div', 'eval-metric');
  const heading = node('div', 'eval-metric-heading');
  heading.append(node('strong', '', label), node('span', '', percent(measurement.rate)));
  root.append(heading);
  const ci = validCI(measurement.ci95) ? measurement.ci95 : null;
  const n = finite(measurement.n) ? `n=${number(measurement.n)} ${unit}` : 'n not recorded';
  const direction = adverse ? 'Lower is better' : 'Higher is better';
  const uncertainty = ci ? `95% CI ${percent(ci[0])}–${percent(ci[1])}` : '95% CI not recorded';
  if (finite(measurement.rate) && measurement.rate >= 0 && measurement.rate <= 1) {
    const color = adverse ? '#a04732' : '#146b69';
    const x = value => 10 + value * 300;
    const chart = svgNode('svg', {viewBox: '0 0 320 36', width: '100%', height: 36, class: 'eval-bar', role: 'img', 'aria-label': `${label}: ${percent(measurement.rate)}; ${n}; ${uncertainty}; ${direction}.`});
    chart.append(svgNode('title', {}, `${label}: ${percent(measurement.rate)}. ${uncertainty}. ${n}.`));
    chart.append(svgNode('rect', {x: 10, y: 10, width: 300, height: 12, rx: 3, fill: '#e5ebee'}));
    chart.append(svgNode('rect', {x: 10, y: 10, width: measurement.rate * 300, height: 12, rx: 3, fill: color, opacity: 0.72}));
    if (ci) {
      chart.append(svgNode('line', {x1: x(ci[0]), y1: 16, x2: x(ci[1]), y2: 16, stroke: '#172b38', 'stroke-width': 2}));
      ci.forEach(value => chart.append(svgNode('line', {x1: x(value), x2: x(value), y1: 7, y2: 25, stroke: '#172b38', 'stroke-width': 2})));
    }
    chart.append(svgNode('circle', {cx: x(measurement.rate), cy: 16, r: 4, fill: color, stroke: '#fff', 'stroke-width': 1.5}));
    root.append(chart);
  }
  root.append(node('p', 'eval-caption', `${direction}. ${n}. ${uncertainty}.`));
  return root;
}

function notice(panel, text) {
  panel.append(node('p', 'eval-notice note', text));
}
function empty(panel, text) {
  panel.append(node('div', 'empty-state', text));
}
function provenance(parent, row) {
  const paths = Array.isArray(row.provenance) ? row.provenance : [];
  if (!paths.length) return;
  const details = node('details', 'eval-provenance');
  details.append(node('summary', '', 'Evidence files'));
  const list = node('ul', 'detail-list');
  paths.forEach(path => list.append(node('li', '', path)));
  details.append(list);
  parent.append(details);
}
function operational(row) {
  const metrics = row.metrics || {};
  const list = node('dl', 'eval-operational');
  [
    ['Median latency', finite(metrics.latency_p50_s) ? `${number(metrics.latency_p50_s)} s` : 'Not recorded'],
    ['95th percentile latency', finite(metrics.latency_p95_s) ? `${number(metrics.latency_p95_s)} s` : 'Not recorded'],
    ['Generation cost / case', money(metrics.cost_per_case_usd)],
    ['AI judge cost / run', money(metrics.judge_cost_total_usd)]
  ].forEach(([label, value]) => {
    const pair = node('div');
    pair.append(node('dt', '', label), node('dd', '', value));
    list.append(pair);
  });
  return list;
}
function familyTable(rows, security = false) {
  const families = [...new Set(rows.flatMap(row => Object.keys(row.strata || {})))].sort();
  if (!families.length) return node('p', 'eval-caption', 'No per-family results recorded.');
  const wrap = node('div', 'table-scroll');
  const table = node('table', 'data-table eval-family-table');
  table.append(node('caption', '', security ? 'Pass rate by threat category, with scored cases per cell.' : 'Behaviour accuracy by research family, with cases per cell. Darker cells are higher.'));
  const head = node('thead');
  const heading = node('tr');
  const corner = node('th', '', security ? 'Threat category' : 'Research family');
  corner.scope = 'col';
  heading.append(corner);
  rows.forEach(row => {
    const cell = node('th', '', row.label || row.id || 'Configuration');
    cell.scope = 'col';
    heading.append(cell);
  });
  head.append(heading);
  const body = node('tbody');
  families.forEach(family => {
    const tr = node('tr');
    const label = node('th', '', human(family));
    label.scope = 'row';
    tr.append(label);
    rows.forEach(row => {
      const entry = row.strata?.[family];
      const n = entry?.n_scored ?? entry?.n;
      const rate = security ? metric(entry?.pass_rate ?? (finite(entry?.passed) && finite(n) && n > 0 ? entry.passed / n : null), n) : metric(entry?.behaviour_accuracy, n);
      const cell = node('td', 'eval-family-cell', `${percent(rate.rate)} · ${finite(rate.n) ? `n=${number(rate.n)}` : 'n not recorded'}`);
      if (finite(rate.rate) && rate.rate >= 0 && rate.rate <= 1) {
        cell.dataset.level = String(Math.min(4, Math.floor(rate.rate * 5)));
      }
      if (security && entry) {
        cell.append(node('small', 'eval-caption', ` Not exercised: ${number(entry.not_exercised)}`));
        if (Array.isArray(entry.useful) && entry.useful.length === 2 && entry.useful.every(finite)) {
          cell.append(node('small', 'eval-caption', ` Useful answers: ${number(entry.useful[0])}/${number(entry.useful[1])}`));
        }
      }
      tr.append(cell);
    });
    body.append(tr);
  });
  table.append(head, body);
  wrap.append(table);
  return wrap;
}

export function renderEvaluation(panel, report) {
  const section = report?.evaluation || {};
  const rows = rowsOf(section);
  const judges = [...new Set(rows.map(row => row.judge).filter(Boolean))];
  notice(panel, `Development results. AI-drafted gold. AI judge${judges.length ? ': ' + judges.join(', ') : ''}. Not human reviewed.`);
  if (!rows.length) return empty(panel, 'No evaluation metrics recorded. A missing result is not a zero score.');
  const grid = node('div', 'eval-model-grid');
  rows.forEach(row => {
    const metrics = row.metrics || {};
    const card = node('article', 'card eval-model-card');
    card.append(node('h3', 'eval-card-heading', row.label || row.id || 'Recorded configuration'));
    card.append(node('p', 'eval-caption', `${number(metrics.n_cases)} evaluation cases`));
    const measurements = [
      ['Behaviour accuracy', metric(metrics.behaviour_accuracy, metrics.n_cases), false, 'cases'],
      ['False-answer rate', metric(metrics.false_answer_rate), true, 'eligible cases'],
      ['Claim support', metric(metrics.claim_supported_rate, metrics.claims_judged), false, 'claims'],
      ['Reference contradiction', metric(metrics.answers_contradicting_a_reference_fact), true, 'judged answers'],
      ['Reference fact coverage', metric(metrics.fact_coverage, row.denominators?.fact_coverage ?? metrics.facts_total ?? metrics.facts_judged), false, 'reference facts']
    ];
    measurements.forEach(([label, value, adverse, unit]) => card.append(rateBar(label, value, adverse, unit)));
    card.append(operational(row));
    provenance(card, row);
    grid.append(card);
  });
  panel.append(grid);
  const definitions = node('details', 'eval-definitions');
  definitions.append(node('summary', '', 'Metric definitions'));
  const list = node('ul', 'detail-list');
  [
    'Behaviour accuracy: share of responses that give the expected answer or abstain as expected. It does not check every claim.',
    'False-answer rate: false answers among the eligible cases that were not over-abstained, not among all cases.',
    'Claim support: share of judged claims fully supported by the evidence. Partially supported claims do not count.',
    'Reference contradiction: share of judged answers that contradict at least one reference fact. It is counted per answer, not per claim.',
    'Reference fact coverage: share of expected facts covered across judged answers, measured against the AI-drafted reference.',
    'Intervals are recorded case-bootstrap 95% intervals. Small strata and overlapping intervals do not support a claim that one configuration is better.',
    'Generation cost per case and judge cost per run are recorded separately. Missing costs and latency percentiles are left blank.',
    'Bars use a 0–100% scale. Dots mark rates and whiskers mark 95% intervals. Denominators differ by metric (cases, claims, reference facts). Scalar metrics have no interval.'
  ].forEach(text => list.append(node('li', '', text)));
  definitions.append(list);
  panel.append(definitions, node('h3', '', 'Results by research family'), familyTable(rows));
}

export function renderSecurity(panel, report) {
  const rows = rowsOf(report?.security);
  notice(panel, 'Development threat suite with deterministic pass criteria. Naive configurations turn off the application defences and serve as baselines only.');
  if (!rows.length) return empty(panel, 'No security measurements recorded.');
  const groups = new Map();
  rows.forEach(row => {
    const label = row.label || row.id?.split('/').pop() || 'Configuration';
    const base = label.replace(/\+naive$/, '');
    if (!groups.has(base)) groups.set(base, []);
    groups.get(base).push({...row, label, naive: /\+naive$/.test(label)});
  });
  const grid = node('div', 'eval-model-grid');
  groups.forEach((variants, model) => {
    const card = node('article', 'card eval-model-card eval-security-group');
    card.append(node('h3', 'eval-card-heading', model));
    variants.sort((a, b) => Number(a.naive) - Number(b.naive)).forEach(row => {
      const metrics = row.metrics || {};
      const n = metrics.n_scored ?? metrics.n_cases;
      const rate = metric(metrics.pass_rate, n, metrics.pass_rate_ci95 ?? metrics.ci95);
      card.append(rateBar(row.naive ? 'Naive baseline' : 'Defended configuration', rate, false, 'scored cases'));
      const detail = [
        `Passed: ${number(metrics.passed)}/${number(n)}`,
        `Canary leaks: ${number(metrics.canary_leaks)}`,
        `Canary caveats: ${number(metrics.canary_caveat)}`,
        `Median latency: ${finite(metrics.latency_p50_s) ? `${number(metrics.latency_p50_s)} s` : 'not recorded'}`,
        `Run cost: ${money(metrics.cost_usd)}`
      ];
      card.append(node('p', 'eval-caption', detail.join(' · ')));
      provenance(card, row);
    });
    if (!variants.some(row => row.naive)) card.append(node('p', 'eval-caption', 'No naive baseline recorded for this model, so no paired comparison is shown.'));
    grid.append(card);
  });
  panel.append(grid, node('p', 'eval-caption', 'Whiskers appear only where a pass-rate interval is recorded. A pass rate of 100% does not mean zero risk. A safe refusal counts as a pass even when it is not a useful answer.'), node('h3', '', 'Results by threat category'), familyTable(rows, true));
}

// Optional replacement for scalar/nested metric dumps in other experiment sections.
export function renderComparison(panel, report, key) {
  if (key === 'evaluation') return renderEvaluation(panel, report);
  if (key === 'security') return renderSecurity(panel, report);
  const rows = rowsOf(report?.[key]);
  if (!rows.length) return empty(panel, 'No comparison measurements recorded.');
  const grid = node('div', 'eval-model-grid');
  rows.forEach(row => {
    const card = node('article', 'card eval-model-card');
    card.append(node('h3', 'eval-card-heading', row.label || row.id || 'Configuration'));
    const list = node('dl', 'eval-operational');
    Object.entries(row.metrics || {}).forEach(([name, value]) => {
      if (value && typeof value === 'object' && finite(value.rate)) {
        card.append(rateBar(human(name), metric(value), /error|false|unsupported|contradict/.test(name)));
      } else if (finite(value) || typeof value === 'boolean') {
        const pair = node('div');
        pair.append(node('dt', '', human(name)), node('dd', '', typeof value === 'boolean' ? (value ? 'Yes' : 'No') : number(value)));
        list.append(pair);
      }
    });
    card.append(list);
    provenance(card, row);
    grid.append(card);
  });
  panel.append(grid);
}
