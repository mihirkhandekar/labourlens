import {el, svgEl, fmt, finite, figure, interactive, columns, dotPlot, reduced} from '../charts.js';
import {chapter, section, grid, stat, callout, evi, button} from './ui.js';

const NODES = {
  validate_question: {label: 'validate_question', sub: 'input guard', guard: true, text: 'Rejects an empty question or one over 1,000 characters. Flags instruction-like text without trusting it.'},
  plan_research: {label: 'plan_research', sub: 'planner model', text: 'The planner proposes up to three read-only tool calls, or decides to finish. It never sees passage text.'},
  execute_tool: {label: 'execute_tool', sub: 'typed tools', text: 'Runs each call in a worker thread with a 10 second limit. One retry for a transient failure.'},
  assess_evidence: {label: 'assess_evidence', sub: 'count and check', text: 'Counts passages, observations and calculations. If every tool call failed it reports an operational failure, never "no evidence".'},
  generate_answer: {label: 'generate_answer', sub: 'answer model', text: 'Writes a structured answer from the evidence, with a verbatim quote for each claim.'},
  validate_answer: {label: 'validate_answer', sub: 'citation guard', guard: true, text: 'Rejects a cited label that is not in the context, a quote that is not verbatim, a quote over 40 words, or a status that contradicts the content. One repair is allowed.'},
  finalize: {label: 'finalize', sub: 'output guard', guard: true, text: 'Blocks answers that contain a known secret or system-prompt text, then sets the outcome.'}
};
const ORDER = Object.keys(NODES);

