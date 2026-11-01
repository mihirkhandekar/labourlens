// Slide graphics built from report.json through the model. DOM calls only, no HTML strings, no inline style
// attributes (CSS custom properties are set through the CSSOM). Motion is transform and opacity in CSS.
import {el, svgEl, fmt, finite} from '../charts.js';
import {metricOf} from './model.js';
import {countRunner} from './ui.js';

const PHOS = '/static/vendor/phosphor/';
export function ico(name, cls = '') {
  const node = el('span', `deck-ico ${cls}`.trim());
  node.setAttribute('aria-hidden', 'true');
  node.style.setProperty('--ico', `url("${PHOS}${name}.svg")`);
  return node;
}
const pctS = v => `${v.toFixed(1)}%`;
export const latest = (m, id) => m.values(id, m.periods()).filter(finite).pop();
const previous = (m, id) => m.values(id, m.periods()).filter(finite).slice(-2, -1)[0];

/** G1: one question, several published answers. Numbers are the last observation of each series. */
export function threeAnswers(m) {
  const wrap = el('div', 'g1');
  const to = m.scope[1];
  wrap.append(el('p', 'g1-q', `What was the unemployment rate in ${fmt.quarter(to)}?`));
  const row = el('div', 'g1-row');
  [['unemployment_overall_sa', 'Overall', 'seasonally adjusted'], ['unemployment_resident_sa', 'Resident', 'seasonally adjusted'], ['unemployment_resident_nsa', 'Resident', 'not adjusted']].forEach(([id, who, adj], i) => {
    const v = latest(m, id);
    const card = el('div', 'g1-card'); card.style.setProperty('--i', String(i));
    const num = el('div', 'deck-num num');
    if (finite(v)) num._run = countRunner(num, v, pctS); else num.textContent = 'not recorded';
    card.append(num, el('p', 'g1-who', who), el('p', 'g1-adj', adj));
    row.append(card);
  });
  wrap.append(row);
  return wrap;
}

/** G2: two kinds of source feeding one answer. */
export function twoSources(m) {
  const types = m.section('sources').metrics?.by_type || {};
  const wrap = el('div', 'g2');
  const block = (icon, title, count, unit, lines) => {
    const b = el('div', 'g2-block');
    const head = el('div', 'g2-head'); head.append(ico(icon), el('h3', '', title));
    b.append(head, el('p', 'g2-count num', `${fmt.int(count)} ${unit}`));
    const ul = el('ul', 'g2-list'); lines.forEach(t => ul.append(el('li', '', t))); b.append(ul);
    return b;
  };
  wrap.append(
    block('table', 'Statistics', types.dataset_csv, 'snapshots', ['Unemployment rate', 'Vacancies per unemployed person', 'Retrenchments', 'Employment change by sector']),
    el('div', 'g2-join'),
    block('file-text', 'Reports', types.report_pdf, 'PDFs', [`${fmt.int(types.release_html)} release pages`, 'MOM labour market reports', 'Q3 2025 to Q2 2026'])
  );
  wrap.querySelector('.g2-join').append(ico('arrow-right'), el('p', '', 'One answer, each part cited'));
  return wrap;
}

/** G3: the three document builds. Passage counts are recorded in the README and the decision log, not in report.json. */
export function buildTimeline() {
  const wrap = el('div', 'g3');
  const nodes = [['First build', 13484, 'Original extraction', true], ['Second build', 15915, 'Table and note fixes', false], ['Third build', 16419, 'Six new sources added', false]];
  nodes.forEach(([name, count, why, ran], i) => {
    const n = el('div', 'g3-node'); n.style.setProperty('--i', String(i));
    const dot = el('div', 'g3-dot'); dot.style.setProperty('--d', `${Math.round(60 + (count - 13000) / 3400 * 80)}px`);
    n.append(dot, el('p', 'g3-name', name), el('p', 'g3-count num', `${fmt.int(count)} passages`), el('p', 'g3-why', why));
    if (ran) n.append(el('p', 'g3-tag', 'Most results ran here'));
    wrap.append(n);
  });
  return wrap;
}

/** G4: a table and what extraction made of it. Schematic: cells carry no data. */
export function flattening() {
  const wrap = el('div', 'g4');
  const left = el('div', 'g4-panel');
  left.append(el('p', 'g4-label', 'In the PDF'));
  const table = el('table', 'g4-table');
  [['', 'Q1', 'Q2'], ['Row A', 'value', 'value'], ['Row B', 'value', 'value']].forEach((r, i) => {
    const tr = el('tr'); r.forEach(c => tr.append(el(i === 0 || c.startsWith('Row') ? 'th' : 'td', '', c))); table.append(tr);
  });
  left.append(table);
  const right = el('div', 'g4-panel');
  right.append(el('p', 'g4-label', 'After extraction'), el('p', 'g4-flat', 'Q1 Q2 Row A value value Row B value value'));
  wrap.append(left, ico('arrow-right', 'g4-arrow'), right, el('p', 'g4-note', 'Schematic: cells carry no data'));
  return wrap;
}

