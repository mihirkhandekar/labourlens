import {secondJudgeSentence} from './graphics.js';
import {el, figure, shareBars, fmt} from '../charts.js';
import {chapter, section, callout, evi, list, details} from './ui.js';
import {goldOf, metricOf} from './model.js';

// Review counts come from docs/human-review/owner-review-final-summary.md and review-inventory.md.
// They are not in report.json; the evidence toggle names the files.
function reviewFigure() {
  const rows = [
    {label: 'Answer verdicts, 40 outputs', sub: 'human review of saved answers', segments: [
      {key: 'c', label: 'Correct', value: 25, cls: 'c1'}, {key: 'p', label: 'Partly correct', value: 6, cls: 'c6'}, {key: 'i', label: 'Incorrect', value: 9, cls: 'c2'}]},
    {label: 'Gold cases, 268', sub: 'owner review of label, evidence, facts', segments: [
      {key: 'ok', label: 'Reviewed, label kept', value: 266, cls: 'c1'}, {key: 'dis', label: 'Label changed in v3.5', value: 2, cls: 'c6'}]},
    {label: 'Held-out v2 questions, 65', sub: 'owner review of label, evidence, facts', segments: [
      {key: 'v2', label: 'Reviewed and signed off', value: 65, cls: 'c1'}]},
    {label: 'Source checks, 30', sub: 'human source/data quality review', segments: [
      {key: 'm', label: 'Match', value: 18, cls: 'c1'}, {key: 'mi', label: 'Minor difference', value: 12, cls: 'c6'}]},
    {label: 'AI review of 40 outputs', sub: 'blind AI judgment, failure-enriched sample', segments: [
      {key: 'ac', label: 'AI: correct', value: 28, cls: 'c1'}, {key: 'ap', label: 'AI: partly correct', value: 6, cls: 'c6'}, {key: 'ai', label: 'AI: incorrect', value: 6, cls: 'c2'}]}
  ];
  return figure({
    id: 'fig-review', title: 'I signed off four separate review streams; labels began as AI drafts', wide: true,
    takeaway: 'I signed off every item after the saved runs. Labels were checked in three separate AI passes from one model family. One human reviewer; not independent inter-rater evidence.',
    summary: rows.map(r => `${r.label}: ${r.segments.map(s => `${s.label} ${s.value}`).join(', ')}`).join('. '),
    source: {data: 'docs/human-review/owner-review-final-summary.md · docs/human-review/review-inventory.md (not in report.json)', files: ['experiments/human-review-sample/independent-ai-review-2.md']},
    note: 'These are four separate review streams, not one sum: 268 gold questions (237 development plus 31 original held-out), 65 held-out v2 questions, 40 saved system answers and 30 source checks. Only the first two are questions; 403 is the total count of items. The original 31-case test overlaps development evidence: 25/31 share at least one evidence id, and 15/31 have all evidence represented in development. The 65-case fresh set is source/evidence-disjoint from the original 268 by a pre-run audit, signed before its first run and not used to tune the default system. It has since been run five times per arm, including a diagnostic after the second tool set was designed. The 40 answers are a failure-enriched sample, six per family plus four status mismatches, not 40 new questions. Source checks are not model outputs. Where an AI suggestion existed my decision matched it in 198 of 198 gold cases, 61 of 64 fresh cases, 38 of 39 answers and 29 of 30 source checks: agreement, not accuracy. I was the sole human reviewer after three separate passes from the same AI model family and after the saved runs were scored. This is not independent inter-rater evidence.',
    table: () => ({caption: 'Review counts', columns: ['Review', 'Group', 'Count'], rows: rows.flatMap(r => r.segments.map(s => [r.label, s.label, s.value]))}),
    draw: (host, c) => shareBars(host, c, {rows, label: 'Review counts by kind', rowH: c.compact ? 60 : 56})
  });
}

