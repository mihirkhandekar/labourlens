import {el, add, svg} from './dom.js';

const root = document.querySelector('#main');
const toggle = document.querySelector('#theme-toggle');
const themeLabel = () => { toggle.textContent = document.documentElement.dataset.theme === 'light' ? 'Dark theme' : 'Light theme'; };
toggle.addEventListener('click', () => {
  const theme = document.documentElement.dataset.theme === 'light' ? 'dark' : 'light';
  document.documentElement.dataset.theme = theme;
  try { localStorage.setItem('labourlens-theme', theme); } catch { /* Storage may be disabled. */ }
  themeLabel();
});
themeLabel();
const link = (label, href) => { const a = el('a', '', label); a.href = href; return a; };
const section = (id, title, intro) => {
  const s = el('section', 'iv-section'); s.id = id;
  const heading = el('h2', '', title); heading.id = `${id}-title`; s.setAttribute('aria-labelledby', heading.id);
  s.append(add(el('div', 'iv-section-head'), heading, el('p', '', intro))); return s;
};
const details = (label, text) => add(el('details', 'iv-detail'), el('summary', '', label), el('p', '', text));
const rate = value => typeof value === 'number' ? value.toFixed(3) : 'Not recorded';

function evidenceFigure() {
  const shell = el('div', 'iv-shell');
  const figure = el('figure', 'iv-evidence');
  const diagram = svg('svg', {viewBox: '0 0 600 260', role: 'img', 'aria-labelledby': 'evidence-diagram-title'});
  diagram.append(svg('title', {id: 'evidence-diagram-title'}, 'Official tables and source passages feed bounded tools, then a cited answer that can be inspected.'));
  for (const [x, y, title, sub] of [[24, 30, 'Official tables', 'Definitions + periods'], [24, 155, 'Source passages', 'Release + provenance'], [230, 92, 'Bounded tools', 'Retrieve · calculate'], [435, 92, 'Cited answer', 'Inspect · question']]) {
    diagram.append(svg('rect', {x, y, width: 145, height: 76, rx: 12}), svg('text', {x: x + 13, y: y + 29, class: 'iv-svg-title'}, title), svg('text', {x: x + 13, y: y + 51, class: 'iv-svg-sub'}, sub));
  }
  diagram.append(svg('path', {d: 'M169 68 H199 V130 H230 M169 193 H199 V130 M375 130 H435', class: 'iv-path'}));
  figure.append(diagram, el('figcaption', '', 'Evidence is inspectable. Authority stays bounded.'));
  shell.append(figure); return shell;
}