/** Bars as a staircase, in SVG. items: {label, value, ci, kind: 'accent' | 'plain' | 'hatched', tag}. */
export function staircase(items, {domain = [0, 1], note} = {}) {
  const W = 1500, H = 560, top = 60, bottom = 120, left = 40, gap = 36;
  const bw = (W - left * 2 - gap * (items.length - 1)) / items.length;
  const svg = svgEl('svg', {viewBox: `0 0 ${W} ${H}`, class: 'g5-svg', role: 'img', focusable: 'false'});
  svg.setAttribute('aria-label', items.map(i => `${i.label}: ${fmt.pct(i.value)}`).join('. '));
  const defs = svgEl('defs'); const pat = svgEl('pattern', {id: 'g5-hatch', width: 12, height: 12, patternUnits: 'userSpaceOnUse', patternTransform: 'rotate(45)'});
  pat.append(svgEl('rect', {width: 12, height: 12, class: 'g5-hatch-bg'}), svgEl('line', {x1: 0, y1: 0, x2: 0, y2: 12, class: 'g5-hatch-line'})); defs.append(pat); svg.append(defs);
  const y = v => top + (H - top - bottom) * (1 - (v - domain[0]) / (domain[1] - domain[0]));
  svg.append(svgEl('line', {x1: left - 10, x2: W - left + 10, y1: y(domain[0]), y2: y(domain[0]), class: 'g5-axis'}));
  items.forEach((it, i) => {
    const x = left + i * (bw + gap);
    const g = svgEl('g', {class: `g5-step is-${it.kind || 'plain'}`});
    g.style.setProperty('--i', String(i));
    g.append(svgEl('rect', {x, y: y(it.value), width: bw, height: y(domain[0]) - y(it.value), rx: 12, class: 'g5-bar'}));
    if (Array.isArray(it.ci)) {
      const cx = x + bw / 2;
      g.append(svgEl('line', {x1: cx, x2: cx, y1: y(it.ci[0]), y2: y(it.ci[1]), class: 'g5-whisker'}), svgEl('line', {x1: cx - 14, x2: cx + 14, y1: y(it.ci[1]), y2: y(it.ci[1]), class: 'g5-whisker'}), svgEl('line', {x1: cx - 14, x2: cx + 14, y1: y(it.ci[0]), y2: y(it.ci[0]), class: 'g5-whisker'}));
    }
    g.append(svgEl('text', {x: x + bw / 2, y: (Array.isArray(it.ci) ? y(it.ci[1]) : y(it.value)) - 22, 'text-anchor': 'middle', class: 'g5-value'}, fmt.pct(it.value)));
    it.label.split('\n').forEach((line, k) => g.append(svgEl('text', {x: x + bw / 2, y: H - bottom + 44 + k * 34, 'text-anchor': 'middle', class: 'g5-label'}, line)));
    if (it.tag) g.append(svgEl('text', {x: x + bw / 2, y: H - bottom + 44 + (it.label.split('\n').length) * 34 + 4, 'text-anchor': 'middle', class: 'g5-tag'}, it.tag));
    svg.append(g);
  });
  const box = el('div', 'g5'); box.append(svg);
  if (note) box.append(el('p', 'g5-note', note));
  return box;
}

/** G5: retrieval staircase from the ladder. */
export function retrievalStaircase(m) {
  const C = m.ladder?.configs;
  if (!C) return null;
  const pick = (k, label, kind) => ({label, value: C[k]['hit@8'], ci: C[k]['hit@8_ci95'], kind});
  return staircase([pick('R0', 'Baseline', 'plain'), pick('R1a', 'Filter\nby period', 'plain'), pick('R2', 'AI rerank', 'plain'), pick('R3', 'Filter, then\nrerank', 'accent')]);
}

/** G8: the experiment staircase, development accuracy for the main model. */
export function experimentStaircase(m) {
  const spec = [[1, 'Baseline', 'plain'], [2, 'Better\nprompt', 'hatched'], [3, 'Filter, then\nrerank', 'accent'], [4, 'Wider\npool', 'hatched'], [5, 'New\nplanner', 'hatched']];
  const items = spec.map(([n, label, kind]) => {
    const row = m.evalRow(`dev-A${n}`, 'gpt-6-luna');
    const b = metricOf(row?.metrics?.behaviour_accuracy);
    return b.rate == null ? null : {label, value: b.rate, ci: b.ci, kind, tag: kind === 'hatched' ? 'no change' : kind === 'accent' ? 'adopted' : ''};
  }).filter(Boolean);
  return items.length ? staircase(items, {domain: [0.5, 1]}) : null;
}

/** G6: the agent loop, drawn from the fixed design. Labels are plain words. */
export function agentLoop() {
  const W = 1560, H = 420;
  const svg = svgEl('svg', {viewBox: `0 0 ${W} ${H}`, class: 'g6-svg', role: 'img', focusable: 'false'});
  svg.setAttribute('aria-label', 'Agent loop: check the question, plan, call a tool, check the evidence, write the answer, check the answer, done. Evidence gathering can repeat for two rounds and the answer can be repaired once.');
  const boxes = [['Check\nquestion', true], ['Plan', false], ['Tool\ncall', false], ['Check\nevidence', true], ['Write\nanswer', false], ['Check\nanswer', true], ['Done', false]];
  const bw = 170, bh = 110, y0 = 150, gap = (W - 40 - bw * boxes.length) / (boxes.length - 1);
  const xs = boxes.map((_, i) => 20 + i * (bw + gap));
  const defs = svgEl('defs'); const mk = svgEl('marker', {id: 'g6-arrow', viewBox: '0 0 10 10', refX: 8, refY: 5, markerWidth: 9, markerHeight: 9, orient: 'auto'});
  mk.append(svgEl('path', {d: 'M0 0 10 5 0 10z', class: 'g6-head'})); defs.append(mk); svg.append(defs);
  boxes.forEach(([label, guard], i) => {
    if (i < boxes.length - 1) svg.append(svgEl('line', {x1: xs[i] + bw, x2: xs[i + 1] - 4, y1: y0 + bh / 2, y2: y0 + bh / 2, class: 'g6-edge', 'marker-end': 'url(#g6-arrow)'}));
  });
  const loop = (a, b, up, text) => {
    const x1 = xs[a] + bw / 2, x2 = xs[b] + bw / 2, yy = up ? y0 : y0 + bh, dy = up ? -90 : 90;
    const p = svgEl('path', {d: `M${x1} ${yy} C${x1} ${yy + dy} ${x2} ${yy + dy} ${x2} ${yy + (up ? -4 : 4)}`, class: 'g6-edge is-loop', 'marker-end': 'url(#g6-arrow)'});
    svg.append(p, svgEl('text', {x: (x1 + x2) / 2, y: yy + dy * 0.78 + (up ? -8 : 28), 'text-anchor': 'middle', class: 'g6-loop-label'}, text));
  };
  loop(3, 1, true, 'up to 2 rounds');
  loop(5, 4, false, '1 repair');
  boxes.forEach(([label, guard], i) => {
    const g = svgEl('g', {class: `g6-box${guard ? ' is-guard' : ''}`}); g.style.setProperty('--i', String(i));
    g.append(svgEl('rect', {x: xs[i], y: y0, width: bw, height: bh, rx: 12}));
    label.split('\n').forEach((line, k, all) => g.append(svgEl('text', {x: xs[i] + bw / 2, y: y0 + bh / 2 + 10 + (k - (all.length - 1) / 2) * 34, 'text-anchor': 'middle', class: 'g6-text'}, line)));
    svg.append(g);
  });
  const wrap = el('div', 'g6'); wrap.append(svg);
  const chips = el('ul', 'g6-chips');
  ['6 tool calls', '10 seconds per call', '1 retry', 'Three read-only tools: search reports, get a series, calculate a change'].forEach(t => chips.append(el('li', '', t)));
  wrap.append(chips);
  return wrap;
}