const limitsFor = m => { const rights = m.section('serving').rights || {}; return [
  ['Labels were AI drafts first', 'An AI drafted all 268 gold cases (237 development, 31 held-out). I went through them in the review interface and signed off on every case, after AI pre-review and after the saved runs were scored. Two labels changed in v3.5 (HO-022 clarify to answer, DEV-018 refuse to clarify). Four later change-clicks were not applied, so labels are unchanged in v3.7.', 'docs/human-review/owner-review-final-summary.md, experiments/gold/CHANGELOG.md'],
  ['Human reviewed after the saved runs', 'I signed off every item in four separate review streams after three separate AI review passes from the same model family. One human reviewer, after the runs; this is owner sign-off, not independent inter-rater evidence. Where an AI suggestion existed, the decision matched it in 198 of 198 gold cases.', 'docs/human-review/owner-review-final-summary.md, docs/human-review/review-inventory.md'],
  ['Held-out reuses development evidence', '31 cases; 25 of 31 reuse a development evidence id and 15 of 31 reuse their whole set. The interval on the r3 gain touches or crosses zero.', 'docs/system-card.md, report.json › evaluation.paired'],
  ['Some scores sit on earlier gold versions', `Development rows use ${goldOf(m.evalRow('dev-A3', 'gpt-6-luna')).label}; held-out rows use ${goldOf(m.heldRow('r3', 'gpt-6-luna')).label}, after post-run label edits. Both were rescored from saved outputs with no new generation. Original held-out scores on v3.2 to v3.4 stay in the evaluation report beside the current ones.`, 'experiments/heldout/FREEZE.md, README.md, experiments/gold/CHANGELOG.md'],
  ['T-I06: handled in one run, not shown stable or general', 'Before the fix, a planted false figure was cited and passed the quote and number checks. The deterministic cross-check handled that one case in both models in the first post-fix run, under a scorer written after the run. In the final-code run it passed for gpt-6-luna and failed for gpt-5.6-luna on an exact-string scorer check. Coverage is a closed grammar, and the end-to-end review found faults in the guard; docs/threat-model.md has their status.', 'docs/experiments/m7-t-i06-crosscheck.md, D-038'],
  ['The scanner is a warning layer, not a boundary', 'On a frozen test it flags 23 of 30 attacks (95% interval 59 to 88%) and 9 of 30 deliberately hard harmless sentences. Paraphrase, role-play and non-English instructions still pass. Zero scanner hits does not certify a source as safe.', 'docs/experiments/injection-scanner-v2.md'],
  ['Extraction has known defects', 'In sampled passages, 1 of 16 lost a note boundary and 2 of 4 HTML passages flattened superscripts; some feedback-form blocks are garbled. The corpus v2 extraction fixes removed the defects found then, with no measurable quality change (X1). No corpus-wide count of remaining defects exists.', 'docs/human-review/ai-pre-review-passage-spot-check.md, docs/evaluation-report.md'],
  ['The sector dataset total sits above MOM\u2019s final figure', 'Migrant domestic workers may explain it, but that is an inference.', 'docs/data-sheet.md › section 5'],
  ['The judge shares a provider with the generators', `Their errors may correlate. A zero unsupported-claim rate on a selected sample does not show the answers are safe.${secondJudgeSentence(m) ? ` ${secondJudgeSentence(m)}` : ' A second judge from another model family has not been run.'}`, 'docs/evaluation-report.md › Judge and uncertainty · docs/experiments/second-judge.md'],
  ['Registered results ran on older corpora than the one served', 'Registered results ran on corpus v1; the X1 and T-I06 post-fix runs used corpus v2. Corpus v3 (85 sources) has three measured evaluations: the X2 development regression check, the e2efix threat run and held-out v2 (65 questions, evidence-disjoint at source level only), plus the tool set v2 runs (X3 and V2post, not adopted). The live site serves corpus v3.1 (16,419 passages; 1,847 chunks); /healthz shows the commit and the corpus fingerprint.', 'README.md › Corpus versions, docs/evaluation-report.md'],
  ['X2 is a regression check, not an ablation', 'Corpus v3, runtime changes B1 to B14, the cross-check and gold v3.6 changed together. Behaviour, false-answer, over-abstention, key-number recall and calculation intervals overlap A3. Ungrounded-number cases rose (gpt-5.6-luna: intervals do not overlap); the claim-support point estimate is lower but not a demonstrated fall. The ungrounded check was also widened, so measurement changed and the two effects are not separable.', 'docs/experiments/m7-e2e-fixes.md, experiments/eval/agent-dev-X2-REPORT.md'],
  ['T-I06 is not shown stable across runs', 'The earlier post-fix run passed 36 of 36 under a scorer written afterwards. In the final-code run gpt-5.6-luna fails: its answer reported the dataset value and disclosed the planted figure in a caveat, but failed an exact-string check. The scorer was not changed, which is a brittleness finding. The 2 Nov fresh rerun fails T-I06 in all four configurations under both scorers. Post-hoc v2 rescoring of saved outputs remains diagnostic only. One case, closed grammar, one run per configuration; the suite does not show a defence effect.', 'experiments/threats/m7-e2efix-20261031/SUMMARY.md, docs/experiments/m7-t-i06-crosscheck.md'],
  ['Costs are list-price estimates', 'List prices dated 30 October 2026, without cached-input discounts. Latency is saved wall time from the recorded runs.', 'docs/system-card.md › Architecture and models'],
  ['Two final runs per arm are not a variance estimate', 'The final headline is the mean of FIN and the pre-registered FIN2 replicate. Development signs agree; no gain is demonstrated on original test or fresh questions. Other experiments remain one run unless labelled otherwise.', 'docs/evaluation-report.md › Read this first'],
  ['Fixed pipeline has one development run', 'Fixed behaviour accuracy .814 versus agent mean .897 on 237 development questions. No original-test or fresh-question comparison. Whole control policies differ; the fixed arm has a narrower extraction schema with the unchanged planner prompt, and historical runtime drift remains possible.', 'experiments/eval/agent-vs-fixed-pipeline.json'],
  ['Retrieval diagnostics do not establish answer gains', 'Strict passage hit@8 is .167/.500 for hybrid and .778/.941 for filter then rerank, on 18 original-test and 34 fresh text questions. These are literal queries on reused sets; case intervals omit reranker and gold uncertainty. No demonstrated end-to-end gain.', 'experiments/eval/heldout-retrieval-20261103-paid/metrics.json'],
  ['Threat v2 changes guards and prompt together', 'Guarded 50/54 versus naive 42/54 attacks, three repeats; 10 versus 2 arm-only passes, exact McNemar p=.039. Both arms fail 3/8 benign cases. This cannot attribute a gap to a single defence layer, and one author wrote the cases.', 'docs/experiments/threat-v2-results.md'],
  ['Temperature and reasoning effort were not varied', 'Calls used provider defaults rather than explicit temperature or reasoning settings. New runs record provider-default temperature and top_p, no seed, prompt hashes and completion limits. Older runs did not record that sampling block.', 'docs/evaluation-report.md › Read this first'],
  ['Licences are unverified for some sources', `${rights.datasets_unverified != null ? `${rights.datasets_unverified} datasets are assumed open but unverified, and ${rights.sources_unresolved} documents have unresolved rights.` : 'Licence status is not recorded.'} All of them stay on my machine; none is committed or published. The report PDFs carry their own copyright notices.`, 'docs/data-sheet.md › section 5 · report.json › serving.rights'],
  ['No provider-side spend cap is verified', 'The app reserves $0.05 per question and keeps a daily budget, but that is its own estimate. A cap set at the provider has not been checked on the server.', 'docs/deploy.md'],
  ['The live app is not the evaluated system', 'It adds a small-talk reply, a scope check, a rewrite of follow-up questions and statistics lookups through MCP, and serves document build v3.1. The scope check was measured alone and the MCP route for latency and protocol behaviour; a separate 65-case served-chain sample (statistics-only MCP; not the fresh 65) measures the served configuration: 90.8% for both models, no observed loss against direct, but 51 reused development cases, 14 hand-written probes, one run and the same judge family.', 'docs/decisions.md › D-050 to D-053 · report.json › serving']
]; };

