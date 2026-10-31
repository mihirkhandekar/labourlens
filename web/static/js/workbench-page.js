// Standalone research page. Answers/history exist in this page's memory only.
import {el, add, icon} from './dom.js';
import {mountWorkbench} from './workbench.js';
const app = document.querySelector('#app');
const header = el('header', 'nav-wrap');
const nav = el('nav', 'nav'); nav.setAttribute('aria-label', 'Primary');
const brand = el('a', 'brand brand-name', 'LabourLens'); brand.href = '/';
const links = el('ul', 'nav-links');
for (const [name, href] of [['Overview', '/'], ['Presentation', '/deck'], ['Workbench', '/workbench']]) {
  const a = el('a', 'nav-link', name); a.href = href;
  if (href === '/workbench') a.setAttribute('aria-current', 'page');
  links.append(add(el('li'), a));
}
const chip = el('span', 'pill nav-chip', 'Checking demo');
const theme = el('button', 'icon-btn theme-toggle'); theme.type = 'button'; theme.append(icon('sun', 'sun'), icon('moon', 'moon'));
function themeLabel() { const dark = document.documentElement.dataset.theme !== 'light'; theme.setAttribute('aria-label', dark ? 'Switch to light theme' : 'Switch to dark theme'); return dark; }
function toggleTheme() { const next = themeLabel() ? 'light' : 'dark'; document.documentElement.dataset.theme = next; try { localStorage.setItem('labourlens-theme', next); } catch {} themeLabel(); }
theme.addEventListener('click', toggleTheme); themeLabel();
const burger = el('button', 'burger'); burger.type = 'button'; burger.setAttribute('aria-label', 'Open menu'); burger.setAttribute('aria-expanded', 'false'); burger.setAttribute('aria-controls', 'page-menu');
burger.append(el('span', 'bar'), el('span', 'bar'), el('span', 'bar'));
add(nav, brand, links, add(el('div', 'nav-tools'), chip, theme, burger)); header.append(nav);
const menu = el('div', 'menu'); menu.id = 'page-menu'; menu.setAttribute('aria-hidden', 'true');
const menuNav = el('nav', 'menu-nav'); menuNav.setAttribute('aria-label', 'Menu');
for (const [name, href] of [['Overview', '/'], ['Presentation', '/deck'], ['Workbench', '/workbench']]) {
  const a = el('a', 'menu-link'); a.href = href; a.tabIndex = -1;
  add(a, add(el('span', 'mask'), add(el('span', 'mi'), el('span', 'ml', name)))); menuNav.append(a);
}
menu.append(menuNav);
const main = el('main', 'view-workbench standalone-workbench'); main.id = 'main'; main.tabIndex = -1;
app.replaceChildren(header, menu, main);
function closeMenu() { menu.classList.remove('open'); menu.setAttribute('aria-hidden', 'true'); burger.setAttribute('aria-expanded', 'false'); burger.setAttribute('aria-label', 'Open menu'); main.inert = false; document.body.classList.remove('menu-open'); menu.querySelectorAll('a').forEach(a => { a.tabIndex = -1; }); }
burger.addEventListener('click', () => {
  if (menu.classList.contains('open')) { closeMenu(); burger.focus(); return; }
  menu.classList.add('open'); menu.setAttribute('aria-hidden', 'false'); burger.setAttribute('aria-expanded', 'true'); burger.setAttribute('aria-label', 'Close menu'); main.inert = true; document.body.classList.add('menu-open'); menu.querySelectorAll('a').forEach(a => { a.tabIndex = 0; }); menu.querySelector('a').focus();
});
const bench = mountWorkbench(main, {onMode: mode => { chip.textContent = mode.text; }});
// A question may be carried from the presentation, but never an answer or access code.
const initial = new URLSearchParams(location.search).get('question');
if (initial) { bench.prefill(initial.slice(0, 1000)); history.replaceState(null, '', location.pathname); }
const observer = new IntersectionObserver(entries => entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('is-in'); observer.unobserve(e.target); } }), {threshold: 0.08});
main.querySelectorAll('.reveal').forEach(e => observer.observe(e));
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && menu.classList.contains('open')) { closeMenu(); burger.focus(); return; }
  if (event.target.closest('input,textarea,select') || event.ctrlKey || event.metaKey || event.altKey || bench.isDrawerOpen()) return;
  if (event.key === '/') { event.preventDefault(); bench.focusComposer(); }
  else if (event.key.toLowerCase() === 't') toggleTheme();
  else if (event.key === '?') { event.preventDefault(); document.querySelector('.page-shortcuts')?.showModal(); }
});
const help = el('dialog', 'modal page-shortcuts'); help.setAttribute('aria-label', 'Keyboard shortcuts');
const close = el('button', 'btn small plain', 'Close'); close.type = 'button'; close.addEventListener('click', () => help.close());
add(help, el('h2', '', 'Keyboard shortcuts'), el('p', '', '/ focuses the composer or sign-in field. Ctrl or Command + Enter sends a question. T switches theme. Arrow keys read chart periods. Escape closes a dialog. Previous questions are held in this page’s memory only.'), close); app.append(help);
