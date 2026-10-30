// Presentation-only projection of the committed report; never executes experiments.
const node = (tag, className = '', text) => {
  const item = document.createElement(tag);
  if (className) item.className = className;
  if (text !== undefined) item.textContent = text;
  return item;
};
const number = (value, digits = 2) => value.toLocaleString(undefined, {maximumFractionDigits: digits});
const labels = {
  dataset_csv: 'Statistics', report_pdf: 'PDF reports', release_html: 'Release pages',
  n: 'Cases (n)', n_cases: 'Cases (n)', n_answer_cases: 'Answerable cases', n_nonanswer_cases: 'Non-answer cases',
  'hit@5': 'Evidence hit at 5', 'hit@10': 'Evidence hit at 10', 'page_hit@5': 'Page hit at 5',
  'passage_recall@5': 'Passage recall at 5', mrr: 'Mean reciprocal rank',
  latency_ms_p50: 'Median retrieval time', latency_p50_s: 'Median response time', latency_max_s: 'Longest response time',
  behavior_accuracy: 'Expected behavior', valid_rate: 'Valid output', gold_cited_rate: 'Gold evidence cited',
  gold_in_context_rate: 'Gold evidence in context', key_number_recall: 'Key-number recall',
  answers_with_ungrounded_numbers: 'Answers with unsupported numbers', calc_correct_rate: 'Correct calculations',
  cost_per_case_usd: 'Cost per case (USD)', cost_usd: 'Cost (USD)', tool_calls_mean: 'Tool calls per case',
  n_chunks: 'Indexed chunks', 'ctx_words@5': 'Context words at 5', connection_seconds: 'Initial MCP connection',
  identical_datasets: 'Identical dataset results', compared_datasets: 'Datasets compared (n)',
  matching_refusals: 'Matching refusals', different_outputs: 'Different outputs',
  verified_open_licence: 'Open licence verified', commit_raw: 'Raw snapshot may be committed',
  metadata_only: 'Metadata only', dataset_snapshot: 'Dataset snapshot', pass: 'Passed', warn: 'Warning', fail: 'Failed',
  bm25_baseline: 'BM25 baseline', blocks: 'Document blocks', fixed150: 'Fixed 150-word chunks',
  stem_on: 'Stemming on', stopwords_off: 'Stopwords kept', period_norm_off: 'Period normalization off',
};
function label(key) {
  const text = String(key);
  if (/^(gpt-|text-embedding-)/.test(text)) return text;
  const chunk = /^(merge|fixed)(\d+)(.*)$/.exec(text);
  if (chunk) return `${chunk[1] === 'merge' ? 'Merged' : 'Fixed'} ${chunk[2]}-word chunks${chunk[3] ? ` · ${chunk[3].replace(/^\+/, '').replaceAll('_', ' ')}` : ''}`;
  return labels[key] || text.replace(/_/g, ' ').replace(/\.(?!\d)/g, ' / ').replace(/\bpdf\b/gi, 'PDF').replace(/\bcsv\b/gi, 'CSV').replace(/^./, c => c.toUpperCase());
}
function format(value, key = '') {
  if (value === undefined || value === null) return 'Not recorded';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) return 'Not recorded';
    if (/usd|cost/.test(key)) return `$${value.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 5})}`;
    if (/(_ms|ms_)/.test(key)) return `${number(value / 1000, 6)} s`;
    if (/seconds|_s$|_seconds/.test(key)) return `${number(value, 3)} s`;
    if (/rate|accuracy|recall|hit@|case_behavior|gold_cited_given|answers_with_ungrounded/.test(key)) return `${number(value * 100, 1)}%`;
    return number(value, 3);
  }
  return typeof value === 'string' ? value : 'See details';
}
function disclosure(title, content) {
  const details = node('details', 'recorded-details');
  details.append(node('summary', '', title), content);
  return details;
}
function table(rows, columns, title) {
  const wrap = node('div', 'table-scroll');
  const grid = node('table', 'data-table recorded-table');
  grid.append(node('caption', 'small muted', title));
  const header = node('tr');
  columns.forEach(([name]) => {
    const cell = node('th', '', name);
    cell.scope = 'col';
    header.append(cell);
  });
  const head = node('thead'); head.append(header);
  const body = node('tbody');
  rows.forEach(row => {
    const tr = node('tr');
    columns.forEach(([, read]) => {
      const cell = node('td');
      const value = read(row);
      cell.append(value instanceof Node ? value : document.createTextNode(String(value ?? 'Not recorded')));
      tr.append(cell);
    });
    body.append(tr);
  });
  grid.append(head, body); wrap.append(grid);
  return wrap;
}
function stats(parent, entries) {
  if (!entries.length) return;
  const grid = node('div', 'metric-grid');
  entries.forEach(([name, value, key]) => {
    const item = node('div', 'metric');
    item.append(node('span', 'metric-value', format(value, key)), node('span', 'metric-label', name));
    grid.append(item);
  });
  parent.append(grid);
}
function provenance(parent, data) {
  const paths = new Set();
  const collect = item => {
    if (!item || typeof item !== 'object') return;
    if (Array.isArray(item)) { item.forEach(collect); return; }
    if (Array.isArray(item.provenance)) item.provenance.forEach(path => { if (typeof path === 'string') paths.add(path); });
    if (Array.isArray(item.rows)) item.rows.forEach(collect);
  };
  collect(data);
  if (!paths.size) return;
  const list = node('ul', 'detail-list recorded-provenance');
  [...paths].sort().forEach(path => list.append(node('li', '', path)));
  parent.append(disclosure(`Artifacts · ${paths.size}`, list));
}
// The table shows six rows per page.
function paged(parent, rows, columns, title) {
  if (!rows.length) { parent.append(node('p', 'empty-state', 'No rows recorded.')); return; }
  const root = node('div');
  const output = node('div');
  const controls = node('div', 'toolbar recorded-controls');
  let page = 0;
  const status = node('span', 'small muted'); status.setAttribute('aria-live', 'polite');
  const previous = node('button', '', 'Previous'); previous.type = 'button';
  const next = node('button', '', 'Next'); next.type = 'button';
  const draw = () => {
    output.replaceChildren(table(rows.slice(page * 6, page * 6 + 6), columns, title));
    status.textContent = `${page * 6 + 1}–${Math.min(page * 6 + 6, rows.length)} of ${rows.length}`;
    previous.disabled = page === 0; next.disabled = (page + 1) * 6 >= rows.length;
  };
  previous.addEventListener('click', () => { page--; draw(); });
  next.addEventListener('click', () => { page++; draw(); });
  if (rows.length > 6) { controls.append(previous, status, next); root.append(controls); }
  root.append(output); parent.append(root); draw();
}
const hiddenField = key => /(^|_)(id|ids)$|sha256|provenance/.test(key);
function measurementRows(value, prefix = '', rows = []) {
  if (!value || typeof value !== 'object') return rows;
  Object.entries(value).forEach(([key, child]) => {
    if (hiddenField(key)) return;
    const name = prefix ? `${prefix} / ${label(key)}` : label(key);
    if (child && typeof child === 'object') measurementRows(child, name, rows);
    else rows.push({name, value: format(child, key)});
  });
  return rows;
}
function moreMeasurements(parent, value, title = 'Additional measurements') {
  const rows = measurementRows(value);
  if (!rows.length) return;
  const content = node('div');
  paged(content, rows, [['Measurement', row => row.name], ['Value', row => row.value]], 'Additional measurements');
  parent.append(disclosure(title, content));
}
const captions = {
  sources: 'Source snapshots. Open licences cover the statistics only; MOM reports are not redistributed.',
  retrieval: 'A hit at 5 means the expected evidence is among the first five results. Compare configurations within one experiment. The cases are development cases, not held-out.',
  answers: 'Expected behavior covers answering, abstaining and asking for clarification. A citation score does not show that every claim is supported. Cost is recorded USD per case.',
  agent: 'Bounded-workflow experiment results, not a live run. Tool errors, unsupported numbers and operational failures are listed under additional measurements.',
  mcp: 'Warm-session MCP latency against direct calls. The initial connection is reported separately. Matching refusals are not data returns.',
  quality: 'Summary counts cover all checks; the table lists notable checks only. Warnings on coverage, rights and definitions remain open when checks pass.',
  reconciliation: 'Advance-to-final differences are release revisions. Dataset-to-final differences remain an unresolved definition or vintage discrepancy; their cause is not established. The series are not interchangeable.',
  eda: 'Change between first and last observation per series, in its own unit and population. No causal claim or forecast.',
};
function experimentGroup(row) {
  const path = row.provenance?.find(path => path.endsWith('.metrics.json')) || row.id || '';
  const directory = path.split('/').slice(-2, -1)[0] || 'Recorded comparison';
  return label(directory.replace(/^dev-E\d+-/, '').replace(/^answer-dev-/, 'Answer experiment ').replace(/^agent-dev-/, 'Agent experiment ').replaceAll('-', ' '));
}
function experiments(parent, data, key) {
  const rows = Array.isArray(data.rows) ? data.rows : [];
  if (!rows.length) { paged(parent, [], [], 'Recorded experiments'); return; }
  const groups = [...new Set(rows.map(experimentGroup))];
  const controls = node('label', 'toolbar recorded-controls');
  controls.append(node('span', '', 'Experiment'));
  const select = node('select'); select.setAttribute('aria-label', 'Recorded experiment');
  groups.forEach((group, index) => { const option = node('option', '', group); option.value = String(index); select.append(option); });
  controls.append(select);
  const output = node('div');
  parent.append(controls, output);
  const draw = () => {
    output.replaceChildren();
    const selected = rows.filter(row => experimentGroup(row) === groups[Number(select.value)]);
    const metrics = key === 'retrieval'
      ? ['n_cases', 'hit@5', 'passage_recall@5', 'latency_ms_p50']
      : ['n', 'behavior_accuracy', 'gold_cited_rate', 'latency_p50_s', 'cost_per_case_usd'];
    const columns = [['Configuration', row => label(row.label || row.method || 'Configuration')], ...metrics.map(metric => [label(metric), row => format(row.metrics?.[metric], metric)])];
    paged(output, selected, columns, groups[Number(select.value)]);
    const details = node('div');
    selected.forEach(row => {
      const content = node('div');
      paged(content, measurementRows(row.metrics), [['Measurement', item => item.name], ['Value', item => item.value]], 'All metrics for this configuration');
      moreMeasurements(content, row.configuration, 'Configuration settings');
      moreMeasurements(content, row.strata, 'Results by question family');
      provenance(content, row);
      details.append(disclosure(label(row.label || row.method || 'Configuration'), content));
    });
    output.append(disclosure('All metrics and settings', details));
  };
  select.addEventListener('change', draw); draw();
}
function sources(parent, data) {
  const rows = data.rows || [];
  stats(parent, [['Source snapshots', data.metrics?.sources, 'sources'], ...Object.entries(data.metrics?.by_type || {}).map(([key, value]) => [label(key), value, key])]);
  const filter = node('label', 'toolbar recorded-controls'); filter.append(node('span', '', 'Source type'));
  const select = node('select'); select.setAttribute('aria-label', 'Filter source type');
  const all = node('option', '', 'All source types'); all.value = ''; select.append(all);
  [...new Set(rows.map(row => row.type || row.source_type).filter(Boolean))].forEach(type => { const option = node('option', '', label(type)); option.value = type; select.append(option); });
  filter.append(select); const output = node('div'); parent.append(filter, output);
  const sourceLink = row => {
    const title = label(row.source_id || 'Official source').replace(/^Mom /, 'MOM ');
    try {
      const url = new URL(row.url);
      if (url.protocol !== 'https:' || !(url.hostname === 'gov.sg' || url.hostname.endsWith('.gov.sg'))) return title;
      const link = node('a', 'source-link', title); link.href = url.href; link.target = '_blank'; link.rel = 'noopener noreferrer'; return link;
    } catch { return title; }
  };
  const draw = () => {
    output.replaceChildren();
    paged(output, rows.filter(row => !select.value || (row.type || row.source_type) === select.value), [
      ['Source', sourceLink], ['Publisher', row => row.publisher], ['Published', row => row.publication_date],
      ['Release', row => label(row.release_stage || 'Not recorded')], ['Rights', row => label(row.rights_status || row.licence || 'Not recorded')],
    ], 'Official sources and publication rights');
  };
  select.addEventListener('change', draw); draw();
  const details = node('div');
  paged(details, rows, [['Source', sourceLink], ['Licence', row => row.licence || row.licence_id || 'Not recorded'], ['Redistribution', row => label(row.redistribution || 'Not recorded')]], 'Licence and packaging conditions');
  parent.append(disclosure('Licence and redistribution', details));
}
function mcp(parent, data) {
  stats(parent, Object.entries(data.metrics || {}).map(([key, value]) => [label(key), value, key]));
  paged(parent, data.rows || [], [
    ['Latency percentile', row => row.metric === 'latency_p50_ms' ? 'Median (p50)' : row.metric === 'latency_p95_ms' ? '95th percentile (p95)' : label(row.metric)],
    ['Direct call', row => format(row.direct, 'latency_ms')], ['MCP call', row => format(row.mcp, 'latency_ms')],
  ], 'Warm-session latency per call');
  if (data.checks?.length) {
    const content = node('div');
    paged(content, data.checks, [['Protocol check', row => row.label], ['Status', row => label(row.status)]], 'Observed protocol checks');
    parent.append(disclosure('Protocol checks', content));
  }
}
function quality(parent, data) {
  stats(parent, Object.entries(data.metrics || {}).map(([key, value]) => [label(key), value, key]));
  const rows = [...(data.rows || [])].sort((a, b) => ({fail: 0, warn: 1, pass: 2}[a.status] ?? 3) - ({fail: 0, warn: 1, pass: 2}[b.status] ?? 3));
  paged(parent, rows, [['Validation check', row => label(row.id)], ['Outcome', row => label(row.status)]], 'Notable checks, warnings and failures first');
}
function reconciliation(parent, data) {
  paged(parent, data.rows || [], [
    ['Quarter', row => row.period], ['Advance', row => format(row.advance?.value)], ['Final', row => format(row.final?.value)],
    ['Dataset', row => format(row.dataset_total?.value)], ['Final − advance', row => format(row.final_minus_advance)], ['Dataset − final', row => format(row.dataset_minus_final)],
  ], 'Employment-change comparison (persons)');
  const content = node('div');
  paged(content, data.rows || [], [['Quarter', row => row.period], ['Advance published', row => row.advance?.publication_date], ['Final published', row => row.final?.publication_date]], 'Publication dates of compared releases');
  parent.append(disclosure('Release publication dates', content));
}
function fallback(parent, data, key) {
  const rows = Array.isArray(data) ? data : data.rows || [];
  if (rows.some(row => row?.metrics)) { experiments(parent, {...data, rows}, key); return; }
  if (key === 'eda') {
    paged(parent, rows, [['Indicator', row => row.label], ['Period', row => `${row.period_from} to ${row.period_to}`], ['Start', row => format(row.start)], ['End', row => format(row.end)], ['Change', row => format(row.change)], ['Unit', row => row.unit], ['n', row => format(row.observations)]], 'Change between first and last observation');
    return;
  }
  stats(parent, Object.entries(data.metrics || {}).filter(([, value]) => typeof value !== 'object').slice(0, 6).map(([key, value]) => [label(key), value, key]));
  const readable = rows.flatMap((row, index) => typeof row === 'object' && row !== null ? measurementRows(row, row.label || `Record ${index + 1}`) : [{name: `Record ${index + 1}`, value: format(row)}]);
  paged(parent, readable, [['Measurement', row => row.name], ['Value', row => row.value]], 'Recorded measurements');
  moreMeasurements(parent, data.errors, 'Error counts');
}
export function renderRecorded(parent, data, key) {
  const root = node('div', 'recorded-data');
  parent.append(root);
  if (!data || typeof data !== 'object' || data.status === 'missing' || data.status === 'unavailable') {
    root.append(node('p', 'empty-state', 'No committed measurements for this section.')); return;
  }
  if (key === 'sources') sources(root, data);
  else if (['retrieval', 'answers', 'agent'].includes(key)) experiments(root, data, key);
  else if (key === 'mcp') mcp(root, data);
  else if (key === 'quality') quality(root, data);
  else if (key === 'reconciliation') reconciliation(root, data);
  else fallback(root, data, key);
  root.append(node('p', 'callout recorded-caption', captions[key] || 'Recorded measurements from committed artifacts, not a live run.'));
  if (Array.isArray(data.limitations) && data.limitations.length) {
    const list = node('ul', 'detail-list small muted');
    data.limitations.filter(item => typeof item === 'string').forEach(item => list.append(node('li', '', item)));
    root.append(list);
  }
  provenance(root, data);
}
