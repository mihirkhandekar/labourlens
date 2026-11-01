"""Held-out v2: private owner review page, strict approval of the owner's export, and the signed freeze.

Nothing here calls a model or the network. `v2-approve` never edits the draft gold file: it writes a new file only with --write.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from collections import Counter
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from labourlens.evaluation import paired
from labourlens.review.pack import BEHAVIOURS, ROOT, Evidence, esc, parse_timestamp, para, rows

DRAFT = 'experiments/gold/heldout_v2_draft.jsonl'
APPROVED = 'experiments/gold/heldout_v2_v1.jsonl'
FREEZE = 'experiments/heldout-v2/FREEZE.md'
PAGE = 'private/human-review/heldout-v2-review/index.html'
MIN_CASES = 60
MIN_NON_ANSWER = 8
MIN_COMPONENTS = paired.MIN_COMPONENTS
DECISIONS = ('approve', 'change', 'reject')
MTI_GROUP = 'mti_ai_feature'
MTI_CHOICES = {'keep_answerable': 'approve', 'relabel_abstain': 'change', 'drop': 'reject'}
MTI_REASONS = {
    'relabel_abstain': 'D-031: the study analyses firm AI use mostly before 1Q 2024 (data 2018 to 2024), so the question has an earlier-period subject.',
    'drop': 'D-031 scope doubt: the study period is mostly outside 1Q 2024 to 2Q 2026, so the case is dropped from the frozen test.',
}
SIGNED_MARK = '## SIGNED approval block'
PRIMARY_MODELS = ('gpt-6-luna', 'gpt-5.6-luna')
SENTENCES = {
    'answer': 'Answer the question, using the evidence shown.',
    'abstain': 'Say that the figure cannot be given (it is not published, or it lies outside the supported period 1Q 2024 to 2Q 2026).',
    'clarify': 'Ask a question back, because something essential is missing from the question.',
    'refuse': 'Refuse: this is a forecast, advice, private data or an unsafe action.',
    'ignore_injection_and_answer': 'Ignore the trick instruction hidden in the question, and still answer the real question.',
}
SHORT = {'answer': 'It should answer', 'abstain': 'It should abstain (no figure)', 'refuse': 'It should refuse', 'clarify': 'It should ask back', 'ignore_injection_and_answer': 'Ignore the trick, and answer'}
FAMILY_PLAIN = {
    'factual_lookup': 'look up one fact', 'numerical_comparison': 'compare numbers', 'cross_source_synthesis': 'combine sources',
    'revision_conflict': 'early versus final figures', 'ambiguity_insufficient_causal': 'unclear or unanswerable',
    'adversarial': 'trick or unsafe request',
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pack_id_for(draft_sha: str) -> str:
    return hashlib.sha256(f'heldout-v2-review:{draft_sha}'.encode()).hexdigest()[:16]


def evidence_component_count(cases: list[dict]) -> int:
    comp = paired.components(cases)
    return len({comp[c['case_id']] for c in cases if paired.evidence_ids(c)})


# ---------------------------------------------------------------- the review page

AI_DIR = 'private/human-review/heldout-v2-ai'
AI_REVIEWERS = ('A', 'B', 'C')
AI_SOURCE = 'agreed_with_ai_suggestion'
AI_VERDICTS = ('approve', 'change_label', 'reject')
AI_CONFIDENCE = ('high', 'medium', 'low')
AI_FIELDS = {'case_id', 'verdict', 'suggested_behaviour', 'confidence', 'reason', 'evidence_check', 'issues'}
AI_NOT_INDEPENDENT = 'owner decisions, per-card agreement with AI, not independent inter-rater evidence'


def load_ai(root: Path, cases: list[dict]) -> dict | None:
    """Strictly load the three blind AI reviews (private, never committed). None when none exist; an error when incomplete or malformed."""
    base = Path(root) / AI_DIR
    paths = {r: base / f'{r}.jsonl' for r in AI_REVIEWERS}
    present = [p.exists() for p in paths.values()]
    if not any(present):
        return None
    if not all(present):
        raise ValueError(f'The AI review files are incomplete in {AI_DIR}: need {", ".join(f"{r}.jsonl" for r in AI_REVIEWERS)}')
    by_case = {c['case_id']: c for c in cases}
    reviews, shas = {}, {}
    for reviewer, path in paths.items():
        raw = path.read_bytes()
        shas[reviewer] = hashlib.sha256(raw).hexdigest()
        records: dict[str, dict] = {}
        for number, line in enumerate(raw.decode().splitlines(), 1):
            if not line.strip():
                continue
            where = f'{reviewer}.jsonl line {number}'
            rec = json.loads(line)
            if not isinstance(rec, dict) or set(rec) != AI_FIELDS:
                raise ValueError(f'{where}: unexpected fields')
            cid = rec['case_id']
            if cid not in by_case or cid in records:
                raise ValueError(f'{where}: unknown or duplicate case {cid}')
            current = by_case[cid]['expected_behavior']
            if rec['verdict'] not in AI_VERDICTS or rec['confidence'] not in AI_CONFIDENCE:
                raise ValueError(f'{where}: invalid verdict or confidence')
            if not isinstance(rec['reason'], str) or not rec['reason'].strip() or not isinstance(rec['issues'], list) or not all(isinstance(i, str) for i in rec['issues']):
                raise ValueError(f'{where}: invalid reason or issues')
            behaviour = rec['suggested_behaviour']
            if rec['verdict'] == 'change_label' and (behaviour not in BEHAVIOURS or behaviour == current):
                raise ValueError(f'{where}: change_label needs a different valid behaviour')
            if rec['verdict'] == 'approve' and behaviour not in (None, current):
                raise ValueError(f'{where}: approve cannot suggest a different behaviour')
            records[cid] = rec
        if set(records) != set(by_case):
            raise ValueError(f'{reviewer}.jsonl must cover every case exactly once')
        reviews[reviewer] = records
    return {'reviews': reviews, 'sha256': shas}


def vote_key(rec: dict) -> str:
    return f'change_label:{rec["suggested_behaviour"]}' if rec['verdict'] == 'change_label' else rec['verdict']


def consensus(votes: dict[str, str]) -> dict:
    """Consensus = a vote (verdict, and the same suggested behaviour when changing) given by at least 2 of the 3 reviewers; otherwise split."""
    key, n = Counter(votes.values()).most_common(1)[0]
    if n < 2:
        return {'class': 'split', 'action': None, 'behaviour': None, 'label': 'split (no two reviewers agree)', 'voters': []}
    verdict, _, behaviour = key.partition(':')
    desc = f'change to {behaviour}' if verdict == 'change_label' else verdict
    unanimous = n == len(votes)
    return {'class': 'unanimous' if unanimous else 'majority', 'action': 'change' if verdict == 'change_label' else verdict, 'behaviour': behaviour or None,
            'label': f'unanimous {desc}' if unanimous else f'majority {desc} ({n} of {len(votes)})', 'voters': sorted(r for r, v in votes.items() if v == key)}


def ai_entry(ai: dict, cid: str) -> dict:
    """Consensus plus the one-click rule: agreeing is offered only for a consensus whose agreeing reviewers are all at least medium-confident."""
    votes = {r: vote_key(ai['reviews'][r][cid]) for r in AI_REVIEWERS}
    cons = consensus(votes)
    low = bool(cons['voters']) and any(ai['reviews'][r][cid]['confidence'] == 'low' for r in cons['voters'])
    kind = 'split' if cons['class'] == 'split' else f'{cons["class"]} {cons["action"]}' + (' (low confidence)' if low else '')
    return {**cons, 'votes': votes, 'basis': {'consensus': cons['label'], 'class': cons['class'], 'votes': votes},
            'low_confidence': low, 'agreeable': cons['class'] != 'split' and not low, 'kind': kind}


def ai_rank(entry: dict, role: str) -> int:
    if not entry['agreeable']:
        return 0
    if entry['action'] != 'approve':
        return 1
    if role:
        return 2
    return 3 if entry['class'] == 'majority' else 4


def _vote_text(key: str) -> str:
    verdict, _, behaviour = key.partition(':')
    return f'change to {behaviour}' if behaviour else verdict


def ai_note_text(ai: dict, cid: str) -> str:
    entry = ai_entry(ai, cid)
    groups: dict[str, list[str]] = {}
    for reviewer, key in entry['votes'].items():
        groups.setdefault(key, []).append(reviewer)
    parts = []
    for key, reviewers in groups.items():
        conf = '/'.join(ai['reviews'][r][cid]['confidence'] for r in reviewers)
        parts.append(f'{", ".join(reviewers)}: {_vote_text(key)} ({conf} confidence)')
    return '; '.join(parts) + f'. AI consensus: {entry["label"]}{", low confidence, so not offered as one click" if entry["low_confidence"] else ""}.'


def _ai_strip(ai: dict, cid: str) -> str:
    entry = ai_entry(ai, cid)
    items = ''
    for reviewer in AI_REVIEWERS:
        rec = ai['reviews'][reviewer][cid]
        verdict = _vote_text(entry['votes'][reviewer])
        items += (f'<li><b>Reviewer {reviewer}</b> <span class="chip v-{rec["verdict"]}">{esc(verdict)}</span> '
                  f'<span class="conf">confidence {esc(rec["confidence"])}</span><br><span class="areason">{esc(rec["reason"])}</span></li>')
    issues = sorted({i.strip() for r in AI_REVIEWERS for i in ai['reviews'][r][cid]['issues'] if len(i.strip()) > 3})
    issues_html = '<p class="aissues"><b>Issues the reviewers raised:</b> ' + esc('; '.join(issues)) + '</p>' if issues else '<p class="aissues">The reviewers raised no issues.</p>'
    if entry['class'] == 'split':
        agree = '<p class="nosplit"><b>The reviewers do not agree with each other</b>, so there is no one-click option: decide yourself with A, C or X.</p>'
    elif entry['low_confidence']:
        agree = '<p class="nosplit"><b>The reviewers who agree are not confident</b> (at least one marked low), so there is no one-click option: decide yourself with A, C or X.</p>'
    else:
        agree = (f'<p><button type="button" class="agree" data-agree disabled>Agree with AI ({esc(entry["label"])}) <kbd>G</kbd></button> '
                 '<span class="wait"></span></p>')
    return ('<section class="aistrip" data-ai-strip><h3>Independent AI review (3 reviewers, not human)</h3>'
            f'<ul class="votes">{items}</ul><p class="consensus"><b>AI consensus:</b> {esc(entry["label"])}</p>{issues_html}{agree}'
            '<p class="fine">AI agreement is not independent human review. If you click Agree, the signed record says you agreed with an AI suggestion on this card.</p></section>')


def _systematic(ai: dict, cases: list[dict], groups: int) -> list[str]:
    def hits(pattern: str, only: set[str] | None = None, issues_only: bool = False) -> tuple[list[str], int]:
        found: dict[str, set[str]] = {}
        for r in AI_REVIEWERS:
            for cid, rec in ai['reviews'][r].items():
                if only is not None and cid not in only:
                    continue
                if re.search(pattern, ' '.join(rec['issues'] + ([] if issues_only else [rec['reason']])), re.I):
                    found.setdefault(cid, set()).add(r)
        reviewers = {r for rs in found.values() for r in rs}
        return sorted(found), len(reviewers)

    clarify = {c['case_id'] for c in cases if c['expected_behavior'] == 'clarify'}
    mti = {c['case_id'] for c in cases if c.get('source_group') in (MTI_GROUP, 'ai_vs_dataset')}
    revision = {c['case_id'] for c in cases if c['family'] == 'revision_conflict'}
    out = []
    ids, n = hits(r'period|d-031|2018|2019', mti)
    if ids:
        out.append(f'<b>Study period of the AI article</b> ({", ".join(ids)}; raised by {n} of 3 reviewers): the study behind the MTI article uses data from 2018 to 2024, mostly before the supported period, so whether these may be answered is your D-031 ruling.')
    ids, n = hits(r'snapshot|vintage|corpus limitation|current value', revision)
    if ids:
        out.append(f'<b>Revision cases test a missing earlier version, not a real conflict</b> ({", ".join(ids)}; {n} of 3 reviewers): the corpus holds one snapshot, so abstaining is right, but a system could reasonably still give the current value.')
    ids, n = hits(r'.', clarify, issues_only=True)
    if ids:
        out.append(f'<b>Open-ended questions have more than one reasonable answer</b> ({", ".join(ids)}; {n} of 3 reviewers): a system might list every reading instead of asking back. Decide whether that should also count as a good answer.')
    ids, n = hits(r'wording|passage says|not in the passage|only in the chart title', issues_only=True)
    if ids:
        out.append(f'<b>Minor wording mismatches</b> between the question and the source ({", ".join(ids)}; {n} of 3 reviewers): all approved, noted for the record.')
    out.append(f'<b>Fewer independent tests than cases</b> (computed from the gold file, not raised by the reviewers): {len(cases)} cases but only {groups} independent evidence groups, because near-identical cases about the same source share one group.')
    return out


def _ai_panel(ai: dict, cases: list[dict], entries: dict[str, dict], roles: dict[str, str], groups: int) -> str:
    unanimous = [cid for cid, e in entries.items() if e['class'] == 'unanimous' and e['action'] == 'approve' and e['agreeable']]
    need = sorted((cid for cid in entries if cid not in unanimous), key=lambda cid: (ai_rank(entries[cid], roles.get(cid, '')), cid))
    kinds = Counter(e['kind'] for e in entries.values())
    kinds_text = ', '.join(f'{k} {v}' for k, v in sorted(kinds.items(), key=lambda kv: (-kv[1], kv[0])))
    need_html = ''.join(f'<li><a href="#v2-{esc(cid)}" data-jump="{esc(cid)}">{esc(cid)}</a>: {esc(ai_note_text(ai, cid))}</li>' for cid in need) or '<li>None: every case was unanimously approved.</li>'
    systematic = ''.join(f'<li>{s}</li>' for s in _systematic(ai, cases, groups))
    return ('<section class="aipanel" id="aipanel"><h2>What three independent AI reviewers found</h2>'
            '<p class="warn"><b>This is not human review.</b> Three AI reviewers (A, B, C: the same model family, so their mistakes can be correlated) checked every case separately, without seeing each other. '
            'You can accept their suggestion one card at a time with “Agree with AI”. Those cards are recorded as <i>agreed with an AI suggestion</i>, counted apart from your own decisions, and never treated as independent human agreement. The signed record says so.</p>'
            f'<p>Of {len(entries)} cases, <b>{len(unanimous)}</b> were unanimously approved by all three reviewers, and <b>{len(need)}</b> need your judgement ({esc(kinds_text)}):</p>'
            f'<ul>{need_html}</ul><p><b>Systematic issues the reviewers raised:</b></p><ul>{systematic}</ul>'
            f'<p><button type="button" id="quick-ai">Review the {len(unanimous)} unanimous approvals quickly</button> '
            'One card at a time, each needing its own key press (G agrees with the AI, A approves yourself). There is no select-all.</p></section>')


def _mti_facts(ev: Evidence) -> list[str]:
    """Facts about the AI article, read from its passages rather than from memory."""
    facts: list[str] = []
    passages = [p for p in ev.passages.values() if 'feature-ai' in p['source_id'] or p['source_id'].startswith('mti-')]
    if not passages:
        return facts
    first = passages[0]
    if first.get('publication_date'):
        facts.append(f'The article was published on {first["publication_date"]} ({first["document_title"]}), which is inside the supported period.')
    pages: dict[str, list] = {'postings': [], 'stops': []}
    for p in passages:
        text = ' '.join(p['text'].split())
        if re.search(r'postings data from 2018 to 2024', text):
            pages['postings'].append(p.get('page_number'))
        if re.search(r'firms.{0,4} AI use up to 2024', text):
            pages['stops'].append(p.get('page_number'))
    def label(numbers: list) -> str:
        unique = sorted({n for n in numbers if n is not None})
        return ('Pages ' if len(unique) > 1 else 'Page ') + ', '.join(str(n) for n in unique)
    if pages['postings']:
        facts.append(f'{label(pages["postings"])}: the study identifies AI-using firms from MyCareersFuture job postings from 2018 to 2024.')
    if pages['stops']:
        facts.append(f'{label(pages["stops"])}: the article itself says its analysis of firm AI use stops at 2024, so it misses the more recent advances.')
    return facts


def _evidence_html(c: dict, ev: Evidence) -> str:
    parts: list[str] = []
    supporting = [pid for e in c.get('evidence_text', []) for pid in e['passage_ids']] + [oid for e in c.get('evidence_data', []) for oid in e['observation_ids']]
    context = [pid for e in c.get('context_only_evidence_text', []) for pid in e['passage_ids']] + [oid for e in c.get('context_only_evidence_data', []) for oid in e['observation_ids']]
    if supporting:
        parts.append('<h3>Evidence for the expected answer</h3>' + ''.join(ev.render(i) for i in dict.fromkeys(supporting)))
    if context:
        parts.append('<h3>Background evidence (shows why the system should not simply answer)</h3>' + ''.join(ev.render(i) for i in dict.fromkeys(context)))
    if not parts:
        parts.append('<h3>Evidence</h3><p>This case needs no source evidence: the right behaviour follows from the question itself.</p>')
    return ''.join(parts)


def _banner(c: dict, facts: list[str], counts: dict, role: str, ai_note: str = '', ai_split: bool = False) -> str:
    ai_html = f'<p class="aiview"><b>AI reviewers’ view (not human; you decide):</b> {esc(ai_note)}</p>' if ai_note else ''
    if role == 'related':
        owner = ('<p><b>Owner decision:</b> keep the answer with a caveat (Approve) or drop the case (Reject). The three reviewers did not agree, so this is not decided by consensus. '
                 'If you relabel HO-V2-022 to abstain, ask yourself whether the same reasoning (the study period) applies to this case.</p>') if ai_split else ''
        return ('<aside class="banner related"><strong>Related to the AI-article question (D-031).</strong> This case also uses the same AI article '
                '(its finding on productivity). Whatever you decide for HO-V2-022, which states the same finding, keeps this one consistent.'
                f'{ai_html}{owner}</aside>')
    bullets = ''.join(f'<li>{esc(f)}</li>' for f in facts) or '<li>(the article passages were not available to this build)</li>'
    common = (f'<aside class="banner mti"><strong>Scope question D-031 — your decision needed.</strong>'
              '<p>Our supported period is <b>Q1 2024 to Q2 2026</b>. Rule D-031: a question about an earlier period must get an abstention, even if the corpus has the answer, and a publication date inside the period does not change that. '
              'The guide says the same: “subjects before 1Q 2024 are abstain”.</p>'
              f'<p>What the evidence actually says (checked in the passages):</p><ul>{bullets}'
              '<li>So the numbers this article gives are pooled estimates from firm data of 2018 to 2024, not figures for a quarter inside the supported period.</li></ul>')
    if role == 'choice':
        after = counts.get(c['case_id'])
        return common + ai_html + (
            '<p><b>Choose one:</b></p><ul>'
            '<li><b>Keep as answerable</b>: you treat the article, published in Q2 2026, as an in-period source. The system must then give the number.</li>'
            '<li><b>Relabel to abstain</b> <span class="rec">recommended</span>: you treat the study period as the subject. The system must then decline. The facts become background evidence.</li>'
            f'<li><b>Drop the case</b>: remove it from the frozen test. Relabelling or dropping lowers the count of independent evidence groups from {counts["__total__"]} to {after}; the minimum to approve is {MIN_COMPONENTS}.</li></ul>'
            '<p><b>Recommendation (an AI’s, not a ruling):</b> relabel to abstain. The study data end in 2024 and mostly start before 2024, and D-031 and the guide say a subject before 1Q 2024 is abstain regardless of when the article appeared. '
            'Choosing “keep” is defensible if you read the question as asking what the article says, but it then conflicts with the written rule. '
            'The cost of relabelling is the lost evidence groups (shown live at the top); the benefit is that the frozen test follows D-031 as written.</p></aside>')
    return common + ai_html + ('<p>This case is an abstention <b>whatever you decide above for the other AI-article cases</b>: it asks for something the article does not give. '
                               'Approve it unless you disagree with the label itself.</p></aside>')


def _controls(cid: str, mti: bool, behaviour: str) -> str:
    chips = ''.join(
        f'<button type="button" data-beh="{b}"{" disabled" if b == behaviour else ""}>{esc(SHORT[b])} <kbd>{n}</kbd></button>'
        for n, b in enumerate(BEHAVIOURS, 1))
    mti_block = ''
    if mti:
        mti_block = ('<div class="mti-choice" role="group" aria-label="D-031 choice"><p><b>D-031 choice for this case</b> (no option is preselected):</p>'
                     '<button type="button" data-mti="keep_answerable">Keep as answerable</button>'
                     '<button type="button" data-mti="relabel_abstain">Relabel to abstain <em>(recommended)</em></button>'
                     '<button type="button" data-mti="drop">Drop the case</button></div>')
    return (f'<div class="decision" data-case-controls="{esc(cid)}">{mti_block}'
            '<div class="buttons" role="group" aria-label="Your decision">'
            '<button type="button" class="big" data-act="approve">Approve <kbd>A</kbd></button>'
            '<button type="button" class="big" data-act="change">Change label <kbd>C</kbd></button>'
            '<button type="button" class="big" data-act="reject">Reject <kbd>X</kbd></button></div>'
            f'<div class="change-panel" hidden><p>What should the system do instead? (keys 1 to 5)</p><div class="chips">{chips}</div></div>'
            '<label class="reason" hidden>Short reason (required)<textarea data-field="reason" rows="2" maxlength="2000"></textarea></label>'
            '<label>Comment (optional)<textarea data-field="comment" rows="2" maxlength="4000"></textarea></label>'
            '<p class="status" aria-live="polite"></p></div>')


def _card(c: dict, ev: Evidence, comp: dict[str, str], role: str, facts: list[str], counts: dict, ai: dict | None = None) -> str:
    cid = c['case_id']
    behaviour = c['expected_behavior']
    why = c.get('abstain_reason') or ''
    if behaviour == 'answer':
        why = why or 'The evidence on the right contains the requested fact.'
        if c.get('difficulty_note'):
            why += ' Note from the author: ' + c['difficulty_note']
    elif not why:
        why = c.get('difficulty_note') or 'See the question.'
    trick = c.get('adversarial')
    trick_html = para('Trick in the question: ' + str(trick.get('type', trick))) if isinstance(trick, dict) else ''
    facts_html = ''.join(para(f) for f in c.get('reference_facts', [])) or para('No figures expected: this label does not depend on a number.')
    if c.get('calculation'):
        facts_html += '<details><summary>How the expected number is calculated</summary><pre>' + esc(json.dumps(c['calculation'], indent=1, ensure_ascii=False)) + '</pre></details>'
    carries = '1' if paired.evidence_ids(c) else '0'
    entry = ai_entry(ai, cid) if ai else None
    banner = _banner(c, facts, counts, role, ai_note_text(ai, cid) if ai else '', bool(entry and not entry['agreeable'])) if role else ''
    ai_html = _ai_strip(ai, cid) if ai else ''
    ai_attrs = f' data-ai-class="{entry["class"]}" data-ai-action="{entry["action"] or ""}"' if entry else ''
    return (f'<article class="card" id="v2-{esc(cid)}" data-case="{esc(cid)}" data-behavior="{esc(behaviour)}" data-component="{esc(comp[cid])}" data-evidence="{carries}" data-role="{role}"{ai_attrs} hidden>'
            f'<h2>{esc(cid)} <span class="tag">{esc(FAMILY_PLAIN.get(c["family"], c["family"]))}</span></h2>{banner}'
            '<div class="split"><div class="left">'
            f'<section><h3>The question</h3><p class="question">{esc(c["question"])}</p>{trick_html}</section>'
            f'<section><h3>What the system should do</h3><p><strong class="behaviour">{esc(behaviour.replace("_", " "))}</strong>: {esc(SENTENCES[behaviour])}</p><p class="why">Why: {esc(why)}</p></section>'
            f'<section><h3>Expected facts or numbers</h3>{facts_html}</section>{ai_html}'
            + _controls(cid, role == 'choice', behaviour) +
            '</div><div class="right"><p class="check"><strong>What to check:</strong> does the evidence support the expected answer? Look at the highlighted box on the page, or the highlighted table row.</p>'
            + _evidence_html(c, ev) + '</div></div></article>')


START = '''<section class="start" id="start"><h1>Held-out v2: approve the 65 test questions</h1>
<p class="private">PRIVATE: contains MOM and MTI text; do not commit or share this page or your export.</p>
{ai_panel}
<h2>Start here</h2>
<ol>
<li><b>Read the flagged AI-article cases first.</b> They come first, with a yellow note. They ask whether a study of 2018 to 2024 data belongs in a test about Q1 2024 to Q2 2026.</li>
<li><b>Go through the other cases with the keyboard.</b> Read the question and what the system should do, look at the evidence on the right, then press <kbd>A</kbd> to approve, <kbd>C</kbd> to change the label or <kbd>X</kbd> to reject. Where the AI reviewers agree you may also press <kbd>G</kbd> (it unlocks a few seconds after the card appears).</li>
<li><b>Download the file and run one command.</b> Type your name, click Download, then run <code>uv run labourlens v2-approve --review-export &lt;the downloaded file&gt;</code> (it first shows a preview; add <code>--write</code> to sign).</li>
</ol>
<h3>What the buttons mean</h3>
<ul><li><b>Approve</b>: the question, the expected behaviour and the expected facts are right as drafted.</li>
<li><b>Change label</b>: the question is fine but the system should do something else (answer, abstain, clarify, refuse, ignore-the-trick-and-answer). Pick which, and give a one-line reason.</li>
<li><b>Reject</b>: this question should not be in the test (unclear, wrong or out of scope). Give a one-line reason.</li>
<li><b>Agree with AI</b> (only where the three AI reviewers agree): you accept their suggested decision for this card. It is recorded as an AI-assisted decision, not as your own independent judgement.</li></ul>
<h3>What approving commits you to</h3>
<p><b>These questions and their expected answers become the frozen test.</b> Once the run starts you cannot change, drop or relabel any of them, because doing so after seeing results would invalidate the comparison. Approving runs nothing and costs nothing. {cost}</p>
<p>Nothing is filled in for you. A card only counts once you press a button (and give a reason when you change or reject).</p>
</section>'''


def _cost_sentence(root: Path, n: int) -> str:
    q = cost_quote(root, n)
    return f'The later run costs about ${q["total"]:.2f} at saved prices (a quote, not a cap).' if q else ''


def build_v2_page(root: Path = ROOT) -> Path:
    root = Path(root).resolve()
    destination = root / PAGE
    if subprocess.run(['git', 'check-ignore', '--quiet', str(destination)], cwd=root, check=False).returncode != 0:
        raise ValueError('The review page must be gitignored before it can contain MOM text')
    draft = root / DRAFT
    cases = rows(draft)
    draft_sha = sha256_file(draft)
    ev = Evidence(root, label='corpus v3', dpi=96, quality=62, compact=True)
    comp = paired.components(cases)
    facts = _mti_facts(ev)
    flagged = [c for c in cases if c.get('source_group') == MTI_GROUP]
    related = [c for c in cases if c.get('source_group') == 'ai_vs_dataset']
    choice_ids = {c['case_id'] for c in flagged if c['expected_behavior'] == 'answer'}
    counts = {'__total__': evidence_component_count(cases)}
    for cid in choice_ids:
        counts[cid] = evidence_component_count([c for c in cases if c['case_id'] != cid])
    roles = {c['case_id']: ('choice' if c['case_id'] in choice_ids else 'flag' if c in flagged else 'related' if c in related else '') for c in cases}
    ai = load_ai(root, cases)
    entries = {c['case_id']: ai_entry(ai, c['case_id']) for c in cases} if ai else {}
    if ai:
        order = sorted(cases, key=lambda c: (ai_rank(entries[c['case_id']], roles[c['case_id']]), c['case_id']))
    else:
        order = flagged + related + [c for c in cases if c not in flagged and c not in related]
    cards = [_card(c, ev, comp, roles[c['case_id']], facts, counts, ai) for c in order]
    meta = {c['case_id']: {'behavior': c['expected_behavior'], 'component': comp[c['case_id']], 'evidence': bool(paired.evidence_ids(c))} for c in cases}
    panel = _ai_panel(ai, cases, entries, roles, counts['__total__']) if ai else ''
    start = START.replace('{ai_panel}', panel).replace('{cost}', esc(_cost_sentence(root, len(cases))))
    ai_js = {cid: {k: e[k] for k in ('class', 'action', 'behaviour', 'label', 'voters', 'votes', 'agreeable')} for cid, e in entries.items()}
    page = (HEAD + TOOLBAR + start + '<main id="cards">' + ''.join(cards) + '</main>' + FOOT
            + '<script>const PACK_ID=' + json.dumps(pack_id_for(draft_sha)) + ';const GOLD_SHA=' + json.dumps(draft_sha) + ';const BEHAVIOURS=' + json.dumps(list(BEHAVIOURS))
            + ';const META=' + json.dumps(meta) + ';const MTI_REASONS=' + json.dumps(MTI_REASONS) + ';const LIMITS=' + json.dumps({'cases': MIN_CASES, 'non_answer': MIN_NON_ANSWER, 'components': MIN_COMPONENTS})
            + ';const AI=' + json.dumps(ai_js).replace('<', '\\u003c') + ';const AI_SHA=' + json.dumps(ai['sha256'] if ai else {}) + ';const AI_SOURCE=' + json.dumps(AI_SOURCE)
            + ';const PAGE_IMAGES=' + json.dumps(ev.images).replace('<', '\\u003c') + ';</script><script>' + SCRIPT + '</script></body></html>')
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(page)
    return destination


HEAD = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; connect-src 'none'; form-action 'none'; base-uri 'none'">
<title>Held-out v2 owner review (private)</title><style>
:root{font:16px/1.55 system-ui,sans-serif;color:#17303a;background:#eef2f1}*{box-sizing:border-box}body{margin:0;padding-bottom:120px}
.start{max-width:1000px;margin:auto;padding:20px 24px;background:#fff}.start h1{font-size:1.6rem;margin:.2em 0}.private{background:#802e25;color:#fff;padding:8px 12px}
kbd{font:700 .8em ui-monospace,monospace;border:1px solid #888;border-radius:4px;padding:1px 6px;background:#f3f3f3;margin-left:4px}code{background:#f1f1f1;padding:1px 5px}
.bar{position:sticky;top:0;z-index:20;background:#fff;border-bottom:2px solid #276b70;padding:8px 16px;box-shadow:0 2px 8px #0002}.bar .row{display:flex;gap:14px;flex-wrap:wrap;align-items:center;max-width:1400px;margin:auto}
progress{width:260px;accent-color:#276b70}.sum span{display:inline-block;margin-right:12px;font-weight:700}.gate{font-size:.85rem}.gate b.bad{color:#9b1c1c}.gate b.ok{color:#1b6b3a}
button{font:inherit;cursor:pointer;padding:6px 12px;border:1px solid #276b70;border-radius:5px;background:#fff;color:#164b50}button[aria-pressed=true]{background:#164b50;color:#fff}button:disabled{opacity:.45;cursor:default}
button[aria-pressed=true] kbd{color:#164b50}
button.big{font-size:1.2rem;font-weight:700;min-height:54px;min-width:150px;border-width:2px}main{max-width:1450px;margin:auto;padding:12px 16px}
.card{background:#fff;border:1px solid #cad6d5;border-radius:8px;padding:16px 20px;margin:12px 0}.card h2{margin:.1em 0}.tag{font-size:.8rem;font-weight:600;background:#e9eef3;border:1px solid #9bb0c4;border-radius:10px;padding:1px 10px;margin-left:8px}
.split{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.2fr);gap:22px;align-items:start}.right{position:sticky;top:var(--bar,150px);max-height:calc(100vh - var(--bar,150px) - 120px);overflow:auto;padding:8px;border-left:3px solid #276b70;background:#f5f9f8}
.question{font-size:1.15rem;font-weight:600}.behaviour{text-transform:uppercase;color:#164b50}.why{opacity:.9}.check{background:#e8f3ef;padding:8px 10px}
h3{font-size:.95rem;letter-spacing:.03em;margin:.9em 0 .3em}.banner{border-left:6px solid #c07500;background:#fff8e1;padding:10px 14px;margin:10px 0}.banner.related{background:#eef3fb;border-color:#4a6fa5}.rec{background:#2b7a4b;color:#fff;border-radius:8px;padding:0 8px;font-size:.8rem}
.decision{margin-top:14px;padding-top:10px;border-top:2px solid #cad6d5}.buttons{display:flex;gap:10px;flex-wrap:wrap}.chips{display:flex;flex-wrap:wrap;gap:8px}.mti-choice{background:#fff8e1;padding:8px;margin-bottom:10px;border:1px solid #e0c36a;border-radius:6px}.mti-choice button{margin:2px 6px 2px 0}
textarea{display:block;width:100%;border:1px solid #899f9c;padding:6px;font:inherit}label{display:block;margin:8px 0}.status{font-weight:700}.status.ok{color:#1b6b3a}.status.todo{color:#8a5a00}
.evidence{border-top:1px solid #b9ccca;margin-top:10px;padding-top:6px}.evidence p{margin:4px 0;font-size:.85rem}.evidence h4{margin:4px 0;font-size:.95rem}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.5 ui-monospace,monospace;background:#f3f5f5;padding:8px}
.pdf-page{position:relative;line-height:0}.pdf-page img{width:100%;height:auto}.bbox{position:absolute;border:2px solid #c07500;background:#ffd80030;pointer-events:none}figure{margin:0}.source-comparison{display:flex;flex-direction:column-reverse;gap:8px}
table{border-collapse:collapse;font-size:.85rem}td,th{border:1px solid #a6bbb8;padding:4px 6px}.cited{background:#fff1a8}.table-scroll{overflow:auto}mark{background:#fff1a8}
.nav{position:fixed;bottom:0;left:0;right:0;background:#fff;border-top:2px solid #276b70;padding:8px;z-index:30;text-align:center}.nav .strip{font-size:.85rem;margin-bottom:6px}.nav button{font-weight:700;min-height:44px;margin:0 6px}
#notice{color:#8c2520;font-weight:600;margin:0}#storage{color:#8c2520;font-weight:700;margin:0}[hidden]{display:none!important}
@media(max-width:900px){.split{grid-template-columns:1fr}.right{position:static;max-height:none}}
.aipanel{background:#eef3fb;border:2px solid #4a6fa5;border-radius:8px;padding:6px 18px;margin:14px 0}.aipanel .warn{background:#fff3cd;border-left:6px solid #c07500;padding:8px 12px}.aipanel li{margin:4px 0}
.aistrip{background:#f1f5fb;border:1px solid #4a6fa5;border-radius:8px;padding:2px 12px;margin:12px 0}.aistrip ul{list-style:none;padding:0;margin:4px 0}.aistrip li{margin:6px 0}.chip{display:inline-block;border-radius:10px;padding:0 9px;font-weight:700;font-size:.85rem;border:1px solid #888}
.chip.v-approve{background:#e3f4e8;border-color:#1b6b3a;color:#1b6b3a}.chip.v-change_label{background:#fff3cd;border-color:#8a5a00;color:#6b4500}.chip.v-reject{background:#fde4e4;border-color:#9b1c1c;color:#9b1c1c}
.conf{font-size:.8rem;opacity:.85}.areason{font-size:.9rem}.fine,.aissues{font-size:.82rem}.nosplit{background:#fff3cd;padding:6px 10px}button.agree{font-weight:700;border-width:2px;background:#e8f0fb}.wait{font-size:.8rem;opacity:.8}
#quick-banner{background:#fff3cd;border:1px solid #c07500;padding:4px 10px;font-size:.88rem}
button.agree[aria-pressed=true]{background:#164b50;color:#fff}button.agree[aria-pressed=true]:disabled{opacity:1}
</style></head><body>'''

TOOLBAR = '''<div class="bar"><div class="row"><progress id="progress" value="0" max="65" aria-label="Decided cases"></progress><strong id="progress-text"></strong>
<span class="sum" id="summary"></span><label>Your name <input id="reviewer" maxlength="200" autocomplete="off" placeholder="Type your own name"></label>
<label><input type="checkbox" id="show-decided"> show decided</label><label>Jump <select id="jump"></select></label><button id="download">Download review file</button>
<button id="toggle-start">Start here</button></div><div class="row gate" id="gate"></div><div class="row" id="quick-banner" hidden><span><b>Quick review of unanimous AI approvals.</b> One key press per card: <kbd>G</kbd> agree with the AI, <kbd>A</kbd> approve yourself, <kbd>C</kbd>/<kbd>X</kbd> disagree. AI agreement is not independent human review.</span> <button id="quick-exit" type="button">Exit quick review</button></div><p id="notice" role="status"></p><p id="storage" role="alert"></p></div>'''

FOOT = '''<div class="nav"><div class="strip"><kbd>A</kbd> approve · <kbd>C</kbd> change label · <kbd>X</kbd> reject · <kbd>G</kbd> agree with AI (when shown) · <kbd>1</kbd>–<kbd>5</kbd> pick the new behaviour · <kbd>Enter</kbd> next · <kbd>Backspace</kbd> previous · <kbd>Esc</kbd> leave a text box</div>
<button id="prev">Previous</button><span id="position"></span><button id="next">Next</button><button id="next-open">Next undecided</button></div>'''

SCRIPT = r'''
const cards = [...document.querySelectorAll('article.card')];
const prefix = 'labourlens-heldout-v2:' + PACK_ID + ':';
const memory = new Map(); let active = '', quick = false, lastActive = '', shownAt = Date.now(); const WAIT_MS = 3000;
const blank = () => ({decision:'', proposed_behavior:'', reason:'', comment:'', mti_choice:'', source:'', ai_basis:null, timestamp:''});
function warn() { document.querySelector('#storage').textContent = 'Autosave is unavailable: your choices stay in this page only. Download the file before closing.'; }
function load(key) { if (memory.has(key)) return memory.get(key); try { const v = JSON.parse(localStorage.getItem(prefix + key) || 'null'); if (v) memory.set(key, v); return v; } catch (e) { warn(); return null; } }
function save(key, value) { memory.set(key, value); try { localStorage.setItem(prefix + key, JSON.stringify(value)); } catch (e) { warn(); } }
try { localStorage.setItem(prefix + 'probe', '1'); localStorage.removeItem(prefix + 'probe'); } catch (e) { warn(); }
const state = new Map(cards.map(c => [c.dataset.case, Object.assign(blank(), load(c.dataset.case) || {})]));
const get = c => state.get(c.dataset.case);
function complete(s) {
  if (s.decision === 'approve') return true;
  if (s.decision === 'change') return BEHAVIOURS.includes(s.proposed_behavior) && s.reason.trim() !== '';
  if (s.decision === 'reject') return s.reason.trim() !== '';
  return false;
}
function effective(c) { const s = get(c); return s.decision === 'change' ? s.proposed_behavior : c.dataset.behavior; }
function persist(c) { const s = get(c); s.timestamp = new Date().toISOString(); save(c.dataset.case, s); }
function paint(c) {
  const s = get(c), box = c.querySelector('.decision');
  box.querySelectorAll('[data-act]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.act === s.decision)));
  box.querySelectorAll('[data-mti]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.mti === s.mti_choice)));
  box.querySelectorAll('[data-beh]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.beh === s.proposed_behavior)));
  const ag = c.querySelector('[data-agree]'); if (ag) ag.setAttribute('aria-pressed', String(s.source === AI_SOURCE && complete(s)));
  box.querySelector('.change-panel').hidden = s.decision !== 'change';
  const reason = box.querySelector('.reason'); reason.hidden = !(s.decision === 'change' || s.decision === 'reject');
  const fields = box.querySelectorAll('[data-field]'); fields.forEach(f => { if (document.activeElement !== f) f.value = s[f.dataset.field] || ''; });
  const st = box.querySelector('.status');
  let text = 'Not decided yet.', cls = 'todo';
  if (s.decision === 'approve') { text = 'Approved as drafted.'; cls = 'ok'; }
  else if (s.decision === 'change') { text = complete(s) ? 'Change label to “' + s.proposed_behavior.replaceAll('_', ' ') + '”.' : 'Change label: pick the new behaviour and write a reason.'; cls = complete(s) ? 'ok' : 'todo'; }
  else if (s.decision === 'reject') { text = complete(s) ? 'Rejected.' : 'Reject: write a short reason.'; cls = complete(s) ? 'ok' : 'todo'; }
  st.textContent = text + (s.source === AI_SOURCE && complete(s) ? ' (you agreed with the AI suggestion)' : ''); st.className = 'status ' + cls;
}
function summary() {
  const done = cards.filter(c => complete(get(c)));
  const n = d => done.filter(c => get(c).decision === d).length;
  document.querySelector('#progress').max = cards.length; document.querySelector('#progress').value = done.length;
  document.querySelector('#progress-text').textContent = done.length + ' of ' + cards.length + ' decided';
  const viaAi = done.filter(c => get(c).source === AI_SOURCE).length;
  document.querySelector('#summary').innerHTML = '<span>' + n('approve') + ' approve</span><span>' + n('change') + ' need change</span><span>' + n('reject') + ' reject</span>' + (Object.keys(AI).length ? '<span>' + (done.length - viaAi) + ' by your own click</span><span>' + viaAi + ' agreed with AI</span>' : '');
  // Gate if every undecided case ends up approved as drafted. Components are estimated from the drafted grouping.
  const kept = cards.filter(c => get(c).decision !== 'reject' || !complete(get(c)));
  const nonAnswer = kept.filter(c => effective(c) !== 'answer').length;
  const comps = new Set(kept.filter(c => c.dataset.evidence === '1' && ['answer', 'ignore_injection_and_answer'].includes(effective(c))).map(c => c.dataset.component));
  const item = (label, v, need) => '<span>' + label + ': <b class="' + (v >= need ? 'ok' : 'bad') + '">' + v + '</b> (need ' + need + ')</span>';
  document.querySelector('#gate').innerHTML = 'Acceptance check if the undecided cases are approved as drafted: ' + item('cases kept', kept.length, LIMITS.cases) + ' ' + item('non-answer cases', nonAnswer, LIMITS.non_answer) + ' ' + item('independent evidence groups', comps.size, LIMITS.components);
}
function isQuickCard(c) { const e = AI[c.dataset.case]; return !!e && e.agreeable && e.class === 'unanimous' && e.action === 'approve'; }
function queue() {
  const showAll = document.querySelector('#show-decided').checked;
  if (quick) return cards.filter(c => isQuickCard(c) && (!complete(get(c)) || c.dataset.case === active));
  return cards.filter(c => showAll || !complete(get(c)) || c.dataset.case === active);
}
function render() {
  const q = queue();
  if (!q.some(c => c.dataset.case === active)) active = q.length ? q[0].dataset.case : '';
  if (active !== lastActive) { lastActive = active; shownAt = Date.now(); }
  cards.forEach(c => { c.hidden = c.dataset.case !== active; paint(c); });
  const current = cards.find(c => c.dataset.case === active);
  if (current) current.querySelectorAll('img[data-page]').forEach(img => { if (!img.src.startsWith('data:')) img.src = 'data:image/jpeg;base64,' + PAGE_IMAGES[img.dataset.page]; });
  const idx = q.findIndex(c => c.dataset.case === active);
  const allDone = cards.every(c => complete(get(c)));
  const quickLeft = cards.filter(x => isQuickCard(x) && !complete(get(x))).length;
  document.querySelector('#position').textContent = quick ? (quickLeft ? 'Quick review: ' + quickLeft + ' unanimous approvals still to review · ' + active : 'Quick review finished: every unanimous approval has a decision. Exit quick review.') : allDone && !document.querySelector('#show-decided').checked ? 'All ' + cards.length + ' decided: type your name and click Download.' : q.length ? 'Card ' + (idx + 1) + ' of ' + q.length + ' · ' + active : 'No cards to show.';
  document.querySelector('#prev').disabled = idx <= 0; document.querySelector('#next').disabled = idx < 0 || idx >= q.length - 1;
  document.querySelector('#next-open').disabled = !cards.some(c => !complete(get(c)));
  const jump = document.querySelector('#jump');
  [...jump.options].forEach((o, i) => { const c = cards[i]; o.textContent = (complete(get(c)) ? '✓ ' : '· ') + c.dataset.case; });
  jump.value = active;
  summary(); document.querySelector('#quick-banner').hidden = !quick; tickAgree();
  document.documentElement.style.setProperty('--bar', document.querySelector('.bar').offsetHeight + 12 + 'px');
}
function move(d) { const q = queue(), i = q.findIndex(c => c.dataset.case === active); if (q[i + d]) { active = q[i + d].dataset.case; render(); } }
function nextOpen() { quick = false; const i = cards.findIndex(c => c.dataset.case === active); for (let k = 1; k <= cards.length; k++) { const c = cards[(i + k) % cards.length]; if (!complete(get(c))) { active = c.dataset.case; render(); return; } } }
function decide(c, act) {
  const s = get(c);
  s.decision = act; s.source = 'owner_manual'; s.ai_basis = null;
  if (act === 'approve') { s.proposed_behavior = ''; s.reason = ''; s.mti_choice = c.dataset.role === 'choice' ? 'keep_answerable' : ''; }
  else if (c.dataset.role === 'choice' && !((act === 'change' && s.mti_choice === 'relabel_abstain') || (act === 'reject' && s.mti_choice === 'drop'))) s.mti_choice = '';
  persist(c); render();
  if (act === 'approve') setTimeout(() => { const q = queue(), i = q.findIndex(x => x.dataset.case === active); if (q[i + 1]) { active = q[i + 1].dataset.case; render(); } }, 0);
}
function mti(c, choice) {
  const s = get(c); s.mti_choice = choice; s.source = 'owner_manual'; s.ai_basis = null;
  if (choice === 'keep_answerable') { s.decision = 'approve'; s.proposed_behavior = ''; s.reason = ''; }
  else if (choice === 'relabel_abstain') { s.decision = 'change'; s.proposed_behavior = 'abstain'; s.reason = MTI_REASONS.relabel_abstain; }
  else { s.decision = 'reject'; s.proposed_behavior = ''; s.reason = MTI_REASONS.drop; }
  persist(c); render();
}
function agreeLeft() { return Math.max(0, WAIT_MS - (Date.now() - shownAt)); }
function tickAgree() {
  const c = cards.find(x => x.dataset.case === active), b = c && c.querySelector('[data-agree]'); if (!b) return;
  const left = agreeLeft(), agreed = b.getAttribute('aria-pressed') === 'true'; b.disabled = left > 0 && !agreed;
  const w = c.querySelector('.wait'); if (w) w.textContent = left > 0 && !agreed ? '(unlocks in ' + Math.ceil(left / 1000) + ' s: read the evidence first)' : '';
}
function agree(c) {
  const e = AI[c.dataset.case]; if (!e || !e.agreeable) return;
  if (agreeLeft() > 0) { document.querySelector('#notice').textContent = 'Read the question and the evidence first: “Agree with AI” unlocks a few seconds after the card appears.'; return; }
  document.querySelector('#notice').textContent = '';
  const s = get(c), choice = c.dataset.role === 'choice';
  s.source = AI_SOURCE; s.ai_basis = {consensus: e.label, class: e.class, votes: e.votes};
  if (e.action === 'approve') { s.decision = 'approve'; s.proposed_behavior = ''; s.reason = ''; s.mti_choice = choice ? 'keep_answerable' : ''; }
  else if (e.action === 'change') { s.decision = 'change'; s.proposed_behavior = e.behaviour; s.reason = (choice && e.behaviour === 'abstain' ? MTI_REASONS.relabel_abstain + ' ' : '') + 'Agreed with the AI reviewers’ consensus (' + e.voters.join(', ') + '): change to ' + e.behaviour.replaceAll('_', ' ') + '.'; s.mti_choice = choice && e.behaviour === 'abstain' ? 'relabel_abstain' : ''; }
  else { s.decision = 'reject'; s.proposed_behavior = ''; s.reason = 'Agreed with the AI reviewers’ consensus (' + e.voters.join(', ') + '): reject.'; s.mti_choice = choice ? 'drop' : ''; }
  persist(c); render();
  setTimeout(() => { const q = queue(), i = q.findIndex(x => x.dataset.case === active); if (q[i + 1]) { active = q[i + 1].dataset.case; render(); } }, 0);
}
document.addEventListener('click', e => {
  const b = e.target.closest('button'); const c = b && b.closest('article.card');
  if (!c) return;
  const s = get(c);
  if (b.dataset.act) decide(c, b.dataset.act);
  else if (b.dataset.mti) mti(c, b.dataset.mti);
  else if (b.dataset.agree !== undefined) agree(c);
  else if (b.dataset.beh) { s.decision = 'change'; s.source = 'owner_manual'; s.ai_basis = null; s.proposed_behavior = b.dataset.beh; if (c.dataset.role === 'choice' && !(b.dataset.beh === 'abstain' && s.mti_choice === 'relabel_abstain')) s.mti_choice = ''; persist(c); render(); }
});
document.addEventListener('input', e => {
  const f = e.target.closest('[data-field]'); const c = f && f.closest('article.card');
  if (!c) return;
  const s = get(c); s[f.dataset.field] = f.value;
  persist(c); paint(c); summary(); document.querySelector('#next-open').disabled = !cards.some(x => !complete(get(x)));
});
document.addEventListener('keydown', e => {
  if (e.ctrlKey || e.metaKey || e.altKey) return;
  const t = e.target;
  if (t.matches('textarea,input,select')) { if (e.key === 'Escape') t.blur(); return; }
  if (t.matches('button') && (e.key === 'Enter' || e.key === ' ')) return;
  const c = cards.find(x => x.dataset.case === active); if (!c) return;
  const k = e.key.length === 1 ? e.key.toLowerCase() : e.key;
  if (k === 'a') { e.preventDefault(); decide(c, 'approve'); }
  else if (k === 'g') { e.preventDefault(); agree(c); }
  else if (k === 'c') { e.preventDefault(); decide(c, 'change'); }
  else if (k === 'x') { e.preventDefault(); decide(c, 'reject'); const r = c.querySelector('[data-field=reason]'); if (r) r.focus(); }
  else if (/^[1-5]$/.test(k) && get(c).decision === 'change') { const b = c.querySelectorAll('[data-beh]')[Number(k) - 1]; if (b && !b.disabled) { e.preventDefault(); b.click(); const r = c.querySelector('[data-field=reason]'); if (r) r.focus(); } }
  else if (k === 'Enter' || k === 'j') { e.preventDefault(); move(1); }
  else if (k === 'Backspace' || k === 'k') { e.preventDefault(); move(-1); }
});
document.querySelector('#prev').addEventListener('click', () => move(-1));
document.querySelector('#next').addEventListener('click', () => move(1));
document.querySelector('#next-open').addEventListener('click', nextOpen);
document.querySelector('#show-decided').addEventListener('change', render);
document.querySelector('#toggle-start').addEventListener('click', () => { const s = document.querySelector('#start'); s.hidden = !s.hidden; if (!s.hidden) window.scrollTo(0, 0); });
const jump = document.querySelector('#jump');
cards.forEach(c => { const o = document.createElement('option'); o.value = c.dataset.case; jump.append(o); });
jump.addEventListener('change', () => { quick = false; document.querySelector('#show-decided').checked = true; active = jump.value; render(); });
document.addEventListener('click', e => {
  const a = e.target.closest('a[data-jump]'); if (!a) return;
  e.preventDefault(); quick = false; document.querySelector('#show-decided').checked = true; active = a.dataset.jump; render();
  window.scrollTo(0, document.querySelector('#cards').offsetTop - document.querySelector('.bar').offsetHeight);
});
const quickBtn = document.querySelector('#quick-ai');
if (quickBtn) quickBtn.addEventListener('click', () => { quick = true; document.querySelector('#start').hidden = true; active = ''; render(); window.scrollTo(0, 0); });
document.querySelector('#quick-exit').addEventListener('click', () => { quick = false; render(); });
document.querySelector('#download').addEventListener('click', () => {
  const name = document.querySelector('#reviewer').value.trim(), notice = document.querySelector('#notice');
  if (!name) { notice.textContent = 'Type your own name first: it is recorded with your decisions.'; return; }
  const results = cards.map(c => { const s = get(c), done = complete(s), viaAi = done && s.source === AI_SOURCE; return {case_id: c.dataset.case, decision: s.decision, proposed_behavior: s.decision === 'change' ? s.proposed_behavior : '', reason: s.decision === 'approve' ? '' : s.reason.trim(),
    comment: s.comment, mti_choice: s.mti_choice, decision_source: done ? (viaAi ? AI_SOURCE : 'owner_manual') : '', ai_basis: viaAi ? s.ai_basis : {}, timestamp: s.timestamp || new Date().toISOString()}; }).sort((a, b) => a.case_id < b.case_id ? -1 : 1);
  const data = {schema_version: 1, kind: 'heldout_v2_review', pack_id: PACK_ID, gold_sha256: GOLD_SHA, reviewer_name: name, exported_at: new Date().toISOString(), ai_files_sha256: AI_SHA, results};
  const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'}));
  const a = document.createElement('a'); a.href = url; a.download = 'heldout-v2-review.json'; document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 5000);
  const open = cards.filter(c => !complete(get(c))).length;
  notice.textContent = open ? 'Downloaded a DRAFT: ' + open + ' cards are still undecided, so v2-approve will refuse it until you finish.' : 'Downloaded. Now run: uv run labourlens v2-approve --review-export <the file>';
});
setInterval(tickAgree, 250);
render();
'''


# ---------------------------------------------------------------- strict export and approval

class V2Result(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    case_id: str
    decision: str
    proposed_behavior: str = ''
    reason: str = ''
    comment: str = Field(default='', max_length=4000)
    mti_choice: str = ''
    decision_source: str = ''
    ai_basis: dict = Field(default_factory=dict)
    timestamp: str

    @model_validator(mode='after')
    def valid(self):
        if not re.fullmatch(r'HO-V2-\d{3}', self.case_id):
            raise ValueError(f'Invalid case id {self.case_id}')
        parse_timestamp(self.timestamp)
        if self.decision not in DECISIONS:
            raise ValueError(f'{self.case_id}: not decided ({self.decision!r})')
        if self.decision_source not in ('owner_manual', AI_SOURCE):
            raise ValueError(f'{self.case_id}: decision_source must be owner_manual or {AI_SOURCE}')
        if self.decision_source == AI_SOURCE and not self.ai_basis:
            raise ValueError(f'{self.case_id}: {AI_SOURCE} needs an ai_basis')
        if self.decision_source == 'owner_manual' and self.ai_basis:
            raise ValueError(f'{self.case_id}: an owner_manual decision carries no ai_basis')
        if self.decision == 'change' and self.proposed_behavior not in BEHAVIOURS:
            raise ValueError(f'{self.case_id}: change needs a valid proposed_behavior')
        if self.decision != 'change' and self.proposed_behavior:
            raise ValueError(f'{self.case_id}: only a change may carry proposed_behavior')
        if self.decision in ('change', 'reject') and not self.reason.strip():
            raise ValueError(f'{self.case_id}: {self.decision} needs a reason')
        if self.decision == 'approve' and self.reason:
            raise ValueError(f'{self.case_id}: approve carries no reason')
        if self.mti_choice:
            if self.mti_choice not in MTI_CHOICES or MTI_CHOICES[self.mti_choice] != self.decision:
                raise ValueError(f'{self.case_id}: mti_choice {self.mti_choice!r} does not match decision {self.decision!r}')
            if self.mti_choice == 'relabel_abstain' and self.proposed_behavior != 'abstain':
                raise ValueError(f'{self.case_id}: relabel_abstain must propose abstain')
        return self


class V2Export(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    schema_version: int
    kind: str
    pack_id: str
    gold_sha256: str
    reviewer_name: str = Field(max_length=200)
    exported_at: str
    results: list[V2Result]
    ai_files_sha256: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode='after')
    def valid(self):
        if self.schema_version != 1 or self.kind != 'heldout_v2_review':
            raise ValueError('Not a held-out v2 review export')
        if not self.reviewer_name.strip():
            raise ValueError('Reviewer name is required')
        parse_timestamp(self.exported_at)
        ids = [r.case_id for r in self.results]
        if len(ids) != len(set(ids)):
            raise ValueError('Duplicate case ids in the export')
        return self


def _matches(r: V2Result, entry: dict) -> bool:
    """Does the owner's decision equal what the AI consensus suggested?"""
    if entry['action'] == 'approve':
        return r.decision == 'approve'
    if entry['action'] == 'change':
        return r.decision == 'change' and r.proposed_behavior == entry['behaviour']
    return entry['action'] == 'reject' and r.decision == 'reject'


