import {el, fmt, finite, figure, dotPlot, dumbbell, columns, heatmap} from '../charts.js';
import {chapter, section, grid, stat, callout, segmented} from './ui.js';
import {FAMILIES, FAMILY_LABEL} from './model.js';

const CASES = 24; // size of the early development set behind experiments E1 to E7

const asCases = rate => Math.round(rate * CASES);

function methodFigure(m) {
  const spec = [
    ['dev-dense-E6', 'merge120 bm25', 'BM25', 'merge120 chunks', 'c6'], ['dev-dense-E6', 'merge120 dense', 'Dense', 'merge120 chunks', 'c3'], ['dev-dense-E6', 'merge120 hybrid-rrf', 'Hybrid', 'merge120 chunks', 'c1'],
    ['dev-dense-E6', 'merge200 bm25', 'BM25', 'merge200 chunks', 'c6'], ['dev-dense-E6', 'merge200 dense', 'Dense', 'merge200 chunks', 'c3'], ['dev-dense-E6', 'merge200 hybrid-rrf', 'Hybrid', 'merge200 chunks', 'c1']
  ];
  const rows = spec.map(([group, name, label, sub]) => {
    const row = m.retrievalRow(group, name), x = row?.metrics || {};
    return {label, sub, hit5: x['hit@5'], hit10: x['hit@10'], mrr: x.mrr, n: x.n_cases};
  });
  const best = rows.reduce((a, r) => r.hit10 > a.hit10 ? r : a, rows[0]);
  return figure({
    id: 'fig-methods', title: `${best.label} on ${best.sub} had the best hit@10 (${fmt.pct(best.hit10)}) on ${rows[0].n} early development cases`,
    takeaway: `BM25 alone reaches ${fmt.pct(rows[3].hit10)} on the same chunks. One case is ${(100 / CASES).toFixed(1)} points.`,
    summary: rows.map(r => `${r.label} ${r.sub}: hit@5 ${fmt.pct(r.hit5)}, hit@10 ${fmt.pct(r.hit10)}, MRR ${fmt.num(r.mrr, 3)}`).join('. '),
    source: {data: 'report.json › retrieval.rows[dev-dense-E6/*].metrics.{hit@5,hit@10,mrr}', files: ['experiments/runs/dev-dense-E6/*.metrics.json']},
    note: `n=${rows[0].n} text cases. Small set: treat gaps of one or two cases as noise.`,
    table: () => ({caption: 'Early development set, hit rates', columns: ['Method', 'Chunks', 'hit@5', 'hit@10', 'MRR'], rows: rows.map(r => [r.label, r.sub, r.hit5, r.hit10, r.mrr])}),
    draw: (host, c) => dumbbell(host, c, {
      rows: rows.map(r => ({label: r.label, sub: r.sub, points: [{key: 'h5', label: 'hit@5', value: r.hit5, cls: 'c3'}, {key: 'h10', label: 'hit@10', value: r.hit10, cls: r === best ? 'brass' : 'c1'}],
        lines: [`${r.label}, ${r.sub}`, `hit@5: ${fmt.pct(r.hit5)} (${asCases(r.hit5)}/${CASES})`, `hit@10: ${fmt.pct(r.hit10)} (${asCases(r.hit10)}/${CASES})`, `MRR: ${fmt.num(r.mrr, 3)}`]})),
      domain: [0, 1], format: v => fmt.pct(v, 0), label: 'hit@5 and hit@10 by method'
    })
  });
}

