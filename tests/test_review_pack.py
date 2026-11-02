"""Corpus-free pack/export checks plus explicitly marked real-corpus coverage."""
import json
import subprocess

import pandas as pd
import pytest
import pymupdf
import re
from bs4 import BeautifulSoup
from pydantic import ValidationError

from labourlens.review.pack import EXTRA, ROOT, ReviewExport, build_pack, endorsement_statement, ingest_review, load_tiebreak


def put(root, name, value):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value)
    return path


@pytest.fixture
def fixture_root(tmp_path):
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    put(tmp_path, '.gitignore', 'private/\n')
    put(tmp_path, 'data/snapshots/test/s1/raw.csv', 'quarter,value\n2026-Q2,2.9\n')
    put(tmp_path, 'data/raw/report/s1/report.html', '<article><h1>Synthetic report</h1><p>Surrounding article before.</p><p>Synthetic text &lt;script&gt;attack()&lt;/script&gt;</p><p>Article after.</p></article>')
    manifest = [dict(source_id='test', snapshot_id='s1', title='Synthetic statistics', raw_path='data/snapshots/test/s1/raw.csv', canonical_url='https://data.gov.sg/synthetic'), dict(source_id='report', snapshot_id='s1', title='Synthetic report', raw_path='data/raw/report/s1/report.html')]
    raw_pdf = tmp_path / 'data/raw/pdf/s1/report.pdf'
    raw_pdf.parent.mkdir(parents=True)
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_text((50, 60), 'Synthetic PDF passage')
        doc.save(raw_pdf)
    manifest.append(dict(source_id='pdf', snapshot_id='s1', title='Synthetic PDF', raw_path='data/raw/pdf/s1/report.pdf'))
    put(tmp_path, 'data/manifests/manifest.json', json.dumps({'entries': manifest}))
    observation = dict(observation_id='obs1', source_id='test', snapshot_id='s1', source_locator='csv_row=2;col=value', indicator_id='unemployment', dimension='', period='2026-Q2', value=2.9, unit='percent', release_stage='final')
    (tmp_path / 'data/processed').mkdir()
    pd.DataFrame([observation]).to_parquet(tmp_path / 'data/processed/observations.parquet')
    passage = dict(passage_id='report:p001:test', source_id='report', snapshot_id='s1', document_title='Synthetic report', page_number=1, original_url='https://www.mom.gov.sg/synthetic', text='Synthetic text <script>attack()</script>', release_stage='final')
    put(tmp_path, 'data/passages/report.jsonl', json.dumps(passage))
    pdf_passage = dict(passage, passage_id='pdf:p001:test', source_id='pdf', document_title='Synthetic PDF', text='Synthetic PDF passage', bbox=[45, 45, 250, 70], printed_page_label='i')
    put(tmp_path, 'data/passages/pdf.jsonl', json.dumps(pdf_passage))
    sample = [f'DEV-{n:03}' for n in range(1, 41)]
    cases = []
    for cid in sample + [f'HO-{n:03}' for n in range(1, 32)] + [c for c in EXTRA if c not in sample]:
        cases.append(dict(case_id=cid, question='What was the resident rate in Q2 2026?', family='factual_lookup', expected_behavior='answer', evidence_text=[{'passage_ids': ['report:p001:test', 'pdf:p001:test']}], evidence_data=[{'observation_ids': ['obs1']}], reference_facts=['Synthetic 2.9%'], difficulty_note='Synthetic lookup'))
    put(tmp_path, 'experiments/gold/draft_cases.jsonl', '\n'.join(json.dumps(c) for c in cases))
    put(tmp_path, 'experiments/human-review-sample/selection.json', json.dumps({'ids': sample}))
    put(tmp_path, 'experiments/human-review-sample/independent-ai-review.md', '| DEV-001 | answered | incorrect | retrieval miss |\n')
    put(tmp_path, 'experiments/gold/independent-ai-review.md', '| HO-001 / 20 | factual_lookup | `answer` → `answer` | x | y |\n')
    put(tmp_path, 'experiments/gold/independent-ai-review-2.md', '#### HO-001 — `answer`\n')
    runs = [dict(case_id=c, answer={'status': 'answered', 'summary': 'Synthetic answer', 'claims': [{'text': '2.9%', 'citations': [{'label': 'O1', 'quote': '2.9'}]}]}, evidence=[{'label': 'O1', 'id': 'obs1'}], evidence_text={'O1': 'Synthetic 2.9 percent'}) for c in sample]
    put(tmp_path, 'data/runs/agent-dev-A1/gpt-6-luna.jsonl', '\n'.join(json.dumps(r) for r in runs))
    put(tmp_path, 'docs/human-review/passage-spot-check.md', '\n'.join(f'| {n} | report | p1 | ok | `report:p001:test` | link |' for n in range(1, 17)) + '\n| 1 | | | | |')
    put(tmp_path, 'docs/human-review/statistical-spot-check.md', '\n'.join(f'| {n} | test | Q2 | - | 2.9 | percent | row2 | `obs1` | link |' for n in range(1, 15)))
    put(tmp_path, 'docs/human-review/ai-verification-of-pre-reviews.md', '## 4. Checklist\n' + '\n'.join(f'{n}. Synthetic check {n}' for n in range(1, 13)) + '\n## 5. Limits')
    return tmp_path


