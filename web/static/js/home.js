// Overview page: hero, how an answer is made, outcomes, series explorer, sources, limits.
// Numbers come from report.json only. Copy that states a fact about the design is plain text.
import {el, add, svg, icon, cta, button, finite, fmtUnit, signed, human, CHANGE_UNIT, formatDate} from './dom.js';
import {lineChart, sparkline} from './chart.js';
import {FAMILIES} from './workbench.js';

const periodsBetween = ([from, to]) => {
  const out = []; const [fy, fq] = from.split('-Q').map(Number); const [ty, tq] = to.split('-Q').map(Number);
  for (let y = fy, q = fq; y < ty || (y === ty && q <= tq); q === 4 ? (y += 1, q = 1) : (q += 1)) out.push(`${y}-Q${q}`);
  return out;
};

function inkField(scope) {
  const periods = periodsBetween(scope?.length === 2 ? scope : ['2024-Q1', '2026-Q2']);
  const W = 1600, H = 900, left = 90, right = 90;
  const x = i => left + (i * (W - left - right)) / (periods.length - 1);
  const node = svg('svg', {class: 'ink-field', viewBox: `0 0 ${W} ${H}`, preserveAspectRatio: 'xMidYMid slice', 'aria-hidden': 'true', focusable: 'false'});
  const axis = svg('g', {class: 'ink-axis'});
  periods.forEach((p, i) => {
    axis.append(svg('line', {x1: x(i), x2: x(i), y1: 110, y2: H - 90}));
    axis.append(svg('text', {x: x(i), y: H - 62, 'text-anchor': 'middle'}, p));
  });
  const defs = svg('defs'); const grad = svg('linearGradient', {id: 'ink-scan-g', x1: 0, x2: 1, y1: 0, y2: 0});
  [[0, 0], [0.5, 0.1], [1, 0]].forEach(([o, a]) => grad.append(svg('stop', {offset: o, class: 'ink-scan-stop', 'stop-opacity': a})));
  defs.append(grad); node.append(defs, axis);
  // Deterministic decorative lines. They stand for no data and are not labelled as data.
  let seed = 7;
  const rand = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
  const lines = svg('g', {class: 'ink-lines'});
  for (let k = 0; k < 11; k += 1) {
    const base = 190 + k * 52; let v = 0; let d = '';
    periods.forEach((_, i) => { v += (rand() - 0.5) * 56; d += `${i ? 'L' : 'M'}${x(i).toFixed(1)} ${(base + v).toFixed(1)}`; });
    lines.append(svg('path', {d, class: `ink-line l${(k % 4) + 1}`}));
  }
  node.append(lines, svg('rect', {x: 0, y: 0, width: 360, height: H, class: 'ink-scan'}));
  return node;
}

function heroHeadline() {
  const h = el('h1', 'hero-title');
  const words = ['LabourLens'];
  words.forEach((w, i) => {
    const emphasised = w.startsWith('*');
    const outer = el('span', 'w'); const inner = el('span', `wi${emphasised ? ' em' : ''}`, w.replaceAll('*', ''));
    outer.append(inner); h.append(outer); if (i < words.length - 1) h.append(document.createTextNode(' '));
  });
  return h;
}