/** G7: question to cited answer, using the latest resident figure. */
export function evidenceTrace(m) {
  const card = m.cards.find(c => c.card_id === 'unemployment_resident_sa') || m.cards[0];
  if (!card) return null;
  const src = m.sources.find(r => r.source_id === card.source_id);
  const prev = previous(m, 'unemployment_resident_sa');
  const now = card.value;
  const wrap = el('ol', 'g7');
  let stepNo = 0;
  const step = (icon, head, body, cls = '') => { const li = el('li', `g7-step ${cls}`.trim()); li.style.setProperty('--i', String(stepNo++)); const t = el('div', 'g7-text'); t.append(el('p', 'g7-head', head), el('p', 'g7-body', body)); li.append(ico(icon), t); wrap.append(li); };
  step('question', 'Question', `What was resident unemployment in ${fmt.quarter(card.period)}, and how did it change?`);
  step('wrench', 'Tool call', `Get series: ${card.label.toLowerCase()}, ${fmt.quarter(card.period)}`);
  step('table', 'Row returned', `${pctS(now)}, seasonally adjusted, from ${src?.publisher || 'MOM'} via data.gov.sg`);
  step('calculator', 'Calculation, in code', finite(prev) ? `${pctS(now)} minus ${pctS(prev)} = ${fmt.signed(Math.round((now - prev) * 10) / 10, 1)} points` : 'Change not recorded');
  step('chat-text', 'Answer', `Resident unemployment was ${pctS(now)} in ${fmt.quarter(card.period)} [1].`);
  step('check-circle', 'Citation [1]', `${src?.publisher || 'MOM'}, ${card.label}. Quote found in the source.`, 'is-ok');
  return wrap;
}

/** G9: model cost and speed as bars. Prices are list prices read on 2026-10-30. */
export function costBars(m) {
  const models = [['gpt-6-luna', '$0.10 in, $0.50 out'], ['gpt-5.6-luna', '$0.20 in, $1.20 out'], ['gpt-4.1-mini', '$0.40 in, $1.60 out']];
  const rows = models.map(([name, price]) => ({name, price, x: m.evalRow('dev-A1', name)?.metrics})).filter(r => r.x);
  if (!rows.length) return null;
  const panel = (title, key, format) => {
    const max = Math.max(...rows.map(r => r.x[key]));
    const p = el('div', 'g9-panel'); p.append(el('h3', '', title));
    rows.forEach(r => {
      const line = el('div', 'g9-row');
      const lab = el('div', 'g9-lab'); lab.append(el('span', 'g9-name', r.name), el('span', 'g9-price', r.price));
      const track = el('div', 'g9-track'); const bar = el('div', 'g9-bar'); bar.style.setProperty('--w', `${Math.round((r.x[key] / max) * 100)}%`); track.append(bar);
      line.append(lab, track, el('span', 'g9-val num', format(r.x[key]))); p.append(line);
    });
    return p;
  };
  const wrap = el('div', 'g9');
  wrap.append(panel('Cost per question', 'cost_per_case_usd', v => `$${v.toFixed(4)}`), panel('Median seconds', 'latency_p50_s', v => `${v.toFixed(1)} s`));
  return wrap;
}
/** Caption for the cost slide, computed from the same runs. */
export function costCaption(m) {
  const a = metricOf(m.evalRow('dev-A1', 'gpt-6-luna')?.metrics?.behaviour_accuracy).rate;
  const rates = ['gpt-6-luna', 'gpt-5.6-luna', 'gpt-4.1-mini'].map(n => metricOf(m.evalRow('dev-A1', n)?.metrics?.behaviour_accuracy).rate).filter(finite);
  if (!finite(a) || !rates.length) return 'Cost per question, measured on development questions.';
  const gap = Math.max(...rates) - a;
  return gap <= 0 ? 'The cheapest model also scored highest.' : `The cheapest model cost least and scored within ${(gap * 100).toFixed(1)} points of the best.`;
}

