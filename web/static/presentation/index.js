import {el, fmt, revealAll, whenVisible, reduced} from '../charts.js';
import {model, metricOf, goldOf} from './model.js';
import {stat, textStat, callout, button, toggle} from './ui.js';
import {renderScope} from './ch1-scope.js';
import {renderData} from './ch2-data.js';
import {renderRetrieval} from './ch3-retrieval.js';
import {renderAgent} from './ch4-agent.js';
import {renderEvaluation} from './ch5-evaluation.js';
import {renderSafety} from './ch6-safety.js';
import {renderMcp} from './ch7-mcp.js';
import {renderLimits, renderNext} from './ch8-limits.js';

let printHooked = false;

const CHAPTERS = [
  ['scope', 'Scope', renderScope], ['data', 'The data', renderData], ['retrieval', 'Retrieval', renderRetrieval], ['agent', 'The agent', renderAgent],
  ['evaluation', 'Evaluation', renderEvaluation], ['safety', 'Safety', renderSafety], ['mcp', 'MCP', renderMcp], ['limits', 'Limits', renderLimits], ['next', 'Next', renderNext]
];

function hero(m) {
  const root = el('header', 'pr-hero');
  const a3 = m.evalRow('dev-A3', 'gpt-6-luna'), r3 = m.heldRow('r3', 'gpt-6-luna'), L = m.ladder?.configs, luna = m.securityRow('gpt-6-luna')?.metrics, q = m.section('quality').metrics || {};
  root.append(el('p', 'eyebrow', 'Evidence report'));
  root.append(el('h2', 'pr-title', 'What was built, what was measured, and where it falls short'));
  root.append(el('p', 'pr-hero-lede', 'A long read through the data, the retrieval experiments, the agent and its evaluation. Each chart names the report.json field it is drawn from. Scores were computed on earlier gold versions and compare the system with mostly AI-drafted labels.'));
  const actions = el('div', 'pr-hero-actions');
  actions.append(
    toggle('Show the evidence', false, on => root.closest('.pr-root')?.classList.toggle('pr-evidence', on)),
    button('Print or save as PDF', {iconName: 'print', kind: 'small plain', onClick: () => { revealAll(root.closest('.pr-root') || document); window.print(); }}),
    button('Start reading', {iconName: 'down', kind: 'small btn-primary', onClick: () => document.getElementById('pr-scope')?.scrollIntoView({behavior: reduced() ? 'auto' : 'smooth', block: 'start'})})
  );
  root.append(actions);
  const date = m.generatedAt ? m.generatedAt.slice(0, 10) : 'unknown date';
  const meta = el('p', 'pr-meta');
  meta.append(document.createTextNode(`Report built ${date} from commit `), el('code', 'pr-path', m.commit ? m.commit.slice(0, 7) : 'unknown'), document.createTextNode(`, ${fmt.int(m.artifactCount)} committed artifacts. Numbers that are not in report.json cite a document.`));
  root.append(meta);
  const stats = el('div', 'pr-stats pr-hero-stats');
  [
    stat({value: m.section('sources').metrics?.sources, label: 'Sources, each with a hash', note: 'Statistics, report PDFs and release pages', src: 'report.json › sources.metrics.sources'}),
    stat({value: q.pass, label: 'Validation checks passed', note: `${fmt.int(q.warn)} warnings, published`, src: 'report.json › quality.metrics'}),
    L ? stat({value: L.R3['hit@8'], format: v => fmt.pct(v), label: 'Retrieval hit@8, filter then rerank', note: `Baseline ${fmt.pct(L.R0['hit@8'])}. 128 development cases`, tone: 'brass', src: 'report.json › retrieval.ladder.configs'}) : null,
    a3 ? stat({value: metricOf(a3.metrics.behaviour_accuracy).rate, format: v => fmt.pct(v), label: 'Behaviour accuracy, development', note: `gpt-6-luna, ${a3.metrics.n_cases} cases, ${goldOf(a3).label}`, src: 'report.json › evaluation.rows[agent-dev-A3/gpt-6-luna]'}) : null,
    r3 ? stat({value: metricOf(r3.metrics.behaviour_accuracy).rate, format: v => fmt.pct(v), label: 'Behaviour accuracy, held-out', note: `${r3.metrics.n_cases} cases, ${goldOf(r3).label}. The r3 gain is inconclusive`, src: 'report.json › evaluation.rows[agent-heldout-H-r3/gpt-6-luna]'}) : null,
    luna ? textStat({text: `${luna.passed}/${luna.n_scored}`, label: 'Threat cases passed', note: 'One failure type is still open: T-I06', tone: 'warn', src: 'report.json › security.rows[gpt-6-luna].metrics'}) : null
  ].filter(Boolean).forEach(item => stats.append(item));
  root.append(stats);
  root.append(callout({
    tone: 'warn', title: 'Read this first',
    items: ['Gold v3.5 has 45 owner-reviewed cases and 223 AI drafts. The owner decided 125 cards, 95 of them by agreeing with an AI suggestion, so this is not independent review.', `Scores on an earlier gold version are historical. Development rows here use ${goldOf(a3).label}; held-out rows use ${goldOf(r3).label}${goldOf(r3).version ? ', and a v3.5 rescore is pending' : ''}.`, 'The held-out set has 31 cases, and the r3 advantage on it is inconclusive.', 'One safety failure, T-I06, is open (chapter 6). The ingestion scanner misses paraphrased attacks, and extraction has known defects.'],
    src: 'README.md · docs/system-card.md · docs/human-review/owner-review-summary.md · chapter 8'
  }));
  return root;
}

