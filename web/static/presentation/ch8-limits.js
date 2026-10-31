import {el, figure, shareBars} from '../charts.js';
import {chapter, section, callout, evi, list, details} from './ui.js';
import {goldOf} from './model.js';

// Review counts come from docs/human-review/owner-review-summary.md, README.md and docs/system-card.md.
// They are not in report.json; the evidence toggle names the files.
function reviewFigure() {
  const rows = [
    {label: 'Owner decisions, 125 cards', sub: 'per card, not independent', segments: [
      {key: 'own', label: 'Own verdict', value: 30, cls: 'c1'}, {key: 'earlier', label: 'Agreed with earlier AI passes', value: 67, cls: 'c6'}, {key: 'tie', label: 'Agreed with the 3-pass tie-break', value: 28, cls: 'c5'}]},
    {label: 'Answer verdicts, 40 outputs', sub: 'owner', segments: [
      {key: 'c', label: 'Correct', value: 25, cls: 'c1'}, {key: 'p', label: 'Partly correct', value: 6, cls: 'c2'}, {key: 'i', label: 'Incorrect', value: 9, cls: 'c4'}]},
    {label: 'Gold cases, 268', sub: 'owner review of label, evidence, facts', segments: [
      {key: 'ok', label: 'Reviewed, no change', value: 43, cls: 'c1'}, {key: 'dis', label: 'Reviewed, label changed', value: 2, cls: 'c2'}, {key: 'dr', label: 'Still AI drafts', value: 223, cls: 'c6'}]},
    {label: 'Source cards, 30', sub: 'owner', segments: [
      {key: 'm', label: 'Match', value: 19, cls: 'c1'}, {key: 'mi', label: 'Minor difference', value: 11, cls: 'c2'}]},
    {label: 'Blind AI review, 40 outputs', sub: 'AI judgment, failure-enriched sample', segments: [
      {key: 'ac', label: 'AI: correct', value: 28, cls: 'c1'}, {key: 'ap', label: 'AI: partly correct', value: 6, cls: 'c2'}, {key: 'ai', label: 'AI: incorrect', value: 6, cls: 'c4'}]}
  ];
  return figure({
    id: 'fig-review', title: 'Who has actually checked what', wide: true,
    takeaway: 'The owner decided 125 cards: 30 by own verdict and 95 by agreeing with an AI suggestion. Agreeing with an AI is circular, so it is not independent inter-rater evidence, and no blinded annotation was run. The 17 manual answer verdicts all agree with the independent AI review. That is agreement, not accuracy. 45 of 268 gold cases are owner-reviewed; 223 are still drafts.',
    summary: rows.map(r => `${r.label}: ${r.segments.map(s => `${s.label} ${s.value}`).join(', ')}`).join('. '),
    source: {data: 'docs/human-review/owner-review-summary.md · README.md · docs/system-card.md (not in report.json)', files: ['experiments/human-review-sample/independent-ai-review-2.md']},
    note: 'The owner review covers 45 gold, 40 answer, 30 source and 10 decision cards, not every gold record and not blanket source verification. The blind AI sample was chosen to be rich in failures, so its counts are not a population accuracy estimate. No endorsed-without-review cards are active.',
    table: () => ({caption: 'Review counts', columns: ['Review', 'Group', 'Count'], rows: rows.flatMap(r => r.segments.map(s => [r.label, s.label, s.value]))}),
    draw: (host, c) => shareBars(host, c, {rows, label: 'Review counts by kind', rowH: c.compact ? 60 : 56})
  });
}

const limitsFor = m => [
  ['Most gold labels are still AI drafts', 'Gold v3.5 has 268 cases (237 development, 31 held-out). 45 are owner-reviewed: 43 left unchanged and 2 label changes applied, HO-022 (clarify to answer) and DEV-018 (refuse to clarify). The other 223 are AI drafts.', 'README.md · docs/system-card.md · experiments/gold/CHANGELOG.md'],
  ['Human review is per card and partly circular', 'The owner decided 125 cards: 30 with their own verdict and 95 by agreeing with an AI suggestion. That is not independent inter-rater evidence, and no blinded annotation was run.', 'docs/human-review/owner-review-summary.md · docs/system-card.md'],
  ['Held-out is small and not evidence-independent', '31 cases. 25 of 31 reuse a development evidence id and 15 of 31 reuse their whole set. The r3 gain has an interval that touches or crosses zero.', 'docs/system-card.md · report.json › evaluation.paired'],
  ['Some scores sit on earlier gold versions', `Development rows use ${goldOf(m.evalRow('dev-A3', 'gpt-6-luna')).label} and held-out rows ${goldOf(m.heldRow('r3', 'gpt-6-luna')).label}, the latter after three post-run edits that lowered or kept scores. The v3.5 label changes (HO-022, DEV-018) await rescoring from saved outputs wherever a row is not already on v3.5, with no new generation. The original freeze is preserved.`, 'experiments/heldout/FREEZE.md · README.md · experiments/gold/CHANGELOG.md'],
  ['T-I06 is open', 'A planted false figure in a passage is cited and passes the quote and number checks. The cross-check against validated statistics is proposed, not built.', 'docs/system-card.md'],
  ['The ingestion scanner misses paraphrase', 'All five paraphrased malicious probes bypassed it. Zero scanner hits does not certify a source as safe.', 'docs/human-review/independent-ai-review-m1-2.md'],
  ['Extraction has known defects', 'In sampled passages, 1 of 16 lost a note boundary and 2 of 4 HTML passages flattened superscripts. Some feedback-form blocks are garbled. No corpus-wide count is claimed. A fix exists on an unmerged branch and is unevaluated.', 'docs/human-review/ai-pre-review-passage-spot-check.md'],
  ['The dataset employment basis is unverified', 'The sector dataset total sits above MOM\u2019s final figure. Migrant domestic workers may explain it, but that is an inference.', 'docs/data-sheet.md › section 5'],
  ['The judge shares a provider with the generators', 'Its errors may correlate with theirs, and a zero unsupported-claim rate on a selected sample does not prove safety.', 'docs/evaluation-report.md › Judge and uncertainty'],
  ['Costs are estimates', 'List prices dated 30 October 2026, without cached-input discounts. Latency is saved wall time from the recorded runs.', 'docs/system-card.md › Architecture and models']
];