// Geometry for a given width. Wide: two rows in a snake. Narrow: one column.
function layout(W) {
  const nodes = {}, edges = [];
  const w = W >= 760 ? Math.min(150, (W - 80) / 4.6) : Math.min(210, W * 0.56), h = 54;
  const node = (id, x, y) => { nodes[id] = {id, x, y, w, h}; };
  const pt = (id, side, dx = 0, dy = 0) => {
    const n = nodes[id];
    return side === 'r' ? [n.x + n.w / 2 + dx, n.y + dy] : side === 'l' ? [n.x - n.w / 2 + dx, n.y + dy] : side === 't' ? [n.x + dx, n.y - n.h / 2 + dy] : [n.x + dx, n.y + n.h / 2 + dy];
  };
  const line = (a, b) => `M${a[0].toFixed(1)} ${a[1].toFixed(1)}L${b[0].toFixed(1)} ${b[1].toFixed(1)}`;
  const curve = (a, c1, c2, b) => `M${a[0].toFixed(1)} ${a[1].toFixed(1)}C${c1[0].toFixed(1)} ${c1[1].toFixed(1)} ${c2[0].toFixed(1)} ${c2[1].toFixed(1)} ${b[0].toFixed(1)} ${b[1].toFixed(1)}`;
  const add = (from, to, d, label, lx, ly, kind = 'main', anchor = 'middle') => edges.push({from, to, d, label, lx, ly, kind, anchor});
  if (W >= 760) {
    const cols = [0, 1, 2, 3].map(i => 50 + w / 2 + i * ((W - 100 - w) / 3));
    const y1 = 96, y2 = 270;
    node('validate_question', cols[1], y1); node('plan_research', cols[2], y1); node('execute_tool', cols[3], y1);
    node('assess_evidence', cols[3], y2); node('generate_answer', cols[2], y2); node('validate_answer', cols[1], y2); node('finalize', cols[0], y2);
    const start = {x: cols[0], y: y1};
    add('start', 'validate_question', line([start.x + 9, start.y], pt('validate_question', 'l')), '', 0, 0);
    add('validate_question', 'plan_research', line(pt('validate_question', 'r'), pt('plan_research', 'l')), 'accepted', (cols[1] + cols[2]) / 2, y1 - 9);
    add('plan_research', 'execute_tool', line(pt('plan_research', 'r', 0, -10), pt('execute_tool', 'l', 0, -10)), 'up to 3 calls', (cols[2] + cols[3]) / 2, y1 - 19);
    add('execute_tool', 'plan_research', curve(pt('execute_tool', 't', -18), [cols[3] - 18, y1 - 70], [cols[2] + 18, y1 - 70], pt('plan_research', 't', 18)), 'next round, at most 2', (cols[2] + cols[3]) / 2, y1 - 62, 'loop');
    add('plan_research', 'assess_evidence', curve(pt('plan_research', 'b', 22), [cols[2] + 22, y1 + 105], [cols[3] - 70, y2 - 100], pt('assess_evidence', 't', -30)), 'finish', cols[2] + 74, y1 + 98, 'main', 'start');
    add('execute_tool', 'assess_evidence', line(pt('execute_tool', 'b', 22), pt('assess_evidence', 't', 22)), 'limit reached', cols[3] + 30, (y1 + y2) / 2, 'main', 'start');
    add('assess_evidence', 'generate_answer', line(pt('assess_evidence', 'l'), pt('generate_answer', 'r')), 'evidence ready', (cols[2] + cols[3]) / 2, y2 - 9);
    add('generate_answer', 'validate_answer', line(pt('generate_answer', 'l', 0, -10), pt('validate_answer', 'r', 0, -10)), 'answer', (cols[1] + cols[2]) / 2, y2 - 19);
    add('validate_answer', 'generate_answer', curve(pt('validate_answer', 'b', 18), [cols[1] + 18, y2 + 76], [cols[2] - 18, y2 + 76], pt('generate_answer', 'b', -18)), 'one repair', (cols[1] + cols[2]) / 2, y2 + 66, 'loop');
    add('validate_answer', 'finalize', line(pt('validate_answer', 'l'), pt('finalize', 'r')), 'valid', (cols[0] + cols[1]) / 2, y2 - 9);
    add('validate_question', 'finalize', curve(pt('validate_question', 'b', -24), [cols[1] - 24, y1 + 62], [cols[0] + 30, y2 - 72], pt('finalize', 't', 14)), 'rejected input', cols[0] + 6, (y1 + y2) / 2 - 8, 'exit', 'start');
    add('assess_evidence', 'finalize', curve(pt('assess_evidence', 'b', -20), [cols[3] - 20, y2 + 120], [cols[0] + 20, y2 + 120], pt('finalize', 'b', 20)), 'tool outage: operational failure', (cols[0] + cols[3]) / 2, y2 + 111, 'exit');
    return {nodes, edges, H: y2 + 140, start, w, wide: true};
  }
  const cx = W / 2 + 4, gap = 76, top = 54;
  ORDER.forEach((id, i) => node(id, cx, top + i * gap));
  const start = {x: cx, y: 14};
  add('start', 'validate_question', line([start.x, start.y + 8], pt('validate_question', 't')), '', 0, 0);
  ORDER.slice(0, -1).forEach((id, i) => {
    const next = ORDER[i + 1];
    const labels = {validate_question: 'accepted', plan_research: 'up to 3 calls', execute_tool: 'limit reached', assess_evidence: 'evidence ready', generate_answer: 'answer', validate_answer: 'valid'};
    add(id, next, line(pt(id, 'b'), pt(next, 't')), labels[id] || '', cx + 8, (nodes[id].y + nodes[next].y) / 2 + 4, 'main', 'start');
  });
  add('execute_tool', 'plan_research', curve(pt('execute_tool', 'r'), [cx + w / 2 + 52, nodes.execute_tool.y], [cx + w / 2 + 52, nodes.plan_research.y], pt('plan_research', 'r')), 'next round', cx + w / 2 + 6, (nodes.execute_tool.y + nodes.plan_research.y) / 2 + 4, 'loop', 'start');
  add('plan_research', 'assess_evidence', curve(pt('plan_research', 'l'), [cx - w / 2 - 44, nodes.plan_research.y], [cx - w / 2 - 44, nodes.assess_evidence.y], pt('assess_evidence', 'l')), 'finish', cx - w / 2 - 6, (nodes.plan_research.y + nodes.assess_evidence.y) / 2 + 4, 'main', 'end');
  add('validate_answer', 'generate_answer', curve(pt('validate_answer', 'l'), [cx - w / 2 - 52, nodes.validate_answer.y], [cx - w / 2 - 52, nodes.generate_answer.y], pt('generate_answer', 'l')), 'repair', cx - w / 2 - 6, (nodes.validate_answer.y + nodes.generate_answer.y) / 2 + 4, 'loop', 'end');
  return {nodes, edges, H: top + ORDER.length * gap - 10, start, w, wide: false};
}

