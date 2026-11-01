// Overview page: hero, how an answer is made, outcomes, series explorer, sources, limits.
// Numbers come from report.json only. Copy that states a fact about the design is plain text.
import {el, add, icon, cta, button, finite, fmtUnit, signed, human, CHANGE_UNIT} from './dom.js';
import {lineChart, sparkline} from './chart.js';
import {FAMILIES} from './workbench.js';

export function renderHome(root, report, {go, tryQuestion}) {
  // ---------- hero ----------
  const hero = el('section', 'hero'); hero.id = 'top';
  const wrap = el('div', 'container hero-grid');
  const copy = el('div', 'hero-copy');
  add(copy, el('h1', 'hero-title', 'Singapore labour statistics, with a source for every number.'),
    el('p', 'lead', 'Ask about unemployment, vacancies and retrenchments, 2024 to 2026. Answers cite MOM data or say nothing is published.'),
    el('p', 'byline', 'Built by Mihir Khandekar, for a GenAI Engineer assessment.'),
    add(el('div', 'hero-cta'), cta('Open the workbench', '/workbench', 'btn btn-primary', 'arrow-ur'), cta('Watch the presentation', '/deck', 'btn', 'arrow-r')));
  wrap.append(copy);

  const cards = Array.isArray(report?.summary?.cards) ? report.summary.cards : [];
  const seriesById = new Map((Array.isArray(report?.charts) ? report.charts : []).map(c => [c.id, c]));
  if (cards.length) wrap.append(specimen(cards, seriesById));
  else wrap.append(add(el('div', 'bezel hero-specimen'), add(el('div', 'bezel-core'), el('p', 'muted', 'The figures could not be loaded. The workbench is unaffected.'))));
  hero.append(wrap);
  root.append(hero);

  // ---------- how an answer is made ----------
  const how = section('how', 'How an answer is made', null);
  const steps = [
    ['Question', 'Checks that the period and series are clear.'],
    ['Search', 'Finds report passages and statistics.'],
    ['Calculate', 'Changes are computed in code.'],
    ['Cited answer', 'Every claim shows its source.']
  ];
  const dl = el('dl', 'how-list reveal');
  steps.forEach(([title, body]) => dl.append(el('dt', '', title), el('dd', '', body)));
  how.body.append(dl);
  root.append(how.node);

  // ---------- outcomes ----------
  const outcomes = section('outcomes', 'Four possible outcomes', null);
  const oc = el('ul', 'outcome-list reveal');
  [
    ['answered', 'check', 'Answered', 'Answer with citations.'],
    ['abstained', 'minus', 'No answer', 'The data does not cover it.'],
    ['clarify', 'help', 'Needs clarification', 'The question has more than one reading.'],
    ['refused', 'shield', 'Refused', 'The request is out of scope, such as a forecast.']
  ].forEach(([status, ic, label, body]) => {
    const badge = el('span', `badge ${status}`); add(badge, icon(ic), el('span', '', label));
    oc.append(add(el('li'), badge, el('p', '', body)));
  });
  outcomes.body.append(oc, button('Try an example question', () => tryQuestion(FAMILIES[0].questions[0]), 'btn small plain', 'arrow-ur'));
  root.append(outcomes.node);

  // ---------- data ----------
  const charts = Array.isArray(report?.charts) ? report.charts : [];
  if (charts.length) root.append(explorer(charts).node);
  if (Array.isArray(report?.sources?.rows) && report.sources.rows.length) root.append(sources(report).node);

  // ---------- limits ----------
  root.append(limits(report).node);
  return {go};
}

function section(id, title, lede) {
  const node = el('section', 'section'); node.id = id;
  const container = el('div', 'container');
  const headEl = el('div', 'section-head reveal');
  add(headEl, el('h2', '', title), lede ? el('p', '', lede) : null);
  const body = el('div', 'section-body');
  container.append(headEl, body); node.append(container);
  return {node, body};
}

