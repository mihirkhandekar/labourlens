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
    const card = el('div', 'g1-card fragment');
    card.dataset.fragmentIndex = String(i);
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
    const n = el('div', 'g3-node fragment');
    n.dataset.fragmentIndex = String(i);
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
  const step = (icon, head, body, cls = '') => { const li = el('li', `g7-step fragment ${cls}`.trim()); const t = el('div', 'g7-text'); t.append(el('p', 'g7-head', head), el('p', 'g7-body', body)); li.append(ico(icon), t); wrap.append(li); };
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
  ['arrow-counter-clockwise', 'Setup', 'Pinned, tested, documented', 'Not shown in the talk', 'Fresh-checkout run pending']
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
    ['Small reference set, AI drafted', 'I reviewed every item. Intervals shown.'], ['Leakage between test sets', 'A fresh set from unseen sources.'], ['Calculation tool gap', 'Tested a fix. It failed its rule.'], ['Questions before 2024', 'It declines. Scope is fixed.']].forEach(([hard, did], i) => {
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
