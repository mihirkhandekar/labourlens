// LabourLens chart kit: small vanilla-SVG charts for the presentation.
// Every chart is drawn at its real pixel width (re-drawn on resize), themed only through CSS
// custom properties (see css/presentation.css), and built with DOM calls only: no HTML strings, no inline
// style attributes. Interaction: pointer hover and keyboard (arrow keys inside a chart).
export const NS = 'http://www.w3.org/2000/svg';

export const el = (tag, cls, text) => {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined && text !== null) node.textContent = text;
  return node;
};
export const svgEl = (tag, attrs = {}, text) => {
  const node = document.createElementNS(NS, tag);
  for (const [key, value] of Object.entries(attrs)) if (value !== undefined && value !== null) node.setAttribute(key, String(value));
  if (text !== undefined && text !== null) node.textContent = text;
  return node;
};
export const finite = value => typeof value === 'number' && Number.isFinite(value);
export const reduced = () => typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;

const nf = new Intl.NumberFormat('en-GB', {maximumFractionDigits: 0});
const MINUS = '\u2212';
export const fmt = {
  int: value => finite(value) ? nf.format(value) : 'not recorded',
  num: (value, digits = 2) => finite(value) ? new Intl.NumberFormat('en-GB', {maximumFractionDigits: digits, minimumFractionDigits: digits}).format(value) : 'not recorded',
  pct: (value, digits = 1) => finite(value) ? `${(100 * value).toFixed(digits)}%` : 'not recorded',
  raw: value => finite(value) ? String(value) : 'not recorded',
  pts: value => finite(value) ? `${value < 0 ? MINUS : '+'}${Math.abs(100 * value).toFixed(1)} pts` : 'not recorded',
  signed: (value, digits = 0) => finite(value) ? `${value < 0 ? MINUS : '+'}${new Intl.NumberFormat('en-GB', {maximumFractionDigits: digits, minimumFractionDigits: digits}).format(Math.abs(value))}` : 'not recorded',
  money: value => finite(value) ? `$${value.toFixed(5)}` : 'not recorded',
  seconds: value => finite(value) ? `${value.toFixed(1)} s` : 'not recorded',
  quarter: period => { const m = /^(\d{4})-Q(\d)$/.exec(period || ''); return m ? `Q${m[2]} ${m[1]}` : String(period); },
  human: value => String(value).replaceAll('_', ' ').replace(/^./, c => c.toUpperCase())
};

export function niceTicks(min, max, count = 5) {
  if (!finite(min) || !finite(max)) return [0, 1];
  if (min === max) max = min + 1;
  const raw = (max - min) / Math.max(1, count);
  const mag = 10 ** Math.floor(Math.log10(raw));
  const norm = raw / mag;
  const step = (norm < 1.5 ? 1 : norm < 3 ? 2 : norm < 7 ? 5 : 10) * mag;
  const out = [];
  for (let v = Math.floor(min / step) * step; v <= Math.ceil(max / step) * step + step * 1e-6; v += step) out.push(+v.toFixed(10));
  return out;
}
export function quantile(sorted, q) {
  if (!sorted.length) return null;
  const pos = (sorted.length - 1) * q;
  const lo = Math.floor(pos), hi = Math.ceil(pos);
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (pos - lo);
}

/* ---------- scroll entry ---------- */
let observer = null;
const callbacks = new WeakMap();
export function whenVisible(node, callback) {
  if (typeof IntersectionObserver !== 'function' || reduced()) { callback(); return; }
  observer ||= new IntersectionObserver(entries => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      observer.unobserve(entry.target);
      const run = callbacks.get(entry.target);
      callbacks.delete(entry.target);
      if (run) run();
    }
  }, {threshold: 0.12, rootMargin: '0px 0px -8% 0px'});
  callbacks.set(node, callback);
  observer.observe(node);
}
export function revealAll(root) {
  root.querySelectorAll('.pr-reveal').forEach(node => node.classList.add('is-in'));
}
export function countUp(node, value, format, duration = 1100) {
  const final = format(value);
  node.textContent = final;
  if (reduced() || !finite(value)) return;
  whenVisible(node, () => {
    const start = performance.now();
    const step = now => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - (1 - t) ** 3;
      node.textContent = t < 1 ? format(value * eased) : final;
      if (t < 1) requestAnimationFrame(step);
    };
    node.textContent = format(0);
    requestAnimationFrame(step);
  });
}

/* ---------- tooltips and keyboard navigation ---------- */
export function interactive(svg, ctx, items, {label = 'Chart values. Use the arrow keys to move between points.', cols = 0} = {}) {
  svg.setAttribute('role', 'group');
  svg.setAttribute('aria-label', label);
  const tip = ctx.tip;
  const clear = () => items.forEach(item => (item.mark || []).forEach(mark => mark.classList.remove('is-active')));
  const hide = () => { tip.classList.remove('is-on'); clear(); };
  const rove = index => items.forEach((item, i) => item.node.setAttribute('tabindex', i === index ? '0' : '-1'));
  const show = index => {
    const item = items[index];
    clear();
    (item.mark || []).forEach(mark => mark.classList.add('is-active'));
    tip.textContent = '';
    item.lines.forEach((line, i) => tip.append(el('span', i ? 'pr-tip-row' : 'pr-tip-title', line)));
    tip.classList.add('is-on');
    const w = tip.offsetWidth, h = tip.offsetHeight;
    let x = item.ax + 14, y = item.ay - h - 12;
    if (x + w > ctx.width - 4) x = item.ax - w - 14;
    if (x < 4) x = Math.max(4, Math.min(ctx.width - w - 4, item.ax - w / 2));
    if (y < 0) y = item.ay + 16;
    tip.style.setProperty('--tx', `${Math.round(x)}px`);
    tip.style.setProperty('--ty', `${Math.round(y)}px`);
  };
  const go = index => {
    if (index < 0 || index >= items.length) return;
    rove(index);
    items[index].node.focus();
  };
  items.forEach((item, index) => {
    const node = item.node;
    node.classList.add('pr-hit');
    node.setAttribute('role', 'img');
    node.setAttribute('aria-label', item.lines.join('. '));
    node.setAttribute('tabindex', index === 0 ? '0' : '-1');
    node.addEventListener('pointerenter', () => show(index));
    node.addEventListener('pointerleave', () => { if (document.activeElement !== node) hide(); });
    node.addEventListener('focus', () => { rove(index); show(index); });
    node.addEventListener('blur', hide);
    node.addEventListener('keydown', event => {
      const step = cols || 1;
      const moves = {ArrowRight: 1, ArrowLeft: -1, ArrowDown: step, ArrowUp: -step};
      if (event.key in moves) { event.preventDefault(); go(index + moves[event.key]); }
      else if (event.key === 'Home') { event.preventDefault(); go(0); }
      else if (event.key === 'End') { event.preventDefault(); go(items.length - 1); }
      else if (event.key === 'Escape') { hide(); }
    });
  });
}