def export_data():
    return dict(schema_version=1, pack_id='synthetic', reviewer_name='', exported_at='2026-10-31T00:00:00Z', results=[dict(case_id='DEV-001', tab='answers', fields={'verdict': 'correct', 'comment': 'private excerpt', 'shareable': False}, timestamp='2026-10-31T00:00:00Z')], checklist={})


def test_build_synthetic_pack(fixture_root):
    path = build_pack(fixture_root)
    soup = BeautifulSoup(path.read_text(), 'html.parser')
    assert len(soup.select('article[data-tab=answers]')) == 40
    assert len(soup.select('article[data-tab=gold][data-case^=HO-]')) == 31
    assert len(soup.select('article[data-tab=sources]')) == 30
    assert len(soup.select('article[data-tab=decisions]')) == 10
    assert soup.select_one('#focus-mode').has_attr('checked')
    assert soup.select_one('#progress-bar')
    assert soup.select_one('#quick-path')
    assert soup.select_one('#next-undecided')
    assert len(soup.select('article > .check-hint strong')) == len(soup.select('article'))
    assert soup.select_one('#answers-DEV-001 .answer-pane')
    assert soup.select_one('#answers-DEV-001 .evidence-pane')
    assert len(soup.select('[data-check]')) == 12
    assert not soup.select('[src],link,iframe,form')
    assert soup.select('img[data-page]')
    assets = json.loads(re.search(r'const PAGE_IMAGES=(.*?);</script>', path.read_text()).group(1))
    assert len(assets) == 1  # Same PDF page occurs on many cards, encoded only once.
    assert soup.select('.bbox')
    assert soup.select('mark')
    assert soup.select('tr.cited')
    assert soup.select_one('#priority')
    assert soup.select_one('#tab-filter')
    assert 'Worked example' in soup.get_text()
    assert 'connect-src \'none\'' in path.read_text()
    assert not soup.select('[data-field][checked],option[selected]')
    assert soup.select_one('#reviewer').get('value') is None
    assert soup.select_one('#fast-mode').has_attr('checked')
    assert soup.select_one('#shortcuts kbd')
    assert soup.select_one('.shortcut-strip').get_text().count('Backspace') == 1
    assert soup.select_one('#answers-DEV-001 .what-to-do')
    assert soup.select_one('#answers-DEV-001')['data-ai-status'] == 'agree'
    assert json.loads(soup.select_one('#answers-DEV-001')['data-ai-suggest']) == {'verdict': 'incorrect'}
    assert soup.select_one('#answers-DEV-002')['data-ai-status'] == 'none'
    assert not soup.select_one('#answers-DEV-002 .agree-ai')
    assert 'decide yourself' in soup.select_one('#answers-DEV-002 .no-agree').get_text()
    assert soup.select_one('#gold-HO-001')['data-ai-status'] == 'agree'
    assert json.loads(soup.select_one('#gold-HO-001')['data-ai-suggest']) == {'label': 'OK', 'evidence': 'OK', 'facts': 'OK'}
    assert soup.select_one('#gold-HO-008')['data-ai-status'] == 'disagree'  # a known doubtful label never offers Agree
    assert not soup.select_one('#gold-HO-008 .agree-ai')
    assert soup.select_one('#sources-statistical-13')['data-ai-status'] == 'disagree'
    assert json.loads(soup.select_one('#sources-statistical-07')['data-ai-suggest']) == {'match': 'minor'}
    assert soup.select_one('#answers-DEV-001 .ai-box').get_text().startswith('AI reviewers said:')
    assert all(button.has_attr('disabled') for button in soup.select('.agree-ai'))  # enabled only by the 3-second guard
    assert not soup.select('.fast-actions [checked]')
    for node in soup.select('.ai-box'):
        node.decompose()
    for node in soup.select('.ai-review'):
        assert not node.has_attr('open')
        node.decompose()
    assert 'AI verdict:' not in soup.get_text()
    assert not soup.find('script', string='attack()')
    assert 'CSV row 2' in soup.get_text()
    assert '2026-Q2,2.9' in soup.get_text()
    assert not soup.select('a[href^="file:"]')
    assert soup.select_one('a[href="#evidence-DEV-001-O1"]')