function embeddingFigure(m) {
  const items = [['bm25_baseline', 'BM25 baseline', 'c6'], ['text-embedding-3-large', 'text-embedding-3-large', 'c1'], ['text-embedding-3-small', 'text-embedding-3-small', 'c3'], ['text-embedding-ada-002', 'text-embedding-ada-002', 'c5']];
  const rows = items.map(([name, label, cls]) => { const x = m.retrievalRow('dev-dense-E5', name)?.metrics || {}; return {label, cls, hit5: x['hit@5'], mrr: x.mrr, hit10: x['hit@10']}; });
  const top = rows.reduce((a, r) => r.hit5 > a.hit5 ? r : a, rows[0]);
  return figure({
    id: 'fig-embeddings', title: `${top.label} had the highest hit@5 (${fmt.pct(top.hit5)}) across BM25 and three embedding models on ${CASES} cases`,
    takeaway: `The spread among the three embedding models is a few cases, so I named no best model. The runtime uses text-embedding-3-large.`,
    summary: rows.map(r => `${r.label}: hit@5 ${fmt.pct(r.hit5)}, MRR ${fmt.num(r.mrr, 3)}`).join('. '),
    source: {data: 'report.json › retrieval.rows[dev-dense-E5/*].metrics.{hit@5,mrr}', files: ['experiments/runs/dev-dense-E5/*.metrics.json']},
    table: () => ({caption: 'Embedding comparison, merge120 chunks', columns: ['Model', 'hit@5', 'hit@10', 'MRR'], rows: rows.map(r => [r.label, r.hit5, r.hit10, r.mrr])}),
    draw: (host, c) => dotPlot(host, c, {
      rows: rows.map(r => ({label: r.label, value: r.hit5, cls: r.cls, hl: r === top, lines: [r.label, `hit@5: ${fmt.pct(r.hit5)} (${asCases(r.hit5)}/${CASES})`, `hit@10: ${fmt.pct(r.hit10)}`, `MRR: ${fmt.num(r.mrr, 3)}`]})),
      domain: [0, 1], axisTitle: 'hit@5', label: 'hit@5 by embedding model'
    })
  });
}

function ablationFigure(m) {
  const get = (group, name) => m.retrievalRow(group, name)?.metrics?.['hit@10'];
  const base = get('dev-E1-chunking', 'merge120');
  const groups = [
    ['Chunking', 'dev-E1-chunking', [['blocks', 'Document blocks'], ['fixed150', 'Fixed 150 words'], ['merge120+tables', 'Merge 120 + tables'], ['merge120', 'Merge 120 (baseline)'], ['merge200', 'Merge 200']]],
    ['Tokenising', 'dev-E2-tokenisation', [['period_norm_off', 'Period normalising off'], ['stem_on', 'Stemming on'], ['stopwords_off', 'Stopwords kept']]],
    ['BM25 weights', 'dev-E3-bm25-params', [['b=0.4', 'b = 0.4'], ['b=0.9', 'b = 0.9'], ['k1=0.9', 'k1 = 0.9'], ['k1=2.0', 'k1 = 2.0']]],
    ['Combined', 'dev-E4-combined', [['merge200+stopwords_off', 'Merge 200, stopwords kept'], ['merge200+stopwords_off+b=0.4', 'Merge 200, stopwords kept, b = 0.4']]]
  ];
  const rows = [];
  const flat = [];
  groups.forEach(([title, group, entries]) => {
    rows.push({group: true, label: title});
    entries.forEach(([name, label]) => {
      const v = get(group, name);
      const delta = finite(v) && finite(base) ? asCases(v) - asCases(base) : null;
      const row = {label, value: v, cls: 'c1', delta, cross: false, lines: [label, `hit@10: ${fmt.pct(v)} (${asCases(v)}/${CASES})`, `vs baseline: ${delta === null ? 'n/a' : `${fmt.signed(delta)} cases`}`]};
      rows.push(row); flat.push(row);
    });
  });
  const drop = flat.reduce((a, r) => r.delta < a.delta ? r : a, flat[0]), gain = flat.reduce((a, r) => r.delta > a.delta ? r : a, flat[0]);
  flat.forEach(r => { r.hl = r === gain || r === drop; r.cls = r === drop ? 'c4' : 'c1'; });
  return figure({
    id: 'fig-ablation', title: `BM25 settings moved hit@10 by ${fmt.signed(drop.delta)} to ${fmt.signed(gain.delta)} cases against merge120 (${fmt.pct(base)}) on ${CASES} cases`, wide: true,
    takeaway: `Largest fall: ${drop.label.toLowerCase()}. Largest rise: ${gain.label.toLowerCase()}. One or two cases is noise.`,
    summary: flat.map(r => `${r.label}: hit@10 ${fmt.pct(r.value)}, ${fmt.signed(r.delta)} cases`).join('. '),
    source: {data: 'report.json › retrieval.rows[dev-E1..E4/*].metrics.hit@10', files: ['experiments/runs/dev-E1-chunking', 'dev-E2-tokenisation', 'dev-E3-bm25-params', 'dev-E4-combined']},
    note: `n=${CASES} cases. The brass dashed line is the baseline.`,
    table: () => ({caption: 'BM25 ablations, hit@10', columns: ['Setting', 'hit@10', 'Cases vs baseline'], rows: flat.map(r => [r.label, r.value, r.delta])}),
    draw: (host, c) => dotPlot(host, c, {
      rows, domain: [0.3, 0.8], ticks: [0.3, 0.4, 0.5, 0.6, 0.7, 0.8], refs: [{value: base, label: 'baseline'}], valueText: r => `${fmt.pct(r.value)} (${fmt.signed(r.delta)})`, axisTitle: 'hit@10', label: 'hit@10 for each BM25 setting', rowH: 31
    })
  });
}

