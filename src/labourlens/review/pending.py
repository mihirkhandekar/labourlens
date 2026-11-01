"""Everything the owner has not yet decided by their own click: inventory, pending-review plan, strict ingest, gold v3.7.

Nothing here calls a model or the network. The owner's own per-card clicks (`owner_manual`) are the only manual evidence. A card
where the owner pressed "Agree with AI" stays `agreed_with_ai_suggestion` everywhere, in the page, the export, the files and
the summary, and is never counted as independent evidence.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import re
from collections import Counter
from datetime import date
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from labourlens.review import heldout_v2 as hv2
from labourlens.review import pack
from labourlens.review.pack import BEHAVIOURS, ROOT, parse_timestamp, rows

PAGE = 'private/human-review/pending-review/index.html'
GOLD_DRAFT = 'experiments/gold/draft_cases.jsonl'
GOLD_V37 = 'experiments/gold/gold_v3.7.jsonl'
GOLD_V37_LOG = 'experiments/gold/gold_v3.7-review-log.jsonl'
FINAL_PROVENANCE = 'experiments/gold/gold_v3.7-final-provenance.json'
CHANGELOG = 'experiments/gold/CHANGELOG.md'
PROPOSALS = 'experiments/gold/proposed_label_changes.jsonl'
INVENTORY = 'docs/human-review/review-inventory.md'
FINAL_SUMMARY = 'docs/human-review/owner-review-final-summary.md'
V2_EXPORT = 'experiments/heldout-v2/owner-review-export.json'
MAIN_EXPORT_PRIVATE = 'private/human-review/owner-exports/review-results.json'
MAIN_EXPORT_DOWNLOADS = Path.home() / 'Downloads' / 'review-results (8).json'
AGREED = hv2.AI_SOURCE
MANUAL = 'owner_manual'
SOURCES = (MANUAL, AGREED)
STREAM_LABEL = {'gold': 'Gold cases', 'answers': 'Saved model answers', 'sources': 'Source checks', 'v2': 'Held-out v2 cases', 'j10': 'J10 extraction gaps'}
QUEUE_LABEL = {'pending': 'never decided by you', 'proposal': 'your earlier label-change proposal', 'redo': 'redo manually (you agreed with AI before)'}
GOLD_DECISIONS = ('approve', 'change', 'reject')
ANSWER_DECISIONS = ('correct', 'partly correct', 'incorrect')
SOURCE_DECISIONS = ('matches', 'minor', 'major')
J10_ITEM_DECISIONS = ('accept', 'not_accept')
J10_FINAL_DECISIONS = ('accept_limits', 'require_fixes', 'inspect_more')
DECISIONS = {'gold': GOLD_DECISIONS, 'v2': GOLD_DECISIONS, 'answers': ANSWER_DECISIONS, 'sources': SOURCE_DECISIONS, 'j10': J10_ITEM_DECISIONS + J10_FINAL_DECISIONS}
REASON_REQUIRED = {'change', 'reject', 'not_accept', 'require_fixes'}
J10_ITEMS = [
    ('J10-1', 'mom-2025-q3-final', 30, None, 'A whole narrative page has no extracted text',
     'In the frozen extraction used by the saved runs, this report page produced no passages at all, so nothing on it could ever be retrieved or cited.'),
    ('J10-2', 'mom-2026-q2-final', 59, 'mom-2026-q2-final:p059:b002:a5dc11e0', 'Unreadable control characters were marked fine',
     'The frozen extraction kept text with hidden control characters and still marked it “ok”, so a reader could not trust the quality flag.'),
    ('J10-3', 'mom-2026-q2-final', 48, 'mom-2026-q2-final:p048:b049:a897f425', 'A page footer was glued onto a note',
     'The frozen extraction appended the page footer to the end of a note and left the printed-page label empty.'),
    ('J10-4', 'mom-2026-q2-final', 22, 'mom-2026-q2-final:p022:b020:7059aed2', 'A note was cut in the middle',
     'The frozen extraction starts and ends this note mid-way, so the definition it gives is incomplete on its own.'),
    ('J10-5', 'mom-2025-q3-final', 51, 'mom-2025-q3-final:p051:b021:661903e0', 'A table row lost its column headings',
     'The frozen extraction kept the numbers of a table row but not the headings and units, so the row cannot be read on its own.'),
]
J10_FINAL = ('J10', 'Your overall J10 decision', 'After looking at the five examples, do you accept the disclosed frozen extraction gaps (they stay unfixed in the saved runs and are disclosed), or not?')
J10_FINAL_OPTIONS = {'accept_limits': 'Accept the gaps, with the limits disclosed', 'require_fixes': 'Do not accept until specific gaps are fixed (say which)', 'inspect_more': 'I still need more inspection'}
FAMILY_ORDER = ('factual_lookup', 'numerical_comparison', 'cross_source_synthesis', 'revision_conflict', 'ambiguity_insufficient_causal', 'adversarial')
AI_FILE_GLOBS = ('experiments/gold/ai-review*/*.jsonl', 'experiments/gold/independent-ai-review*.md', 'experiments/human-review-sample/*.md',
                 'docs/human-review/ai-adjudication.md', 'docs/human-review/ai-verification-of-pre-reviews.md',
                 'private/human-review/tiebreak/*.jsonl', 'private/human-review/heldout-v2-ai/*.jsonl', 'private/human-review/pending-ai/Pend*.jsonl')
AI_DEV_NOTE = 'These AI reviews looked at an earlier draft of the case; some concerns were fixed afterwards (see the gold changelog). Check whether a concern still applies.'


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


# ---------------------------------------------------------------- the owner's earlier decisions

def find_main_export(root: Path, explicit: Path | None = None) -> Path:
    candidates = [Path(explicit)] if explicit else [Path(root) / MAIN_EXPORT_PRIVATE, MAIN_EXPORT_DOWNLOADS]
    for path in candidates:
        if path.exists():
            return path
    raise ValueError(f'The owner export of the main review pack is not found. Pass --main-export, or copy it to {MAIN_EXPORT_PRIVATE}.')


class State:
    """Everything read from files once: gold, the main export, the saved runs, the v2 gold and its owner provenance."""

    def __init__(self, root: Path, main_export: Path | None = None, use_overlay: bool = False):
        self.root = Path(root).resolve()
        root = self.root
        self.gold = rows(root / GOLD_DRAFT)
        self.gold_by_id = {c['case_id']: c for c in self.gold}
        self.main_path = find_main_export(root, main_export)
        self.main_sha = sha256_file(self.main_path)
        export = pack.ReviewExport.model_validate_json(self.main_path.read_text())
        self.reviewer = export.reviewer_name
        self.exported_at = export.exported_at
        self.main: dict[tuple[str, str], dict] = {}
        for r in export.results:
            decided = any(getattr(r.fields, f) for f in pack.DECISION_FIELDS) or bool(r.fields.decision)
            source = None if r.endorsement or not decided else (r.decision_source or MANUAL)
            self.main[(r.tab, r.case_id)] = {'source': source, 'fields': r.fields, 'ai_basis': r.ai_basis}
        selection = root / 'experiments/human-review-sample/selection.json'
        self.sample = json.loads(selection.read_text())['ids'] if selection.exists() else []
        run = root / 'data/runs/agent-dev-A1/gpt-6-luna.jsonl'
        self.runs = {r['case_id']: r for r in rows(run)} if run.exists() else {}
        v2_draft = root / hv2.DRAFT
        self.v2_cases = rows(v2_draft) if v2_draft.exists() else []
        self.v2_by_id = {c['case_id']: c for c in self.v2_cases}
        v2_final = root / hv2.APPROVED
        self.v2_final = {c['case_id']: c for c in rows(v2_final)} if v2_final.exists() else {}
        self.v2_provenance = {cid: c.get('owner_review') for cid, c in self.v2_final.items()}
        proposals = root / PROPOSALS
        self.proposals = {p['case_id']: p for p in rows(proposals) if p.get('status') == 'proposed_not_applied'} if proposals.exists() else {}
        spot = {'passage': root / 'docs/human-review/passage-spot-check.md', 'statistical': root / 'docs/human-review/statistical-spot-check.md'}
        self.source_ids = {}
        for kind, column, path in (('passage', 4, spot['passage']), ('statistical', 7, spot['statistical'])):
            if path.exists():
                for n, identifier in enumerate(pack.source_rows(path, column), 1):
                    self.source_ids[f'{kind}-{n:02}'] = identifier

        # After a pending-ingest --write the final provenance is stored; only the inventory reads it, so planning and ingest keep seeing the state the pack was built from.
        self.overlay = None
        overlay = root / FINAL_PROVENANCE
        if use_overlay and overlay.exists():
            self.overlay = json.loads(overlay.read_text())
            for cid, source in self.overlay['streams']['v2'].items():
                if cid in self.v2_provenance:
                    self.v2_provenance[cid] = {**(self.v2_provenance[cid] or {}), 'decision_source': source}

    def gold_source(self, cid: str) -> str | None:
        if self.overlay is not None:
            return self.overlay['streams']['gold'].get(cid)
        provenance = self.gold_by_id[cid].get('owner_review')
        return provenance['decision_source'] if provenance else None

    def main_source(self, tab: str, cid: str) -> str | None:
        if self.overlay is not None and tab in ('answers', 'sources'):
            return self.overlay['streams'][tab].get(cid)
        item = self.main.get((tab, cid))
        return item['source'] if item else None

    def j10_decision(self) -> str | None:
        if self.overlay is not None and self.overlay.get('j10'):
            return self.overlay['j10'].get('J10')
        item = self.main.get(('decisions', 'J10'))
        return item['fields'].decision if item else None


# ---------------------------------------------------------------- AI suggestions, one normalised shape

def ai_file_hashes(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for pattern in AI_FILE_GLOBS:
        for name in sorted(glob.glob(str(Path(root) / pattern))):
            out[os.path.relpath(name, root)] = sha256_file(Path(name))
    return out


def make_info(status: str, text: str, decision: str | None = None, proposed_behavior: str = '', basis: str = 'earlier_passes',
              opinions: list[dict] | None = None, risk: int = 3) -> dict:
    """status none: no AI review exists; disagree: AI reviews disagree or raise a concern (no one-click); agree: one-click allowed."""
    opinions = opinions or []
    info = {'status': status, 'text': text, 'decision': decision if status == 'agree' else None, 'proposed_behavior': proposed_behavior if status == 'agree' else '',
            'basis': basis, 'opinions': opinions, 'risk': risk}
    info['ai_basis'] = ({'basis': basis, 'decision': decision, 'proposed_behavior': proposed_behavior,
                         'opinions': [[o['reviewer'], o['verdict']] for o in opinions], 'text_sha256': sha_text(text)[:16]} if status == 'agree' else {})
    return info


def _unify_pack(tab: str, raw: dict) -> dict:
    suggest = raw.get('suggest') or {}
    if raw['status'] == 'agree':
        decision = suggest.get('verdict') if tab == 'answers' else suggest.get('match') if tab == 'sources' else 'approve'
        opinions = [{'reviewer': o['reviewer'], 'confidence': o['confidence'], 'verdict': o['verdict'], 'reason': o['reason']} for o in raw.get('opinions', [])]
        return make_info('agree', raw['text'], decision, basis=raw.get('basis', 'earlier_passes'), opinions=opinions, risk=3)
    opinions = [{'reviewer': o['reviewer'], 'confidence': o['confidence'], 'verdict': o['verdict'], 'reason': o['reason']} for o in raw.get('opinions', [])]
    return make_info(raw['status'], raw['text'], opinions=opinions, risk=0 if raw['status'] == 'disagree' else 4)


def _gold_review_files(root: Path) -> list[tuple[str, list[dict]]]:
    out = []
    for name in sorted(glob.glob(str(Path(root) / 'experiments/gold/ai-review*/*.jsonl'))):
        label = os.path.relpath(name, Path(root) / 'experiments/gold')
        label = re.sub(r'\.jsonl$', '', label)
        out.append((label, rows(Path(name))))
    return out


def _flat(value) -> str:
    if value in (None, '', [], {}):
        return ''
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


FRESH_DIR = 'private/human-review/pending-ai'
FRESH_LABEL = 'Fresh blind review 2026-11-01'
FRESH_FIELDS = {'case_id', 'verdict', 'confidence', 'flags', 'reason'}
FRESH_VERDICTS = ('approve', 'change_label', 'reject')


def load_fresh(root: Path) -> dict[str, list[dict]]:
    """The six fresh blind reviews (two per dev case), read strictly if present. They are AI opinion only."""
    out: dict[str, list[dict]] = {}
    for name in sorted(glob.glob(str(Path(root) / FRESH_DIR / 'Pend*.jsonl'))):
        reviewer = Path(name).stem
        for number, rec in enumerate(rows(Path(name)), 1):
            where = f'{reviewer} line {number}'
            if not FRESH_FIELDS <= set(rec) <= FRESH_FIELDS | {'suggested_behavior'}:
                raise ValueError(f'{where}: unexpected fields')
            if rec['verdict'] not in FRESH_VERDICTS or not isinstance(rec['flags'], list) or not all(isinstance(f, str) for f in rec['flags']):
                raise ValueError(f'{where}: invalid verdict or flags')
            if rec['verdict'] == 'change_label' and rec.get('suggested_behavior') not in BEHAVIOURS:
                raise ValueError(f'{where}: change_label needs a valid suggested_behavior')
            out.setdefault(rec['case_id'], []).append({**rec, 'reviewer': reviewer})
    return out


def fresh_view(records: list[dict]) -> dict:
    """The net of the fresh reviewers for one case, plus the flags that need a look (anything other than 'other')."""
    votes = [f'change to {r["suggested_behavior"]}' if r['verdict'] == 'change_label' else r['verdict'] for r in records]
    if len(votes) == 2 and votes[0] == votes[1]:
        net = f'both {votes[0]}' if votes[0] == 'approve' else f'both {votes[0]}'
    elif len(votes) == 2:
        net = 'split (' + ' / '.join(votes) + ')'
    else:
        net = f'{len(votes)} reviewer(s): ' + ', '.join(votes)
    flags = sorted({f for r in records for f in r['flags'] if f != 'other'})
    change = any(r['verdict'] != 'approve' for r in records)
    return {'net': net, 'flags': flags, 'change': change, 'reviewers': [r['reviewer'] for r in records],
            'votes': {r['reviewer']: v for r, v in zip(records, votes)}}


def gold_dev_infos(root: Path, ids: list[str]) -> dict[str, dict]:
    """AI view of gold cases from the saved review files. Runs no AI. A case no file covers says so."""
    per_case: dict[str, list[dict]] = {}
    for label, records in _gold_review_files(root):
        for r in records:
            verdict = str(r.get('verdict', ''))
            proposal = _flat(r.get('proposed_changes') or r.get('proposed_correction'))
            if verdict in ('ok', 'agree'):
                kind = 'support'
            elif verdict in ('drop', 'disagree') or re.search(r'behaviou?r', proposal, re.I):
                kind = 'dispute'
            else:
                kind = 'concern'
            issues = r.get('issues') or []
            issues = issues if isinstance(issues, list) else [str(issues)]
            text = '; '.join(str(i) for i in issues[:2])[:360]
            confidence = r.get('confidence')
            per_case.setdefault(r['case_id'], []).append({'reviewer': label, 'verdict': verdict, 'kind': kind, 'confidence': str(confidence) if confidence is not None else '',
                                                          'reason': text or ('no issue raised' if kind == 'support' else 'see the review file')})
    fresh = load_fresh(root)
    for cid, records in fresh.items():
        for r in records:
            if r['verdict'] == 'approve':
                kind = 'concern' if any(f != 'other' for f in r['flags']) else 'support'
            else:
                kind = 'dispute'
            verdict = f'change to {r["suggested_behavior"]}' if r['verdict'] == 'change_label' else r['verdict']
            flags = f'[flags: {", ".join(r["flags"])}] ' if r['flags'] else ''
            per_case.setdefault(cid, []).append({'reviewer': f'{FRESH_LABEL}: {r["reviewer"]}', 'verdict': verdict, 'kind': kind, 'confidence': r['confidence'], 'reason': flags + r['reason'], 'fresh': True})
    adjudication = Path(root) / 'docs/human-review/ai-adjudication.md'
    flagged: dict[str, str] = {}
    if adjudication.exists():
        for line in adjudication.read_text().splitlines():
            m = re.match(r'^\| ((?:DEV|HO)-\d{3}) \|(.+)\|\s*([^|]+?)\s*\|$', line)
            if m and 'NEEDS-HUMAN-JUDGEMENT' in m[3]:
                flagged[m[1]] = m[3]
    out = {}
    for cid in ids:
        opinions = per_case.get(cid, [])
        note = flagged.get(cid)
        if not opinions and not note:
            out[cid] = make_info('none', 'No AI review file covers this case, and no AI was run for it. Decide yourself.', risk=2)
            continue
        counts = Counter(o['kind'] for o in opinions)
        summary = f'{len(opinions)} AI reviewer(s): {counts["support"]} found nothing wrong, {counts["concern"]} raised a concern, {counts["dispute"]} dispute the label or drop the case.'
        shown = [{'reviewer': o['reviewer'], 'confidence': o['confidence'] or 'n/a', 'verdict': o['verdict'], 'reason': o['reason']} for o in opinions]
        if note:
            summary += ' The AI adjudication marks this case as a judgement call for you (' + note.replace('NEEDS-HUMAN-JUDGEMENT', 'owner judgement') + ').'
        view = fresh_view(fresh[cid]) if cid in fresh else None
        if view:
            lead = f'{FRESH_LABEL} (two reviewers): {view["net"]}.'
            if view['change'] or view['flags']:
                lead += ' NOTE: ' + ('they say to change the label. ' if view['change'] else '') + ('Flags: ' + ', '.join(view['flags']) + '. ' if view['flags'] else '') + 'Look at this card first.'
            summary = lead + ' Earlier and fresh reviews together: ' + summary
        if view and (view['change'] or view['flags']):
            out[cid] = make_info('disagree', summary + ' ' + AI_DEV_NOTE, opinions=shown, risk=-2 if view['change'] else -1)
            out[cid]['fresh'] = view
            continue
        if counts['dispute']:
            out[cid] = make_info('disagree', summary + ' ' + AI_DEV_NOTE, opinions=shown, risk=0)
        elif counts['concern'] or note:
            out[cid] = make_info('disagree', summary + ' ' + AI_DEV_NOTE, opinions=shown, risk=1)
        else:
            weak = 'Only one AI reviewer looked at this case. ' if len(opinions) == 1 else ''
            out[cid] = make_info('agree', summary + ' ' + weak + 'Suggestion: the label is fine.', 'approve', basis='ai_review_files', opinions=shown, risk=2 if len(opinions) == 1 else 3)
        if view:
            out[cid]['fresh'] = view
    return out


def v2_infos(root: Path, cases: list[dict]) -> dict[str, dict]:
    ai = hv2.load_ai(root, cases)
    out = {}
    for c in cases:
        cid = c['case_id']
        if ai is None:
            out[cid] = make_info('none', 'No AI review file covers this case. Decide yourself.', risk=2)
            continue
        entry = hv2.ai_entry(ai, cid)
        opinions = [{'reviewer': f'v2 reviewer {r}', 'confidence': ai['reviews'][r][cid]['confidence'], 'verdict': hv2._vote_text(entry['votes'][r]), 'reason': ai['reviews'][r][cid]['reason']} for r in hv2.AI_REVIEWERS]
        if entry['agreeable']:
            decision = 'change' if entry['action'] == 'change' else entry['action']
            out[cid] = make_info('agree', f'3 AI reviewers: {entry["label"]}.', decision, entry['behaviour'] or '', basis='heldout_v2_ai_files', opinions=opinions, risk=3 if entry['action'] == 'approve' else 1)
        else:
            why = 'the reviewers disagree' if entry['class'] == 'split' else 'the agreeing reviewers are low-confidence'
            out[cid] = make_info('disagree', f'3 AI reviewers: {entry["label"]} ({why}). Decide yourself.', opinions=opinions, risk=0)
    return out


def ai_infos(root: Path, st: State) -> dict[tuple[str, str], dict]:
    """The AI view of every item in every stream, whether or not it is pending."""
    out: dict[tuple[str, str], dict] = {}
    root = st.root
    counts = {'passage': sum(k.startswith('passage') for k in st.source_ids), 'statistical': sum(k.startswith('statistical') for k in st.source_ids)}
    if st.sample or st.source_ids:
        raw = pack.ai_suggestions(root, st.gold_by_id, st.sample, counts)
        raw = pack.apply_tiebreak(raw, pack.load_tiebreak(root))
        for (tab, cid), info in raw.items():
            out[(tab, cid)] = _unify_pack(tab, info)
    pack_gold = {cid for (tab, cid) in out if tab == 'gold'}
    dev_ids = [c['case_id'] for c in st.gold if c['case_id'] not in pack_gold]
    for cid, info in gold_dev_infos(root, dev_ids).items():
        out[('gold', cid)] = info
    for cid, info in v2_infos(root, st.v2_cases).items():
        out[('v2', cid)] = info
    return out


# ---------------------------------------------------------------- the plan: which cards exist (no HTML)

def _answer_status(st: State, cid: str) -> str:
    r = st.runs.get(cid, {})
    return str((r.get('answer') or {}).get('status', r.get('outcome')))


def plan(root: Path, st: State) -> list[dict]:
    """Every pending and redo card with its options, AI view and the owner's earlier decision. Order: pending first, risk first."""
    infos = ai_infos(root, st)
    cards: list[dict] = []

    def add(stream, queue, cid, family, title, info, earlier, **extra):
        cards.append({'key': f'{stream}:{cid}', 'stream': stream, 'queue': queue, 'case_id': cid, 'family': family, 'title': title, 'ai': info,
                      'earlier': earlier, 'risk': info['risk'], **extra})

    for c in st.gold:
        cid = c['case_id']
        source = st.gold_source(cid)
        info = infos[('gold', cid)]
        if cid in st.proposals:
            p = st.proposals[cid]
            add('gold', 'proposal', cid, c['family'], cid, info, f'You marked this label wrong and proposed “{p["proposed_behavior"]}” (draft says “{c["expected_behavior"]}”). The change was never applied.', behavior=c['expected_behavior'], proposed=p['proposed_behavior'])
        elif source is None:
            add('gold', 'pending', cid, c['family'], cid, info, 'You have not decided this case.', behavior=c['expected_behavior'])
        elif source == AGREED:
            add('gold', 'redo', cid, c['family'], cid, info, 'You pressed Agree with AI on this card.', behavior=c['expected_behavior'])
    for cid in st.sample:
        if st.main_source('answers', cid) == AGREED and cid in st.runs:
            c = st.gold_by_id[cid]
            add('answers', 'redo', cid, c['family'], cid, infos[('answers', cid)], 'You pressed Agree with AI on this saved answer.', behavior=c['expected_behavior'], status=_answer_status(st, cid))
    for cid, identifier in st.source_ids.items():
        if st.main_source('sources', cid) == AGREED:
            add('sources', 'redo', cid, cid.split('-')[0], cid, infos[('sources', cid)], 'You pressed Agree with AI on this source check.', passage=identifier)
    for c in st.v2_cases:
        prov = st.v2_provenance.get(c['case_id']) or {}
        if prov.get('decision_source') == AGREED:
            add('v2', 'redo', c['case_id'], c['family'], c['case_id'], infos[('v2', c['case_id'])], 'You pressed Agree with AI on this held-out v2 card (the v2 test is already signed and frozen).', behavior=c['expected_behavior'])
    j10_final = st.main.get(('decisions', 'J10'))
    if (st.root / 'data/manifests/manifest.json').exists() and j10_final is not None and j10_final['fields'].decision in ('inspect_more', ''):
        none = make_info('none', 'No AI suggestion: this is your own inspection of the original page.', risk=1)
        for cid, source_id, page, passage, title, gap in J10_ITEMS:
            add('j10', 'pending', cid, 'extraction', title, none, 'Your J10 decision was “I need more inspection before deciding”.', source_id=source_id, page=page, passage=passage, gap=gap)
        add('j10', 'pending', J10_FINAL[0], 'extraction', J10_FINAL[1], none, 'Your J10 decision was “I need more inspection before deciding”.', question=J10_FINAL[2], final=True)
    queue_order = {'proposal': 0, 'pending': 1, 'redo': 2}
    stream_order = {'j10': 0, 'gold': 1, 'v2': 2, 'answers': 3, 'sources': 4}

    def key(c):
        family = FAMILY_ORDER.index(c['family']) if c['family'] in FAMILY_ORDER else len(FAMILY_ORDER)
        return (queue_order[c['queue']], stream_order[c['stream']], bool(c.get('final')), c['risk'], family, c['case_id'])

    return sorted(cards, key=key)


