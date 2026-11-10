// Deck runtime: builds the slides from slideSpecs(), starts reveal.js, and adds the toolbar,
// speaker notes drawer, chart fitting, count-up and the number morph between slides.
// No inline script or style: everything is a DOM call or a CSSOM property write.
import Reveal from '/static/vendor/reveal/reveal.mjs';
import {el, reduced, setTipFormatter} from '../charts.js';
import {slideSpecs} from './slides.js';
import {withoutSecondModel, scrubDom} from './model.js';
import {chartLines, tightenLabels, tipNotes} from './tooltips.js';
import {experimentsSpec, experimentTarget, revealExperiment} from './experiments.js';

const DESIGN_W = 1920, DESIGN_H = 1080, CHART_W = 600;
const printing = /[?&]print-pdf/.test(location.search);
const narrow = matchMedia('(max-width: 800px)');
const fluid = () => !printing && narrow.matches;
const sizeConfig = () => fluid() ? {width: '100%', height: '100%', margin: 0, minScale: 1, maxScale: 1} : {width: DESIGN_W, height: DESIGN_H, margin: 0, minScale: 0.2, maxScale: 2};

const root = document.querySelector('.reveal');
const slidesHost = root.querySelector('.slides');
const fits = [];

function icon(name) {
  const span = el('span', `deck-ico ico-${name}`);
  span.setAttribute('aria-hidden', 'true');
  return span;
}

function chartBox(node, {w = CHART_W, mode = 'clamp'} = {}) {
  const box = el('div', 'deck-visual is-chart');
  box.dataset.w = String(w);
  box.append(node);
  fits.push({box, fig: node, mode, w});
  return box;
}
function visualBox(node) {
  if (node?.classList?.contains('pr-fig')) return chartBox(node);
  const box = el('div', 'deck-visual');
  if (node) box.append(node);
  return box;
}

const fitRuns = new WeakMap();
function fitAll() {
  fits.forEach(entry => {
    const {box, fig, mode} = entry;
    if (fluid()) { box.style.setProperty('--k', '1'); box.style.setProperty('--ox', '0px'); box.style.removeProperty('height'); box.style.removeProperty('--w'); return; }
    const bw = box.clientWidth, bh = box.clientHeight;
    const h = fig.offsetHeight;
    if (!bw || !h) return;
    let w = entry.w;
    if (mode === 'clamp' && bh) {
      // Widen the drawing until the chart fills the box: the chart height is fixed, so scale to the height, then redraw wider.
      const ideal = Math.max(560, Math.min(1000, Math.round(bw / (bh / h))));
      const runs = fitRuns.get(box) || 0;
      if (Math.abs(ideal - w) > 24 && runs < 5) { fitRuns.set(box, runs + 1); entry.w = w = ideal; }
    }
    box.style.setProperty('--w', `${w}px`);
    let k = bw / w;
    if (mode === 'clamp' && bh && h * k > bh) k = bh / h;
    if (mode === 'free') box.style.height = `${Math.ceil(h * k)}px`;
    box.style.setProperty('--k', k.toFixed(3));
    box.style.setProperty('--ox', `${Math.max(0, Math.round((bw - w * k) / 2))}px`);
  });
}

const FLOW_STAGES = ['Sources', 'Processing', 'Retrieval', 'Agent', 'Answer', 'Checks'];