const RUNG = {
  R0: ['Hybrid baseline', 'BM25 + dense, rank fusion'], R1a: ['Period and release filter', 'hard metadata filter'], R1b: ['Soft metadata boost', 'bonus for matching documents'],
  R2: ['LLM rerank', 'gpt-6-luna, pool of 30'], R3: ['Filter, then rerank', 'the agent default'], 'R1b_x0.5': ['Soft boost, half weight', 'sensitivity'], R1b_x2: ['Soft boost, double weight', 'sensitivity']
};

function ladderFigure(m) {
  const L = m.ladder?.configs;
  if (!L) return null;
  const order = ['R0', 'R1a', 'R1b', 'R2', 'R3'];
  const row = id => { const x = L[id] || {}; return {id, label: RUNG[id][0], sub: RUNG[id][1], value: x['hit@8'], ci: x['hit@8_ci95'], mrr: x['mrr@10'], diff: x['hit@8_diff_vs_R0'], diffCi: x['hit@8_diff_ci95'], bw: x['paired_hit@8_better_worse'], lat: x.added_latency_ms_p50, cost: x.cost_usd_per_query_mean}; };
  const main = order.map(row), extra = ['R1b_x0.5', 'R1b_x2'].map(row);
  const best = main.find(r => r.id === 'R3');
  const all = [...main, ...extra];
  const state = {k: 8};
  const at = (r, k) => L[r.id]?.[`hit@${k}`];
  const mk = r => ({
    label: r.label, sub: r.sub, value: at(r, state.k), ci: state.k === 8 ? r.ci : null, hl: r.id === 'R3', cls: r.id === 'R0' ? 'c6' : 'c1',
    lines: [`${r.id}: ${r.label}`, state.k === 8 ? `hit@8: ${fmt.pct(r.value)}, 95% CI ${fmt.pct(r.ci?.[0])} to ${fmt.pct(r.ci?.[1])}` : `hit@${state.k}: ${fmt.pct(at(r, state.k))} (interval recorded for hit@8 only)`, `MRR@10: ${fmt.num(r.mrr, 3)}`,
      r.id === 'R0' ? 'Baseline' : `hit@8 vs R0: ${fmt.pts(r.diff)} (CI ${fmt.pts(r.diffCi?.[0])} to ${fmt.pts(r.diffCi?.[1])})`,
      r.bw ? `Paired hit@8: better in ${r.bw[0]}, worse in ${r.bw[1]} cases` : '', `Added latency, median: ${fmt.num((r.lat || 0) / 1000, 2)} s`].filter(Boolean)
  });
  const seg = segmented('Cut-off k for hit@k', [3, 5, 8, 10].map(k => ({value: String(k), label: `hit@${k}`})), '8', v => { state.k = +v; sync(); fig.redraw(); });
  const controls = el('div', 'pr-controls');
  controls.append(el('span', 'pr-select-label', 'Cut-off'), seg);
  const sync = () => {
    const k = state.k;
    fig.setTakeaway(k === 8
      ? `R3 minus R0: ${fmt.pts(best.diff)} (95% CI ${fmt.pts(best.diffCi[0])} to ${fmt.pts(best.diffCi[1])}). Each step alone gives less.`
      : `At hit@${k}, the baseline reaches ${fmt.pct(at(main[0], k))} and filter then rerank ${fmt.pct(at(best, k))}. Intervals are recorded for hit@8 only, so none are drawn here.`);
    fig.setSummary(all.map(r => `${r.id} ${r.label}: hit@${k} ${fmt.pct(at(r, k))}`).join('. '));
  };
  const fig = figure({
    id: 'fig-ladder', title: `Filtering then reranking (R3) raised hit@8 from ${fmt.pct(L.R0['hit@8'])} to ${fmt.pct(best.value)} on ${m.ladder.n_cases} development cases`, wide: true, controls,
    takeaway: '', summary: '',
    source: {data: 'report.json › retrieval.ladder.configs[R0..R3].{hit@3,hit@5,hit@8,hit@10,hit@8_ci95,mrr@10}', files: ['experiments/runs/dev-R-V31/summary.json']},
    note: `hit@k: a gold passage is inside the top k chunks. n=${m.ladder.n_cases} answerable development text cases, current corpus v3.1 and gold v3.6. Frozen corpus-v1 history remains in the report data. Whiskers are 95% bootstrap intervals (hit@8 only). Labels are AI-drafted and an LLM also does the reranking, so R2 and R3 may be optimistic. Two definitions of hit@8 exist: the chunk-level one plotted here (a gold passage is in one of the top 8 chunks, and a merged chunk can hold several passages) and a stricter count of gold in the first eight distinct passages of the answer context, ${fmt.pct(m.ladder.end_to_end_context?.R0?.gold_in_first8_context_passages)} for R0 and ${fmt.pct(m.ladder.end_to_end_context?.R3?.gold_in_first8_context_passages)} for R3. The gap between R0 and R3 stays large under both.`,
    table: () => ({caption: 'Retrieval ladder, development cases', columns: ['Config', 'hit@3', 'hit@5', 'hit@8', 'hit@10', 'hit@8 CI low', 'hit@8 CI high', 'MRR@10', 'Gold passages covered @8'], rows: all.map(r => [`${r.id} ${r.label}`, L[r.id]['hit@3'], L[r.id]['hit@5'], L[r.id]['hit@8'], L[r.id]['hit@10'], r.ci?.[0], r.ci?.[1], r.mrr, L[r.id]['gold_passage_coverage@8']])}),
    draw: (host, c) => dotPlot(host, c, {rows: [...main.map(mk), {group: true, label: 'Soft-boost weight, for sensitivity'}, ...extra.map(mk)], domain: [0, 1], axisTitle: `hit@${state.k}`, label: `hit@${state.k} by retrieval configuration`, rowH: c.compact ? 42 : 44})
  });
  sync();
  return fig;
}

