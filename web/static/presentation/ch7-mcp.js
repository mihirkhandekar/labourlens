import {el, svgEl, fmt, figure, interactive, dumbbell, shareBars} from '../charts.js';
import {chapter, section, grid, stat, callout, evi, dataTable} from './ui.js';

const TOOLS = ['get_statistic', 'list_datasets', 'describe_dataset', 'get_dimension_values', 'latest_value', 'compare_periods', 'series_summary', 'get_revisions', 'get_provenance'];
const CHECKS = {
  'Timeout refusal': ['Slow server', 'A call that exceeds the 1.5 second limit times out.'],
  'Unavailable refusal': ['Server dies mid-call', 'Reported as unavailable. It is not returned as "no data".'],
  'Version refusal': ['Unexpected version', 'A server that reports another protocol version is refused.'],
  'Schema refusal': ['Broken output schema', 'A result that breaks its own schema is refused.'],
  'Size refusal': ['400 KB response', 'Refused by the response-size cap.'],
  'Secret absent': ['No inherited secrets', 'The server process starts without OPENAI_API_KEY.']
};

function diagramFigure() {
  const boxes = [
    {id: 'agent', title: 'Agent', sub: 'plans and answers', text: 'In the live app, get_series goes through the MCP client (get_statistic only). The accuracy evaluations called statistics directly.'},
    {id: 'client', title: 'MCP client', sub: 'treats the server as untrusted', text: 'Allow-listed launch, minimal environment, name and version checks, tool allow-list, input schemas, deadlines, size caps, typed result validation, and quarantine of instruction-like content.'},
    {id: 'server', title: 'MCP server', sub: '9 tools, 2 resources, 1 prompt', text: 'labourlens-stats. Serves statistics and catalogue metadata only. MOM report text is excluded. Default transport is stdio; an optional loopback HTTP transport needs a bearer token.'},
    {id: 'store', title: 'Validated statistics', sub: 'observations and catalogue', text: 'The same validated observation table the agent uses. Rows carry observation identifiers.'}
  ];
  return figure({
    id: 'fig-mcp', title: `A client treats the ${TOOLS.length}-tool MCP server as untrusted and validates every result`, wide: true,
    takeaway: '',
    summary: `Four boxes in a row: ${boxes.map(b => `${b.title} (${b.sub})`).join(', ')}. A dashed trust boundary sits between the client and the server.`,
    source: {data: 'docs/architecture.md › 5. MCP trust boundary (no report.json field)', files: ['src/labourlens/mcp/server.py', 'src/labourlens/mcp/client.py']},
    draw: (host, c) => {
      const wide = c.width >= 760;
      const bw = wide ? Math.min(190, (c.width - 60) / 4 - 14) : Math.min(260, c.width - 24), bh = 70;
      const H = wide ? 190 : boxes.length * 104 + 14;
      const svg = svgEl('svg', {class: 'pr-svg', width: c.width, height: H, viewBox: `0 0 ${c.width} ${H}`, focusable: 'false'});
      svg.setAttribute('aria-label', 'MCP architecture');
      const pos = boxes.map((b, i) => wide ? {x: 20 + bw / 2 + i * ((c.width - 40 - bw) / 3), y: 96} : {x: c.width / 2, y: 52 + i * 104});
      const arrow = (a, b) => {
        const d = wide ? `M${a.x + bw / 2} ${a.y}L${b.x - bw / 2 - 6} ${b.y}` : `M${a.x} ${a.y + bh / 2}L${b.x} ${b.y - bh / 2 - 6}`;
        const g = svgEl('g', {class: 'pr-edge is-main is-flow'});
        g.append(svgEl('path', {d, class: 'pr-edge-path', fill: 'none'}), svgEl('path', {d, class: 'pr-edge-flow', fill: 'none'}));
        svg.append(g);
      };
      for (let i = 0; i < boxes.length - 1; i++) arrow(pos[i], pos[i + 1]);
      // trust boundary between client and server
      const bx = wide ? (pos[1].x + pos[2].x) / 2 : c.width / 2, by = wide ? 0 : (pos[1].y + pos[2].y) / 2;
      svg.append(wide ? svgEl('line', {x1: bx, x2: bx, y1: 14, y2: H - 14, class: 'pr-boundary'}) : svgEl('line', {x1: 12, x2: c.width - 12, y1: by, y2: by, class: 'pr-boundary'}));
      svg.append(svgEl('text', {x: wide ? bx + 8 : 16, y: wide ? 24 : by - 6, class: 'pr-t pr-t-brass'}, 'trust boundary: the server is untrusted'));
      const items = [];
      boxes.forEach((b, i) => {
        const p = pos[i];
        const g = svgEl('g', {class: `pr-node${b.id === 'client' ? ' is-guard' : ''}`});
        g.append(svgEl('rect', {x: p.x - bw / 2, y: p.y - bh / 2, width: bw, height: bh, rx: 14, class: 'pr-node-shape'}));
        g.append(svgEl('text', {x: p.x, y: p.y - 4, class: 'pr-t pr-node-label', 'text-anchor': 'middle'}, b.title), svgEl('text', {x: p.x, y: p.y + 15, class: 'pr-t pr-t-sub', 'text-anchor': 'middle'}, b.sub));
        svg.append(g);
        const hit = svgEl('rect', {x: p.x - bw / 2, y: p.y - bh / 2, width: bw, height: bh, rx: 14, class: 'pr-row-hit'});
        svg.append(hit);
        items.push({node: hit, lines: [b.title, b.text], ax: p.x, ay: p.y - bh / 2, mark: []});
      });
      host.append(svg);
      interactive(svg, c, items, {label: 'MCP architecture boxes. Use the arrow keys to read each one.'});
    }
  });
}