const EXPLAIN = {
  'validate_question:accepted': () => 'The question passed the length check. Instruction-like text is flagged, never trusted.',
  'plan_research:gather': d => `Round ${d.round}: the planner chose ${d.n_calls} tool call${d.n_calls === 1 ? '' : 's'}.`,
  'execute_tool:ok': d => `${d.tool} ran in ${d.seconds} s and returned validated results.`,
  'plan_research:finish': d => `Round ${d.round}: the planner decided it had enough evidence and made no more calls.`,
  'assess_evidence:evidence_ready': d => `Evidence ready: ${d.passages} passages, ${d.observations} observations, ${d.calculations} calculations.`,
  'generate_answer:generated': () => 'The answer model wrote a structured answer from the evidence only.',
  'validate_answer:valid': () => 'Every label and quote checked out, so no repair was needed.',
  'finalize:answered': () => 'The output guard passed the answer. Outcome: answered.'
};
const explain = ev => (EXPLAIN[`${ev.node}:${ev.event}`] || (() => `${ev.node}: ${ev.event}`))(ev.detail || {});

function graphFigure(m) {
  const events = m.events;
  const state = {step: events.length ? -1 : -1, timer: null};
  const card = el('div', 'pr-step-card');
  const cardTitle = el('p', 'pr-step-title', 'Press Next to step through a recorded run');
  const cardText = el('p', 'pr-step-text', 'Nothing is shown here except node names, events and counts. No model text is recorded or displayed.');
  const cardMeta = el('p', 'pr-step-meta mono', '');
  card.append(cardTitle, cardText, cardMeta);
  card.setAttribute('aria-live', 'polite');
  const counter = el('span', 'pr-step-count', events.length ? `Step 0 of ${events.length}` : 'No recorded run');
  let svgRef = null;
  const paint = () => {
    if (!svgRef) return;
    const visited = new Set(events.slice(0, state.step + 1).map(e => e.node));
    const current = state.step >= 0 ? events[state.step].node : null;
    const prev = state.step > 0 ? events[state.step - 1].node : state.step === 0 ? 'start' : null;
    const used = new Set();
    for (let i = 0; i <= state.step; i++) used.add(`${i ? events[i - 1].node : 'start'}>${events[i].node}`);
    svgRef.querySelectorAll('[data-node]').forEach(node => {
      node.classList.toggle('is-done', visited.has(node.dataset.node));
      node.classList.toggle('is-active', node.dataset.node === current);
    });
    svgRef.querySelectorAll('[data-edge]').forEach(edge => {
      const key = edge.dataset.edge;
      edge.classList.toggle('is-done', used.has(key));
      edge.classList.toggle('is-active', state.step >= 0 && key === `${prev}>${current}`);
    });
    if (state.step < 0) { cardTitle.textContent = 'Press Next to step through a recorded run'; cardText.textContent = 'Nothing is shown here except node names, events and counts. No model text is recorded or displayed.'; cardMeta.textContent = ''; }
    else {
      const ev = events[state.step];
      cardTitle.textContent = `${ev.node} \u2192 ${ev.event}`;
      cardText.textContent = explain(ev);
      cardMeta.textContent = Object.keys(ev.detail || {}).length ? JSON.stringify(ev.detail) : 'no detail recorded';
    }
    counter.textContent = `Step ${state.step + 1} of ${events.length}`;
  };
  const go = step => { state.step = Math.max(-1, Math.min(events.length - 1, step)); paint(); };
  const stop = () => { if (state.timer) { clearInterval(state.timer); state.timer = null; } playBtn.firstChild.textContent = 'Play'; };
  const playBtn = button('Play', {iconName: 'play', kind: 'small', onClick: () => {
    if (state.timer) { stop(); return; }
    if (state.step >= events.length - 1) go(-1);
    playBtn.firstChild.textContent = 'Pause';
    state.timer = setInterval(() => { if (state.step >= events.length - 1) { stop(); return; } go(state.step + 1); }, reduced() ? 1800 : 1300);
  }});
  const prevBtn = button('Back', {iconName: 'prev', kind: 'small plain', onClick: () => { stop(); go(state.step - 1); }});
  const nextBtn = button('Next', {iconName: 'next', kind: 'small btn-primary', onClick: () => { stop(); go(state.step + 1); }});
  const resetBtn = button('Reset', {iconName: 'reset', kind: 'small plain', onClick: () => { stop(); go(-1); }});
  [prevBtn, nextBtn, resetBtn].forEach(b => b.disabled = !events.length);
  playBtn.disabled = !events.length;
  const controls = el('div', 'pr-controls pr-step-controls');
  controls.setAttribute('role', 'group');
  controls.setAttribute('aria-label', 'Step through a recorded run');
  controls.append(prevBtn, nextBtn, playBtn, resetBtn, counter);
  const fig = figure({
    id: 'fig-graph', title: 'The agent graph: seven nodes, three guards', wide: true,
    takeaway: 'One agent, one loop for evidence gathering (at most 2 rounds) and one for repair (one attempt). Brass outlines mark the guards. Any tool outage ends as an operational failure, never as "no evidence".',
    summary: `LangGraph state graph with seven nodes: ${ORDER.join(', ')}. Guards: validate_question, validate_answer and finalize. Loops: execute_tool back to plan_research; validate_answer back to generate_answer.`,
    source: {data: 'report.json › agent.events (recorded run) · node set from docs/architecture.md §4', files: ['experiments/runs/web-live-smoke.trace.json', 'src/labourlens/agent/graph.py']},
    note: 'The recorded run is a statistics-only smoke test: it used get_series and no report passages.',
    controls,
    table: () => ({caption: 'Recorded run, one row per event', columns: ['Step', 'Node', 'Event', 'Detail'], rows: events.map((e, i) => [i + 1, e.node, e.event, JSON.stringify(e.detail || {})])}),
    aside: card,
    draw: (host, c) => {
      const geo = layout(c.width);
      const svg = svgEl('svg', {class: 'pr-svg pr-graph', width: c.width, height: geo.H, viewBox: `0 0 ${c.width} ${geo.H}`, focusable: 'false'});
      svg.setAttribute('aria-label', 'Agent state graph');
      const defs = svgEl('defs');
      ['', '-active'].forEach(suffix => {
        const marker = svgEl('marker', {id: `pr-arrow${suffix}`, viewBox: '0 0 10 10', refX: 8, refY: 5, markerWidth: 7, markerHeight: 7, orient: 'auto-start-reverse'});
        marker.append(svgEl('path', {d: 'M1 1L9 5L1 9', class: `pr-arrowhead${suffix}`, fill: 'none'}));
        defs.append(marker);
      });
      svg.append(defs);
      geo.edges.forEach(edge => {
        const g = svgEl('g', {class: `pr-edge is-${edge.kind}`, 'data-edge': `${edge.from}>${edge.to}`});
        g.append(svgEl('path', {d: edge.d, class: 'pr-edge-path', fill: 'none', 'marker-end': 'url(#pr-arrow)'}));
        g.append(svgEl('path', {d: edge.d, class: 'pr-edge-flow', fill: 'none'}));
        if (edge.label) g.append(svgEl('text', {x: edge.lx, y: edge.ly, class: 'pr-t pr-t-edge', 'text-anchor': edge.anchor}, edge.label));
        svg.append(g);
      });
      const start = svgEl('g', {class: 'pr-node pr-start', 'data-node': 'start'});
      start.append(svgEl('circle', {cx: geo.start.x, cy: geo.start.y, r: 9, class: 'pr-node-shape'}), svgEl('text', {x: geo.start.x, y: geo.start.y - 16, class: 'pr-t pr-t-sub', 'text-anchor': 'middle'}, 'START'));
      svg.append(start);
      const items = [];
      ORDER.forEach(id => {
        const n = geo.nodes[id], spec = NODES[id];
        const g = svgEl('g', {class: `pr-node${spec.guard ? ' is-guard' : ''}`, 'data-node': id});
        g.append(svgEl('rect', {x: n.x - n.w / 2, y: n.y - n.h / 2, width: n.w, height: n.h, rx: 14, class: 'pr-node-shape'}));
        g.append(svgEl('text', {x: n.x, y: n.y - 3, class: 'pr-t pr-node-label', 'text-anchor': 'middle'}, spec.label));
        g.append(svgEl('text', {x: n.x, y: n.y + 14, class: 'pr-t pr-t-sub', 'text-anchor': 'middle'}, spec.sub));
        if (spec.guard) {
          const badge = svgEl('g', {class: 'pr-guard-badge'});
          badge.append(svgEl('circle', {cx: n.x - n.w / 2 + 2, cy: n.y - n.h / 2 + 2, r: 11}), svgEl('path', {d: `M${n.x - n.w / 2 + 2} ${n.y - n.h / 2 - 4}l5 2v3.4c0 3-2 5.2-5 6.4-3-1.2-5-3.4-5-6.4v-3.4z`, fill: 'none'}));
          g.append(badge);
        }
        svg.append(g);
        const hit = svgEl('rect', {x: n.x - n.w / 2, y: n.y - n.h / 2, width: n.w, height: n.h, rx: 14, class: 'pr-row-hit'});
        svg.append(hit);
        items.push({node: hit, lines: [`${spec.label}${spec.guard ? ' (guard)' : ''}`, spec.text], ax: n.x, ay: n.y - n.h / 2, mark: []});
      });
      host.append(svg);
      interactive(svg, c, items, {label: 'Agent graph nodes. Use arrow keys to move between nodes; each shows what the node does.'});
      svgRef = svg;
      paint();
    }
  });
  return fig;
}