def pack_id(root: Path, st: State) -> str:
    material = {'gold': sha256_file(root / GOLD_DRAFT), 'v2': sha256_file(root / hv2.DRAFT) if (root / hv2.DRAFT).exists() else '', 'main': st.main_sha,
                'ai': ai_file_hashes(root), 'plan': 'pending-review-v1'}
    return hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest()[:16]


# ---------------------------------------------------------------- inventory

def _count(values) -> Counter:
    return Counter(values)


def inventory(root: Path, st: State) -> dict:  # State(use_overlay=True) shows the state after pending-ingest --write
    """All counts, computed from files. Returns rows plus the lists of pending ids."""
    root = st.root
    infos = ai_infos(root, st)
    rows_: list[dict] = []
    pending: dict[str, list[str]] = {}

    def row(name, what, population, manual, agreed, ai_only, untouched, ai_files, stored, wording, **extra):
        rows_.append({'name': name, 'what': what, 'population': population, 'manual': manual, 'agreed': agreed, 'ai_only': ai_only, 'untouched': untouched,
                      'ai_files': ai_files, 'stored': stored, 'wording': wording, **extra})

    ho = [c for c in st.gold if c['case_id'].startswith('HO-')]
    extra = [c for c in st.gold if c['case_id'] in pack.EXTRA]
    rest = [c for c in st.gold if not c['case_id'].startswith('HO-') and c['case_id'] not in pack.EXTRA]

    def tally(cases):
        s = Counter(st.gold_source(c['case_id']) or 'none' for c in cases)
        return s[MANUAL], s[AGREED], s['none']

    gold_files = 'private/human-review/pending-ai/Pend{A,B}{1,2,3}.jsonl (fresh blind, two per dev case); experiments/gold/ai-review/{base,a,b,c}.jsonl; experiments/gold/ai-review-2/{a,b}.jsonl; experiments/gold/ai-review-3/v3.jsonl; docs/human-review/ai-adjudication.md; private/human-review/tiebreak/'
    gold_store = '`owner_review` on each record of `experiments/gold/draft_cases.jsonl` (reviewer, decision_source, date); full export in the private main export'
    m, a, n = tally(ho)
    row('Gold: original held-out cases (HO-001…031)', 'Is the expected behaviour, evidence and facts of each case right?', len(ho), m, a, 0, n, gold_files, gold_store,
        f'{m} reviewed by the owner’s own click and {a} by the owner agreeing with an AI suggestion, per card.')
    m, a, n = tally(extra)
    row('Gold: 14 extra owner-decision dev cases', 'Same question, for the dev cases the owner was asked to look at', len(extra), m, a, 0, n, gold_files, gold_store,
        f'{m} reviewed by the owner’s own click and {a} by the owner agreeing with an AI suggestion, per card.')
    m, a, n = tally(rest)
    covered = gold_dev_infos(root, [c['case_id'] for c in rest])
    uncovered = [cid for cid, i in covered.items() if i['status'] == 'none']
    coverage = Counter(len([1 for _, recs in _gold_review_files(root) for r in recs if r['case_id'] == cid]) for cid in (c['case_id'] for c in rest))
    pending['gold dev, never decided by the owner'] = [c['case_id'] for c in rest if st.gold_source(c['case_id']) is None]
    row('Gold: remaining dev cases', 'Same question; these are the development cases the system was tuned on', len(rest), m, a, n - len(uncovered), len(uncovered), gold_files, 'nothing yet (pending-review pack)',
        f'AI-reviewed only: {n - len(uncovered)} cases (AI reviewers per case: ' + ', '.join(f'{k}: {v}' for k, v in sorted(coverage.items())) + '). Not reviewed by the owner.')
    v2 = st.v2_provenance
    m2 = sum((v or {}).get('decision_source') == MANUAL for v in v2.values())
    a2 = sum((v or {}).get('decision_source') == AGREED for v in v2.values())
    pending['held-out v2 agreed with AI (optional redo)'] = [cid for cid, v in v2.items() if (v or {}).get('decision_source') == AGREED]
    row('Held-out v2 cases (HO-V2-001…065)', 'Were the 65 new test questions and labels right? (signed and frozen before the run)', len(st.v2_cases), m2, a2, len(st.v2_cases) - m2 - a2, 0,
        'private/human-review/heldout-v2-ai/{A,B,C}.jsonl', f'`owner_review` on each record of `{hv2.APPROVED}`; export `{V2_EXPORT}`; signed block in `experiments/heldout-v2/FREEZE.md`',
        f'{m2} by the owner’s own click, {a2} by agreeing with an AI suggestion.')
    ans = [cid for cid in st.sample]
    sa = Counter(st.main_source('answers', cid) or 'none' for cid in ans)
    pending['answers agreed with AI (optional redo)'] = [cid for cid in ans if st.main_source('answers', cid) == AGREED]
    row('Saved model answers (sample of 40)', 'Is each saved answer right, partly right or wrong?', len(ans), sa[MANUAL], sa[AGREED], sa['none'], 0,
        'experiments/human-review-sample/*.md (two AI passes); private/human-review/tiebreak/', 'private main export (`review-results (8).json`, tab answers); summary `docs/human-review/owner-review-summary.md`',
        f'{sa[MANUAL]} verdicts by the owner’s own click, {sa[AGREED]} by agreeing with an AI suggestion.')
    for kind, label in (('passage', 'Source checks: passage extraction'), ('statistical', 'Source checks: statistical rows')):
        ids = [k for k in st.source_ids if k.startswith(kind)]
        s = Counter(st.main_source('sources', k) or 'none' for k in ids)
        pending[f'{kind} checks agreed with AI (optional redo)'] = [k for k in ids if st.main_source('sources', k) == AGREED]
        row(label, 'Does the extracted text or value match the original page or table row?', len(ids), s[MANUAL], s[AGREED], s['none'], 0,
            'docs/human-review/ai-pre-review-*-spot-check.md; docs/human-review/ai-verification-of-pre-reviews.md', 'private main export (tab sources)',
            f'{s[MANUAL]} by the owner’s own click, {s[AGREED]} by agreeing with an AI suggestion.')
    dec = [('decisions', f'J{i}') for i in range(1, 11)]
    decided = [k for k in dec if st.main.get(k, {}).get('source')]
    j10_decision = st.j10_decision()
    unresolved = j10_decision == 'inspect_more'
    if unresolved:
        pending['J10 extraction gaps (owner asked for more inspection)'] = [i[0] for i in J10_ITEMS] + ['J10']
    row('Owner decisions J1–J10', 'Methodology and acceptance choices (rubric, rights, limits)', 10, len(decided), 0, 0, 10 - len(decided), 'none (judgement calls; AI adjudication lists them)',
        'private main export (tab decisions); `docs/human-review/owner-review-summary.md`',
        f'{len(decided)} chosen by the owner. J10 is "{j10_decision or "undecided"}": ' + ('an explicit request for more inspection, not acceptance.' if unresolved else 'accepted with the frozen extraction gaps disclosed, not fixed (own clicks on five original pages).' if j10_decision == 'accept_limits' else 'see the summary.'))
    unapplied = list(st.proposals)
    all_proposals = rows(Path(root) / PROPOSALS) if (Path(root) / PROPOSALS).exists() else []
    applied = [p['case_id'] for p in all_proposals if str(p.get('status', '')).startswith(('applied', 'export_noop'))]
    pending['owner label-change proposals not yet applied'] = unapplied
    row('Owner label-change proposals', 'Label changes the owner proposed in the main pack', len(all_proposals), len(all_proposals), 0, 0, 0, 'none', f'`{PROPOSALS}`; chat confirmations quoted in `{CHANGELOG}`',
        f'{len(applied)} applied in gold v3.5 on the owner’s chat confirmation ({", ".join(applied) or "none"}); {len(unapplied)} still waiting. Chat confirmation is the owner’s decision but not a per-card click in a pack.')
    structured = Path(root) / 'experiments/gold/heldout_v2_structured_draft.jsonl'
    n_structured = len(rows(structured)) if structured.exists() else 0
    row('Held-out v2 structured draft (60 cases)', 'The reserved structured-only draft of v2 (`HO-V2S-…`), kept on file and not used for the signed test', n_structured, 0, 0, 0, n_structured, 'none',
        'nothing', 'kept as a draft: never reviewed by anyone and not part of any result.')
    threats = Path(root) / 'experiments/threats/cases.jsonl'
    n_threats = len(rows(threats)) if threats.exists() else 0
    row('Threat-suite cases and verdicts', 'Does the system resist injection, secret requests and unsafe tools?', n_threats, 0, 0, n_threats, 0, 'automatic scorer (experiments/threats/runs/*.verdicts.jsonl)',
        'nothing (no human verdicts exist)', 'scored automatically; not human-reviewed.')
    row('Automatic judge validation', 'Does the automatic judge agree with a reference?', 40, 0, 0, 40, 0, 'AI pre-review used as reference (docs/evaluation-report.md)', 'nothing',
        'validated against an AI pre-review only. The owner’s manual answer verdicts could serve as the human reference but this has not been computed.')
    audits = sorted(glob.glob(str(Path(root) / 'experiments/heldout-v2/*audit*.json')))
    row('Extraction and evidence audits', 'Were extraction fixes and evidence ids migrated correctly?', len(audits) + 1, 0, 0, len(audits) + 1, 0, 'experiments/heldout-v2/evidence-audit*.json; experiments/gold/evidence-migration-v3.6.json; docs/experiments/m7-extraction-fixes.md',
        'nothing', 'machine and AI audits only; J10 covers the human acceptance.')
    ai_docs = sorted(str(f) for pattern in ('e2e-review-*.md', 'copy-audit.md', 'deck-copy-review.md', 'site-artifact-review.md', 'independent-ai-review-m1*.md')
                     for f in (Path(root) / 'docs/human-review').glob(pattern))
    row('AI reviews of documents, deck, site and code', 'End-to-end, copy, deck, site and security reviews', len(ai_docs), 0, 0, len(ai_docs), 0, ', '.join(os.path.relpath(d, root) for d in ai_docs[:12]) + (' …' if len(ai_docs) > 12 else ''),
        'nothing', 'AI reviews only; never described as human review.')
    return {'rows': rows_, 'pending': pending, 'main_sha': st.main_sha, 'main_path': str(st.main_path), 'reviewer': st.reviewer, 'exported_at': st.exported_at,
            'gold_sha': sha256_file(root / GOLD_DRAFT), 'ai_hashes': ai_file_hashes(root), 'infos_gold_uncovered': uncovered}


