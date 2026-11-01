// The development loop I worked in, drawn with the presentation's loop styles: six steps, my approval
// as the one highlighted gate, and the guardrails that sat around every step.
import {svg} from './dom.js';
import {el} from './dom.js';

const W = 1500, H = 700;

export function processLoop() {
  const root = svg('svg', {viewBox: `0 0 ${W} ${H}`, class: 'g6-svg rp-loop', role: 'img', focusable: 'false'});
  root.setAttribute('aria-label', 'The development loop: propose, compare, approve, build, verify, record, then the next decision. I approve at the third step. Around it sit guardrails: a written contract, milestone gates, a decision log, state kept in files, frozen results, a rights scan, read-only tools and a budget ledger.');

  const defs = svg('defs');
  const marker = svg('marker', {id: 'rp-arrow', viewBox: '0 0 10 10', refX: 8, refY: 5, markerWidth: 9, markerHeight: 9, orient: 'auto'});
  marker.append(svg('path', {d: 'M0 0 10 5 0 10z', class: 'g6-head'}));
  defs.append(marker);
  root.append(defs);

  // Frame that the guardrails sit on.
  const top = 70, bottom = 640;
  root.append(svg('rect', {x: 8, y: top, width: W - 16, height: bottom - top, rx: 28, class: 'rp-frame'}));

  const tab = (label, cx, y) => {
    const width = Math.max(220, label.length * 17 + 56);
    const g = svg('g', {class: 'rp-guard'});
    g.append(svg('rect', {x: cx - width / 2, y: y - 30, width, height: 60, rx: 12}), svg('text', {x: cx, y: y + 9, 'text-anchor': 'middle'}, label));
    return g;
  };
  ['Written contract', 'Milestone gates', 'Decision log', 'State in files'].forEach((label, i) => root.append(tab(label, 190 + i * 373, top)));
  ['Frozen results', 'Rights scan', 'Read-only tools', 'Budget ledger'].forEach((label, i) => root.append(tab(label, 190 + i * 373, bottom)));

  // The loop.
  const steps = [['Propose', 'options'], ['Compare', 'baseline'], ['Approve', 'my call'], ['Build', 'in scope'], ['Verify', 'checks'], ['Record', 'log']];
  const bw = 190, bh = 130, y0 = 270, x0 = 60;
  const gap = (W - 2 * x0 - steps.length * bw) / (steps.length - 1);
  const xs = steps.map((_, i) => x0 + i * (bw + gap));
  for (let i = 0; i < steps.length - 1; i += 1) {
    root.append(svg('line', {x1: xs[i] + bw, x2: xs[i + 1] - 4, y1: y0 + bh / 2, y2: y0 + bh / 2, class: 'g6-edge', 'marker-end': 'url(#rp-arrow)'}));
  }
  const fromX = xs[steps.length - 1] + bw / 2, toX = xs[0] + bw / 2, yy = y0 + bh;
  root.append(svg('path', {d: `M${fromX} ${yy} C${fromX} ${yy + 110} ${toX} ${yy + 110} ${toX} ${yy + 4}`, class: 'g6-edge is-loop', 'marker-end': 'url(#rp-arrow)'}));
  root.append(svg('text', {x: (fromX + toX) / 2, y: yy + 128, 'text-anchor': 'middle', class: 'g6-loop-label'}, 'Next decision'));
  steps.forEach(([name, sub], i) => {
    const g = svg('g', {class: `g6-box${name === 'Approve' ? ' is-guard' : ''}`});
    g.append(svg('rect', {x: xs[i], y: y0, width: bw, height: bh, rx: 12}), svg('text', {x: xs[i] + bw / 2, y: y0 + 62, 'text-anchor': 'middle', class: 'g6-text'}, name), svg('text', {x: xs[i] + bw / 2, y: y0 + 100, 'text-anchor': 'middle', class: 'g5-tag'}, sub));
    root.append(g);
  });
  root.append(svg('text', {x: xs[2] + bw / 2, y: y0 - 28, 'text-anchor': 'middle', class: 'g6-loop-label'}, 'My decision'));

  const wrap = el('div', 'g6 rp-loop-wrap');
  wrap.append(root);
  return wrap;
}
