"""Pending-review inventory, page, strict ingest and gold v3.7 isolation, built only from synthetic fixtures."""
import hashlib
import json
import subprocess
from pathlib import Path

import pandas as pd
import pymupdf
import pytest
from bs4 import BeautifulSoup

from labourlens.review import pending as P
from labourlens.review import pending_page as PP


def put(root, name, text):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def passage(n):
    text = f'Synthetic wording only {n}.'
    return dict(passage_id=f'rep:p001:b{n:03}', source_id='rep', snapshot_id='s1', document_title='Synthetic report', page_number=1, printed_page_label='1',
                section_heading='h', original_url='https://example.invalid/doc', text=text, text_sha256=hashlib.sha256(text.encode()).hexdigest(),
                release_stage='final', bbox=[40, 40, 300, 80], publication_date='2026-08-11')


def case(cid, behaviour='answer', split='dev', reviewed=None):
    c = dict(case_id=cid, split=split, family='factual_lookup', question=f'Synthetic question {cid}?', expected_behavior=behaviour,
             evidence_text=[dict(source_id='rep', passage_ids=['rep:p001:b001'], locator='p.1', primary=True, why='Direct source evidence')] if behaviour == 'answer' else [],
             evidence_data=[], reference_facts=[f'Synthetic fact {cid}.'] if behaviour == 'answer' else [], calculation=None,
             abstain_reason=None if behaviour == 'answer' else 'Synthetic reason.', adversarial=None, difficulty_note='', drafted_by='ai:test', reviewed_by=None,
             review_status='draft', notes='', ai_review='x', ai_review_2='y')
    if reviewed:
        c.update(reviewed_by='Synth', review_status='owner_reviewed', owner_review={'reviewer': 'Synth', 'decision_source': reviewed, 'date': '2026-10-31'})
    return c


def ai_record(cid, verdict, kind='a'):
    base = dict(case_id=cid, verdict=verdict, confidence=0.9, issues=[] if verdict in ('ok', 'agree') else ['Synthetic concern about evidence wording.'], reviewer=f'synthetic {kind}')
    base['proposed_changes'] = {} if verdict == 'ok' else {'evidence_text': 'add alternative'}
    return base


def main_export(entries):
    results = []
    for tab, cid, fields, source in entries:
        item = dict(case_id=cid, tab=tab, fields=fields, timestamp='2026-10-31T01:00:00Z')
        if source:
            item['decision_source'] = source
        results.append(item)
    return dict(schema_version=1, pack_id='synthetic', reviewer_name='Synth', exported_at='2026-10-31T03:00:00Z', results=results, checklist={})