function sliderFigure(m) {
  const H = m.ladder?.first_relevant_rank_histogram;
  if (!H?.R0 || !H?.R3) return null;
  const cats = [...Array.from({length: 10}, (_, i) => String(i + 1)), 'miss'];
  const take = id => cats.map(k => H[id][k === 'miss' ? '0' : k] ?? 0);
  const before = take('R0'), after = take('R3');
  const slider = el('input', 'pr-range');
  slider.type = 'range'; slider.min = '0'; slider.max = '100'; slider.value = '100'; slider.step = '1';
  slider.setAttribute('aria-label', 'Fade filter then rerank in over the hybrid baseline');
  const label = el('label', 'pr-range-wrap');
  label.append(el('span', 'pr-range-end', 'Hybrid baseline only (R0)'), slider, el('span', 'pr-range-end', 'Filter, then rerank over the baseline (R3)'));
  let stage = null;
  const apply = () => { if (stage) stage.style.setProperty('--mix', String(+slider.value / 100)); };
  slider.addEventListener('input', apply);
  const fig = figure({
    id: 'fig-rank-shift', title: `R3 puts the first relevant chunk at rank 1 in ${after[0]} of ${after.reduce((a, b) => a + b, 0)} cases, up from ${before[0]} with R0`,
    takeaway: `No relevant chunk in the top 10: ${before[10]} cases with R0, ${after[10]} with R3.`,
    summary: `Rank of the first relevant chunk, counts of cases. Baseline: ${cats.map((k, i) => `${k}: ${before[i]}`).join(', ')}. Filter then rerank: ${cats.map((k, i) => `${k}: ${after[i]}`).join(', ')}.`,
    source: {data: 'report.json › retrieval.ladder.first_relevant_rank_histogram[R0, R3]', files: ['experiments/runs/dev-R-V31/summary.json']},
    note: 'Counts of the 128 development cases. "None" means no relevant chunk in the top 10. Drag the slider to fade the after state (green) in over the before state (grey).',
    controls: label,
    table: () => ({caption: 'First relevant rank, cases', columns: ['Rank', 'R0 hybrid', 'R3 filter then rerank'], rows: cats.map((k, i) => [k === 'miss' ? 'Not in top 10' : `Rank ${k}`, before[i], after[i]])}),
    draw: (host, c) => {
      stage = el('div', 'pr-compare');
      const a = el('div', 'pr-compare-layer is-before'), b = el('div', 'pr-compare-layer is-after');
      a.setAttribute('inert', '');
      a.setAttribute('aria-hidden', 'true');
      stage.append(a, b);
      host.append(stage);
      const mkCtx = () => ({width: c.width, compact: c.compact, tip: c.tip, legend: () => {}});
      const common = {categories: cats.map(k => k === 'miss' ? 'None' : k), max: 120, yTitle: 'Cases', yFormat: fmt.int, tipTitle: (cat, i) => cats[i] === 'miss' ? 'Not in top 10' : `First relevant chunk at rank ${cat}`, label: 'First relevant rank', height: c.compact ? 230 : 290};
      columns(a, mkCtx(), {...common, series: [{key: 'r0', label: 'R0', cls: 'c6', values: before}]});
      columns(b, mkCtx(), {...common, series: [{key: 'r3', label: 'R3', cls: 'c1', values: after, hl: [0]}], extraLines: cats.map((k, i) => [`Baseline R0: ${before[i]} cases`]), tipFormat: v => `${v} cases`});
      const tags = el('div', 'pr-compare-tags');
      tags.append(el('span', 'pr-tag is-before', 'Grey: hybrid, R0'), el('span', 'pr-tag is-after', 'Green: filter then rerank, R3'));
      stage.append(tags);
      apply();
    }
  });
  return fig;
}

