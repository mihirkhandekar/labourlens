// The landing page is the project report: a compact hero, a step navigator and one band per step.
// Content lives in report-story.js; numbers come from report.json only.
import {el, add, cta} from './dom.js';
import {buildBands, STEPS} from './report-story.js';

const reducedMotion = () => matchMedia('(prefers-reduced-motion: reduce)').matches;

export function renderHome(root, report) {
  root.classList.add('rp');
  const hero = el('section', 'rp-hero'); hero.id = 'top';
  hero.setAttribute('aria-labelledby', 'hero-title');
  const inner = el('div', 'rp-hero-inner');
  const copy = el('div', 'rp-hero-copy');
  const title = el('h1', 'rp-hero-title', 'Singapore AI Agent for Workforce Policy Researchers');
  title.id = 'hero-title';
  const repository = cta('Repository', 'https://github.com/mihirkhandekar/labourlens', 'btn', 'arrow-ur');
  repository.target = '_blank'; repository.rel = 'noopener noreferrer';
  const repo = el('div', 'rp-repo');
  repo.append(repository, el('span', 'rp-note', 'Private repository shared with reviewers.'));
  add(copy, title,
    el('p', 'rp-hero-lead', 'A bounded research agent for Singapore workforce policy, built around official statistics, reports and reproducible evaluation.'),
    el('p', 'rp-byline', 'Mihir Khandekar'),
    add(el('div', 'rp-hero-cta'), cta('Open the workbench', '/workbench', 'btn btn-primary', 'arrow-ur'), cta('View the deck', '/deck', 'btn', 'arrow-r'), repo));
  inner.append(copy);
  hero.append(inner);

  const body = el('div', 'rp-body');
  const bands = report ? buildBands(report) : [];
  const nav = stepNav(bands.map(b => b.id));
  body.append(nav.node);
  bands.forEach(b => body.append(b.node));
  if (!bands.length) body.append(el('p', 'rp-missing rp-inner', 'The report data could not be loaded, so the steps are not shown. The workbench is unaffected.'));
  root.append(hero, body);
  nav.start(bands.map(b => b.node));
  if (location.hash.length > 1) requestAnimationFrame(() => document.getElementById(decodeURIComponent(location.hash.slice(1)))?.scrollIntoView());
}

/** Text-only list of steps: smooth anchor scrolling, a highlighted current step and arrow-key movement. */
function stepNav(ids) {
  const node = el('nav', 'rp-steps'); node.setAttribute('aria-label', 'Report steps');
  const list = el('ol', 'rp-steps-list');
  const links = new Map();
  STEPS.filter(([id]) => ids.includes(id)).forEach(([id, label]) => {
    const li = el('li');
    const a = el('a', 'rp-step', label); a.href = `#${id}`; a.dataset.step = id;
    li.append(a); list.append(li); links.set(id, a);
  });
  node.append(list);

  let current = null;
  const setCurrent = id => {
    if (id === current || !links.has(id)) return;
    current = id;
    links.forEach((a, key) => { if (key === id) a.setAttribute('aria-current', 'location'); else a.removeAttribute('aria-current'); });
    // On narrow screens the list scrolls sideways: keep the current step in view without moving the page.
    const a = links.get(id);
    if (node.scrollWidth > node.clientWidth + 2) node.scrollTo({left: Math.max(0, a.offsetLeft - 2), behavior: reducedMotion() ? 'auto' : 'smooth'});
  };

  list.addEventListener('click', event => {
    const a = event.target.closest('a.rp-step');
    if (!a) return;
    event.preventDefault();
    const target = document.getElementById(a.dataset.step);
    if (!target) return;
    setCurrent(a.dataset.step);
    target.scrollIntoView({behavior: reducedMotion() ? 'auto' : 'smooth', block: 'start'});
    history.replaceState(null, '', `#${a.dataset.step}`);
    target.querySelector('.rp-title')?.focus({preventScroll: true});
  });
  list.addEventListener('keydown', event => {
    const all = [...links.values()];
    const at = all.indexOf(document.activeElement);
    if (at < 0) return;
    const next = {ArrowDown: at + 1, ArrowRight: at + 1, ArrowUp: at - 1, ArrowLeft: at - 1, Home: 0, End: all.length - 1}[event.key];
    if (next === undefined) return;
    event.preventDefault();
    all[Math.max(0, Math.min(all.length - 1, next))].focus();
  });

  const start = sections => {
    if (typeof IntersectionObserver !== 'function') return;
    const visible = new Set();
    // A thin band across the upper part of the viewport decides which step is current.
    const spy = new IntersectionObserver(entries => {
      entries.forEach(entry => { if (entry.isIntersecting) visible.add(entry.target.id); else visible.delete(entry.target.id); });
      const first = sections.find(s => visible.has(s.id));
      if (first) setCurrent(first.id);
    }, {rootMargin: '-28% 0px -62% 0px', threshold: 0});
    sections.forEach(s => spy.observe(s));
  };
  return {node, start};
}