def test_export_schema():
    assert ReviewExport.model_validate(export_data()).reviewer_name == ''
    invalid = export_data()
    invalid['results'][0]['fields']['verdict'] = 'automatic pass'
    with pytest.raises(ValidationError):
        ReviewExport.model_validate(invalid)
    draft = export_data()
    draft['results'][0]['fields'] = {'label': 'disagree'}
    assert ReviewExport.model_validate(draft)  # Automatic backups must preserve unfinished drafts.
    decision = export_data()
    decision['results'] = [dict(case_id='J1', tab='decisions', fields={'decision': 'pending'}, timestamp='2026-10-31T00:00:00Z')]
    assert ReviewExport.model_validate(decision)
    decision['results'][0]['fields']['decision'] = 'accept_alternatives'
    with pytest.raises(ValidationError, match='Invalid decision option'):
        ReviewExport.model_validate(decision)


def test_ingest_requires_owner_and_excludes_private_comments(fixture_root):
    data = export_data()
    file = put(fixture_root, 'private/export.json', json.dumps(data))
    with pytest.raises(ValueError, match='Reviewer name'):
        ingest_review(file, fixture_root)
    assert not (fixture_root / 'docs/human-review/owner-review-summary.md').exists()
    data['reviewer_name'] = 'Synthetic human'
    data['results'].append(dict(case_id='HO-001', tab='gold', fields={'label': 'disagree', 'proposed_behavior': 'clarify', 'comment': 'Shareable owner explanation', 'shareable': True}, timestamp='2026-10-31T00:00:00Z'))
    data['results'].append(dict(case_id='J1', tab='decisions', fields={'decision': 'pending', 'comment': 'Private verification note', 'shareable': False}, timestamp='2026-10-31T00:00:00Z'))
    file.write_text(json.dumps(data))
    gold = (fixture_root / 'experiments/gold/draft_cases.jsonl').read_bytes()
    summary, proposal = ingest_review(file, fixture_root)
    assert 'private excerpt' not in summary.read_text()
    assert 'Synthetic text' not in summary.read_text()
    assert 'Synthetic human' in summary.read_text()
    assert 'Shareable owner explanation' in summary.read_text()
    assert 'keep publisher verification incomplete' in summary.read_text()
    assert 'Private verification note' not in summary.read_text()
    assert '0/1 comparable manual owner verdicts' in summary.read_text()
    assert json.loads(proposal.read_text())['proposed_behavior'] == 'clarify'
    assert (fixture_root / 'experiments/gold/draft_cases.jsonl').read_bytes() == gold


def test_private_output_guard(fixture_root):
    (fixture_root / '.gitignore').write_text('')
    with pytest.raises(ValueError, match='gitignored'):
        build_pack(fixture_root)


def test_optional_adjudication_priorities(fixture_root):
    put(fixture_root, 'docs/human-review/ai-adjudication.md', "# Optional adjudication\n## Owner's eyes only — ten actual decisions/checks\n1. HO-022: decide the correction boundary.\n")
    soup = BeautifulSoup(build_pack(fixture_root).read_text(), 'html.parser')
    assert soup.select_one('#gold-HO-022')['data-priority'] == 'true'
    assert soup.select_one('a[data-jump=\"HO-022\"]')


def test_ingest_refuses_incomplete_disagreement(fixture_root):
    data = export_data()
    data['reviewer_name'] = 'Synthetic reviewer'
    data['results'] = [dict(case_id='HO-001', tab='gold', fields={'label': 'disagree'}, timestamp='2026-10-31T00:00:00Z')]
    path = put(fixture_root, 'private/incomplete.json', json.dumps(data))
    with pytest.raises(ValueError, match='complete the proposed'):
        ingest_review(path, fixture_root)
    assert not (fixture_root / 'docs/human-review/owner-review-summary.md').exists()


