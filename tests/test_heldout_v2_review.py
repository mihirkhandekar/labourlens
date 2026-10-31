"""Held-out v2 review page, strict approval and run wrapper, built only from synthetic fixtures."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

import pandas as pd
import pymupdf
import pytest
from bs4 import BeautifulSoup

from labourlens.review import heldout_v2 as hv2

NON_ANSWER = {**{i: 'abstain' for i in range(52, 60)}, **{i: 'clarify' for i in range(60, 64)},
              **{i: 'refuse' for i in (64, 65, 44, 45, 46)}, **{i: 'ignore_injection_and_answer' for i in (47, 48, 49, 50)}}
MTI_ANSWER = (20, 21, 22)


def put(root, name, text):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def passage(source, n, text='Synthetic wording only.'):
    return dict(passage_id=f'{source}:p001:b{n:03}', source_id=source, snapshot_id='s1', document_title=f'Synthetic {source}', page_number=1, printed_page_label='1',
                section_heading='h', original_url='https://example.invalid/doc', text=text, text_sha256=hashlib.sha256(f'{source}{n}{text}'.encode()).hexdigest(),
                release_stage='final', bbox=[40, 40, 300, 80], publication_date='2026-08-11')


def make_cases():
    answers = [i for i in range(1, 66) if i not in NON_ANSWER]
    unique = [i for i in answers if i != 22][:22]  # 22 independent evidence groups; case 22 shares case 4's passage
    ids = {i: (f'rep:p001:b{i:03}' if i in unique else 'rep:p001:b004' if i == 22 else 'rep:p001:b001') for i in answers + [47, 48, 49, 50]}
    cases = []
    for i in range(1, 66):
        behaviour = NON_ANSWER.get(i, 'answer')
        group = 'mti_ai_feature' if i in (20, 21, 22, 52, 53) else 'ai_vs_dataset' if i == 43 else 'wage'
        case = dict(case_id=f'HO-V2-{i:03}', split='heldout', family='factual_lookup' if behaviour == 'answer' else 'ambiguity_insufficient_causal',
                    question=f'Synthetic question {i}?', expected_behavior=behaviour, evidence_text=[], evidence_data=[], reference_facts=[], calculation=None,
                    abstain_reason=None, adversarial=None, difficulty_note='', drafted_by='ai:test', reviewed_by=None, review_status='draft', source_group=group, notes='')
        if behaviour in ('answer', 'ignore_injection_and_answer'):
            pid = ids.get(i, 'rep:p001:b001')
            case['evidence_text'] = [dict(source_id='rep', passage_ids=[pid], locator='p.1', primary=True, why='Direct source evidence')]
            case['reference_facts'] = [f'Synthetic fact {i}.']
        else:
            case['abstain_reason'] = 'Synthetic reason.'
        if i == 1:
            case['evidence_data'] = [dict(source_id='dsx', period='2026-Q2', dimension='', observation_ids=['obs1'])]
        cases.append(case)
    return cases


@pytest.fixture
def root(tmp_path):
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    put(tmp_path, '.gitignore', 'private/\n')
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_text((50, 60), 'Synthetic PDF page')
        (tmp_path / 'data/raw/rep/s1').mkdir(parents=True)
        doc.save(tmp_path / 'data/raw/rep/s1/rep.pdf')
    put(tmp_path, 'data/snapshots/dsx/s1/raw.csv', 'quarter,value\n2026-Q2,2.9\n')
    entries = [dict(source_id='rep', snapshot_id='s1', title='Synthetic report', raw_path='data/raw/rep/s1/rep.pdf'),
               dict(source_id='mti-feature-ai-x', snapshot_id='s1', title='Synthetic AI article', raw_path='data/raw/rep/s1/rep.pdf'),
               dict(source_id='dsx', snapshot_id='s1', title='Synthetic dataset', raw_path='data/snapshots/dsx/s1/raw.csv', canonical_url='https://example.invalid/data')]
    put(tmp_path, 'data/manifests/manifest.json', json.dumps({'entries': entries}))
    passages = [passage('rep', n) for n in range(1, 66)]
    passages.append(passage('mti-feature-ai-x', 1, 'Synthetic: postings data from 2018 to 2024 are summarised here.'))
    passages.append(passage('mti-feature-ai-x', 2, 'Synthetic note: firms’ AI use up to 2024 stay preliminary.'))
    put(tmp_path, 'data/passages/rep.jsonl', '\n'.join(json.dumps(p) for p in passages))
    (tmp_path / 'data/processed').mkdir(parents=True)
    pd.DataFrame([dict(observation_id='obs1', source_id='dsx', snapshot_id='s1', source_locator='csv_row=2;col=value', indicator_id='x', dimension='', period='2026-Q2',
                       value=2.9, unit='percent', release_stage='final', population='p', adjustment='a')]).to_parquet(tmp_path / 'data/processed/observations.parquet')
    cases = make_cases()
    put(tmp_path, hv2.DRAFT, '\n'.join(json.dumps(c) for c in cases) + '\n')
    for name in ('planner_v1', 'planner_v1_user', 'answer_v3', 'answer_v3_user', 'rerank_v1', 'judge_v1'):
        put(tmp_path, f'prompts/{name}.md', f'prompt {name}')
    put(tmp_path, 'specs/prices.yaml', 'prices: {}\n')
    write_freeze(tmp_path)
    return tmp_path


def write_freeze(root, drop=None):
    hashes = hv2.frozen_hashes(root)
    if drop:
        hashes.pop(drop)
    put(root, hv2.FREEZE, '# Synthetic freeze draft\n\n' + '\n'.join(f'- `{k}` `{v}`' for k, v in hashes.items()) + '\n')


def export_for(root, decisions=None, name='Synthetic Owner'):
    draft = root / hv2.DRAFT
    sha = hv2.sha256_file(draft)
    decisions = decisions or {}
    results = []
    for case in hv2.rows(draft):
        base = dict(case_id=case['case_id'], decision='approve', proposed_behavior='', reason='', comment='', mti_choice='', decision_source='owner_manual', timestamp='2026-10-31T00:00:00Z')
        base.update(decisions.get(case['case_id'], {}))
        results.append(base)
    return dict(schema_version=1, kind='heldout_v2_review', pack_id=hv2.pack_id_for(sha), gold_sha256=sha, reviewer_name=name, exported_at='2026-10-31T01:00:00Z', results=results)


def write_export(root, data, name='export.json'):
    return put(root, f'private/{name}', json.dumps(data))


RELABEL = {f'HO-V2-0{n}': dict(decision='change', proposed_behavior='abstain', reason=hv2.MTI_REASONS['relabel_abstain'], mti_choice='relabel_abstain') for n in (20, 21, 22)}


def test_page_is_small_lazy_and_separate_from_the_main_pack(root):
    path = hv2.build_v2_page(root)
    page = path.read_text()
    soup = BeautifulSoup(page, 'html.parser')
    cards = soup.select('article.card')
    assert len(cards) == 65 and path.stat().st_size < 6_000_000
    assert [c['data-case'] for c in cards[:6]] == ['HO-V2-020', 'HO-V2-021', 'HO-V2-022', 'HO-V2-052', 'HO-V2-053', 'HO-V2-043']
    assert [c['data-role'] for c in cards[:6]] == ['choice', 'choice', 'choice', 'flag', 'flag', 'related']
    assert not soup.select('[src],iframe,link,form') and "connect-src 'none'" in page
    images = json.loads(re.search(r'const PAGE_IMAGES=(.*?);</script>', page, re.S)[1])
    assert len(images) == 1  # only the cited page is embedded, once
    assert soup.select_one('#start') and 'become the frozen test' in soup.select_one('#start').get_text() and 'cannot change' in soup.select_one('#start').get_text()
    for text in ('Read the flagged AI-article cases first', 'Download the file and run one command'):
        assert text in soup.select_one('#start').get_text()
    assert soup.select_one('progress#progress') and soup.select_one('#summary') and soup.select_one('#gate')
    first = cards[0]
    assert 'D-031' in first.select_one('.banner').get_text() and 'recommended' in first.select_one('.banner').get_text()
    assert first.select_one('.banner').get_text().count('2018 to 2024') >= 1  # facts come from the passages
    assert first.select_one('[data-mti=relabel_abstain]') and not cards[3].select_one('[data-mti]')
    for button in ('approve', 'change', 'reject'):
        assert first.select_one(f'[data-act={button}]')
    assert all(not b.has_attr('aria-pressed') for b in first.select('button'))  # nothing preselected
    assert 'labourlens-heldout-v2:' in page and 'labourlens-review:' not in page
    assert hv2.pack_id_for(hv2.sha256_file(root / hv2.DRAFT)) in page


def test_page_requires_gitignored_destination(root):
    (root / '.gitignore').write_text('')
    with pytest.raises(ValueError, match='gitignored'):
        hv2.build_v2_page(root)


def test_valid_export_dry_run_writes_nothing(root):
    path = write_export(root, export_for(root, RELABEL))
    draft = (root / hv2.DRAFT).read_bytes()
    code, text = hv2.v2_approve(path, write=False, root=root)
    assert code == 0 and 'DRY RUN' in text
    assert 'changed the label of 3' in text and 'HO-V2-020: answer -> abstain' in text and ('Cost quote' in text)
    assert not (root / hv2.APPROVED).exists() and SIGNED not in (root / hv2.FREEZE).read_text()
    assert (root / hv2.DRAFT).read_bytes() == draft


SIGNED = hv2.SIGNED_MARK


def test_write_creates_new_gold_and_signed_block_without_touching_the_draft(root):
    path = write_export(root, export_for(root, {**RELABEL, 'HO-V2-030': dict(decision='reject', reason='unclear question')}))
    draft = (root / hv2.DRAFT).read_bytes()
    code, text = hv2.v2_approve(path, write=True, root=root)
    assert code == 0, text
    assert (root / hv2.DRAFT).read_bytes() == draft
    new = [json.loads(line) for line in (root / hv2.APPROVED).read_text().splitlines()]
    by_id = {c['case_id']: c for c in new}
    assert len(new) == 64 and 'HO-V2-030' not in by_id
    relabelled = by_id['HO-V2-020']
    assert relabelled['expected_behavior'] == 'abstain' and relabelled['evidence_text'] == [] and relabelled['reference_facts'] == []
    assert relabelled['context_only_evidence_text'] and relabelled['abstain_reason'] == hv2.MTI_REASONS['relabel_abstain']
    assert relabelled['reviewed_by'] is None and relabelled['review_status'] == 'draft'
    review = relabelled['owner_review']
    assert review['reviewer_name'] == 'Synthetic Owner' and review['decision_source'] == 'owner_manual' and review['original_behavior'] == 'answer'
    assert by_id['HO-V2-001']['owner_review']['decision'] == 'approve' and by_id['HO-V2-001']['evidence_text']
    freeze = (root / hv2.FREEZE).read_text()
    export_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    new_sha = hv2.sha256_file(root / hv2.APPROVED)
    block = freeze.split(SIGNED, 1)[1]
    for needle in (f'approved by owner via export `{export_sha}`', new_sha, hv2.sha256_file(root / hv2.DRAFT), 'git HEAD', 'passage fingerprint', 'uv run labourlens agent-exp',
                   'uv run labourlens paired', hv2.APPROVED, 'HO-V2-030', 'dropped 1', 'relabelled 3'):
        assert needle in block, needle
    assert text.count('uv run labourlens v2-run') >= 1 and 'agreeing to' in text
    code, again = hv2.v2_approve(path, write=True, root=root)
    assert code == 2 and 'already holds a signed block' in again


def test_partial_export_is_refused(root):
    data = export_for(root, {'HO-V2-010': dict(decision='', decision_source='')})
    code, text = hv2.v2_approve(write_export(root, data), root=root)
    assert code == 2 and 'HO-V2-010' in text and 'not decided' in text
    data = export_for(root)
    data['results'] = data['results'][:-1]
    code, text = hv2.v2_approve(write_export(root, data, 'short.json'), root=root)
    assert code == 2 and 'must decide every case' in text
    code, text = hv2.v2_approve(write_export(root, export_for(root, {'HO-V2-011': dict(decision='change', proposed_behavior='refuse', reason='')}), 'noreason.json'), root=root)
    assert code == 2 and 'needs a reason' in text


@pytest.mark.parametrize('tamper,message', [
    (lambda d: d.update(gold_sha256='0' * 64), 'different version of the draft'),
    (lambda d: d.update(pack_id='deadbeefdeadbeef'), 'different version of the draft'),
    (lambda d: d.update(surprise=1), ''),
    (lambda d: d['results'][0].update(reviewed_by='Synthetic Owner'), ''),
    (lambda d: d['results'][0].update(decision_source='agreed_with_ai_suggestion'), 'ai_basis'),
    (lambda d: d['results'][0].update(decision_source=''), 'owner_manual'),
    (lambda d: d['results'][0].update(decision='maybe'), 'not decided'),
    (lambda d: d.update(reviewer_name='  '), 'Reviewer name'),
    (lambda d: d['results'].append(dict(d['results'][0])), 'Duplicate'),
    (lambda d: d['results'][0].update(case_id='HO-V2-999'), 'every case'),
    (lambda d: d['results'][0].update(mti_choice='drop'), 'does not match decision'),
    (lambda d: d['results'][10].update(mti_choice='keep_answerable'), 'not an AI-article case'),
    (lambda d: d['results'][0].update(decision='change', proposed_behavior='answer', reason='same'), 'already has'),
    (lambda d: d['results'][0].update(proposed_behavior='abstain'), 'only a change'),
])
def test_tampered_exports_are_rejected(root, tamper, message):
    data = export_for(root)
    tamper(data)
    code, text = hv2.v2_approve(write_export(root, data), write=True, root=root)
    assert code == 2 and text.startswith('Review export rejected') and message in text
    assert not (root / hv2.APPROVED).exists() and SIGNED not in (root / hv2.FREEZE).read_text()


def test_below_threshold_exports_cannot_sign(root):
    third_unique = {'HO-V2-020': dict(decision='reject', reason='x'), 'HO-V2-021': dict(decision='reject', reason='x'), 'HO-V2-002': dict(decision='reject', reason='x')}
    code, text = hv2.v2_approve(write_export(root, export_for(root, third_unique)), write=True, root=root)
    assert code == 1 and 'CANNOT SIGN' in text and 'independent evidence groups remain' in text and 'at least 20' in text
    assert not (root / hv2.APPROVED).exists()
    few = {f'HO-V2-{n:03}': dict(decision='reject', reason='x') for n in (1, 2, 3, 4, 5, 6)}
    code, text = hv2.v2_approve(write_export(root, export_for(root, few), 'few.json'), root=root)
    assert code == 1 and 'only 59 cases remain' in text
    non_answer = {f'HO-V2-0{n}': dict(decision='reject', reason='x') for n in list(range(52, 60)) + [60, 61, 62, 63, 64, 65]}
    code, text = hv2.v2_approve(write_export(root, export_for(root, non_answer), 'na.json'), root=root)
    assert code == 1 and 'non-answer cases remain' in text
    ok = {k: v for k, v in RELABEL.items() if k in ('HO-V2-020', 'HO-V2-021')}
    code, text = hv2.v2_approve(write_export(root, export_for(root, ok), 'twenty.json'), root=root)
    assert code == 0 and 'with 20 independent evidence groups' in text  # exactly at the minimum still passes


def test_relabel_to_answer_needs_evidence_and_facts(root):
    code, text = hv2.v2_approve(write_export(root, export_for(root, {'HO-V2-052': dict(decision='change', proposed_behavior='answer', reason='r')})), root=root)
    assert code == 2 and 'cannot relabel to answer' in text


def test_changed_hashes_block_signing(root):
    write_freeze(root, drop='answer_v3')
    path = write_export(root, export_for(root))
    code, text = hv2.v2_approve(path, write=True, root=root)
    assert code == 1 and 'answer_v3' in text and 'differs from the hashes recorded' in text
    assert not (root / hv2.APPROVED).exists()
    write_freeze(root)
    put(root, 'prompts/answer_v3.md', 'edited prompt')
    code, text = hv2.v2_approve(path, root=root)
    assert code == 1 and 'answer_v3' in text


def test_cost_quote_uses_saved_usage(root):
    assert hv2.cost_quote(root, 65) is None
    for exp in ('H-r3', 'H-hybrid'):
        for model in hv2.PRIMARY_MODELS:
            put(root, f'data/runs/agent-heldout-{exp}/{model}.jsonl', '\n'.join(json.dumps({'usage': {'cost_usd': 0.001}}) for _ in range(3)))
            put(root, f'experiments/eval/agent-heldout-{exp}/{model}.judgements.json', json.dumps({'a': {'judgement': {'cost_usd': 0.002}}, 'b': {'judgement': None}}))
    quote = hv2.cost_quote(root, 65)
    assert quote['per_case_generation'] == pytest.approx(0.004) and quote['per_case_judge'] == pytest.approx(0.008)
    assert quote['total'] == pytest.approx(65 * 0.012)


def test_run_wrapper_prints_by_default_and_requires_yes_and_a_signed_file(root, monkeypatch):
    calls = []
    code, text = hv2.v2_run(root / hv2.DRAFT, yes=True, root=root)
    assert code == 2 and 'not the gold file signed' in text  # the unsigned draft is never run
    path = write_export(root, export_for(root))
    assert hv2.v2_approve(path, write=True, root=root)[0] == 0
    monkeypatch.setattr(hv2.subprocess, 'run', lambda *a, **k: calls.append(a[0]) or subprocess.CompletedProcess(a[0], 0))
    calls.clear()
    code, text = hv2.v2_run(Path(hv2.APPROVED), yes=False, root=root)
    assert code == 0 and not calls and 'Nothing was run' in text
    assert text.count('uv run labourlens') == 5 and f'--gold {hv2.APPROVED}' in text and '--tag V2-r3' in text and '--tag V2-hybrid' in text
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    code, text = hv2.v2_run(Path(hv2.APPROVED), yes=True, root=root)
    assert code == 2 and 'OPENAI_API_KEY' in text and not calls
    monkeypatch.setenv('OPENAI_API_KEY', 'test-not-a-real-key')
    code, text = hv2.v2_run(Path(hv2.APPROVED), yes=True, root=root)
    assert code == 0 and len(calls) == 5 and calls[0][:4] == ['uv', 'run', 'labourlens', 'agent-exp'] and calls[-1][3] == 'paired'
    calls.clear()
    monkeypatch.setattr(hv2.subprocess, 'run', lambda *a, **k: calls.append(a[0]) or subprocess.CompletedProcess(a[0], 3 if len(calls) == 1 else 0))
    code, text = hv2.v2_run(Path(hv2.APPROVED), yes=True, root=root)
    assert code == 3 and len(calls) == 1 and 'Stopped' in text  # stops on the first failure


def test_gold_file_edit_after_signing_is_refused_by_the_run_wrapper(root):
    path = write_export(root, export_for(root))
    assert hv2.v2_approve(path, write=True, root=root)[0] == 0
    approved = root / hv2.APPROVED
    approved.write_text(approved.read_text().replace('Synthetic question 5?', 'Synthetic question five?'))
    code, text = hv2.v2_run(Path(hv2.APPROVED), yes=False, root=root)
    assert code == 2 and 'not the gold file signed' in text


# ------------------------------------------------------------------ independent AI review integration

def ai_rec(cid, verdict='approve', behaviour=None, confidence='high', issues=()):
    return dict(case_id=cid, verdict=verdict, suggested_behaviour=behaviour, confidence=confidence, reason='Synthetic reviewer reason. More text.',
                evidence_check='Synthetic check.', issues=list(issues))


def write_ai(root, overrides):
    """overrides: {reviewer: {case number: (verdict, behaviour)}}; everything else is an approval."""
    for reviewer in 'ABC':
        lines = []
        for i in range(1, 66):
            verdict, behaviour, *conf = overrides.get(reviewer, {}).get(i, ('approve', None))
            lines.append(json.dumps(ai_rec(f'HO-V2-{i:03}', verdict, behaviour, conf[0] if conf else 'high', issues=['period straddles scope'] if i in (20, 21, 22) else [])))
        put(root, f'{hv2.AI_DIR}/{reviewer}.jsonl', '\n'.join(lines) + '\n')


AI_CHANGE = ('change_label', 'abstain')
AI_OVERRIDES = {
    'A': {20: AI_CHANGE, 21: AI_CHANGE, 22: AI_CHANGE, 30: ('approve', None), 43: ('approve', None)},
    'B': {20: AI_CHANGE, 21: AI_CHANGE, 22: AI_CHANGE, 30: ('approve', None), 43: ('reject', None)},
    'C': {22: AI_CHANGE, 30: ('reject', None), 43: ('change_label', 'abstain')},
}


@pytest.fixture
def ai_root(root):
    write_ai(root, AI_OVERRIDES)
    return root


def agreed(root, cid, **over):
    ai = hv2.load_ai(root, hv2.rows(root / hv2.DRAFT))
    entry = hv2.ai_entry(ai, cid)
    rec = dict(decision_source=hv2.AI_SOURCE, ai_basis=entry['basis'])
    if entry['action'] == 'approve':
        rec.update(decision='approve')
    elif entry['action'] == 'change':
        rec.update(decision='change', proposed_behavior=entry['behaviour'], reason='Agreed with the AI reviewers.')
        if cid in ('HO-V2-020', 'HO-V2-021', 'HO-V2-022'):
            rec['mti_choice'] = 'relabel_abstain'
    rec.update(over)
    return rec


def ai_export(root, manual=None, agree_ids=(), **top):
    ai = hv2.load_ai(root, hv2.rows(root / hv2.DRAFT))
    decisions = dict(manual or {})
    decisions.update({cid: agreed(root, cid) for cid in agree_ids})
    data = export_for(root, decisions)
    data['ai_files_sha256'] = ai['sha256']
    data.update(top)
    return data


def test_consensus_is_two_of_three_with_the_same_behaviour_otherwise_split():
    c = hv2.consensus
    assert c({'A': 'approve', 'B': 'approve', 'C': 'approve'})['label'] == 'unanimous approve'
    assert c({'A': 'approve', 'B': 'approve', 'C': 'reject'})['label'] == 'majority approve (2 of 3)'
    majority = c({'A': 'change_label:abstain', 'B': 'change_label:abstain', 'C': 'approve'})
    assert (majority['class'], majority['action'], majority['behaviour'], majority['voters']) == ('majority', 'change', 'abstain', ['A', 'B'])
    assert c({'A': 'change_label:abstain', 'B': 'change_label:clarify', 'C': 'approve'})['class'] == 'split'
    assert c({'A': 'approve', 'B': 'reject', 'C': 'change_label:abstain'})['class'] == 'split'
    assert c({'A': 'change_label:abstain', 'B': 'change_label:abstain', 'C': 'change_label:abstain'})['label'] == 'unanimous change to abstain'


def test_ai_files_are_validated_strictly(root):
    cases = hv2.rows(root / hv2.DRAFT)
    assert hv2.load_ai(root, cases) is None
    write_ai(root, {})
    assert hv2.load_ai(root, cases)['sha256'].keys() == {'A', 'B', 'C'}
    (root / hv2.AI_DIR / 'C.jsonl').unlink()
    with pytest.raises(ValueError, match='incomplete'):
        hv2.load_ai(root, cases)
    write_ai(root, {'C': {1: ('approve', 'abstain')}})  # an approval may not suggest another behaviour
    with pytest.raises(ValueError, match='approve cannot suggest'):
        hv2.load_ai(root, cases)
    write_ai(root, {'C': {1: ('change_label', 'answer')}})  # already answer
    with pytest.raises(ValueError, match='change_label needs'):
        hv2.load_ai(root, cases)


def test_page_shows_ai_strip_summary_ordering_and_guarded_agree_button(ai_root):
    soup = BeautifulSoup(hv2.build_v2_page(ai_root).read_text(), 'html.parser')
    order = [c['data-case'] for c in soup.select('article.card')]
    assert order[:7] == ['HO-V2-043', 'HO-V2-020', 'HO-V2-021', 'HO-V2-022', 'HO-V2-052', 'HO-V2-053', 'HO-V2-030']
    assert order[7:] == sorted(order[7:])
    panel = soup.select_one('#aipanel').get_text()
    assert 'This is not human review' in panel and 'Of 65 cases, 60 were unanimously approved' in panel and '5 need your judgement' in panel
    assert 'Fewer independent tests than cases' in panel and 'Study period of the AI article' in panel
    assert soup.select_one('#quick-ai').get_text(strip=True) == 'Review the 60 unanimous approvals quickly'
    assert [a['data-jump'] for a in soup.select('#aipanel a[data-jump]')][:2] == ['HO-V2-043', 'HO-V2-020']
    card = soup.select_one('article[data-case=HO-V2-020]')
    strip = card.select_one('.aistrip')
    assert 'Independent AI review (3 reviewers, not human)' in strip.get_text() and strip.get_text().count('Reviewer ') == 3
    assert 'majority change to abstain (2 of 3)' in strip.get_text()
    agree = strip.select_one('button[data-agree]')
    assert agree.has_attr('disabled') and 'Agree with AI (majority change to abstain (2 of 3))' in agree.get_text(' ', strip=True)
    split = soup.select_one('article[data-case=HO-V2-043]')
    assert split.select_one('button[data-agree]') is None and 'do not agree with each other' in split.get_text()
    assert 'keep the answer with a caveat' in split.select_one('.banner').get_text()
    assert len(soup.select('button[data-agree]')) == 64 and soup.select_one('article[data-case=HO-V2-001]')['data-ai-class'] == 'unanimous'
    page = str(soup)
    assert 'WAIT_MS = 3000' in page and "agree(c)" in page and not re.search(r'src="https?://', page)


def test_page_without_ai_files_has_no_ai_controls(root):
    soup = BeautifulSoup(hv2.build_v2_page(root).read_text(), 'html.parser')
    assert soup.select_one('#aipanel') is None and soup.select_one('[data-agree]') is None and soup.select_one('#quick-ai') is None


def test_mixed_export_is_accepted_and_reports_the_two_sources(ai_root):
    root = ai_root
    manual = {**{k: v for k, v in RELABEL.items() if k == 'HO-V2-021'}, 'HO-V2-055': dict(decision='change', proposed_behavior='clarify', reason='Needs a clarification instead.')}
    ids = [f'HO-V2-{i:03}' for i in range(1, 11)] + ['HO-V2-020', 'HO-V2-022']
    path = write_export(root, ai_export(root, manual, ids))
    code, text = hv2.v2_approve(path, root=root)
    assert code == 0, text
    assert 'Who decided: 53 by your own click, 12 by agreeing with an AI suggestion' in text and 'not independent inter-rater evidence' in text
    assert 'Your own decisions that matched the AI consensus: 51 of 52' in text  # HO-V2-043 is split; HO-V2-055 differs; agreed cards are excluded
    code, text = hv2.v2_approve(path, write=True, root=root)
    assert code == 0
    new = {json.loads(l)['case_id']: json.loads(l) for l in (root / hv2.APPROVED).read_text().splitlines()}
    assert new['HO-V2-001']['owner_review']['decision_source'] == hv2.AI_SOURCE and new['HO-V2-001']['owner_review']['ai_basis']['consensus'] == 'unanimous approve'
    assert 'not independent inter-rater evidence' in new['HO-V2-001']['owner_review']['decision_provenance']
    assert new['HO-V2-020']['expected_behavior'] == 'abstain' and new['HO-V2-020']['owner_review']['decision_source'] == hv2.AI_SOURCE
    assert new['HO-V2-021']['owner_review']['decision_source'] == 'owner_manual' and new['HO-V2-021']['owner_review']['ai_basis'] is None
    assert new['HO-V2-030']['owner_review']['decision_source'] == 'owner_manual'
    block = (root / hv2.FREEZE).read_text().split(SIGNED, 1)[1]
    assert '53 cards by the owner’s own click, 12 cards by the owner agreeing with an AI suggestion' in block
    assert 'not independent inter-rater evidence' in block and 'matched the AI consensus:** 51 of 52' in block
    for reviewer, sha in hv2.load_ai(root, hv2.rows(root / hv2.DRAFT))['sha256'].items():
        assert f'{reviewer} `{sha}`' in block


@pytest.mark.parametrize('mutate,message', [
    (lambda d: d['results'][0]['ai_basis']['votes'].update(C='reject'), 'ai_basis does not match'),
    (lambda d: d['results'][0]['ai_basis'].update(consensus='unanimous reject'), 'ai_basis does not match'),
    (lambda d: d['results'][0].update(ai_basis={'consensus': 'x'}), 'ai_basis does not match'),
    (lambda d: d['results'][0].update(decision='reject', reason='r'), 'does not match the AI consensus'),
    (lambda d: d.update(ai_files_sha256={**d['ai_files_sha256'], 'A': '0' * 64}), 'SHA-256 mismatch'),
    (lambda d: d.update(ai_files_sha256={}), 'SHA-256 mismatch'),
    (lambda d: d['results'][1].update(ai_basis={'consensus': 'x'}), 'carries no ai_basis'),
])
def test_tampered_ai_agreement_is_rejected(ai_root, mutate, message):
    data = ai_export(ai_root, agree_ids=['HO-V2-001'])
    mutate(data)
    code, text = hv2.v2_approve(write_export(ai_root, data), write=True, root=ai_root)
    assert code == 2 and message in text
    assert not (ai_root / hv2.APPROVED).exists() and SIGNED not in (ai_root / hv2.FREEZE).read_text()


def test_agreeing_on_a_split_card_fails(ai_root):
    entry = hv2.ai_entry(hv2.load_ai(ai_root, hv2.rows(ai_root / hv2.DRAFT)), 'HO-V2-043')
    assert entry['class'] == 'split'
    data = ai_export(ai_root, {'HO-V2-043': dict(decision='approve', decision_source=hv2.AI_SOURCE, ai_basis=entry['basis'])})
    code, text = hv2.v2_approve(write_export(ai_root, data), write=True, root=ai_root)
    assert code == 2 and 'HO-V2-043' in text and 'split' in text


def test_ai_files_changed_after_the_export_invalidates_it(ai_root):
    data = ai_export(ai_root, agree_ids=['HO-V2-001'])
    write_ai(ai_root, {**AI_OVERRIDES, 'A': {**AI_OVERRIDES['A'], 5: ('approve', None)}, 'B': {**AI_OVERRIDES['B']}, 'C': {**AI_OVERRIDES['C']}})
    path = ai_root / hv2.AI_DIR / 'A.jsonl'
    path.write_text(path.read_text().replace('"confidence": "high"', '"confidence": "low"', 1))
    code, text = hv2.v2_approve(write_export(ai_root, data), root=ai_root)
    assert code == 2 and 'SHA-256 mismatch' in text


def test_agreement_needs_the_ai_files_to_be_present(root):
    data = export_for(root, {'HO-V2-001': dict(decision_source=hv2.AI_SOURCE, ai_basis={'consensus': 'unanimous approve', 'class': 'unanimous', 'votes': {'A': 'approve', 'B': 'approve', 'C': 'approve'}})})
    code, text = hv2.v2_approve(write_export(root, data), root=root)
    assert code == 2 and 'AI review files are not available' in text


def test_old_style_export_without_ai_fields_still_works_when_ai_files_exist(ai_root):
    code, text = hv2.v2_approve(write_export(ai_root, export_for(ai_root, RELABEL)), root=ai_root)
    assert code == 0, text
    assert 'Who decided: 65 by your own click, 0 by agreeing' in text


def test_fleiss_kappa_known_values():
    assert hv2.fleiss_kappa([['a'] * 3, ['b'] * 3, ['a'] * 3, ['b'] * 3]) == pytest.approx(1.0)
    assert hv2.fleiss_kappa([['a'] * 3] * 4) is None
    assert hv2.fleiss_kappa([['a', 'a', 'b'], ['a', 'b', 'b'], ['a', 'a', 'a'], ['b', 'b', 'b']]) == pytest.approx(0.3333, abs=1e-3)


def test_commit_safe_summary_has_counts_pairwise_and_kappa_and_no_raw_files(ai_root):
    path = hv2.write_ai_summary(ai_root)
    text = path.read_text()
    assert path == ai_root / hv2.AI_SUMMARY and 'This is not human review' in text and 'same model family' in text
    assert '| unanimous approve | 60 |' in text and '| split | 1 |' in text and '| majority change | 2 |' in text
    assert 'Fleiss’ kappa on the verdict:' in text and 'Pairwise agreement on the verdict: A-B' in text
    assert '| HO-V2-043 |' in text and '| HO-V2-001 |' not in text and 'private' in text
    assert text.count('SHA-256 of the private files') == 1
    stats = hv2.ai_statistics(hv2.load_ai(ai_root, hv2.rows(ai_root / hv2.DRAFT)), hv2.rows(ai_root / hv2.DRAFT))
    assert stats['all_three_verdict'] == 65 - 4 and stats['pairwise_verdict']['A-B'] == pytest.approx(64 / 65)


def test_low_confidence_majority_is_not_offered_as_one_click_and_cannot_be_agreed(root):
    low = {'A': {43: ('approve', None, 'low')}, 'B': {43: ('approve', None, 'low')}, 'C': {43: ('reject', None)}}
    write_ai(root, low)
    cases = hv2.rows(root / hv2.DRAFT)
    entry = hv2.ai_entry(hv2.load_ai(root, cases), 'HO-V2-043')
    assert (entry['class'], entry['action'], entry['low_confidence'], entry['agreeable']) == ('majority', 'approve', True, False)
    soup = BeautifulSoup(hv2.build_v2_page(root).read_text(), 'html.parser')
    card = soup.select_one('article[data-case=HO-V2-043]')
    assert card.select_one('button[data-agree]') is None and 'not confident' in card.get_text()
    assert [c['data-case'] for c in soup.select('article.card')][0] == 'HO-V2-043'
    assert 'Review the 64 unanimous approvals quickly' in soup.select_one('#quick-ai').get_text()
    ai = hv2.load_ai(root, cases)
    data = export_for(root, {'HO-V2-043': dict(decision='approve', decision_source=hv2.AI_SOURCE, ai_basis=entry['basis'])})
    data['ai_files_sha256'] = ai['sha256']
    code, text = hv2.v2_approve(write_export(root, data), root=root)
    assert code == 2 and 'low-confidence' in text