function rail(chapters) {
  const nav = el('nav', 'pr-rail');
  nav.setAttribute('aria-label', 'Presentation chapters');
  const track = el('div', 'pr-rail-track');
  track.setAttribute('aria-hidden', 'true');
  track.append(el('i', 'pr-rail-fill'));
  const ol = el('ol', 'pr-rail-list');
  const links = chapters.map(([id, label], i) => {
    const li = el('li', 'pr-rail-item');
    const a = el('a', 'pr-rail-link');
    a.href = `#pr-${id}`;
    a.append(el('span', 'pr-rail-no', String(i + 1).padStart(2, '0')), el('span', 'pr-rail-label', label));
    a.addEventListener('click', event => {
      event.preventDefault();
      document.getElementById(`pr-${id}`)?.scrollIntoView({behavior: reduced() ? 'auto' : 'smooth', block: 'start'});
    });
    li.append(a);
    ol.append(li);
    return a;
  });
  nav.append(track, ol);
  return {nav, links, fill: track.firstChild};
}

export function mountPresentation(root, report, ctx = {}) {
  root.textContent = '';
  root.classList.add('pr-root');
  if (!report || typeof report !== 'object') {
    root.append(el('p', 'pr-empty', 'The report data could not be loaded. Rebuild it with: uv run labourlens build-report.'));
    return;
  }
  const m = model(report);
  const layout = el('div', 'pr-layout');
  const main = el('div', 'pr-main');
  const sections = [];
  CHAPTERS.forEach(([id, label, render]) => {
    try { sections.push(render(m, ctx)); }
    catch (error) {
      const failed = el('section', 'pr-chapter');
      failed.id = `pr-${id}`;
      failed.append(callout({tone: 'bad', title: `${label} could not be drawn`, text: 'Part of the report data is missing or malformed. Other chapters are unaffected.'}));
      sections.push(failed);
      if (typeof console !== 'undefined') console.error(`presentation chapter ${id}`, error);
    }
  });
  const r = rail(CHAPTERS);
  main.append(hero(m), ...sections);
  layout.append(r.nav, main);
  root.append(layout);

  // Active chapter in the rail, driven by an IntersectionObserver (no scroll listener).
  const setActive = index => {
    r.links.forEach((link, i) => { if (i === index) link.setAttribute('aria-current', 'step'); else link.removeAttribute('aria-current'); link.classList.toggle('is-done', i < index); });
    r.fill.parentElement.style.setProperty('--p', String((index + 1) / CHAPTERS.length));
  };
  if (typeof IntersectionObserver === 'function') {
    const io = new IntersectionObserver(entries => {
      entries.forEach(entry => { if (entry.isIntersecting) setActive(sections.indexOf(entry.target)); });
    }, {rootMargin: '-35% 0px -55% 0px', threshold: 0});
    sections.forEach(section => io.observe(section));
  }
  setActive(-1);
  root.querySelectorAll('.pr-reveal').forEach(node => whenVisible(node, () => node.classList.add('is-in')));
  if (!printHooked) { printHooked = true; window.addEventListener('beforeprint', () => document.querySelectorAll('.pr-root').forEach(node => revealAll(node))); }
}