function toolCards(m) {
  const counts = {};
  m.trace.forEach(r => (r.tools_used || []).forEach(t => { counts[t] = (counts[t] || 0) + 1; }));
  const tools = [
    ['search_reports', 'P', 'Searches the MOM report passages: hybrid search, period and release filter, then rerank. Returns passages labelled P1, P2 and so on.'],
    ['get_series', 'O', 'Reads validated statistics by source, indicator, adjustment and period. Returns observations labelled O1, O2 and so on, each with a trace id.'],
    ['calculate_change', 'C', 'Computes a difference or percent change from two observations using exact decimals. Returns a calculation labelled C1. The model never does arithmetic.']
  ];
  const wrap = el('div', 'pr-tools');
  tools.forEach(([name, label, text]) => {
    const card = el('article', 'pr-tool pr-reveal');
    const head = el('header', 'pr-tool-head');
    head.append(el('code', 'pr-tool-name', name), el('span', 'pr-pill-label', 'read-only'));
    card.append(head, el('p', 'pr-tool-text', text));
    const foot = el('p', 'pr-tool-foot');
    foot.append(el('span', 'pr-tool-label', `Label ${label}`), el('span', 'num', `${fmt.int(counts[name])} recorded calls`));
    card.append(foot, evi(`report.json › agent.trace[*].tools_used (${name})`));
    wrap.append(card);
  });
  return wrap;
}