def load_export(path: Path, cases: list[dict], draft_sha: str, ai: dict | None = None) -> tuple[V2Export, str]:
    raw = Path(path).read_bytes()
    export = V2Export.model_validate_json(raw)
    if export.gold_sha256 != draft_sha or export.pack_id != pack_id_for(draft_sha):
        raise ValueError('The export was made for a different version of the draft gold file. Rebuild the review page and review again.')
    expected = {c['case_id'] for c in cases}
    got = {r.case_id for r in export.results}
    if got != expected:
        raise ValueError(f'The export must decide every case: missing {sorted(expected - got)[:5]}, unexpected {sorted(got - expected)[:5]}')
    by_id = {c['case_id']: c for c in cases}
    for r in export.results:
        if r.mti_choice and by_id[r.case_id].get('source_group') != MTI_GROUP:
            raise ValueError(f'{r.case_id}: mti_choice on a case that is not an AI-article case')
        if r.decision == 'change' and r.proposed_behavior == by_id[r.case_id]['expected_behavior']:
            raise ValueError(f'{r.case_id}: change to the behaviour it already has')
    agreed = [r for r in export.results if r.decision_source == AI_SOURCE]
    if agreed and ai is None:
        raise ValueError('The export records agreement with the AI reviewers, but the AI review files are not available here')
    if ai is not None and (agreed or export.ai_files_sha256) and export.ai_files_sha256 != ai['sha256']:
        raise ValueError('The AI review files differ from the ones the page was built with (SHA-256 mismatch). Rebuild the page and review again.')
    for r in agreed:
        entry = ai_entry(ai, r.case_id)
        if entry['class'] == 'split':
            raise ValueError(f'{r.case_id}: the AI reviewers were split, so agreeing with them is not allowed')
        if entry['low_confidence']:
            raise ValueError(f'{r.case_id}: the reviewers who agree are low-confidence, so agreeing with them is not allowed')
        if r.ai_basis != entry['basis']:
            raise ValueError(f'{r.case_id}: ai_basis does not match the AI review files')
        if not _matches(r, entry):
            raise ValueError(f'{r.case_id}: the decision does not match the AI consensus ({entry["label"]})')
    return export, hashlib.sha256(raw).hexdigest()


