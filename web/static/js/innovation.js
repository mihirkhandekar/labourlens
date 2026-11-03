import {el, add} from './dom.js';

const root = document.querySelector('#main');
const toggle = document.querySelector('#theme-toggle');
function themeLabel() { toggle.textContent = document.documentElement.dataset.theme === 'light' ? 'Dark theme' : 'Light theme'; }
toggle.addEventListener('click', () => {
  const theme = document.documentElement.dataset.theme === 'light' ? 'dark' : 'light';
  document.documentElement.dataset.theme = theme;
  try { localStorage.setItem('labourlens-theme', theme); } catch { /* Storage may be disabled. */ }
  themeLabel();
});
themeLabel();
const repo = 'https://github.com/mihirkhandekar/labourlens/blob/master/';
const percent = new Intl.NumberFormat('en-SG', {style: 'percent', maximumFractionDigits: 0});
function anchor(text, href) { const a = el('a', '', text); a.href = href; return a; }
function table(caption, headers, rows) {
  const node = el('table', 'iv-table'); node.append(el('caption', '', caption));
  const head = el('tr'); headers.forEach(text => { const th = el('th', '', text); th.scope = 'col'; head.append(th); });
  const body = el('tbody'); rows.forEach(row => {
    const tr = el('tr'); row.forEach((text, i) => { const cell = el(i === 0 ? 'th' : 'td', '', text); if (!i) cell.scope = 'row'; tr.append(cell); }); body.append(tr);
  });
  node.append(add(el('thead'), head), body); return node;
}
function render(page) {
  const c = page.content; const m = page.measurements;
  const contents = el('nav', 'iv-contents'); contents.setAttribute('aria-label', 'Assessment contents');
  contents.append(el('p', 'iv-contents-title', 'Contents'));
  const documentBody = el('article', 'iv-document');
  const header = el('header', 'iv-header');
  header.append(el('h1', '', c.title), el('p', 'iv-scope', c.scope), el('h2', 'iv-abstract-title', 'Abstract'), el('p', '', c.abstract));
  documentBody.append(header);
  function addSection(id, title) {
    const section = el('section', 'iv-section'); section.id = id;
    const heading = el('h2', '', title); heading.id = `${id}-title`; section.setAttribute('aria-labelledby', heading.id);
    section.append(heading); documentBody.append(section);
    const a = anchor(title, `#${id}`); contents.append(a); return section;
  }
  const approach = addSection('approach', 'Current approach');
  const approachList = el('ul'); c.approach.forEach(text => approachList.append(el('li', '', text))); approach.append(approachList);
  function results(kind) {
    if (kind === 'retrieval') return table('Relevant report passages in the first eight results. Same development set.', ['Method', 'Passage hit rate'], [
      ['BM25 keyword search', percent.format(m.retrieval.R0)],
      ['Filter then rerank', percent.format(m.retrieval.R3)]
    ]);
  }
  c.sections.forEach(spec => {
    const section = addSection(spec.id, spec.title);
    section.append(el('p', 'iv-summary', spec.summary));
    spec.paragraphs.forEach(p => section.append(el('p', '', p.text)));
    spec.tables.forEach(kind => section.append(results(kind)));
    spec.proposals.forEach(proposal => {
      const detail = el('details', 'iv-proposal');
      const registered = proposal.title.startsWith('Third Decisions attempt:');
      detail.append(el('summary', '', `${registered ? 'Registered plan, untested' : 'Proposal'}: ${proposal.title}`));
      const dl = el('dl');
      [['What I would change', proposal.title], ['Why', proposal.gap], ['Plan', proposal.measure], ['How I would check it', proposal.threshold], ['Status', registered ? 'Preregistered plan; untested; not adopted' : proposal.status]].forEach(([term, text]) => dl.append(el('dt', '', term), el('dd', '', text)));
      detail.append(dl); section.append(detail);
    });
  });
  const limitations = addSection('limitations', 'Limitations and threats to validity');
  const list = el('ul'); c.limitations.forEach(text => list.append(el('li', '', text))); limitations.append(list);
  const components = addSection('components', 'Mocked or unverified components and their production replacements');
  components.append(el('p', 'iv-summary', 'Production design only. These replacements are not deployed or verified.'));
  components.append(table('Current boundaries and proposed production architecture.', ['Component', 'Current state', 'Proposed production replacement'], c.components.map(item => [item.component, item.current, item.replacement])));
  documentBody.append(add(el('footer', 'iv-footer'), anchor('Project report', '/'), anchor('Short assessment source', `${repo}docs/innovation.md`)));
  root.replaceChildren(contents, documentBody);
  if ('IntersectionObserver' in window) {
    const links = new Map([...contents.querySelectorAll('a')].map(a => [a.hash.slice(1), a]));
    const visible = new Set();
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => entry.isIntersecting ? visible.add(entry.target.id) : visible.delete(entry.target.id));
      const first = [...documentBody.querySelectorAll('section')].find(s => visible.has(s.id));
      if (first) links.forEach((a, id) => id === first.id ? a.setAttribute('aria-current', 'location') : a.removeAttribute('aria-current'));
    }, {rootMargin: '-8% 0px -55% 0px', threshold: 0});
    documentBody.querySelectorAll('section').forEach(section => observer.observe(section));
  }
}
try {
  const response = await fetch('/static/data/report.json', {credentials: 'same-origin'});
  if (!response.ok) throw new Error('The report data is unavailable.');
  const report = await response.json();
  if (!report.innovation) throw new Error('The innovation projection is missing. Run labourlens build-report.');
  render(report.innovation);
} catch (error) {
  root.replaceChildren(el('h1', '', 'Assessment unavailable'), el('p', '', error.message), anchor('Project report', '/'));
}