function familyHeat(m) {
  const L = m.ladder?.configs;
  if (!L) return null;
  const cols = ['R0', 'R1a', 'R1b', 'R2', 'R3'];
  const rows = FAMILIES.map(f => ({
    label: FAMILY_LABEL[f],
    cells: cols.map(id => { const e = L[id]?.['by_family_hit@8']?.[f]; return e ? {value: e['hit@8'], n: e.n, lines: [`${FAMILY_LABEL[f]}, ${id}`, `hit@8: ${fmt.pct(e['hit@8'])}`, `${e.n} cases`]} : null; })
  }));
  const rev = L.R3?.['by_family_hit@8']?.revision_conflict, rev0 = L.R0?.['by_family_hit@8']?.revision_conflict;
  return figure({
    id: 'fig-retrieval-family', title: rev && rev0 ? `Revision-conflict questions gained most: hit@8 rose from ${fmt.pct(rev0['hit@8'], 1)} to ${fmt.pct(rev['hit@8'], 1)} with R3` : 'hit@8 by question family',
    takeaway: 'Strata are small; n is in each cell.',
    summary: rows.map(r => `${r.label}: ${r.cells.map((c, i) => `${cols[i]} ${c ? fmt.pct(c.value) : 'n/a'}`).join(', ')}`).join('. '),
    source: {data: 'report.json › retrieval.ladder.configs[*].by_family_hit@8', files: ['experiments/runs/dev-R-V31/summary.json']},
    table: () => ({caption: 'hit@8 by family', columns: ['Family', ...cols], rows: rows.map(r => [r.label, ...r.cells.map(c => c ? `${c.value} (n=${c.n})` : '')])}),
    draw: (host, c) => heatmap(host, c, {cols: cols.map(id => ({label: id})), rows, label: 'hit@8 by question family and configuration'})
  });
}

