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
  const box = (x, y, w, h, title, lines, detail, group, {accent = false} = {}) => {
    const node = svgEl('g', {class: 'production-node'});
    node.append(svgEl('rect', {
      x, y, width: w, height: h, rx: 14,
      fill: accent ? 'var(--paper-2)' : 'var(--paper)',
      stroke: accent ? 'var(--accent)' : 'var(--line-strong)',
      'stroke-width': accent ? 2 : 1.5
    }));
    text(node, x + 22, y + 44, title, 32, accent ? '--accent' : '--ink', 600);
    lines.forEach((value, i) => text(node, x + 22, y + 86 + i * 34, value, 26));
    attachTip(node, x + w / 2, title, detail);
    svg.append(node);
    entries.push({group, title, lines, detail});
    return node;
  };

  // A separate enclosure prevents the target design being mistaken for deployed infrastructure.
  const current = svgEl('g');
  current.append(svgEl('rect', {
    x: 10, y: 5, width: 1660, height: 65, rx: 12,
    fill: 'var(--paper-2)', stroke: 'var(--accent)', 'stroke-width': 2
  }));
  text(current, 32, 46, 'Built today', 29, '--accent', 600);
  text(current, 260, 46, 'One Droplet: Caddy → Docker → LabourLens', 27, '--ink', 500);
  text(current, 1100, 46, 'Everything below is proposed.', 25, '--muted');
  attachTip(current, 840, 'Built today', 'The current deployment uses one Droplet, Caddy and Docker. Replication, managed services and the production controls below are proposals, not completed work.');
  svg.append(current);
  entries.push({
    group: 'Current deployment',
    title: 'Built today',
    lines: ['One Droplet', 'Caddy → Docker → LabourLens', 'Everything below is proposed.'],
    detail: 'The current deployment uses one Droplet, Caddy and Docker. Replication, managed services and the production controls below are proposals, not completed work.'
  });

  text(svg, 25, 125, 'Proposed production design', 34, '--ink', 600);
  text(svg, 25, 164, 'A question travels left to right; evidence is read only at answer time.', 26, '--muted');

  const path = 'Proposed request path';
  box(25, 190, 385, 140, 'Protected access', ['CDN, WAF, rate limits', 'SSO, per-user credentials'],
    'Cache public assets, filter hostile requests and limit abuse before traffic reaches the application. Use SSO with short-lived sessions and per-user credentials, and authorise every request. Never cache private answers in a shared CDN.', path);
  box(440, 190, 385, 140, 'API replicas', ['Behind a load balancer', 'Job state kept outside'],
    'Balance requests across stateless API replicas. Keep job state outside the replicas so a reconnecting user can resume their own event stream.', path);
  box(855, 190, 385, 140, 'Queued workers', ['Deadlines and retries', 'Progress streamed to user'],
    'Queue research and ingestion separately. Workers enforce deadlines, limited retries and cancellation; persisted job events let any API replica stream progress by server-sent events.', path);
  box(1270, 190, 385, 140, 'Model gateway', ['Budgets, PII redaction', 'Evaluated-model failover'],
    'Redact personal data before provider calls. Enforce user budgets, isolate caches by access scope and version, and fail over only to models that have been evaluated.', path, {accent: true});
  line('M410 260 H440');
  line('M825 260 H855');
  line('M1240 260 H1270');

  // Workers reach evidence through read-only services, not arbitrary network destinations.
  text(svg, 330, 402, 'Read-only evidence, versioned', 28, '--ink', 600);
  line('M1047 330 V360 H272 V420');
  line('M1047 360 V420');
  line('M1047 360 H1412 V420');
  const evidence = 'Read-only evidence';
  box(25, 420, 495, 140, 'Versioned sources', ['Immutable snapshots, checksums', 'Rights-aware access'],
    'Preserve immutable source snapshots and checksums. Restrict PDFs and extracted text according to source rights; do not assume public availability permits redistribution.', evidence);
  box(592, 420, 495, 140, 'Search and statistics', ['Hybrid BM25 + dense index', 'Versioned Parquet, exact maths'],
    'Keep keyword and vector indexes on the same evidence version and apply access and release filters before retrieval, keeping passage provenance for every citation. Store validated observations as versioned Parquet with definitions, units and revision status, and run read-only deterministic calculations.', evidence);
  box(1160, 420, 495, 140, 'Read-only MCP service', ['Separate network boundary', 'Allowlists, no write access'],
    'Expose typed read-only tools from a separate service. Enforce service identity, schemas, timeouts and network policy; treat all returned content as untrusted.', evidence);

  // These controls span the whole environment rather than forming steps in an answer.
  const around = svgEl('g', {class: 'production-node'});
  around.append(svgEl('rect', {x: 25, y: 600, width: 1630, height: 80, rx: 14, fill: 'var(--paper)', stroke: 'var(--line-strong)', 'stroke-width': 1.5, 'stroke-dasharray': '7 5'}));
  text(around, 47, 648, 'Around everything', 30, '--ink', 600);
  text(around, 380, 648, 'Secrets manager · Audit and tracing · Evaluation release gates · Backups with restore drills', 28);
  const aroundDetail = 'Secrets: scoped service credentials, rotated keys, none in prompts or logs. Audit: traces, metrics and alerts for latency, cost, failures and retrieval drift, with redacted access logs. Release gates: deterministic, retrieval, answer and adversarial checks before a canary rollout, with rollback. Backups: encrypted, versioned copies outside the primary failure domain, with practised restores.';
  attachTip(around, 840, 'Around everything', aroundDetail);
  svg.append(around);
  entries.push({group: 'Around everything', title: 'Controls across the environment', lines: ['Secrets manager', 'Audit and tracing', 'Evaluation release gates', 'Backups with restore drills'], detail: aroundDetail});

  text(svg, 25, 710, 'Proposed, not implemented or load-tested. Managed services and recovery targets need workload, rights and security review.', 24, '--muted');
  const mobile = el('div', 'production-mobile');
  let group;
  entries.forEach(entry => {
    if (entry.group !== group) {
      group = entry.group;
      mobile.append(el('h3', 'production-mobile-group', group));
      if (group === 'Proposed request path') {
        mobile.append(el('p', 'production-mobile-flow', 'Protected access → API replicas → queued workers → model gateway. Server-sent events return progress and the final answer.'));
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
