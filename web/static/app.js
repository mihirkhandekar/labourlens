// LabourLens shell: floating nav, routing between Overview and Presentation (the Workbench is its own page, /workbench), theme,
// reveal observer, keyboard shortcuts and boot. The Presentation view is owned by evaluation.js:
//   export function renderPresentation(rootEl, report)
// rootEl is an empty <div id="presentation-root" class="presentation">; report is the parsed
// report.json, or null when it could not be loaded. The shell calls it once, on first visit.
import {el, add, icon} from './js/dom.js';
import {renderHome} from './js/home.js';

const VIEWS = [
  ['overview', 'Overview', 'Overview'],
  ['presentation', 'Presentation', 'Presentation']
];
const EXTERNAL = [['/workbench', 'Workbench']];
// Old deep link: /#workbench opens the standalone page.
if (location.hash === '#workbench') location.replace('/workbench');
const root = document.querySelector('#app');
let report = null;
let home = null;
let lastMode = {known: false, text: 'Checking demo', enabled: false, authenticated: false};
let currentView = '';
let presentationState = 'idle';
let firstRoute = true;

// ---------- theme ----------
const media = matchMedia('(prefers-color-scheme: dark)');
const effectiveTheme = () => document.documentElement.dataset.theme || (media.matches ? 'dark' : 'light');
function applyThemeLabel() {
  const dark = effectiveTheme() === 'dark';
  themeButtons.forEach(b => b.setAttribute('aria-label', dark ? 'Switch to light theme' : 'Switch to dark theme'));
}
function toggleTheme() {
  const next = effectiveTheme() === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = next;
  try { localStorage.setItem('labourlens-theme', next); } catch { /* storage blocked */ }
  applyThemeLabel();
}
media.addEventListener('change', applyThemeLabel);
const themeButton = () => {
  const b = el('button', 'icon-btn theme-toggle'); b.type = 'button';
  b.append(icon('sun', 'sun'), icon('moon', 'moon'));
  b.addEventListener('click', toggleTheme);
  return b;
};
const themeButtons = [];

// ---------- nav ----------
function brandMark() {
  const ns = 'http://www.w3.org/2000/svg';
  const s = document.createElementNS(ns, 'svg');
  s.setAttribute('viewBox', '0 0 32 32'); s.setAttribute('class', 'brand-mark'); s.setAttribute('aria-hidden', 'true'); s.setAttribute('focusable', 'false');
  const part = (tag, attrs) => { const n = document.createElementNS(ns, tag); Object.entries(attrs).forEach(([k, v]) => n.setAttribute(k, v)); s.append(n); };
  part('rect', {width: 32, height: 32, rx: 9, class: 'bm-bg'});
  part('circle', {cx: 14.5, cy: 14.5, r: 7.5, class: 'bm-ring'});
  part('path', {d: 'M20.5 20.5 26 26', class: 'bm-handle'});
  part('path', {d: 'M10 17l2.8-3 2.2 1.8 3.3-4', class: 'bm-line'});
  part('circle', {cx: 18.3, cy: 11.8, r: 1.6, class: 'bm-dot'});
  return s;
}

const header = el('header', 'nav-wrap');
const nav = el('nav', 'nav'); nav.setAttribute('aria-label', 'Primary');
const brand = el('a', 'brand'); brand.href = '#overview';
add(brand, brandMark(), el('span', 'brand-name', 'LabourLens'));
const links = el('ul', 'nav-links');
const navLinks = new Map();
VIEWS.forEach(([id, label]) => { const li = el('li'); const a = el('a', 'nav-link', label); a.href = `#${id}`; navLinks.set(id, a); li.append(a); links.append(li); });
EXTERNAL.forEach(([href, label]) => { const li = el('li'); const a = el('a', 'nav-link', label); a.href = href; li.append(a); links.append(li); });
const navChip = el('span', 'pill nav-chip'); const navDot = el('span', 'dot'); const navChipText = el('span', '', 'Checking demo'); add(navChip, navDot, navChipText);
const themeBtn = themeButton(); themeButtons.push(themeBtn);
const helpBtn = el('button', 'icon-btn help-btn'); helpBtn.type = 'button'; helpBtn.setAttribute('aria-label', 'Keyboard shortcuts'); helpBtn.append(icon('keyboard'));
const burger = el('button', 'burger'); burger.type = 'button'; burger.setAttribute('aria-expanded', 'false'); burger.setAttribute('aria-controls', 'menu'); burger.setAttribute('aria-label', 'Open menu');
burger.append(el('span', 'bar'), el('span', 'bar'), el('span', 'bar'));
add(nav, brand, links, add(el('div', 'nav-tools'), navChip, helpBtn, themeBtn, burger));
header.append(nav);

