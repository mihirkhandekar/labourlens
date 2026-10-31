// Small DOM builders shared by the presentation chapters. Text only: never HTML strings.
import {el, finite, fmt, reduced} from '../charts.js';

export const append = (parent, ...children) => { children.filter(Boolean).forEach(child => parent.append(child)); return parent; };

/** A chapter opens with an action title (one sentence stating the finding) and 2 to 4 terse bullets. */
export function chapter({id, title, bullets}) {
  const root = el('section', 'pr-chapter');
  root.id = `pr-${id}`;
  root.dataset.chapter = id;
  const head = el('header', 'pr-chapter-head');
  const heading = el('h3', 'pr-chapter-title', title);
  heading.id = `pr-${id}-title`;
  root.setAttribute('aria-labelledby', heading.id);
  append(head, heading, Array.isArray(bullets) && bullets.length ? bulletList(bullets, 'pr-list pr-lede') : null);
  const body = el('div', 'pr-chapter-body');
  root.append(head, body);
  return {root, body, head};
}

function bulletList(items, cls) {
  const ul = el('ul', cls);
  items.forEach(text => ul.append(el('li', '', text)));
  return ul;
}

/** A block under a chapter. `title` is an action title; `intro` is an optional array of terse bullets or one short line. */
export function section(title, intro) {
  const root = el('div', 'pr-block');
  const head = el('div', 'pr-block-head');
  head.append(el('h4', 'pr-block-title', title));
  if (Array.isArray(intro) && intro.length) head.append(bulletList(intro, 'pr-list pr-block-intro'));
  else if (intro) head.append(el('p', 'pr-block-intro', intro));
  root.append(head);
  return root;
}

export function evi(path) {
  return el('span', 'pr-evi', path);
}

/** Returns a function that counts the number up from zero once, or sets the final text under reduced motion. */
export function countRunner(node, value, format, duration = 900) {
  node.textContent = format(value);
  return () => {
    if (reduced() || !finite(value)) { node.textContent = format(value); return; }
    const start = performance.now();
    const step = now => {
      const t = Math.min(1, (now - start) / duration);
      node.textContent = t < 1 ? format(value * (1 - (1 - t) ** 3)) : format(value);
      if (t < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  };
}

export function stat({value, format = fmt.int, label, note, src, tone, big}) {
  const root = el('div', `pr-stat${tone ? ` is-${tone}` : ''}${big ? ' is-big' : ''}`);
  const number = el('div', 'pr-stat-value num');
  number._run = countRunner(number, value, format);
  root.append(number, el('div', 'pr-stat-label', label));
  if (note) root.append(el('p', 'pr-stat-note', note));
  if (src) root.append(evi(src));
  return root;
}

export function textStat({text, label, note, src, tone}) {
  const root = el('div', `pr-stat${tone ? ` is-${tone}` : ''}`);
  root.append(el('div', 'pr-stat-value num', text), el('div', 'pr-stat-label', label));
  if (note) root.append(el('p', 'pr-stat-note', note));
  if (src) root.append(evi(src));
  return root;
}

export function bezel(...children) {
  const outer = el('div', 'bezel pr-bezel');
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
  const root = el('aside', `pr-callout is-${tone}`);
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

// Phosphor icons (vendor/phosphor) drawn as a CSS mask, so they take the text colour.
const ICONS = {play: 'play', pause: 'pause', prev: 'caret-left', next: 'caret-right', reset: 'arrow-counter-clockwise'};
export function icon(name, cls = 'pr-icon') {
  const node = el('span', cls);
  node.setAttribute('aria-hidden', 'true');
  node.style.setProperty('--ico', `url("/static/vendor/phosphor/${ICONS[name] || 'caret-right'}.svg")`);
  return node;
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