/* ---------- figure shell: title, takeaway, chart host, legend, data table, source ---------- */
let figureCounter = 0;
export function figure(options) {
  const id = options.id || `pr-fig-${++figureCounter}`;
  const root = el('figure', 'pr-fig pr-reveal');
  root.id = id;
  if (options.wide) root.classList.add('is-wide');
  const head = el('header', 'pr-fig-head');
  const title = el('h4', 'pr-fig-title', options.title);
  title.id = `${id}-title`;
  const takeaway = el('p', 'pr-fig-takeaway', options.takeaway || '');
  head.append(title, takeaway);
  root.setAttribute('aria-labelledby', title.id);
  const body = el('div', 'pr-fig-body');
  if (options.controls) body.append(options.controls);
  const host = el('div', 'pr-host');
  const tip = el('div', 'pr-tip');
  tip.setAttribute('aria-hidden', 'true');
  const legend = el('ul', 'pr-legend');
  legend.setAttribute('aria-label', 'Legend');
  const summary = el('p', 'visually-hidden', options.summary || '');
  summary.id = `${id}-summary`;
  root.setAttribute('aria-describedby', summary.id);
  body.append(host, legend, summary);
  if (options.aside) body.append(options.aside);

  const foot = el('footer', 'pr-fig-foot');
  const toggle = el('button', 'pr-link-btn', 'View data table');
  toggle.type = 'button';
  toggle.setAttribute('aria-expanded', 'false');
  const tableWrap = el('div', 'pr-table-wrap');
  tableWrap.id = `${id}-table`;
  tableWrap.hidden = true;
  toggle.setAttribute('aria-controls', tableWrap.id);
  const source = el('p', 'pr-source');
  source.append(el('span', 'pr-source-label', 'Source '));
  source.append(el('code', 'pr-path', options.source?.data || 'report.json'));
  if (options.source?.files?.length) {
    const files = el('span', 'pr-evi', options.source.files.join(' · '));
    source.append(files);
  }
  if (options.note) foot.append(el('p', 'pr-fig-note', options.note));
  foot.append(toggle, source);

  const api = {root, host, tip, setTakeaway: text => { takeaway.textContent = text; }, setSummary: text => { summary.textContent = text; }};
  let width = 0;
  const draw = () => {
    host.textContent = '';
    host.append(tip);
    tip.classList.remove('is-on');
    legend.textContent = '';
    const ctx = {
      width, compact: width < 540, tip,
      legend: entries => entries.forEach(entry => {
        const li = el('li', 'pr-legend-item');
        li.append(el('i', `pr-swatch ${entry.cls || 'c1'}${entry.dash ? ' is-dash' : ''}`), el('span', '', entry.label));
        legend.append(li);
      })
    };
    options.draw(host, ctx);
  };
  const buildTable = () => {
    const data = typeof options.table === 'function' ? options.table() : options.table;
    tableWrap.textContent = '';
    if (!data) return;
    const scroll = el('div', 'pr-table-scroll');
    const table = el('table', 'pr-table');
    table.append(el('caption', '', data.caption || options.title));
    const thead = el('thead'), headRow = el('tr');
    data.columns.forEach((name, i) => { const th = el('th', i ? 'is-num' : '', name); th.scope = 'col'; headRow.append(th); });
    thead.append(headRow);
    const tbody = el('tbody');
    data.rows.forEach(row => {
      const tr = el('tr');
      row.forEach((cell, i) => {
        const node = i === 0 ? el('th', '', String(cell)) : el('td', 'is-num', cell === null || cell === undefined ? '' : String(cell));
        if (i === 0) node.scope = 'row';
        tr.append(node);
      });
      tbody.append(tr);
    });
    table.append(thead, tbody);
    scroll.append(table);
    tableWrap.append(scroll);
  };
  toggle.addEventListener('click', () => {
    const open = tableWrap.hidden;
    if (open) buildTable();
    tableWrap.hidden = !open;
    toggle.setAttribute('aria-expanded', String(open));
    toggle.textContent = open ? 'Hide data table' : 'View data table';
  });
  api.redraw = () => { if (width) draw(); if (!tableWrap.hidden) buildTable(); };
  const core = el('div', 'pr-fig-core');
  core.append(head, body, tableWrap, foot);
  root.append(core);
  if (typeof ResizeObserver === 'function') {
    new ResizeObserver(() => {
      const next = Math.round(host.clientWidth);
      if (next > 40 && Math.abs(next - width) >= 6) { width = next; draw(); }
    }).observe(host);
  } else {
    width = 640;
    queueMicrotask(draw);
  }
  whenVisible(root, () => root.classList.add('is-in'));
  return api;
}

/* ---------- shared drawing helpers ---------- */
function newSvg(ctx, height, label) {
  const svg = svgEl('svg', {class: 'pr-svg', width: ctx.width, height, viewBox: `0 0 ${ctx.width} ${height}`, preserveAspectRatio: 'xMinYMin meet', focusable: 'false'});
  svg.setAttribute('aria-label', label || 'Chart');
  return svg;
}
const delay = (node, ms) => { if (ms) node.style.transitionDelay = `${Math.round(ms)}ms`; return node; };
const dashIn = path => {
  let length = 0;
  try { length = path.getTotalLength(); } catch { length = 0; }
  if (length > 0) { path.setAttribute('stroke-dasharray', length.toFixed(1)); path.setAttribute('stroke-dashoffset', length.toFixed(1)); path.classList.add('pr-draw'); }
};
const textWidth = (text, px = 11) => String(text).length * px * 0.58;
function spread(labels, minGap, top, bottom) {
  const sorted = labels.slice().sort((a, b) => a.y - b.y);
  sorted.forEach((label, i) => { label.ty = i && sorted[i - 1].ty + minGap > label.y ? sorted[i - 1].ty + minGap : label.y; });
  const overflow = sorted.length ? sorted[sorted.length - 1].ty - bottom : 0;
  if (overflow > 0) sorted.forEach(label => { label.ty -= overflow; });
  sorted.forEach(label => { label.ty = Math.max(top, label.ty); });
  return sorted;
}

