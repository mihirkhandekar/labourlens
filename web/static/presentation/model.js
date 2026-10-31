// Typed selectors over report.json. The presentation draws only what these return: a missing
// value stays missing (null) and is shown as "not recorded", never as zero.
import {finite} from '../charts.js';

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
    ladder: section('retrieval').ladder || null,
    paired: Array.isArray(section('evaluation').paired) ? section('evaluation').paired : [],
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

// Rank per run: '0' is "not in the top 10", '1'..'10' is the rank of the first relevant chunk.
export function runLabel(runId) {
  const match = /agent-dev-(A\d)\/([^/]+)$/.exec(runId || '');
  return match ? {step: match[1], model: match[2]} : {step: runId, model: ''};
}

// Gold versions are identified by the SHA-256 recorded when a run was scored. Add a version here
// when a new gold file is adopted; an unknown hash is shown as its first eight characters.
const KNOWN_GOLD = {'647b26a2': 'v3.2', '050bb40b': 'v3.4', 'aac4b405': 'v3.5'};
export function goldOf(row) {
  const sha = row?.scoring_provenance?.gold_sha256;
  if (typeof sha !== 'string') return {sha: null, version: null, label: 'gold version not recorded'};
  const version = KNOWN_GOLD[sha.slice(0, 8)] || null;
  return {sha: sha.slice(0, 8), version, label: version ? `gold ${version}` : `gold ${sha.slice(0, 8)}`};
}
