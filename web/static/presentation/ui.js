// Small DOM builders shared by the presentation chapters. Text only: never HTML strings.
import {el, svgEl, countUp, fmt, finite} from '../charts.js';

export const append = (parent, ...children) => { children.filter(Boolean).forEach(child => parent.append(child)); return parent; };

export function chapter({id, no, title, lede, eyebrow}) {
  const root = el('section', 'pr-chapter');
  root.id = `pr-${id}`;
  root.dataset.chapter = id;
  const head = el('header', 'pr-chapter-head pr-reveal');
  const number = el('span', 'pr-chapter-no', String(no).padStart(2, '0'));
  number.setAttribute('aria-hidden', 'true');
  const text = el('div', 'pr-chapter-text');
  const tag = el('p', 'eyebrow', eyebrow || `Chapter ${no}`);
  const heading = el('h3', 'pr-chapter-title', title);
  heading.id = `pr-${id}-title`;
  root.setAttribute('aria-labelledby', heading.id);
  append(text, tag, heading, lede ? el('p', 'pr-lede', lede) : null);
  append(head, number, text);
  const body = el('div', 'pr-chapter-body');
  root.append(head, body);
  return {root, body, head};
}

export function section(title, intro) {
  const root = el('div', 'pr-block');
  const head = el('div', 'pr-block-head pr-reveal');
  head.append(el('h4', 'pr-block-title', title));
  if (intro) head.append(el('p', 'pr-block-intro', intro));
  root.append(head);
  return root;
}

export function evi(path) {
  return el('span', 'pr-evi', path);
}

export function stat({value, format = fmt.int, label, note, src, tone, big}) {
  const root = el('div', `pr-stat pr-reveal${tone ? ` is-${tone}` : ''}${big ? ' is-big' : ''}`);
  const number = el('div', 'pr-stat-value num');
  countUp(number, value, format);
  root.append(number, el('div', 'pr-stat-label', label));
  if (note) root.append(el('p', 'pr-stat-note', note));
  if (src) root.append(evi(src));
  return root;
}

export function textStat({text, label, note, src, tone}) {
  const root = el('div', `pr-stat pr-reveal${tone ? ` is-${tone}` : ''}`);
  root.append(el('div', 'pr-stat-value num', text), el('div', 'pr-stat-label', label));
  if (note) root.append(el('p', 'pr-stat-note', note));
  if (src) root.append(evi(src));
  return root;
}

export function bezel(...children) {
  const outer = el('div', 'bezel pr-bezel pr-reveal');
  const core = el('div', 'bezel-core');
  append(core, ...children);
  outer.append(core);
  return {root: outer, core};
}

export function grid(cls, ...children) {
  const root = el('div', `pr-grid-layout ${cls || ''}`.trim());
  append(root, ...children);
  return root;
}

export function callout({tone = 'note', title, text, items, src}) {
  const root = el('aside', `pr-callout is-${tone} pr-reveal`);
  const rule = el('span', 'pr-callout-rule');
  rule.setAttribute('aria-hidden', 'true');
  const body = el('div', 'pr-callout-body');
  if (title) body.append(el('h5', 'pr-callout-title', title));
  if (text) body.append(el('p', '', text));
  if (items?.length) {
    const list = el('ul', 'pr-list');
    items.forEach(item => list.append(el('li', '', item)));
    body.append(list);
  }
  if (src) body.append(evi(src));
  root.append(rule, body);
  return root;
}

export function details(summary, ...children) {
  const root = el('details', 'pr-details');
  root.append(el('summary', '', summary));
  const inner = el('div', 'pr-details-body');
  append(inner, ...children);
  root.append(inner);
  return root;
}

export function list(items, cls = 'pr-list') {
  const ul = el('ul', cls);
  items.forEach(item => ul.append(el('li', '', item)));
  return ul;
}

// Segmented single-choice control (radio group built from buttons).
export function segmented(label, options, selected, onChange) {
  const root = el('div', 'pr-seg');
  root.setAttribute('role', 'radiogroup');
  root.setAttribute('aria-label', label);
  const buttons = options.map(option => {
    const button = el('button', 'pr-seg-btn', option.label);
    button.type = 'button';
    button.setAttribute('role', 'radio');
    button.dataset.value = option.value;
    root.append(button);
    return button;
  });
  const apply = value => buttons.forEach(button => {
    const on = button.dataset.value === value;
    button.setAttribute('aria-checked', String(on));
    button.tabIndex = on ? 0 : -1;
    button.classList.toggle('is-on', on);
  });
  buttons.forEach((button, index) => {
    button.addEventListener('click', () => { apply(button.dataset.value); onChange(button.dataset.value); });
    button.addEventListener('keydown', event => {
      const step = {ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1}[event.key];
      if (!step) return;
      event.preventDefault();
      const next = buttons[(index + step + buttons.length) % buttons.length];
      next.focus();
      next.click();
    });
  });
  apply(selected);
  return root;
}