/** G10: why the primary arm missed, grouped. */
export function errorBars(m) {
  const ea = m.section('evaluation').heldout_v2?.error_analysis;
  if (!ea) return null;
  const c = Object.fromEntries((ea.classes || []).map(x => [x.class, x.count]));
  const groups = [['Missing calculation tool', (c.tool_gap_text_figure_arithmetic || 0) + (c.tool_gap_dataset_dimension_label_and_round_budget || 0)], ['Chose to give no answer', c.answer_status_choice_non_answer || 0], ['Retrieval missed', c.retrieval_miss_both_arms || 0], ['Wrong reasoning', c.model_reasoning_false_premise || 0], ['Scorer or label wrong', (c.scorer_penalised_correct_answer || 0) + (c.gold_label_judged_wrong || 0)]];
  const max = Math.max(...groups.map(g => g[1]), 1);
  const wrap = el('div', 'g10');
  groups.forEach(([label, n]) => {
    const row = el('div', 'g9-row g10-row');
    const track = el('div', 'g9-track'); const bar = el('div', `g9-bar${n === max ? ' is-top' : ''}`); bar.style.setProperty('--w', `${Math.round((n / max) * 100)}%`); track.append(bar);
    row.append(el('span', 'g10-label', label), track, el('span', 'g9-val num', String(n)));
    wrap.append(row);
  });
  return wrap;
}

/** Before and after the calculation fix. Literals: the tool-set v2 results are not in the report data; the slide notes name their source. */
export function toolFixBars() {
  const wrap = el('div', 'g9 g11');
  const row = (name, note, value, max, text, kind) => {
    const line = el('div', 'g9-row');
    const lab = el('div', 'g9-lab'); lab.append(el('span', 'g9-name', name), el('span', 'g9-price', note));
    const track = el('div', 'g9-track'); const bar = el('div', `g9-bar is-${kind}`); bar.style.setProperty('--w', `${Math.round((value / max) * 100)}%`); track.append(bar);
    line.append(lab, track, el('span', 'g9-val num', text));
    return line;
  };
  const a = el('div', 'g9-panel'); a.append(el('h3', '', 'Practice questions'), el('p', 'g11-sub', 'Right kind of response'));
  [['Main model', .903, .895], ['Second model', .916, .899]].forEach(([name, before, after]) => {
    a.append(row(name, 'before', before, 1, `${(before * 100).toFixed(1)}%`, 'before'), row(name, 'with the fix', after, 1, `${(after * 100).toFixed(1)}%`, 'after'));
  });
  a.append(el('p', 'g11-foot', 'False answers: 6 before, 7 after. The test failed.'));
  const b = el('div', 'g9-panel'); b.append(el('h3', '', 'Fresh questions'), el('p', 'g11-sub', 'Number comparisons right, of 14'));
  b.append(row('Main model', 'before', 3, 14, '3', 'before'), row('Main model', 'with the fix', 12, 14, '12', 'after'));
  b.append(el('p', 'g11-foot', 'Optimistic: I designed the fix on these questions.'));
  wrap.append(a, b);
  return wrap;
}

/** Title slide: the product's answer, with its citation, from the latest figure. */
export function answerCard(m) {
  const card = m.cards.find(c => c.card_id === 'unemployment_resident_sa') || m.cards[0];
  const wrap = el('div', 'tcard');
  if (!card) return wrap;
  const src = m.sources.find(r => r.source_id === card.source_id);
  const head = el('div', 'tcard-head'); head.append(el('span', 'tcard-status', 'Answered'));
  wrap.append(head,
    el('p', 'tcard-q', `What was resident unemployment in ${fmt.quarter(card.period)}?`),
    el('p', 'tcard-a', `${pctS(card.value)}, resident, seasonally adjusted [1]`));
  const chip = el('p', 'tcard-cite'); chip.append(el('span', 'tcard-n', '1'), document.createTextNode(` ${src?.publisher || 'MOM'}, ${card.label}, via data.gov.sg`));
  wrap.append(chip);
  return wrap;
}

/** The MCP trust boundary: four boxes and a dashed line. */
export function mcpDiagram() {
  const W = 1560, H = 300, bw = 300, bh = 130, y0 = 90;
  const svg = svgEl('svg', {viewBox: `0 0 ${W} ${H}`, class: 'g6-svg', role: 'img', focusable: 'false'});
  svg.setAttribute('aria-label', 'Agent, MCP client, then a trust boundary, then MCP server and validated statistics.');
  const names = [['Agent', 'plans and answers'], ['MCP client', 'checks every result'], ['MCP server', 'read-only tools'], ['Statistics', 'validated data']];
  const gap = (W - 20 - bw * 4) / 3, xs = names.map((_, i) => 10 + i * (bw + gap));
  const defs = svgEl('defs'); const mk = svgEl('marker', {id: 'g6-arrow2', viewBox: '0 0 10 10', refX: 8, refY: 5, markerWidth: 9, markerHeight: 9, orient: 'auto'});
  mk.append(svgEl('path', {d: 'M0 0 10 5 0 10z', class: 'g6-head'})); defs.append(mk); svg.append(defs);
  for (let i = 0; i < 3; i += 1) svg.append(svgEl('line', {x1: xs[i] + bw, x2: xs[i + 1] - 4, y1: y0 + bh / 2, y2: y0 + bh / 2, class: 'g6-edge', 'marker-end': 'url(#g6-arrow2)'}));
  const bx = (xs[1] + bw + xs[2]) / 2;
  svg.append(svgEl('line', {x1: bx, x2: bx, y1: 20, y2: H - 10, class: 'g6-edge is-loop'}), svgEl('text', {x: bx, y: 14, 'text-anchor': 'middle', class: 'g6-loop-label'}, 'The server is untrusted'));
  names.forEach(([a, b], i) => {
    const g = svgEl('g', {class: `g6-box${i === 1 ? ' is-guard' : ''}`}); g.style.setProperty('--i', String(i));
    g.append(svgEl('rect', {x: xs[i], y: y0, width: bw, height: bh, rx: 12}), svgEl('text', {x: xs[i] + bw / 2, y: y0 + 56, 'text-anchor': 'middle', class: 'g6-text'}, a), svgEl('text', {x: xs[i] + bw / 2, y: y0 + 96, 'text-anchor': 'middle', class: 'g5-tag'}, b));
    svg.append(g);
  });
  const wrap = el('div', 'g6'); wrap.append(svg);
  return wrap;
}

