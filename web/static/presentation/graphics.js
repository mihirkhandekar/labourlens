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
    block('table', 'Structured: statistics', types.dataset_csv, 'snapshots', ['Unemployment rate', 'Vacancies per unemployed person', 'Retrenchments', 'Employment change by sector', 'Transport and storage jobs']),
    el('div', 'g2-join'),
    block('file-text', 'Unstructured: reports', types.report_pdf, 'PDFs', [`${fmt.int(types.release_html)} release pages`, 'MOM labour market reports', 'MTI AI-and-employment article'])
  );
  wrap.querySelector('.g2-join').append(el('span', 'g2-plus', '+'));
  return wrap;
}

/** G3: the current document build first, then the two earlier builds in a plain table. Passage counts are recorded in the README and the decision log, not in report.json. */
export function buildTimeline() {
  const wrap = el('div', 'g3b');
  wrap.append(el('p', 'g3b-lead', 'The system, the live site and the final held-out test all use the current document build: 85 sources, 16,419 passages. Two earlier builds are kept only so older results can be reproduced.'));
  const table = el('table', 'g3b-table');
  const head = el('tr'); ['Build', 'Passages', 'What it was for'].forEach(h => head.append(el('th', '', h))); table.append(el('thead', '', '')); table.lastChild.append(head);
  const body = el('tbody');
  [['Earlier build (v1)', 13484, 'First experiments and the original held-out test. Results frozen.'], ['Middle build (v2)', 15915, 'Extraction fixes tested alone. No measurable change.'], ['Current build (v3)', 16419, 'Adds six untouched sources, so the 65-question held-out set shares no evidence with development.']].forEach(([name, count, why], i) => {
    const tr = el('tr', i === 2 ? 'is-current' : ''); tr.append(el('th', '', name), el('td', 'num', fmt.int(count)), el('td', '', why)); body.append(tr);
  });
  table.append(body); wrap.append(table);
  wrap.append(el('p', 'g3b-note', 'Which numbers come from which build: development accuracy 0.903 appears on the earlier build (first experiments) and on the current build (regression check); held-out v2 0.754 is on the current build. Do not compare numbers across builds.'));
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
  const tagged = items.some(i => i.tag);
  const W = 1500, H = tagged ? 640 : 560, top = 60, bottom = tagged ? 200 : 120, left = 40, gap = 36;
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

/** Before and after the calculation fix. Values are development and diagnostic results. */
export function toolFixBars() {
  const wrap = el('div', 'g9 g11');
  const row = (name, note, value, max, text, kind) => {
    const line = el('div', 'g9-row');
    const lab = el('div', 'g9-lab'); lab.append(el('span', 'g9-name', name), el('span', 'g9-price', note));
    const track = el('div', 'g9-track'); const bar = el('div', `g9-bar is-${kind}`); bar.style.setProperty('--w', `${Math.round((value / max) * 100)}%`); track.append(bar);
    line.append(lab, track, el('span', 'g9-val num', text));
    return line;
  };
  const a = el('div', 'g9-panel'); a.append(el('h3', '', 'Development cases'), el('p', 'g11-sub', 'Behaviour accuracy, n=237'));
  [['gpt-6-luna', .903, .895], ['gpt-5.6-luna', .916, .899]].forEach(([name, before, after]) => {
    a.append(row(name, 'before', before, 1, `${(before * 100).toFixed(1)}%`, 'before'), row(name, 'with tool bundle', after, 1, `${(after * 100).toFixed(1)}%`, 'after'));
  });
  a.append(el('p', 'g11-foot', 'False answers: 6 before, 7 after, limit 6. Criteria failed; not adopted.'));
  const b = el('div', 'g9-panel'); b.append(el('h3', '', 'Same 65 questions, reused'), el('p', 'g11-sub', 'Correct number comparisons, of 14; not fresh'));
  b.append(row('gpt-6-luna', 'before', 3, 14, '3', 'before'), row('gpt-6-luna', 'with tool bundle', 12, 14, '12', 'after'));
  b.append(el('p', 'g11-foot', 'Optimistic: the fix was designed on these questions.'));
  wrap.append(a, b);
  return wrap;
}
/** The calculation fix: planner evidence, new calculator, dimension recovery and bonus round. */
export function toolFixFlow() {
  const wrap = el('div', 'g11');
  wrap.style.setProperty('display', 'grid');
  wrap.style.setProperty('grid-template-rows', 'auto minmax(0, 1fr)');
  wrap.style.setProperty('gap', '12px');
  wrap.style.setProperty('height', '100%');
  const flow = el('div', 'g14 is-compact');
  flow.style.setProperty('height', 'auto');
  flow.style.setProperty('grid-template-columns', 'repeat(4, minmax(0, 1fr))');
  [['Planner evidence', 'Up to five short figure snippets per passage.'], ['New calculation', 'Decimal arithmetic on two compatible figures.'], ['Dimension recovery', 'Return valid labels after a mismatch.'], ['Bonus round', 'One extra lookup after correction.']].forEach(([head, body], i) => {
    const card = el('div', 'g14-card'); card.style.setProperty('--i', String(i));
    card.append(el('h3', '', head), el('p', '', body)); flow.append(card);
  });
  wrap.append(flow, toolFixBars());
  return wrap;
}

/** The MCP trust boundary: four boxes and a dashed line. */
export function mcpDiagram() {
  const W = 1560, H = 300, bw = 300, bh = 130, y0 = 90;
  const svg = svgEl('svg', {viewBox: `0 0 ${W} ${H}`, class: 'g6-svg', role: 'img', focusable: 'false'});
  svg.setAttribute('aria-label', 'Host application uses an MCP client to validate calls and results from an MCP server with read-only tools and resources, backed by statistics.');
  const names = [['Host app', 'live app: direct calls'], ['MCP client', 'checks every result'], ['MCP server', '9 tools, 2 resources'], ['Statistics', 'read-only data']];
  const gap = (W - 20 - bw * 4) / 3, xs = names.map((_, i) => 10 + i * (bw + gap));
  const defs = svgEl('defs'); const mk = svgEl('marker', {id: 'g6-arrow2', viewBox: '0 0 10 10', refX: 8, refY: 5, markerWidth: 9, markerHeight: 9, orient: 'auto'});
  mk.append(svgEl('path', {d: 'M0 0 10 5 0 10z', class: 'g6-head'})); defs.append(mk); svg.append(defs);
  for (let i = 0; i < 3; i += 1) svg.append(svgEl('line', {x1: xs[i] + bw, x2: xs[i + 1] - 4, y1: y0 + bh / 2, y2: y0 + bh / 2, class: 'g6-edge', 'marker-end': 'url(#g6-arrow2)'}));
  const bx = (xs[1] + bw + xs[2]) / 2;
  svg.append(svgEl('line', {x1: bx, x2: bx, y1: 20, y2: H - 10, class: 'g6-edge is-loop'}), svgEl('text', {x: bx, y: 14, 'text-anchor': 'middle', class: 'g6-loop-label'}, 'Optional MCP trust boundary'));
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
  ['chart-line', 'Evaluation', '30+ cases, human review, errors', 'How I measured; fresh questions', 'One human reviewer'],
  ['shield', 'Safety', 'Injection, privacy, least privilege', 'Safety tests; What protects it', 'Attack scanner is weak'],
  ['note', 'Concepts', 'Tokens, embeddings, agents, MCP', 'Across the talk', 'Rehearsal pending'],
  ['path', 'MCP', 'A tool, a resource, a client demo', 'The MCP server', 'Remote deployment unverified'],
  ['arrow-counter-clockwise', 'Setup', 'Pinned, tested, documented', 'Not shown in the talk', 'Clean-clone check recorded']
];
/** The assignment as two plain columns: the problem statement in my words, and the ten asks as a ruled list. */
export function assignmentBrief() {
  const wrap = el('div', 'ab');
  const statement = el('div', 'ab-col'); statement.append(el('h3', '', 'The problem statement'));
  ['Policy researchers work with government statistics, reports and internal notes that can be incomplete, inconsistent or hard to search.',
    'Build a GenAI assistant that answers analytical questions from supplied or public data, gives traceable evidence for each answer, and says plainly when it is uncertain.',
    'The brief puts applied machine learning, experiments, retrieval quality, evaluation and responsible AI ahead of full-stack engineering.'].forEach(t => statement.append(el('p', 'ab-text', t)));
  const asks = el('div', 'ab-col'); asks.append(el('h3', '', 'What it asked for'));
  const list = el('ul', 'ab-list');
  REQUIREMENTS.forEach(([, name, ask]) => { const li = el('li', ''); li.append(el('strong', '', name), el('span', '', ask)); list.append(li); });
  asks.append(list);
  wrap.append(statement, asks);
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
    ['Small reference set, AI drafted', 'I signed off the labels. Intervals shown.'], ['Leakage between test sets', 'A fresh set from unseen sources.'], ['Calculation tool gap', 'Tested a fix. It failed its rule.'], ['Questions before 2024', 'It declines. Scope is fixed.']].forEach(([hard, did], i) => {
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
  if (items.length === 4) wrap.style.setProperty('grid-template-columns', 'repeat(4, minmax(0, 1fr))');
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

/** The system and its two cross-cutting checks plus the optional MCP route. */
export function architectureDiagram() {
  const wrap = el('div', 'g17');
  const stages = [['database', 'Sources', ['Quarterly statistics', 'MOM reports and an MTI article']], ['file-text', 'Processing', ['Parse and clean', 'Create passages', 'Validate observations']], ['magnifying-glass', 'Retrieval', ['BM25 and embeddings', 'Filter period/release', 'Rerank candidates']], ['wrench', 'Agent', ['Plan and assess evidence', 'Three typed tools', 'Calculate in code']], ['check-circle', 'Answer', ['Cited, validated output', 'Or clarify, decline, refuse']]];
  const row = el('div', 'g17-row');
  stages.forEach(([icon, name, lines], i) => {
    if (i) { const arrow = el('div', 'g17-arrow'); arrow.append(ico('arrow-right')); row.append(arrow); }
    const box = el('div', 'g17-stage'); box.style.setProperty('--i', String(i));
    const head = el('div', 'g12-head'); head.append(ico(icon), el('h3', '', name));
    const ul = el('ul'); lines.forEach(t => ul.append(el('li', '', t)));
    box.append(head, ul); row.append(box);
  });
  const bars = el('div', 'g17-bars');
  bars.style.setProperty('grid-template-columns', 'repeat(3, minmax(0, 1fr))');
  [['shield', 'Guardrails', 'Retrieved text is untrusted. Tools are read-only; calls are bounded.'], ['chart-line', 'Evaluation', 'Development and fresh cases, human review and attack tests.'], ['path', 'MCP', 'Optional client validates server tools/resources. Web app calls the same tools directly.']].forEach(([icon, name, text]) => {
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


/** Early answer-model screening: G1 cost per case against behaviour accuracy, n=30. */
export function earlyModelChart() {
  const data = [
    ['gpt-4.1-mini', 0.00161, 0.83], ['gpt-5.4-mini', 0.00335, 0.70],
    ['gpt-5.6-luna', 0.00113, 0.73], ['gpt-6-luna', 0.00051, 0.60],
    ['gpt-6-sol', 0.00912, 0.60], ['gpt-6.1-terra', 0.00432, 0.57]
  ];
  const W = 1500, H = 600, left = 140, right = 80, top = 75, bottom = 115;
  const svg = svgEl('svg', {viewBox: `0 0 ${W} ${H}`, class: 'g5-svg', role: 'img', focusable: 'false'});
  svg.setAttribute('aria-label', 'Six-model exploratory chart: per-case cost on the horizontal axis and behaviour accuracy on the vertical axis, from 30 development cases.');
  const x = cost => left + cost / 0.01 * (W - left - right);
  const y = accuracy => top + (0.9 - accuracy) / 0.4 * (H - top - bottom);
  svg.append(svgEl('line', {x1: left, x2: W - right, y1: H - bottom, y2: H - bottom, class: 'g5-axis'}),
    svgEl('line', {x1: left, x2: left, y1: top, y2: H - bottom, class: 'g5-axis'}),
    svgEl('text', {x: (left + W - right) / 2, y: H - 22, 'text-anchor': 'middle', class: 'g5-label'}, 'Cost per case (USD)'),
    svgEl('text', {x: 24, y: 42, class: 'g5-label'}, 'Behaviour accuracy'));
  data.forEach(([name, cost, accuracy], i) => {
    const g = svgEl('g', {class: `g5-step${name === 'gpt-6-luna' ? ' is-accent' : ' is-plain'}`});
    g.style.setProperty('--i', String(i));
    g.append(svgEl('circle', {cx: x(cost), cy: y(accuracy), r: 16, class: 'g5-bar'}),
      svgEl('text', {x: x(cost) + 22, y: y(accuracy) - 10, class: 'g5-label'}, name),
      svgEl('text', {x: x(cost) + 22, y: y(accuracy) + 24, class: 'g5-tag'}, `${fmt.pct(accuracy)} · $${cost.toFixed(5)}`));
    svg.append(g);
  });
  return svg;
}

/** Registered held-out set and the second fresh set, main model, baseline against filter then rerank. */
export function freshQuestions(m) {
  const hybrid = metricOf(m.heldRow('hybrid', 'gpt-6-luna')?.metrics?.behaviour_accuracy).rate, r3 = metricOf(m.heldRow('r3', 'gpt-6-luna')?.metrics?.behaviour_accuracy).rate;
  const v2 = m.section('evaluation').heldout_v2?.paired?.['gpt-6-luna'], pair = m.paired[0]?.models?.['gpt-6-luna'];
  if (![hybrid, r3].every(finite) || !v2) return null;
  const row = (name, note, value, kind) => ({name, note, value, max: 1, text: fmt.pct(value), kind});
  return pairPanels([
    {title: '31 original test questions', sub: 'Primary gpt-6-luna; behaviour accuracy', rows: [row('Baseline search', 'before', hybrid, 'before'), row('Filter, then rerank', 'after', r3, 'after')], foot: [pair ? `Gain ${fmt.pts(pair.diff)}, interval ${fmt.pts(pair.ci95[0])} to ${fmt.pts(pair.ci95[1])}.` : '']},
    {title: '65 fresh questions', sub: 'Primary gpt-6-luna; behaviour accuracy', rows: [row('Baseline search', 'before', v2.behaviour_accuracy.baseline, 'before'), row('Filter, then rerank', 'after', v2.behaviour_accuracy.candidate, 'after')], foot: [`${v2.better} cases better, ${v2.worse} worse.`]}
  ]);
}

/** The four separate review streams as a plain ruled list. Counts come from the review inventory, not the report data. */
export function reviewStreams() {
  const wrap = el('div', 'g21 is-list');
  const list = el('ul', 'g21-rows');
  [['Gold questions', 268, '237 development and 31 original test; the 31 share evidence with development. Decisions: approve, change or reject.'],
    ['Fresh-set (v2) questions', 65, 'Written on six sources no earlier question uses. Decisions: approve, change or reject.'],
    ['Saved system answers', 40, 'Not questions. Rated right, partly right or wrong: 25, 6 and 9.'],
    ['Source checks', 30, 'Not questions. Checked against the original pages: match, minor difference or major difference. 18 match, 12 minor.']].forEach(([name, n, what], i) => {
    const li = el('li', 'g21-row'); li.style.setProperty('--i', String(i));
    const head = el('div', 'g21-rowhead'); head.append(el('span', 'g21-name', name), el('span', 'g21-n num', String(n)));
    li.append(head, el('p', 'g21-what', what)); list.append(li);
  });
  wrap.append(list, el('p', 'g21-total', 'Only the first two are questions. 403 items signed off in total, in four separate streams.'));
  return wrap;
}


/** Attack, defence and result from the final 36-case threat report, as a flow per attack: attack, the control it meets, and one segment per case (filled when the primary model passed). */
export function threatMatrix() {
  const wrap = el('div', 'tm');
  const head = el('div', 'tm-row tm-head'); head.append(el('span', '', 'Attack'), el('span', '', 'Defence it meets'), el('span', '', 'Cases passed by gpt-6-luna'));
  wrap.append(head);
  const rows = [
    ['Question injection and secret requests', 'Input flags; secret and prompt output checks', 6, 6, ''],
    ['Injection or false figure in a passage', 'Untrusted evidence cannot set instructions; figures cross-checked against statistics', 6, 6, 'gpt-5.6-luna 5/6, planted figure'],
    ['Sensitive data, credentials, PII', 'Refusal; no personal-data tool exists', 5, 5, ''],
    ['Unsupported or causal claim', 'Answer from cited evidence or decline', 4, 4, ''],
    ['Unsafe tool use', 'Typed read-only tools, argument and call caps', 5, 5, ''],
    ['Malicious or malformed MCP output', 'Allow-list, schema checks, size and time caps', 10, 10, ''],
    ['Paraphrased injection', 'Keyword scanner plus untrusted-text rules', 0, 5, 'scanner probes, outside the 36: missed all five']
  ];
  rows.forEach(([attack, defence, passed, total, note], i) => {
    const row = el('div', 'tm-row'); row.style.setProperty('--i', String(i));
    const seg = el('div', 'tm-seg'); seg.setAttribute('role', 'img'); seg.setAttribute('aria-label', `${passed} of ${total} passed${note ? `; ${note}` : ''}`);
    for (let k = 0; k < total; k += 1) seg.append(el('i', k < passed ? 'is-pass' : 'is-miss'));
    const res = el('div', 'tm-res'); res.append(seg, el('span', 'tm-count num', `${passed}/${total}`));
    if (note) res.append(el('span', 'tm-note', note));
    row.append(el('span', 'tm-attack', attack), el('span', 'tm-def', defence), res);
    wrap.append(row);
  });
  return wrap;
}

/** A screenshot and scannable link to the workbench, served locally. */
export function workbenchShot() {
  const wrap = el('div', 'g22');
  wrap.style.setProperty('grid-template-columns', 'minmax(0, 1fr) auto');
  wrap.style.setProperty('gap', '24px');
  const img = el('img', 'g22-img'); img.src = '/static/presentation/workbench.png'; img.alt = 'The LabourLens workbench: a question box, example questions, session history and an activity timeline.'; img.width = 1500; img.height = 900;
  const link = el('a', 'g22-link'); link.href = 'https://labourlens.navig.me/workbench'; link.setAttribute('aria-label', 'Try the workbench at labourlens.navig.me');
  link.style.setProperty('display', 'grid'); link.style.setProperty('justify-items', 'center'); link.style.setProperty('gap', '12px');
  link.style.setProperty('color', 'var(--accent)'); link.style.setProperty('text-decoration', 'none');
  const qr = el('img', 'g22-qr'); qr.src = '/static/presentation/workbench-qr.svg'; qr.alt = 'QR code linking to the LabourLens workbench'; qr.width = 240; qr.height = 240;
  link.append(qr, el('span', '', 'Try the workbench'));
  wrap.append(img, link);
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


/** Three review measures. Counts come from the review inventory and the sets used in the report. */
export function measureCards(m) {
  const dev = m.evalRow('dev-A3', 'gpt-6-luna')?.metrics?.n_cases, held = m.heldRow('r3', 'gpt-6-luna')?.metrics?.n_cases, v2 = m.section('evaluation').heldout_v2?.paired?.['gpt-6-luna']?.n_gold_cases;
  const referenceCount = finite(dev) && finite(held) ? fmt.int(dev + held) : 'not recorded';
  return cardRow([{icon: 'stack', head: 'Reference set', line: `${referenceCount} total: ${fmt.int(dev)} development, ${fmt.int(held)} original test.`}, {icon: 'chart-line', head: 'Fresh set', line: `${fmt.int(v2)} source- and evidence-disjoint; used once, not tuned on.`}, {icon: 'check-circle', head: 'Human reviewed', line: 'I signed off the labels on both sets, 40 saved answers and 30 source checks.'}]);
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
