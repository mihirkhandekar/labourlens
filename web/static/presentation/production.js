import {el, svgEl} from '../charts.js';

let graphicSerial = 0;

/** The current deployment and a proposed production topology, not an implementation claim. */
export function productionArchitecture() {
  const width = 1680, height = 720;
  const wrap = el('div', 'production-architecture has-tip-host');
  const entries = [];
  const svg = svgEl('svg', {
    viewBox: `0 0 ${width} ${height}`,
    class: 'production-svg',
    width: '100%',
    height: '100%',
    'font-family': 'inherit',
    role: 'group',
    'aria-label': 'Production architecture. Built today: one Droplet with Caddy and Docker. Everything below is proposed: protected access, replicated APIs, queued workers, isolated evidence services and operational controls.'
  });
  const serial = ++graphicSerial;
  const tip = el('div', 'deck-tip is-svg');
  tip.id = `production-tip-${serial}`;
  tip.setAttribute('role', 'tooltip');
  const defs = svgEl('defs');
  const markerId = `production-arrow-${serial}`;
  const marker = svgEl('marker', {
    id: markerId, viewBox: '0 0 10 10', refX: 9, refY: 5,
    markerWidth: 6, markerHeight: 6, orient: 'auto-start-reverse'
  });
  marker.append(svgEl('path', {d: 'M0 0 10 5 0 10z', fill: 'var(--muted)'}));
  defs.append(marker); svg.append(defs);

  const text = (parent, x, y, value, size = 24, colour = '--ink-2', weight = 400) => {
    const node = svgEl('text', {x, y, fill: `var(${colour})`, 'font-size': size, 'font-weight': weight}, value);
    parent.append(node);
    return node;
  };
  const line = (d, {dashed = false, arrow = true, colour = '--muted'} = {}) => {
    const attrs = {d, fill: 'none', stroke: `var(${colour})`, 'stroke-width': 2};
    if (dashed) attrs['stroke-dasharray'] = '7 6';
    if (arrow) attrs['marker-end'] = `url(#${markerId})`;
    svg.append(svgEl('path', attrs));
  };
  const attachTip = (node, x, label, detail) => {
    node.setAttribute('tabindex', '0');
    node.setAttribute('role', 'img');
    node.setAttribute('aria-label', `${label}. ${detail}`);
    node.setAttribute('aria-describedby', tip.id);
    node.classList.add('is-tipped');
    const show = () => {
      tip.textContent = detail;
      tip.style.setProperty('--at', `${Math.max(12, Math.min(88, x / width * 100))}%`);
      tip.classList.add('is-on');
    };
    const hide = () => tip.classList.remove('is-on');
    node.addEventListener('mouseenter', show);
    node.addEventListener('mouseleave', hide);
    node.addEventListener('focus', show);
    node.addEventListener('blur', hide);
    node.addEventListener('keydown', event => { if (event.key === 'Escape') hide(); });
  };
  const box = (x, y, w, h, title, lines, detail, {accent = false, dashed = false} = {}) => {
    const node = svgEl('g', {class: 'production-node'});
    const attrs = {
      x, y, width: w, height: h, rx: 12,
      fill: accent ? 'var(--paper-2)' : 'var(--paper)',
      stroke: accent ? 'var(--accent)' : 'var(--line-strong)',
      'stroke-width': accent ? 2 : 1.5
    };
    if (dashed) attrs['stroke-dasharray'] = '7 5';
    node.append(svgEl('rect', attrs));
    text(node, x + 17, y + 32, title, 26, accent ? '--accent' : '--ink', 600);
    lines.forEach((value, i) => text(node, x + 17, y + 62 + i * 27, value, 24));
    attachTip(node, x + w / 2, title, detail);
    svg.append(node);
    entries.push({group: y < 300 ? 'Proposed request flow' : y < 550 ? 'Proposed evidence services' : 'Proposed operational controls', title, lines, detail});
    return node;
  };

  // A separate enclosure prevents the target design being mistaken for deployed infrastructure.
  const current = svgEl('g');
  current.append(svgEl('rect', {
    x: 10, y: 5, width: 1660, height: 65, rx: 12,
    fill: 'var(--paper-2)', stroke: 'var(--accent)', 'stroke-width': 2
  }));
  text(current, 32, 46, 'Built today', 29, '--accent', 600);
  text(current, 260, 46, 'Single Droplet: Caddy → Docker → LabourLens', 27, '--ink', 500);
  text(current, 1000, 46, 'Controls below are proposed, not deployed.', 25, '--muted');
  attachTip(current, 840, 'Built today', 'The current deployment uses one Droplet, Caddy and Docker. Replication, managed services and the production controls below are proposals, not completed work.');
  svg.append(current);
  entries.push({
    group: 'Current deployment',
    title: 'Built today',
    lines: ['Single Droplet', 'Caddy → Docker → LabourLens', 'Controls below are proposed, not deployed.'],
    detail: 'The current deployment uses one Droplet, Caddy and Docker. Replication, managed services and the production controls below are proposals, not completed work.'
  });

  text(svg, 25, 119, 'Proposed production architecture', 34, '--ink', 600);
  text(svg, 25, 151, 'Authenticated access, bounded execution and versioned evidence. Read only at answer time.', 25, '--muted');

  // Solid arrows carry requests or evidence. The return path carries server-sent events.
  line('M305 230 H350');
  line('M645 230 H690');
  line('M1000 230 H1045');
  line('M1340 230 H1385');
  line('M1192 285 V319 H167 V285');
  text(svg, 370, 310, 'SSE: task state, tool activity and final answer', 24, '--muted');

  box(25, 175, 280, 110, 'Edge / CDN', ['WAF and rate limits', 'Browser access / TLS'],
    'Cache public assets, filter hostile requests and limit abuse before traffic reaches the application. Never cache private answers in the shared CDN.');
  box(350, 175, 295, 110, 'Identity', ['SSO and user sessions', 'Per-user credentials'],
    'Use SSO with short-lived sessions and per-user credentials. Authorise each request and bind queued jobs, evidence access and event streams to the user.');
  box(690, 175, 310, 110, 'Load balancer', ['Stateless API replicas', 'External job state'],
    'Balance requests across stateless API replicas. Keep job state outside replicas so reconnecting users can resume their own event stream.');
  box(1045, 175, 295, 110, 'Async queue', ['Async workers', 'Research and ingestion'],
    'Queue research and ingestion separately. Workers enforce deadlines, limited retries and cancellation; persisted job events let API replicas stream progress through SSE.');
  box(1385, 175, 270, 110, 'LLM gateway', ['Budget and failover', 'Cache / PII redaction'],
    'Redact personal data before provider calls. Enforce user budgets, isolate caches by access scope and version, and fail over only to evaluated models.', {accent: true});

  // Worker evidence access branches to search and the isolated MCP service, not arbitrary network destinations.
  line('M1192 285 V344 H585 V375');
  line('M1192 344 H965 V375');
  line('M1192 344 H205 V375', {dashed: true});
  text(svg, 1215, 365, 'Evidence services', 24, '--muted', 500);
  line('M1140 440 H1175');
  line('M380 440 H415', {dashed: true});

  box(25, 375, 355, 130, 'Immutable snapshots', ['Object storage and PDFs', 'Rights-aware access', 'Checksums and versions'],
    'Preserve immutable source snapshots and checksums. Restrict PDFs and extracted text according to source rights; do not assume public availability permits redistribution.');
  box(415, 375, 345, 130, 'Managed search', ['BM25 + dense/vector', 'Evidence version filters', 'Passage-level citations'],
    'Keep keyword and vector indexes on the same evidence version. Apply access and release filters before retrieval; retain passage provenance for every citation.');
  box(795, 375, 345, 130, 'Read-only MCP service', ['Separate network boundary', 'Tool and network allowlists', 'No shell or write access'],
    'Expose typed read-only tools from a separate service. Enforce service identity, schemas, timeouts and network policy; treat all returned content as untrusted.');
  box(1175, 375, 480, 130, 'Analytical store', ['Versioned Parquet + DuckDB', 'Read-only analytical queries', 'Deterministic calculations'],
    'Store validated observations as versioned Parquet. Run bounded read-only DuckDB queries and deterministic calculations; keep definitions, units and revision status attached.');

  // These controls span the target environment rather than forming extra steps in an answer.
  line('M25 538 H1655', {dashed: true, arrow: false});
  [217, 632, 1047, 1462].forEach(x => line(`M${x} 538 V555`, {dashed: true, arrow: false}));
  text(svg, 25, 530, 'Cross-cutting controls', 24, '--ink', 600);
  text(svg, 500, 530, 'Dashed: ingestion / control scope. Solid: requests, evidence and SSE.', 24, '--muted');
  box(25, 555, 385, 130, 'Secrets manager', ['Scoped service identities', 'Key rotation / least privilege', 'No secrets in prompts or logs'],
    'Issue scoped credentials to each service, rotate provider keys and avoid shared administrator tokens. Keep secrets out of prompts, traces and source control.', {dashed: true});
  box(440, 555, 385, 130, 'Observability and audit', ['Traces, metrics and alerts', 'Retrieval and answer drift', 'Access and tool audit trail'],
    'Trace requests, tool calls and provider usage. Monitor latency, cost, failures and retrieval drift; retain access audits with redaction and defined retention.', {dashed: true});
  box(855, 555, 385, 130, 'CI/CD evaluation gates', ['Retrieval, safety, MCP checks', 'Versioned release artefacts', 'Canary rollout and rollback'],
    'Gate releases on deterministic, retrieval, answer and adversarial checks. Canary API, worker and index versions together; roll back on breached quality or service limits.', {dashed: true});
  box(1270, 555, 385, 130, 'Backup and recovery', ['Separate failure domain', 'Encrypted versioned backups', 'Restore drills and targets'],
    'Back up source objects, manifests and job state outside the primary failure domain. Rebuild indexes from snapshots and practise restores against agreed recovery targets.', {dashed: true});

  text(svg, 25, 716, 'Proposed, not implemented or load-tested. Managed services and recovery targets need workload, rights and security review.', 24, '--muted');
  const mobile = el('div', 'production-mobile');
  let group;
  entries.forEach(entry => {
    if (entry.group !== group) {
      group = entry.group;
      mobile.append(el('h3', 'production-mobile-group', group));
      if (group === 'Proposed request flow') {
        mobile.append(el('p', 'production-mobile-flow', 'Edge → identity → load balancer and APIs → queued workers → LLM gateway. SSE returns task state, tool activity and the final answer.'));
      }
    }
    const article = el('article', 'production-mobile-entry');
    const lines = el('ul', 'production-mobile-lines');
    entry.lines.forEach(value => lines.append(el('li', '', value)));
    article.append(el('h4', '', entry.title), lines, el('p', 'production-mobile-tip', entry.detail));
    mobile.append(article);
  });
  mobile.append(el('p', 'production-mobile-note', 'Proposed, not implemented or load-tested. Managed services and recovery targets need workload, rights and security review.'));
  wrap.append(svg, mobile, tip);
  return wrap;
}
