// Rights-safe numeric projections only. No report or question text is rendered.
import {el} from '../charts.js';
import data from './experiments-data.js';
import {EXPERIMENTS_B} from './experiments-data-b.js';

const extra = EXPERIMENTS_B.map(item => ({
  ...item,
  changed: item.factorsChanged.join(' '),
  fixed: item.heldFixed.join(' '),
  measurement: `${item.measurement.cases}; n=${item.measurement.n}. Build: ${item.measurement.corpusOrSystem}. ${item.measurement.metrics.join(' ')}`,
  tables: [...(item.table ? [item.table] : []), ...(item.tables || [])].map(t => ({...t, title: t.caption})),
  exampleNote: `${item.example.title}: ${item.example.lines.join(' ')}`,
  examples: [],
  limit: item.doesNotShow
}));

// Most relevant card for each main slide (by title), then a chapter fallback. Unmatched slides
// open at the top of the notebook.
const BY_TITLE = {
  'Processing reports': 'e1b',
  'Retrieval Strategies': 'e6',
  'Does filtering help?': 'r-series',
  'Statistics lookup through MCP': 'agent-mcp-all-tools',
  'Agent loop': 'agent-versus-fixed',
  'Three example runs': 'agent-m4-bounded-tools',
  'Checking the answer': 'generation-groundedness',
  'Choosing models': 'generation-m3-g1',
  'How I evaluated': 'generation-final-dev',
  'Does better retrieval improve answers?': 'generation-final-dev',
  'Attacks and defences': 'threat-v2-challenge',
  'Agent Workbench': 'agent-served-chain-s65',
  'C. Retrieval reference': 'e6',
  'D. Agent reference': 'agent-m4-bounded-tools',
  'E. Evaluation reference': 'generation-final-dev',
  'F. Safety reference': 'threat-v2-challenge',
  'G. MCP reference': 'agent-mcp-all-tools',
  'M. Live app against the evaluated system': 'agent-served-changes-not-evaluated',
  'P. Where the system still fails': 'agent-v2post-diagnostic'
};
const BY_CHAPTER = {Retrieval: 'experiment-group-retrieval', Agent: 'experiment-group-agent', Answer: 'experiment-group-generation', Checks: 'experiment-group-generation', Safety: 'experiment-group-threat', Processing: 'e1b'};

export function experimentTarget(slide) {
  const id = BY_TITLE[slide?.dataset.title] || BY_CHAPTER[slide?.dataset.chapter];
  return id && !id.startsWith('experiment-group-') ? `experiment-${id}` : id || null;
}

// Open and scroll to a card once the notebook slide is laid out.
export function revealExperiment(slide, id) {
  const go = () => {
    const target = id && slide.querySelector(`#${id}`);
    if (!target) return;
    if (target instanceof HTMLDetailsElement) target.open = true;
    target.scrollIntoView({block: 'start'});
    target.focus({preventScroll: true});
  };
  go();
  requestAnimationFrame(() => requestAnimationFrame(go));
}

function table(spec) {
  const wrap = el('div', 'experiment-table');
  const t = el('table');
  const caption = el('caption', '', spec.title || 'Measured results'); t.append(caption);
  const head = el('thead'), tr = el('tr');
  spec.columns.forEach(value => tr.append(el('th', '', value))); head.append(tr); t.append(head);
  const body = el('tbody');
  spec.rows.forEach(row => {
    const r = el('tr');
    row.forEach(value => { const cell = el('td'); if (value instanceof Node) cell.append(value); else cell.textContent = String(value ?? '-'); r.append(cell); });
    body.append(r);
  });
  t.append(body); wrap.append(t, el('p', 'experiment-source', `Source: ${spec.source}`));
  return wrap;
}

export function experimentsSpec() {
  const panel = el('div', 'experiments-content');
  panel.append(el('p', 'experiments-intro', 'Saved experiments, grouped by the question they tested. Results belong to the build named on each card, not necessarily the served app. Select a row to inspect the design, sources, worked example and limits. The page opened at the card most relevant to the slide you left; E twice within 400 ms closes it and returns to that slide.'));
  const experiments = [...data.experiments, ...extra];
  const jump = (id, label) => {
    const link = el('a', '', label); link.href = `#${id}`;
    link.addEventListener('click', event => {
      event.preventDefault(); event.stopPropagation();
      const target = panel.querySelector(`#${id}`);
      if (target instanceof HTMLDetailsElement) target.open = true;
      target?.scrollIntoView({block: 'start'});
      target?.focus({preventScroll: true});
    });
    return link;
  };
  const index = el('nav', 'experiment-index'); index.setAttribute('aria-label', 'Experiment groups');
  const groups = [['retrieval', 'Retrieval'], ['generation', 'Generation'], ['agent', 'Agent'], ['threat', 'Threat']];
  groups.forEach(([id, label]) => index.append(jump(`experiment-group-${id}`, label))); panel.append(index);
  const overview = table({title: 'Experiment index · select a card', source: 'Cited artifact paths on each card below', columns: ['Id', 'Factor changed', 'Headline result', 'Details'], rows: experiments.map(e => [e.id, e.changed.length > 105 ? `${e.changed.slice(0, 102)}…` : e.changed, e.takeaway, jump(`experiment-${e.id}`, 'Open card')])});
  overview.classList.add('experiment-overview'); panel.append(overview);
  const definitions = el('details', 'experiment-entry');
  definitions.append(el('summary', '', 'How to read the measurements'));
  definitions.append(el('p', '', data.definitions)); panel.append(definitions);
  groups.forEach(([group, label]) => {
    const heading = el('h3', 'experiment-group-title', label); heading.id = `experiment-group-${group}`; heading.tabIndex = -1; panel.append(heading);
    experiments.filter(e => e.group === group).forEach(experiment => {
    const entry = el('details', 'experiment-entry'); entry.id = `experiment-${experiment.id}`; entry.tabIndex = -1;
    entry.append(el('summary', '', `${experiment.title} · ${experiment.status || 'measured'}`));
    for (const [label, key] of [['Question', 'question'], ['Changed', 'changed'], ['Held fixed', 'fixed'], ['Measurement', 'measurement']]) {
      entry.append(el('p', '', `${label}: ${experiment[key]}`));
    }
    experiment.tables.forEach(spec => entry.append(table(spec)));
    entry.append(el('h3', '', 'Worked example'));
    entry.append(el('p', '', experiment.exampleNote));
    experiment.examples.forEach(example => {
      entry.append(el('p', 'experiment-source', `${example.case_id} · ${example.label} · first relevant rank: ${example.first_relevant_rank ?? 'not in saved ranking'} · Source: ${example.source}`));
      entry.append(table({title: `${example.case_id}: saved ranked candidates`, source: example.source, columns: ['Rank', 'Chunk id', 'Relevant', 'Score', 'Words', 'Source id', 'Locator'], rows: example.ranked.map((r, index) => [index + 1, r.chunk_id, r.relevant, r.score, r.words, r.source_id, r.locator])}));
    });
    entry.append(el('p', 'experiment-takeaway', `What to say: ${experiment.takeaway}`));
    entry.append(el('p', '', `Does not show: ${experiment.limit}`)); panel.append(entry);
  });
  });
  return {id: 'experiments', chapter: 'Experiments', layout: 'scroll', cls: 'experiments', title: 'Experiment notebook', panel: [panel], notes: ['Numeric evidence only; no MOM passage text. Open each experiment for its design, sources and limitations.']};
}