function limitCards(m) {
  const wrap = el('div', 'pr-limit-grid');
  limitsFor(m).forEach(([title, text, src], i) => {
    const card = el('article', `pr-limit${i === 4 ? ' is-open' : ''}`);
    card.append(el('span', 'pr-limit-no', String(i + 1).padStart(2, '0')), el('h5', 'pr-limit-title', title), el('p', '', text), evi(src));
    wrap.append(card);
  });
  return wrap;
}

export function renderLimits(m, ctx) {
  const ch = chapter({
    id: 'limits', title: 'I signed off four separate review streams; labels began as AI drafts',
    bullets: [
      'I signed off four separate review streams, drafted by AI: gold questions, held-out v2 questions, saved answers and source checks.',
      'One human reviewer, after three AI passes from the same model family and after the runs.',
      `${limitsFor(m).length} limits below constrain what the results show, including the single T-I06 result and the scanner bypass.`
    ]
  });
  const review = section('Human review: 268 gold questions, 65 fresh questions, 40 answers and 30 source checks');
  review.append(reviewFigure().root);
  ch.body.append(review);
  const limits = section(`${limitsFor(m).length} limits on the conclusions`);
  limits.append(limitCards(m));
  const rec = [...(m.report?.limitations || []), ...(m.section('evaluation').limitations || [])];
  if (rec.length) limits.append(details('Limitations recorded in report.json', list(rec), evi('report.json › limitations · evaluation.limitations')));
  ch.body.append(limits);
  return ch.root;
}