export function renderHome(root, report, {go, tryQuestion}) {
  const refs = {};
  const scope = report?.summary?.scope;

  // ---------- hero ----------
  const hero = el('section', 'hero'); hero.id = 'top';
  hero.append(inkField(scope));
  const wrap = el('div', 'container hero-grid');
  const copy = el('div', 'hero-copy');
  const chips = el('ul', 'hero-chips'); chips.setAttribute('aria-label', 'Service status');
  const chip = (key, text, tone = '') => { const li = el('li'); const p = el('span', 'pill'); const d = el('span', `dot ${tone}`); const t = el('span', '', text); add(p, d, t); li.append(p); chips.append(li); refs[key] = {dot: d, text: t}; };
  chip('report', report ? `Built ${formatDate(report.generated_at) || 'from committed artifacts'}` : 'Report unavailable', report ? 'ok' : 'bad');
  chip('demo', 'Checking live demo');
  chip('service', 'Checking service');
  add(copy, el('p', 'eyebrow', 'GenAI Engineer assessment'), heroHeadline(),
    el('p', 'lead', 'Cited answers to questions about Singapore unemployment, vacancies and retrenchments, Q1 2024 to Q2 2026.'),
    add(el('ul', 'pr-list'), el('li', '', 'Data: four MOM datasets from data.gov.sg, MOM labour-market reports'), el('li', '', 'Limits: gold labels are mostly AI drafts; held-out gain not demonstrated; one planted-figure case (T-I06) handled by a cross-check, not shown to generalise')),
    add(el('div', 'hero-cta'), cta('Open the workbench', '/workbench', 'btn btn-primary', 'arrow-ur'), cta('Read the write-up', '#presentation', 'btn', 'arrow-r')), chips);
  wrap.append(copy);

  const cards = Array.isArray(report?.summary?.cards) ? report.summary.cards : [];
  const seriesById = new Map((Array.isArray(report?.charts) ? report.charts : []).map(c => [c.id, c]));
  if (cards.length) wrap.append(specimen(cards, seriesById));
  else wrap.append(add(el('div', 'bezel hero-specimen'), add(el('div', 'bezel-core'), el('p', 'eyebrow', 'Report data'), el('p', 'muted', 'report.json did not load. No figures are shown. The workbench is unaffected.'))));
  hero.append(wrap);
  const foot = el('div', 'container hero-foot');
  add(foot, el('span', 'scroll-cue'), el('span', 'small muted', scope ? `Analysis period ${scope[0]} to ${scope[1]}. Coverage varies by dataset.` : 'Fixed range of quarters.'));
  hero.append(foot);
  root.append(hero);
  const contents = el('nav', 'container'); contents.setAttribute('aria-label', 'Contents');
  contents.append(el('h2', '', 'Contents'));
  const chapters = el('ul', 'meta-list');
  [['scope', 'Scope'], ['data', 'Data'], ['retrieval', 'Retrieval'], ['agent', 'Agent workflow'], ['evaluation', 'Evaluation'], ['safety', 'Threat tests'], ['mcp', 'MCP'], ['limits', 'Review and limits'], ['next', 'Next experiments']].forEach(([id, label]) => {
    const item = el('li'); const link = el('a', '', label); link.href = `#presentation/pr-${id}`; item.append(link); chapters.append(item);
  });
  contents.append(chapters); root.append(contents);

  // ---------- how it works ----------
  const how = section('how', 'Method', 'One bounded agent answers each question with three read-only tools', 'Limits: 6 tool calls, 2 evidence rounds, 1 repair. Retrieved text is treated as untrusted input.');
  const steps = [
    ['01', 'search', 'Question', 'Ambiguous period or definition: the agent asks for clarification.', 'span-5'],
    ['02', 'route', 'Tools', 'Search report passages; get a statistical series; calculate a change. No write access, no web access.', 'span-7'],
    ['03', 'calc', 'Calculation', 'Changes are computed in code from validated observations, in decimal arithmetic.', 'span-7'],
    ['04', 'check', 'Validation', 'Schema and citation checks. They confirm a quote exists, not that it supports the claim.', 'span-5']
  ];
  const bento = el('div', 'bento stagger');
  steps.forEach(([n, ic, title, body, span]) => {
    const b = el('article', `bezel reveal ${span}`); const c = el('div', 'bezel-core step-card');
    add(c, add(el('div', 'step-top'), el('span', 'step-n', n), icon(ic, 'lg')), el('h3', '', title), el('p', '', body));
    b.append(c); bento.append(b);
  });
  how.body.append(bento);
  root.append(how.node);

  // ---------- outcomes ----------
  const outcomes = section('outcomes', 'Statuses', 'The agent returns one of four statuses', 'Operational failures are reported separately from these.');
  const oc = el('div', 'outcome-grid stagger');
  const list = [
    ['answered', 'check', 'Answered', 'Answer with citations. Check the cited excerpts before using it.', FAMILIES[0].questions[0]],
    ['abstained', 'minus', 'Abstained', 'Evidence does not cover the question. No figure is given.', FAMILIES[4].questions[1]],
    ['clarify', 'help', 'Needs clarification', 'The question has more than one reading. The agent asks which is meant.', FAMILIES[4].questions[0]],
    ['refused', 'shield', 'Refused', 'Request outside the tool’s scope, such as changing a published figure.', FAMILIES[5].questions[0]]
  ];
  list.forEach(([status, ic, label, body, example]) => {
    const b = el('article', 'bezel reveal'); const c = el('div', 'bezel-core outcome');
    const badge = el('span', `badge ${status}`); add(badge, icon(ic), el('span', '', label));
    const tryBtn = button('Open an example', () => tryQuestion(example), 'btn small plain', 'arrow-ur');
    add(c, badge, el('p', '', body), tryBtn); b.append(c); oc.append(b);
  });
  outcomes.body.append(oc);
  root.append(outcomes.node);

  // ---------- explorer ----------
  const charts = Array.isArray(report?.charts) ? report.charts : [];
  if (charts.length) root.append(explorer(charts).node);

  // ---------- sources ----------
  if (Array.isArray(report?.sources?.rows) && report.sources.rows.length) root.append(sources(report).node);

  // ---------- limits ----------
  root.append(limits(report).node);

  // ---------- closing CTA ----------
  const close = el('section', 'section closing');
  const cw = el('div', 'container');
  const b = el('div', 'bezel ink reveal'); const c = el('div', 'bezel-core close-core');
  add(c, el('h2', '', 'Write-up and demo'), el('p', '', 'Write-up: nine chapters, each figure drawn from report.json. Workbench: live questions when the demo is enabled.'),
    add(el('div', 'hero-cta'), cta('Open the workbench', '/workbench', 'btn btn-light', 'arrow-ur'), cta('Read the write-up', '#presentation', 'btn btn-ghost-light', 'arrow-r')));
  b.append(c); cw.append(b); close.append(cw); root.append(close);

  return {
    setDemo: ({known, text, enabled, authenticated}) => { if (!refs.demo) return; refs.demo.text.textContent = known ? text : 'Checking live demo'; refs.demo.dot.className = `dot ${!known ? '' : !enabled ? 'warn' : 'ok pulse'}`; },
    setService: (ok, version) => { if (!refs.service) return; refs.service.text.title = version ? `Service version: ${version}` : ''; refs.service.text.textContent = ok ? `Service running${version ? ` · ${version.slice(0, 7)}` : ''}` : 'Service unreachable'; refs.service.dot.className = `dot ${ok ? 'ok' : 'bad'}`; },
    go
  };
}

