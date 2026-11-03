// Accessible vanilla-SVG line chart. Every chart has a title, a text summary, a keyboard-readable
// cursor, a tooltip and a data-table view. Straight segments only: no smoothing, no invented points.
import {el, svg, icon, finite, fmtUnit} from './dom.js';

const DASH = ['', '7 5', '2 4', '10 4 2 4', '1 0', '4 3'];
const nice = (min, max, ticks) => {
  const span = max - min || Math.abs(max) || 1;
  const rough = span / ticks;
  const power = 10 ** Math.floor(Math.log10(rough));
  const step = [1, 2, 2.5, 5, 10].map(m => m * power).find(s => s >= rough) ?? 10 * power;
  const lo = Math.floor(min / step) * step;
  const hi = Math.ceil(max / step) * step;
  const out = [];
  for (let v = lo; v <= hi + step / 1e6; v += step) out.push(Number(v.toFixed(10)));
  return out;
};

function describe(series, unit) {
  return series.map(item => {
    const known = item.points.filter(p => finite(p.value));
    if (!known.length) return `${item.label}: no published values in this range.`;
    const lo = known.reduce((a, b) => (b.value < a.value ? b : a));
    const hi = known.reduce((a, b) => (b.value > a.value ? b : a));
    const gaps = item.points.length - known.length;
    return `${item.label}: ${item.points.length} periods, ${item.points[0].period} to ${item.points.at(-1).period}. `
      + `First ${fmtUnit(known[0].value, unit)}, latest ${fmtUnit(known.at(-1).value, unit)}, `
      + `lowest ${fmtUnit(lo.value, unit)} in ${lo.period}, highest ${fmtUnit(hi.value, unit)} in ${hi.period}.`
      + (gaps ? ` ${gaps} period${gaps > 1 ? 's' : ''} without a published value.` : '');
  }).join(' ');
}

/**
 * @param {{title:string, caption?:string, unit?:string, series:{label:string, points:{period:string,value:number|null}[]}[],
 *          chips?:string[], compact?:boolean, headingLevel?:string}} options
 */