function wrapText(text, maxChars) {
  if (text.length <= maxChars) return [text];
  const lines = [];
  let line = '';
  for (const word of text.split(' ')) {
    if (line && `${line} ${word}`.length > maxChars) { lines.push(line); line = word; } else line = line ? `${line} ${word}` : word;
  }
  if (line) lines.push(line);
  if (lines.length > 2) { lines.length = 2; lines[1] = `${lines[1].slice(0, Math.max(1, maxChars - 1))}\u2026`; }
  return lines;
}
// Row label, right-aligned at x and centred on cy, wrapped to at most two lines plus an optional sub-label.
function rowLabel(svg, x, cy, label, sub, maxPx, hl) {
  const lines = wrapText(String(label), Math.max(8, Math.floor(maxPx / 6.9))).map(t => ({t, cls: `pr-t pr-t-row${hl ? ' is-hl' : ''}`}));
  if (sub) lines.push({t: sub.length > Math.floor(maxPx / 5.6) ? `${sub.slice(0, Math.max(4, Math.floor(maxPx / 5.6) - 1))}\u2026` : sub, cls: 'pr-t pr-t-sub'});
  const lh = 13.5, top = cy - (lines.length - 1) * lh / 2 + 4;
  lines.forEach((l, i) => svg.append(svgEl('text', {x, y: top + i * lh, class: l.cls, 'text-anchor': 'end'}, l.t)));
}

/* ---------- line chart (categorical x), multiple series, optional intervals ---------- */
// series: [{key,label,values:[number|null],cls,dash,ci:[[lo,hi]|null],focus}]
export function lineChart(host, ctx, o) {
  const W = ctx.width, compact = ctx.compact;
  const H = o.height || (compact ? 250 : 320);
  const m = {t: 18, r: compact ? 16 : (o.rightLabel ?? 132), b: 46, l: o.left ?? 50};
  const iw = W - m.l - m.r, ih = H - m.t - m.b;
  const n = o.periods.length;
  const values = o.series.flatMap(s => [...s.values.filter(finite), ...(s.ci || []).flatMap(c => c || [])]);
  let lo = Math.min(...values), hi = Math.max(...values);
  if (o.zero) lo = Math.min(0, lo);
  if (o.domain) [lo, hi] = o.domain;
  const ticks = niceTicks(lo, hi, compact ? 4 : 5);
  const d0 = ticks[0], d1 = ticks[ticks.length - 1];
  const x = i => m.l + (n === 1 ? iw / 2 : i * iw / (n - 1));
  const y = v => m.t + ih - (v - d0) / (d1 - d0) * ih;
  const svg = newSvg(ctx, H, o.label);
  const grid = svgEl('g', {class: 'pr-grid'});
  ticks.forEach(tick => {
    grid.append(svgEl('line', {x1: m.l, x2: W - m.r, y1: y(tick), y2: y(tick), class: tick === 0 ? 'pr-zero' : 'pr-gridline'}));
    grid.append(svgEl('text', {x: m.l - 8, y: y(tick) + 4, class: 'pr-t', 'text-anchor': 'end'}, (o.yFormat || fmt.int)(tick)));
  });
  svg.append(grid);
  if (o.yTitle) svg.append(svgEl('text', {x: m.l, y: 10, class: 'pr-t pr-t-axis'}, o.yTitle));
  const axis = svgEl('g', {class: 'pr-axis'});
  const every = iw / Math.max(1, n - 1) < 38 ? 2 : 1;
  o.periods.forEach((period, i) => {
    const isQ = /^\d{4}-Q\d$/.test(period);
    const q = isQ ? period.slice(-1) : null;
    if (i % every === 0 || i === n - 1) {
      axis.append(svgEl('line', {x1: x(i), x2: x(i), y1: m.t + ih, y2: m.t + ih + 4, class: 'pr-tick'}));
      axis.append(svgEl('text', {x: x(i), y: m.t + ih + 17, class: 'pr-t', 'text-anchor': 'middle'}, q ? `Q${q}` : period));
      if (isQ && (q === '1' || i === 0)) axis.append(svgEl('text', {x: x(i), y: m.t + ih + 31, class: 'pr-t pr-t-year', 'text-anchor': 'middle'}, period.slice(0, 4)));
    }
  });
  axis.append(svgEl('line', {x1: m.l, x2: W - m.r, y1: m.t + ih, y2: m.t + ih, class: 'pr-baseline'}));
  svg.append(axis);
  (o.refs || []).forEach(ref => {
    svg.append(svgEl('line', {x1: m.l, x2: W - m.r, y1: y(ref.value), y2: y(ref.value), class: 'pr-ref'}));
    svg.append(svgEl('text', {x: m.l + 4, y: y(ref.value) - 5, class: 'pr-t pr-t-brass'}, ref.label));
  });
  const marks = o.series.map(() => []);
  const ends = [];
  o.series.forEach((s, si) => {
    let d = '', pen = false;
    s.values.forEach((v, i) => { if (!finite(v)) { pen = false; return; } d += `${pen ? 'L' : 'M'}${x(i).toFixed(1)} ${y(v).toFixed(1)}`; pen = true; });
    const cls = `s-${s.cls || 'c1'}`;
    if (s.ci) s.ci.forEach((c, i) => { if (c) svg.append(svgEl('line', {x1: x(i), x2: x(i), y1: y(c[0]), y2: y(c[1]), class: `pr-whisker ${cls}`})); });
    const path = svgEl('path', {d, class: `pr-line ${cls}${s.dash ? ' is-dash' : ''}${s.focus ? ' is-focus' : ''}`, fill: 'none'});
    svg.append(path);
    if (!s.dash) dashIn(path); else path.classList.add('pr-fade');
    s.values.forEach((v, i) => {
      if (!finite(v)) return;
      const dot = svgEl('circle', {cx: x(i), cy: y(v), r: s.focus ? 4 : 3, class: `pr-dot pr-pop f-${s.cls || 'c1'}`});
      delay(dot, 500 + i * 40);
      svg.append(dot);
      marks[si][i] = dot;
    });
    const last = s.values.map((v, i) => finite(v) ? i : -1).filter(i => i >= 0).pop();
    const present = s.values.filter(finite).length;
    if (last !== undefined && present === 1 && last < n - 1) {
      svg.append(svgEl('text', {x: x(last) + 10, y: y(s.values[last]) + 20, class: `pr-t pr-label f-${s.cls || 'c1'}`}, s.label));
    } else if (last !== undefined) ends.push({s, y: y(s.values[last]), x: x(last), value: s.values[last]});
  });
  if (compact) ctx.legend(o.series.map(s => ({label: s.label, cls: s.cls, dash: s.dash})));
  else spread(ends, 14, m.t + 6, m.t + ih).forEach(label => {
    svg.append(svgEl('text', {x: label.x + 10, y: label.ty + 4, class: `pr-t pr-label f-${label.s.cls || 'c1'}`}, label.s.label));
  });
  (o.notes || []).forEach(note => {
    const nx = x(note.index), ny = y(note.value);
    svg.append(svgEl('circle', {cx: nx, cy: ny, r: 7, class: 'pr-ring'}));
    const side = note.side || (nx > W * 0.6 ? 'left' : 'right');
    const tx = side === 'left' ? nx - 12 : nx + 12, ty = ny + (note.dy ?? -16);
    svg.append(svgEl('text', {x: tx, y: ty, class: 'pr-t pr-t-brass', 'text-anchor': side === 'left' ? 'end' : 'start'}, note.text));
  });
  const items = o.periods.map((period, i) => {
    const hit = svgEl('rect', {x: x(i) - Math.max(10, iw / Math.max(1, n - 1) / 2), y: m.t, width: Math.max(20, iw / Math.max(1, n - 1)), height: ih, class: 'pr-col'});
    svg.append(hit);
    const lines = [o.periodLabel ? o.periodLabel(period) : fmt.quarter(period)];
    o.series.forEach(s => { if (finite(s.values[i])) lines.push(`${s.label}: ${(o.tipFormat || o.yFormat || fmt.int)(s.values[i])}${s.ci?.[i] ? ` (95% CI ${(o.tipFormat || o.yFormat || fmt.int)(s.ci[i][0])} to ${(o.tipFormat || o.yFormat || fmt.int)(s.ci[i][1])})` : ''}`); });
    if (o.extraLines?.[i]) lines.push(...o.extraLines[i]);
    const ys = o.series.map(s => s.values[i]).filter(finite);
    return {node: hit, lines, ax: x(i), ay: y(Math.max(...ys)), mark: marks.map(row => row[i]).filter(Boolean)};
  });
  host.append(svg);
  interactive(svg, ctx, items, {label: `${o.label || 'Line chart'}. Use left and right arrow keys to move between periods.`});
  return svg;
}