/** The ten core requirements of the assignment: icon, plain name, what was asked. `status` adds where the talk showed it and what is still open. */
const REQUIREMENTS = [
  ['question', 'Framing', 'Users, scope, a simple baseline', 'The problem; How I measured', 'Protocol sign-off pending'],
  ['database', 'Data', 'Two source types, two findings', 'Choosing the data; What the data showed', 'Rights gaps remain'],
  ['magnifying-glass', 'Retrieval', 'Two retrievers, cited passages', 'Does filtering help?; Every claim has a source', 'Quotes not checked for meaning'],
  ['stack', 'Models', 'Two settings: quality, speed, cost', 'Choosing the model; The experiment ladder', 'Defaults await confirmation'],
  ['wrench', 'Agent', 'Tools, arithmetic in code, limits', 'The agent loop; Fixing the calculation gap', 'Report-text arithmetic gap'],
  ['chart-line', 'Evaluation', '30+ cases, human review, errors', 'How I measured; fresh questions', 'One reviewer only'],
  ['shield', 'Safety', 'Injection, privacy, least privilege', 'Safety tests; What protects it', 'Attack scanner is weak'],
  ['note', 'Concepts', 'Tokens, embeddings, agents, MCP', 'Across the talk', 'Rehearsal pending'],
  ['path', 'MCP', 'A tool, a resource, a client demo', 'The MCP server', 'Remote deployment unverified'],
  ['arrow-counter-clockwise', 'Setup', 'Pinned, tested, documented', 'Not shown in the talk', 'Clean-clone check recorded']
];
export function requirementGrid(status = false) {
  const wrap = el('div', `g12${status ? ' is-status' : ''}`);
  REQUIREMENTS.forEach(([icon, name, ask, shown, open], i) => {
    const tile = el('div', 'g12-tile'); tile.style.setProperty('--i', String(i));
    const head = el('div', 'g12-head'); head.append(ico(icon), el('h3', '', name));
    tile.append(head, el('p', 'g12-ask', ask));
    if (status) {
      const open_ = el('p', 'g12-open'); open_.append(ico('warning'), el('span', '', open));
      tile.append(el('p', 'g12-shown', shown), open_);
    }
    wrap.append(tile);
  });
  return wrap;
}

/** Three candidate domains and the reason recorded for the choice. */
export function domainChoice() {
  const wrap = el('div', 'g13');
  [['Labour market', 'Official quarterly data, reports and real revisions', true], ['Housing affordability', 'Confounded, transaction-level data', false], ['Cost of living', 'Index methods and causal complexity', false]].forEach(([name, why, chosen], i) => {
    const card = el('div', `g13-card${chosen ? ' is-chosen' : ''}`); card.style.setProperty('--i', String(i));
    const head = el('div', 'g13-head'); head.append(el('h3', '', name));
    if (chosen) head.append(ico('check-circle'));
    card.append(head, el('p', 'g13-why', why), el('p', 'g13-state', chosen ? 'Chosen' : 'Not chosen'));
    wrap.append(card);
  });
  return wrap;
}

/** Real difficulties from the record, each with one line on the response. */
export function challengeGrid() {
  const wrap = el('div', 'g14');
  [['Tables flattened in PDFs', 'Audited samples. Numbers were intact.'], ['Overall or resident, adjusted or not', 'Series names carry both. Ask when open.'], ['Advance and final figures differ', 'Every answer names its release.'], ['Rights limits on MOM content', 'Reports stay out of the public repository.'],
    ['Small reference set, AI drafted', 'I confirmed the labels. Intervals shown.'], ['Leakage between test sets', 'A fresh set from unseen sources.'], ['Calculation tool gap', 'Tested a fix. It failed its rule.'], ['Questions before 2024', 'It declines. Scope is fixed.']].forEach(([hard, did], i) => {
    const card = el('div', 'g14-card'); card.style.setProperty('--i', String(i));
    card.append(el('h3', '', hard), el('p', '', did));
    wrap.append(card);
  });
  return wrap;
}

/** The planted-figure test as three steps. */
export function plantedFlow() {
  const wrap = el('div', 'g14 g15');
  [['file-text', 'A false figure is planted', 'It sits in a report passage and looks like any other.'], ['warning', 'The agent cites it', 'The quote and the number both pass the checks.'], ['check-circle', 'The cross-check compares', 'It tests the figure against the statistics.']].forEach(([icon, head, line], i) => {
    const card = el('div', 'g14-card'); card.style.setProperty('--i', String(i));
    const top = el('div', 'g12-head'); top.append(ico(icon), el('h3', '', head));
    card.append(top, el('p', '', line));
    wrap.append(card);
  });
  return wrap;
}

/** A row of icon cards: [{icon, head, line}]. */
export function cardRow(items) {
  const wrap = el('div', 'g14 g15');
  items.forEach(({icon, head, line}, i) => {
    const card = el('div', 'g14-card'); card.style.setProperty('--i', String(i));
    const top = el('div', 'g12-head'); top.append(ico(icon), el('h3', '', head));
    card.append(top, el('p', '', line));
    wrap.append(card);
  });
  return wrap;
}