def _relabel(case: dict, behaviour: str, reason: str) -> dict:
    new = json.loads(json.dumps(case))
    old = new['expected_behavior']
    answering = ('answer', 'ignore_injection_and_answer')
    new['expected_behavior'] = behaviour
    if behaviour in answering and old not in answering:
        text, data = new.get('context_only_evidence_text', []), new.get('context_only_evidence_data', [])
        if not (text or data) or not new.get('reference_facts'):
            raise ValueError(f'{case["case_id"]}: cannot relabel to {behaviour}: the draft has no evidence or expected facts for an answer')
        new['evidence_text'], new['evidence_data'] = text, data
        new['context_only_evidence_text'], new['context_only_evidence_data'] = [], []
        new['abstain_reason'] = None
    elif behaviour not in answering and old in answering:
        # Scorers must not treat the old answer evidence as gold for a non-answer label: keep it as background only.
        new['context_only_evidence_text'] = new.get('context_only_evidence_text', []) + new.get('evidence_text', [])
        new['context_only_evidence_data'] = new.get('context_only_evidence_data', []) + new.get('evidence_data', [])
        new['evidence_text'], new['evidence_data'] = [], []
        new['reference_facts'] = []
        new['calculation'] = None
        new['abstain_reason'] = reason
    else:
        new['abstain_reason'] = reason if behaviour not in answering else None
    return new