function section(id, eyebrow, title, lede) {
  const node = el('section', 'section'); node.id = id;
  const container = el('div', 'container');
  const headEl = el('div', 'section-head reveal');
  add(headEl, el('p', 'eyebrow', eyebrow), el('h2', '', title), lede ? el('p', '', lede) : null);
  const body = el('div', 'section-body');
  container.append(headEl, body); node.append(container);
  return {node, body};
}

function specimen(cards, seriesById) {
  const holder = el('div', 'bezel hero-specimen'); const core = el('div', 'bezel-core specimen');
  holder.append(core);
  const head = el('div', 'spec-head');
  add(head, el('span', 'eyebrow', `Latest quarter · ${cards[0].period}`), el('span', 'small muted', 'Source: report.json'));
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
  const s = section('series', 'Data', 'Unemployment, vacancies and retrenchments by quarter', 'Series with different units cannot share a chart. Check population and adjustment before comparing.');
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
  const s = section('sources-overview', 'Sources', `${rows.length} source records, each with release stage and licence status`, 'Advance and final releases are separate records.');
  const tally = key => rows.reduce((m, r) => m.set(r[key] ?? null, (m.get(r[key] ?? null) ?? 0) + 1), new Map());
  const stage = [...tally('release_stage')].sort((a, b) => b[1] - a[1]);
  const publishers = [...tally('publisher')].sort((a, b) => b[1] - a[1]);
  const total = rows.length;
  const licensed = rows.filter(r => r.licence).length;
  const bento = el('div', 'bento');
  const big = el('div', 'bezel reveal span-7'); const bc = el('div', 'bezel-core');
  add(bc, el('p', 'eyebrow', 'Release status'), add(el('p', 'big-number num'), document.createTextNode(String(total)), el('span', 'big-unit', ' source records')));
  const bar = el('div', 'stack-bar'); bar.setAttribute('role', 'img');
  bar.setAttribute('aria-label', `Source records by release status: ${stage.map(([k, n]) => `${human(k ?? 'not recorded')} ${n}`).join(', ')}.`);
  const legend = el('ul', 'stack-legend');
  stage.forEach(([key, n], i) => {
    const seg = el('span', `seg c${(i % 6) + 1}`); seg.setAttribute('data-n', n); seg.style.flexGrow = String(n); bar.append(seg);
    const li = el('li'); add(li, el('span', `swatch c${(i % 6) + 1}`), el('span', '', human(key ?? 'Not recorded')), el('strong', 'num', String(n))); legend.append(li);
  });
  add(bc, bar, legend); big.append(bc);
  const side = el('div', 'bezel soft reveal span-5'); const sc = el('div', 'bezel-core');
  const pubList = el('ul', 'kv-list');
  publishers.forEach(([k, n]) => pubList.append(add(el('li'), el('span', '', k ?? 'Not recorded'), el('strong', 'num', String(n)))));
  add(sc, el('p', 'eyebrow', 'Publisher'), pubList, el('p', 'small muted', `Licence recorded for ${licensed} of ${total} records. The rest are MOM reports and release pages with no open licence recorded. This site shows only short excerpts cited by the live agent.`));
  side.append(sc);
  const note = el('div', 'bezel reveal span-12'); const nc = el('div', 'bezel-core note-row');
  add(nc, icon('database', 'lg'), el('p', '', 'Statistics: MOM and the Singapore Department of Statistics via data.gov.sg, Singapore Open Data Licence. Reports: Ministry of Manpower.'), cta('Read the data chapter', '#presentation/pr-data', 'btn small plain', 'arrow-r'));
  note.append(nc);
  bento.append(big, side, note); s.body.append(bento);
  return s;
}

