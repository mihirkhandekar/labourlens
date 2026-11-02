// Typed selectors over report.json. The presentation draws only what these return: a missing
// value stays missing (null) and is shown as "not recorded", never as zero.
import {finite} from '../charts.js';

/** The standalone-question rewrite check (two saved runs), as one plain sentence. Numbers come from report.json serving.context. */
export function contextSentence(serving) {
  const a = serving?.context?.v1, b = serving?.context?.v2;
  if (!a?.conversation || !b?.conversation) return 'The rewrite check is not available in the report data.';
  const cost = b.cost_and_latency || {};
  return `Measured on its own on ${b.conversation.n} conversation cases and ${b.adversarial.n} planted-instruction histories, one gpt-6-luna call each and string checks only: ${a.conversation.passed} of ${a.conversation.n} conversation cases on the first run, then ${b.conversation.passed} of ${b.conversation.n} after I reworded the date facts, and ${b.adversarial.passed} of ${b.adversarial.n} planted instructions resisted. ${cost.calls} calls cost $${Number(cost.total_cost_usd).toFixed(4)}, median ${cost.latency_p50_s} s. This is not an independent test, because the cases guided the fix, and the accuracy of full answers after a rewrite is not measured.`;
}

export const MODELS = {'gpt-6-luna': 'gpt-6-luna', 'gpt-5.6-luna': 'gpt-5.6-luna', 'gpt-4.1-mini': 'gpt-4.1-mini'};
export const FAMILIES = ['factual_lookup', 'numerical_comparison', 'cross_source_synthesis', 'revision_conflict', 'ambiguity_insufficient_causal', 'adversarial'];
export const FAMILY_LABEL = {
  factual_lookup: 'Factual lookup', numerical_comparison: 'Numerical comparison', cross_source_synthesis: 'Cross-source synthesis',
  revision_conflict: 'Revision conflict', ambiguity_insufficient_causal: 'Ambiguity and causal overreach', adversarial: 'Adversarial'
};

export function model(report) {
  const section = key => report?.[key] || {};
  const rows = key => Array.isArray(section(key).rows) ? section(key).rows : [];
  const charts = Object.fromEntries((Array.isArray(report?.charts) ? report.charts : []).map(chart => [chart.id, chart]));
  const find = (key, id) => rows(key).find(row => row.id === id) || null;
  const m = {
    report, section, rows, charts,
    excerpts: report?.row_excerpts && typeof report.row_excerpts === 'object' ? report.row_excerpts : {},
    heldoutV31: report?.heldout_v31 && typeof report.heldout_v31 === 'object' ? report.heldout_v31 : null,
    finalEvaluation: report?.final_evaluation && typeof report.final_evaluation === 'object' ? report.final_evaluation : null,
    generatedAt: report?.generated_at || null,
    commit: report?.provenance?.commit || null,
    artifactCount: Array.isArray(report?.provenance?.artifacts) ? report.provenance.artifacts.length : null,
    scope: report?.summary?.scope || ['2024-Q1', '2026-Q2'],
    cards: Array.isArray(report?.summary?.cards) ? report.summary.cards : [],
    evalRow: (experiment, name) => find('evaluation', `experiments/eval/agent-${experiment}/${name}`),
    heldRow: (retriever, name) => find('evaluation', `experiments/eval/agent-heldout-H-${retriever}/${name}`),
    answerRow: (group, name) => find('answers', `experiments/runs/answer-dev-${group}/${name}`),
    retrievalRow: (group, name) => find('retrieval', `experiments/runs/${group}/${name}`),
    securityRow: name => find('security', `experiments/threats/runs/${name}`),
    // Corpus-v3 threat run m7-e2efix-20261031: its own key, never a registered security row.
    e2efixRow: name => (Array.isArray(section('security').e2efix?.rows) ? section('security').e2efix.rows : []).find(row => row.id === `experiments/threats/m7-e2efix-20261031/runs/${name}`) || null,
    e2efixThreats: Array.isArray(section('security').e2efix?.rows) ? section('security').e2efix.rows : [],
    devX2RegressionCheck: section('evaluation').dev_x2_regression_check && typeof section('evaluation').dev_x2_regression_check === 'object' ? section('evaluation').dev_x2_regression_check : null,
    ladder: section('retrieval').ladder || null,
    methodsV31: section('retrieval').methods?.methods ? section('retrieval').methods : null,
    paired: Array.isArray(section('evaluation').paired) ? section('evaluation').paired : [],
    secondJudge: section('evaluation').second_judge && typeof section('evaluation').second_judge === 'object' ? section('evaluation').second_judge : null,
    pairedCorpusV2Diagnostic: section('evaluation').corpus_v2_diagnostic && typeof section('evaluation').corpus_v2_diagnostic === 'object' ? section('evaluation').corpus_v2_diagnostic : null,
    trace: Array.isArray(section('agent').trace) ? section('agent').trace : [],
    events: Array.isArray(section('agent').events) ? section('agent').events : [],
    sources: rows('sources'),
    periods() {
      const set = new Set();
      Object.values(charts).forEach(chart => (chart.points || []).forEach(point => set.add(point.period)));
      return [...set].sort();
    },
    // Values aligned with `periods`, null where the series has no observation.
    values(chartId, periods) {
      const chart = charts[chartId];
      if (!chart) return null;
      const byPeriod = new Map((chart.points || []).map(point => [point.period, point.value]));
      return periods.map(period => byPeriod.has(period) ? byPeriod.get(period) : null);
    }
  };
  return m;
}

