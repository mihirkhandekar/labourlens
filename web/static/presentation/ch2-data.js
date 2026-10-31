import {el, fmt, finite, figure, lineChart, columns, dumbbell, shareBars, sparkline} from '../charts.js';
import {chapter, section, grid, callout, chips, evi, selectField, toggle} from './ui.js';

const POP = {resident: 'resident', overall: 'overall', citizen: 'citizen', establishments: 'establishments', unverified_basis: 'basis unverified', not_applicable: 'no population'};
const ADJ = {seasonally_adjusted: 'seasonally adjusted', not_adjusted: 'not adjusted', not_applicable: 'no adjustment', unspecified: 'adjustment not stated'};
const pctText = v => `${v.toFixed(1)}%`;
const setTitle = (fig, text) => { const h = fig.root.querySelector('.pr-fig-title'); if (h) h.textContent = text; };

function definitionChips(m, entries) {
  const palette = ['c1', 'c3', 'c5', 'c6'];
  return chips(entries.map(entry => Array.isArray(entry) ? entry : [entry, null]).filter(([id]) => m.charts[id]).map(([id, label], i) => {
    const chart = m.charts[id];
    return {label: `${label || chart.title}: ${POP[chart.population] || chart.population} · ${ADJ[chart.adjustment] || chart.adjustment} · ${chart.unit}`, cls: `f-${palette[i % 4]}`};
  }));
}

function sourceFigures(m) {
  const rows = m.sources;
  const count = pick => rows.reduce((acc, row) => { const k = pick(row); acc[k] = (acc[k] || 0) + 1; return acc; }, {});
  const type = count(r => r.type), rights = count(r => r.rights_status), stage = count(r => r.release_stage), redistribution = count(r => r.redistribution);
  const seg = (obj, key, label, cls) => ({key: `${label}`, label, value: obj[key] || 0, cls});
  const model = [
    {label: 'Type', segments: [seg(type, 'dataset_csv', 'Dataset snapshot', 'c1'), seg(type, 'report_pdf', 'Report PDF', 'c2'), seg(type, 'release_html', 'Release page', 'c3')]},
    {label: 'Rights status', segments: [seg(rights, 'verified_open_licence', 'Open licence, verified', 'c1'), seg(rights, 'verified_all_rights_reserved', 'All rights reserved, verified', 'c4'), seg(rights, 'unresolved', 'Unresolved', 'c6')]},
    {label: 'Release stage', segments: [seg(stage, 'dataset_snapshot', 'Dataset snapshot', 'c1'), seg(stage, 'final', 'Final', 'c3'), seg(stage, 'advance', 'Advance', 'c2'), seg(stage, 'annual', 'Annual', 'c5')]},
    {label: 'Redistribution', segments: [seg(redistribution, 'commit_raw', 'May be committed', 'c1'), seg(redistribution, 'local_only', 'Kept local', 'c6')]}
  ];
  return figure({
    id: 'fig-sources', title: `${rows.length} source records: ${rights.verified_open_licence || 0} open licence, ${rights.verified_all_rights_reserved || 0} all rights reserved, ${rights.unresolved || 0} unresolved`,
    takeaway: `All-rights-reserved reports stay out of Git. Unresolved rights are on release pages.`,
    summary: model.map(row => `${row.label}: ${row.segments.map(s => `${s.label} ${s.value}`).join(', ')}`).join('. '),
    source: {data: 'report.json › sources.rows[*].{type,rights_status,release_stage,redistribution}', files: ['data/export/sources.json']},
    table: () => ({caption: 'Sources grouped by attribute', columns: ['Grouping', 'Value', 'Sources'], rows: model.flatMap(row => row.segments.map(s => [row.label, s.label, s.value]))}),
    draw: (host, c) => shareBars(host, c, {rows: model, label: 'Sources grouped four ways', rowH: c.compact ? 50 : 52})
  });
}