/* ---------- dot / lollipop / bar plot (horizontal), with optional intervals ---------- */
// rows: [{label, sub, value, ci:[lo,hi], n, cls, hl, lines:[...], group:true}]
export function dotPlot(host, ctx, o) {
  const W = ctx.width, compact = ctx.compact;
  const domain = o.domain || [0, 1];
  const rowH = o.rowH || (compact ? 34 : 36);
  const labelW = Math.min(compact ? W * 0.42 : 270, Math.max(compact ? 96 : 120, Math.max(...o.rows.map(r => textWidth(r.label, 12))) + 14));
  const m = {t: 22, r: compact ? 56 : 84, b: o.axisTitle ? 50 : 30, l: labelW};
  const iw = W - m.l - m.r;
  let cursor = m.t;
  const placed = o.rows.map(row => { const h = row.group ? 30 : rowH; const entry = {row, y: cursor, h}; cursor += h; return entry; });
  const H = cursor + m.b;
  const allTicks = o.ticks || niceTicks(domain[0], domain[1], compact ? 4 : 5).filter(t => t >= domain[0] - 1e-9 && t <= domain[1] + 1e-9);
  const ticks = allTicks.length > 1 && iw / (allTicks.length - 1) < 48 ? allTicks.filter((_, i) => i % 2 === 0) : allTicks;
  const x = v => m.l + (Math.min(domain[1], Math.max(domain[0], v)) - domain[0]) / (domain[1] - domain[0]) * iw;
  const base = o.baseline ?? domain[0];
  const svg = newSvg(ctx, H, o.label);
  ticks.forEach(t => {
    svg.append(svgEl('line', {x1: x(t), x2: x(t), y1: m.t - 6, y2: cursor, class: t === 0 && domain[0] < 0 ? 'pr-zero' : 'pr-gridline'}));
    svg.append(svgEl('text', {x: x(t), y: cursor + 18, class: 'pr-t', 'text-anchor': 'middle'}, (o.format || fmt.pct)(t, 0)));
  });
  if (o.axisTitle) svg.append(svgEl('text', {x: m.l, y: cursor + 40, class: 'pr-t pr-t-axis'}, o.axisTitle));
  (o.refs || []).forEach(ref => {
    svg.append(svgEl('line', {x1: x(ref.value), x2: x(ref.value), y1: m.t - 6, y2: cursor, class: 'pr-ref'}));
    svg.append(svgEl('text', {x: x(ref.value) + 5, y: m.t - 9, class: 'pr-t pr-t-brass'}, ref.label));
  });
  const items = [];
  let rank = 0;
  placed.forEach(({row, y, h}) => {
    if (row.group) {
      svg.append(svgEl('text', {x: 0, y: y + 20, class: 'pr-t pr-t-group'}, row.label));
      return;
    }
    const cy = y + h / 2;
    const cls = row.cls || 'c1';
    rowLabel(svg, m.l - 12, cy, row.label, row.sub, m.l - 18, row.hl);
    const mark = [];
    if (finite(row.value)) {
      const mode = o.mode || 'lollipop';
      if (mode === 'bar') {
        const bar = svgEl('rect', {x: Math.min(x(base), x(row.value)), y: cy - 8, width: Math.max(1, Math.abs(x(row.value) - x(base))), height: 16, rx: 3, class: `pr-bar pr-grow f-${row.hl ? 'brass' : cls}`});
        delay(bar, rank * 50);
        svg.append(bar);
        mark.push(bar);
      } else {
        const stem = svgEl('line', {x1: x(base), x2: x(row.value), y1: cy, y2: cy, class: `pr-stem s-${row.hl ? 'brass' : cls}`});
        svg.append(stem);
        const length = Math.abs(x(row.value) - x(base));
        if (length > 0) { stem.setAttribute('stroke-dasharray', length.toFixed(1)); stem.setAttribute('stroke-dashoffset', length.toFixed(1)); stem.classList.add('pr-draw'); delay(stem, rank * 50); }
      }
      if (row.ci && finite(row.ci[0]) && finite(row.ci[1])) {
        const whisk = svgEl('g', {class: `pr-ci s-${row.cross ? 'brass' : 'ink'} pr-fade`});
        whisk.append(svgEl('line', {x1: x(row.ci[0]), x2: x(row.ci[1]), y1: cy, y2: cy}));
        row.ci.forEach(v => whisk.append(svgEl('line', {x1: x(v), x2: x(v), y1: cy - 6, y2: cy + 6})));
        delay(whisk, 500 + rank * 50);
        svg.append(whisk);
      }
      const dot = svgEl('circle', {cx: x(row.value), cy, r: row.hl ? 6 : 5, class: `pr-dot pr-pop f-${row.hl ? 'brass' : cls}`});
      delay(dot, 350 + rank * 50);
      svg.append(dot);
      mark.push(dot);
      const right = Math.max(x(row.value), row.ci && finite(row.ci[1]) ? x(row.ci[1]) : 0);
      const text = (o.valueText ? o.valueText(row) : (o.format || fmt.pct)(row.value));
      const flip = right + 8 + textWidth(text, 12) > W - 2;
      svg.append(svgEl('text', {x: flip ? x(row.value) - 10 : right + 9, y: cy + 4, class: `pr-t pr-value${row.hl ? ' is-hl' : ''}`, 'text-anchor': flip ? 'end' : 'start'}, text));
    } else {
      svg.append(svgEl('text', {x: m.l + 6, y: cy + 4, class: 'pr-t'}, 'not recorded'));
    }
    const hit = svgEl('rect', {x: 0, y, width: W, height: h, class: 'pr-row-hit'});
    svg.append(hit);
    const lines = row.lines || [`${row.label}${row.sub ? ` (${row.sub})` : ''}`, (o.format || fmt.pct)(row.value)];
    items.push({node: hit, lines, ax: finite(row.value) ? x(row.value) : m.l, ay: cy, mark});
    rank++;
  });
  svg.append(svgEl('line', {x1: x(base), x2: x(base), y1: m.t - 6, y2: cursor, class: 'pr-baseline'}));
  host.append(svg);
  interactive(svg, ctx, items, {label: `${o.label || 'Dot plot'}. Use the arrow keys to move between rows.`});
  return svg;
}

