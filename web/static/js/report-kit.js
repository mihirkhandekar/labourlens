// Building blocks for the report page: bands, sub-steps, the scaled stage for the deck graphics,
// details blocks, rows and tables. Text goes in through textContent only; no helper accepts markup.
import {el, add} from './dom.js';

/** An editorial band: a heading, a short paragraph, a visual area and a place for details. */
export function band({id, title, lede, layout = 'stack', tint = false}) {
  const node = el('section', `rp-band is-${layout}${tint ? ' is-tint' : ''}`);
  node.id = id;
  const inner = el('div', 'rp-inner');
  const head = el('header', 'rp-head reveal');
  const heading = el('h2', 'rp-title', title);
  heading.id = `${id}-title`;
  heading.tabIndex = -1;
  node.setAttribute('aria-labelledby', heading.id);
  head.append(heading);
  (Array.isArray(lede) ? lede : [lede]).filter(Boolean).forEach(text => head.append(el('p', 'rp-lede', text)));
  const visual = el('div', 'rp-visual');
  inner.append(head, visual);
  node.append(inner);
  return {node, inner, head, visual, id};
}

/** A graphic from the presentation. It was drawn for a 1920 px slide, so on wide screens it is scaled to fit
 *  its column (CSS zoom); on narrow screens the presentation's own small-screen rules apply and wide drawings scroll. */
export function stage(node, {design = 1680, label} = {}) {
  const box = el('div', 'rp-stage reveal');
  if (label) { box.setAttribute('role', 'group'); box.setAttribute('aria-label', label); }
  const canvas = el('div', 'rp-canvas');
  canvas.append(node);
  box.append(canvas);
  const narrow = matchMedia('(max-width: 800px)');
  const fit = () => {
    const width = box.clientWidth;
    if (!width) return;
    box.classList.toggle('is-fluid', narrow.matches);
    if (narrow.matches) {
      canvas.style.removeProperty('zoom'); canvas.style.removeProperty('width');
      // A drawing that scrolls sideways must be reachable from the keyboard.
      if (box.scrollWidth > width + 2) box.tabIndex = 0; else box.removeAttribute('tabindex');
      return;
    }
    box.removeAttribute('tabindex');
    const zoom = Math.min(1, width / design);
    canvas.style.setProperty('zoom', zoom.toFixed(4));
    canvas.style.setProperty('width', `${Math.round(width / zoom)}px`);
  };
  if (typeof ResizeObserver === 'function') new ResizeObserver(fit).observe(box);
  narrow.addEventListener('change', fit);
  return box;
}

/** A chart or table built by the chart kit. It draws at its own width, so it needs no scaling. */
export function chartBox(node) {
  const box = el('div', 'rp-chart reveal');
  box.append(node);
  return box;
}

/** A numbered-free sub-step inside a band: a small heading, one or two sentences and a visual. */
export function sub(title, text, visual, {note} = {}) {
  const node = el('div', 'rp-sub');
  const copy = el('div', 'rp-sub-copy reveal');
  copy.append(el('h3', 'rp-sub-title', title));
  (Array.isArray(text) ? text : [text]).filter(Boolean).forEach(t => copy.append(el('p', '', t)));
  if (note) copy.append(el('p', 'rp-note', note));
  node.append(copy);
  if (visual) node.append(visual);
  return node;
}

/** Collapsed detail under a band. `children` are DOM nodes. */
export function more(summary, ...children) {
  const node = el('details', 'rp-more');
  node.append(el('summary', '', summary));
  const body = el('div', 'rp-more-body');
  children.filter(Boolean).forEach(child => body.append(child));
  node.append(body);
  return node;
}

/** Heading, optional paragraph and content, inside a details body. */
export function group(title, ...children) {
  const node = el('div', 'rp-group');
  if (title) node.append(el('h4', 'rp-group-title', title));
  children.filter(Boolean).forEach(child => node.append(typeof child === 'string' ? el('p', '', child) : child));
  return node;
}

/** Label and sentence rows. items: [[head, body]]. */
export function rows(items) {
  const ul = el('ul', 'rp-rows');
  items.filter(Boolean).forEach(([head, body]) => {
    const li = el('li', 'reveal');
    li.append(el('strong', '', head), el('span', '', body));
    ul.append(li);
  });
  return ul;
}

/** Big numbers. items: [{value, label, note}]. */
export function statRow(items, {cols} = {}) {
  const wrap = el('ul', `rp-stats${cols ? ` has-${cols}` : ''}`);
  items.filter(Boolean).forEach(({value, label, note}) => {
    const li = el('li', 'rp-stat reveal');
    li.append(el('span', 'rp-stat-num num', value), el('span', 'rp-stat-label', label));
    if (note) li.append(el('span', 'rp-stat-note', note));
    wrap.append(li);
  });
  return wrap;
}

/** A plain table: header row, then rows of strings. */
export function table(caption, columns, body) {
  const scroll = el('div', 'rp-table-scroll');
  const t = el('table', 'rp-table');
  t.append(el('caption', '', caption));
  const head = el('tr');
  columns.forEach(name => { const th = el('th', '', name); th.scope = 'col'; head.append(th); });
  const thead = el('thead'); thead.append(head);
  const tbody = el('tbody');
  body.forEach(row => {
    const tr = el('tr');
    row.forEach((cell, i) => {
      const node = el(i ? 'td' : 'th', '', cell);
      if (!i) node.scope = 'row';
      tr.append(node);
    });
    tbody.append(tr);
  });
  t.append(thead, tbody);
  scroll.append(t);
  return scroll;
}

/** Commands as a block of code lines. */
export function commands(lines) {
  const pre = el('pre', 'rp-code reveal');
  const code = el('code', '', lines.join('\n'));
  pre.append(code);
  pre.tabIndex = 0;
  pre.setAttribute('aria-label', 'Commands');
  return pre;
}

export function link(label, href, {external = false} = {}) {
  const a = el('a', 'rp-link', label);
  a.href = href;
  if (external) { a.target = '_blank'; a.rel = 'noopener noreferrer'; }
  return a;
}

export function note(text) { return el('p', 'rp-note', text); }
export { el, add };