const menu = el('div', 'menu'); menu.id = 'menu'; menu.setAttribute('aria-hidden', 'true');
const menuNav = el('nav', 'menu-nav'); menuNav.setAttribute('aria-label', 'Menu');
VIEWS.forEach(([id, label], i) => {
  const a = el('a', 'menu-link'); a.href = `#${id}`; a.tabIndex = -1;
  const inner = el('span', 'mi'); add(inner, el('span', 'mn mono', String(i + 1).padStart(2, '0')), el('span', 'ml', label));
  const maskEl = el('span', 'mask'); maskEl.append(inner); a.append(maskEl); menuNav.append(a);
});
EXTERNAL.forEach(([href, label], i) => {
  const a = el('a', 'menu-link'); a.href = href; a.tabIndex = -1;
  const inner = el('span', 'mi'); add(inner, el('span', 'mn mono', String(VIEWS.length + i + 1).padStart(2, '0')), el('span', 'ml', label));
  const maskEl = el('span', 'mask'); maskEl.append(inner); a.append(maskEl); menuNav.append(a);
});
const menuFoot = el('div', 'menu-foot');
const menuTheme = themeButton(); themeButtons.push(menuTheme); menuTheme.tabIndex = -1;
add(menuFoot, el('p', 'small muted', 'GenAI Engineer assessment submission'), menuTheme);
add(menu, menuNav, menuFoot);

// ---------- views ----------
const main = el('main', 'views'); main.id = 'main'; main.tabIndex = -1;
const viewEls = new Map();
VIEWS.forEach(([id, label]) => { const v = el('div', `view view-${id}`); v.id = `view-${id}`; v.hidden = true; viewEls.set(id, v); main.append(v); });
const overviewRoot = viewEls.get('overview');
const presentationRoot = el('div', 'presentation'); presentationRoot.id = 'presentation-root';
viewEls.get('presentation').append(presentationRoot);

const footer = el('footer', 'site-footer');
const fc = el('div', 'container footer-grid');
add(fc, add(el('div', 'footer-brand'), brandMark(), el('p', 'brand-name', 'LabourLens'), el('p', 'small muted', 'GenAI Engineer assessment submission. A research prototype using Singapore statistics and MOM reports; not an official source.')),
  add(el('div', 'footer-col'), el('h2', 'footer-h', 'Pages'), (() => { const ul = el('ul'); VIEWS.forEach(([id, label]) => { const li = el('li'); const a = el('a', '', label); a.href = `#${id}`; li.append(a); ul.append(li); }); EXTERNAL.forEach(([href, label]) => { const li = el('li'); const a = el('a', '', label); a.href = href; li.append(a); ul.append(li); }); return ul; })()),
  add(el('div', 'footer-col'), el('h2', 'footer-h', 'Data and rights'), el('p', 'small', 'Statistics: Ministry of Manpower and Singapore Department of Statistics via data.gov.sg, under the Singapore Open Data Licence. The licence conditions include attribution and no implied endorsement.'),
    el('p', 'small muted', 'MOM reports remain the Ministry’s. This site shows no report text beyond short excerpts the live agent cites. Fonts: Fraunces, Geist and Geist Mono, SIL OFL 1.1.')));