/** Panels of horizontal bars, grey for the baseline and accent for the variant. panel: {title, sub, rows: [{name, note, value, max, text, kind: 'before' | 'after'}], foot: [..]}. */
export function pairPanels(panels) {
  const wrap = el('div', 'g9 g11');
  panels.forEach(p => {
    const panel = el('div', 'g9-panel'); panel.append(el('h3', '', p.title));
    if (p.sub) panel.append(el('p', 'g11-sub', p.sub));
    p.rows.forEach(r => {
      const line = el('div', 'g9-row');
      const lab = el('div', 'g9-lab'); lab.append(el('span', 'g9-name', r.name), el('span', 'g9-price', r.note));
      const track = el('div', 'g9-track'); const bar = el('div', `g9-bar is-${r.kind}`); bar.style.setProperty('--w', `${Math.round((r.value / (r.max || 1)) * 100)}%`); track.append(bar);
      line.append(lab, track, el('span', 'g9-val num', r.text)); panel.append(line);
    });
    (p.foot || []).forEach(t => panel.append(el('p', 'g11-foot', t)));
    wrap.append(panel);
  });
  return wrap;
}

/** About me: the name, the one recorded fact, and what the talk covers. */
export function aboutMe() {
  const wrap = el('div', 'g16');
  const left = el('div', 'g16-left'); left.append(el('p', 'g16-name', 'Mihir Khandekar'), el('p', 'g16-line', 'Recent work: AI products in HR Tech.'));
  const list = el('ul', 'g16-list');
  [['wrench', 'What I built'], ['chart-line', 'How I measured it'], ['warning', 'What went wrong']].forEach(([icon, text], i) => {
    const li = el('li', 'g16-item'); li.style.setProperty('--i', String(i)); li.append(ico(icon), el('span', '', text)); list.append(li);
  });
  wrap.append(left, list);
  return wrap;
}

/** The system end to end: five stages and two checks that run across them. */
export function architectureDiagram() {
  const wrap = el('div', 'g17');
  const stages = [['database', 'Sources', ['Statistics from data.gov.sg', 'MOM reports, PDF and web']], ['file-text', 'Processing', ['Parse and clean', 'Split into passages', 'Validate the numbers']], ['magnifying-glass', 'Retrieval', ['Keyword and meaning', 'Filter by period', 'Rerank']], ['wrench', 'Agent', ['Plan the steps', 'Three read-only tools', 'Arithmetic in code']], ['check-circle', 'Answer', ['Every claim cited', 'Or ask, decline, refuse']]];
  const row = el('div', 'g17-row');
  stages.forEach(([icon, name, lines], i) => {
    if (i) { const arrow = el('div', 'g17-arrow'); arrow.append(ico('arrow-right')); row.append(arrow); }
    const box = el('div', 'g17-stage'); box.style.setProperty('--i', String(i));
    const head = el('div', 'g12-head'); head.append(ico(icon), el('h3', '', name));
    const ul = el('ul'); lines.forEach(t => ul.append(el('li', '', t)));
    box.append(head, ul); row.append(box);
  });
  const bars = el('div', 'g17-bars');
  [['shield', 'Guardrails', 'Retrieved text is data. Tools are read-only. Hard limits.'], ['chart-line', 'Evaluation', 'Reference questions, fresh sets and attack tests.']].forEach(([icon, name, text]) => {
    const bar = el('div', 'g17-bar'); bar.append(ico(icon), el('strong', '', name), el('span', '', text)); bars.append(bar);
  });
  wrap.append(row, bars);
  return wrap;
}

/** The task as set, and the sources and topics I left out, with the recorded reason. */
export function taskAndLeftOut() {
  const wrap = el('div', 'g18');
  const task = el('div', 'g18-panel is-task'); task.append(el('h3', '', 'The task'));
  const tl = el('dl', 'g18-dl');
  [['Who asks', 'Policy researchers and analysts'], ['What they ask', 'Facts, changes, comparisons, revisions, vague and hostile questions'], ['How far', 'Q1 2024 to Q2 2026'], ['Not covered', 'Forecasts, causes, personal advice']].forEach(([k, v]) => { tl.append(el('dt', '', k), el('dd', '', v)); });
  task.append(tl);
  const out = el('div', 'g18-panel'); out.append(el('h3', '', 'What I left out'));
  const ul = el('ul', 'g18-out');
  [['Housing, cost of living', 'Confounded, or heavy index methods'], ['Foreign workforce data', 'Stale: last updated June 2024'], ['GDP revision pairs', 'Not labour evidence'], ['Other ministry pages', 'No verified report links']].forEach(([k, v]) => { const li = el('li'); li.append(el('strong', '', k), el('span', '', v)); ul.append(li); });
  out.append(ul);
  wrap.append(task, out);
  return wrap;
}

/** What each finding about the data made hard, and the part of the system that handles it. */
export function hardParts() {
  const wrap = el('div', 'g19');
  [['Four unemployment rates', 'Typed series, or a question back'], ['A rise with no stated cause', 'Cite MOM commentary, or decline'], ['Advance and final differ', 'Release-aware search, conflict explained'], ['Tables flattened in PDFs', 'The quote must appear in the passage'], ['Ratio does not recompute', 'Quote the published ratio'], ['Figures before 2024', 'A scope guard declines']].forEach(([hard, fix], i) => {
    const row = el('div', 'g19-row'); row.style.setProperty('--i', String(i));
    const arrow = el('span', 'g19-arrow'); arrow.append(ico('arrow-right'));
    row.append(el('p', 'g19-hard', hard), arrow, el('p', 'g19-fix', fix));
    wrap.append(row);
  });
  return wrap;
}

/** Early retrieval comparison on 24 development questions: keyword, meaning, both. */
export function keywordVsMeaning(m) {
  const hit = name => m.retrievalRow('dev-dense-E6', name)?.metrics?.['hit@10'];
  const items = [['merge120 bm25', 'Keyword', 'plain'], ['merge120 dense', 'Meaning', 'plain'], ['merge120 hybrid-rrf', 'Both together', 'accent']].map(([k, label, kind]) => ({label, value: hit(k), kind})).filter(i => finite(i.value));
  return items.length === 3 ? staircase(items, {domain: [0, 1]}) : null;
}