@pytest.fixture
def root(tmp_path):
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    put(tmp_path, '.gitignore', 'private/\n')
    with pymupdf.open() as doc:
        doc.new_page().insert_text((50, 60), 'Synthetic PDF page')
        (tmp_path / 'data/raw/rep/s1').mkdir(parents=True)
        doc.save(tmp_path / 'data/raw/rep/s1/rep.pdf')
    put(tmp_path, 'data/manifests/manifest.json', json.dumps({'entries': [dict(source_id='rep', snapshot_id='s1', title='Synthetic report', raw_path='data/raw/rep/s1/rep.pdf')]}))
    put(tmp_path, 'data/passages/rep.jsonl', '\n'.join(json.dumps(passage(n)) for n in range(1, 4)))
    (tmp_path / 'data/processed').mkdir(parents=True)
    pd.DataFrame([dict(observation_id='obs1', source_id='dsx', snapshot_id='s1', source_locator='csv_row=2;col=value', indicator_id='x', dimension='', period='2026-Q2', value=2.9,
                       unit='percent', release_stage='final', population='p', adjustment='a')]).to_parquet(tmp_path / 'data/processed/observations.parquet')
    cases = [case(f'DEV-{n:03}') for n in range(1, 9)] + [case('DEV-009', 'abstain'), case('DEV-010', 'clarify')]
    cases += [case('HO-001', split='heldout', reviewed='agreed_with_ai_suggestion'), case('HO-002', split='heldout', reviewed='owner_manual'), case('HO-003', split='heldout', reviewed='agreed_with_ai_suggestion')]
    put(tmp_path, P.GOLD_DRAFT, ''.join(json.dumps(c) + '\n' for c in cases))
    # AI coverage: DEV-001 two ok reviewers (agreeable), DEV-002 a label dispute, DEV-003 a concern, DEV-004 one ok reviewer, DEV-005..010 uncovered except 006 (single ok).
    a = [ai_record('DEV-001', 'ok'), ai_record('DEV-002', 'drop'), ai_record('DEV-003', 'fix'), ai_record('DEV-004', 'ok'), ai_record('DEV-006', 'ok')]
    b = [ai_record('DEV-001', 'ok', 'b'), ai_record('DEV-007', 'ok', 'b')]
    put(tmp_path, 'experiments/gold/ai-review/a.jsonl', ''.join(json.dumps(r) + '\n' for r in a))
    put(tmp_path, 'experiments/gold/ai-review/b.jsonl', ''.join(json.dumps(r) + '\n' for r in b))
    ok = dict(label='OK', evidence='OK', facts='OK')
    export = main_export([('gold', 'HO-001', ok, 'agreed_with_ai_suggestion'), ('gold', 'HO-002', dict(label='disagree', proposed_behavior='abstain'), 'owner_manual'),
                          ('gold', 'HO-003', ok, 'agreed_with_ai_suggestion'), ('decisions', 'J10', dict(decision='inspect_more'), 'owner_manual'),
                          ('decisions', 'J1', dict(decision='verified'), 'owner_manual')])
    put(tmp_path, P.MAIN_EXPORT_PRIVATE, json.dumps(export))
    put(tmp_path, P.CHANGELOG, '# Gold set change log\n\n## v3.6 earlier entry\n\ntext\n')
    return tmp_path


def required_results(root, overrides=None, include_redo=()):
    st = P.State(root)
    cards = P.plan(root, st)
    overrides = overrides or {}
    results = []
    for card in cards:
        if card['queue'] == 'redo' and card['key'] not in include_redo:
            continue
        opts = PP.options_for(card)
        item = dict(key=card['key'], stream=card['stream'], queue=card['queue'], case_id=card['case_id'], decision=opts[0]['v'], proposed_behavior='', reason='', comment='',
                    decision_source='owner_manual', ai_basis={}, timestamp='2026-11-01T00:00:00Z')
        item.update(overrides.get(card['key'], {}))
        results.append(item)
    return st, cards, dict(schema_version=1, kind='pending_review', pack_id=P.pack_id(root, st), reviewer_name='Synthetic Owner', exported_at='2026-11-01T01:00:00Z',
                           main_export_sha256=st.main_sha, ai_files_sha256=P.ai_file_hashes(root), results=results)


def write_export(root, data, name='pending.json'):
    return put(root, f'private/{name}', json.dumps(data))


def test_plan_separates_pending_redo_and_orders_by_risk(root):
    st = P.State(root)
    cards = P.plan(root, st)
    by = {(c['stream'], c['queue']): [x['case_id'] for x in cards if (x['stream'], x['queue']) == (c['stream'], c['queue'])] for c in cards}
    assert sorted(by[('gold', 'pending')]) == [f'DEV-{n:03}' for n in range(1, 11)]
    assert sorted(by[('gold', 'redo')]) == ['HO-001', 'HO-003'] and ('gold', 'proposal') not in by
    assert [c['key'] for c in cards if c['stream'] == 'j10'][-1] == 'j10:J10'
    pending_gold = [c for c in cards if (c['stream'], c['queue']) == ('gold', 'pending')]
    assert pending_gold[0]['case_id'] == 'DEV-002' and pending_gold[0]['risk'] == 0  # an AI label dispute comes first
    assert [c['risk'] for c in pending_gold] == sorted(c['risk'] for c in pending_gold)
    info = {c['case_id']: c['ai'] for c in pending_gold}
    assert info['DEV-001']['status'] == 'agree' and info['DEV-002']['status'] == 'disagree' and info['DEV-003']['status'] == 'disagree'
    assert info['DEV-005']['status'] == 'none' and 'none was run' in info['DEV-005']['text'] or 'no AI was run' in info['DEV-005']['text']