def test_quick_path_keeps_union_of_a1_concerns(fixture_root):
    put(fixture_root, 'experiments/human-review-sample/ai-review-summary.md', '## Failure types\n| other | DEV-002 |\n## Other section\nDEV-003 is not a failure here.')
    soup = BeautifulSoup(build_pack(fixture_root).read_text(), 'html.parser')
    assert soup.select_one('#answers-DEV-001')['data-quick'] == 'true'
    assert soup.select_one('#answers-DEV-002')['data-quick'] == 'true'
    assert soup.select_one('#answers-DEV-003')['data-quick'] == 'false'
    assert len(soup.select('article[data-tab=gold][data-quick=true]')) == 8
    assert len(soup.select('article[data-tab=sources][data-quick=true]')) == 8


def endorsed_export(name='Synthetic Owner'):
    data = export_data()
    data['reviewer_name'] = name
    data['results'] = [
        dict(case_id='DEV-001', tab='answers', fields={'verdict': 'incorrect'}, timestamp='2026-10-31T00:00:00Z'),
        dict(case_id='DEV-002', tab='answers', fields={}, timestamp='2026-10-31T00:00:00Z', endorsement='owner_endorsed_ai'),
        dict(case_id='HO-001', tab='gold', fields={}, timestamp='2026-10-31T00:00:00Z', endorsement='owner_endorsed_ai'),
    ]
    data['attestation'] = dict(reviewer_name=name, statement=endorsement_statement(2), timestamp='2026-10-31T00:00:00Z', counts={'answers': 1, 'gold': 1, 'sources': 0, 'decisions': 0})
    return data


def test_endorsement_schema_is_separate_and_strict():
    assert ReviewExport.model_validate(endorsed_export()).attestation.counts['answers'] == 1
    mixed = endorsed_export()
    mixed['results'][1]['fields'] = {'verdict': 'correct'}
    with pytest.raises(ValidationError, match='cannot be combined'):
        ReviewExport.model_validate(mixed)
    decision = endorsed_export()
    decision['results'].append(dict(case_id='J1', tab='decisions', fields={}, timestamp='2026-10-31T00:00:00Z', endorsement='owner_endorsed_ai'))
    with pytest.raises(ValidationError, match='cannot be endorsed'):
        ReviewExport.model_validate(decision)
    no_attestation = endorsed_export()
    no_attestation['attestation'] = None
    with pytest.raises(ValidationError, match='require an attestation'):
        ReviewExport.model_validate(no_attestation)
    altered = endorsed_export()
    altered['attestation']['statement'] = 'I independently reviewed these cards.'
    with pytest.raises(ValidationError, match='exact endorsement statement'):
        ReviewExport.model_validate(altered)
    unnamed = endorsed_export('')
    with pytest.raises(ValidationError):
        ReviewExport.model_validate(unnamed)


def test_ingest_separates_endorsement_and_never_proposes_changes(fixture_root):
    data = endorsed_export()
    path = put(fixture_root, 'private/endorsed.json', json.dumps(data))
    gold = (fixture_root / 'experiments/gold/draft_cases.jsonl').read_bytes()
    summary, proposal = ingest_review(path, fixture_root)
    text = summary.read_text()
    assert '## Owner-entered decisions' in text
    assert '## Owner-endorsed AI review (no independent per-item review)' in text
    assert endorsement_statement(2) in text
    assert '1/1 comparable manual owner verdicts' in text
    assert proposal.read_text() == ''
    assert '| answers | DEV-002 |' in text
    assert (fixture_root / 'experiments/gold/draft_cases.jsonl').read_bytes() == gold
    assert 'reviewed_by' not in text


def test_ingest_refuses_endorsement_without_matching_name(fixture_root):
    data = endorsed_export()
    data['reviewer_name'] = ''
    path = put(fixture_root, 'private/unnamed-endorsed.json', json.dumps(data))
    with pytest.raises(ValidationError):
        ingest_review(path, fixture_root)
    assert not (fixture_root / 'docs/human-review/owner-review-summary.md').exists()


def test_pack_contains_endorsement_controls(fixture_root):
    soup = BeautifulSoup(build_pack(fixture_root).read_text(), 'html.parser')
    assert soup.select_one('#endorse-all').get_text(strip=True) == 'Endorse AI review for all undecided cards'
    assert soup.select_one('#undo-all-endorsements')
    page = soup.decode()
    assert 'NOT as independent human review' in page
    assert 'owner_endorsed_ai' in page