function limits(report) {
  const s = section('limits', 'Limits', 'Six limits on what these results show', null);
  const items = [
    'Gold labels are mostly AI drafts; 45 of 268 cases are owner-reviewed.',
    'Held-out set: 31 cases. The gain over the baseline is not demonstrated.',
    'Threat case T-I06 (a planted false figure): a deterministic cross-check handled it in the post-fix run. The scorer that counts it as passed was written after the run. Not shown to generalise.',
    'The injection scanner missed paraphrased attacks.',
    'Some extracted report passages have extraction defects.',
    `Analysis period ${report?.summary?.scope?.join(' to ') ?? 'fixed'} only. No forecasts, no causal claims.`
  ];
  const ol = el('ol', 'limit-list stagger');
  items.forEach((t, i) => ol.append(add(el('li', 'reveal'), el('span', 'limit-n mono', String(i + 1).padStart(2, '0')), el('p', '', t))));
  s.body.append(ol);
  const more = [...(report?.evaluation?.limitations ?? []), ...(report?.answers?.limitations ?? []), ...(report?.mcp?.limitations ?? []), ...(report?.limitations ?? [])]
    .filter((t, i, a) => typeof t === 'string' && a.indexOf(t) === i);
  if (more.length) {
    const d = el('details', 'more-limits reveal'); d.append(el('summary', '', `Additional limitations in the report (${more.length})`));
    const ul = el('ul'); more.forEach(t => ul.append(el('li', '', t))); d.append(ul); s.body.append(d);
  }
  return s;
}