/* ---------- dumbbell: several values per row on one scale ---------- */
// rows: [{label, sub, points:[{key,value,cls,label}], lines}]
export function dumbbell(host, ctx, o) {
  const W = ctx.width, compact = ctx.compact;
  const rowH = o.rowH || (compact ? 40 : 44);
  const labelW = Math.min(compact ? W * 0.3 : 210, Math.max(compact ? 80 : 110, Math.max(...o.rows.map(r => textWidth(r.label, 12))) + 14));
  const m = {t: 34, r: 24, b: 30, l: labelW};
  const iw = W - m.l - m.r, H = m.t + o.rows.length * rowH + m.b;
  const all = o.rows.flatMap(r => r.points.map(p => p.value)).filter(finite);
  const domain = o.domain || (() => { const t = niceTicks(Math.min(...all, 0), Math.max(...all), compact ? 3 : 5); return [t[0], t[t.length - 1]]; })();
  const ticks = niceTicks(domain[0], domain[1], compact ? 3 : 5);
  const x = v => m.l + (v - domain[0]) / (domain[1] - domain[0]) * iw;
  const svg = newSvg(ctx, H, o.label);
  ticks.forEach(t => {
    svg.append(svgEl('line', {x1: x(t), x2: x(t), y1: m.t - 8, y2: m.t + o.rows.length * rowH, class: t === 0 ? 'pr-zero' : 'pr-gridline'}));
    svg.append(svgEl('text', {x: x(t), y: m.t + o.rows.length * rowH + 18, class: 'pr-t', 'text-anchor': 'middle'}, (o.format || fmt.int)(t)));
  });
  const seen = new Map();
  const gaps = o.rows.map(r => { const xs = r.points.map(p => x(p.value)).filter(finite).sort((a, b) => a - b); return xs.length > 1 ? Math.min(...xs.slice(1).map((v, i) => v - xs[i])) : 0; });
  const labelRow = gaps.indexOf(Math.max(...gaps));
  const inline = !compact && Math.max(...gaps) >= 96;
  const items = [];
  o.rows.forEach((row, ri) => {
    const cy = m.t + ri * rowH + rowH / 2;
    rowLabel(svg, m.l - 12, cy, row.label, row.sub, m.l - 18);
    const vals = row.points.map(p => p.value).filter(finite);
    const lo = Math.min(...vals), hi = Math.max(...vals);
    const link = svgEl('line', {x1: x(lo), x2: x(hi), y1: cy, y2: cy, class: 'pr-link-line'});
    svg.append(link);
    const length = x(hi) - x(lo);
    if (length > 0) { link.setAttribute('stroke-dasharray', length.toFixed(1)); link.setAttribute('stroke-dashoffset', length.toFixed(1)); link.classList.add('pr-draw'); delay(link, ri * 60); }
    const marks = [];
    row.points.forEach(p => {
      if (!finite(p.value)) return;
      const dot = svgEl('circle', {cx: x(p.value), cy, r: 6, class: `pr-dot pr-pop f-${p.cls || 'c1'}`});
      delay(dot, 300 + ri * 60);
      svg.append(dot);
      marks.push(dot);
      if (inline && ri === labelRow && !seen.has(p.key)) {
        seen.set(p.key, true);
        svg.append(svgEl('text', {x: x(p.value), y: cy - 14, class: `pr-t pr-label f-${p.cls || 'c1'}`, 'text-anchor': 'middle'}, p.label || p.key));
      }
    });
    const hit = svgEl('rect', {x: 0, y: cy - rowH / 2, width: W, height: rowH, class: 'pr-row-hit'});
    svg.append(hit);
    items.push({node: hit, lines: row.lines, ax: x(hi), ay: cy, mark: marks});
  });
  if (!inline) ctx.legend([...new Map(o.rows.flatMap(r => r.points).map(p => [p.key, {label: p.label || p.key, cls: p.cls}])).values()]);
  host.append(svg);
  interactive(svg, ctx, items, {label: `${o.label || 'Comparison'}. Use the arrow keys to move between rows.`});
  return svg;
}