export function lineChart({title, caption, unit = '', series, chips = [], compact = false, headingLevel = 'h3', comparisonPair = false, lead = null}) {
  const periods = [...new Set(series.flatMap(s => s.points.map(p => p.period)))].sort();
  const lookup = series.map(s => new Map(s.points.map(p => [p.period, p.value])));
  const figure = el('figure', `chart${compact ? ' compact' : ''}`);
  const head = el('figcaption', 'chart-head');
  const heading = el(headingLevel, 'chart-title', title);
  head.append(heading);
  if (chips.length) { const row = el('div', 'chart-chips'); chips.forEach(c => row.append(el('span', 'pill', c))); head.append(row); }
  if (caption) head.append(el('p', 'chart-caption', caption));
  figure.append(head);
  if (lead) figure.append(lead);

  const stage = el('div', 'chart-stage');
  stage.tabIndex = 0;
  stage.setAttribute('role', 'group');
  stage.setAttribute('aria-roledescription', 'interactive chart');
  stage.setAttribute('aria-label', `${title}. Press the left and right arrow keys to read each period.`);
  const tip = el('div', 'chart-tip'); tip.setAttribute('aria-hidden', 'true'); tip.hidden = true;
  const live = el('p', 'visually-hidden'); live.setAttribute('aria-live', 'polite');
  stage.append(tip);
  figure.append(stage, live);

  if (series.length > 1) {
    const legend = el('ul', 'chart-legend');
    series.forEach((s, i) => {
      const item = el('li');
      const sample = svg('svg', {width: 28, height: 10, 'aria-hidden': 'true'});
      sample.append(svg('line', {x1: 1, x2: 27, y1: 5, y2: 5, class: `ln s${i + 1}`, 'stroke-dasharray': DASH[i % DASH.length]}));
      item.append(sample, el('span', '', s.label)); legend.append(item);
    });
    figure.append(legend);
  }

  const summary = el('p', 'chart-summary', describe(series, unit));
  const toolbar = el('div', 'chart-tools');
  const toggle = el('button', 'btn small plain');
  toggle.type = 'button'; toggle.setAttribute('aria-pressed', 'false');
  toggle.append(icon('table'), el('span', '', 'Data table'));
  const wrap = el('div', 'table-wrap'); wrap.hidden = true; wrap.tabIndex = 0;
  wrap.setAttribute('role', 'region'); wrap.setAttribute('aria-label', `${title}: data table`);
  const table = el('table', 'data-table');
  table.append(el('caption', 'visually-hidden', `${title}${unit ? `, unit: ${unit}` : ''}`));
  const headRow = el('tr'); headRow.append(Object.assign(el('th', '', 'Period'), {scope: 'col'}));
  series.forEach(s => headRow.append(Object.assign(el('th', '', s.label), {scope: 'col'})));
  const thead = el('thead'); thead.append(headRow);
  const tbody = el('tbody');
  periods.forEach(period => {
    const row = el('tr'); row.append(Object.assign(el('th', 'mono', period), {scope: 'row'}));
    lookup.forEach(map => row.append(el('td', 'num', finite(map.get(period)) ? fmtUnit(map.get(period), unit) : 'No value')));
    tbody.append(row);
  });
  table.append(thead, tbody); wrap.append(table);
  toggle.addEventListener('click', () => {
    const on = wrap.hidden; wrap.hidden = !on; toggle.setAttribute('aria-pressed', String(on));
  });
  toolbar.append(toggle);
  figure.append(summary, toolbar, wrap);
  if (comparisonPair && series.length === 1 && periods.length === 2 && periods.every(p => finite(lookup[0].get(p)))) {
    const pair = el('dl', 'chart-pair');
    periods.forEach(period => { const cell = el('div'); cell.append(el('dt', '', period), el('dd', 'num', fmtUnit(lookup[0].get(period), unit))); pair.append(cell); });
    const change = lookup[0].get(periods[1]) - lookup[0].get(periods[0]);
    const cell = el('div'); cell.append(el('dt', '', 'Change'), el('dd', 'num', `${change > 0 ? '+' : ''}${fmtUnit(Number(change.toFixed(10)), unit === 'percent' ? 'percentage points' : unit)}`)); pair.append(cell);
    stage.replaceWith(pair); live.remove(); figure.dataset.presentation = 'before-after';
    return figure;
  }
  const rateAxis = /percent|percentage|\brate\b|%/i.test(unit);
  const axisNote = el('p', 'chart-axis-note small muted'); axisNote.hidden = true; head.append(axisNote);

  // ---- drawing ----
  let active = -1;
  let drawn = false;
  let geometry = null;
  let root = null;

  const place = (index, announce) => {
    if (!geometry || index < 0 || index >= periods.length) return;
    active = index;
    const {x, left, plotW, ys} = geometry;
    root.querySelector('.chart-cursor').setAttribute('transform', `translate(${x(index)} 0)`);
    root.querySelector('.chart-cursor').classList.add('on');
    root.querySelectorAll('.mk').forEach(m => m.classList.toggle('on', Number(m.dataset.i) === index));
    tip.replaceChildren(el('strong', 'mono', periods[index]));
    const lines = [];
    series.forEach((s, si) => {
      const value = lookup[si].get(periods[index]);
      const row = el('div', 'tip-row');
      const sw = svg('svg', {width: 18, height: 8, 'aria-hidden': 'true'});
      sw.append(svg('line', {x1: 1, x2: 17, y1: 4, y2: 4, class: `ln s${si + 1}`, 'stroke-dasharray': DASH[si % DASH.length]}));
      row.append(sw, el('span', 'tip-label', s.label), el('span', 'tip-value num', finite(value) ? fmtUnit(value, unit) : 'No published value'));
      tip.append(row);
      lines.push(`${s.label}: ${finite(value) ? fmtUnit(value, unit) : 'no published value'}`);
    });
    tip.hidden = false;
    const tipW = tip.offsetWidth || 180;
    const px = x(index);
    const flip = px + tipW + 24 > left + plotW + 24;
    const firstY = ys(index);
    tip.style.transform = `translate(${flip ? px - tipW - 14 : px + 14}px, ${Math.max(4, Math.min(firstY - 20, geometry.height - 110))}px)`;
    if (announce) live.textContent = `${periods[index]}. ${lines.join('. ')}.`;
  };
  const clear = () => {
    active = -1; tip.hidden = true;
    root?.querySelector('.chart-cursor')?.classList.remove('on');
    root?.querySelectorAll('.mk.on').forEach(m => m.classList.remove('on'));
  };

  function draw(width) {
    const height = compact ? 176 : width < 520 ? 270 : 340;
    const left = 52, right = 20, top = 18, bottom = 34;
    const plotW = Math.max(40, width - left - right), plotH = height - top - bottom;
    const values = series.flatMap(s => s.points.map(p => p.value)).filter(finite);
    const lo = values.length ? Math.min(...values) : 0, hi = values.length ? Math.max(...values) : 1;
    const pad = (hi - lo || Math.abs(hi) || 1) * 0.12;
    const ticks = nice(rateAxis ? lo - pad : Math.min(0, lo), rateAxis ? hi + pad : Math.max(0, hi + pad), compact ? 3 : 5);
    const y0 = ticks[0], y1 = ticks.at(-1);
    figure.dataset.axisMinimum = String(y0);
    axisNote.hidden = y0 === 0;
    axisNote.textContent = y0 === 0 ? '' : 'The axis does not start at zero.';
    const n = periods.length;
    const x = i => left + (n === 1 ? plotW / 2 : (i * plotW) / (n - 1));
    const y = v => top + plotH - ((v - y0) / (y1 - y0 || 1)) * plotH;
    const ys = i => { const v = lookup.map(m => m.get(periods[i])).find(finite); return finite(v) ? y(v) : top + plotH / 2; };
    geometry = {x, ys, left, plotW, height};

    const node = svg('svg', {class: 'chart-svg', width, height, viewBox: `0 0 ${width} ${height}`, 'aria-hidden': 'true', focusable: 'false'});
    const grid = svg('g', {class: 'grid'});
    ticks.forEach(t => {
      grid.append(svg('line', {x1: left, x2: left + plotW, y1: y(t), y2: y(t)}));
      grid.append(svg('text', {x: left - 10, y: y(t) + 3.5, 'text-anchor': 'end', class: 'tick num'}, fmtUnit(t, unit === 'percent' ? 'percent' : '').replace(/ $/, '')));
    });
    node.append(grid);
    const step = Math.max(1, Math.ceil(56 / (n > 1 ? plotW / (n - 1) : plotW)));
    const labels = svg('g', {class: 'xlabels'});
    periods.forEach((p, i) => {
      if ((n - 1 - i) % step !== 0) return;
      labels.append(svg('line', {x1: x(i), x2: x(i), y1: top + plotH, y2: top + plotH + 5, class: 'xtick'}));
      labels.append(svg('text', {x: x(i), y: height - 10, 'text-anchor': i === 0 && n > 1 ? 'start' : i === n - 1 && n > 1 ? 'end' : 'middle', class: 'tick'}, p));
    });
    node.append(labels);

    // gaps: a dashed marker where a period has no published value in any series
    periods.forEach((p, i) => {
      if (lookup.every(m => !finite(m.get(p)))) node.append(svg('line', {x1: x(i), x2: x(i), y1: top, y2: top + plotH, class: 'gap'}));
    });

    series.forEach((s, si) => {
      let d = '', pen = false, lastPoint = null;
      const marks = svg('g', {class: `marks s${si + 1}`});
      periods.forEach((p, i) => {
        const v = lookup[si].get(p);
        if (!finite(v)) { pen = false; return; }
        d += `${pen ? 'L' : 'M'}${x(i).toFixed(2)} ${y(v).toFixed(2)}`; pen = true; lastPoint = [i, v];
        marks.append(svg('circle', {cx: x(i), cy: y(v), r: compact ? 3 : 4, class: 'mk', 'data-i': i}));
      });
      if (series.length === 1 && finite(lookup[0].get(periods[0])) && n > 1) {
        const first = periods.findIndex(p => finite(lookup[0].get(p)));
        const lastIdx = lastPoint ? lastPoint[0] : first;
        const fill = `${d}L${x(lastIdx).toFixed(2)} ${top + plotH}L${x(first).toFixed(2)} ${top + plotH}Z`;
        if (!d.includes('M', 1)) node.append(svg('path', {d: fill, class: `area s${si + 1}`}));
      }
      if (d) node.append(svg('path', {d, class: `ln s${si + 1}`, 'stroke-dasharray': DASH[si % DASH.length], 'stroke-width': compact ? 2 : 2.25}));
      node.append(marks);
      if (series.length === 1 && lastPoint) {
        const earlier = periods.slice(0, lastPoint[0]).map(p => lookup[0].get(p)).filter(finite).at(-1);
        const below = finite(earlier) && lastPoint[1] < earlier;
        node.append(svg('text', {x: x(lastPoint[0]), y: y(lastPoint[1]) + (below ? 22 : -12), 'text-anchor': lastPoint[0] === n - 1 && n > 1 ? 'end' : 'middle', class: 'endlabel num'}, fmtUnit(lastPoint[1], unit)));
      }
    });
    node.append(svg('line', {x1: 0, x2: 0, y1: top, y2: top + plotH, class: 'chart-cursor'}));
    if (!drawn) node.append(svg('rect', {x: left - 8, y: 0, width: plotW + right + 8, height: top + plotH + 2, class: 'chart-wipe'}));
    root?.remove();
    root = node;
    stage.prepend(node);
    stage.style.setProperty('--chart-h', `${height}px`);
    if (!drawn) {
      drawn = true;
      const wipe = node.querySelector('.chart-wipe');
      if (wipe && 'IntersectionObserver' in window) {
        const io = new IntersectionObserver(entries => { if (entries.some(e => e.isIntersecting)) { wipe.classList.add('go'); io.disconnect(); } }, {threshold: 0.35});
        io.observe(stage);
      } else wipe?.classList.add('go');
    }
    if (active >= 0) place(active, false);
  }

  const resize = new ResizeObserver(entries => {
    const width = Math.floor(entries[0].contentRect.width);
    if (width > 0) requestAnimationFrame(() => draw(width));
  });
  resize.observe(stage);

  stage.addEventListener('pointermove', event => {
    if (!geometry) return;
    const rect = stage.getBoundingClientRect();
    const px = event.clientX - rect.left;
    const n = periods.length;
    const index = n === 1 ? 0 : Math.round(((px - geometry.left) / geometry.plotW) * (n - 1));
    place(Math.max(0, Math.min(n - 1, index)), false);
  });
  stage.addEventListener('pointerleave', () => { if (document.activeElement !== stage) clear(); });
  stage.addEventListener('focus', () => { if (active < 0) place(periods.length - 1, true); });
  stage.addEventListener('blur', clear);
  stage.addEventListener('keydown', event => {
    const last = periods.length - 1;
    const map = {ArrowLeft: Math.max(0, (active < 0 ? last : active) - 1), ArrowRight: Math.min(last, (active < 0 ? last : active) + 1), Home: 0, End: last};
    if (event.key in map) { event.preventDefault(); place(map[event.key], true); }
    else if (event.key === 'Escape') { clear(); }
  });
  return figure;
}

/** Tiny line for tiles. Decorative: the number beside it carries the information. */
export function sparkline(points, {width = 120, height = 36, label = ''} = {}) {
  const known = points.filter(p => finite(p.value));
  const node = svg('svg', {class: 'spark', width, height, viewBox: `0 0 ${width} ${height}`, role: 'img', 'aria-label': label || 'Trend line'});
  if (known.length < 2) return node;
  const lo = Math.min(...known.map(p => p.value)), hi = Math.max(...known.map(p => p.value));
  const x = i => 3 + (i * (width - 6)) / (points.length - 1);
  const y = v => 4 + (height - 8) - ((v - lo) / (hi - lo || 1)) * (height - 8);
  let d = '', pen = false;
  points.forEach((p, i) => { if (!finite(p.value)) { pen = false; return; } d += `${pen ? 'L' : 'M'}${x(i).toFixed(1)} ${y(p.value).toFixed(1)}`; pen = true; });
  node.append(svg('path', {d, class: 'spark-line'}));
  const last = points.findLastIndex(p => finite(p.value));
  node.append(svg('circle', {cx: x(last), cy: y(points[last].value), r: 3, class: 'spark-dot'}));
  return node;
}