function buildSlide(spec) {
  const section = el('section', 'deck-section');
  if (spec.id) section.id = spec.id;
  section.dataset.chapter = spec.chapter || '';
  section.dataset.title = spec.title || '';
  if (spec.chapter === 'Appendix' || spec.layout === 'appendix') section.dataset.appendix = '';
  if (spec.id === 'experiments') section.dataset.experiments = '';
  const inner = el('div', `deck-slide is-${spec.layout}${spec.cls ? ` ${spec.cls}` : ''}${spec.warn ? ' is-warn' : ''}`);
  const heading = el(spec.layout === 'title' ? 'h1' : 'h2', 'deck-title', spec.title);
  if (spec.layout !== 'title') inner.append(heading);
  if (spec.stage != null && spec.layout !== 'title') {
    inner.classList.add('has-flow');
    const nav = el('nav', 'deck-flow'); nav.setAttribute('aria-label', 'Where this slide sits in the system');
    const ul = el('ul');
    FLOW_STAGES.forEach((label, i) => { const li = el('li', spec.stage === 'all' || spec.stage === i ? 'is-here' : '', label); if (spec.stage === i) li.setAttribute('aria-current', 'step'); ul.append(li); });
    nav.append(ul); inner.append(nav);
  }
  if (spec.caption) inner.classList.add('has-caption');
  const bullets = () => {
    if (!spec.bullets?.length) return null;
    const ul = el('ul', 'deck-bullets');
    spec.bullets.forEach(text => { const li = el('li', 'deck-bullet', text); ul.append(li); });
    return ul;
  };
  if (spec.layout === 'title') {
    const left = el('div', 'tl-left');
    if (spec.wordmark) left.append(el('p', 'deck-wordmark', spec.wordmark));
    left.append(heading);
    const by = el('div', 'tl-by'); by.append(el('p', 'tl-author', spec.author)); if (spec.role) by.append(el('p', 'tl-role', spec.role));
    left.append(by);
    inner.append(left);
  } else if (spec.layout === 'agenda') {
    const nav = el('nav', 'deck-agenda'); nav.setAttribute('aria-label', 'Contents');
    const ol = el('ul');
    [...(spec.items || []), ['appendix', 'Appendix']].forEach(([id, label]) => {
      const li = el('li'); const a = el('a', '', label); a.href = `#/${id}`; li.append(a); ol.append(li);
    });
    nav.append(ol); inner.append(nav);
  } else if (spec.layout === 'scroll') {
    const panel = el('div', 'deck-scroll');
    panel.tabIndex = 0; panel.setAttribute('role', 'region'); panel.setAttribute('aria-label', spec.title); panel.setAttribute('data-prevent-swipe', '');
    spec.panel.forEach(node => { panel.append(node); });
    panel.querySelectorAll('.pr-fig').forEach(f => {
      const box = el('div', 'deck-visual is-chart'); f.replaceWith(box); box.append(f);
      box.dataset.w = '520'; fits.push({box, fig: f, mode: 'free', w: 520});
    });
    inner.append(panel);
    const stop = event => { if (['ArrowUp', 'ArrowDown', 'PageUp', 'PageDown', 'Home', 'End', ' '].includes(event.key) && panel.scrollHeight > panel.clientHeight) event.stopPropagation(); };
    panel.addEventListener('keydown', stop, true);
  } else if (spec.layout === 'appendix') {
    const nav = el('nav', 'deck-agenda'); nav.setAttribute('aria-label', 'Appendix slides');
    const ul = el('ul');
    spec.indexItems.forEach(([letter, title]) => { const li = el('li'); li.textContent = `${letter}. ${title}`; ul.append(li); });
    nav.append(ul); inner.append(nav);
  } else {
    const stacked = spec.visual?.classList?.contains('pr-fig') && spec.bullets?.length;
    const body = el('div', `deck-body${spec.bullets?.length ? '' : ' is-solo'}${stacked ? ' is-stack' : ''}`);
    const list = bullets();
    if (list) body.append(list);
    body.append(visualBox(spec.visual));
    inner.append(body);
  }
  if (spec.caption || spec.rows) {
    const caption = el('div', 'deck-caption');
    if (spec.rows) caption.append(spec.rows);
    if (spec.caption) caption.append(el('p', 'deck-caption-text', spec.caption));
    inner.append(caption);
    inner.classList.add('has-caption');
  }
  if (spec.source) inner.append(el('p', 'deck-source', `Source: ${spec.source}`));
  section.append(inner);
  const notes = el('aside', 'notes');
  (spec.notes || []).filter(Boolean).forEach(line => notes.append(el('p', '', line)));
  if (spec.detail) notes.append(el('p', '', `${spec.detail.label || 'How to read this'}: ${spec.detail.content.replace(/\n+/g, ' ')}`));
  // Popovers are short; what they used to say is kept here. Long spoken labels are shortened the same way.
  tightenLabels(inner);
  tipNotes(inner).forEach(line => notes.append(el('p', '', line)));
  if (!notes.children.length) notes.append(el('p', '', spec.title));
  section.append(notes);
  return section;
}