const help = el('dialog', 'modal'); help.setAttribute('aria-labelledby', 'help-title');
const helpRows = [['/', 'Open the workbench page'], ['1  2  3', 'Overview, Presentation, Workbench'], ['T', 'Switch light and dark theme'], ['P', 'Presenter mode: larger type'], ['Arrow keys', 'Move along a chart when it has focus'], ['Esc', 'Close the evidence drawer, menu or this list'], ['?', 'Open this list']];
const helpList = el('dl', 'shortcut-list');
helpRows.forEach(([k, d]) => { const dt = el('dt'); k.split(' ').filter(Boolean).forEach(part => dt.append(part === '+' || part === 'or' ? document.createTextNode(` ${part} `) : el('span', 'kbd', part))); helpList.append(dt, el('dd', '', d)); });
const helpClose = el('button', 'icon-btn'); helpClose.type = 'button'; helpClose.setAttribute('aria-label', 'Close'); helpClose.append(icon('x'));
helpClose.addEventListener('click', () => help.close());
add(help, add(el('div', 'modal-head'), el('h2', '', 'Keyboard shortcuts'), helpClose), helpList);
help.id = 'help'; help.querySelector('h2').id = 'help-title';
help.addEventListener('click', event => { if (event.target === help) help.close(); });
helpBtn.addEventListener('click', () => help.showModal());

const live = el('p', 'visually-hidden'); live.setAttribute('role', 'status');
const shell = el('div', 'shell');
footer.append(fc);
add(shell, header, menu, main, footer, live);
root.replaceChildren(shell, help);
applyThemeLabel();

// ---------- reveal on scroll (IntersectionObserver only) ----------
const reveal = new IntersectionObserver(entries => {
  entries.forEach(entry => { if (entry.isIntersecting) { entry.target.classList.add('is-in'); reveal.unobserve(entry.target); } });
}, {rootMargin: '0px 0px -8% 0px', threshold: 0.12});
const observeReveals = scope => scope.querySelectorAll('.reveal:not(.is-in)').forEach(node => reveal.observe(node));

// ---------- menu ----------
function setMenu(open) {
  menu.classList.toggle('open', open);
  menu.setAttribute('aria-hidden', String(!open));
  burger.setAttribute('aria-expanded', String(open));
  burger.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
  document.body.classList.toggle('menu-open', open);
  [main, footer].forEach(node => { node.inert = open; });
  menu.querySelectorAll('a, button').forEach(node => { node.tabIndex = open ? 0 : -1; });
  if (open) menu.querySelector('a')?.focus(); else if (document.activeElement && menu.contains(document.activeElement)) burger.focus();
}
burger.addEventListener('click', () => setMenu(!menu.classList.contains('open')));
menu.addEventListener('click', event => { if (event.target.closest('a')) setMenu(false); });
matchMedia('(min-width: 768px)').addEventListener('change', event => { if (event.matches) setMenu(false); });

// ---------- router ----------
async function ensurePresentation() {
  if (presentationState !== 'idle') return;
  presentationState = 'loading';
  presentationRoot.append(add(el('div', 'container presentation-loading'), el('div', 'skeleton sk-line w60'), el('div', 'skeleton sk-line w90'), el('div', 'skeleton sk-chart')));
  try {
    const mod = await import('./evaluation.js');
    presentationRoot.replaceChildren();
    if (typeof mod.renderPresentation === 'function') mod.renderPresentation(presentationRoot, report);
    else {
      const panel = el('section', 'container presentation-fallback');
      panel.append(el('h1', '', 'Presentation'));
      mod.renderEvaluation?.(panel, report); mod.renderSecurity?.(panel, report);
      presentationRoot.append(panel);
    }
    presentationState = 'ready';
    observeReveals(presentationRoot);
    new MutationObserver(() => observeReveals(presentationRoot)).observe(presentationRoot, {childList: true, subtree: true});
  } catch (error) {
    presentationState = 'idle';
    presentationRoot.replaceChildren(add(el('div', 'container'), add(el('div', 'bezel'), add(el('div', 'bezel-core'), el('h2', '', 'The presentation did not load.'), el('p', 'muted', `${error.message}. Reload the page to try again.`)))));
  }
}