function catalogue() {
  const wrap = el('div', 'pr-mcp-cat');
  const mk = (title, entries, cls) => {
    const col = el('div', 'pr-mcp-col');
    col.append(el('h5', 'pr-mini-title', title));
    const ul = el('ul', 'pr-mono-list');
    entries.forEach(e => ul.append(el('li', '', e)));
    col.append(ul);
    return col;
  };
  wrap.append(mk('Tools (all read-only)', TOOLS), mk('Resources', ['labourlens://sources', 'labourlens://source/{id}']), mk('Prompt', ['compare_quarters']));
  wrap.append(evi('src/labourlens/mcp/server.py · docs/mcp-demo-transcript.md §1 and §15'));
  return wrap;
}

function checkCards(m) {
  const checks = m.section('mcp').checks || [];
  const wrap = el('div', 'pr-checks');
  checks.forEach(check => {
    const [title, text] = CHECKS[check.label] || [check.label, ''];
    const card = el('article', 'pr-check');
    const head = el('header', 'pr-check-head');
    head.append(el('strong', '', title), el('span', `pr-status is-${check.status === 'observed' ? 'ok' : 'warn'}`, check.status));
    card.append(head, el('p', '', text), evi(`report.json › mcp.checks[${check.label}] · docs/mcp-demo-transcript.md`));
    wrap.append(card);
  });
  return wrap;
}

function latencyFigures(m) {
  const mcp = m.section('mcp'), rows = mcp.rows || [], x = mcp.metrics || {};
  const p50 = rows.find(r => r.metric === 'latency_p50_ms') || rows[0] || {};
  const names = {latency_p50_ms: 'Median per call', latency_p95_ms: 'Slowest 5% of calls'};
  const lat = figure({
    id: 'fig-mcp-latency', title: rows.length ? `MCP took ${p50.mcp} ms at the median per call against ${p50.direct} ms direct` : 'Direct call against MCP, latency per call',
    takeaway: rows.length ? `Connecting once costs ${fmt.num(x.connection_seconds, 2)} s. The live app pays this once at startup; the accuracy evaluations used direct calls.` : 'No latency rows recorded.',
    summary: rows.map(r => `${names[r.metric] || r.metric}: direct ${r.direct} ms, MCP ${r.mcp} ms`).join('. '),
    source: {data: 'report.json › mcp.rows[*].{direct,mcp} · mcp.metrics.connection_seconds', files: ['docs/mcp-demo-transcript.md §17']},
    note: 'Warm-session timings exclude the one-off connection (spawn, initialise, discovery).',
    table: () => ({caption: 'Latency per call (ms)', columns: ['Measure', 'Direct', 'MCP over stdio'], rows: rows.map(r => [names[r.metric] || r.metric, r.direct, r.mcp])}),
    draw: (host, c) => dumbbell(host, c, {
      rows: rows.map(r => ({label: names[r.metric] || r.metric, points: [{key: 'd', label: 'Direct', value: r.direct, cls: 'c1'}, {key: 'm', label: 'MCP', value: r.mcp, cls: 'c3'}], lines: [names[r.metric] || r.metric, `Direct: ${r.direct} ms`, `MCP: ${r.mcp} ms`]})),
      domain: [0, 40], format: v => `${v} ms`, label: 'Direct against MCP latency'
    })
  });
  const same = x.identical_datasets, refused = x.matching_refusals, diff = x.different_outputs, total = x.compared_datasets;
  const parity = figure({
    id: 'fig-mcp-parity', title: `MCP output differed from direct calls on ${diff} of ${total} datasets`,
    takeaway: `${same} identical, ${refused} refused identically as over-large queries.`,
    summary: `${same} identical, ${refused} refused by both, ${diff} different, of ${total}.`,
    source: {data: 'report.json › mcp.metrics.{identical_datasets,matching_refusals,different_outputs,compared_datasets}', files: ['docs/mcp-demo-transcript.md §17']},
    table: () => ({caption: 'Direct against MCP outputs', columns: ['Outcome', 'Datasets'], rows: [['Identical rows', same], ['Both refused', refused], ['Different output', diff]]}),
    draw: (host, c) => shareBars(host, c, {rows: [{label: `${total} datasets`, segments: [{key: 's', label: 'Identical rows', value: same, cls: 'c1'}, {key: 'r', label: 'Both refused the same query', value: refused, cls: 'c2'}, {key: 'd', label: 'Different output', value: diff, cls: 'c4'}]}], rowH: 58, label: 'Parity of direct and MCP results'})
  });
  return [lat, parity];
}