function limitCards(m) {
  const wrap = el('div', 'pr-limit-grid');
  limitsFor(m).forEach(([title, text, src], i) => {
    const card = el('article', `pr-limit pr-reveal${i === 4 ? ' is-open' : ''}`);
    card.append(el('span', 'pr-limit-no', String(i + 1).padStart(2, '0')), el('h5', 'pr-limit-title', title), el('p', '', text), evi(src));
    wrap.append(card);
  });
  return wrap;
}

export function renderLimits(m, ctx) {
  const ch = chapter({
    id: 'limits', no: 8, eyebrow: 'Human review and limits', title: 'What has been checked, and what has not',
    lede: 'Most scores here compare the system with AI-drafted labels using an AI judge. Human review has started and is partial. This chapter says exactly how far it goes.'
  });
  const review = section('Human review status');
  review.append(reviewFigure().root);
  ch.body.append(review);
  const limits = section('Known limitations', 'Each is documented in the repository. None is hidden in a footnote.');
  limits.append(limitCards(m));
  const rec = [...(m.report?.limitations || []), ...(m.section('evaluation').limitations || [])];
  if (rec.length) limits.append(details('Limitations recorded in report.json', list(rec), evi('report.json › limitations · evaluation.limitations')));
  ch.body.append(limits);
  return ch.root;
}

const NEXT = [
  ['Rescore on gold v3.5, then rerun held-out on frozen gold', 'Rescore the saved outputs on v3.5, with no new generation. Then rerun held-out on frozen, reviewed gold. The current r3 comparison is inconclusive and was scored after post-run edits.', 'Success: a paired interval for r3 minus hybrid that excludes zero, or a clear null.'],
  ['Cross-check passage figures against the statistics', 'Closes T-I06. Compare a figure in a cited passage with the validated observation for the same series, period and vintage, and surface genuine conflicts instead of overwriting them.', 'Success: the planted-figure cases fail safely, with no new false conflicts on the development set.'],
  ['Add independent review', '223 gold cases are still drafts, and 95 owner decisions agreed with an AI suggestion. Add blinded, independent annotation, then promote reviewed gold from draft.', 'Success: named independent reviewers on every gold case used in a reported metric.'],
  ['Evaluate the extraction fixes', 'The branch lifts passage counts and removes garbled blocks, but 61 gold passage ids need migration. It needs its own retrieval and answer evaluation.', 'Success: retrieval and answer metrics on the migrated gold, reported next to the current ones.'],
  ['Replace the heuristic scanner', 'Paraphrased attacks get through. Add model-assisted screening and test it on a larger, human-written set.', 'Success: paraphrase probes caught at a measured rate, with the false-positive cost reported.'],
  ['Soften the period filter', 'A later release can restate an earlier quarter, and a hard filter can exclude it. Test a filter that widens when the pool is weak.', 'Success: fewer filter-related misses without losing the R3 gain.']
];

export function renderNext(m, ctx) {
  const ch = chapter({
    id: 'next', no: 9, eyebrow: 'Next', title: 'What I would do next',
    lede: 'Six steps, in order of how much they would change what can be claimed. Each names the result that would show it worked.'
  });
  const ol = el('ol', 'pr-next');
  NEXT.forEach(([title, text, success], i) => {
    const li = el('li', 'pr-next-item pr-reveal');
    li.append(el('span', 'pr-next-no', String(i + 1)), el('h5', 'pr-next-title', title), el('p', '', text), el('p', 'pr-next-success', success));
    ol.append(li);
  });
  ch.body.append(ol);
  const reproduce = callout({
    tone: 'note', title: 'Check any number yourself',
    text: 'Turn on \u201cShow the evidence\u201d at the top of this page to see the report field or file behind each number. The report is rebuilt from committed artifacts with: uv run labourlens build-report.',
    src: 'README.md · docs/deploy.md'
  });
  ch.body.append(reproduce);
  return ch.root;
}