def test_inventory_counts_come_from_files(root):
    st = P.State(root)
    inv = P.inventory(root, st)
    rows = {r['name']: r for r in inv['rows']}
    held = rows['Gold: original held-out cases (HO-001…031)']
    assert (held['population'], held['manual'], held['agreed']) == (3, 1, 2)
    rest = rows['Gold: remaining dev cases']
    assert (rest['population'], rest['manual'], rest['agreed'], rest['ai_only'], rest['untouched']) == (10, 0, 0, 6, 4)
    assert inv['pending']['gold dev, never decided by the owner'][:2] == ['DEV-001', 'DEV-002']
    assert 'J10 extraction gaps (owner asked for more inspection)' in inv['pending']
    text = P.inventory_markdown(root, st)
    assert 'Do not write “all labelling was manually reviewed by the owner”' in text and 'AI-only streams' in text and st.main_sha in text


def test_page_has_no_agree_control_and_shows_ai_below_each_card(root):
    path = PP.build_pending_page(root)
    page = path.read_text()
    soup = BeautifulSoup(page, 'html.parser')
    cards = soup.select('article.card')
    assert len(cards) == len(P.plan(root, P.State(root)))
    assert not soup.select('[data-agree], .agree, #manual-only, #clear-agreed')
    assert 'Agree with AI</button>' not in page and "k === 'g'" not in page and 'function agree' not in page
    gold = soup.select_one('article[data-key="gold:DEV-002"]')
    strip = gold.select_one('.aistrip')
    assert 'AI suggestion (for reference, decide yourself)' in strip.get_text()
    assert strip.parent is gold and gold.select_one('.split') in strip.find_previous_siblings()  # below the evidence and the label
    assert 'start' in page and 'no “Agree with AI” button' in soup.select_one('#start').get_text()
    assert not __import__('re').search(r'src="https?://', page)
    assert 'labourlens-pending:' in page and 'labourlens-heldout-v2:' not in page and "decision_source: 'owner_manual'" in page
    assert 'data-page=' in page and 'loading="lazy"' in page


def test_valid_manual_export_dry_run_then_write_isolated(root):
    draft = (root / P.GOLD_DRAFT).read_bytes()
    st, cards, data = required_results(root, {'gold:DEV-002': dict(decision='change', proposed_behavior='abstain', reason='The figure is not published.'),
                                              'gold:DEV-003': dict(decision='reject', reason='Unclear question.')})
    path = write_export(root, data)
    code, text = P.pending_ingest(path, write=False, root=root)
    assert code == 0, text
    assert 'DRY RUN' in text and 'DEV-002 answer->abstain' in text and 'removed: DEV-003' in text and 'by your own click' in text
    assert not (root / P.GOLD_V37).exists() and (root / P.GOLD_DRAFT).read_bytes() == draft and not (root / P.FINAL_SUMMARY).exists()
    code, text = P.pending_ingest(path, write=True, root=root)
    assert code == 0, text
    new = {json.loads(l)['case_id']: json.loads(l) for l in (root / P.GOLD_V37).read_text().splitlines()}
    assert (root / P.GOLD_DRAFT).read_bytes() == draft  # the pinned file is never touched
    assert 'DEV-003' not in new and new['DEV-002']['expected_behavior'] == 'abstain' and new['DEV-002']['evidence_text'] == []
    assert new['DEV-001']['owner_review'] == {'reviewer': 'Synthetic Owner', 'decision_source': 'owner_manual', 'date': '2026-11-01'}
    assert new['HO-001']['owner_review']['decision_source'] == 'agreed_with_ai_suggestion'  # never silently converted to manual
    assert new['HO-002']['owner_review']['decision_source'] == 'owner_manual'
    changelog = (root / P.CHANGELOG).read_text()
    assert changelog.startswith('# Gold set change log') and changelog.index('## v3.7') < changelog.index('## v3.6') and 'post-hoc' in changelog
    summary = (root / P.FINAL_SUMMARY).read_text()
    assert 'not independent inter-rater evidence' in summary and '--no-judge' in summary and 'gold_v3.7.jsonl' in summary and 'DEV-002 answer -> abstain' in summary
    log = [json.loads(l) for l in (root / P.GOLD_V37_LOG).read_text().splitlines()]
    assert {e['case_id'] for e in log} >= {'DEV-002', 'DEV-003'} and all(e['reviewer'] == 'Synthetic Owner' for e in log)
    # a second write is idempotent and never duplicates the changelog entry
    code, _ = P.pending_ingest(path, write=True, root=root)
    assert code == 0 and (root / P.CHANGELOG).read_text().count('## v3.7') == 1