export const metricOf = value => {
  if (finite(value)) return {rate: value, ci: null, n: null};
  if (value && typeof value === 'object') return {rate: value.rate ?? value.value ?? null, ci: Array.isArray(value.ci95) && value.ci95.length === 2 ? value.ci95 : null, n: value.n ?? null};
  return {rate: null, ci: null, n: null};
};

// Deck only: the slides present gpt-6-luna alone. The report page and the documents keep both models, so this
// is applied to the report data and the built DOM in deck.js and nowhere else.
const SECOND = /gpt-5\.6-luna/;
const TWO = /\b(both models|two models|either model|second model|each model)\b|\(four configurations\)/i;
const REWRITE = [
  [/Not for gpt-5\.6-luna\./g, 'Not clearly: the sign differs between the two judges for gpt-6-luna.'],
  [/judge-measured; a second judge did not reproduce it for gpt-5\.6-luna/g, 'judge-measured; a second judge gave a different sign for gpt-6-luna on the sampled answers'],
  [/all four registered configurations/g, 'both registered configurations'],
  [/all four configurations/g, 'both gpt-6-luna configurations'],
  [/for both defended models/g, 'for the defended model'],
  [/Primary model gpt-6-luna/g, 'Model gpt-6-luna'],
  [/Right kind of response at least 205 and 209 of 237/g, 'Right kind of response at least 205 of 237'],
  [/Cases with an ungrounded number at most 34 and 51/g, 'Cases with an ungrounded number at most 34'],
  [/Main model/g, 'gpt-6-luna'],
  // The 65 fresh questions and the registered 31 are different sets: name them apart before the generic rule.
  [/\b(a|the) held-out test\b/gi, '$1 test'],
  [/\b(\d+ )?held-out v2 (questions|cases|set)\b/gi, (m, n = '') => `${n}${/^[A-Z]/.test(m) ? 'Fresh' : 'fresh'} ${m.split(' ').pop()}`],
  [/\b(Evidence-disjoint |evidence-disjoint )?held-out v2 (design|result|run|acceptance rule|evaluation|test)\b/gi, (m, pre = '', what) => (pre ? `${pre}fresh-question ${what}` : `${/^[A-Z]/.test(m) ? 'Fresh' : 'fresh'}-question ${what}`)],
  [/\bheld-out v2\b/gi, m => (/^[A-Z]/.test(m) ? 'The fresh questions' : 'the fresh questions')],
  [/\boriginal held-out\b/gi, m => (/^[A-Z]/.test(m) ? 'Original test' : 'original test')],
  [/held-out/gi, m => (/^[A-Z]/.test(m) ? 'Original test' : 'original test')],
  [/the primary filtered arm/g, 'the filtered arm']
];
/** Drop every sentence or clause that names the second model or relies on there being two; what remains is true for gpt-6-luna alone. */
export function scrubText(text) {
  if (typeof text !== 'string') return text;
  const rewritten = REWRITE.reduce((t, [re, to]) => t.replace(re, to), text);
  if (!SECOND.test(rewritten) && !TWO.test(rewritten)) return rewritten;
  return rewritten.split(/(?<=[.;])\s+/).filter(part => !SECOND.test(part) && !TWO.test(part)).join(' ').replace(/[;,]\s*$/, '.').trim();
}
export function withoutSecondModel(value) {
  const names = x => x && typeof x === 'object' && ['id', 'label', 'model', 'name', 'key', 'run_id'].some(f => typeof x[f] === 'string' && SECOND.test(x[f]));
  if (typeof value === 'string') return scrubText(value);
  if (Array.isArray(value)) return value.filter(x => !names(x)).map(withoutSecondModel).filter(x => x !== '');
  if (value && typeof value === 'object') {
    const out = {};
    Object.entries(value).forEach(([k, x]) => { if (!SECOND.test(k)) out[k] = withoutSecondModel(x); });
    return out;
  }
  return value;
}
/** Remove second-model text from a built DOM subtree: text nodes, tooltips, titles and labels. Emptied wrappers go too. */
export function scrubDom(root) {
  const flagged = text => SECOND.test(text) || TWO.test(text);
  const cellText = cell => [...cell.childNodes].filter(n => !n.classList?.contains('deck-tip')).map(n => n.textContent).join('');
  root.querySelectorAll('table').forEach(table => {
    const rows = [...table.rows], head = rows[0];
    if (head) [...head.cells].map((cell, i) => [cell, i]).reverse().forEach(([cell, i]) => { if (flagged(cellText(cell))) rows.forEach(row => row.cells[i]?.remove()); });
    rows.slice(1).forEach(row => { if ([...row.cells].some(cell => flagged(cellText(cell)))) row.remove(); });
  });
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  const nodes = [];
  while (walker.nextNode()) if (scrubText(walker.currentNode.nodeValue) !== walker.currentNode.nodeValue) nodes.push(walker.currentNode);
  nodes.forEach(node => {
    const next = scrubText(node.nodeValue);
    if (next) { node.nodeValue = next; return; }
    let parent = node.parentElement; node.remove();
    while (parent && parent !== root && !parent.textContent.trim() && !parent.querySelector('svg,img,canvas')) { const up = parent.parentElement; parent.remove(); parent = up; }
  });
  root.querySelectorAll('[title],[aria-label],[aria-description]').forEach(node => ['title', 'aria-label', 'aria-description'].forEach(attr => {
    const v = node.getAttribute(attr);
    if (v && scrubText(v) !== v) { const next = scrubText(v); if (next) node.setAttribute(attr, next); else node.removeAttribute(attr); }
  }));
}

// Rank per run: '0' is "not in the top 10", '1'..'10' is the rank of the first relevant chunk.
export function runLabel(runId) {
  const match = /agent-dev-(A\d)\/([^/]+)$/.exec(runId || '');
  return match ? {step: match[1], model: match[2]} : {step: runId, model: ''};
}

// Gold versions are identified by the SHA-256 recorded when a run was scored. Add a version here
// when a new gold file is adopted; an unknown hash is shown as its first eight characters.
const KNOWN_GOLD = {'647b26a2': 'v3.2', '050bb40b': 'v3.4', 'aac4b405': 'v3.5', '6169a9de': 'v3.6', 'af3ad026': 'v3.7', 'e3d16597': 'fresh set v1'};
export function goldOf(row) {
  const sha = row?.scoring_provenance?.gold_sha256;
  if (typeof sha !== 'string') return {sha: null, version: null, label: 'gold version not recorded'};
  const version = KNOWN_GOLD[sha.slice(0, 8)] || null;
  return {sha: sha.slice(0, 8), version, label: version ? `gold ${version}` : `gold ${sha.slice(0, 8)}`};
}