/* ---------- columns (vertical bars), optionally stacked ---------- */
// categories:[string], series:[{key,label,values,cls}]
export function columns(host, ctx, o) {
  const W = ctx.width, compact = ctx.compact;
  const H = o.height || (compact ? 230 : 280);
  const m = {t: 18, r: 12, b: o.bottom ?? 42, l: o.left ?? 46};
  const iw = W - m.l - m.r, ih = H - m.t - m.b;
  const n = o.categories.length;
  const totals = o.categories.map((_, i) => o.stacked ? o.series.reduce((sum, s) => sum + (finite(s.values[i]) ? s.values[i] : 0), 0) : Math.max(...o.series.map(s => finite(s.values[i]) ? s.values[i] : 0)));
  const ticks = niceTicks(0, o.max ?? Math.max(...totals), compact ? 4 : 5);
  const d1 = ticks[ticks.length - 1];
  const y = v => m.t + ih - v / d1 * ih;
  const band = iw / n;
  const groupW = Math.min(64, band * 0.72);
  const svg = newSvg(ctx, H, o.label);
  ticks.forEach(t => {
    svg.append(svgEl('line', {x1: m.l, x2: W - m.r, y1: y(t), y2: y(t), class: t === 0 ? 'pr-baseline' : 'pr-gridline'}));
    svg.append(svgEl('text', {x: m.l - 8, y: y(t) + 4, class: 'pr-t', 'text-anchor': 'end'}, (o.yFormat || fmt.int)(t)));
  });
  if (o.yTitle) svg.append(svgEl('text', {x: m.l, y: 10, class: 'pr-t pr-t-axis'}, o.yTitle));
  const items = [];
  o.categories.forEach((cat, i) => {
    const cx = m.l + band * i + band / 2;
    svg.append(svgEl('text', {x: cx, y: H - m.b + 17, class: 'pr-t', 'text-anchor': 'middle'}, cat));
    if (o.catSub?.[i]) svg.append(svgEl('text', {x: cx, y: H - m.b + 31, class: 'pr-t pr-t-year', 'text-anchor': 'middle'}, o.catSub[i]));
    let acc = 0;
    const marks = [];
    o.series.forEach((s, si) => {
      const v = s.values[i];
      if (!finite(v)) return;
      const w = o.stacked ? groupW : groupW / o.series.length;
      const bx = o.stacked ? cx - groupW / 2 : cx - groupW / 2 + si * w;
      const top = o.stacked ? y(acc + v) : y(v);
      const bottom = o.stacked ? y(acc) : y(0);
      const rect = svgEl('rect', {x: bx, y: top, width: Math.max(1, w - (o.stacked ? 0 : 2)), height: Math.max(0.5, bottom - top), class: `pr-bar pr-rise f-${s.hl?.includes(i) ? 'brass' : s.cls || 'c1'}`});
      delay(rect, i * 40);
      svg.append(rect);
      marks.push(rect);
      acc += v;
    });
    const hit = svgEl('rect', {x: cx - band / 2, y: m.t, width: band, height: ih, class: 'pr-col'});
    svg.append(hit);
    const lines = [o.tipTitle ? o.tipTitle(cat, i) : cat, ...o.series.map(s => `${s.label}: ${(o.tipFormat || o.yFormat || fmt.int)(s.values[i])}`)];
    if (o.stacked) lines.push(`Total: ${(o.tipFormat || o.yFormat || fmt.int)(totals[i])}`);
    if (o.extraLines?.[i]) lines.push(...o.extraLines[i]);
    items.push({node: hit, lines, ax: cx, ay: y(totals[i]), mark: marks});
  });
  ctx.legend(o.series.length > 1 ? o.series.map(s => ({label: s.label, cls: s.cls})) : []);
  host.append(svg);
  interactive(svg, ctx, items, {label: `${o.label || 'Column chart'}. Use left and right arrow keys to move between columns.`});
  return svg;
}

/* ---------- heatmap: rows x columns of rates with the case count in each cell ---------- */
// cols:[{key,label,sub}], rows:[{label,cells:[{value,n,lines}|null]}]
export function heatmap(host, ctx, o) {
  const W = ctx.width, compact = ctx.compact;
  const labelW = Math.min(compact ? W * 0.34 : 230, Math.max(100, Math.max(...o.rows.map(r => textWidth(r.label, 12))) + 14));
  const cellH = o.cellH || (compact ? 42 : 46);
  const rotateProbe = (W - labelW - 4) / o.cols.length < 56 && Math.max(...o.cols.map(c => String(c.short || c.label).length)) * 6.6 > (W - labelW - 4) / o.cols.length - 4;
  const headH = o.headH || (rotateProbe ? 66 : 52);
  const m = {t: headH, r: 4, b: 6, l: labelW};
  const cw = (W - m.l - m.r) / o.cols.length;
  const tight = cw < 56;
  const H = m.t + o.rows.length * cellH + m.b;
  const svg = newSvg(ctx, H, o.label);
  o.cols.forEach((col, c) => {
    const cx = m.l + cw * c + cw / 2;
    const text = String(tight && col.short ? col.short : col.label);
    if (rotateProbe) {
      svg.append(svgEl('text', {x: cx - 3, y: headH - 8, transform: `rotate(-40 ${cx - 3} ${headH - 8})`, class: 'pr-t pr-t-colhead', 'text-anchor': 'start'}, text));
      return;
    }
    const lines = wrapText(text, Math.max(6, Math.floor((cw - 8) / 7.4)));
    const base = col.sub ? headH - 26 : headH - 12;
    lines.forEach((line, i) => svg.append(svgEl('text', {x: cx, y: base - (lines.length - 1 - i) * 13, class: 'pr-t pr-t-colhead', 'text-anchor': 'middle'}, line)));
    if (col.sub && !tight) svg.append(svgEl('text', {x: cx, y: headH - 11, class: 'pr-t pr-t-sub', 'text-anchor': 'middle'}, col.sub));
  });
  const items = [];
  o.rows.forEach((row, r) => {
    const cy = m.t + r * cellH;
    rowLabel(svg, m.l - 12, cy + cellH / 2, row.label, null, m.l - 18);
    row.cells.forEach((cell, c) => {
      const cx = m.l + cw * c;
      if (!cell || !finite(cell.value)) {
        svg.append(svgEl('rect', {x: cx + 2, y: cy + 2, width: cw - 4, height: cellH - 4, rx: 5, class: 'pr-cell is-empty'}));
        return;
      }
      const level = cell.tone === 'bad' ? 0 : Math.min(5, Math.floor((o.invert ? 1 - cell.value : cell.value) * 6));
      const rect = svgEl('rect', {x: cx + 2, y: cy + 2, width: cw - 4, height: cellH - 4, rx: 5, class: `pr-cell pr-fade ${cell.tone === 'bad' ? 'is-bad' : `lv${level}`}`});
      delay(rect, (r * o.cols.length + c) * 14);
      svg.append(rect);
      const dark = cell.tone === 'bad' || level >= 3;
      const sub = cell.sub ?? (finite(cell.n) ? `n=${cell.n}` : '');
      svg.append(svgEl('text', {x: cx + cw / 2, y: cy + cellH / 2 + (sub ? 1 : 5), class: `pr-t pr-cell-value${dark ? ' is-dark' : ''}${tight ? ' is-tight' : ''}`, 'text-anchor': 'middle'}, cell.text ?? (o.format || fmt.pct)(cell.value, tight ? 0 : 1)));
      if (sub) svg.append(svgEl('text', {x: cx + cw / 2, y: cy + cellH / 2 + 14, class: `pr-t pr-cell-n${dark ? ' is-dark' : ''}`, 'text-anchor': 'middle'}, sub));
      const hit = svgEl('rect', {x: cx + 2, y: cy + 2, width: cw - 4, height: cellH - 4, rx: 5, class: 'pr-cell-hit'});
      svg.append(hit);
      items.push({node: hit, lines: cell.lines, ax: cx + cw / 2, ay: cy + cellH / 2, mark: [rect], r, c});
    });
  });
  host.append(svg);
  interactive(svg, ctx, items, {label: `${o.label || 'Heatmap'}. Use the arrow keys to move between cells.`, cols: o.rows.every(r => r.cells.every(c => c && finite(c.value))) ? o.cols.length : 0});
  return svg;
}