const NEXT = [
  ['Write a new untouched set of fresh questions', 'The 65 fresh questions are no longer untouched: they have been run five times per arm and one diagnostic shaped the second tool set. I would write a new set on sources no earlier case cites, freeze it with the decision rule fixed first, and run it once.', 'Success: a paired interval for r3 minus hybrid that excludes zero, or a clear null, on questions nobody has tuned against.'],
  ['Isolate the figure cross-check and prompt effects', 'Threat v2 tests eight planted figures and compares a guards-plus-prompt bundle. I would freeze new cases and separate those factors, widen phrasings recognised in real passages and measure false conflicts.', 'Success: a per-layer comparison with a fixed scorer, and a lower benign-failure count than 3 of 8.'],
  ['Add independent review', 'I would add blinded, independent annotation of the gold cases, because one reviewer after the AI drafts is not independent. Where an AI suggestion existed, the owner\u2019s decision matched it in 198 of 198 gold cases.', 'Success: named independent reviewers on every gold case used in a reported metric.'],
  ['Count extraction defects corpus-wide', 'I would count lost note boundaries and flattened superscripts across the whole corpus, not a sample, and fix the worst. The corpus v2 fixes removed the defects found, and X1 showed no measurable quality change.', 'Success: a defect rate before and after the fix, with retrieval and answer metrics reported next to it.'],
  ['Replace the heuristic scanner', 'I would add model-assisted screening and test it on a larger, human-written set. The current scanner missed all 5 paraphrase probes.', 'Success: paraphrase probes caught at a measured rate, with the false-positive cost reported.'],
  ['Soften the period filter', 'I would test a filter that widens when the candidate pool is weak. A later release can restate an earlier quarter, and a hard filter can exclude it.', 'Success: fewer filter-related misses with the R3 gain kept.']
];