function parseHash() {
  const raw = decodeURIComponent(location.hash.replace(/^#/, ''));
  const [first, ...rest] = raw.split('/');
  if (!raw || first === 'top') return {view: 'overview'};
  if (VIEWS.some(([id]) => id === first)) return {view: first, anchor: rest.join('/')};
  return {view: null, anchor: raw};
}
async function route() {
  let {view, anchor} = parseHash();
  if (view === null) {
    await ensurePresentation();
    const target = presentationRoot.querySelector(`[id="${CSS.escape(anchor)}"]`);
    view = target ? 'presentation' : 'overview';
  }
  const changed = view !== currentView;
  currentView = view;
  viewEls.forEach((node, id) => { node.hidden = id !== view; if (id === view && changed) { node.classList.remove('enter'); void node.offsetWidth; node.classList.add('enter'); } });
  navLinks.forEach((a, id) => { if (id === view) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current'); });
  const label = VIEWS.find(([id]) => id === view)[2];
  document.title = view === 'overview' ? 'LabourLens | GenAI Engineer assessment' : `LabourLens | ${label}`;
  live.textContent = `${label} page`;
  if (view === 'presentation') await ensurePresentation();
  observeReveals(viewEls.get(view));
  if (view === 'presentation' && anchor) {
    const target = presentationRoot.querySelector(`[id="${CSS.escape(anchor)}"]`);
    if (target) { target.scrollIntoView({block: 'start', behavior: 'instant'}); return; }
  }
  if (changed) { window.scrollTo({top: 0, behavior: 'instant'}); if (!firstRoute) main.focus({preventScroll: true}); }
  firstRoute = false;
}
window.addEventListener('hashchange', route);

// ---------- shortcuts ----------
document.addEventListener('keydown', event => {
  if (event.target.closest?.('input, textarea, select, [contenteditable="true"]')) return;
  if (event.altKey || event.ctrlKey || event.metaKey) return;
  if (document.querySelector('dialog[open]')) return;
  const key = event.key;
  if (key === 'Escape' && menu.classList.contains('open')) { setMenu(false); return; }
  if (key === '/') { event.preventDefault(); location.href = '/workbench'; }
  else if (key === '?') { event.preventDefault(); help.showModal(); }
  else if (key === '1' || key === '2') { location.hash = `#${VIEWS[Number(key) - 1][0]}`; }
  else if (key === '3') location.href = '/workbench';
  else if (key.toLowerCase() === 't') toggleTheme();
  else if (key.toLowerCase() === 'p') { const on = document.documentElement.dataset.presenter !== 'on'; document.documentElement.dataset.presenter = on ? 'on' : 'off'; live.textContent = on ? 'Presenter mode on' : 'Presenter mode off'; }
});

// ---------- boot ----------
function setMode(mode) {
  lastMode = mode;
  navChipText.textContent = mode.text;
  navDot.className = `dot ${!mode.known ? '' : !mode.enabled ? 'warn' : mode.authenticated ? 'ok pulse' : 'warn'}`;
  home?.setDemo(mode);
}
fetch('/api/status', {credentials: 'same-origin'}).then(r => r.json()).then(d => {
  const enabled = Boolean(d.enabled), authenticated = Boolean(d.authenticated);
  setMode({known: true, enabled, authenticated, text: !enabled ? 'Report only' : authenticated ? 'Live demo, signed in' : 'Live demo, signed out'});
}).catch(() => setMode({known: true, enabled: false, authenticated: false, text: 'Status unavailable'}));

async function loadReport() {
  try {
    const response = await fetch('/static/data/report.json', {credentials: 'same-origin'});
    if (!response.ok) throw new Error(`Report not found (${response.status}). Run labourlens build-report.`);
    const data = await response.json();
    if (!data || typeof data !== 'object' || Array.isArray(data)) throw new Error('report.json has an unexpected format.');
    report = data;
  } catch (error) {
    report = null;
    overviewRoot.append(add(el('p', 'error-banner'), icon('warn'), el('span', '', `${error.message} The workbench still works. No report numbers are shown.`)));
  }
}
async function checkService() {
  try {
    const response = await fetch('/healthz', {credentials: 'same-origin'});
    const data = await response.json();
    home?.setService(response.ok && data.status === 'ok', data.version);
  } catch { home?.setService(false); }
}

await loadReport();
home = renderHome(overviewRoot, report, {
  go: id => { location.hash = `#${id}`; },
  tryQuestion: text => { location.href = `/workbench?question=${encodeURIComponent(text)}`; }
});
home.setDemo(lastMode);
checkService();
await route();
if ('requestIdleCallback' in window) requestIdleCallback(() => import('./evaluation.js').catch(() => {}));