function specimen(cards, seriesById) {
  const holder = el('div', 'bezel hero-specimen'); const core = el('div', 'bezel-core specimen');
  holder.append(core);
  const head = el('div', 'spec-head');
  add(head, el('span', 'small', `Latest quarter: ${cards[0].period}`), el('span', 'small muted', 'Source: MOM, via data.gov.sg'));
  const readout = el('div', 'spec-readout'); readout.setAttribute('aria-live', 'polite');
  const chartSlot = el('div', 'spec-chart');
  const tiles = el('ul', 'tiles');
  let selected = 0;
  const tileButtons = [];
  const show = index => {
    selected = index;
    const card = cards[index];
    const series = seriesById.get(card.card_id);
    tileButtons.forEach((b, i) => b.setAttribute('aria-pressed', String(i === index)));
    readout.replaceChildren(
      el('p', 'spec-label', card.label),
      el('p', 'spec-value num', fmtUnit(card.value, card.unit)),
      el('p', 'spec-change small', finite(card.change) ? `${signed(card.change)} ${CHANGE_UNIT[card.change_unit] ?? card.change_unit ?? ''} from the previous quarter` : 'Change not recorded'),
      add(el('p', 'spec-meta'), el('span', 'pill', human(card.population)), el('span', 'pill', human(card.adjustment)))
    );
    chartSlot.replaceChildren(series ? lineChart({title: `${card.label}, quarterly`, unit: card.unit, compact: true, headingLevel: 'h3', series: [{label: card.label, points: series.points.map(p => ({period: p.period, value: finite(p.value) ? p.value : null}))}]}) : el('p', 'small muted', 'No series for this figure in the report.'));
  };
  cards.forEach((card, i) => {
    const li = el('li'); const b = el('button', 'tile'); b.type = 'button'; b.setAttribute('aria-pressed', 'false');
    const series = seriesById.get(card.card_id);
    add(b, el('span', 'tile-label', card.label), tileValue(card), series ? sparkline(series.points, {width: 96, height: 26, label: `${card.label} trend`}) : null);
    b.addEventListener('click', () => show(i));
    tileButtons.push(b); li.append(b); tiles.append(li);
  });
  add(core, head, readout, chartSlot, tiles);
  show(0);
  return holder;
}

function tileValue(card) {
  const node = el('span', 'tile-value num');
  if (card.unit === 'percent') { node.textContent = fmtUnit(card.value, card.unit); return node; }
  node.append(document.createTextNode(fmtUnit(card.value, '')), el('small', 'tile-unit', ` ${card.unit ?? ''}`));
  return node;
}

function explorer(charts) {
  const s = section('series', 'Explore the data', 'Each series keeps its own population and adjustment.');
  const box = el('div', 'bezel reveal'); const core = el('div', 'bezel-core explorer');
  const picker = el('div', 'picker'); picker.setAttribute('role', 'group'); picker.setAttribute('aria-label', 'Series');
  const slot = el('div', 'explorer-chart');
  const chosen = new Set([charts.find(c => c.id === 'unemployment_resident_sa')?.id ?? charts[0].id]);
  const buttons = new Map();
  const render = () => {
    const picked = charts.filter(c => chosen.has(c.id));
    const unit = picked[0]?.unit;
    buttons.forEach((b, id) => {
      const c = charts.find(x => x.id === id);
      b.setAttribute('aria-pressed', String(chosen.has(id)));
      b.disabled = false; b.title = c.unit !== unit && chosen.size ? 'Selecting this replaces the current selection, because the units differ.' : '';
    });
    const title = picked.length === 1 ? human(picked[0].title) : `${picked.length} series, ${unit}`;
    const meta = picked.flatMap(c => [`${c.title}: ${human(c.population)}, ${human(c.adjustment)}`]);
    const fig = lineChart({title, unit, headingLevel: 'h3', caption: picked.length === 1 ? picked[0].description : 'Each series keeps its own population and adjustment. Do not read a gap between lines as a like-for-like difference.',
      chips: picked.length === 1 ? [`Unit: ${unit}`, `Population: ${human(picked[0].population)}`, `Adjustment: ${human(picked[0].adjustment)}`] : [`Unit: ${unit}`],
      series: picked.map(c => ({label: c.title, points: c.points.map(p => ({period: p.period, value: finite(p.value) ? p.value : null}))}))});
    slot.replaceChildren(fig);
    if (picked.length > 1) { const dl = el('ul', 'meta-list small muted'); meta.forEach(m => dl.append(el('li', '', m))); slot.append(dl); }
  };
  charts.forEach(c => {
    const b = el('button', 'chip'); b.type = 'button'; b.textContent = c.title; b.setAttribute('aria-pressed', 'false');
    b.addEventListener('click', () => {
      const unit = [...chosen].map(id => charts.find(x => x.id === id).unit)[0];
      if (chosen.has(c.id)) { if (chosen.size > 1) chosen.delete(c.id); }
      else { if (unit && unit !== c.unit) chosen.clear(); chosen.add(c.id); }
      render();
    });
    buttons.set(c.id, b); picker.append(b);
  });
  add(core, picker, slot); box.append(core); s.body.append(box);
  render();
  return s;
}