def test_existing_v37_with_different_content_is_never_overwritten(root):
    put(root, P.GOLD_V37, 'something else\n')
    st, cards, data = required_results(root)
    code, text = P.pending_ingest(write_export(root, data), write=True, root=root)
    assert code == 2 and 'never overwritten' in text and (root / P.GOLD_V37).read_text() == 'something else\n'


def test_partial_export_validates_but_cannot_write(root):
    st, cards, data = required_results(root)
    data['results'] = data['results'][:4]
    path = write_export(root, data)
    code, text = P.pending_ingest(path, write=False, root=root)
    assert code == 1 and 'CANNOT WRITE YET' in text and 'never decided by you' in text
    code, text = P.pending_ingest(path, write=True, root=root)
    assert code == 1 and not (root / P.GOLD_V37).exists()


@pytest.mark.parametrize('mutate,message', [
    (lambda d: d.update(surprise=1), ''),
    (lambda d: d['results'][0].update(reviewed_by='Synthetic Owner'), ''),
    (lambda d: d.update(pack_id='deadbeefdeadbeef'), 'different version'),
    (lambda d: d.update(main_export_sha256='0' * 64), 'differs from the one'),
    (lambda d: d.update(ai_files_sha256={'x': '0' * 64}), 'SHA-256 mismatch'),
    (lambda d: d['results'][0].update(decision='maybe'), 'invalid decision'),
    (lambda d: d['results'][0].update(decision_source=''), 'decision_source'),
    (lambda d: d['results'][0].update(key='gold:DEV-999', case_id='DEV-999'), 'not a card'),
    (lambda d: d['results'][0].update(ai_basis={'basis': 'x'}), 'carries no ai_basis'),
    (lambda d: d['results'].append(dict(d['results'][0])), 'Duplicate'),
    (lambda d: d['results'][0].update(decision='change', proposed_behavior='answer', reason='r'), 'already has'),
    (lambda d: d['results'][0].update(decision='change', proposed_behavior='abstain', reason=''), 'needs a reason'),
    (lambda d: d['results'][0].update(timestamp='yesterday'), ''),
])
def test_tampered_exports_are_rejected(root, mutate, message):
    st, cards, data = required_results(root)
    first = next(r for r in data['results'] if r['stream'] == 'gold')
    data['results'].remove(first)
    data['results'].insert(0, first)
    mutate(data)
    code, text = P.pending_ingest(write_export(root, data), write=True, root=root)
    assert code == 2 and text.startswith('Review export rejected') and message in text
    assert not (root / P.GOLD_V37).exists()