function httpTable() {
  const wrap = el('div', 'pr-http');
  wrap.append(el('h5', 'pr-mini-title', 'Loopback HTTP transport: 7 hardening attempts'));
  wrap.append(dataTable('Hardening checks, from the saved transcript', ['Attempt', 'Result'], [
    ['Request with no token', 'HTTP 401'], ['Request with a wrong token', 'HTTP 401'], ['Valid token, hostile Host header', 'HTTP 421'], ['Valid token, hostile browser Origin', 'HTTP 403'],
    ['Start bound to 0.0.0.0', 'Refused to start (exit 2)'], ['Start with a 5-character token', 'Refused to start (exit 2)'], ['Client pointed at a non-loopback URL', 'Refused: not_allowed']
  ]));
  wrap.append(evi('docs/mcp-demo-transcript.md › 16. Loopback HTTP transport with a bearer token'));
  return wrap;
}

export function renderMcp(m, ctx) {
  const mcp = m.section('mcp'), x = mcp.metrics || {};
  const p50 = (mcp.rows || []).find(r => r.metric === 'latency_p50_ms');
  const ch = chapter({
    id: 'mcp',
    title: p50 && x.compared_datasets != null ? `MCP output differed from direct calls on ${x.different_outputs} of ${x.compared_datasets} datasets, at ${p50.mcp} ms against ${p50.direct} ms per median call` : 'MCP server and client against direct calls',
    bullets: [
      `Server: ${TOOLS.length} read-only tools, 2 resources, 1 prompt. Statistics and catalogue only; no MOM report text.`,
      `Client: treats the server as untrusted; ${(mcp.checks || []).length} scripted failure behaviours observed.`,
      'Comparison: the same queries over the direct route and over MCP. The live app uses MCP for get_series; the accuracy evaluations used the direct route.',
      'Limit: a protocol demo on the cases tried, not an audit.'
    ]
  });
  const stats = el('div', 'pr-stats');
  stats.append(
    stat({value: TOOLS.length, label: 'Read-only tools', note: 'Plus two resources and one prompt', src: 'docs/architecture.md › 5 · src/labourlens/mcp/server.py'}),
    stat({value: (mcp.checks || []).length, label: 'Failure behaviours observed', note: 'Timeout, outage, version, schema, size, secrets', src: 'report.json › mcp.checks'}),
    stat({value: x.different_outputs, label: 'Different outputs, MCP against direct', note: `Of ${x.compared_datasets} datasets compared`, tone: 'brass', src: 'report.json › mcp.metrics.different_outputs'}),
    stat({value: x.connection_seconds, format: v => `${v.toFixed(2)} s`, label: 'One-off connection cost', note: 'Spawn, initialise, discovery', src: 'report.json › mcp.metrics.connection_seconds'})
  );
  const a = section(`${TOOLS.length} read-only tools and 2 resources behind a client that validates results`);
  a.append(stats, diagramFigure().root, catalogue());
  ch.body.append(a);
  const b = section(`${(mcp.checks || []).length} failure behaviours observed against a hostile test server`, ['Scripted runs, one per behaviour.', 'Each is an observed result, not a general guarantee.']);
  b.append(checkCards(m));
  ch.body.append(b);
  const c = section(x.compared_datasets != null ? `MCP matched direct output on ${x.compared_datasets} datasets: ${x.identical_datasets} identical, ${x.matching_refusals} the same refusal` : 'MCP against a direct call');
  const [lat, parity] = latencyFigures(m);
  c.append(grid('pr-split', lat.root, parity.root), httpTable());
  ch.body.append(c);
  ch.body.append(callout({tone: 'warn', title: 'Limits', items: (mcp.limitations || []).concat(['Resource handling is assessed separately from tool-result screening.', 'A protocol demo shows the controls work on the cases tried. It is not an audit.']), src: 'report.json › mcp.limitations · docs/architecture.md › 5'}));
  return ch.root;
}