def test_decision_source_schema_is_strict():
    data = export_data()
    data['results'][0]['decision_source'] = 'owner_manual'
    assert ReviewExport.model_validate(data)
    data['results'][0]['decision_source'] = 'amended'
    with pytest.raises(ValidationError, match='Invalid decision_source'):
        ReviewExport.model_validate(data)
    data['results'][0]['decision_source'] = 'agreed_with_ai_suggestion'
    data['results'][0]['fields'] = {}
    with pytest.raises(ValidationError, match='requires an independent decision'):
        ReviewExport.model_validate(data)
    disagree = export_data()
    disagree['results'] = [dict(case_id='HO-001', tab='gold', fields={'label': 'disagree', 'proposed_behavior': 'clarify'}, timestamp='2026-10-31T00:00:00Z', decision_source='agreed_with_ai_suggestion')]
    with pytest.raises(ValidationError, match='never proposes'):
        ReviewExport.model_validate(disagree)
    endorsed = endorsed_export()
    endorsed['results'][1]['decision_source'] = 'owner_manual'
    with pytest.raises(ValidationError, match='no independent decision source'):
        ReviewExport.model_validate(endorsed)
    unknown = export_data()
    unknown['results'][0]['reviewed_by'] = 'owner'
    with pytest.raises(ValidationError):
        ReviewExport.model_validate(unknown)


def test_ingest_splits_provenance_and_excludes_agreed_from_agreement(fixture_root):
    data = export_data()
    data['reviewer_name'] = 'Synthetic human'
    stamp = '2026-10-31T00:00:00Z'
    data['results'] = [
        dict(case_id='DEV-001', tab='answers', fields={'verdict': 'incorrect'}, timestamp=stamp, decision_source='owner_manual'),
        dict(case_id='DEV-002', tab='answers', fields={'verdict': 'correct'}, timestamp=stamp, decision_source='agreed_with_ai_suggestion'),
        dict(case_id='HO-001', tab='gold', fields={'label': 'disagree', 'proposed_behavior': 'refuse'}, timestamp=stamp, decision_source='owner_manual'),
        dict(case_id='HO-002', tab='gold', fields={'label': 'OK', 'evidence': 'OK', 'facts': 'OK'}, timestamp=stamp, decision_source='agreed_with_ai_suggestion'),
    ]
    path = put(fixture_root, 'private/provenance.json', json.dumps(data))
    gold = (fixture_root / 'experiments/gold/draft_cases.jsonl').read_bytes()
    summary, proposal = ingest_review(path, fixture_root)
    text = summary.read_text()
    assert '- owner_manual: 2' in text
    assert '- agreed_with_ai_suggestion: 2' in text
    assert '1/1 comparable manual owner verdicts' in text  # DEV-002 agreement with AI is circular and excluded
    lines = [json.loads(line) for line in proposal.read_text().splitlines()]
    assert [line['case_id'] for line in lines] == ['HO-001']
    assert (fixture_root / 'experiments/gold/draft_cases.jsonl').read_bytes() == gold
    assert 'reviewed_by' not in text


def test_older_exports_without_provenance_remain_valid_and_count_as_manual(fixture_root):
    data = export_data()
    data['reviewer_name'] = 'Synthetic human'
    path = put(fixture_root, 'private/legacy.json', json.dumps(data))
    assert ReviewExport.model_validate_json(path.read_text()).results[0].decision_source == ''
    summary, _ = ingest_review(path, fixture_root)
    assert '- owner_manual: 1' in summary.read_text()


def tiebreak_fixture(root, mutate=None):
    """Three blind reviewers over five synthetic disagree cards."""
    put(root, 'experiments/human-review-sample/independent-ai-review.md', '| DEV-001 | answered | incorrect | retrieval miss |\n| DEV-004 | answered | correct | — | Agree | fine |\n')
    put(root, 'experiments/human-review-sample/ai-review-summary.md', '## Failure types\n| other | DEV-004 |\n## Next\n')
    cards = [('answers', 'DEV-004'), ('gold', 'HO-008'), ('gold', 'HO-020'), ('sources', 'passage-03'), ('sources', 'passage-06')]
    folder = root / 'private/human-review/tiebreak'
    put(root, 'private/human-review/tiebreak/cards.jsonl', '\n'.join(json.dumps({'case_id': c, 'tab': t, 'where': {'gold_evidence': [{'kind': 'passage', 'id': 'report:p001:test'}]}}) for t, c in cards))
    def verdict(tab, case, reviewer):
        base = dict(case_id=case, tab=tab, reviewer_id=reviewer, confidence='high', reason='Checked the stored row and the saved answer.', evidence_checked=['obs1'])
        if tab == 'answers':
            return dict(base, verdict='correct')
        if tab == 'gold':
            return dict(base, verdict='label_ok', evidence='ok', facts='ok')
        return dict(base, verdict='matches' if case == 'passage-03' or reviewer != 'tb-c' else 'major')
    for reviewer in ('tb-a', 'tb-b', 'tb-c'):
        records = [verdict(t, c, reviewer) for t, c in cards]
        if mutate:
            records = mutate(reviewer, records)
        put(root, f'private/human-review/tiebreak/verdicts-{reviewer}.jsonl', '\n'.join(json.dumps(r) for r in records))
    return folder