/* ---------- stacked 100% bars (shares of a whole) ---------- */
// rows:[{label,sub,segments:[{key,label,value,cls}]}]
export function shareBars(host, ctx, o) {
  const W = ctx.width, compact = ctx.compact;
  const rowH = o.rowH || (compact ? 44 : 48);
  const labelW = Math.min(compact ? W * 0.4 : 200, Math.max(90, Math.max(...o.rows.map(r => textWidth(r.label, 12))) + 14));
  const m = {t: 8, r: 8, b: 8, l: labelW};
  const iw = W - m.l - m.r, H = m.t + o.rows.length * rowH + m.b;
  const svg = newSvg(ctx, H, o.label);
  const items = [];
  const unlabeled = new Map();
  o.rows.forEach((row, ri) => {
    const cy = m.t + ri * rowH;
    rowLabel(svg, m.l - 12, cy + rowH / 2, row.label, row.sub, m.l - 18);
    const total = row.segments.reduce((sum, s) => sum + (finite(s.value) ? s.value : 0), 0) || 1;
    let acc = 0;
    const marks = [];
    row.segments.forEach(seg => {
      if (!finite(seg.value) || seg.value <= 0) return;
      const w = seg.value / total * iw;
      const rect = svgEl('rect', {x: m.l + acc / total * iw, y: cy + 9, width: Math.max(1, w - 1.5), height: rowH - 18, rx: 3, class: `pr-bar pr-grow f-${seg.cls || 'c1'}`});
      delay(rect, ri * 60);
      svg.append(rect);
      marks.push(rect);
      const full = `${seg.value} ${seg.label}`;
      const fits = w - 1.5 > textWidth(full, 11.5) + 16;
      if (w > 26) svg.append(svgEl('text', {x: m.l + acc / total * iw + w / 2, y: cy + rowH / 2 + 4, class: 'pr-t pr-seg-value', 'text-anchor': 'middle'}, fits ? full : String(seg.value)));
      if (!fits) unlabeled.set(`${seg.cls}|${seg.label}`, {label: seg.label, cls: seg.cls});
      acc += seg.value;
    });
    const hit = svgEl('rect', {x: 0, y: cy, width: W, height: rowH, class: 'pr-row-hit'});
    svg.append(hit);
    items.push({node: hit, lines: row.lines || [row.label, ...row.segments.map(s => `${s.label}: ${s.value}`)], ax: m.l + iw / 2, ay: cy + rowH / 2, mark: marks});
  });
  ctx.legend([...unlabeled.values()]);
  host.append(svg);
  interactive(svg, ctx, items, {label: `${o.label || 'Share bars'}. Use the arrow keys to move between rows.`});
  return svg;
}

/* ---------- box + whisker strip, one row per group ---------- */
// rows:[{label,sub,q:{p5,p25,p50,p75,p95,max},n,cls,lines}]
export function boxStrip(host, ctx, o) {
  const W = ctx.width, compact = ctx.compact;
  const rowH = o.rowH || 34;
  const labelW = Math.min(compact ? W * 0.34 : 190, Math.max(100, Math.max(...o.rows.map(r => textWidth(r.label, 12))) + 14));
  const m = {t: 20, r: 16, b: 32, l: labelW};
  const iw = W - m.l - m.r, H = m.t + o.rows.length * rowH + m.b;
  const top = Math.max(...o.rows.map(r => r.q.p95));
  const ticks = niceTicks(0, o.max ?? top * 1.08, compact ? 4 : 6);
  const d1 = ticks[ticks.length - 1];
  const x = v => m.l + Math.min(v, d1) / d1 * iw;
  const svg = newSvg(ctx, H, o.label);
  ticks.forEach(t => {
    svg.append(svgEl('line', {x1: x(t), x2: x(t), y1: m.t - 6, y2: m.t + o.rows.length * rowH, class: 'pr-gridline'}));
    svg.append(svgEl('text', {x: x(t), y: m.t + o.rows.length * rowH + 18, class: 'pr-t', 'text-anchor': 'middle'}, (o.format || fmt.int)(t)));
  });
  if (o.axisTitle) svg.append(svgEl('text', {x: m.l, y: 10, class: 'pr-t pr-t-axis'}, o.axisTitle));
  const items = [];
  o.rows.forEach((row, ri) => {
    const cy = m.t + ri * rowH + rowH / 2;
    rowLabel(svg, m.l - 12, cy, row.label, null, m.l - 18, row.hl);
    const g = svgEl('g', {class: 'pr-box pr-fade'});
    delay(g, ri * 50);
    g.append(svgEl('line', {x1: x(row.q.p5), x2: x(row.q.p95), y1: cy, y2: cy, class: 'pr-whisker-line'}));
    g.append(svgEl('rect', {x: x(row.q.p25), y: cy - 8, width: Math.max(1.5, x(row.q.p75) - x(row.q.p25)), height: 16, rx: 3, class: `pr-box-body f-${row.hl ? 'brass' : row.cls || 'c1'}`}));
    g.append(svgEl('line', {x1: x(row.q.p50), x2: x(row.q.p50), y1: cy - 8, y2: cy + 8, class: 'pr-median'}));
    svg.append(g);
    const hit = svgEl('rect', {x: 0, y: cy - rowH / 2, width: W, height: rowH, class: 'pr-row-hit'});
    svg.append(hit);
    items.push({node: hit, lines: row.lines, ax: x(row.q.p50), ay: cy, mark: [g]});
  });
  host.append(svg);
  interactive(svg, ctx, items, {label: `${o.label || 'Distribution'}. Use the arrow keys to move between rows.`});
  return svg;
}