function provenanceChain(m) {
  const card = m.cards.find(c => c.card_id === 'unemployment_resident_sa') || m.cards[0];
  if (!card) return null;
  const source = m.sources.find(row => row.source_id === card.source_id);
  const steps = [
    ['Publisher', source ? `${source.publisher}, via data.gov.sg` : 'not recorded', source?.url || null],
    ['Snapshot', source ? `${source.snapshot_id}` : 'not recorded', null],
    ['SHA-256', source?.sha256 ? `${source.sha256.slice(0, 16)}…` : 'not recorded', null],
    ['Observation', card.observation_id, null],
    ['Figure shown', `${card.value}% in ${fmt.quarter(card.period)}`, null]
  ];
  const ol = el('ol', 'pr-chain');
  steps.forEach(([label, value, href], i) => {
    const li = el('li', 'pr-chain-step');
    li.append(el('span', 'pr-chain-label', label));
    if (href) { const a = el('a', 'pr-chain-value', value); a.href = href; a.rel = 'noopener noreferrer'; a.target = '_blank'; li.append(a); }
    else li.append(el('span', 'pr-chain-value mono', value));
    if (i < steps.length - 1) li.append(el('i', 'pr-chain-arrow'));
    ol.append(li);
  });
  const wrap = el('div', 'pr-chain-wrap pr-reveal');
  wrap.append(el('h5', 'pr-mini-title', `Trace one number: ${card.label}, ${fmt.quarter(card.period)}`), ol,
    el('p', 'pr-small', 'The trace command looks up the raw cell from an observation id. A matching hash confirms the snapshot is the recorded download.'),
    evi('report.json › summary.cards[unemployment_resident_sa] · sources.rows[resident_unemployment_rate]'));
  return wrap;
}

function qualityFigure(m) {
  const q = m.section('quality');
  const pass = q.metrics?.pass, warn = q.metrics?.warn;
  const warnings = (q.rows || []).filter(r => r.status === 'warn');
  const fig = figure({
    id: 'fig-quality', title: `${fmt.int(pass)} of ${fmt.int((pass || 0) + (warn || 0))} validation checks passed; ${fmt.int(warn)} raised warnings`,
    takeaway: '',
    summary: `${pass} pass, ${warn} warn. No failing check is recorded in the report.`,
    source: {data: 'report.json › quality.metrics · quality.rows', files: ['data/export/quality.json']},
    table: () => ({caption: 'Validation outcomes', columns: ['Outcome', 'Checks'], rows: [['Pass', pass], ['Warn', warn]]}),
    draw: (host, c) => shareBars(host, c, {rows: [{label: `${(pass || 0) + (warn || 0)} checks`, segments: [{key: 'p', label: 'Pass', value: pass || 0, cls: 'c1'}, {key: 'w', label: 'Warn', value: warn || 0, cls: 'c2'}]}], label: 'Validation outcomes', rowH: 56})
  });
  const wrap = el('div', 'pr-warnings pr-reveal');
  wrap.append(el('h5', 'pr-mini-title', 'Warnings'));
  const ul = el('ul', 'pr-warn-list');
  warnings.forEach(w => { const li = el('li'); li.append(el('code', 'pr-path', w.id)); ul.append(li); });
  wrap.append(ul, el('p', 'pr-small', 'Vacancy ratio recomputed from counts differs from the published ratio by up to 0.67; the two come from different surveys. Warning, not error.'), evi('docs/data-sheet.md › section 5'));
  return grid('pr-split', fig.root, wrap);
}