function boundsFigures(m) {
  const trace = m.trace;
  if (!trace.length) return null;
  const hist = (key, max) => Array.from({length: max + 1}, (_, i) => trace.filter(r => r[key] === i).length);
  const calls = hist('tool_calls', 6), rounds = hist('rounds', 2);
  const maxCalls = Math.max(...trace.map(r => r.tool_calls)), maxRounds = Math.max(...trace.map(r => r.rounds));
  const ops = trace.reduce((a, r) => a + (r.operational_failure ? 1 : 0), 0), errors = trace.reduce((a, r) => a + (finite(r.tool_errors) ? r.tool_errors : 0), 0);
  const repaired = trace.filter(r => r.attempts > 1).length;
  const figCalls = figure({
    id: 'fig-calls', title: 'Tool calls per case, all recorded runs',
    takeaway: `Across ${fmt.int(trace.length)} recorded cases the agent made at most ${maxCalls} tool calls and ran at most ${maxRounds} rounds. The limits are 6 and 2. The planner cannot exceed them, and the data confirm it did not.`,
    summary: `Tool calls per case: ${calls.map((n, i) => `${i} calls: ${n} cases`).join(', ')}. Rounds: ${rounds.map((n, i) => `${i}: ${n}`).join(', ')}.`,
    source: {data: 'report.json › agent.trace[*].tool_calls, .rounds', files: ['experiments/runs/agent-dev-A1..A5/*.scores.jsonl']},
    table: () => ({caption: 'Cases by number of tool calls', columns: ['Tool calls', 'Cases', 'Rounds', 'Cases (by rounds)'], rows: calls.map((n, i) => [i, n, i <= 2 ? i : '', i <= 2 ? rounds[i] : ''])}),
    draw: (host, c) => columns(host, c, {categories: calls.map((_, i) => String(i)), series: [{key: 'n', label: 'Cases', cls: 'c1', values: calls, hl: [calls.indexOf(Math.max(...calls))]}], yFormat: fmt.int, yTitle: 'Cases', tipTitle: cat => `${cat} tool calls`, label: 'Cases by number of tool calls'})
  });
  const usage = {};
  trace.forEach(r => (r.tools_used || []).forEach(t => { usage[t] = (usage[t] || 0) + 1; }));
  const rows = Object.entries(usage).sort((a, b) => b[1] - a[1]).map(([name, n], i) => ({label: name, value: n, cls: 'c1', hl: i === 0, lines: [name, `${fmt.int(n)} recorded calls`]}));
  const figTools = figure({
    id: 'fig-tools', title: 'Which tools were called',
    takeaway: `${fmt.int(errors)} tool errors in ${fmt.int(trace.length)} cases; ${fmt.int(ops)} ended as an operational failure. ${fmt.int(repaired)} cases (${fmt.pct(repaired / trace.length)}) needed the one allowed repair of an invalid answer.`,
    summary: rows.map(r => `${r.label}: ${r.value} calls`).join('. '),
    source: {data: 'report.json › agent.trace[*].tools_used, .tool_errors, .operational_failure, .attempts', files: ['experiments/runs/agent-dev-A1..A5/*.scores.jsonl']},
    table: () => ({caption: 'Recorded tool calls', columns: ['Tool', 'Calls'], rows: rows.map(r => [r.label, r.value])}),
    draw: (host, c) => dotPlot(host, c, {rows, mode: 'bar', domain: [0, Math.max(...rows.map(r => r.value)) * 1.1], format: v => fmt.int(v), valueText: r => fmt.int(r.value), axisTitle: 'Recorded calls', label: 'Recorded calls per tool'})
  });
  return {figCalls, figTools, maxCalls, maxRounds, ops, errors, repaired, total: trace.length};
}