def test_agreed_decisions_are_verified_and_reported_separately(root):
    st = P.State(root)
    card = next(c for c in P.plan(root, st) if c['key'] == 'gold:DEV-001')
    assert card['ai']['status'] == 'agree'
    good = dict(decision='approve', decision_source='agreed_with_ai_suggestion', ai_basis=card['ai']['ai_basis'])
    _, _, data = required_results(root, {'gold:DEV-001': good})
    code, text = P.pending_ingest(write_export(root, data), write=True, root=root)
    assert code == 0 and '1 by agreeing with an AI suggestion' in text
    new = {json.loads(l)['case_id']: json.loads(l) for l in (root / P.GOLD_V37).read_text().splitlines()}
    assert new['DEV-001']['owner_review']['decision_source'] == 'agreed_with_ai_suggestion'
    # tampered basis, a different decision than the suggestion, and agreeing where the AI disagreed all fail
    bad_basis = dict(good, ai_basis={**good['ai_basis'], 'decision': 'reject'})
    for overrides, message in (({'gold:DEV-001': bad_basis}, 'ai_basis does not match'),
                               ({'gold:DEV-001': dict(good, decision='reject', reason='r')}, 'does not match the AI suggestion'),
                               ({'gold:DEV-002': dict(decision='approve', decision_source='agreed_with_ai_suggestion', ai_basis=good['ai_basis'])}, 'no one-click suggestion')):
        (root / P.GOLD_V37).unlink(missing_ok=True)
        _, _, data = required_results(root, overrides)
        code, text = P.pending_ingest(write_export(root, data, 'bad.json'), write=False, root=root)
        assert code == 2 and message in text, text


def test_final_provenance_keeps_agreed_unless_redone_manually_and_stats_use_manual_only(root):
    st, cards, data = required_results(root, include_redo=('gold:HO-001',))
    export = P.PendingExport.model_validate(data)
    final = P.final_provenance(st, export)
    assert final['gold']['HO-001'] == 'owner_manual' and final['gold']['HO-003'] == 'agreed_with_ai_suggestion' and final['gold']['HO-002'] == 'owner_manual'
    infos = P.ai_infos(root, st)
    stats = P.manual_vs_ai(st, export, infos)
    # DEV-001 (own approve, AI agrees) counts; DEV-004 single-reviewer approve counts; agreed cards never count
    assert stats['gold'][1] >= 2 and stats['gold'][0] <= stats['gold'][1]
    text, wording = P.final_summary(root, st, export, 'a' * 64, cards, {'changed': [], 'dropped': []}, None, infos, False)
    assert 'agreed with AI' in text and 'excluded from every agreement statistic' in text
    assert any('agreeing with an AI suggestion' in w for w in wording)
    assert P.wording({'gold': {'owner_manual': 5}})[0].startswith('All 5 labelling items')


def test_summary_and_inventory_do_not_quote_passages(root):
    st, cards, data = required_results(root)
    code, _ = P.pending_ingest(write_export(root, data), write=True, root=root)
    assert code == 0
    for rel in (P.FINAL_SUMMARY,):
        assert 'Synthetic wording only' not in (root / rel).read_text()
    out = P.write_inventory(root)
    assert out == root / P.INVENTORY and 'Synthetic wording only' not in out.read_text()


# ------------------------------------------------------------------ fresh blind reviews (AI opinion only)

def write_fresh(root, spec):
    """spec: {reviewer: [(case, verdict, behaviour, flags)]}"""
    for reviewer, items in spec.items():
        lines = []
        for cid, verdict, behaviour, flags in items:
            rec = dict(case_id=cid, verdict=verdict, confidence='high', flags=flags, reason='Synthetic fresh reason.')
            if behaviour:
                rec['suggested_behavior'] = behaviour
            lines.append(json.dumps(rec))
        put(root, f'{P.FRESH_DIR}/{reviewer}.jsonl', '\n'.join(lines) + '\n')


FRESH = {
    'PendA1': [('DEV-001', 'approve', None, []), ('DEV-005', 'change_label', 'abstain', ['evidence_missing']), ('DEV-004', 'approve', None, ['ambiguous_question']), ('DEV-008', 'approve', None, ['other'])],
    'PendB1': [('DEV-001', 'approve', None, ['other']), ('DEV-005', 'change_label', 'abstain', ['evidence_missing']), ('DEV-004', 'approve', None, []), ('DEV-008', 'change_label', 'answer', [])],
}