function render(page) {
  const c = page.content; const m = page.measurements;
  const hero = el('section', 'iv-hero');
  const title = el('h1', '', c.title);
  hero.append(el('p', 'iv-context', 'Innovation assessment'), title, el('p', 'iv-lead', c.intro), add(el('div', 'iv-jump'), link('What is new', '#contribution'), link('Measured results', '#results'), link('The proposed workbench', '#roadmap')));
  const contribution = section('contribution', 'What is new here', c.contribution_intro);
  contribution.append(evidenceFigure());
  const features = el('div', 'iv-features');
  c.contributions.forEach(item => features.append(add(el('article', 'iv-feature'), el('h3', '', item.title), el('p', '', item.text), details('Where the boundary is', item.detail))));
  contribution.append(features);

  const results = section('results', 'Results, with the limits attached', 'Saved measurements, not a promise about the next question. Answer-quality figures below use gpt-6-luna and the mean of two runs per arm on corpus v3.1.');
  const rows = el('div', 'iv-results');
  const result = (value, title, caveat) => rows.append(add(el('article', 'iv-result'), el('p', 'iv-value', value), add(el('div'), el('h3', '', title), el('p', '', caveat))));
  result(`${rate(m.retrieval.R0)} → ${rate(m.retrieval.R3)}`, 'Retrieval hit@8', `${m.retrieval.n} development text questions, hybrid search versus filter then rerank. This set shaped the design; retrieval relevance is not answer accuracy.`);
  for (const split of m.splits) {
    const r3 = split.arms.find(a => a.arm === 'r3'); const hybrid = split.arms.find(a => a.arm === 'hybrid');
    if (!r3 || !hybrid) continue;
    const labels = {dev: ['Development behaviour accuracy', 'Development shaped the design.'], registered: ['Original test behaviour accuracy', 'This set shares evidence with development; no demonstrated gain.'], fresh: ['Fresh test behaviour accuracy', 'Different sources, but outcomes are now known; no demonstrated gain.']};
    const [label, caveat] = labels[split.id] || ['Test behaviour accuracy', 'No demonstrated gain.'];
    result(`${rate(r3.accuracy)} / ${rate(hybrid.accuracy)}`, label, `${split.n} questions, filter then rerank / hybrid. ${caveat} Two runs do not estimate run-to-run variance.`);
    if (split.id === 'dev') result(`${r3.latency.toFixed(2)} s · $${r3.cost.toFixed(6)}`, 'The quality trade-off', 'Mean of run median latencies and estimated cost per case for filter then rerank. Saved usage at list prices, not a bill; full comparisons exclude web-only steps and MCP.');
  }
  result(`${m.scanner.before} → ${m.scanner.after} of 30`, 'Scanner detection', 'Malicious fixture detections before and after. False positives remain 9 of 30 benign fixtures. A warning layer, not proof that a passage is safe.');
  result(`${m.mcp.different_outputs} / ${m.mcp.compared_datasets}`, 'Different outputs, MCP versus direct', `${m.mcp.identical_datasets} identical dataset responses and ${m.mcp.matching_refusals} matching refusals in a tool-level comparison. This is protocol evidence, not an end-to-end quality guarantee or the all-three-tools route.`);
  results.append(rows, add(el('p', 'iv-source-note'), el('span', '', 'Methods, intervals, MCP-versus-direct measurements and negative results: '), link('read the evaluation report', 'https://github.com/mihirkhandekar/labourlens/blob/main/docs/evaluation-report.md')));

  const roadmap = section('roadmap', c.roadmap_title, c.roadmap_intro);
  const map = el('div', 'iv-roadmap');
  c.roadmap.forEach(group => {
    const row = el('article', 'iv-roadmap-row');
    row.append(add(el('div', 'iv-roadmap-label'), el('h3', '', group.name), el('p', '', group.purpose)));
    const shell = el('div', 'iv-shell'); const list = el('div', 'iv-roadmap-items');
    group.items.forEach(item => {
      const d = el('details', 'iv-roadmap-item');
      d.append(add(el('summary'), el('span', '', item.title), el('span', 'iv-proposal', item.status), el('span', 'iv-plus', '+')), el('p', '', item.why)); list.append(d);
    });
    shell.append(list); row.append(shell); map.append(row);
  });
  roadmap.append(map);
  const limits = section('limits', 'What I would not claim', 'The limits are part of the assessment, not footnotes to it.');
  const list = el('ul', 'iv-limits'); c.limits.forEach(text => list.append(el('li', '', text))); limits.append(list);
  const footer = add(el('footer', 'iv-footer'), el('p', '', 'A research prototype by Mihir Khandekar. Not an official government source.'), link('Back to the project report', '/'));
  root.replaceChildren(hero, contribution, results, roadmap, limits, footer);
  if (!matchMedia('(prefers-reduced-motion: reduce)').matches && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => entries.forEach(entry => { if (entry.isIntersecting) { entry.target.classList.add('iv-visible'); observer.unobserve(entry.target); } }), {threshold: 0.06});
    root.querySelectorAll('.iv-feature, .iv-result, .iv-roadmap-row').forEach(node => { node.classList.add('iv-enter'); observer.observe(node); });
  }
}
try {
  const response = await fetch('/static/data/report.json', {credentials: 'same-origin'});
  if (!response.ok) throw new Error('The report data is unavailable.');
  const report = await response.json();
  if (!report.innovation) throw new Error('The innovation projection is missing. Run labourlens build-report.');
  render(report.innovation);
} catch (error) {
  root.replaceChildren(el('h1', '', 'The assessment could not be loaded'), el('p', '', error.message), link('Read the project report', '/'));
}
