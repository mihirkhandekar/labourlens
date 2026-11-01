// LabourLens overview shell: floating nav, theme toggle, reveal observer and boot.
// The presentation is its own page (/deck) and the workbench is /workbench. Old links such as
// /#presentation and /#workbench are forwarded.
import {el, add, icon} from './js/dom.js';
import {renderHome} from './js/home.js';

const PAGES = [['/', 'Overview'], ['/deck', 'Presentation'], ['/workbench', 'Workbench']];
if (location.hash === '#workbench') location.replace('/workbench');
if (/^#presentation/.test(location.hash)) location.replace('/deck');
const root = document.querySelector('#app');

// ---------- theme ----------
const effectiveTheme = () => document.documentElement.dataset.theme === 'light' ? 'light' : 'dark';
const themeButtons = [];
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
const themeButton = () => {
  const b = el('button', 'icon-btn theme-toggle'); b.type = 'button';
  b.append(icon('sun', 'sun'), icon('moon', 'moon'));
  b.addEventListener('click', toggleTheme);
  themeButtons.push(b);
  return b;
};

// ---------- nav ----------
const header = el('header', 'nav-wrap');
const nav = el('nav', 'nav'); nav.setAttribute('aria-label', 'Primary');
const brand = el('a', 'brand'); brand.href = '/';
add(brand, el('span', 'brand-name', 'LabourLens'));
const links = el('ul', 'nav-links');
PAGES.forEach(([href, label]) => {
  const li = el('li'); const a = el('a', 'nav-link', label); a.href = href;
  if (href === '/') a.setAttribute('aria-current', 'page');
  li.append(a); links.append(li);
});
const burger = el('button', 'burger'); burger.type = 'button'; burger.setAttribute('aria-expanded', 'false'); burger.setAttribute('aria-controls', 'menu'); burger.setAttribute('aria-label', 'Open menu');
burger.append(el('span', 'bar'), el('span', 'bar'), el('span', 'bar'));
add(nav, brand, links, add(el('div', 'nav-tools'), themeButton(), burger));
header.append(nav);

const menu = el('div', 'menu'); menu.id = 'menu'; menu.setAttribute('aria-hidden', 'true');
const menuNav = el('nav', 'menu-nav'); menuNav.setAttribute('aria-label', 'Menu');
PAGES.forEach(([href, label]) => {
  const a = el('a', 'menu-link'); a.href = href; a.tabIndex = -1;
  const inner = el('span', 'mi'); inner.append(el('span', 'ml', label));
  const maskEl = el('span', 'mask'); maskEl.append(inner); a.append(maskEl); menuNav.append(a);
});
const menuFoot = el('div', 'menu-foot');
const menuTheme = themeButton(); menuTheme.tabIndex = -1;
add(menuFoot, menuTheme);
add(menu, menuNav, menuFoot);

// ---------- page ----------
const main = el('main', 'views'); main.id = 'main'; main.tabIndex = -1;
const overviewRoot = el('div', 'view view-overview enter');
main.append(overviewRoot);

const footer = el('footer', 'site-footer');
const fc = el('div', 'container');
fc.append(el('p', 'small muted', 'Statistics: Ministry of Manpower and the Singapore Department of Statistics via data.gov.sg, under the Singapore Open Data Licence. MOM reports remain the Ministry\u2019s. A research prototype by Mihir Khandekar, not an official source.'));
footer.append(fc);
const shell = el('div', 'shell');
add(shell, header, menu, main, footer);
root.replaceChildren(shell);
applyThemeLabel();
document.title = 'LabourLens';

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
document.addEventListener('keydown', event => {
  if (event.target.closest?.('input, textarea, select, [contenteditable="true"]')) return;
  if (event.altKey || event.ctrlKey || event.metaKey) return;
  if (event.key === 'Escape' && menu.classList.contains('open')) setMenu(false);
  else if (event.key.toLowerCase() === 't') toggleTheme();
});

// ---------- boot ----------
let report = null;
try {
  const response = await fetch('/static/data/report.json', {credentials: 'same-origin'});
  if (!response.ok) throw new Error(`Report not found (${response.status}). Run labourlens build-report.`);
  const data = await response.json();
  if (!data || typeof data !== 'object' || Array.isArray(data)) throw new Error('report.json has an unexpected format.');
  report = data;
} catch (error) {
  overviewRoot.append(add(el('p', 'error-banner'), icon('warn'), el('span', '', `${error.message} The workbench still works. No report numbers are shown.`)));
}
renderHome(overviewRoot, report, {
  go: href => { location.href = href; },
  tryQuestion: text => { location.href = `/workbench?question=${encodeURIComponent(text)}`; }
});
observeReveals(overviewRoot);
