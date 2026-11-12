import {el, svgEl} from '../charts.js';
import {withTip} from './graphics.js';

let graphicSerial = 0;

/** The current deployment and a proposed production topology, not an implementation claim. */
export function productionArchitecture() {
  const width = 1680, height = 520;
  const wrap = el('div', 'production-architecture has-tip-host');
  const entries = [];
  const svg = svgEl('svg', {
    viewBox: `0 0 ${width} ${height}`,
    class: 'production-svg',
    width: '100%',
    height: '100%',
    'font-family': 'inherit',
    role: 'group',
    'aria-label': 'Production architecture. Built today: one Droplet with Caddy and Docker. Everything below is proposed: protected access, API and workers, a model gateway, read-only evidence and operational controls.'
  });
  const serial = ++graphicSerial;
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
    const host = withTip(el('div', 'production-tip-host'), detail, `${x > width * .7 ? 'is-production-right ' : ''}is-up`, detail);
    host.tabIndex = -1;
    node.setAttribute('tabindex', '0');
    node.setAttribute('role', 'img');
    node.setAttribute('aria-label', label);
    node.setAttribute('aria-describedby', host.getAttribute('aria-describedby'));
    node.classList.add('is-tipped');
    const show = () => {
      const bounds = node.getBoundingClientRect(), parent = wrap.getBoundingClientRect();
      const scaleX = parent.width / wrap.offsetWidth, scaleY = parent.height / wrap.offsetHeight;
      host.style.left = `${(bounds.left - parent.left) / scaleX}px`;
      host.style.top = `${(bounds.top - parent.top) / scaleY}px`;
      host.style.width = `${bounds.width / scaleX}px`;
      host.classList.add('is-active');
    };
    const hide = () => host.classList.remove('is-active');
    node.addEventListener('mouseenter', show);
    node.addEventListener('mouseleave', hide);
    node.addEventListener('focus', show);
    node.addEventListener('blur', hide);
    node.addEventListener('keydown', event => {
      if (event.key === 'Escape') {
        hide();
        event.preventDefault();
        event.stopPropagation();
      }
    });
    wrap.append(host);
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

  const path = 'Proposed request path';
  box(25, 160, 385, 140, 'Protected access', ['Login, rate limits', 'Per-user credentials'],
    'Authorise every request, use short-lived sessions and never cache private answers in a shared CDN. For example SSO, a web application firewall and rate limits.', path);
  box(440, 160, 385, 140, 'API and workers', ['Stateless replicas', 'Queued jobs with deadlines'],
    'Keep job state outside the API replicas so users can resume their own event streams. Workers enforce deadlines, limited retries and cancellation, and stream progress.', path);
  box(855, 160, 385, 140, 'Model gateway', ['Budgets, redaction', 'Evaluated-model failover'],
    'One place for keys, budgets, routing and logging. Redact personal data and fail over only to evaluated models. Any vendor is an example, not an endorsement.', path, {accent: true});
  box(1270, 160, 385, 140, 'Read-only evidence', ['Versioned sources and search', 'Statistics and MCP service'],
    'Immutable snapshots with checksums, indexes on the same evidence version and a read-only MCP service behind an allowlist. Restrict report text according to source rights.', path);
  line('M410 230 H440');
  line('M825 230 H855');
  line('M1240 230 H1270');

  // These controls span the whole environment rather than forming steps in an answer.
  const around = svgEl('g', {class: 'production-node'});
  around.append(svgEl('rect', {x: 25, y: 360, width: 1630, height: 80, rx: 14, fill: 'var(--paper)', stroke: 'var(--line-strong)', 'stroke-width': 1.5, 'stroke-dasharray': '7 5'}));
  text(around, 47, 408, 'Around everything', 30, '--ink', 600);
  text(around, 380, 408, 'Secrets manager · Audit and tracing · Evaluation release gates · Backups with restore drills', 28);
  const aroundDetail = 'OpenTelemetry logs and traces, secrets in a vault, budget alerts and evaluation as a CI gate. Use scoped credentials and redacted logs. Keep encrypted backups outside the primary failure domain and practise restores.';
  attachTip(around, 840, 'Around everything', aroundDetail);
  svg.append(around);
  entries.push({group: 'Around everything', title: 'Controls across the environment', lines: ['Secrets manager', 'Audit and tracing', 'Evaluation release gates', 'Backups with restore drills'], detail: aroundDetail});

  const mobile = el('div', 'production-mobile');
  let group;
  entries.forEach(entry => {
    if (entry.group !== group) {
      group = entry.group;
      mobile.append(el('h3', 'production-mobile-group', group));
      if (group === 'Proposed request path') {
        mobile.append(el('p', 'production-mobile-flow', 'Protected access → API and workers → model gateway → read-only evidence. Server-sent events return progress and the final answer.'));
      }
    }
    const article = el('article', 'production-mobile-entry');
    const lines = el('ul', 'production-mobile-lines');
    entry.lines.forEach(value => lines.append(el('li', '', value)));
    article.append(el('h4', '', entry.title), lines, el('p', 'production-mobile-tip', entry.detail));
    mobile.append(article);
  });
  wrap.append(svg, mobile);
  return wrap;
}