function hintFigure(m) {
  const L = m.ladder?.configs;
  if (!L) return null;
  const ids = ['R0', 'R1a', 'R2', 'R3'];
  const cls = {R0: 'c6', R1a: 'c3', R2: 'c5', R3: 'c1'};
  const rows = [['has_hint', 'Question names a period or release'], ['no_hint', 'No period or release named']].map(([key, label]) => {
    const n = L.R0?.['by_hint_hit@8']?.[key]?.n;
    return {label, sub: `n=${n}`, points: ids.map(id => ({key: id, label: id, value: L[id]?.['by_hint_hit@8']?.[key]?.['hit@8'], cls: id === 'R3' ? 'brass' : cls[id]})),
      lines: [label, `${n} cases`, ...ids.map(id => `${id}: ${fmt.pct(L[id]?.['by_hint_hit@8']?.[key]?.['hit@8'])}`)]};
  });
  const h = rows[0].points, nh = rows[1].points;
  return figure({
    id: 'fig-hint', title: `With a period or release named, hit@8 rose from ${fmt.pct(h[0].value)} to ${fmt.pct(h[3].value)}; without one the baseline was already ${fmt.pct(nh[0].value)}`,
    takeaway: 'With no period named, the filter has nothing to act on.',
    summary: rows.map(r => `${r.label} (${r.sub}): ${r.points.map(p => `${p.label} ${fmt.pct(p.value)}`).join(', ')}`).join('. '),
    source: {data: 'report.json › retrieval.ladder.configs[*].by_hint_hit@8', files: ['experiments/runs/dev-R-V31/summary.json']},
    table: () => ({caption: 'hit@8 by hint', columns: ['Group', ...ids], rows: rows.map(r => [`${r.label} (${r.sub})`, ...r.points.map(p => p.value)])}),
    draw: (host, c) => dumbbell(host, c, {rows, domain: [0.4, 1], format: v => fmt.pct(v, 0), label: 'hit@8 with and without a period hint'})
  });
}