export function renderAgent(m, ctx) {
  const ch = chapter({
    id: 'agent', no: 4, eyebrow: 'The agent', title: 'One bounded agent, with guards at the edges',
    lede: 'A LangGraph state graph runs one research agent. It can only call three read-only tools, and code does the arithmetic. Every loop has a limit, every limit is enforced in code, and every failure has a named outcome.'
  });
  const g = section('The state graph', 'Step through a recorded run, or press the arrow keys on the diagram to read what each node does.');
  g.append(graphFigure(m).root);
  ch.body.append(g);

  const t = section('Three typed tools', 'Arguments are checked against enums built from the source catalogue. A tool cannot write, fetch the web or run code.');
  t.append(toolCards(m));
  ch.body.append(t);

  const limits = section('Limits, and whether they held');
  const stats = el('div', 'pr-stats pr-limits');
  const b = boundsFigures(m);
  [
    [2, 'Evidence rounds', b ? `Largest seen: ${b.maxRounds}` : ''], [6, 'Tool calls per run', b ? `Largest seen: ${b.maxCalls}. At most 3 per round.` : 'At most 3 per round.'], [10, 'Seconds per tool call', 'Run in a worker thread with a timeout.'],
    [1, 'Retry, transient tool failure', 'Also 1 retry for malformed planner output.'], [1, 'Repair of an invalid answer', b ? `${fmt.int(b.repaired)} of ${fmt.int(b.total)} cases used it.` : ''], [1000, 'Characters per question', 'Longer input is rejected before any model call.']
  ].forEach(([value, label, note]) => stats.append(stat({value, label, note, src: 'docs/architecture.md › 4. The agent graph · src/labourlens/agent/graph.py'})));
  limits.append(stats);
  if (b) limits.append(grid('pr-split', b.figCalls.root, b.figTools.root));
  ch.body.append(limits);

  ch.body.append(callout({
    tone: 'note', title: 'Eight named outcomes',
    text: 'answered, abstained, clarify, refused, invalid, rejected_input, blocked_output and operational_failure. A tool outage, a timeout or a planner outage ends as operational_failure. It is never reported as missing evidence.',
    src: 'docs/architecture.md › 4. The agent graph'
  }));
  return ch.root;
}
