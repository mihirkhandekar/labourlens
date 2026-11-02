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
const repo = 'https://github.com/mihirkhandekar/labourlens/blob/main/';
const rateFormat = new Intl.NumberFormat('en-SG', {minimumFractionDigits: 3, maximumFractionDigits: 3});
const rate = n => typeof n === 'number' ? rateFormat.format(n) : 'Not recorded';
const interval = values => Array.isArray(values) ? `[${values.map(rate).join(', ')}]` : 'Not recorded';
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
  const references = new Map(c.references.map((reference, i) => [reference.id, {...reference, number: i + 1}]));
  function cited(text, refs = []) {
    const p = el('p', '', text);
    refs.forEach(id => {
      const ref = references.get(id); if (!ref) return;
      const a = anchor(`[${ref.number}]`, `${repo}${ref.path}`); a.setAttribute('aria-label', `Reference ${ref.number}: ${ref.label}`);
      p.append(document.createTextNode(' '), add(el('sup'), a));
    }); return p;
  }
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
    if (kind === 'retrieval') return table('Table 1. Retrieval, 128 development text questions; 95% case-bootstrap intervals.', ['Method', 'n', 'Hit@8', '95% interval'], [
      ['Hybrid', String(m.retrieval.n), rate(m.retrieval.R0), interval(m.retrieval_intervals.R0)],
      ['Filter then rerank', String(m.retrieval.n), rate(m.retrieval.R3), interval(m.retrieval_intervals.R3)]
    ]);
    if (kind === 'answers') return table('Table 2. Behaviour accuracy, gpt-6-luna, two-run means. Difference: rerank minus hybrid.', ['Set', 'n', 'Rerank', 'Hybrid', 'Difference [95% interval]'], m.splits.map(split => {
      const arms = Object.fromEntries(split.arms.map(a => [a.arm, a]));
      return [{dev: 'Development', registered: 'Original test', fresh: 'Fresh test'}[split.id], String(split.n), rate(arms.r3?.accuracy), rate(arms.hybrid?.accuracy), `${rate(split.paired.paired_difference)} ${interval(split.paired.interval)}`];
    }));
    const arm = m.splits.find(s => s.id === 'dev')?.arms.find(a => a.arm === 'r3');
    return table('Table 3. Development runtime and estimated cost, filter then rerank.', ['Measure', 'Value', 'Unit'], [
      ['Mean of run medians', arm ? arm.latency.toFixed(2) : 'Not recorded', 'seconds'],
      ['Run p95 values', arm ? arm.p95_runs.join(' / ') : 'Not recorded', 'seconds'],
      ['Mean estimated cost', arm ? arm.cost.toFixed(6) : 'Not recorded', 'USD / question']
    ]);
  }
  c.sections.forEach(spec => {
    const section = addSection(spec.id, spec.title);
    section.append(el('p', 'iv-summary', spec.summary));
    spec.paragraphs.forEach(p => section.append(cited(p.text, p.refs)));
    spec.tables.forEach(kind => section.append(results(kind)));
    spec.proposals.forEach(proposal => {
      const detail = el('details', 'iv-proposal');
      detail.append(el('summary', '', `Proposal: ${proposal.title}`));
      const dl = el('dl');
      [['Proposal', proposal.title], ['Evidence gap it closes', proposal.gap], ['Measure', proposal.measure], ['Success threshold', proposal.threshold], ['Status', proposal.status]].forEach(([term, text]) => dl.append(el('dt', '', term), el('dd', '', text)));
      detail.append(dl); section.append(detail);
    });
  });
  const limitations = addSection('limitations', 'Limitations and threats to validity');
  const list = el('ul'); c.limitations.forEach(text => list.append(el('li', '', text))); limitations.append(list);
  const components = addSection('components', 'Mocked or unverified components and their production replacements');
  components.append(table('Table 4. Current boundaries and required production replacements.', ['Component', 'Current state', 'Production replacement'], c.components.map(item => [item.component, item.current, item.replacement])));
  const refs = addSection('references', 'References');
  const refList = el('ol', 'iv-references'); c.references.forEach(reference => refList.append(add(el('li'), anchor(reference.label, `${repo}${reference.path}`)))); refs.append(refList);
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