export function renderNext(m, ctx) {
  const ch = chapter({
    id: 'next', title: 'Six experiments would close the main evaluation gaps',
    bullets: [
      'Each step names the gap it addresses and the measurement that would close it.',
      'None is built or run yet.'
    ]
  });
  const ol = el('ol', 'pr-next');
  NEXT.forEach(([title, text, success], i) => {
    const li = el('li', 'pr-next-item');
    li.append(el('span', 'pr-next-no', String(i + 1)), el('h5', 'pr-next-title', title), el('p', '', text), el('p', 'pr-next-success', success));
    ol.append(li);
  });
  ch.body.append(ol);
  const reproduce = callout({
    tone: 'note', title: 'Report provenance',
    text: 'Turn on \u201cShow the evidence\u201d to see the report field or file behind each number. Rebuild the report from committed artifacts with: uv run labourlens build-report.',
    src: 'README.md · docs/deploy.md'
  });
  ch.body.append(reproduce);
  return ch.root;
}

const olist = items => { const ol = el('ol', 'pr-list'); items.forEach(t => ol.append(el('li', '', t))); return ol; };
const ciText = ci => ci ? `95% CI ${fmt.pct(ci[0])} to ${fmt.pct(ci[1])}` : '';

export function renderSummary(m, ctx) {
  const L = m.ladder?.configs, a3 = m.evalRow('dev-A3', 'gpt-6-luna'), held = m.heldRow('r3', 'gpt-6-luna');
  const dev = metricOf(a3?.metrics?.behaviour_accuracy), ho = metricOf(held?.metrics?.behaviour_accuracy);
  const pair = m.paired[0]?.models?.['gpt-6-luna'], pairN = m.paired[0]?.n;
  const luna = m.securityRow('gpt-6-luna')?.metrics, x = m.section('mcp').metrics || {};
  const crosses = pair && pair.ci95[0] <= 0;
  const title = ho.rate != null
    ? `On ${ho.n ?? 31} held-out cases r3 scored ${fmt.pct(ho.rate)}${ho.ci ? ` (${ciText(ho.ci)})` : ''}, and its gain over hybrid is ${crosses ? 'not demonstrated' : 'above zero'}`
    : 'Held-out result not recorded';
  const ch = chapter({id: 'summary', title});
  const findings = [
    L?.R0 && L?.R3 ? `${fmt.pct(L.R0['hit@8'])} to ${fmt.pct(L.R3['hit@8'])}: hit@8 from R0 to R3 on ${fmt.int(m.ladder.n_cases)} development cases.` : null,
    dev.rate != null ? `${fmt.pct(dev.rate)}: behaviour accuracy of A3 with gpt-6-luna on ${fmt.int(dev.n ?? a3.metrics.n_cases)} development cases${dev.ci ? ` (${ciText(dev.ci)})` : ''}.` : null,
    pair ? `${fmt.pts(pair.diff)}: held-out r3 minus hybrid for gpt-6-luna on ${fmt.int(pairN)} cases, interval ${fmt.pts(pair.ci95[0])} to ${fmt.pts(pair.ci95[1])}${crosses ? ', not demonstrated' : ''}.` : null,
    luna ? `${fmt.int(luna.passed)} of ${fmt.int(luna.n_scored)}: threat-suite cases passed by gpt-6-luna with defences.` : null,
    x.compared_datasets != null ? `${fmt.int(x.different_outputs)} of ${fmt.int(x.compared_datasets)}: datasets whose output differed between MCP and direct calls.` : null
  ].filter(Boolean);
  const block = section('Five results');
  block.append(olist(findings));
  const open = section('Open items');
  open.append(olist([
    'T-I06: a deterministic cross-check handled the one planted-figure case in the first post-fix run, under a scorer written after it. The final-code run on corpus v3 is 36/36 for gpt-6-luna and 35/36 for gpt-5.6-luna: not shown stable.',
    'Labels were AI drafts, confirmed by one human reviewer after the saved runs; three review passes used the same model family. This is not independent inter-rater evidence.',
    'The original test overlaps development evidence; the later 65-case fresh set was evidence-disjoint and signed before its first run, but it has since been run five times per arm and motivated a second tool set that was not adopted.'
  ]));
  ch.body.append(block, open);
  return ch.root;
}