function sources(report) {
  const rows = report.sources.rows;
  const s = section('sources-overview', `${rows.length} sources`, 'Advance and final releases are kept apart.');
  const tally = key => rows.reduce((m, r) => m.set(r[key] ?? null, (m.get(r[key] ?? null) ?? 0) + 1), new Map());
  const stage = [...tally('release_stage')].sort((a, b) => b[1] - a[1]);
  const total = rows.length;
  const box = el('div', 'bezel reveal'); const bc = el('div', 'bezel-core');
  add(bc, add(el('p', 'big-number num'), document.createTextNode(String(total)), el('span', 'big-unit', ' source records')));
  const bar = el('div', 'stack-bar'); bar.setAttribute('role', 'img');
  bar.setAttribute('aria-label', `Source records by release status: ${stage.map(([k, n]) => `${human(k ?? 'not recorded')} ${n}`).join(', ')}.`);
  const legend = el('ul', 'stack-legend');
  stage.forEach(([key, n], i) => {
    const seg = el('span', `seg c${(i % 6) + 1}`); seg.setAttribute('data-n', n); seg.style.flexGrow = String(n); bar.append(seg);
    const li = el('li'); add(li, el('span', `swatch c${(i % 6) + 1}`), el('span', '', human(key ?? 'Not recorded')), el('strong', 'num', String(n))); legend.append(li);
  });
  add(bc, bar, legend, el('p', 'small muted', `Statistics: Ministry of Manpower and the Singapore Department of Statistics via data.gov.sg, under the Singapore Open Data Licence. Reports: Ministry of Manpower. This site shows only short excerpts cited by the live agent.`));
  box.append(bc); s.body.append(box);
  return s;
}

function limits(report) {
  const s = section('limits', 'Limits', null);
  const items = [
    'Most reference answers were drafted by an AI. I reviewed 45 of 268.',
    'On fresh questions, filtering helped by a few cases only.',
    'A planted wrong figure was caught once and missed once. The attack scanner is weak.',
    'The live system uses a newer document build than most results.',
    `Covers ${report?.summary?.scope?.map(p => p.replace('-', ' ')).join(' to ') ?? 'a fixed period'}. No forecasts, no claims about causes.`
  ];
  const ul = el('ul', 'limit-list stagger');
  items.forEach(t => ul.append(add(el('li', 'reveal'), el('p', '', t))));
  s.body.append(ul);
  const more = [...(report?.evaluation?.limitations ?? []), ...(report?.answers?.limitations ?? []), ...(report?.mcp?.limitations ?? []), ...(report?.limitations ?? [])]
    .filter((t, i, a) => typeof t === 'string' && a.indexOf(t) === i);
  if (more.length) {
    const d = el('details', 'more-limits reveal'); d.append(el('summary', '', `Additional limitations in the report (${more.length})`));
    const ul2 = el('ul'); more.forEach(t => ul2.append(el('li', '', t))); d.append(ul2); s.body.append(d);
  }
  return s;
}