export function toggle(label, pressed, onChange) {
  const button = el('button', 'pr-toggle');
  button.type = 'button';
  const knob = el('span', 'pr-toggle-knob');
  knob.setAttribute('aria-hidden', 'true');
  button.append(knob, el('span', 'pr-toggle-label', label));
  const set = value => { button.setAttribute('aria-pressed', String(value)); };
  set(pressed);
  button.addEventListener('click', () => { const next = button.getAttribute('aria-pressed') !== 'true'; set(next); onChange(next); });
  return button;
}

export function selectField(label, options, value, onChange) {
  const wrap = el('label', 'pr-select');
  wrap.append(el('span', 'pr-select-label', label));
  const select = el('select', 'pr-select-input');
  options.forEach(option => {
    const node = el('option', '', option.label);
    node.value = option.value;
    select.append(node);
  });
  select.value = value;
  select.addEventListener('change', () => onChange(select.value));
  wrap.append(select);
  return {root: wrap, select};
}

export function chips(entries) {
  const row = el('ul', 'pr-chips');
  entries.forEach(entry => {
    const li = el('li', `pr-chip${entry.tone ? ` is-${entry.tone}` : ''}`);
    if (entry.cls) li.append(el('i', `pr-swatch ${entry.cls}`));
    li.append(el('span', '', entry.label));
    row.append(li);
  });
  return row;
}

export function dataTable(caption, columns, rows) {
  const scroll = el('div', 'pr-table-scroll');
  const table = el('table', 'pr-table');
  table.append(el('caption', '', caption));
  const head = el('tr');
  columns.forEach((name, i) => { const th = el('th', i ? 'is-num' : '', name); th.scope = 'col'; head.append(th); });
  const thead = el('thead'); thead.append(head);
  const tbody = el('tbody');
  rows.forEach(row => {
    const tr = el('tr');
    row.forEach((cell, i) => {
      const node = i ? el('td', 'is-num', cell) : el('th', '', cell);
      if (!i) node.scope = 'row';
      tr.append(node);
    });
    tbody.append(tr);
  });
  table.append(thead, tbody);
  scroll.append(table);
  return scroll;
}

// Tiny line icons (hairline strokes). Drawn here, no icon library.
const ICONS = {
  arrow: 'M5 12h14M13 6l6 6-6 6',
  down: 'M12 5v14M6 13l6 6 6-6',
  print: 'M7 9V4h10v5M7 17H5a1 1 0 0 1-1-1v-5a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v5a1 1 0 0 1-1 1h-2M7 14h10v6H7z',
  eye: 'M2 12s3.6-6.5 10-6.5S22 12 22 12s-3.6 6.5-10 6.5S2 12 2 12zM12 9.2a2.8 2.8 0 1 0 0 5.6 2.8 2.8 0 0 0 0-5.6z',
  shield: 'M12 3l7 3v5.5c0 4.4-3 7.8-7 9.5-4-1.7-7-5.1-7-9.5V6z',
  play: 'M8 5l11 7-11 7z',
  pause: 'M8 5v14M16 5v14',
  prev: 'M15 6l-6 6 6 6',
  next: 'M9 6l6 6-6 6',
  reset: 'M5 12a7 7 0 1 0 2.1-5M5 4v4h4'
};
export function icon(name, cls = 'pr-icon') {
  const svg = svgEl('svg', {class: cls, viewBox: '0 0 24 24', 'aria-hidden': 'true', focusable: 'false'});
  svg.append(svgEl('path', {d: ICONS[name] || ICONS.arrow}));
  return svg;
}

export function button(label, {iconName, kind = '', onClick, pressed} = {}) {
  const btn = el('button', `btn pr-btn ${kind}`.trim());
  btn.type = 'button';
  btn.append(el('span', '', label));
  if (iconName) {
    const ico = el('span', 'btn-ico');
    ico.append(icon(iconName, 'icon'));
    btn.append(ico);
  }
  if (pressed !== undefined) btn.setAttribute('aria-pressed', String(pressed));
  if (onClick) btn.addEventListener('click', onClick);
  return btn;
}

export const humanize = fmt.human;
export const isNum = finite;
