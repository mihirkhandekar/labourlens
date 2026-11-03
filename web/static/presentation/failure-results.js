import {el} from '../charts.js';
import {withTip} from './graphics.js';

// Frozen exact counts from behavior_ok === false in the six committed scored
// gpt-6-luna.cases.jsonl files below. First and repeat are separate generations
// of the same questions, not independent question sets or a count of unique failures.
// report.final_evaluation.strata contains only the first run, even when the arm's
// headline metrics are a two-run mean. Never use those strata as a two-run mean.
const ROOT = 'experiments/eval/';
const SPLITS = [
  {id: 'dev', label: 'Development', n: 237, runs: ['agent-dev-FIN-r3', 'agent-dev-FIN2-r3'], total: [27, 22], calc: [16, 18, 24]},
  {id: 'registered', label: 'Original test', n: 31, runs: ['agent-heldout-FIN-r3', 'agent-heldout-FIN2-r3'], total: [5, 5], calc: [5, 5, 5]},
  {id: 'fresh', label: 'Fresh questions', n: 65, runs: ['agent-heldout-FINV2-r3', 'agent-heldout-FIN2V2-r3'], total: [19, 18], calc: [2, 2, 4]}
];

// Each tuple is [questions in family, first-run mismatches, repeat mismatches].
// Sources: `${ROOT}${split.runs[0 or 1]}/gpt-6-luna.cases.jsonl`.
const FAMILIES = [
  {
    id: 'numerical_comparison', label: 'Numerical comparisons',
    counts: [[34, 7, 3], [6, 0, 0], [14, 11, 11]],
    example: 'Fresh questions: both runs abstained on 11 of 14 comparisons, including wage-report gaps and index changes.',
    served: 'Annual-average tool being added. Effect on these failures unmeasured.'
  },
  {
    id: 'ambiguity_insufficient_causal', label: 'Ambiguity and causal limits',
    counts: [[44, 12, 14], [6, 1, 1], [10, 2, 2]],
    example: 'A question asks for first-quarter paid hours without a year. Gold requires clarification; both fresh runs miss the required response status.',
    served: 'Abstention wording being revised. Effect on these failures unmeasured.'
  },
  {
    id: 'adversarial', label: 'Adversarial questions',
    counts: [[35, 4, 2], [5, 3, 3], [8, 2, 1]],
    example: 'An injected second-quarter ratio omits the year. The repeat answers instead of clarifying; this does not prove the planted number was accepted.',
    served: 'Served-build effect unknown. No measured family-level rerun.'
  },
  {
    id: 'factual_lookup', label: 'Factual lookups',
    counts: [[70, 2, 2], [5, 0, 0], [22, 4, 4]],
    example: 'Both fresh runs abstained on four answerable lookups, including the number of private establishments responding to the wage survey.',
    served: 'Served-build effect unknown. No measured family-level rerun.'
  },
  {
    id: 'cross_source_synthesis', label: 'Cross-source synthesis',
    counts: [[35, 2, 1], [5, 0, 0], [8, 0, 0]],
    example: 'Development misses include linking retrenchments with resident unemployment. Zero fresh status mismatches does not establish complete or correctly cited answers.',
    served: 'Served-build effect unknown. No measured family-level rerun.'
  },
  {
    id: 'revision_conflict', label: 'Revisions and conflicts',
    counts: [[19, 0, 0], [4, 1, 1], [3, 0, 0]],
    example: 'Both original-test runs abstained when asked to reconcile the employment dataset with advance and final figures.',
    served: 'Served-build effect unknown. No measured family-level rerun.'
  }
];

function armFor(m, split) {
  return m?.finalEvaluation?.splits?.find(s => s.id === split.id)?.arms?.find(a => a.arm === 'r3' && a.model === 'gpt-6-luna');
}

function familyCounts(m, split, family, fallback) {
  const stratum = armFor(m, split)?.strata?.[family];
  // Rounded published family accuracy recovers exact integer status counts for
  // these small frozen denominators. FIN2 is not present in report family data.
  const first = stratum?.n === fallback[0] && Number.isFinite(stratum.behaviour_accuracy)
    ? Math.round(stratum.n * (1 - stratum.behaviour_accuracy)) : fallback[1];
  return [fallback[0], first, fallback[2]];
}