export function renderRetrieval(m, ctx) {
  const L = m.ladder?.configs;
  const ch = chapter({
    id: 'retrieval',
    title: L ? `Metadata filtering then reranking (R3) raised hit@8 from ${fmt.pct(L.R0['hit@8'])} to ${fmt.pct(L.R3['hit@8'])} on ${m.ladder.n_cases} development cases` : 'Retrieval experiments',
    bullets: [
      'Compared R0 hybrid (BM25 + dense, rank fusion), R1a hard period and release filter, R1b soft boost, R2 LLM rerank, R3 filter then rerank.',
      `Metric: hit@8 with 95% bootstrap intervals. Hybrid was chosen as baseline from ${CASES} earlier cases.`,
      'Caveat: a hard period filter can exclude the right document when a later release restates an earlier quarter.',
      'Caveat: an LLM reranks and an LLM drafted the labels, so R2 and R3 may be optimistic.'
    ]
  });
  const intro = section(L ? `R3 gained ${fmt.pts(L.R3['hit@8_diff_vs_R0'])} hit@8 over R0 (95% CI ${fmt.pts(L.R3['hit@8_diff_ci95']?.[0])} to ${fmt.pts(L.R3['hit@8_diff_ci95']?.[1])}); R1a, R1b and R2 each gained less` : 'Retrieval ladder');
  if (L) {
    const stats = el('div', 'pr-stats');
    stats.append(
      stat({value: L.R0['hit@8'], format: v => fmt.pct(v), label: 'hit@8, hybrid baseline', note: 'R0, 128 development cases', src: 'report.json › retrieval.ladder.configs.R0.hit@8'}),
      stat({value: L.R3['hit@8'], format: v => fmt.pct(v), label: 'hit@8, filter then rerank', note: 'R3, the agent default', tone: 'brass', src: 'report.json › retrieval.ladder.configs.R3.hit@8'}),
      stat({value: m.ladder.end_to_end_context?.R3?.gold_in_context_of_top8_chunks, format: v => fmt.pct(v), label: 'gold passage in the context', note: `R0 was ${fmt.pct(m.ladder.end_to_end_context?.R0?.gold_in_context_of_top8_chunks)}. Built from the top 8 chunks; counting only the first eight distinct passages it is ${fmt.pct(m.ladder.end_to_end_context?.R3?.gold_in_first8_context_passages)} against ${fmt.pct(m.ladder.end_to_end_context?.R0?.gold_in_first8_context_passages)}.`, src: 'report.json › retrieval.ladder.end_to_end_context'}),
      stat({value: L.R3['rerank_latency_s_p50_p95']?.[0], format: v => `${v.toFixed(2)} s`, label: 'median rerank time', note: `95th percentile ${fmt.seconds(L.R3['rerank_latency_s_p50_p95']?.[1])}. Mean $${L.R3.cost_usd_per_query_mean} per query. ${fmt.int(L.R3.rerank_failures)} rerank failures.`, src: 'report.json › retrieval.ladder.configs.R3.{rerank_latency_s_p50_p95,cost_usd_per_query_mean,rerank_failures}'})
    );
    intro.append(stats);
  }
  const lad = ladderFigure(m);
  if (lad) intro.append(lad.root);
  const slider = sliderFigure(m);
  const fam = familyHeat(m), hint = hintFigure(m);
  if (slider) intro.append(slider.root);
  if (fam || hint) intro.append(grid('pr-split', fam?.root, hint?.root));
  ch.body.append(intro);

  const earlier = section(`I chose the hybrid baseline from ${CASES} early cases, where gaps were a few cases`, ['Methods, embedding models and BM25 settings compared on hit@5 and hit@10.', 'Noisy: one case is about 4.2 points.']);
  earlier.append(grid('pr-split', methodFigure(m).root, embeddingFigure(m).root));
  earlier.append(ablationFigure(m).root);
  ch.body.append(earlier);

  ch.body.append(callout({
    tone: 'warn', title: 'Retrieval evaluation limits',
    items: [
      'The labels were AI drafts first and were reviewed afterwards by one person. The ladder above ran on corpus v1. A corpus v2 rerun (X1) found no measurable change. The X2 regression check on corpus v3 did not rerun the ladder.',
      'An LLM reranks and an LLM drafted the labels, so R2 and R3 may look better than they are.',
      'A hard period filter can exclude the right document when a later release restates an earlier quarter. Documented, not fixed.',
      'The development set was inspected many times, so it is not an unbiased estimate for new questions.',
      'Retrieval-only diagnostics now cover 18 original-test and 34 fresh text questions. Strict first-eight-context-passages hit@8: hybrid .167/.500, filter then rerank .778/.941. Literal questions, reused sets and case-only intervals limit interpretation. No demonstrated end-to-end gain.'
    ],
    src: 'docs/evaluation-report.md › Expanded retrieval study · docs/experiments/m6-retrieval-improvements.md'
  }));
  return ch.root;
}