def apply_review(cases: list[dict], export: V2Export, export_sha: str, ai: dict | None = None) -> tuple[list[dict], dict]:
    by_id = {r.case_id: r for r in export.results}
    out, relabelled, dropped = [], [], []
    for c in cases:
        r = by_id[c['case_id']]
        if r.decision == 'reject':
            dropped.append(c['case_id'])
            continue
        new = _relabel(c, r.proposed_behavior, r.reason) if r.decision == 'change' else json.loads(json.dumps(c))
        if r.decision == 'change':
            relabelled.append((c['case_id'], c['expected_behavior'], r.proposed_behavior))
        new['owner_review'] = {'decision': r.decision, 'reviewer_name': export.reviewer_name, 'reviewed_at': r.timestamp,
                               'original_behavior': c['expected_behavior'], 'reason': r.reason, 'comment': r.comment,
                               'export_sha256': export_sha, 'decision_source': r.decision_source, 'ai_basis': r.ai_basis or None,
                               'decision_provenance': AI_NOT_INDEPENDENT if r.decision_source == AI_SOURCE else 'owner decision by own click'}
        out.append(new)
    problems = thresholds(out)
    report = {'kept': len(out), 'relabelled': relabelled, 'dropped': dropped, 'problems': problems,
              'by_family': dict(Counter(c['family'] for c in out)), 'by_behavior': dict(Counter(c['expected_behavior'] for c in out)),
              'non_answer': sum(c['expected_behavior'] != 'answer' for c in out), 'evidence_components': evidence_component_count(out),
              'approved_unchanged': sum(1 for r in export.results if r.decision == 'approve')}
    report['sources'] = {'owner_manual': sum(r.decision_source == 'owner_manual' for r in export.results), AI_SOURCE: sum(r.decision_source == AI_SOURCE for r in export.results)}
    agree = comparable = 0
    if ai:
        for r in export.results:
            entry = ai_entry(ai, r.case_id)
            if r.decision_source == 'owner_manual' and entry['class'] != 'split':
                comparable += 1
                agree += _matches(r, entry)
    report['own_vs_ai'] = (agree, comparable)
    return out, report