def test_fresh_reviews_are_added_to_the_ai_block_and_sort_first(root):
    before = P.pack_id(root, P.State(root))
    write_fresh(root, FRESH)
    st = P.State(root)
    assert P.pack_id(root, st) != before  # the new files are hashed into the pack identity
    cards = P.plan(root, st)
    pending = [c for c in cards if (c['stream'], c['queue']) == ('gold', 'pending')]
    first = [c['case_id'] for c in pending[:4]]
    assert first[:3] == ['DEV-005', 'DEV-008', 'DEV-004']  # label changes first, then flagged cards
    assert [c['risk'] for c in pending[:3]] == [-2, -2, -1]
    info = {c['case_id']: c['ai'] for c in pending}
    assert 'both change to abstain' in info['DEV-005']['text'] and 'Look at this card first' in info['DEV-005']['text']
    assert info['DEV-005']['fresh']['change'] and info['DEV-005']['fresh']['flags'] == ['evidence_missing']
    assert 'split (approve / change to answer)' in info['DEV-008']['text'] and info['DEV-008']['fresh']['change']
    assert info['DEV-004']['fresh']['net'] == 'both approve' and info['DEV-004']['fresh']['flags'] == ['ambiguous_question'] and info['DEV-004']['risk'] == -1
    assert info['DEV-001']['status'] == 'agree' and 'both approve' in info['DEV-001']['text'] and info['DEV-001']['risk'] >= 2  # an 'other' flag alone does not escalate
    assert any(o['reviewer'].startswith('Fresh blind review 2026-11-01') for o in info['DEV-001']['opinions'])
    soup = BeautifulSoup(PP.build_pending_page(root).read_text(), 'html.parser')
    strip = soup.select_one('article[data-key="gold:DEV-005"] .aistrip').get_text()
    assert 'Fresh blind review 2026-11-01 (two reviewers): both change to abstain' in strip and 'fresh AI reviewer says change the label' in soup.select_one('article[data-key="gold:DEV-005"]').get_text()
    keys = [c['data-key'] for c in soup.select('article.card')]
    assert keys.index('gold:DEV-005') < keys.index('gold:DEV-001') and not soup.select('[data-agree]')


def test_fresh_files_are_validated_strictly(root):
    put(root, f'{P.FRESH_DIR}/PendA1.jsonl', json.dumps(dict(case_id='DEV-001', verdict='change_label', confidence='high', flags=[], reason='x')) + '\n')
    with pytest.raises(ValueError, match='suggested_behavior'):
        P.load_fresh(root)
    put(root, f'{P.FRESH_DIR}/PendA1.jsonl', json.dumps(dict(case_id='DEV-001', verdict='approve', confidence='high', flags=[], reason='x', surprise=1)) + '\n')
    with pytest.raises(ValueError, match='unexpected fields'):
        P.load_fresh(root)


def test_final_summary_lists_fresh_reviews_as_ai_opinion_only(root):
    write_fresh(root, FRESH)
    st, cards, data = required_results(root)
    code, _ = P.pending_ingest(write_export(root, data), write=True, root=root)
    assert code == 0
    text = (root / P.FINAL_SUMMARY).read_text()
    assert 'Fresh blind AI review of the development cases (Fresh blind review 2026-11-01): AI opinion only' in text
    assert '| DEV-005 | both change to abstain | evidence_missing | approve | owner_manual |' in text and '| DEV-001 |' not in text.split('Fresh blind AI review')[1].split('## Gold changes')[0]
    assert 'never human review' in text
    # an export built before the fresh files existed is rejected (different pack identity)


# ------------------------------------------------------------------ owner policy that stops recorded changes from being applied

def write_policy(root, cases, name='policy.json'):
    data = dict(policy_ref='D-047', decided='2026-11-01', text='owner policy 2026-11-01: out-of-period figures needed, abstain retained',
                non_applied_changes=[dict(case_id=c, proposed_behavior=b) for c, b in cases])
    return put(root, name, json.dumps(data))