def inventory_markdown(root: Path, st: State) -> str:
    inv = inventory(root, st)
    lines = ['# Review inventory', '',
             'Every review stream in the project, with counts computed from files by `uv run labourlens review-inventory`. '
             '“Owner manual” means the owner’s own click on that card. “Agreed with AI” means the owner pressed Agree for that one card. '
             '“AI only” means an AI reviewed it and the owner has not decided it. “Untouched” means neither. Raw reviewer files and the owner’s export stay private.', '',
             f'Inputs: gold `{GOLD_DRAFT}` SHA-256 `{inv["gold_sha"]}`; main owner export (reviewer {inv["reviewer"]}, exported {inv["exported_at"]}) SHA-256 `{inv["main_sha"]}`; {len(inv["ai_hashes"])} AI source files hashed (listed in the pending-review export).', '',
             '| Stream | What is reviewed | Population | Owner manual | Agreed with AI | AI only | Untouched | Where the AI view comes from | Where the owner’s decisions are stored | Wording for the report |',
             '|---|---|---:|---:|---:|---:|---:|---|---|---|']
    for r in inv['rows']:
        lines.append(f'| {r["name"]} | {r["what"]} | {r["population"]} | {r["manual"]} | {r["agreed"]} | {r["ai_only"]} | {r["untouched"]} | {r["ai_files"]} | {r["stored"]} | {r["wording"]} |')
    total = {k: sum(r[k] for r in inv['rows'] if r['name'].startswith(('Gold', 'Held-out v2 cases', 'Saved', 'Source'))) for k in ('population', 'manual', 'agreed', 'ai_only', 'untouched')}
    all_manual = total['population'] and total['manual'] == total['population']
    lines += ['', f'Labelling and verdict streams together (gold, held-out v2, saved answers, source checks): {total["population"]} items, {total["manual"]} by the owner’s own click, {total["agreed"]} by agreeing with an AI suggestion, {total["ai_only"]} AI-reviewed only, {total["untouched"]} untouched.', '',
              '## Status wording that is true today', '',
              *([f'- All {total["population"]} labelling items were decided by the owner’s own click (pending-review export ingested). The report may say they were reviewed card by card by the owner, as one person’s review made after AI pre-review and after the runs were scored; it is not independent inter-rater evidence.']
                if all_manual else
                [f'- Do not write “all labelling was manually reviewed by the owner”. Today {total["manual"]} of {total["population"]} items were decided by the owner’s own click.',
                 f'- True: “The owner made a per-card decision on {total["manual"] + total["agreed"]} of {total["population"]} labelling items; {total["manual"]} by their own click and {total["agreed"]} by agreeing with an AI suggestion. The remaining {total["ai_only"] + total["untouched"]} were checked by AI reviewers only.”']),
              '- AI-only streams (threat suite, judge validation, audits, document reviews) are never called human review.', '',
              '## Pending items', '']
    for name, ids in inv['pending'].items():
        lines.append(f'### {name} ({len(ids)})')
        lines.append('')
        lines.append(', '.join(ids) if ids else 'none')
        lines.append('')
    lines += ['## How to finish', '', '1. `uv run labourlens pending-review-pack`, then open `private/human-review/pending-review/index.html` and decide the cards (turn on “Manual only” so every decision is your own click).',
              '2. `uv run labourlens pending-ingest --review-export <downloaded file>` (dry run), then add `--write`.', '']
    return '\n'.join(lines)


