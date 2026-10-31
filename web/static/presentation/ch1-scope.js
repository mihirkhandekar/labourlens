import {el, fmt, finite, figure, dotPlot} from '../charts.js';
import {chapter, section, grid, bezel, stat, callout, chips, evi} from './ui.js';
import {FAMILIES, FAMILY_LABEL} from './model.js';

const CARD_ORDER = ['unemployment_resident_sa', 'unemployment_overall_sa', 'vacancy_ratio', 'job_vacancy_rate', 'retrenchments', 'reentry_6m'];
const UNIT_TEXT = {percent: 'percent', ratio: 'ratio', persons: 'persons'};
const ADJ_TEXT = {seasonally_adjusted: 'seasonally adjusted', not_adjusted: 'not adjusted', not_applicable: 'no adjustment', unspecified: 'adjustment not stated'};

function cardFormat(card) {
  if (card.unit === 'percent') return v => `${v.toFixed(1)}%`;
  if (card.unit === 'ratio') return v => v.toFixed(2);
  return v => fmt.int(v);
}
function changeText(card) {
  if (!finite(card.change)) return 'change not recorded';
  if (card.change === 0) return 'no change on previous quarter';
  const unit = card.change_unit === 'percentage_points' ? ' pts' : card.unit === 'persons' ? ' persons' : '';
  const digits = card.unit === 'ratio' ? 2 : card.unit === 'persons' ? 0 : 1;
  return `${fmt.signed(card.change, digits)}${unit} on previous quarter`;
}

function periodStrip(m) {
  const periods = m.periods();
  const root = el('div', 'pr-periods');
  root.setAttribute('role', 'img');
  root.setAttribute('aria-label', `Analysis window: ${periods.length} quarters, ${fmt.quarter(periods[0])} to ${fmt.quarter(periods[periods.length - 1])}.`);
  periods.forEach((period, i) => {
    const cell = el('div', 'pr-period');
    cell.append(el('span', 'pr-period-q', `Q${period.slice(-1)}`), el('span', 'pr-period-y', period.slice(2, 4)));
    cell.dataset.edge = i === 0 ? 'first' : i === periods.length - 1 ? 'last' : '';
    root.append(cell);
  });
  return root;
}

function pipeline() {
  const steps = [
    ['Question', 'Checked for length and instruction-like text.'],
    ['Plan', 'A model proposes up to three read-only tool calls.'],
    ['Evidence', 'Passages and validated statistics come back with labels.'],
    ['Calculate', 'Code does the arithmetic. The model does not.'],
    ['Answer', 'Structured claims, each with a verbatim quote.'],
    ['Check', 'Quotes, labels and status are validated before display.']
  ];
  const ol = el('ol', 'pr-pipeline');
  steps.forEach(([title, text], i) => {
    const li = el('li', 'pr-pipe-step');
    li.append(el('span', 'pr-pipe-no', String(i + 1)), el('strong', '', title), el('span', '', text));
    ol.append(li);
  });
  return ol;
}