function main(report) {
  setTipFormatter(chartLines);
  const specs = report && typeof report === 'object' ? slideSpecs(withoutSecondModel(report)) : [];
  if (!specs.length) {
    slidesHost.append(buildSlide({layout: 'text', title: 'The report data could not be loaded', bullets: ['Rebuild it with: uv run labourlens build-report.'], notes: ['report.json is missing or malformed.']}));
  }
  specs.forEach(spec => slidesHost.append(buildSlide(spec)));
  if (specs.length) slidesHost.append(buildSlide(experimentsSpec()));
  scrubDom(slidesHost);

  const slides = () => [...slidesHost.querySelectorAll(':scope > section')];
  // Detach, rather than visually hide, references so every Reveal view uses the same slide set.
  const allSlides = slides();
  const appendixSlides = allSlides.filter(slide => 'appendix' in slide.dataset);
  const experimentSlides = allSlides.filter(slide => 'experiments' in slide.dataset);
  const mainSlides = allSlides.filter(slide => !('appendix' in slide.dataset) && !('experiments' in slide.dataset));
  function appendixTarget(hash) {
    let path;
    try { path = decodeURIComponent(hash.replace(/^#\/?/, '')); } catch { return null; }
    const [name] = path.split('/');
    if (/^\d+$/.test(name)) {
      const target = allSlides[Number(name) - 1]; // hashOneBasedIndex
      return appendixSlides.includes(target) ? target : null;
    }
    if (!name) return null;
    return appendixSlides.find(slide => slide.id === name || [...slide.querySelectorAll('[id], [data-id]')].some(node => node.id === name || node.dataset.id === name)) || null;
  }
  let appendicesVisible = Boolean(appendixTarget(location.hash));
  appendixSlides.forEach(slide => slide.remove());
  if (appendicesVisible) slidesHost.append(...appendixSlides);
  let experimentsVisible = false;
  experimentSlides.forEach(slide => slide.remove());
  const deck = new Reveal(root, {
    ...sizeConfig(), center: false, controls: false, progress: true, slideNumber: false, hash: true, hashOneBasedIndex: true,
    transition: reduced() ? 'none' : 'fade', transitionSpeed: 'default', backgroundTransition: 'none', autoAnimate: false,
    touch: true, keyboard: true, overview: true, help: true, pause: false, mouseWheel: false, fragments: true, fragmentInURL: false,
    scrollActivationWidth: null, pdfSeparateFragments: false, navigationMode: 'linear', display: 'block', previewLinks: false, respondToHashChanges: true
  });

  function setAppendices(visible, target = null) {
    if (visible !== appendicesVisible) {
      // Move first while the current appendix still belongs to Reveal's slide set.
      if (!visible && appendixSlides.includes(deck.getCurrentSlide())) {
        deck.slide(Math.max(0, mainSlides.length - 1));
        // Reveal writes the hash after a delay; clear the appendix target now so the same link works again.
        history.replaceState(null, '', `#/${mainSlides.length}`);
      }
      appendicesVisible = visible;
      if (visible) {
        // References retain their original indices, even when the notebook is open.
        experimentSlides.forEach(slide => slide.remove());
        slidesHost.append(...appendixSlides);
        if (experimentsVisible) slidesHost.append(...experimentSlides);
      }
      else appendixSlides.forEach(slide => slide.remove());
      deck.sync();
    }
    if (target) deck.slide(slides().indexOf(target));
    sync({type: 'ready'});
  }
  let experimentReturn = null;
  function setExperiments(visible) {
    deck.toggleOverview(false);
    if (visible) {
      experimentReturn = deck.getCurrentSlide();
      const card = experimentTarget(experimentReturn);
      experimentsVisible = true;
      slidesHost.append(...experimentSlides);
      deck.sync();
      deck.slide(slides().indexOf(experimentSlides[0]));
      sync({type: 'ready'});
      revealExperiment(experimentSlides[0], card);
      return;
    }
    const back = slides().indexOf(experimentReturn);
    deck.slide(back >= 0 ? back : mainSlides.length - 1);
    experimentsVisible = false;
    experimentSlides.forEach(slide => slide.remove());
    deck.sync();
    sync({type: 'ready'});
    experimentReturn = null;
  }
  // Run before Reveal's bubbling hash listener: restore the target, sync and jump before
  // Reveal tries resolving a detached id. This also handles numeric appendix bookmarks.
  window.addEventListener('hashchange', () => {
    const target = appendixTarget(location.hash);
    if (target) setAppendices(true, target);
  }, true);
  // Reveal clamps numeric slide links itself, so reveal appendix link targets before it sees the click.
  document.addEventListener('click', event => {
    const link = event.target instanceof Element ? event.target.closest('a[href^="#"]') : null;
    const target = link ? appendixTarget(link.getAttribute('href')) : null;
    if (!target) return;
    event.preventDefault();
    event.stopPropagation();
    setAppendices(true, target);
    history.replaceState(null, '', link.getAttribute('href'));
  }, true);

  // ---------- toolbar ----------
  const bar = el('div', 'deck-bar'); bar.setAttribute('role', 'toolbar'); bar.setAttribute('aria-label', 'Presentation controls');
  const button = (name, label, onClick, key) => {
    const b = el('button', 'deck-btn'); b.type = 'button';
    b.setAttribute('aria-label', label); b.title = key ? `${label} (${key})` : label;
    b.append(icon(name)); b.addEventListener('click', onClick);
    return b;
  };
  const prev = button('caret-left', 'Previous slide', () => deck.prev(), 'Left arrow');
  const next = button('caret-right', 'Next slide', () => deck.next(), 'Right arrow');
  const counter = el('span', 'deck-counter'); counter.setAttribute('aria-hidden', 'true');
  const chapter = el('span', 'deck-chapter');
  const overviewBtn = button('squares-four', 'Slide overview', () => deck.toggleOverview(), 'O or Escape');
  const themeBtn = button('sun', 'Switch between dark and light theme', () => toggleTheme(), 'T');
  const fsBtn = button('arrows-out-simple', 'Enter fullscreen', () => toggleFullscreen(), 'F');
  const group = el('div', 'deck-group');
  group.append(prev, counter, next);
  const tools = el('div', 'deck-group');
  tools.append(overviewBtn, themeBtn);
  if (document.fullscreenEnabled) tools.append(fsBtn);
  bar.append(group, chapter, tools);
  root.append(bar);

  const live = el('p', 'visually-hidden'); live.setAttribute('role', 'status'); root.append(live);
  const drawer = el('aside', 'deck-notes'); drawer.hidden = true; drawer.setAttribute('aria-label', 'Speaker notes'); drawer.tabIndex = 0;
  root.append(drawer);

  function toggleNotes(force) {
    const open = force ?? drawer.hidden;
    drawer.hidden = !open;
    root.classList.toggle('notes-open', open);
    if (open) renderNotes();
    requestAnimationFrame(fitAll);
  }
  function renderNotes() {
    const slide = deck.getCurrentSlide();
    drawer.replaceChildren();
    const source = slide?.querySelector('aside.notes');
    [...(source?.children || [])].forEach(p => drawer.append(p.cloneNode(true)));
  }
  function toggleTheme() {
    const dark = (document.documentElement.dataset.theme || 'dark') !== 'light';
    const nextTheme = dark ? 'light' : 'dark';
    document.documentElement.dataset.theme = nextTheme;
    try { localStorage.setItem('labourlens-theme', nextTheme); } catch { /* storage blocked */ }
  }
  function toggleFullscreen() {
    if (document.fullscreenElement) document.exitFullscreen(); else document.documentElement.requestFullscreen().catch(() => {});
  }
  document.addEventListener('fullscreenchange', () => {
    const on = Boolean(document.fullscreenElement);
    fsBtn.setAttribute('aria-label', on ? 'Exit fullscreen' : 'Enter fullscreen');
    fsBtn.title = on ? 'Exit fullscreen (F)' : 'Enter fullscreen (F)';
    fsBtn.querySelector('.deck-ico').className = `deck-ico ico-${on ? 'arrows-in-simple' : 'arrows-out-simple'}`;
  });
  // Speaker notes: press X twice quickly to show or hide the drawer. There is no button for it.
  let lastX = 0;
  document.addEventListener('keydown', event => {
    if (event.key.toLowerCase() !== 'x' || event.repeat || event.ctrlKey || event.metaKey || event.altKey) return;
    const target = event.target;
    if (target instanceof HTMLElement && (target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName))) return;
    const now = performance.now();
    if (now - lastX < 450) { lastX = 0; toggleNotes(); } else lastX = now;
  });
  deck.addKeyBinding({keyCode: 84, key: 'T', description: 'Light or dark theme'}, toggleTheme);
  // Reveal normally assigns A to auto-slide. Reserve it explicitly and handle the
  // double press in capture phase, including while the overview is open.
  deck.addKeyBinding({keyCode: 65, key: 'A A', description: 'Show or hide appendices (double press within 400 ms)'}, () => {});
  deck.registerKeyboardShortcut('X X', 'Show or hide speaker notes (double press within 450 ms)');
  // E is unassigned by Reveal; reserve it so a single press cannot trigger another action.
  deck.addKeyBinding({keyCode: 69, key: 'E E', description: 'Show or hide experiments (double press within 400 ms)'}, () => {});
  let lastE = null;
  document.addEventListener('keydown', event => {
    if (event.key.toLowerCase() !== 'e') { lastE = null; return; }
    const target = event.target;
    if (event.repeat || event.ctrlKey || event.metaKey || event.altKey ||
        target instanceof HTMLElement && (target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName))) {
      lastE = null;
      return;
    }
    event.preventDefault();
    event.stopImmediatePropagation();
    lastA = null;
    const now = performance.now();
    if (lastE !== null && now - lastE <= 400) { lastE = null; setExperiments(!experimentsVisible); }
    else lastE = now;
  }, true);
  let lastA = null;
  document.addEventListener('keydown', event => {
    if (event.key.toLowerCase() !== 'a') { lastA = null; return; }
    const target = event.target;
    if (event.repeat || event.ctrlKey || event.metaKey || event.altKey ||
        target instanceof HTMLElement && (target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName))) {
      lastA = null;
      return;
    }
    event.preventDefault();
    event.stopImmediatePropagation();
    const now = performance.now();
    if (lastA !== null && now - lastA <= 400) { lastA = null; setAppendices(!appendicesVisible); }
    else lastA = now;
  }, true);

  // ---------- slide entry effects ----------
  const rects = new Map();
  const place = node => { let x = 0, y = 0, n = node; while (n && !n.classList?.contains('deck-slide')) { x += n.offsetLeft; y += n.offsetTop; n = n.offsetParent; } return {x, y, w: node.offsetWidth, h: node.offsetHeight}; };
  const remember = slide => { rects.clear(); slide?.querySelectorAll('[data-morph]').forEach(n => rects.set(n.dataset.morph, place(n))); };
  function enter(slide, previous) {
    if (!slide) return;
    slide.querySelectorAll('.pr-fig').forEach(fig => {
      fig.classList.remove('is-in');
      setTimeout(() => fig.classList.add('is-in'), reduced() ? 0 : 90);
    });
    slide.querySelectorAll('.pr-stat-value, .deck-num').forEach(n => n._run?.());
    if (!reduced() && previous) {
      slide.querySelectorAll('[data-morph]').forEach(node => {
        const from = rects.get(node.dataset.morph);
        if (!from) return;
        const to = place(node);
        const s = from.w / (to.w || 1);
        node.style.transition = 'none';
        node.style.transformOrigin = '0 0';
        node.style.transform = `translate(${from.x - to.x}px, ${from.y - to.y}px) scale(${s})`;
        void node.offsetWidth;
        node.style.transition = 'transform 560ms var(--spring)';
        node.style.transform = 'none';
      });
    }
  }
  function sync(event) {
    const slide = deck.getCurrentSlide();
    const all = slides();
    const index = all.indexOf(slide);
    const counted = all.filter(node => !('experiments' in node.dataset));
    counter.textContent = experimentSlides.includes(slide) ? `Experiments · ${mainSlides.length} main` : `${counted.indexOf(slide) + 1} / ${counted.length}`;
    chapter.textContent = slide?.dataset.chapter || '';
    prev.disabled = index <= 0; next.disabled = index >= all.length - 1;
    live.textContent = experimentSlides.includes(slide) ? 'Experiment notebook' : `Slide ${counted.indexOf(slide) + 1} of ${counted.length}: ${slide?.dataset.title || ''}`;
    if (!drawer.hidden) renderNotes();
    if (event?.type !== 'ready') enter(slide, event?.previousSlide); else enter(slide, null);
    setTimeout(() => remember(slide), 700);
    requestAnimationFrame(fitAll);
  }
  deck.on('ready', sync);
  deck.on('slidechanged', sync);
  deck.on('resize', () => requestAnimationFrame(fitAll));

  narrow.addEventListener('change', () => { deck.configure(sizeConfig()); document.documentElement.classList.toggle('deck-fluid', fluid()); requestAnimationFrame(fitAll); });
  document.documentElement.classList.toggle('deck-fluid', fluid());
  if (printing) document.documentElement.classList.add('deck-print');

  const ro = new ResizeObserver(() => requestAnimationFrame(fitAll));
  fits.forEach(f => { ro.observe(f.box); ro.observe(f.fig); });

  return deck.initialize();
}

let report = null;
try {
  const response = await fetch('/static/data/report.json', {credentials: 'same-origin'});
  if (response.ok) report = await response.json();
} catch { report = null; }
await main(report);