def write_inventory(root: Path = ROOT, main_export: Path | None = None) -> Path:
    from labourlens.data import rights_scan

    root = Path(root).resolve()
    st = State(root, main_export, use_overlay=True)
    text = inventory_markdown(root, st)
    passages = root / 'data' / 'passages'
    if passages.exists():
        hits = rights_scan.scan_text(text, rights_scan.build_shingles(passages))
        if hits:
            raise ValueError(f'The inventory would quote source passages (lines {[h[0] for h in hits][:5]})')
    out = root / INVENTORY
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    return out


# ---------------------------------------------------------------- strict export and ingest

class PendingResult(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    key: str
    stream: str
    queue: str
    case_id: str
    decision: str
    proposed_behavior: str = ''
    reason: str = ''
    comment: str = Field(default='', max_length=4000)
    decision_source: str = ''
    ai_basis: dict = Field(default_factory=dict)
    timestamp: str

    @model_validator(mode='after')
    def valid(self):
        if self.stream not in DECISIONS or self.queue not in QUEUE_LABEL or self.key != f'{self.stream}:{self.case_id}':
            raise ValueError(f'{self.key}: invalid stream, queue or key')
        parse_timestamp(self.timestamp)
        if self.decision not in DECISIONS[self.stream]:
            raise ValueError(f'{self.key}: invalid decision {self.decision!r}')
        if self.decision_source not in SOURCES:
            raise ValueError(f'{self.key}: decision_source must be {MANUAL} or {AGREED}')
        if self.decision == 'change' and self.proposed_behavior not in BEHAVIOURS:
            raise ValueError(f'{self.key}: change needs a valid proposed_behavior')
        if self.decision != 'change' and self.proposed_behavior:
            raise ValueError(f'{self.key}: only a change may carry proposed_behavior')
        if self.decision in REASON_REQUIRED and not self.reason.strip():
            raise ValueError(f'{self.key}: {self.decision} needs a reason')
        if self.decision_source == AGREED and not self.ai_basis:
            raise ValueError(f'{self.key}: {AGREED} needs an ai_basis')
        if self.decision_source == MANUAL and self.ai_basis:
            raise ValueError(f'{self.key}: an {MANUAL} decision carries no ai_basis')
        return self


class PendingExport(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    schema_version: int
    kind: str
    pack_id: str
    reviewer_name: str = Field(max_length=200)
    exported_at: str
    main_export_sha256: str
    ai_files_sha256: dict[str, str]
    results: list[PendingResult]

    @model_validator(mode='after')
    def valid(self):
        if self.schema_version != 1 or self.kind != 'pending_review':
            raise ValueError('Not a pending-review export')
        if not self.reviewer_name.strip():
            raise ValueError('Reviewer name is required')
        parse_timestamp(self.exported_at)
        keys = [r.key for r in self.results]
        if len(keys) != len(set(keys)):
            raise ValueError('Duplicate cards in the export')
        return self


def load_pending_export(path: Path, root: Path, st: State) -> tuple[PendingExport, str, list[dict]]:
    raw = Path(path).read_bytes()
    export = PendingExport.model_validate_json(raw)
    cards = plan(root, st)
    by_key = {c['key']: c for c in cards}
    if export.pack_id != pack_id(root, st):
        raise ValueError('The export was made for a different version of the inputs (gold, owner export or AI files). Rebuild the pending pack and review again.')
    if export.main_export_sha256 != st.main_sha:
        raise ValueError('The owner export of the main pack differs from the one the page was built with')
    if export.ai_files_sha256 != ai_file_hashes(root):
        raise ValueError('The AI review files differ from the ones the page was built with (SHA-256 mismatch)')
    for r in export.results:
        card = by_key.get(r.key)
        if card is None:
            raise ValueError(f'{r.key}: not a card of this pending pack')
        if (r.stream, r.queue, r.case_id) != (card['stream'], card['queue'], card['case_id']):
            raise ValueError(f'{r.key}: stream or queue does not match the card')
        if r.decision == 'change' and r.proposed_behavior == card.get('behavior'):
            raise ValueError(f'{r.key}: change to the behaviour it already has')
        if r.stream == 'j10':
            final = card.get('final')
            allowed = J10_FINAL_DECISIONS if final else J10_ITEM_DECISIONS
            if r.decision not in allowed:
                raise ValueError(f'{r.key}: invalid J10 decision')
        if r.decision_source == AGREED:
            ai = card['ai']
            if ai['status'] != 'agree':
                raise ValueError(f'{r.key}: the AI reviewers gave no one-click suggestion, so agreeing with them is not allowed')
            if r.ai_basis != ai['ai_basis']:
                raise ValueError(f'{r.key}: ai_basis does not match the AI review files')
            if (r.decision, r.proposed_behavior) != (ai['decision'], ai['proposed_behavior']):
                raise ValueError(f'{r.key}: the decision does not match the AI suggestion')
    return export, hashlib.sha256(raw).hexdigest(), cards


def remaining(cards: list[dict], export: PendingExport) -> dict[str, list[str]]:
    done = {r.key for r in export.results}
    out: dict[str, list[str]] = {}
    for c in cards:
        if c['key'] not in done:
            out.setdefault(c['queue'], []).append(c['key'])
    return out


# ---------------------------------------------------------------- applying to a new gold version

POLICY_FILE = 'experiments/gold/v3.7-policy-decisions.json'


def load_policy(path: Path, root: Path) -> dict:
    """The owner's later policy decisions that stop specific recorded 'change' clicks from being applied. Strict, no extra fields."""
    path = Path(path)
    path = path if path.is_absolute() else Path(root) / path
    data = json.loads(path.read_text())
    if not isinstance(data, dict) or set(data) != {'policy_ref', 'decided', 'text', 'non_applied_changes'}:
        raise ValueError('Policy file: expected exactly policy_ref, decided, text and non_applied_changes')
    date.fromisoformat(data['decided'])
    cases = {}
    for item in data['non_applied_changes']:
        if not isinstance(item, dict) or set(item) != {'case_id', 'proposed_behavior'} or item['proposed_behavior'] not in BEHAVIOURS or item['case_id'] in cases:
            raise ValueError(f'Policy file: invalid or duplicate entry {item!r}')
        cases[item['case_id']] = item['proposed_behavior']
    return {'ref': data['policy_ref'], 'decided': data['decided'], 'text': data['text'], 'cases': cases, 'sha256': sha256_file(path)}


def apply_to_gold(st: State, export: PendingExport, export_sha: str, policy: dict | None = None) -> tuple[list[dict], list[dict], dict]:
    """Returns (new gold records, per-case review log, report). Existing pinned files are never touched.

    With a policy, the set of recorded 'change' clicks must equal the policy's list exactly: nothing is dropped silently and no entry is stale."""
    recorded = {r.case_id: r.proposed_behavior for r in export.results if r.stream == 'gold' and r.decision == 'change'}
    if policy is not None and recorded != policy['cases']:
        missing = sorted(set(recorded) - set(policy['cases']))
        extra = sorted(set(policy['cases']) - set(recorded))
        different = sorted(c for c in set(recorded) & set(policy['cases']) if recorded[c] != policy['cases'][c])
        raise ValueError(f'The non-applied changes in the policy file do not match the export: change(s) in the export but not in the policy {missing}; in the policy but not in the export {extra}; different behaviour {different}')
    not_applied = []
    today = parse_timestamp(export.exported_at).date().isoformat()
    by_key = {r.key: r for r in export.results}
    out, log, changed, dropped = [], [], [], []
    for c in st.gold:
        cid = c['case_id']
        r = by_key.get(f'gold:{cid}')
        new = json.loads(json.dumps(c))
        if r is None:
            out.append(new)
            continue
        entry = {'case_id': cid, 'queue': r.queue, 'decision': r.decision, 'decision_source': r.decision_source, 'reason': r.reason, 'comment': r.comment,
                 'reviewer': export.reviewer_name, 'timestamp': r.timestamp, 'export_sha256': export_sha, 'ai_basis': r.ai_basis or None,
                 'earlier_source': st.gold_source(cid), 'original_behavior': c['expected_behavior']}
        if r.decision == 'reject':
            dropped.append(cid)
            entry.update(applied=True, applied_note='case removed from gold v3.7')
            log.append(entry)
            continue
        entry['applied'] = True
        if r.decision == 'change' and policy is not None:
            not_applied.append((cid, c['expected_behavior'], r.proposed_behavior))
            entry.update(applied=False, policy_ref=policy['ref'], policy_text=policy['text'], applied_note=f'recorded click: change {c["expected_behavior"]} -> {r.proposed_behavior}; not applied, label stays {c["expected_behavior"]}')
        elif r.decision == 'change':
            new = hv2._relabel(new, r.proposed_behavior, r.reason)
            changed.append((cid, c['expected_behavior'], r.proposed_behavior))
            entry['applied_note'] = f'label {c["expected_behavior"]} -> {r.proposed_behavior}'
        else:
            entry['applied_note'] = 'label kept'
        new['review_status'] = 'owner_reviewed'
        new['reviewed_by'] = export.reviewer_name
        new['owner_review'] = {'reviewer': export.reviewer_name, 'decision_source': r.decision_source, 'date': today}
        out.append(new)
        log.append(entry)
    return out, log, {'changed': changed, 'dropped': dropped, 'not_applied': not_applied, 'policy': policy}


def final_provenance(st: State, export: PendingExport) -> dict[str, dict]:
    """Per stream, the final source of each item: the pending decision if there is one, else the owner's earlier one."""
    by_key = {r.key: r for r in export.results}
    final: dict[str, dict] = {s: {} for s in ('gold', 'answers', 'sources', 'v2')}
    for c in st.gold:
        r = by_key.get(f'gold:{c["case_id"]}')
        final['gold'][c['case_id']] = r.decision_source if r else st.gold_source(c['case_id'])
    for cid in st.sample:
        r = by_key.get(f'answers:{cid}')
        final['answers'][cid] = r.decision_source if r else st.main_source('answers', cid)
    for cid in st.source_ids:
        r = by_key.get(f'sources:{cid}')
        final['sources'][cid] = r.decision_source if r else st.main_source('sources', cid)
    for c in st.v2_cases:
        r = by_key.get(f'v2:{c["case_id"]}')
        final['v2'][c['case_id']] = r.decision_source if r else (st.v2_provenance.get(c['case_id']) or {}).get('decision_source')
    return final


def _decision_of_main(tab: str, f) -> str | None:
    if tab == 'gold':
        return 'approve' if f.label == 'OK' else 'change' if f.label == 'disagree' else None
    if tab == 'answers':
        return f.verdict or None
    return f.match or None


def manual_vs_ai(st: State, export: PendingExport, infos: dict) -> dict[str, tuple[int, int]]:
    """Agreement with the AI suggestion, counted over owner_manual decisions only (earlier and new), where a suggestion exists."""
    stats = {s: [0, 0] for s in ('gold', 'answers', 'sources', 'v2')}

    def record(stream, cid, decision, behaviour=''):
        info = infos.get((stream, cid))
        if not info or info['status'] != 'agree' or decision is None:
            return
        stats[stream][1] += 1
        stats[stream][0] += (decision, behaviour) == (info['decision'], info['proposed_behavior'])

    by_key = {r.key: r for r in export.results}
    for (tab, cid), item in st.main.items():
        if tab in ('gold', 'answers', 'sources') and item['source'] == MANUAL and f'{tab}:{cid}' not in by_key:
            if tab == 'gold' and cid in st.gold_by_id and st.gold_source(cid) != MANUAL:
                continue
            record(tab, cid, _decision_of_main(tab, item['fields']), item['fields'].proposed_behavior if tab == 'gold' and item['fields'].label == 'disagree' else '')
    for cid in st.v2_cases:
        prov = st.v2_provenance.get(cid['case_id']) or {}
        if prov.get('decision_source') == MANUAL and f'v2:{cid["case_id"]}' not in by_key:
            record('v2', cid['case_id'], prov.get('decision'), '')
    for r in export.results:
        if r.stream in stats and r.decision_source == MANUAL:
            record(r.stream, r.case_id, r.decision, r.proposed_behavior)
    return {s: (a, b) for s, (a, b) in stats.items()}


def policy_changelog(report: dict) -> str:
    if not report.get('not_applied'):
        return ''
    pol = report['policy']
    ids = ', '.join(f'{i} (clicked: {a} -> {b})' for i, a, b in report['not_applied'])
    return (f'**Policy ({pol["ref"]}, {pol["decided"]}):** {pol["text"]}. Recorded owner clicks not applied, labels unchanged from v3.6: {ids}. '
            f'The clicks stay in `{GOLD_V37_LOG}` (decision_source owner_manual, applied false, policy_ref {pol["ref"]}); policy file `{POLICY_FILE}` SHA-256 `{pol["sha256"]}`.\n\n')


def changelog_entry(export: PendingExport, export_sha: str, report: dict, new_sha: str, counts: dict) -> str:
    changes = ', '.join(f'{i} {a}->{b}' for i, a, b in report['changed']) or 'none'
    dropped = ', '.join(report['dropped']) or 'none'
    return (f'## v3.7: owner review of the cases never reviewed before ({export.exported_at[:10]}), post-hoc\n\n'
            f'**DECISION:** New file `{GOLD_V37}` (SHA-256 `{new_sha}`); `draft_cases.jsonl` (v3.6) and every older file are untouched, and every saved run, freeze and score stays pinned to the file it used. '
            f'Reviewer `{export.reviewer_name}`, export SHA-256 `{export_sha}`. Per-case decisions: `{GOLD_V37_LOG}`.\n\n'
            f'**Counts in this version:** {counts["manual"]} cases decided by the owner’s own click, {counts["agreed"]} by the owner agreeing with an AI suggestion, {counts["none"]} without an owner decision. '
            f'Label changes: {changes}. Cases removed: {dropped}.\n\n'
            + policy_changelog(report)
            + '**Post-hoc disclosure:** these changes were made after the saved runs were scored on v3.5/v3.6. They do not alter those results. Any rescoring on v3.7 is a separate, labelled sensitivity analysis.\n\n')


def wording(counts: dict[str, dict]) -> list[str]:
    total = sum(sum(v.values()) for v in counts.values())
    manual = sum(v.get(MANUAL, 0) for v in counts.values())
    agreed = sum(v.get(AGREED, 0) for v in counts.values())
    none = total - manual - agreed
    if total and manual == total:
        return [f'All {total} labelling items (gold cases, held-out v2 cases, saved-answer verdicts and source checks) were reviewed card by card by the owner, each by the owner’s own decision.',
                'This is one person’s review, made after AI pre-review and after the saved runs were scored; it is not independent inter-rater evidence.']
    sentences = [f'The owner made a per-card decision on {manual + agreed} of {total} labelling items: {manual} by their own click and {agreed} by agreeing with an AI suggestion.']
    if none:
        sentences.append(f'The other {none} items were reviewed by AI reviewers only.')
    sentences.append('Agreement with an AI suggestion is not independent human review and is not used in agreement statistics.')
    return sentences


def final_summary(root: Path, st: State, export: PendingExport, export_sha: str, cards: list[dict], report: dict, new_sha: str | None, infos: dict, written: bool) -> tuple[str, list[str]]:
    final = final_provenance(st, export)
    counts = {s: Counter(v or 'none' for v in vs.values()) for s, vs in final.items()}
    agreement = manual_vs_ai(st, export, infos)
    wording_lines = wording({s: dict(c) for s, c in counts.items()})
    pending_left = remaining(cards, export)
    prior = {s: Counter() for s in final}
    for (tab, cid), item in st.main.items():
        if tab in prior and item['source']:
            prior[tab][item['source']] += 1
    lines = ['# Owner review: final summary', '',
             f'Reviewer: {export.reviewer_name}. Pending-review export {export.exported_at}, SHA-256 `{export_sha}`. Status: ' + ('written' if written else 'dry run, nothing written') + '.', '',
             '## What is and is not independent human evidence', '',
             '- **Own clicks (`owner_manual`)** are the owner’s own per-card judgement. They are one person’s review, made after AI pre-review and after the saved runs were scored.',
             '- **Agreed with AI (`agreed_with_ai_suggestion`)** are per-card decisions where the owner accepted an AI suggestion. They are reported separately, are never described as manual, and are excluded from every agreement statistic below.',
             '- This is not independent inter-rater evidence: there is one human reviewer, and the AI reviewers are one model family.',
             '- Gold changes made now are post-hoc: the saved runs and freezes keep the gold file they were scored on.', '',
             '## Final provenance by stream', '', '| Stream | Items | Owner manual | Agreed with AI | No owner decision |', '|---|---:|---:|---:|---:|']
    for s in ('gold', 'v2', 'answers', 'sources'):
        c = counts[s]
        lines.append(f'| {STREAM_LABEL[s]} | {sum(c.values())} | {c[MANUAL]} | {c[AGREED]} | {c["none"]} |')
    total = Counter()
    for c in counts.values():
        total.update(c)
    lines += [f'| **All** | {sum(total.values())} | {total[MANUAL]} | {total[AGREED]} | {total["none"]} |', '',
              '## This pending-review export', '', f'- Cards decided: {len(export.results)}: {sum(r.decision_source == MANUAL for r in export.results)} by own click, {sum(r.decision_source == AGREED for r in export.results)} agreed with AI.']
    by_queue = Counter((r.queue, r.decision_source) for r in export.results)
    for q in ('proposal', 'pending', 'redo'):
        lines.append(f'  - {QUEUE_LABEL[q]}: {by_queue[(q, MANUAL)]} own click, {by_queue[(q, AGREED)]} agreed with AI, {len(pending_left.get(q, []))} still undecided.')
    j10 = [r for r in export.results if r.stream == 'j10']
    if j10:
        lines += ['', '### J10 extraction gaps', '', '| Item | Your decision | Reason |', '|---|---|---|']
        for r in sorted(j10, key=lambda r: r.case_id):
            lines.append(f'| {r.case_id} | {r.decision} | {pack.md_cell(r.reason) if r.reason else ""} |')
    fresh_rows = [(cid, info['fresh']) for (stream, cid), info in sorted(infos.items()) if stream == 'gold' and info.get('fresh')]
    if fresh_rows:
        decided = {r.case_id: r for r in export.results if r.stream == 'gold'}
        flagged_rows = [(cid, f) for cid, f in fresh_rows if f['change'] or f['flags']]
        lines += ['', f'## Fresh blind AI review of the development cases ({FRESH_LABEL}): AI opinion only', '',
                  f'Two independent AI reviewers per case looked at {len(fresh_rows)} development cases before your review. Their verdicts are AI opinion, never human review, and were shown below each card for reference only. '
                  f'Net: ' + ', '.join(f'{k} {v}' for k, v in sorted(Counter(f['net'].split(' (')[0] for _, f in fresh_rows).items())) + '.', '',
                  '| Case | Fresh net | Flags other than “other” | Your decision | Source |', '|---|---|---|---|---|']
        for cid, f in flagged_rows:
            r = decided.get(cid)
            skipped = any(i == cid for i, _, _ in report.get('not_applied', []))
            lines.append(f'| {cid} | {f["net"]} | {", ".join(f["flags"]) or "none"} | ' + (f'{r.decision}' + (f' to {r.proposed_behavior}' if r.proposed_behavior else '') + (' (click recorded, not applied: ' + report['policy']['ref'] + ')' if skipped else '') if r else 'not decided') + f' | {r.decision_source if r else "n/a"} |')
        if not flagged_rows:
            lines.append('| none | | | | |')
    if report.get('not_applied'):
        pol = report['policy']
        lines += ['', '## Owner clicks not applied because of a later policy decision', '',
                  f'Policy {pol["ref"]} ({pol["decided"]}): {pol["text"]}. The clicks are recorded as owner_manual, with applied false; the labels stay as in v3.6.', '',
                  '| Case | Label in v3.6 | Owner click | Applied |', '|---|---|---|---|'] + [f'| {i} | {a} | change to {b} | no ({pol["ref"]}) |' for i, a, b in report['not_applied']]
    j10_final_result = next((r for r in export.results if r.key == 'j10:J10'), None)
    if j10_final_result is not None:
        accepted = [r.case_id for r in export.results if r.stream == 'j10' and r.decision == 'accept']
        meaning = {'accept_limits': 'The owner accepted the disclosed frozen extraction gaps, with the limits disclosed, after inspecting the original pages. This is acceptance of limitations, not a claim that the defects were fixed.',
                   'require_fixes': 'The owner did not accept the gaps until specific fixes are made.', 'inspect_more': 'The owner still needs more inspection: J10 stays open.'}[j10_final_result.decision]
        lines += ['', '## J10 (human acceptance of the frozen extraction gaps)', '', f'- Decision: `{j10_final_result.decision}` (own click). Items accepted individually: {len(accepted)} of {len([r for r in export.results if r.stream == "j10"]) - 1} ({", ".join(sorted(accepted)) or "none"}).',
                  f'- {meaning}', '- Progress wording: “J10: accepted by the owner (own clicks) with the frozen extraction gaps disclosed and not fixed in the saved runs.”' if j10_final_result.decision == 'accept_limits' else '- Progress wording: J10 remains open.']
    lines += ['', '## Gold changes (post-hoc)', '', f'- Label changes: {", ".join(f"{i} {a} -> {b}" for i, a, b in report["changed"]) or "none"}.',
              f'- Cases removed: {", ".join(report["dropped"]) or "none"}.',
              f'- New file: `{GOLD_V37}`' + (f' (SHA-256 `{new_sha}`)' if new_sha else ' (not written in a dry run)') + '; older gold files are untouched.',
              f'- Held-out v2 decisions never alter the signed v2 gold: any disagreement is listed here only: ' + (', '.join(f'{r.case_id} {r.decision}' for r in export.results if r.stream == 'v2' and r.decision != 'approve') or 'none') + '.', '',
              '## Agreement with the AI suggestion (owner_manual decisions only)', '', '| Stream | Own decisions with an AI suggestion | Same as the AI |', '|---|---:|---:|']
    for s in ('gold', 'v2', 'answers', 'sources'):
        a, b = agreement[s]
        lines.append(f'| {STREAM_LABEL[s]} | {b} | {a}' + (f' ({a / b:.0%})' if b else '') + ' |')
    lines += ['', 'This is agreement, not accuracy. Small counts: read the numbers, not the percentages.', '',
              '## Exact wording for the report', ''] + [f'> {w}' for w in wording_lines] + ['',
              '## Rescoring on gold v3.7 (separate offline step, no model calls)', '',
              'The saved evaluations stay scored on v3.5/v3.6 and keep their hashes. ' + ('Gold v3.7 has the same questions, labels, facts and evidence as v3.6 and differs only in review provenance fields, so a rescoring changes no behaviour or score; it only records the all-reviewed status against the v3.7 hash. ' if not report['changed'] and not report['dropped'] else 'To measure the effect of the v3.7 changes, ') + 'If you rescore, do it from the saved runs without the judge, one experiment at a time, '
              'for example (this rewrites `experiments/eval/<exp>/`, so run it on a copy or a scratch checkout, never over a frozen result):', '',
              '```', f'uv run labourlens eval --exp agent-dev-A1 --split dev --gold {GOLD_V37} --allow-gold-mismatch --no-judge', '```', '',
              'Report the result as a post-hoc sensitivity analysis next to, never instead of, the original scores.', '']
    return '\n'.join(lines), wording_lines


def pending_ingest(review_export: Path, write: bool = False, root: Path = ROOT, main_export: Path | None = None, policy_file: Path | None = None) -> tuple[int, str]:
    root = Path(root).resolve()
    try:
        st = State(root, main_export)
        export, export_sha, cards = load_pending_export(review_export, root, st)
        policy = load_policy(policy_file, root) if policy_file else None
        new_cases, log, report = apply_to_gold(st, export, export_sha, policy)
    except (ValueError, OSError) as exc:
        return 2, f'Review export rejected: {exc}'
    infos = ai_infos(root, st)
    left = remaining(cards, export)
    blocking = {q: ids for q, ids in left.items() if q != 'redo'}
    final = final_provenance(st, export)
    gold_final = Counter(final['gold'].get(c['case_id']) or 'none' for c in st.gold if c['case_id'] not in report['dropped'])
    counts = {'manual': gold_final[MANUAL], 'agreed': gold_final[AGREED], 'none': gold_final['none']}
    body = ''.join(json.dumps(c, ensure_ascii=False) + '\n' for c in new_cases)
    new_sha = hashlib.sha256(body.encode()).hexdigest()
    summary, wording_lines = final_summary(root, st, export, export_sha, cards, report, new_sha if write else None, infos, write)
    head = ['PENDING REVIEW INGEST ' + ('(WRITTEN)' if write else '(DRY RUN: nothing written)'), '',
            f'Reviewer: {export.reviewer_name}   Export: {export_sha[:16]}…', '',
            f'{len(export.results)} cards decided: {sum(r.decision_source == MANUAL for r in export.results)} by your own click, {sum(r.decision_source == AGREED for r in export.results)} by agreeing with an AI suggestion.']
    for q in ('proposal', 'pending', 'redo'):
        head.append(f'  - {QUEUE_LABEL[q]}: {len(left.get(q, []))} undecided' + (' (optional)' if q == 'redo' else ''))
    head += ['', f'Gold v3.7 would have {len(new_cases)} cases; label changes applied: {", ".join(f"{i} {a}->{b}" for i, a, b in report["changed"]) or "none"}; removed: {", ".join(report["dropped"]) or "none"}.']
    if report['not_applied']:
        pol = report['policy']
        head.append(f'Owner clicks NOT applied because of policy {pol["ref"]} ({pol["text"]}): ' + ', '.join(f'{i} ({a} -> {b})' for i, a, b in report['not_applied']) + '. Labels stay as in v3.6; the clicks are kept in the review log.')
    if blocking:
        head += ['', 'CANNOT WRITE YET: these required cards are undecided:']
        for q, ids in blocking.items():
            head.append(f'  - {QUEUE_LABEL[q]}: {", ".join(ids[:12])}{" …" if len(ids) > 12 else ""} ({len(ids)})')
        return 1, '\n'.join(head)
    head += ['', 'Wording the report may use once you write this:'] + [f'  “{w}”' for w in wording_lines]
    if not write:
        return 0, '\n'.join(head + ['', 'Run the same command again with --write to create gold_v3.7, the changelog entry and the final summary.'])
    out = root / GOLD_V37
    if out.exists() and out.read_text() != body:
        return 2, '\n'.join(head + ['', f'{GOLD_V37} already exists with different content; it is never overwritten.'])
    log_body = ''.join(json.dumps(e, ensure_ascii=False) + '\n' for e in log)
    out.write_text(body)
    (root / GOLD_V37_LOG).write_text(log_body)
    changelog = root / CHANGELOG
    old = changelog.read_text() if changelog.exists() else '# Gold set change log\n\n'
    title, _, rest = old.partition('\n\n')
    if f'## v3.7: owner review' not in old:
        changelog.write_text(title + '\n\n' + changelog_entry(export, export_sha, report, new_sha, counts) + rest)
    j10_results = {r.case_id: r.decision for r in export.results if r.stream == 'j10'}
    (root / FINAL_PROVENANCE).write_text(json.dumps({'export_sha256': export_sha, 'gold_v3_7_sha256': new_sha, 'reviewer': export.reviewer_name, 'streams': final, 'j10': j10_results}, indent=1, sort_keys=True) + '\n')
    summary_path = root / FINAL_SUMMARY
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(summary)
    return 0, '\n'.join(head + ['', f'Wrote {GOLD_V37} (SHA-256 {new_sha}), {GOLD_V37_LOG}, a changelog entry, {FINAL_PROVENANCE} and {FINAL_SUMMARY}.'])
