// Small DOM helpers. Text always goes in through textContent; no helper accepts markup.
export const el = (tag, className, text) => {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = text;
  return node;
};
export const add = (parent, ...children) => { parent.append(...children.filter(Boolean)); return parent; };
export const attrs = (node, map) => { Object.entries(map).forEach(([key, value]) => node.setAttribute(key, String(value))); return node; };
const SVG_NS = 'http://www.w3.org/2000/svg';
export const svg = (tag, map = {}, text) => {
  const node = document.createElementNS(SVG_NS, tag);
  Object.entries(map).forEach(([key, value]) => node.setAttribute(key, String(value)));
  if (text !== undefined) node.textContent = text;
  return node;
};
/** An icon from the sprite in index.html. */
export const icon = (name, className = '') => {
  const node = svg('svg', {class: `icon ${className}`.trim(), 'aria-hidden': 'true', focusable: 'false'});
  node.append(svg('use', {href: `#i-${name}`}));
  return node;
};
export const button = (label, onClick, className = '', iconName) => {
  const node = el('button', className);
  node.type = 'button';
  if (iconName) {
    node.append(el('span', '', label));
    const wrap = el('span', 'btn-ico'); wrap.append(icon(iconName)); node.append(wrap);
  } else node.textContent = label;
  if (onClick) node.addEventListener('click', onClick);
  return node;
};
/** Link-styled button with a nested trailing icon circle. */
export const cta = (label, href, className = 'btn', iconName = 'arrow-ur') => {
  const node = el('a', className);
  node.href = href;
  node.append(el('span', '', label));
  const wrap = el('span', 'btn-ico'); wrap.append(icon(iconName)); node.append(wrap);
  return node;
};
export const safeLink = (url, label, className = 'source-link') => {
  let parsed;
  try { parsed = new URL(String(url)); } catch { return null; }
  if (parsed.protocol !== 'https:') return null;
  const link = el('a', className);
  link.href = parsed.href; link.target = '_blank'; link.rel = 'noopener noreferrer';
  link.append(el('span', '', label || parsed.hostname), icon('external'));
  return link;
};

export const finite = value => typeof value === 'number' && Number.isFinite(value);
const numberFormat = new Intl.NumberFormat('en-SG', {maximumFractionDigits: 6});
export const fmt = value => finite(value) ? numberFormat.format(value) : 'No value';
export const UNIT_LABEL = {percent: '%', persons: 'persons', vacancies: 'vacancies', ratio: 'ratio'};
export const fmtUnit = (value, unit) => finite(value) ? (unit === 'percent' ? `${fmt(value)}%` : `${fmt(value)}${unit ? ` ${UNIT_LABEL[unit] ?? unit}` : ''}`) : 'No value';
export const human = key => String(key ?? '').replaceAll('_', ' ').replace(/^./, c => c.toUpperCase());
export const signed = value => finite(value) ? `${value > 0 ? '+' : value < 0 ? '−' : ''}${fmt(Math.abs(value))}` : 'No value';
export const CHANGE_UNIT = {percentage_points: 'percentage points', ratio_points: 'ratio points', persons: 'persons'};
export const formatDate = iso => {
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? '' : date.toLocaleDateString('en-SG', {day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC'});
};
export const money = value => finite(Number(value)) ? `$${Number(value).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 6})}` : 'Not recorded';
export const seconds = value => finite(Number(value)) ? `${Number(value).toLocaleString('en-US', {maximumFractionDigits: 2})} s` : 'Not recorded';
