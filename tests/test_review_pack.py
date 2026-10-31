"""Corpus-free pack/export checks plus explicitly marked real-corpus coverage."""
import json
import subprocess
from pathlib import Path

import pandas as pd
import pytest
import pymupdf
import re
from bs4 import BeautifulSoup
from pydantic import ValidationError

from labourlens.review.pack import EXTRA, ROOT, ReviewExport, build_pack, endorsement_statement, ingest_review


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
    assert '0/1 comparable' in summary.read_text()
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
    assert '## Independent human review' in text
    assert '## Owner-endorsed AI review (no independent per-item review)' in text
    assert endorsement_statement(2) in text
    assert '1/1 comparable independent owner verdicts' in text
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


@pytest.mark.corpus
def test_real_pack():
    if not (ROOT / 'data/processed/observations.parquet').exists():
        pytest.skip('Local corpus unavailable')
    path = build_pack(ROOT)
    soup = BeautifulSoup(path.read_text(), 'html.parser')
    assert len(soup.select('article[data-tab=answers]')) == 40
    assert len(soup.select('article[data-tab=gold][data-case^=HO-]')) == 31
    assert len(soup.select('article[data-tab=sources]')) == 30