def thresholds(cases: list[dict]) -> list[str]:
    problems = []
    if len(cases) < MIN_CASES:
        problems.append(f'only {len(cases)} cases remain; the acceptance rule needs at least {MIN_CASES}')
    non_answer = sum(c['expected_behavior'] != 'answer' for c in cases)
    if non_answer < MIN_NON_ANSWER:
        problems.append(f'only {non_answer} non-answer cases remain; at least {MIN_NON_ANSWER} are needed')
    components = evidence_component_count(cases)
    if components < MIN_COMPONENTS:
        problems.append(f'only {components} independent evidence groups remain; the acceptance rule needs at least {MIN_COMPONENTS}')
    return problems


# ---------------------------------------------------------------- hashes, cost, commands, signed block

def passage_fingerprint(root: Path) -> tuple[str, int]:
    lines = []
    for path in sorted((root / 'data/passages').glob('*.jsonl')):
        for p in rows(path):
            lines.append(f"{p['passage_id']}:{p['text_sha256']}")
    lines.sort()
    return hashlib.sha256('\n'.join(lines).encode()).hexdigest(), len(lines)


def frozen_hashes(root: Path) -> dict[str, str]:
    files = {'planner_v1': 'prompts/planner_v1.md', 'planner_v1_user': 'prompts/planner_v1_user.md', 'answer_v3': 'prompts/answer_v3.md',
             'answer_v3_user': 'prompts/answer_v3_user.md', 'rerank_v1': 'prompts/rerank_v1.md', 'judge_v1': 'prompts/judge_v1.md',
             'specs/prices.yaml': 'specs/prices.yaml', 'observations.parquet': 'data/processed/observations.parquet',
             'manifest.json': 'data/manifests/manifest.json'}
    out = {name: sha256_file(root / rel) for name, rel in files.items() if (root / rel).exists()}
    out['passage_fingerprint'] = passage_fingerprint(root)[0]
    return out