def test_policy_keeps_labels_and_records_the_click_unapplied(root):
    draft = (root / P.GOLD_DRAFT).read_bytes()
    _, _, data = required_results(root, {'gold:DEV-002': dict(decision='change', proposed_behavior='abstain', reason='Not published.'),
                                         'gold:DEV-005': dict(decision='change', proposed_behavior='clarify', reason='Needs a period.')})
    path = write_export(root, data)
    policy = write_policy(root, [('DEV-002', 'abstain')])
    code, text = P.pending_ingest(path, write=False, root=root, policy_file=policy)
    assert code == 2 and 'do not match the export' in text and "['DEV-005']" in text  # DEV-005 would be silently applied
    policy = write_policy(root, [('DEV-002', 'abstain'), ('DEV-005', 'clarify')])
    code, text = P.pending_ingest(path, write=False, root=root, policy_file=policy)
    assert code == 0, text
    assert 'label changes applied: none' in text and 'NOT applied because of policy D-047' in text and 'DEV-002 (answer -> abstain)' in text
    assert not (root / P.GOLD_V37).exists()
    code, text = P.pending_ingest(path, write=True, root=root, policy_file=policy)
    assert code == 0, text
    new = {json.loads(l)['case_id']: json.loads(l) for l in (root / P.GOLD_V37).read_text().splitlines()}
    old = {json.loads(l)['case_id']: json.loads(l) for l in draft.decode().splitlines()}
    assert new['DEV-002']['expected_behavior'] == old['DEV-002']['expected_behavior'] == 'answer'  # label unchanged
    assert new['DEV-002']['evidence_text'] == old['DEV-002']['evidence_text']
    assert new['DEV-002']['owner_review'] == {'reviewer': 'Synthetic Owner', 'decision_source': 'owner_manual', 'date': '2026-11-01'}
    log = {e['case_id']: e for e in map(json.loads, (root / P.GOLD_V37_LOG).read_text().splitlines())}
    assert log['DEV-002']['decision'] == 'change' and log['DEV-002']['decision_source'] == 'owner_manual' and log['DEV-002']['applied'] is False and log['DEV-002']['policy_ref'] == 'D-047'
    assert log['DEV-001']['applied'] is True
    assert 'Policy (D-047, 2026-11-01)' in (root / P.CHANGELOG).read_text()
    summary = (root / P.FINAL_SUMMARY).read_text()
    assert 'Owner clicks not applied because of a later policy decision' in summary and '| DEV-002 | answer | change to abstain | no (D-047) |' in summary
    assert (root / P.GOLD_DRAFT).read_bytes() == draft


@pytest.mark.parametrize('listed', [[], [('DEV-002', 'clarify')], [('DEV-002', 'abstain'), ('DEV-003', 'abstain')]])
def test_policy_set_must_match_the_recorded_changes_exactly(root, listed):
    _, _, data = required_results(root, {'gold:DEV-002': dict(decision='change', proposed_behavior='abstain', reason='Not published.')})
    code, text = P.pending_ingest(write_export(root, data), write=True, root=root, policy_file=write_policy(root, listed))
    assert code == 2 and 'do not match the export' in text and not (root / P.GOLD_V37).exists()


def test_policy_file_is_validated_strictly(root):
    _, _, data = required_results(root)
    path = write_export(root, data)
    put(root, 'bad.json', json.dumps(dict(policy_ref='D', decided='2026-11-01', text='x', non_applied_changes=[], surprise=1)))
    code, text = P.pending_ingest(path, root=root, policy_file=root / 'bad.json')
    assert code == 2 and 'expected exactly' in text


def test_j10_acceptance_is_recorded_in_the_summary(root):
    _, _, data = required_results(root, {'j10:J10': dict(decision='accept_limits')})
    code, _ = P.pending_ingest(write_export(root, data), write=True, root=root)
    assert code == 0
    text = (root / P.FINAL_SUMMARY).read_text()
    assert '## J10 (human acceptance of the frozen extraction gaps)' in text and '`accept_limits` (own click)' in text and 'not a claim that the defects were fixed' in text