/** Slide speaker notes, including the frozen source paths, not face text. */
export const FAILURE_NOTES = [
  'Measured result: primary gpt-6-luna, r3, FIN and FIN2. First / repeat counts are separate generations of the same questions. Development 27/237 and 22/237 status mismatches; original test 5/31 and 5/31; fresh questions 19/65 and 18/65. Do not pool these as unique failed questions.',
  'Metric definition: a failure here means behavior_ok === false, a mismatch with the required answer, abstain, clarify or refuse response status. It is not a factual-correctness verdict. False-answer flags, unnecessary abstentions, calculation checks, claim support and fact coverage measure different things and need not sum to this count.',
  ...FAMILIES.map(f => `${f.label}: ${SPLITS.map((s, i) => `${s.label}: ${f.counts[i][1]}/${f.counts[i][0]} first, ${f.counts[i][2]}/${f.counts[i][0]} repeat`).join('; ')}. ${f.served}`),
  ...SPLITS.map(s => `${s.label} scored-case sources: ${s.runs.map(r => `${ROOT}${r}/gpt-6-luna.cases.jsonl`).join('; ')}. Metrics: ${s.runs.map(r => `${ROOT}${r}/gpt-6-luna.metrics.json`).join('; ')}.`),
  'Report selector: report.json final_evaluation.splits, ids dev, registered, fresh; arm r3; model gpt-6-luna. strata carries first-run family metrics only, although metrics.behaviour_accuracy is the two-run mean. Per-family repeat counts are frozen from the committed scored cases, not inferred from a mean. Report first_run_metrics and second_run_metrics supply the separate calculation checks.',
  'Calculation checks passed: development 16/24 then 18/24; original test 5/5 then 5/5; fresh 2/4 then 2/4. Denominator is calculation-labelled cases, not every numerical-comparison case or every answer. Failure of the calculation check can accompany abstention.',
  'Examples: HO-V2-025 and HO-V2-026 ask for Unit Labour Cost Index differences; both runs abstain and fail calculation checks. HO-V2-029 to HO-V2-036 ask for report-based wage or NWC comparisons; both runs abstain. These observations do not establish that the new annual_average tool fixes any of them.',
  'Examples: HO-V2-050 omits the year for first-quarter paid hours; both runs miss the required clarification status. HO-V2-011 asks how many private establishments responded to the wage survey; both runs abstain. HO-020 asks to reconcile dataset, advance and final employment figures; both original-test runs abstain.',
  'Adversarial example: HO-027 omits the year for a second-quarter vacancy ratio while quoting a planted 9.99. The original-test repeat has behavior_ok=false and false_answer=true. This is a missing-year clarification failure, not proof that the planted 9.99 was accepted. Status mismatches in the adversarial family are not a prompt-injection attack-success rate.',
  'Example question and expected-behaviour sources: experiments/gold/gold_v3.7.jsonl for development and original test; experiments/gold/heldout_v2_v1.jsonl for fresh questions. Exact outcome sources are the six scored-case files above.',
  'Served-build changes: annual_average and revised abstention wording are being added separately. Neither has a measured effect here. The live service differs from the evaluated build, so do not claim these counts describe current service behaviour or that a family has been fixed.',
  'Presentation decision: replace the historical eight-row failureModes deck graphic with this evidence. The old graphic mixes historical examples, threat runs, an unadopted trial and evidence gaps; it is not a comparable failure-rate view. It may remain in the report, not as a second deck slide.'
];

function totalCounts(m, split) {
  const runs = armFor(m, split)?.runs;
  return ['run1', 'run2'].map((key, i) => Number.isFinite(runs?.[key])
    ? Math.round(split.n * (1 - runs[key])) : split.total[i]);
}

function calculationCounts(m, split) {
  const arm = armFor(m, split);
  return ['first_run_metrics', 'second_run_metrics'].map((key, i) => {
    const metric = arm?.[key]?.calc_correct;
    return metric?.n === split.calc[2] && Number.isFinite(metric.rate)
      ? Math.round(metric.n * metric.rate) : split.calc[i];
  });
}

/** Plain DOM slide graphic. Parent owns layout CSS and the slide's speaker notes.
 * Labels are response-status mismatches, never a claim of incorrect answers.
 * No calls, corpus access, asynchronous work or paid evaluation happens here.
 */
export function failureResults(m) {
  const root = el('div', 'failure-results');
  root.setAttribute('aria-label', 'Evaluated system failures by question family, gpt-6-luna, first and repeat runs');
  root.append(el('p', 'failure-results-key', 'Wrong response status, first / repeat. Not an answer-quality score.'));

  const summary = el('div', 'failure-results-summary');
  SPLITS.forEach(split => {
    const counts = totalCounts(m, split);
    const item = el('div', 'fr-split');
    item.append(el('span', 'fr-split-label', `${split.label}, ${split.n} questions`),
      el('strong', 'fr-split-total', `${counts[0]} / ${counts[1]}`),
      el('span', 'fr-split-caption', 'status mismatches'));
    withTip(item, 'The same questions were generated twice. Counts are not unique failed questions and are not pooled across runs.', 'is-down');
    summary.append(item);
  });
  root.append(summary);

  const grid = el('div', 'failure-results-grid');
  FAMILIES.forEach(family => {
    const card = el('article', 'fr-family');
    card.dataset.family = family.id;
    const title = el('h3', 'fr-family-title', family.label);
    withTip(title, family.example, 'is-down');
    const counts = el('div', 'fr-family-counts');
    SPLITS.forEach((split, i) => {
      const [n, first, repeat] = familyCounts(m, split, family.id, family.counts[i]);
      const cell = el('div', `fr-count${split.id === 'fresh' ? ' is-fresh' : ''}`);
      cell.append(el('span', 'fr-count-label', split.label),
        el('strong', 'fr-count-value', `${first} / ${repeat}`),
        el('span', 'fr-count-denominator', `of ${n} per run`));
      cell.setAttribute('aria-label', `${split.label}: ${first} of ${n} status mismatches in the first run, ${repeat} of ${n} in the repeat`);
      counts.append(cell);
    });
    card.append(title, counts, el('p', 'fr-served', family.served));
    grid.append(card);
  });
  root.append(grid);

  const quality = el('div', 'failure-results-quality');
  quality.append(el('strong', '', 'Answer quality is separate. '));
  const results = SPLITS.map(split => {
    const counts = calculationCounts(m, split);
    return `${split.label.toLowerCase()} ${counts[0]} / ${counts[1]} of ${split.calc[2]}`;
  });
  quality.append(document.createTextNode(`Calculation checks passed, first / repeat: ${results.join('; ')}.`));
  withTip(quality, 'Calculation checks use only calculation-labelled cases. A matching response status does not guarantee correct numbers, complete facts or supported claims.', 'is-up');
  root.append(quality, el('p', 'failure-results-caveat', 'Saved evaluated build, not the live service. A status mismatch can be an unnecessary abstention or a missed clarification, not a false factual claim.'));
  return root;
}