def hash_mismatches(root: Path, freeze_text: str) -> list[str]:
    """Content fingerprints recorded before signing must still appear in FREEZE.md; otherwise a dated amendment is needed first.

    The manifest file also carries rights metadata that may change without touching any passage or observation, so a manifest
    difference is reported as a note (see hash_notes) and recorded in the signed block rather than blocking the signature."""
    recorded = set(re.findall(r'\b[0-9a-f]{64}\b', freeze_text))
    return [f'{name} ({digest[:12]}…) differs from the hashes recorded in FREEZE.md' for name, digest in frozen_hashes(root).items()
            if digest not in recorded and name != 'manifest.json']


def hash_notes(root: Path, freeze_text: str) -> list[str]:
    digest = frozen_hashes(root).get('manifest.json')
    if digest and digest not in set(re.findall(r'\b[0-9a-f]{64}\b', freeze_text)):
        return [f'manifest.json ({digest[:12]}…) differs from the hash in the FREEZE.md draft. Passages and observations are unchanged, so this does not block signing; '
                'the signed block records the current hash. Check `git diff` of data/manifests/manifest.json if you want to know why (for example rights metadata).']
    return []


def git_state(root: Path) -> tuple[str, bool]:
    def run(*args: str) -> str:
        return subprocess.run(['git', *args], cwd=root, capture_output=True, text=True, check=False).stdout.strip()
    head = run('rev-parse', 'HEAD') or 'unknown (no commit)'
    return head, bool(run('status', '--porcelain', '--untracked-files=no'))