/* ---------- scatter with direct labels ---------- */
// points:[{key,label,x,y,cls,hl,lines}]
export function scatter(host, ctx, o) {
  const W = ctx.width, compact = ctx.compact;
  const H = o.height || (compact ? 290 : 360);
  const m = {t: 22, r: compact ? 20 : 40, b: 48, l: 54};
  const iw = W - m.l - m.r, ih = H - m.t - m.b;
  const xs = o.points.map(p => p.x), ys = o.points.map(p => p.y);
  const lx = o.logX ? Math.log10 : v => v;
  const xmin = o.xDomain?.[0] ?? Math.min(...xs) * (o.logX ? 0.8 : 1), xmax = o.xDomain?.[1] ?? Math.max(...xs) * (o.logX ? 1.25 : 1.05);
  const yt = niceTicks(o.yDomain?.[0] ?? Math.min(...ys), o.yDomain?.[1] ?? Math.max(...ys), compact ? 4 : 5);
  const y0 = yt[0], y1 = yt[yt.length - 1];
  const x = v => m.l + (lx(v) - lx(xmin)) / (lx(xmax) - lx(xmin)) * iw;
  const y = v => m.t + ih - (v - y0) / (y1 - y0) * ih;
  const svg = newSvg(ctx, H, o.label);
  yt.forEach(t => {
    svg.append(svgEl('line', {x1: m.l, x2: W - m.r, y1: y(t), y2: y(t), class: 'pr-gridline'}));
    svg.append(svgEl('text', {x: m.l - 8, y: y(t) + 4, class: 'pr-t', 'text-anchor': 'end'}, (o.yFormat || fmt.pct)(t, 0)));
  });
  (o.xTicks || niceTicks(xmin, xmax, 5)).forEach(t => {
    if (t < xmin || t > xmax) return;
    svg.append(svgEl('line', {x1: x(t), x2: x(t), y1: m.t, y2: m.t + ih, class: 'pr-gridline'}));
    svg.append(svgEl('text', {x: x(t), y: m.t + ih + 17, class: 'pr-t', 'text-anchor': 'middle'}, (o.xFormat || fmt.int)(t)));
  });
  svg.append(svgEl('line', {x1: m.l, x2: W - m.r, y1: m.t + ih, y2: m.t + ih, class: 'pr-baseline'}));
  svg.append(svgEl('text', {x: m.l + iw / 2, y: H - 6, class: 'pr-t pr-t-axis', 'text-anchor': 'middle'}, o.xTitle || ''));
  svg.append(svgEl('text', {x: m.l, y: 11, class: 'pr-t pr-t-axis'}, o.yTitle || ''));
  const items = [];
  const labels = o.points.map(p => ({p, x: x(p.x), y: y(p.y)}));
  labels.forEach(({p, x: px, y: py}, i) => {
    const dot = svgEl('circle', {cx: px, cy: py, r: p.hl ? 8 : 6.5, class: `pr-dot pr-pop f-${p.hl ? 'brass' : p.cls || 'c1'}`});
    delay(dot, i * 70);
    svg.append(dot);
    const right = px + 12 + textWidth(p.label, 11) < W - 4;
    svg.append(svgEl('text', {x: right ? px + 11 : px - 11, y: py - 9, class: `pr-t pr-label${p.hl ? ' is-hl' : ''}`, 'text-anchor': right ? 'start' : 'end'}, p.label));
    const hit = svgEl('circle', {cx: px, cy: py, r: 16, class: 'pr-hit-dot'});
    svg.append(hit);
    items.push({node: hit, lines: p.lines, ax: px, ay: py, mark: [dot]});
  });
  host.append(svg);
  interactive(svg, ctx, items, {label: `${o.label || 'Scatter plot'}. Use the arrow keys to move between points.`});
  return svg;
}

/* ---------- sparkline (static, decorative; the values are in the adjacent text) ---------- */
export function sparkline(values, {width = 120, height = 34, cls = 'c1'} = {}) {
  const svg = svgEl('svg', {class: 'pr-spark', width, height, viewBox: `0 0 ${width} ${height}`, 'aria-hidden': 'true', focusable: 'false'});
  const clean = values.filter(finite);
  if (clean.length < 2) return svg;
  const lo = Math.min(...clean), hi = Math.max(...clean), span = hi - lo || 1;
  const x = i => 3 + i * (width - 6) / (values.length - 1);
  const y = v => height - 4 - (v - lo) / span * (height - 8);
  let d = '';
  values.forEach((v, i) => { if (finite(v)) d += `${d ? 'L' : 'M'}${x(i).toFixed(1)} ${y(v).toFixed(1)}`; });
  const path = svgEl('path', {d, class: `pr-line s-${cls}`, fill: 'none'});
  svg.append(path);
  const last = values.length - 1;
  if (finite(values[last])) svg.append(svgEl('circle', {cx: x(last), cy: y(values[last]), r: 2.6, class: `f-${cls}`}));
  return svg;
}