export function renderScope(m, ctx) {
  const nQ = m.periods().length;
  const nDocs = (m.section('sources').metrics?.by_type?.report_pdf || 0) + (m.section('sources').metrics?.by_type?.release_html || 0);
  const ch = chapter({
    id: 'scope', no: 1, eyebrow: 'Scope',
    title: `The analysis window is ${nQ} quarters, ${fmt.quarter(m.scope[0])} to ${fmt.quarter(m.scope[1])}, over four datasets and ${nDocs} MOM documents`,
    bullets: ['Users: policy researchers comparing statistics with MOM commentary.', 'Output: cited answer, clarification, abstention or refusal.', 'The evaluation measures where that behaviour fails.']
  });
  const [from, to] = m.scope;

  const scopeCard = bezel(
    el('p', 'pr-kicker', 'Analysis window'),
    el('p', 'pr-big-text', `${fmt.quarter(from)} to ${fmt.quarter(to)}`),
    periodStrip(m),
    el('p', 'pr-small', 'Earlier documents are context only. Requests outside the window must abstain. Dataset coverage varies by quarter; checked at ingestion.'),
    evi('report.json › summary.scope · charts[].points[].period')
  );
  const types = m.section('sources').metrics?.by_type || {};
  const sourceCard = bezel(
    el('p', 'pr-kicker', 'Sources'),
    el('p', 'pr-big-text', 'Datasets and MOM documents'),
    chips([
      {label: `${fmt.int(types.dataset_csv)} dataset snapshots`, cls: 'f-c1'},
      {label: `${fmt.int(types.report_pdf)} report PDFs`, cls: 'f-c2'},
      {label: `${fmt.int(types.release_html)} release pages`, cls: 'f-c3'}
    ]),
    el('p', 'pr-small', 'Datasets (data.gov.sg): resident unemployment, vacancies per unemployed person, retrenched employees, employment change by sector. Text: MOM labour-market reports Q3 2025 to Q2 2026 and the Q2 2026 advance release.'),
    evi('report.json › sources.metrics.by_type')
  );
  ch.body.append(grid('pr-split', scopeCard.root, sourceCard.root));

  // Latest figures, with the series definition next to every number.
  const kpiBlock = section(`${CARD_ORDER.length} headline series, latest value ${fmt.quarter(to)}`, ['Each card carries population, seasonal adjustment and unit.', 'Unemployment rates with different definitions are not comparable.']);
  const kpis = el('div', 'pr-kpis');
  CARD_ORDER.map(id => m.cards.find(card => card.card_id === id)).filter(Boolean).forEach(card => {
    const unit = UNIT_TEXT[card.unit] || card.unit;
    kpis.append(stat({
      value: card.value, format: cardFormat(card), label: card.label,
      note: `${changeText(card)}. ${card.population === 'not_applicable' ? '' : `${card.population} · `}${ADJ_TEXT[card.adjustment] || card.adjustment} · ${unit}`,
      src: `report.json › summary.cards[${card.card_id}] · observation ${card.observation_id}`
    }));
  });
  kpiBlock.append(kpis);
  ch.body.append(kpiBlock);

  // Question families
  const familyBlock = section(`The gold set covers ${FAMILIES.length} question families`, ['Counts are the development split scored in run A3.']);
  const a3 = m.evalRow('dev-A3', 'gpt-6-luna');
  const strata = a3?.strata || {};
  const rows = FAMILIES.filter(f => strata[f]).map(f => ({label: FAMILY_LABEL[f], value: strata[f].n, cls: 'c1', lines: [FAMILY_LABEL[f], `${strata[f].n} development cases`]}));
  const total = rows.reduce((sum, r) => sum + r.value, 0);
  const biggest = rows.reduce((a, b) => b.value > a.value ? b : a, rows[0]);
  const smallest = rows.reduce((a, b) => b.value < a.value ? b : a, rows[0]);
  const fig = figure({
    id: 'fig-families', title: `${fmt.int(total)} development cases split across ${rows.length} question families, from ${smallest.value} to ${biggest.value} per family`,
    takeaway: `${biggest.label} is the largest group (${biggest.value}); ${smallest.label} the smallest (${smallest.value}). Small families give wide intervals.`,
    summary: rows.map(r => `${r.label}: ${r.value} cases`).join('. '),
    source: {data: 'report.json › evaluation.rows[agent-dev-A3/gpt-6-luna].strata[*].n', files: ['experiments/eval/agent-dev-A3/gpt-6-luna.metrics.json']},
    table: () => ({caption: 'Development cases per family', columns: ['Family', 'Cases'], rows: rows.map(r => [r.label, r.value])}),
    draw: (host, c) => dotPlot(host, c, {
      rows: rows.map(r => ({...r, hl: r === biggest})), mode: 'bar', domain: [0, Math.max(80, ...rows.map(r => r.value))], format: v => String(Math.round(v)),
      valueText: r => String(r.value), label: 'Cases per family', axisTitle: 'Cases'
    })
  });
  const outcomes = el('div', 'pr-outcomes pr-reveal');
  outcomes.append(el('h5', 'pr-mini-title', 'Four outcomes'));
  [['Answered', 'Cited claims, plus a calculation where needed.'], ['Abstained', 'Evidence does not support an answer.'], ['Clarify', 'Series or period left open by the question.'], ['Refused', 'Request is out of bounds.']].forEach(([name, text]) => {
    const row = el('div', 'pr-outcome');
    row.append(el('strong', '', name), el('span', '', text));
    outcomes.append(row);
  });
  familyBlock.append(grid('pr-split is-wide-left', fig.root, outcomes));
  ch.body.append(familyBlock);

  // How an answer is made + out of scope
  const flow = section('Code does the arithmetic; a validator checks quotes, labels and status before display', ['Model proposes up to three read-only tool calls.', 'Tools return labelled passages and validated statistics.']);
  flow.append(pipeline());
  ch.body.append(flow);

  ch.body.append(callout({
    tone: 'note', title: 'Out of scope',
    items: ['Forecasting', 'Causal claims the data cannot support', 'Unrestricted web research', 'Advice about an individual\u2019s employment'],
    src: 'CLAUDE.md › Approved scope · docs/system-card.md › Intended use'
  }));
  return ch.root;
}
