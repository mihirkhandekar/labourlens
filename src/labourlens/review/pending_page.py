"""The pending-review page: one offline file with every card the owner has not decided by their own click.

Guided mode shows one card at a time. There is no select-all and no Agree-with-AI control: every decision is the owner's own click
(A, C, X, P, W), recorded as owner_manual. The AI suggestion is shown below each card for reference only.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from labourlens.review import heldout_v2 as hv2
from labourlens.review import pack
from labourlens.review import pending as P
from labourlens.review.pack import ROOT, Evidence, esc, para

GOLD_OPTS = [{'v': 'approve', 'key': 'a', 'label': 'Approve label'}, {'v': 'change', 'key': 'c', 'label': 'Change label'}, {'v': 'reject', 'key': 'x', 'label': 'Reject case'}]
ANSWER_OPTS = [{'v': 'correct', 'key': 'a', 'label': 'Right'}, {'v': 'partly correct', 'key': 'p', 'label': 'Partly right'}, {'v': 'incorrect', 'key': 'w', 'label': 'Wrong'}]
SOURCE_OPTS = [{'v': 'matches', 'key': 'a', 'label': 'Matches'}, {'v': 'minor', 'key': 'p', 'label': 'Small difference'}, {'v': 'major', 'key': 'w', 'label': 'Does not match'}]
J10_OPTS = [{'v': 'accept', 'key': 'a', 'label': 'Accept this limitation'}, {'v': 'not_accept', 'key': 'x', 'label': 'Do not accept'}]
J10_FINAL_OPTS = [{'v': 'accept_limits', 'key': 'a', 'label': P.J10_FINAL_OPTIONS['accept_limits']}, {'v': 'require_fixes', 'key': 'x', 'label': P.J10_FINAL_OPTIONS['require_fixes']},
                  {'v': 'inspect_more', 'key': 'm', 'label': P.J10_FINAL_OPTIONS['inspect_more']}]
RISK_TEXT = {-2: 'fresh AI reviewer says change the label: look first', -1: 'fresh AI reviewers flag a problem: look first', 0: 'AI disagrees or raised a doubt', 1: 'needs a look (AI concern or judgement call)', 2: 'one AI reviewer or none', 3: 'AI reviewers agree'}


def options_for(card: dict) -> list[dict]:
    if card['stream'] in ('gold', 'v2'):
        return GOLD_OPTS
    if card['stream'] == 'answers':
        return ANSWER_OPTS
    if card['stream'] == 'sources':
        return SOURCE_OPTS
    return J10_FINAL_OPTS if card.get('final') else J10_OPTS


def _gold_evidence(c: dict, ev: Evidence) -> str:
    sections = [('evidence_text', 'Evidence for the expected answer (text)'), ('evidence_data', 'Evidence for the expected answer (data rows)'),
                ('partial_evidence_text', 'Partial evidence (covers only part of the question)'), ('context_only_evidence_text', 'Background text (shows why the system should not simply answer)'),
                ('context_only_evidence_data', 'Background data rows')]
    out = []
    for field, title in sections:
        ids = [i for e in c.get(field, []) for i in e.get('passage_ids', e.get('observation_ids', []))]
        if ids:
            out.append(f'<h3>{esc(title)}</h3>' + ''.join(ev.render(i) for i in dict.fromkeys(ids)))
    return ''.join(out) or '<h3>Evidence</h3><p>This case needs no source evidence: the right behaviour follows from the question itself.</p>'


def _chip_class(verdict: str) -> str:
    v = str(verdict).lower()
    if v.startswith(('change', 'fix', 'concern', 'partly', 'minor')):
        return 'v-change_label'
    if v.startswith(('drop', 'disagree', 'reject', 'incorrect', 'major', 'label_wrong', 'wrong')):
        return 'v-reject'
    return 'v-approve'


def _ai_strip(card: dict) -> str:
    """Reference only: shown below the card, never actionable. There is no Agree button anywhere on this page."""
    ai = card['ai']
    items = ''.join(f'<li><b>{esc(o["reviewer"])}</b> <span class="conf">confidence {esc(o["confidence"])}</span> <span class="chip {_chip_class(o["verdict"])}">{esc(o["verdict"])}</span><br><span class="areason">{esc(o["reason"])}</span></li>' for o in ai['opinions'])
    if ai['status'] == 'agree':
        verdict = {'approve': 'approve the label'}.get(ai['decision'], str(ai['decision']) + (f' to {ai["proposed_behavior"]}' if ai['proposed_behavior'] else ''))
        lead = f'<p><b>The AI reviewers lean to:</b> {esc(verdict)}.</p>'
    elif ai['status'] == 'disagree':
        lead = '<p><b>The AI reviewers disagree, raised a concern, or marked this as your judgement.</b></p>'
    else:
        lead = '<p><b>No AI review exists for this card, and none was run.</b></p>'
    return (f'<section class="aistrip" data-ai-strip><h3>AI suggestion (for reference, decide yourself)</h3>{lead}<p>{esc(ai["text"])}</p><ul class="votes">{items}</ul>'
            '<p class="fine">AI reviewers are not human review. There is no way to accept this suggestion with one click: use your own decision buttons above.</p></section>')


def _controls(card: dict) -> str:
    opts = options_for(card)
    buttons = ''.join(f'<button type="button" class="big" data-act="{esc(o["v"])}">{esc(o["label"])} <kbd>{o["key"].upper()}</kbd></button>' for o in opts)
    change = ''
    if card['stream'] in ('gold', 'v2'):
        chips = ''.join(f'<button type="button" data-beh="{b}"{" disabled" if b == card.get("behavior") else ""}>{esc(hv2.SHORT[b])} <kbd>{n}</kbd></button>' for n, b in enumerate(pack.BEHAVIOURS, 1))
        change = f'<div class="change-panel" hidden><p>What should the system do instead? (keys 1 to 5)</p><div class="chips">{chips}</div></div>'
    return ('<div class="decision"><div class="buttons" role="group" aria-label="Your decision">' + buttons + '</div>' + change +
            '<label class="reason" hidden>Short reason (required)<textarea data-field="reason" rows="2" maxlength="2000"></textarea></label>'
            '<label>Comment (optional)<textarea data-field="comment" rows="2" maxlength="4000"></textarea></label><p class="status" aria-live="polite"></p></div>')


def _frame(card: dict, left: str, right: str, banner: str = '', ai_html: str = '') -> str:
    tags = (f'<span class="tag">{esc(P.STREAM_LABEL[card["stream"]])}</span><span class="tag q-{card["queue"]}">{esc(P.QUEUE_LABEL[card["queue"]])}</span>'
            f'<span class="tag risk-{card["risk"]}">{esc(RISK_TEXT.get(card["risk"], ""))}</span>')
    earlier = f'<p class="earlier"><b>Earlier:</b> {esc(card["earlier"])}</p>'
    return (f'<article class="card" id="c-{esc(card["key"])}" data-key="{esc(card["key"])}" hidden><h2>{esc(card["title"])} {tags}</h2>{earlier}{banner}'
            f'<div class="split"><div class="left">{left}</div><div class="right">{right}</div></div>{ai_html}</article>')


def _gold_card(card: dict, c: dict, ev: Evidence) -> str:
    behaviour = c['expected_behavior']
    why = c.get('abstain_reason') or c.get('difficulty_note') or 'The evidence on the right contains the requested fact.'
    facts = ''.join(para(f) for f in c.get('reference_facts', [])) or para('No figures expected: this label does not depend on a number.')
    if c.get('calculation'):
        facts += '<details><summary>How the expected number is calculated</summary><pre>' + esc(json.dumps(c['calculation'], indent=1, ensure_ascii=False)) + '</pre></details>'
    trick = c.get('adversarial')
    trick_html = para('Trick in the question: ' + str(trick.get('type', trick))) if isinstance(trick, dict) else ''
    left = (f'<section><h3>The question</h3><p class="question">{esc(c["question"])}</p>{trick_html}</section>'
            f'<section><h3>What the draft says the system should do</h3><p><strong class="behaviour">{esc(behaviour.replace("_", " "))}</strong>: {esc(hv2.SENTENCES[behaviour])}</p><p class="why">Why: {esc(why)}</p></section>'
            f'<section><h3>Expected facts or numbers</h3>{facts}</section>' + _controls(card))
    right = ('<p class="check"><strong>What to check:</strong> is the question realistic and clear, is the behaviour the right way to handle it, and does the evidence support the expected facts?</p>'
             + _gold_evidence(c, ev))
    return _frame(card, left, right, ai_html=_ai_strip(card))


def _answer_card(card: dict, c: dict, run: dict, ev: Evidence, ev_old: Evidence) -> str:
    facts = ''.join(para(f) for f in c.get('reference_facts', []))
    left = ('<section><p class="check"><strong>What to check:</strong> is the saved answer right, using the page or table on the right? Is every number, period and population correct?</p>'
            f'<details><summary>What the gold says (open only after forming your own view)</summary><p>Expected behaviour: <b>{esc(c["expected_behavior"])}</b></p>{facts}</details></section>'
            + _controls(card))
    return _frame(card, left, pack.answer_review_html(c, run, ev_old), ai_html=_ai_strip(card))


def _source_card(card: dict, ev_old: Evidence) -> str:
    kind = card['case_id'].split('-')[0]
    hint = ('Compare the highlighted passage with the original page: words, numbers, boundaries.' if kind == 'passage'
            else 'Compare the highlighted CSV row: column, population, period, units and seasonal basis. A dash is not zero.')
    left = f'<p class="check"><strong>What to check:</strong> {esc(hint)}</p>' + _controls(card)
    return _frame(card, left, ev_old.render(card['passage']), ai_html=_ai_strip(card))


def _v2_card(card: dict, c: dict, ev: Evidence) -> str:
    facts = ''.join(para(f) for f in c.get('reference_facts', [])) or para('No figures expected: this label does not depend on a number.')
    why = c.get('abstain_reason') or c.get('difficulty_note') or 'The evidence contains the requested fact.'
    banner = '<aside class="banner related"><b>This held-out v2 test is already signed and frozen.</b> A decision here is recorded and reported, but never edits the frozen v2 file.</aside>'
    left = (f'<section><h3>The question</h3><p class="question">{esc(c["question"])}</p></section>'
            f'<section><h3>What the frozen test says the system should do</h3><p><strong class="behaviour">{esc(c["expected_behavior"].replace("_", " "))}</strong>: {esc(hv2.SENTENCES[c["expected_behavior"]])}</p><p class="why">Why: {esc(why)}</p></section>'
            f'<section><h3>Expected facts or numbers</h3>{facts}</section>' + _controls(card))
    return _frame(card, left, hv2._evidence_html(c, ev), banner, _ai_strip(card))


def _passage_box(title: str, passages: list[dict]) -> str:
    if not passages:
        return f'<div><h5>{esc(title)}</h5><p><b>No text was kept for this page.</b></p></div>'
    shown = ''.join('<pre>' + esc(' '.join(p['text'].split())[:700]) + ('…' if len(' '.join(p['text'].split())) > 700 else '') + '</pre>' for p in passages[:4])
    more = f'<p>…and {len(passages) - 4} more.</p>' if len(passages) > 4 else ''
    return f'<div><h5>{esc(title)} ({len(passages)} passage(s) on this page)</h5>{shown}{more}</div>'


def _j10_card(card: dict, ev: Evidence, ev_old: Evidence) -> str:
    if card.get('final'):
        left = (para(card['question']) + '<p>Your five answers above are recorded separately. This overall choice is the J10 decision from the main pack, asked again now that you have looked at the pages.</p>'
                + _controls(card))
        return _frame(card, left, '<p>No evidence for this card: it is your overall choice.</p>')
    entries = {sid: e for (sid, _), e in ev.manifest.items()}
    entry = entries.get(card['source_id'])
    if entry is None:
        return _frame(card, para(card['gap']) + _controls(card), '<p>The report is not in this corpus, so no page can be shown.</p>')
    raw = (ev.root / entry['raw_path']).resolve()
    key, width, height = ev.page_image(raw, card['page'])
    frozen = sorted((p for p in ev_old.passages.values() if p['source_id'] == card['source_id'] and p.get('page_number') == card['page']), key=lambda p: p['passage_id'])
    if card.get('passage') and card['passage'] in ev_old.passages:
        first = ev_old.passages[card['passage']]
        frozen = [first] + [p for p in frozen if p['passage_id'] != first['passage_id']]
    current = sorted((p for p in ev.passages.values() if p['source_id'] == card['source_id'] and p.get('page_number') == card['page']), key=lambda p: p['passage_id'])
    image = (f'<figure><button type="button" class="zoom-page" aria-expanded="false">Enlarge / restore page</button><div class="pdf-page"><img data-page="{key}" alt="Original report page {card["page"]}" loading="lazy"></div>'
             '<figcaption>The original stored PDF page. Enlarge to read the small print.</figcaption></figure>')
    left = (f'<section><p class="check"><strong>What to check:</strong> {esc(card["gap"])} Compare the page with the two extractions below, then say whether you accept this limitation being disclosed instead of fixed in the saved runs.</p>'
            f'<div class="j10-compare">{_passage_box("Frozen extraction (used by the saved runs)", frozen)}{_passage_box("Current extraction (after the extraction fixes)", current)}</div></section>' + _controls(card))
    return _frame(card, left, image + para(f'{card["source_id"]}, PDF page {card["page"]}'))


STREAM_TOTALS = 'gold|v2|answers|sources|j10'

START = '''<section class="start" id="start"><h1>Pending review: everything you have not decided by your own click</h1>
<p class="private">PRIVATE: contains MOM and MTI text; do not commit or share this page or your export.</p>
<h2>Start here</h2>
<p><b>What is pending.</b> {pending_text}</p>
<p><b>Optional redo.</b> {redo_text}</p>
<ol>
<li><b>Work one card at a time (Guided mode).</b> Read the question and the evidence, then press your own key. There is no select-all.</li>
<li><b>Every decision is your own click.</b> There is no “Agree with AI” button and no AI key on this page. Under each card, below the evidence and the label, the AI suggestion is shown for reference only (“decide yourself”): read the evidence first, decide, then compare.</li>
<li><b>Finish.</b> Type your name, click Download, then run <code>uv run labourlens pending-ingest --review-export &lt;the downloaded file&gt;</code>. It first shows a preview; add <code>--write</code> to create gold v3.7 (a new file; nothing existing is changed).</li>
</ol>
<h3>What the final report will say</h3>
<p>Every decision made here is recorded as <code>owner_manual</code>, for any click or key. That records that the page received an input, so the report calls these “recorded decisions”. Cards you leave in the redo queue stay recorded as agreed with an AI suggestion, and the report says how many. This is one human reviewer, after AI pre-review and after the runs were scored: not independent inter-rater evidence.</p>
<h3>Keys</h3><p><kbd>A</kbd> approve / right / matches / accept · <kbd>C</kbd> change label · <kbd>X</kbd> reject / do not accept · <kbd>P</kbd> partly right / small difference · <kbd>W</kbd> wrong / does not match · <kbd>1</kbd>–<kbd>5</kbd> new behaviour · <kbd>Enter</kbd> next · <kbd>Backspace</kbd> previous</p>
</section>'''

TOOLBAR = '''<div class="bar"><div class="row"><progress id="progress" value="0" max="1" aria-label="Required cards decided"></progress><strong id="progress-text"></strong>
<span class="sum" id="summary"></span><label>Your name <input id="reviewer" maxlength="200" autocomplete="off" placeholder="Type your own name"></label>
<label>Show <select id="filter"></select></label><label><input type="checkbox" id="show-decided"> show decided</label><label>Jump <select id="jump"></select></label>
<button id="download">Download export</button><button id="toggle-start">Start here</button></div>
<div class="row gate" id="streams"></div><p id="notice" role="status"></p><p id="storage" role="alert"></p></div>'''

FOOT = '''<div class="nav"><div class="strip" id="keys"></div>
<button id="prev">Previous</button><span id="position"></span><button id="next">Next</button><button id="next-open">Next undecided</button></div>'''

EXTRA_CSS = '''
.review-split{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.2fr);gap:18px}.j10-compare{display:grid;grid-template-columns:1fr;gap:10px}
.tag.q-redo{background:#fff3cd;border-color:#c07500}.tag.q-pending,.tag.q-proposal{background:#e3f4e8;border-color:#1b6b3a}.tag.risk-0{background:#fde4e4;border-color:#9b1c1c}.tag.risk-1{background:#fff3cd;border-color:#c07500}
.earlier{font-size:.88rem;opacity:.9}
figure.zoomed .pdf-page{width:230%}figure.zoomed{overflow:auto}
'''

SCRIPT = r'''
const cards = [...document.querySelectorAll('article.card')];
const prefix = 'labourlens-pending:' + PACK_ID + ':';
const memory = new Map(); let active = '', lastActive = '';
const blank = () => ({decision:'', proposed_behavior:'', reason:'', comment:'', source:'', ai_basis:null, timestamp:''});
function warn() { document.querySelector('#storage').textContent = 'Autosave is unavailable: your choices stay in this page only. Download the file before closing.'; }
function load(key) { if (memory.has(key)) return memory.get(key); try { const v = JSON.parse(localStorage.getItem(prefix + key) || 'null'); if (v) memory.set(key, v); return v; } catch (e) { warn(); return null; } }
function save(key, value) { memory.set(key, value); try { localStorage.setItem(prefix + key, JSON.stringify(value)); } catch (e) { warn(); } }
try { localStorage.setItem(prefix + 'probe', '1'); localStorage.removeItem(prefix + 'probe'); } catch (e) { warn(); }
const state = new Map(cards.map(c => [c.dataset.key, Object.assign(blank(), load('card:' + c.dataset.key) || {})]));
const get = c => state.get(c.dataset.key), meta = c => META[c.dataset.key];
function complete(s, m) {
  if (!m.opts.some(o => o.v === s.decision)) return false;
  if (s.decision === 'change' && !BEHAVIOURS.includes(s.proposed_behavior)) return false;
  if (REASON_REQUIRED.includes(s.decision) && !s.reason.trim()) return false;
  return true;
}
const done = c => complete(get(c), meta(c));
function persist(c) { const s = get(c); s.timestamp = new Date().toISOString(); save('card:' + c.dataset.key, s); }
function paint(c) {
  const s = get(c), m = meta(c), box = c.querySelector('.decision');
  box.querySelectorAll('[data-act]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.act === s.decision)));
  box.querySelectorAll('[data-beh]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.beh === s.proposed_behavior)));
  const panel = box.querySelector('.change-panel'); if (panel) panel.hidden = s.decision !== 'change';
  box.querySelector('.reason').hidden = !(s.decision === 'change' || REASON_REQUIRED.includes(s.decision));
  box.querySelectorAll('[data-field]').forEach(f => { if (document.activeElement !== f) f.value = s[f.dataset.field] || ''; });
  let text = 'Not decided yet.', cls = 'todo';
  const label = (m.opts.find(o => o.v === s.decision) || {}).label;
  if (s.decision) {
    if (done(c)) { text = 'Decided: ' + label + (s.decision === 'change' ? ' to “' + s.proposed_behavior.replaceAll('_', ' ') + '”' : '') + '. ' + '(Your own click.)'; cls = 'ok'; }
    else text = (s.decision === 'change' ? 'Change label: pick the new behaviour and write a reason.' : 'Write a short reason.');
  }
  const st = box.querySelector('.status'); st.textContent = text; st.className = 'status ' + cls;
}
const required = c => meta(c).queue !== 'redo';
function summary() {
  const dec = cards.filter(done);
  const own = dec.filter(c => get(c).source === 'owner_manual').length, ai = dec.length - own;
  const req = cards.filter(required), reqDone = req.filter(done).length, redo = cards.filter(c => !required(c)), redoDone = redo.filter(done).length;
  const p = document.querySelector('#progress'); p.max = Math.max(1, req.length); p.value = reqDone;
  document.querySelector('#progress-text').textContent = reqDone + ' of ' + req.length + ' required cards decided';
  document.querySelector('#summary').innerHTML = '<span>' + own + ' decided by your own click</span><span>redo ' + redoDone + ' of ' + redo.length + ' (optional)</span>';
  const groups = {};
  cards.forEach(c => { const m = meta(c), k = m.stream + ' ' + m.queue; groups[k] = groups[k] || [0, 0]; groups[k][1]++; if (done(c)) groups[k][0]++; });
  document.querySelector('#streams').innerHTML = Object.entries(groups).map(([k, v]) => '<span>' + k + ': <b>' + v[0] + '/' + v[1] + '</b></span>').join(' ');
}
function matchesFilter(c) {
  const f = document.querySelector('#filter').value, m = meta(c);
  if (f === 'all') return true;
  if (f === 'required') return m.queue !== 'redo';
  if (f === 'redo') return m.queue === 'redo';
  return (m.stream + ' ' + m.queue) === f;
}
function queue() {
  const showAll = document.querySelector('#show-decided').checked;
  return cards.filter(c => matchesFilter(c) && (showAll || !done(c) || c.dataset.key === active));
}
function render() {
  const q = queue();
  if (!q.some(c => c.dataset.key === active)) active = q.length ? q[0].dataset.key : '';
  cards.forEach(c => { c.hidden = c.dataset.key !== active; paint(c); });
  const current = cards.find(c => c.dataset.key === active);
  if (current) current.querySelectorAll('img[data-page]').forEach(img => { if (!img.src.startsWith('data:')) img.src = 'data:image/jpeg;base64,' + PAGE_IMAGES[img.dataset.page]; });
  const idx = q.findIndex(c => c.dataset.key === active);
  document.querySelector('#position').textContent = q.length ? 'Card ' + (idx + 1) + ' of ' + q.length + ' in this view · ' + active : 'Nothing left in this view: change “Show”, or type your name and download.';
  document.querySelector('#prev').disabled = idx <= 0; document.querySelector('#next').disabled = idx < 0 || idx >= q.length - 1;
  document.querySelector('#next-open').disabled = !cards.some(c => matchesFilter(c) && !done(c));
  const jump = document.querySelector('#jump');
  [...jump.options].forEach((o, i) => { const c = cards[i]; o.textContent = (done(c) ? '✓ ' : '· ') + c.dataset.key; });
  jump.value = active;
  document.querySelector('#keys').innerHTML = keysHelp();
  summary();
  document.documentElement.style.setProperty('--bar', document.querySelector('.bar').offsetHeight + 12 + 'px');
}
function keysHelp() {
  const c = cards.find(x => x.dataset.key === active); if (!c) return '';
  const m = meta(c);
  return m.opts.map(o => '<kbd>' + o.key.toUpperCase() + '</kbd> ' + o.label).join(' · ') + (m.stream === 'gold' || m.stream === 'v2' ? ' · <kbd>1</kbd>–<kbd>5</kbd> new behaviour' : '') + ' · <kbd>Enter</kbd> next · <kbd>Backspace</kbd> previous';
}
function move(d) { const q = queue(), i = q.findIndex(c => c.dataset.key === active); if (q[i + d]) { active = q[i + d].dataset.key; render(); } }
function nextOpen() { const i = cards.findIndex(c => c.dataset.key === active); for (let k = 1; k <= cards.length; k++) { const c = cards[(i + k) % cards.length]; if (matchesFilter(c) && !done(c)) { active = c.dataset.key; render(); return; } } }
function advance() { setTimeout(() => { const q = queue(), i = q.findIndex(x => x.dataset.key === active); if (q[i + 1]) { active = q[i + 1].dataset.key; render(); } }, 0); }
function decide(c, act) {
  const s = get(c);
  s.decision = act; s.source = 'owner_manual'; s.ai_basis = null;
  if (act !== 'change') s.proposed_behavior = '';
  if (!REASON_REQUIRED.includes(act) && act !== 'change') s.reason = '';
  persist(c); render();
  if (done(c)) advance();
  else { const r = c.querySelector('[data-field=reason]'); if (r && !r.closest('.reason').hidden && act !== 'change') r.focus(); }
}
document.addEventListener('click', e => {
  const z = e.target.closest('.zoom-page'); if (z) { const f = z.closest('figure'); f.classList.toggle('zoomed'); z.setAttribute('aria-expanded', String(f.classList.contains('zoomed'))); return; }
  const a = e.target.closest('a[data-jump]'); if (a) { e.preventDefault(); document.querySelector('#show-decided').checked = true; active = a.dataset.jump; render(); return; }
  const b = e.target.closest('button'); const c = b && b.closest('article.card'); if (!c) return;
  if (b.dataset.act) decide(c, b.dataset.act);
  else if (b.dataset.beh) { const s = get(c); s.decision = 'change'; s.source = 'owner_manual'; s.ai_basis = null; s.proposed_behavior = b.dataset.beh; persist(c); render(); const r = c.querySelector('[data-field=reason]'); if (r) r.focus(); }
});
document.addEventListener('input', e => {
  const f = e.target.closest('[data-field]'); const c = f && f.closest('article.card'); if (!c) return;
  const s = get(c); s[f.dataset.field] = f.value; persist(c); paint(c); summary();
});
document.addEventListener('keydown', e => {
  if (e.ctrlKey || e.metaKey || e.altKey) return;
  const t = e.target;
  if (t.matches('textarea,input,select')) { if (e.key === 'Escape') t.blur(); return; }
  if (t.matches('button') && (e.key === 'Enter' || e.key === ' ')) return;
  const c = cards.find(x => x.dataset.key === active); if (!c) return;
  const k = e.key.length === 1 ? e.key.toLowerCase() : e.key, m = meta(c);
  const opt = m.opts.find(o => o.key === k);
  if (opt) { e.preventDefault(); decide(c, opt.v); }
  else if (/^[1-5]$/.test(k) && get(c).decision === 'change') { const b = c.querySelectorAll('[data-beh]')[Number(k) - 1]; if (b && !b.disabled) { e.preventDefault(); b.click(); } }
  else if (k === 'Enter' || k === 'j') { e.preventDefault(); move(1); }
  else if (k === 'Backspace' || k === 'k') { e.preventDefault(); move(-1); }
});
document.querySelector('#prev').addEventListener('click', () => move(-1));
document.querySelector('#next').addEventListener('click', () => move(1));
document.querySelector('#next-open').addEventListener('click', nextOpen);
document.querySelector('#show-decided').addEventListener('change', render);
document.querySelector('#filter').addEventListener('change', () => { active = ''; render(); });
document.querySelector('#toggle-start').addEventListener('click', () => { const s = document.querySelector('#start'); s.hidden = !s.hidden; if (!s.hidden) window.scrollTo(0, 0); });
const jump = document.querySelector('#jump');
cards.forEach(c => { const o = document.createElement('option'); o.value = c.dataset.key; jump.append(o); });
jump.addEventListener('change', () => { document.querySelector('#show-decided').checked = true; active = jump.value; render(); });
const filter = document.querySelector('#filter');
const groupCounts = {}; cards.forEach(c => { const m = meta(c), k = m.stream + ' ' + m.queue; groupCounts[k] = (groupCounts[k] || 0) + 1; });
filter.innerHTML = '<option value="all">Everything, in order (' + cards.length + ')</option><option value="required">Required only (' + cards.filter(required).length + ')</option><option value="redo">Optional redo only (' + cards.filter(c => !required(c)).length + ')</option>'
  + Object.entries(groupCounts).map(([k, n]) => '<option value="' + k + '">' + k + ' (' + n + ')</option>').join('');
document.querySelector('#download').addEventListener('click', () => {
  const name = document.querySelector('#reviewer').value.trim(), notice = document.querySelector('#notice');
  if (!name) { notice.textContent = 'Type your own name first: it is recorded with your decisions.'; return; }
  const results = cards.filter(done).map(c => { const s = get(c), m = meta(c); return {key: c.dataset.key, stream: m.stream, queue: m.queue, case_id: m.case_id, decision: s.decision,
    proposed_behavior: s.decision === 'change' ? s.proposed_behavior : '', reason: s.reason.trim(), comment: s.comment, decision_source: 'owner_manual',
    ai_basis: {}, timestamp: s.timestamp || new Date().toISOString()}; });
  const data = {schema_version: 1, kind: 'pending_review', pack_id: PACK_ID, reviewer_name: name, exported_at: new Date().toISOString(), main_export_sha256: MAIN_SHA, ai_files_sha256: AI_SHA, results};
  const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'}));
  const a = document.createElement('a'); a.href = url; a.download = 'pending-review.json'; document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 5000);
  const open = cards.filter(c => required(c) && !done(c)).length;
  notice.textContent = open ? 'Downloaded a PARTIAL export: ' + open + ' required cards are still undecided, so pending-ingest will not write until you finish them.' : 'Downloaded. Now run: uv run labourlens pending-ingest --review-export <the file>';
});
render();
'''


def build_pending_page(root: Path = ROOT, main_export: Path | None = None) -> Path:
    root = Path(root).resolve()
    destination = root / P.PAGE
    if subprocess.run(['git', 'check-ignore', '--quiet', str(destination)], cwd=root, check=False).returncode != 0:
        raise ValueError('The pending-review page must be gitignored before it can contain MOM text')
    st = P.State(root, main_export)
    cards = P.plan(root, st)
    ev = Evidence(root, label='corpus v3', dpi=88, quality=56, compact=True)
    frozen = root / pack.FROZEN_V1
    ev_old = Evidence(root, base=frozen, label='corpus v1 (frozen run)', like=ev, dpi=88, quality=56, compact=True) if (frozen / 'manifests/manifest.json').exists() else ev
    html = []
    meta = {}
    for card in cards:
        stream = card['stream']
        if stream == 'gold':
            html.append(_gold_card(card, st.gold_by_id[card['case_id']], ev))
        elif stream == 'answers':
            html.append(_answer_card(card, st.gold_by_id[card['case_id']], st.runs[card['case_id']], ev, ev_old))
        elif stream == 'sources':
            html.append(_source_card(card, ev_old))
        elif stream == 'v2':
            html.append(_v2_card(card, st.v2_by_id[card['case_id']], ev))
        else:
            html.append(_j10_card(card, ev, ev_old))
        ai = card['ai']
        meta[card['key']] = {'stream': stream, 'queue': card['queue'], 'case_id': card['case_id'], 'opts': options_for(card),
                             'ai': {'status': ai['status'], 'decision': ai['decision'], 'proposed_behavior': ai['proposed_behavior'], 'ai_basis': ai['ai_basis']}}
    counts = {}
    for c in cards:
        counts[(c['stream'], c['queue'])] = counts.get((c['stream'], c['queue']), 0) + 1
    n = lambda s, q: counts.get((s, q), 0)
    pending = (f'{n("gold", "pending")} development gold cases that no human has ever decided (AI reviewers looked at them, you did not)'
               + (f'; {n("gold", "proposal")} label-change proposals not yet applied' if n('gold', 'proposal') else '')
               + (f'; {n("j10", "pending")} J10 cards (five original pages from the frozen extraction, then your overall J10 choice)' if n('j10', 'pending') else '') + '.')
    redo_total = sum(v for (s, q), v in counts.items() if q == 'redo')
    redo = (f'{redo_total} cards where you earlier pressed “Agree with AI” ({n("gold", "redo")} gold, {n("answers", "redo")} saved answers, {n("sources", "redo")} source checks, {n("v2", "redo")} held-out v2). '
            'Please redo them with your own click if you can; any you leave stay recorded as agreed with an AI suggestion. Use “Show” to filter.')
    start = START.replace('{pending_text}', esc(pending)).replace('{redo_text}', esc(redo))
    head = hv2.HEAD.replace('Held-out v2 owner review (private)', 'Pending review (private)').replace('</style></head><body>', EXTRA_CSS + '</style></head><body>')
    reasons = sorted(P.REASON_REQUIRED)
    page = (head + TOOLBAR + start + '<main id="cards">' + ''.join(html) + '</main>' + FOOT
            + '<script>const PACK_ID=' + json.dumps(P.pack_id(root, st)) + ';const MAIN_SHA=' + json.dumps(st.main_sha) + ';const AI_SHA=' + json.dumps(P.ai_file_hashes(root))
            + ';const BEHAVIOURS=' + json.dumps(list(pack.BEHAVIOURS)) + ';const REASON_REQUIRED=' + json.dumps(reasons)
            + ';const META=' + json.dumps(meta).replace('<', '\\u003c') + ';const PAGE_IMAGES=' + json.dumps(ev.images).replace('<', '\\u003c') + ';</script><script>' + SCRIPT + '</script></body></html>')
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(page)
    return destination