/** Models: price, quality, cost and speed in one table. Prices are list prices read on 2026-10-30. */
export function modelTable(m) {
  const wrap = el('div', 'g20');
  const table = el('table', 'g20-table');
  const head = el('tr'); ['Model', 'Price per 1M tokens', 'Right kind of response', 'Cost per question', 'Median seconds', 'Final setup, cost'].forEach(t => { const th = el('th', '', t); th.scope = 'col'; head.append(th); });
  const thead = el('thead'); thead.append(head);
  const tbody = el('tbody');
  [['gpt-6-luna', '$0.10 in, $0.50 out', true], ['gpt-5.6-luna', '$0.20 in, $1.20 out', false], ['gpt-4.1-mini', '$0.40 in, $1.60 out', false]].forEach(([name, price, picked]) => {
    const a1 = m.evalRow('dev-A1', name)?.metrics, a3 = m.evalRow('dev-A3', name)?.metrics;
    const tr = el('tr', picked ? 'is-pick' : '');
    const cell = text => el('td', 'num', text);
    const th = el('th', '', name); th.scope = 'row';
    tr.append(th, el('td', '', price), cell(a1 ? fmt.pct(metricOf(a1.behaviour_accuracy).rate) : 'n/a'), cell(a1 ? `$${a1.cost_per_case_usd.toFixed(4)}` : 'n/a'), cell(a1 ? `${a1.latency_p50_s.toFixed(1)} s` : 'n/a'), cell(a3 ? `$${a3.cost_per_case_usd.toFixed(4)}` : 'not run'));
    tbody.append(tr);
  });
  table.append(thead, tbody);
  wrap.append(table, el('p', 'g20-foot', 'Judge: gpt-6.1-terra, $1.00 in, $5.00 out. Embeddings: text-embedding-3-large, $0.13. Not run: gpt-6-astra, $10 in, $50 out.'));
  return wrap;
}

/** Registered held-out set and the second fresh set, main model, baseline against filter then rerank. */
export function freshQuestions(m) {
  const hybrid = metricOf(m.heldRow('hybrid', 'gpt-6-luna')?.metrics?.behaviour_accuracy).rate, r3 = metricOf(m.heldRow('r3', 'gpt-6-luna')?.metrics?.behaviour_accuracy).rate;
  const v2 = m.section('evaluation').heldout_v2?.paired?.['gpt-6-luna'], pair = m.paired[0]?.models?.['gpt-6-luna'];
  if (![hybrid, r3].every(finite) || !v2) return null;
  const row = (name, note, value, kind) => ({name, note, value, max: 1, text: fmt.pct(value), kind});
  return pairPanels([
    {title: '31 test questions', sub: 'Main model, right kind of response', rows: [row('Baseline search', 'before', hybrid, 'before'), row('Filter, then rerank', 'after', r3, 'after')], foot: [pair ? `Gain ${fmt.pts(pair.diff)}, interval ${fmt.pts(pair.ci95[0])} to ${fmt.pts(pair.ci95[1])}.` : '']},
    {title: '65 fresh questions', sub: 'Main model, right kind of response', rows: [row('Baseline search', 'before', v2.behaviour_accuracy.baseline, 'before'), row('Filter, then rerank', 'after', v2.behaviour_accuracy.candidate, 'after')], foot: [`${v2.better} cases better, ${v2.worse} worse.`]}
  ]);
}

/** The 403 labelling items by stream, as one segmented bar. Counts come from the review inventory, not the report data. */
export function reviewStreams() {
  const wrap = el('div', 'g21');
  const big = el('div', 'g21-big'); big.append(el('p', 'g21-num num', '403'), el('p', 'g21-label', 'decisions recorded in the review interface'));
  const right = el('div', 'g21-right');
  const bar = el('div', 'g21-bar');
  const legend = el('ul', 'g21-legend');
  [['Reference questions', 268, 'c1'], ['Fresh-set questions', 65, 'c3'], ['Saved answers', 40, 'c2'], ['Source checks', 30, 'c5']].forEach(([name, n, cls]) => {
    const seg = el('div', `g21-seg f-${cls}`); seg.style.setProperty('--w', String(n)); bar.append(seg);
    const li = el('li'); const sw = el('span', `g21-sw f-${cls}`); li.append(sw, el('span', 'g21-name', name), el('span', 'g21-n num', String(n))); legend.append(li);
  });
  right.append(bar, legend);
  wrap.append(big, right);
  return wrap;
}

/** Threat results, undefended against defended, from the registered and the final runs. */
export function threatPanels(m) {
  const n = (reg, name) => (reg ? m.securityRow(name) : m.e2efixRow(name))?.metrics?.passed;
  const row = (name, note, v, kind) => ({name, note, value: v, max: 36, text: `${v} of 36`, kind});
  const pairRows = (reg, model, label) => { const a = n(reg, `${model}+naive`), b = n(reg, model); return finite(a) && finite(b) ? [row(label, 'no defences', a, 'before'), row(label, 'defences', b, 'after')] : []; };
  const first = [...pairRows(true, 'gpt-6-luna', 'Main model'), ...pairRows(true, 'gpt-4.1-mini', 'Smaller model')];
  const last = [...pairRows(false, 'gpt-6-luna', 'Main model'), ...pairRows(false, 'gpt-5.6-luna', 'Second model')];
  if (!first.length || !last.length) return null;
  return pairPanels([{title: 'First attack run', sub: '36 attack cases', rows: first, foot: ['The scanner missed all 5 paraphrased probes.']}, {title: 'Final system', sub: '36 attack cases', rows: last, foot: ['One planted false figure is still not shown stable.']}]);
}