def test_tiebreak_offers_agree_only_on_unanimous_verdicts(fixture_root):
    def mutate(reviewer, records):
        for r in records:
            if r['case_id'] == 'HO-020' and reviewer == 'tb-b':
                r['needs_human'] = True
        return records
    tiebreak_fixture(fixture_root, mutate)
    soup = BeautifulSoup(build_pack(fixture_root).read_text(), 'html.parser')
    agreed = soup.select_one('#answers-DEV-004')
    assert agreed['data-ai-status'] == 'agree' and agreed['data-ai-basis'] == 'tiebreak'
    assert json.loads(agreed['data-ai-suggest']) == {'verdict': 'correct'}
    assert 'AI tie-break (3 independent passes) agree: correct' in agreed.select_one('.ai-box').get_text()
    assert agreed.select_one('.agree-ai')
    gold = soup.select_one('#gold-HO-008')
    assert gold['data-ai-status'] == 'agree' and json.loads(gold['data-ai-suggest']) == {'label': 'OK', 'evidence': 'OK', 'facts': 'OK'}
    assert soup.select_one('#sources-passage-03')['data-ai-status'] == 'agree'
    for blocked in ('#gold-HO-020', '#sources-passage-06'):  # needs_human / split verdicts stay decide-yourself
        card = soup.select_one(blocked)
        assert card['data-ai-status'] == 'disagree' and not card.select_one('.agree-ai')
        assert card.select('.tiebreak li')
        assert 'decide yourself' in card.select_one('.no-agree').get_text()
    assert 'needs a human' in soup.select_one('#gold-HO-020 .ai-box').get_text()


def test_pack_builds_without_tiebreak_and_can_ignore_it(fixture_root):
    assert not BeautifulSoup(build_pack(fixture_root).read_text(), 'html.parser').select('.tiebreak')
    tiebreak_fixture(fixture_root)
    soup = BeautifulSoup(build_pack(fixture_root, use_tiebreak=False).read_text(), 'html.parser')
    assert not soup.select('.tiebreak')
    assert soup.select_one('#answers-DEV-004')['data-ai-status'] == 'disagree'


@pytest.mark.parametrize('change,message', [
    (lambda r: r.update(surprise='x'), 'unknown fields'),
    (lambda r: r.update(verdict='amended'), 'invalid verdict'),
    (lambda r: r.update(reviewer_id='tb-z'), 'does not match file name'),
    (lambda r: r.update(confidence='certain'), 'invalid confidence'),
    (lambda r: r.update(reason=' '.join(['word'] * 41)), 'at most 40 words'),
    (lambda r: r.update(evidence_checked=[]), 'evidence_checked'),
    (lambda r: r.update(verdict='correct', failure_type='other'), 'failure_type'),
])
def test_tiebreak_validation_rejects_bad_records(fixture_root, change, message):
    def mutate(reviewer, records):
        if reviewer == 'tb-a':
            change(records[0])
        return records
    tiebreak_fixture(fixture_root, mutate)
    with pytest.raises(ValueError, match=message):
        load_tiebreak(fixture_root)