def cost_quote(root: Path, n_cases: int) -> dict | None:
    """Mean saved per-case generation and judge cost of the registered original held-out runs, for both models and arms."""
    gen = judge = 0.0
    found = 0
    for exp in ('H-r3', 'H-hybrid'):
        for model in PRIMARY_MODELS:
            run = root / f'data/runs/agent-heldout-{exp}/{model}.jsonl'
            judgements = root / f'experiments/eval/agent-heldout-{exp}/{model}.judgements.json'
            if not run.exists():
                continue
            records = rows(run)
            if records:
                gen += sum(r['usage']['cost_usd'] for r in records) / len(records)
                found += 1
            if judgements.exists():
                data = json.loads(judgements.read_text())
                costs = [v['judgement']['cost_usd'] for v in data.values() if isinstance(v, dict) and isinstance(v.get('judgement'), dict) and 'cost_usd' in v['judgement']]
                judge += sum(costs) / len(costs) if costs else 0.0
    if found < 4:
        return None
    return {'per_case_generation': gen, 'per_case_judge': judge, 'cases': n_cases, 'total': n_cases * (gen + judge)}


def run_commands(gold_rel: str) -> list[str]:
    models = ' '.join(PRIMARY_MODELS)
    return [
        f'uv run labourlens agent-exp --split heldout --gold {gold_rel} --tag V2-r3 --retrieval r3 --pairs {models}',
        f'uv run labourlens agent-exp --split heldout --gold {gold_rel} --tag V2-hybrid --retrieval hybrid --pairs {models}',
        f'uv run labourlens eval --exp agent-heldout-V2-r3 --split heldout --gold {gold_rel}',
        f'uv run labourlens eval --exp agent-heldout-V2-hybrid --split heldout --gold {gold_rel}',
        f'uv run labourlens paired --gold {gold_rel} --candidate agent-heldout-V2-r3 --baseline agent-heldout-V2-hybrid --models {models} --out experiments/heldout-v2/paired.json',
    ]


def signed_block(root: Path, export: V2Export, export_sha: str, draft_sha: str, new_sha: str, report: dict, out_rel: str, notes: list[str] | None = None, ai: dict | None = None) -> str:
    head, dirty = git_state(root)
    hashes = frozen_hashes(root)
    count = passage_fingerprint(root)[1]
    quote = cost_quote(root, report['kept'])
    lines = [
        '', SIGNED_MARK + ' (held-out v2, gold v1)', '',
        f'**SIGNED by the owner ({export.reviewer_name}) on {export.exported_at}: approved by owner via export `{export_sha}`.** This block supersedes the draft hash listed above; the draft file is unchanged.', '',
        f'- **Frozen gold:** `{out_rel}`, {report["kept"]} cases, SHA-256 `{new_sha}`.',
        f'- **Derived from draft:** `{DRAFT}` SHA-256 `{draft_sha}`.',
        f'- **Owner changes:** approved unchanged {report["approved_unchanged"]}; relabelled {len(report["relabelled"])} ({", ".join(f"{i} {a}->{b}" for i, a, b in report["relabelled"]) or "none"}); dropped {len(report["dropped"])} ({", ".join(report["dropped"]) or "none"}).',
        f'- **Who decided what:** {report["sources"]["owner_manual"]} cards by the owner’s own click, {report["sources"][AI_SOURCE]} cards by the owner agreeing with an AI suggestion ({AI_NOT_INDEPENDENT}). The three AI reviewers are one model family, so their agreement is not independent human review.',
        f'- **Owner’s own decisions that matched the AI consensus:** {report["own_vs_ai"][0]} of {report["own_vs_ai"][1]} (cards agreed with the AI are excluded).',
        *(['- **AI review files (SHA-256):** ' + ', '.join(f'{k} `{v}`' for k, v in ai['sha256'].items()) + '.'] if ai else []),
        f'- **Distribution:** families {json.dumps(report["by_family"], sort_keys=True)}; behaviours {json.dumps(report["by_behavior"], sort_keys=True)}; independent evidence groups {report["evidence_components"]}; non-answer cases {report["non_answer"]}.',
        f'- **Code:** git HEAD `{head}`; uncommitted changes to tracked files at signing: {"yes" if dirty else "no"}.',
        f'- **Corpus:** passage fingerprint `{hashes["passage_fingerprint"]}` ({count} passages); observations `{hashes.get("observations.parquet", "missing")}`; manifest `{hashes.get("manifest.json", "missing")}`.',
        '- **Prompts and prices:** ' + '; '.join(f'`{k}` `{v}`' for k, v in hashes.items() if k not in ('passage_fingerprint', 'observations.parquet', 'manifest.json')) + '.',
        f'- **Environment recorded at signing:** `LABOURLENS_CROSSCHECK={os.environ.get("LABOURLENS_CROSSCHECK", "(unset: guard on)")}`, `LABOURLENS_GUARDS={os.environ.get("LABOURLENS_GUARDS", "(unset)")}`. Run both arms with the same setting.',
        f'- **Cost quote (inference from saved usage, not a cap):** {"about $%.2f" % quote["total"] if quote else "no saved usage found"}.',
        '- **Commands, in order (paid APIs):**', '```', *run_commands(out_rel), '```', *([''] + [f'- **Note at signing:** {n}' for n in notes] if notes else []), '',
    ]
    return '\n'.join(lines)


def _plain_summary(root: Path, export: V2Export, export_sha: str, report: dict, mismatches: list[str], out_rel: str, write: bool, notes: list[str] | None = None) -> str:
    quote = cost_quote(root, report['kept'])
    lines = ['HELD-OUT V2 APPROVAL ' + ('(WRITTEN)' if write else '(DRY RUN: nothing written)'), '',
             f'Reviewer: {export.reviewer_name}   Export: {export_sha[:16]}…', '',
             f'You approved {report["approved_unchanged"]} cases unchanged, changed the label of {len(report["relabelled"])}, rejected {len(report["dropped"])}.',
             f'Who decided: {report["sources"]["owner_manual"]} by your own click, {report["sources"][AI_SOURCE]} by agreeing with an AI suggestion ({AI_NOT_INDEPENDENT}).',
             f'Your own decisions that matched the AI consensus: {report["own_vs_ai"][0]} of {report["own_vs_ai"][1]} (cards you agreed with the AI on are excluded).']
    for case_id, old, new in report['relabelled']:
        lines.append(f'  - {case_id}: {old} -> {new}')
    for case_id in report['dropped']:
        lines.append(f'  - {case_id}: dropped')
    lines += ['', f'The frozen test would have {report["kept"]} cases, {report["non_answer"]} of them non-answer, with {report["evidence_components"]} independent evidence groups.',
              'By family: ' + ', '.join(f'{k} {v}' for k, v in sorted(report['by_family'].items())),
              'By behaviour: ' + ', '.join(f'{k} {v}' for k, v in sorted(report['by_behavior'].items())), '']
    if report['problems'] or mismatches:
        lines.append('CANNOT SIGN YET:')
        lines += [f'  - {p}' for p in report['problems'] + mismatches]
        lines.append('')
    if notes:
        lines += ['NOTE (does not block signing):'] + [f'  - {n}' for n in notes] + ['']
    lines.append('What you are agreeing to: these questions and answers become the frozen test; you cannot change them after the run starts.')
    lines.append('Cost quote for the run: ' + (f'about ${quote["total"]:.2f} (generation ${quote["cases"] * quote["per_case_generation"]:.2f} + judging ${quote["cases"] * quote["per_case_judge"]:.2f}; a quote from saved usage, not a cap).' if quote else 'no saved usage to quote from.'))
    if write:
        lines += ['', 'Next, to run the test (this spends money; it needs OPENAI_API_KEY):', f'  uv run labourlens v2-run --gold {out_rel} --yes', '(without --yes it only prints the five commands)']
    else:
        lines += ['', 'To sign and write the frozen file, run the same command again with --write.']
    return '\n'.join(lines)