export function renderData(m, ctx) {
  const qm0 = m.section('quality').metrics || {};
  const ch = chapter({
    id: 'data', no: 2, eyebrow: 'The data',
    title: `${m.sources.length} source records, ${fmt.int(qm0.pass)} of ${fmt.int((qm0.pass || 0) + (qm0.warn || 0))} validation checks passed, ${fmt.int(qm0.warn)} warnings`,
    bullets: ['Statistics: data.gov.sg datasets. Reports: MOM.', 'Hashed snapshots; population, adjustment, unit and release status kept in observation metadata.', 'Charts redraw on a selectable window of quarters.']
  });

  const srcRows = m.sources;
  const nCommit = srcRows.filter(r => r.redistribution === 'commit_raw').length;
  const prov = section(`Only ${nCommit} of ${srcRows.length} source records may be committed to Git`, ['Each record carries publisher, date, rights status, release stage and a snapshot hash.']);
  prov.append(grid('pr-split is-wide-left', sourceFigures(m).root, provenanceChain(m)));
  prov.append(qualityFigure(m));
  prov.append(callout({
    tone: 'note', title: 'Reuse and redistribution',
    items: ['Statistical datasets: Singapore Open Data Licence. Attribution kept; no agency endorsement implied.', 'MOM report PDFs: copyright notice reserves rights. PDFs and their text stay local, out of Git.', 'Release pages with unresolved rights are listed as unresolved.'],
    src: 'docs/system-card.md › Data and rights · docs/data-sheet.md'
  }));
  ch.body.append(prov);

  // ---------- EDA ----------
  const eda = section(`Quarterly series over ${m.periods().length} quarters, with a selectable window`, ['Each chart redraws on the same quarters.', 'Units and statistical definitions are labelled on every chart.']);
  const periods = m.periods();
  const state = {from: 0, to: periods.length - 1, nsa: true};
  const options = periods.map((p, i) => ({value: String(i), label: fmt.quarter(p)}));
  const fromField = selectField('From', options, '0', v => { state.from = Math.min(+v, state.to); fromField.select.value = String(state.from); refresh(); });
  const toField = selectField('To', options, String(periods.length - 1), v => { state.to = Math.max(+v, state.from); toField.select.value = String(state.to); refresh(); });
  const nsaToggle = toggle('Show unadjusted series', true, on => { state.nsa = on; refresh(); });
  const bar = el('div', 'pr-controls pr-reveal');
  bar.setAttribute('role', 'group');
  bar.setAttribute('aria-label', 'Window for the charts below');
  bar.append(fromField.root, toField.root, nsaToggle);
  eda.append(bar);
  const win = () => periods.slice(state.from, state.to + 1);
  const slice = id => m.values(id, win());
  const stamp = el('p', 'pr-small pr-window-note');

  // Unemployment
  const unempSeries = () => [
    {key: 'resident_sa', label: 'Resident, adjusted', cls: 'c1', values: slice('unemployment_resident_sa'), focus: true},
    {key: 'overall_sa', label: 'Overall, adjusted', cls: 'c3', values: slice('unemployment_overall_sa')},
    {key: 'citizen_sa', label: 'Citizen, adjusted', cls: 'c5', values: slice('unemployment_citizen_sa')},
    ...(state.nsa ? [{key: 'resident_nsa', label: 'Resident, unadjusted', cls: 'c6', dash: true, values: slice('unemployment_resident_nsa')}] : [])
  ];
  const gap = () => {
    const a = slice('unemployment_resident_sa'), b = slice('unemployment_resident_nsa');
    let best = null;
    a.forEach((v, i) => { if (finite(v) && finite(b[i])) { const d = Math.abs(b[i] - v); if (!best || d > best.d) best = {d, i, v, n: b[i]}; } });
    return best;
  };
  const fUnemp = figure({
    id: 'fig-unemployment', title: 'Unemployment rates, by population and adjustment', wide: true,
    takeaway: '', summary: '',
    source: {data: 'report.json › charts[unemployment_*_sa|nsa].points', files: ['data/export/series.json']},
    table: () => ({caption: 'Unemployment rate (percent) by quarter', columns: ['Quarter', ...unempSeries().map(s => s.label)], rows: win().map((p, i) => [fmt.quarter(p), ...unempSeries().map(s => finite(s.values[i]) ? s.values[i] : '')])}),
    aside: definitionChips(m, [['unemployment_resident_sa', 'Resident, adjusted'], ['unemployment_overall_sa', 'Overall, adjusted'], ['unemployment_citizen_sa', 'Citizen, adjusted'], ['unemployment_resident_nsa', 'Resident, unadjusted']]),
    draw: (host, c) => {
      const series = unempSeries(), g = gap();
      lineChart(host, c, {
        periods: win(), series, yFormat: v => `${v.toFixed(1)}%`, yTitle: 'Unemployment rate, percent', label: 'Unemployment rates by quarter',
        notes: state.nsa && g ? [{index: g.i, value: g.n, text: `Unadjusted ${pctText(g.n)} vs adjusted ${pctText(g.v)}`}] : []
      });
    }
  });

  // Vacancies
  const fRatio = figure({
    id: 'fig-vacancy-ratio', title: 'Vacancies per unemployed person',
    takeaway: '', summary: '',
    source: {data: 'report.json › charts[vacancy_ratio].points', files: ['data/export/series.json']},
    table: () => ({caption: 'Vacancies per unemployed person (ratio)', columns: ['Quarter', 'Ratio'], rows: win().map((p, i) => [fmt.quarter(p), slice('vacancy_ratio')[i] ?? ''])}),
    aside: definitionChips(m, ['vacancy_ratio']),
    draw: (host, c) => {
      const values = slice('vacancy_ratio');
      const last = values.map((v, i) => finite(v) ? i : -1).filter(i => i >= 0).pop();
      lineChart(host, c, {
        periods: win(), series: [{key: 'ratio', label: 'Ratio', cls: 'c1', values, focus: true}], yFormat: v => v.toFixed(2), rightLabel: 20, label: 'Vacancies per unemployed person',
        yTitle: 'Vacancies per unemployed person', notes: last !== undefined ? [{index: last, value: values[last], text: `${values[last].toFixed(2)} in ${fmt.quarter(win()[last])}`, dy: -14}] : []
      });
    }
  });
  const fVac = figure({
    id: 'fig-vacancies', title: 'Job vacancies',
    takeaway: '', summary: '',
    source: {data: 'report.json › charts[job_vacancies].points', files: ['data/export/series.json']},
    table: () => ({caption: 'Job vacancies (count)', columns: ['Quarter', 'Vacancies'], rows: win().map((p, i) => [fmt.quarter(p), slice('job_vacancies')[i] ?? ''])}),
    aside: definitionChips(m, ['job_vacancies']),
    draw: (host, c) => {
      const values = slice('job_vacancies').map(v => finite(v) ? v : null);
      const low = values.reduce((a, v, i) => finite(v) && (a < 0 || v < values[a]) ? i : a, -1);
      columns(host, c, {
        categories: win().map(p => `Q${p.slice(-1)}`), catSub: win().map(p => p.slice(-1) === '1' ? p.slice(0, 4) : ''), series: [{key: 'v', label: 'Vacancies', cls: 'c3', values, hl: low >= 0 ? [low] : []}],
        yFormat: v => v >= 1000 ? `${Math.round(v / 1000)}k` : String(v), tipFormat: fmt.int, tipTitle: (cat, i) => fmt.quarter(win()[i]), yTitle: 'Vacancies', label: 'Job vacancies by quarter'
      });
    }
  });

  // Retrenchments
  const fRetr = figure({
    id: 'fig-retrenchments', title: 'Retrenched employees: permanent and term contract', wide: true,
    takeaway: '', summary: '',
    source: {data: 'report.json › charts[retrenched_permanent|retrenched_term_contract|retrenchments].points', files: ['data/export/series.json']},
    table: () => ({caption: 'Retrenched employees (persons)', columns: ['Quarter', 'Permanent', 'Term contract', 'Total'], rows: win().map((p, i) => [fmt.quarter(p), slice('retrenched_permanent')[i] ?? '', slice('retrenched_term_contract')[i] ?? '', slice('retrenchments')[i] ?? ''])}),
    aside: definitionChips(m, [['retrenchments', 'Retrenched employees, total']]),
    draw: (host, c) => {
      const total = slice('retrenchments');
      const top = total.reduce((a, v, i) => finite(v) && (a < 0 || v > total[a]) ? i : a, -1);
      columns(host, c, {
        categories: win().map(p => `Q${p.slice(-1)}`), catSub: win().map(p => p.slice(-1) === '1' ? p.slice(0, 4) : ''), stacked: true,
        series: [{key: 'perm', label: 'Permanent', cls: 'c1', values: slice('retrenched_permanent'), hl: top >= 0 ? [top] : []}, {key: 'term', label: 'Term contract', cls: 'c3', values: slice('retrenched_term_contract'), hl: top >= 0 ? [top] : []}],
        yFormat: fmt.int, tipTitle: (cat, i) => fmt.quarter(win()[i]), yTitle: 'Persons', label: 'Retrenched employees by quarter'
      });
    }
  });

  // Revisions
  const rec = m.section('reconciliation').rows || [];
  const fRev = figure({
    id: 'fig-revisions', title: 'One quarter, three employment-change numbers', wide: true,
    takeaway: '', summary: '',
    source: {data: 'report.json › reconciliation.rows[*].{advance,final,dataset_total}.value', files: ['data/export/reconciliation.json']},
    table: () => ({caption: 'Employment change by quarter (persons)', columns: ['Quarter', 'Advance release', 'Final report', 'Sector dataset total', 'Final minus advance', 'Dataset minus final'], rows: visibleRec().map(r => [fmt.quarter(r.period), r.advance.value, r.final.value, r.dataset_total.value, r.final_minus_advance, r.dataset_minus_final])}),
    draw: (host, c) => {
      const data = visibleRec();
      dumbbell(host, c, {
        rows: data.map(r => ({
          label: fmt.quarter(r.period), sub: `revision ${fmt.signed(r.final_minus_advance)}`,
          points: [{key: 'adv', label: 'Advance release', value: r.advance.value, cls: 'c3'}, {key: 'fin', label: 'Final report', value: r.final.value, cls: 'c1'}, {key: 'ds', label: 'Sector dataset total', value: r.dataset_total.value, cls: 'c2'}],
          lines: [fmt.quarter(r.period), `Advance release: ${fmt.int(r.advance.value)} (${r.advance.publication_date})`, `Final report: ${fmt.int(r.final.value)} (${r.final.publication_date})`, `Sector dataset total: ${fmt.int(r.dataset_total.value)}`, `Final minus advance: ${fmt.signed(r.final_minus_advance)}`, `Dataset minus final: ${fmt.signed(r.dataset_minus_final)}`]
        })),
        format: v => `${Math.round(v / 1000)}k`, domain: [0, 35000], label: 'Employment change: advance, final and dataset'
      });
    }
  });
  const visibleRec = () => rec.filter(r => periods.indexOf(r.period) >= state.from && periods.indexOf(r.period) <= state.to);

  const refresh = () => {
    const w = win();
    stamp.textContent = `Showing ${fmt.quarter(w[0])} to ${fmt.quarter(w[w.length - 1])} (${w.length} quarters).`;
    // takeaways computed from the visible window
    const g = gap();
    const adj = ['unemployment_resident_sa', 'unemployment_overall_sa', 'unemployment_citizen_sa'].flatMap(id => slice(id)).filter(finite);
    setTitle(fUnemp, g && state.nsa
      ? `The unadjusted resident rate reached ${pctText(g.n)} against ${pctText(g.v)} adjusted in ${fmt.quarter(w[g.i])}`
      : adj.length ? `Adjusted unemployment rates ranged from ${pctText(Math.min(...adj))} to ${pctText(Math.max(...adj))} over ${w.length} quarters` : 'Unemployment rates: no observations in this window');
    fUnemp.setTakeaway('Do not mix adjusted and unadjusted rates.');
    fUnemp.setSummary(`Unemployment rates, ${fmt.quarter(w[0])} to ${fmt.quarter(w[w.length - 1])}. ${unempSeries().map(s => `${s.label}: ${s.values.filter(finite).map(pctText).join(', ')}`).join('. ')}.`);
    const ratio = slice('vacancy_ratio').filter(finite);
    setTitle(fRatio, ratio.length ? `Vacancies per unemployed person ranged from ${Math.min(...ratio).toFixed(2)} to ${Math.max(...ratio).toFixed(2)} over ${ratio.length} quarters` : 'Vacancies per unemployed person: no observations in this window');
    fRatio.setTakeaway('');
    fRatio.setSummary(`Vacancies per unemployed person: ${ratio.join(', ')}.`);
    const vac = slice('job_vacancies').filter(finite);
    setTitle(fVac, vac.length ? `Job vacancies ranged from ${fmt.int(Math.min(...vac))} to ${fmt.int(Math.max(...vac))} over ${vac.length} quarters` : 'Job vacancies: no observations in this window');
    fVac.setTakeaway('');
    fVac.setSummary(`Job vacancies: ${vac.map(fmt.int).join(', ')}.`);
    const total = slice('retrenchments');
    const top = total.reduce((a, v, i) => finite(v) && (a < 0 || v > total[a]) ? i : a, -1);
    const termShare = Math.max(0, ...slice('retrenched_term_contract').map((v, i) => finite(v) && finite(total[i]) && total[i] > 0 ? v / total[i] : 0));
    setTitle(fRetr, top >= 0 ? `Retrenchments peaked at ${fmt.int(total[top])} persons in ${fmt.quarter(w[top])}; term contracts were at most ${(100 * termShare).toFixed(1)}% of a quarter` : 'Retrenched employees: no observations in this window');
    fRetr.setTakeaway('');
    fRetr.setSummary(`Retrenched employees: ${total.filter(finite).map(fmt.int).join(', ')} persons.`);
    const rv = visibleRec();
    if (rv.length) {
      const big = rv.reduce((a, r) => Math.abs(r.final_minus_advance) > Math.abs(a.final_minus_advance) ? r : a, rv[0]);
      const gaps = rv.map(r => r.dataset_minus_final);
      setTitle(fRev, `${fmt.quarter(big.period)} employment change: advance release ${fmt.int(big.advance.value)}, final report ${fmt.int(big.final.value)}`);
      fRev.setTakeaway(`Sector dataset total minus final: ${fmt.signed(Math.min(...gaps))} to ${fmt.signed(Math.max(...gaps))} persons in the quarters shown. Different releases and bases; not merged.`);
      fRev.setSummary(rv.map(r => `${fmt.quarter(r.period)}: advance ${r.advance.value}, final ${r.final.value}, dataset ${r.dataset_total.value}`).join('. '));
    } else {
      setTitle(fRev, 'Advance and final employment-change figures exist for 2025-Q3 to 2026-Q2 only');
      fRev.setTakeaway('Widen the window to see them.');
      fRev.setSummary('No revision data in this window.');
    }
    [fUnemp, fRatio, fVac, fRetr, fRev].forEach(f => f.redraw());
  };

  eda.append(stamp);
  eda.append(fUnemp.root);
  eda.append(grid('pr-split', fRatio.root, fVac.root));
  eda.append(fRetr.root, fRev.root);
  refresh();

  // Findings, computed from the full series.
  const resident = m.values('unemployment_resident_sa', periods).filter(finite), nsa = m.values('unemployment_resident_nsa', periods).filter(finite);
  const retr = m.values('retrenchments', periods), retrTop = retr.reduce((a, v, i) => finite(v) && (a < 0 || v > retr[a]) ? i : a, -1);
  const gaps = rec.map(r => r.dataset_minus_final);
  const findings = el('ol', 'pr-findings pr-reveal');
  const revAbs = rec.map(r => Math.abs(r.final_minus_advance));
  const retrPeak = retrTop >= 0 ? `${fmt.int(retr[retrTop])} persons in ${fmt.quarter(periods[retrTop])}` : '';
  const resRange = resident.length ? `${pctText(Math.min(...resident))} and ${pctText(Math.max(...resident))}` : '';
  const gapRange = rec.length ? `${fmt.int(Math.min(...gaps))} to ${fmt.int(Math.max(...gaps))} persons across ${rec.length} quarters` : '';
  [
    [resident.length && nsa.length ? `Adjusted resident unemployment stayed between ${resRange}; the unadjusted rate ranged from ${pctText(Math.min(...nsa))} to ${pctText(Math.max(...nsa))}` : 'Adjusted and unadjusted rates are different series', 'Stored under separate series identifiers.', 'report.json › charts[unemployment_resident_sa, unemployment_resident_nsa]'],
    [retrTop >= 0 ? `Retrenchments peaked at ${retrPeak}, the highest of ${periods.length} quarters` : 'Retrenchment peak not recorded', retrTop >= 0 ? `Adjusted resident unemployment stayed between ${resRange} over the same period. The data do not show why; I infer no cause.` : 'Not recorded.', 'report.json › charts[retrenchments] · eda.rows[retrenchments]'],
    [rec.length ? `Final figures differ from advance releases by ${fmt.int(Math.min(...revAbs))} to ${fmt.int(Math.max(...revAbs))} persons across ${rec.length} quarters` : 'Advance and final figures differ', rec.length ? 'Answers name the vintage they use.' : 'Not recorded.', 'report.json › reconciliation.rows'],
    [rec.length ? `The sector dataset total ${gaps.every(g => g > 0) ? 'is above' : 'differs from'} MOM\u2019s final figure by ${gapRange}` : 'Sector dataset total and MOM final figure differ', rec.length ? 'MOM\u2019s headline excludes migrant domestic workers; the dataset\u2019s basis is unverified. That this explains the gap is an inference, not a verified fact.' : 'Not recorded.', 'report.json › reconciliation.rows[*].dataset_minus_final · docs/data-sheet.md']
  ].forEach(([title, text, src]) => {
    const li = el('li', 'pr-finding');
    li.append(el('strong', '', title), el('span', '', text), evi(src));
    findings.append(li);
  });
  const findBlock = el('div', 'pr-find-block');
  findBlock.append(el('h5', 'pr-mini-title', 'Four findings'), findings);
  eda.append(findBlock);

  // Series catalogue
  const edaRows = m.section('eda').rows || [];
  const atlas = el('div', 'pr-atlas pr-reveal');
  atlas.append(el('h5', 'pr-mini-title', 'Series catalogue'), el('p', 'pr-small', `${m.section('eda').summary} ${edaRows.length} validated series, with their recorded observation ranges.`));
  const cells = el('ul', 'pr-atlas-grid');
  edaRows.forEach(row => {
    const chart = m.charts[row.id];
    const digits = row.unit === 'ratio' ? 2 : row.unit === 'percent' ? 1 : 0;
    const value = v => row.unit === 'percent' ? `${v.toFixed(1)}%` : row.unit === 'ratio' ? v.toFixed(2) : fmt.int(v);
    const li = el('li', 'pr-atlas-cell');
    li.append(el('span', 'pr-atlas-name', row.label), sparkline((chart?.points || []).map(p => p.value), {width: 132, height: 36}));
    li.append(el('span', 'pr-atlas-val num', `${value(row.start)} \u2192 ${value(row.end)}`), el('span', 'pr-atlas-sub', `${fmt.signed(row.change, digits)}${row.unit === 'percent' ? ' pts' : ''} · range ${value(row.minimum)} to ${value(row.maximum)}`));
    li.append(el('span', 'pr-atlas-def', `${POP[chart?.population] || ''} · ${ADJ[chart?.adjustment] || ''} · ${row.unit}`));
    cells.append(li);
  });
  atlas.append(cells, evi('report.json › eda.rows[*] · charts[*].points'));
  eda.append(atlas);
  ch.body.append(eda);
  return ch.root;
}