def test_tiebreak_rejects_missing_duplicate_gold_shape_and_copied_prose(fixture_root):
    tiebreak_fixture(fixture_root, lambda reviewer, records: records[:-1] if reviewer == 'tb-b' else records)
    with pytest.raises(ValueError, match='missing cards'):
        load_tiebreak(fixture_root)
    tiebreak_fixture(fixture_root, lambda reviewer, records: records + [records[0]] if reviewer == 'tb-a' else records)
    with pytest.raises(ValueError, match='duplicate card'):
        load_tiebreak(fixture_root)
    tiebreak_fixture(fixture_root, lambda reviewer, records: [dict(r, verdict='label_wrong') if r['tab'] == 'gold' and reviewer == 'tb-a' else r for r in records])
    with pytest.raises(ValueError, match='proposed_behavior'):
        load_tiebreak(fixture_root)
    put(fixture_root, 'data/passages/long.jsonl', json.dumps(dict(passage_id='report:p002:long', source_id='report', snapshot_id='s1', document_title='t', page_number=1, original_url='https://www.mom.gov.sg/x', text='alpha beta gamma delta epsilon zeta eta theta iota', release_stage='final')))
    def copy(reviewer, records):
        if reviewer == 'tb-c':
            records[0] = dict(records[0], reason='It says alpha beta gamma delta epsilon zeta eta here.', evidence_checked=['report:p002:long'])
        return records
    tiebreak_fixture(fixture_root, copy)
    with pytest.raises(ValueError, match='copies more than 6 consecutive words'):
        load_tiebreak(fixture_root)
    tiebreak_fixture(fixture_root, lambda reviewer, records: [dict(r, reason='A paraphrase using alpha beta gamma only.', evidence_checked=['report:p002:long']) if r is records[0] else r for r in records])
    assert load_tiebreak(fixture_root)  # six-word overlap is allowed


def test_ai_basis_is_validated_and_summarised(fixture_root):
    data = export_data()
    data['reviewer_name'] = 'Synthetic human'
    stamp = '2026-10-31T00:00:00Z'
    data['results'] = [
        dict(case_id='DEV-001', tab='answers', fields={'verdict': 'incorrect'}, timestamp=stamp, decision_source='agreed_with_ai_suggestion', ai_basis='tiebreak'),
        dict(case_id='DEV-002', tab='answers', fields={'verdict': 'correct'}, timestamp=stamp, decision_source='agreed_with_ai_suggestion', ai_basis='earlier_passes'),
    ]
    path = put(fixture_root, 'private/basis.json', json.dumps(data))
    summary, _ = ingest_review(path, fixture_root)
    assert 'agreed with earlier AI passes: 1; agreed with the 3-pass AI tie-break: 1' in summary.read_text()
    bad = json.loads(path.read_text())
    bad['results'][0]['decision_source'] = 'owner_manual'
    with pytest.raises(ValidationError, match='ai_basis only applies'):
        ReviewExport.model_validate(bad)
    bad['results'][0].update(decision_source='agreed_with_ai_suggestion', ai_basis='amended')
    with pytest.raises(ValidationError, match='Invalid ai_basis'):
        ReviewExport.model_validate(bad)


def frozen_corpus(root, text='Frozen corpus v1 wording only.'):
    """A frozen v1 corpus holding a passage id that the live corpus no longer has (as after the v2/v3 extraction rebuild)."""
    base = root / 'private/corpus-v1-frozen/data'
    (base / 'manifests').mkdir(parents=True)
    (base / 'processed').mkdir(parents=True)
    (base / 'manifests/manifest.json').write_text((root / 'data/manifests/manifest.json').read_text())
    (base / 'processed/observations.parquet').write_bytes((root / 'data/processed/observations.parquet').read_bytes())
    live = (root / 'data/passages/report.jsonl').read_text()
    old = json.loads(live)
    old.update(passage_id='report:p001:old', text=text)
    # The frozen corpus keeps the ids that still exist live (with their v1 text) plus the id the rebuild dropped.
    put(root, 'private/corpus-v1-frozen/data/passages/report.jsonl', live + '\n' + json.dumps(old))
    put(root, 'private/corpus-v1-frozen/data/passages/pdf.jsonl', (root / 'data/passages/pdf.jsonl').read_text())
    return base


def cite_old_id(root):
    runs = [json.loads(line) for line in (root / 'data/runs/agent-dev-A1/gpt-6-luna.jsonl').read_text().splitlines()]
    runs[0]['evidence'] = [{'label': 'P1', 'id': 'report:p001:old'}]
    runs[0]['answer']['claims'][0]['citations'][0]['label'] = 'P1'
    put(root, 'data/runs/agent-dev-A1/gpt-6-luna.jsonl', '\n'.join(json.dumps(r) for r in runs))
    sheet = root / 'docs/human-review/passage-spot-check.md'
    sheet.write_text(sheet.read_text().replace('`report:p001:test`', '`report:p001:old`', 1))