def v2_approve(review_export: Path, write: bool = False, root: Path = ROOT) -> tuple[int, str]:
    root = Path(root).resolve()
    draft = root / DRAFT
    cases = rows(draft)
    draft_sha = sha256_file(draft)
    try:
        ai = load_ai(root, cases)
        export, export_sha = load_export(review_export, cases, draft_sha, ai)
    except ValueError as exc:
        return 2, f'Review export rejected: {exc}'
    try:
        new_cases, report = apply_review(cases, export, export_sha, ai)
    except ValueError as exc:
        return 2, f'Review export rejected: {exc}'
    freeze_path = root / FREEZE
    freeze_text = freeze_path.read_text() if freeze_path.exists() else ''
    mismatches = hash_mismatches(root, freeze_text)
    notes = hash_notes(root, freeze_text)
    out_path = root / APPROVED
    body = ''.join(json.dumps(c, ensure_ascii=False) + '\n' for c in new_cases)
    new_sha = hashlib.sha256(body.encode()).hexdigest()
    summary = _plain_summary(root, export, export_sha, report, mismatches, APPROVED, write, notes)
    if report['problems'] or mismatches:
        return 1, summary
    if not write:
        return 0, summary
    if SIGNED_MARK in freeze_text:
        return 2, summary + '\n\nFREEZE.md already holds a signed block. Amend it by hand with a dated note instead of signing twice.'
    if out_path.exists() and out_path.read_text() != body:
        return 2, summary + f'\n\n{APPROVED} already exists with different content; it is never overwritten.'
    out_path.write_text(body)
    with freeze_path.open('a') as handle:
        handle.write(signed_block(root, export, export_sha, draft_sha, new_sha, report, APPROVED, notes, ai))
    return 0, summary + f'\n\nWrote {APPROVED} (SHA-256 {new_sha}) and appended the signed block to {FREEZE}.'


def v2_run(gold: Path, yes: bool = False, root: Path = ROOT) -> tuple[int, str]:
    """Thin wrapper: prints the registered commands; runs them (paid) only with --yes and only for the signed gold file."""
    root = Path(root).resolve()
    gold_path = Path(gold)
    gold_path = gold_path if gold_path.is_absolute() else root / gold_path
    if not gold_path.exists():
        return 2, f'Gold file not found: {gold}'
    sha = sha256_file(gold_path)
    freeze = (root / FREEZE).read_text() if (root / FREEZE).exists() else ''
    if SIGNED_MARK not in freeze or sha not in freeze.split(SIGNED_MARK, 1)[1]:
        return 2, f'Refusing: {gold} (SHA-256 {sha[:16]}…) is not the gold file signed in {FREEZE}. Run v2-approve --write first.'
    rel = os.path.relpath(gold_path, root)
    commands = run_commands(rel)
    text = ['Registered commands (paid APIs), in this order:', *[f'  {c}' for c in commands]]
    if not yes:
        return 0, '\n'.join(text + ['', 'Nothing was run. Add --yes to run them one after another (this spends money; it needs OPENAI_API_KEY).'])
    if not os.environ.get('OPENAI_API_KEY'):
        return 2, '\n'.join(text + ['', 'Refusing to run: OPENAI_API_KEY is not set.'])
    for command in commands:
        done = subprocess.run(command.split(), cwd=root, check=False)
        if done.returncode:
            return done.returncode, '\n'.join(text + ['', f'Stopped: this command failed ({done.returncode}): {command}'])
    return 0, '\n'.join(text + ['', 'All commands finished.'])


# ---------------------------------------------------------------- commit-safe summary of the AI reviews

AI_SUMMARY = 'docs/human-review/heldout-v2-ai-review-summary.md'


def fleiss_kappa(items: list[list[str]]) -> float | None:
    """Fleiss' kappa for a fixed number of raters per item; None when chance agreement is 1 (no variation at all)."""
    n, total = len(items[0]), len(items)
    cats = sorted({x for item in items for x in item})
    counts = [[item.count(c) for c in cats] for item in items]
    p_item = [(sum(x * x for x in row) - n) / (n * (n - 1)) for row in counts]
    p_bar = sum(p_item) / total
    p_e = sum((sum(row[j] for row in counts) / (total * n)) ** 2 for j in range(len(cats)))
    return None if p_e == 1 else (p_bar - p_e) / (1 - p_e)


def ai_statistics(ai: dict, cases: list[dict]) -> dict:
    ids = [c['case_id'] for c in cases]
    verdicts = {r: [ai['reviews'][r][cid]['verdict'] for cid in ids] for r in AI_REVIEWERS}
    votes = {r: [vote_key(ai['reviews'][r][cid]) for cid in ids] for r in AI_REVIEWERS}
    pairs = [(a, b) for i, a in enumerate(AI_REVIEWERS) for b in AI_REVIEWERS[i + 1:]]
    entries = {cid: ai_entry(ai, cid) for cid in ids}
    return {
        'n': len(ids),
        'verdict_counts': {r: dict(Counter(v)) for r, v in verdicts.items()},
        'pairwise_verdict': {f'{a}-{b}': sum(x == y for x, y in zip(verdicts[a], verdicts[b])) / len(ids) for a, b in pairs},
        'pairwise_vote': {f'{a}-{b}': sum(x == y for x, y in zip(votes[a], votes[b])) / len(ids) for a, b in pairs},
        'all_three_verdict': sum(len({verdicts[r][i] for r in AI_REVIEWERS}) == 1 for i in range(len(ids))),
        'kappa_verdict': fleiss_kappa([[verdicts[r][i] for r in AI_REVIEWERS] for i in range(len(ids))]),
        'kappa_vote': fleiss_kappa([[votes[r][i] for r in AI_REVIEWERS] for i in range(len(ids))]),
        'consensus': dict(Counter(e['kind'] for e in entries.values())),
        'entries': entries,
    }


def _plain(text: str) -> str:
    return re.sub(r'<[^>]+>', '', re.sub(r'<b>(.*?)</b>', r'**\1**', text))


def _first_sentence(text: str, limit: int = 28) -> str:
    first = re.split(r'(?<=\.)\s', text.strip(), maxsplit=1)[0]
    words = first.split()
    return ' '.join(words[:limit]) + (' …' if len(words) > limit else '')


def ai_summary_markdown(root: Path = ROOT) -> str:
    root = Path(root).resolve()
    cases = rows(root / DRAFT)
    ai = load_ai(root, cases)
    if ai is None:
        raise ValueError(f'No AI review files in {AI_DIR}')
    stats = ai_statistics(ai, cases)
    n = stats['n']
    family = {c['case_id']: c['family'] for c in cases}
    fmt = lambda x: 'undefined' if x is None else f'{x:.3f}'
    lines = [
        '# Held-out v2: independent AI review summary', '',
        '**Status:** AI review of the draft gold file, performed before any owner decision. **This is not human review.** '
        'The raw reviewer files stay private (they sit under `private/`, which is gitignored) and are embedded in the private owner review page.', '',
        '## Provenance', '',
        f'- Draft gold file: `{DRAFT}`, SHA-256 `{sha256_file(root / DRAFT)}`, {n} cases.',
        '- Three separate blind AI review passes (A, B, C), one verdict per case: approve, change label (with the suggested behaviour) or reject, each with a confidence. They were not shown each other’s output.',
        '- SHA-256 of the private files: ' + ', '.join(f'{k}.jsonl `{v}`' for k, v in ai['sha256'].items()) + '.',
        '- The three reviewers are the same model family. Their errors are therefore correlated, and their agreement is weaker evidence than agreement between independent people. '
        'It does not substitute for the owner’s review and is never counted as independent inter-rater evidence.', '',
        '## Verdicts per reviewer', '', '| Reviewer | approve | change label | reject |', '|---|---:|---:|---:|',
        *[f'| {r} | {c.get("approve", 0)} | {c.get("change_label", 0)} | {c.get("reject", 0)} |' for r, c in stats['verdict_counts'].items()], '',
        '## AI consensus', '',
        'Consensus is a verdict given by at least 2 of the 3 reviewers (and, for a change, the same suggested behaviour); otherwise the case is split.', '',
        '| Consensus | Cases |', '|---|---:|', *[f'| {k} | {v} |' for k, v in sorted(stats['consensus'].items(), key=lambda kv: (-kv[1], kv[0]))], '',
        '## Agreement between the reviewers', '',
        f'- All three gave the same verdict on {stats["all_three_verdict"]} of {n} cases.',
        '- Pairwise agreement on the verdict: ' + ', '.join(f'{k} {v:.1%}' for k, v in stats['pairwise_verdict'].items()) + '.',
        '- Pairwise agreement on verdict plus suggested behaviour: ' + ', '.join(f'{k} {v:.1%}' for k, v in stats['pairwise_vote'].items()) + '.',
        f'- Fleiss’ kappa on the verdict: {fmt(stats["kappa_verdict"])}; on verdict plus suggested behaviour: {fmt(stats["kappa_vote"])}.',
        '- Kappa is unstable when almost every case gets the same verdict, as here (most cases are approvals), so read the raw agreement counts first.', '',
        '## Cases that are not unanimous approvals', '',
        '| Case | Family | A | B | C | Consensus | Reviewers’ main reason (first sentence, abbreviated) |', '|---|---|---|---|---|---|---|',
    ]
    for cid, entry in stats['entries'].items():
        if entry['kind'] == 'unanimous approve':
            continue
        cells = []
        reasons = []
        for r in AI_REVIEWERS:
            rec = ai['reviews'][r][cid]
            cells.append(f'{_vote_text(entry["votes"][r])} ({rec["confidence"]})')
            reasons.append(f'{r}: {_first_sentence(rec["reason"])}')
        lines.append(f'| {cid} | {FAMILY_PLAIN.get(family[cid], family[cid])} | ' + ' | '.join(cells) + f' | {entry["label"]}' + (' (low confidence, no one-click)' if entry['low_confidence'] else '') + ' | ' + ' '.join(reasons).replace('|', '/') + ' |')
    lines += ['', '## Systematic issues the reviewers raised', '', *[f'- {_plain(s)}' for s in _systematic(ai, cases, evidence_component_count(cases))], '',
              '## How the owner review page uses this', '',
              '- Each card shows the three verdicts, the computed consensus and the reviewers’ issues beside the evidence.',
              '- “Agree with AI” exists only where a consensus exists, unlocks a few seconds after a card appears, and is recorded as `agreed_with_ai_suggestion`. '
              f'`v2-approve` verifies the recorded basis against the file hashes above and reports those cards separately: {AI_NOT_INDEPENDENT}.',
              '- The owner’s own decisions are still `owner_manual`; the share of them that matched the AI consensus is reported with agree-with-AI cards excluded.', '']
    return '\n'.join(lines)


def write_ai_summary(root: Path = ROOT) -> Path:
    """Write the commit-safe summary; refuses if it would repeat more than six consecutive words of any local passage."""
    from labourlens.data import rights_scan

    root = Path(root).resolve()
    text = ai_summary_markdown(root)
    passages = root / 'data' / 'passages'
    if passages.exists():
        hits = rights_scan.scan_text(text, rights_scan.build_shingles(passages))
        if hits:
            raise ValueError(f'The summary would quote source passages (lines {[h[0] for h in hits][:5]}); shorten the reviewer reasons')
    out = root / AI_SUMMARY
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    return out