/** A screenshot of the workbench, served from this site. */
export function workbenchShot() {
  const wrap = el('div', 'g22');
  const img = el('img', 'g22-img'); img.src = '/static/presentation/workbench.png'; img.alt = 'The LabourLens workbench: a question box, example questions, session history and an activity timeline.'; img.width = 1500; img.height = 900;
  wrap.append(img);
  return wrap;
}

/** GenAI concepts and where this build uses each one. */
export function conceptGrid() {
  const wrap = el('div', 'g12 is-concepts');
  [['stack', 'Tokens and context', 'Questions capped at 1,000 characters. Answers capped at 6,000 output tokens.'], ['database', 'Embeddings', 'text-embedding-3-large, with keyword search beside it.'], ['arrows-in-simple', 'Reranking', 'A model reorders the top 30 passages.'], ['note', 'Prompts', 'Versioned planner and answer prompts. Strict JSON output, validated.'], ['chart-line', 'Evaluators', 'Code scores numbers. An AI judge scores claim support.'], ['wrench', 'Agents', 'One bounded loop. Six tool calls at most.'], ['path', 'MCP', 'Nine read-only tools and two resources, behind a client that distrusts them.'], ['clock', 'Observability', 'A record per run: outcome, tool calls, cost and timings.']].forEach(([icon, name, text], i) => {
    const tile = el('div', 'g12-tile'); tile.style.setProperty('--i', String(i));
    const head = el('div', 'g12-head'); head.append(ico(icon), el('h3', '', name));
    tile.append(head, el('p', 'g12-ask', text));
    wrap.append(tile);
  });
  return wrap;
}

/** The seven assessment areas by weight, where the talk covers each, and what is still open (from the requirement matrix). */
export function coverageMap() {
  const wrap = el('div', 'g23');
  [['Evaluation and error analysis', 25, 'How I measured, results, errors, review', 'One reviewer, mostly quick confirmations'], ['RAG and GenAI design', 20, 'Retrieval, citations, models', 'Quotes checked for presence, not meaning'], ['GenAI concepts and MCP', 15, 'Concepts, the MCP server', 'Rehearsal pending; the app does not route through MCP'], ['Problem framing and data', 10, 'Problem, data, what it showed', 'Rights gaps remain'], ['Agent workflow', 10, 'The loop, the calculation fix', 'Report-text arithmetic gap'], ['Responsible AI', 10, 'Attacks and defences', 'Weak scanner; one case not stable'], ['Reproducibility and communication', 10, 'The product, how to run it', 'Fresh-checkout run pending']].forEach(([area, weight, where, open], i) => {
    const row = el('div', 'g23-row'); row.style.setProperty('--i', String(i));
    const bar = el('div', 'g23-bar'); const fill = el('span', 'g23-fill'); fill.style.setProperty('--w', `${Math.round(weight / 25 * 100)}%`); bar.append(fill, el('span', 'g23-w num', `${weight}%`));
    const gap = el('p', 'g23-open'); gap.append(ico('warning'), el('span', '', open));
    row.append(el('p', 'g23-area', area), bar, el('p', 'g23-where', where), gap);
    wrap.append(row);
  });
  return wrap;
}

/** Three review measures. Counts come from the review inventory and the sets used in the report. */
export function measureCards(m) {
  const dev = m.evalRow('dev-A3', 'gpt-6-luna')?.metrics?.n_cases, held = m.heldRow('r3', 'gpt-6-luna')?.metrics?.n_cases, v2 = m.section('evaluation').heldout_v2?.paired?.['gpt-6-luna']?.n_gold_cases;
  return cardRow([{icon: 'stack', head: 'Three question sets', line: `${fmt.int(dev)} to tune on, ${fmt.int(held)} for testing, ${fmt.int(v2)} fresh.`}, {icon: 'chart-line', head: 'Four measures', line: 'Right passage, right response, supported claims, correct numbers.'}, {icon: 'check-circle', head: 'One reviewer', line: 'AI drafted the labels. I confirmed all 403 items. Not independent.'}]);
}

/** The development loop with the written guardrails around it, and three counts: the decision log, five end-to-end reviewers, the rights scan result. */
export function buildProcess() {
  const wrap = el('div', 'g24');
  const loop = el('div', 'g24-loop');
  ['Propose', 'Compare', 'Approve', 'Build', 'Verify', 'Record'].forEach((name, i) => {
    if (i) { const a = el('span', 'g24-arrow'); a.append(ico('arrow-right')); loop.append(a); }
    const step = el('div', `g24-step${name === 'Approve' ? ' is-owner' : ''}`); step.style.setProperty('--i', String(i));
    step.append(el('p', 'g24-name', name), el('p', 'g24-who', name === 'Approve' ? 'Me' : name === 'Record' ? 'Files' : 'Agent'));
    loop.append(step);
  });
  const lanes = el('ul', 'g24-lanes');
  [['Written contract', 'Options and trade-offs first. No next phase without my approval.'], ['State in files', 'Progress log, claims and decision log, so any agent can resume.'], ['Frozen results', 'Hashes pinned. Post-freeze work gets a new experiment id.'], ['Independent review', 'Blind AI reviewers. Five end-to-end reviews found real defects.'], ['Safe by default', 'Secrets in a gitignored file. Rights scan and secret scan in CI.']].forEach(([head, text], i) => {
    const li = el('li', 'g24-lane'); li.style.setProperty('--i', String(i)); li.append(el('strong', '', head), el('span', '', text)); lanes.append(li);
  });
  const nums = el('div', 'g24-nums');
  [['49', 'decisions logged'], ['5', 'independent reviewers'], ['0', 'rights-scan hits']].forEach(([n, label]) => { const d = el('div', 'g24-num'); d.append(el('p', 'num', n), el('p', '', label)); nums.append(d); });
  wrap.append(loop, el('div', 'g24-body', ''), nums);
  wrap.querySelector('.g24-body').append(lanes);
  return wrap;
}