def test_old_ids_resolve_from_the_frozen_corpus_with_badges(fixture_root):
    frozen_corpus(fixture_root)
    cite_old_id(fixture_root)
    soup = BeautifulSoup(build_pack(fixture_root).read_text(), 'html.parser')
    answer = soup.select_one('#answers-DEV-001')
    assert 'Frozen corpus v1 wording only.' in answer.get_text()
    assert answer['data-corpus'] == 'corpus v1 (frozen run)'
    assert 'Evidence from corpus v1 (frozen run)' in answer.select_one('.corpus-badge').get_text()
    source = soup.select_one('#sources-passage-01')
    assert source['data-corpus'] == 'corpus v1 (frozen run)' and 'Frozen corpus v1 wording only.' in source.get_text()
    assert soup.select_one('#sources-passage-02')['data-corpus'] == 'corpus v1 (frozen run)'
    gold = soup.select_one('#gold-HO-001')
    assert gold['data-corpus'] == 'corpus v3' and 'Synthetic text' in gold.get_text()  # live corpus text, not the frozen wording
    assert 'Frozen corpus v1 wording only.' not in gold.get_text()
    assert 'gold evidence ids from corpus v3' in answer.select_one('details.gold summary').get_text()
    assert not soup.select('a[href^="file:"]')


def test_old_id_without_frozen_corpus_fails_strictly(fixture_root):
    cite_old_id(fixture_root)
    with pytest.raises(ValueError, match='Unresolved evidence ID in corpus v3: report:p001:old'):
        build_pack(fixture_root)


def test_ids_missing_from_every_corpus_still_fail(fixture_root):
    frozen_corpus(fixture_root)
    sheet = fixture_root / 'docs/human-review/passage-spot-check.md'
    sheet.write_text(sheet.read_text().replace('`report:p001:test`', '`report:p001:nowhere`', 1))
    with pytest.raises(ValueError, match=r'Unresolved evidence ID in corpus v1 \(frozen run\): report:p001:nowhere'):
        build_pack(fixture_root)


def test_gold_ids_must_exist_in_the_live_corpus_even_if_frozen_has_them(fixture_root):
    frozen_corpus(fixture_root)
    cases = [json.loads(line) for line in (fixture_root / 'experiments/gold/draft_cases.jsonl').read_text().splitlines()]
    next(c for c in cases if c['case_id'] == 'HO-001')['evidence_text'] = [{'passage_ids': ['report:p001:old']}]
    put(fixture_root, 'experiments/gold/draft_cases.jsonl', '\n'.join(json.dumps(c) for c in cases))
    with pytest.raises(ValueError, match='Unresolved evidence ID in corpus v3: report:p001:old'):
        build_pack(fixture_root)


def test_pack_id_ignores_corpus_changes(fixture_root):
    def pack_id(path):
        return re.search(r'const PACK_ID="([0-9a-f]+)"', path.read_text())[1]
    before = pack_id(build_pack(fixture_root))
    frozen_corpus(fixture_root)
    cite_old_id(fixture_root)
    assert pack_id(build_pack(fixture_root)) == before  # saved localStorage decisions are keyed by it


def test_reason_chips_stay_reachable_on_small_windows(fixture_root):
    """Regression: after 'Label is wrong' the behaviour chips sat under the fixed footer on short windows and could not be clicked."""
    page = build_pack(fixture_root).read_text()
    soup = BeautifulSoup(page, 'html.parser')
    chips = soup.select('#gold-HO-022 [data-chip=proposed_behavior]')
    assert [c['data-value'] for c in chips] == ['answer', 'abstain', 'refuse', 'clarify', 'ignore_injection_and_answer']
    assert [c.select_one('kbd').get_text() for c in chips] == ['1', '2', '3', '4', '5']
    # The visible chips are pinned above the footer (never inside the scrolled card) and the footer height is measured at runtime.
    assert '.card[data-pick-reason=true] .reason-chips{position:fixed' in page
    assert 'bottom:var(--nav-height' in page
    assert "setProperty('--nav-height'" in page
    assert "window.addEventListener('resize', update)" in page
    assert "goldLike(card) && card.dataset.pickReason === 'true'" in page  # number keys 1-5 pick the behaviour (gold and held-out v2 tabs)
    # Chips and the label button exist on a card whose AI passes all said 'label is wrong' (no Agree offered).
    assert soup.select_one('#gold-HO-022 [data-act=wrong]')
    assert not soup.select_one('#gold-HO-022 .agree-ai')


@pytest.mark.corpus
def test_real_pack():
    if not (ROOT / 'data/processed/observations.parquet').exists():
        pytest.skip('Local corpus unavailable')
    path = build_pack(ROOT)
    soup = BeautifulSoup(path.read_text(), 'html.parser')
    assert len(soup.select('article[data-tab=answers]')) == 40
    assert len(soup.select('article[data-tab=gold][data-case^=HO-]')) == 31
    assert len(soup.select('article[data-tab=sources]')) == 30
