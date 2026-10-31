"""Corpus-free pack/export checks plus explicitly marked real-corpus coverage."""
import json
import subprocess
from pathlib import Path

import pandas as pd
import pytest
from bs4 import BeautifulSoup
from pydantic import ValidationError

from labourlens.review.pack import EXTRA, ROOT, ReviewExport, build_pack, ingest_review


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
    put(tmp_path, 'data/raw/report/s1/report.html', '<p>Synthetic report</p>')
    manifest = [dict(source_id='test', snapshot_id='s1', title='Synthetic statistics', raw_path='data/snapshots/test/s1/raw.csv', canonical_url='https://data.gov.sg/synthetic'), dict(source_id='report', snapshot_id='s1', title='Synthetic report', raw_path='data/raw/report/s1/report.html')]
    put(tmp_path, 'data/manifests/manifest.json', json.dumps({'entries': manifest}))
    observation = dict(observation_id='obs1', source_id='test', snapshot_id='s1', source_locator='csv_row=2;col=value', indicator_id='unemployment', dimension='', period='2026-Q2', value=2.9, unit='percent', release_stage='final')
    (tmp_path / 'data/processed').mkdir()
    pd.DataFrame([observation]).to_parquet(tmp_path / 'data/processed/observations.parquet')
    passage = dict(passage_id='report:p001:test', source_id='report', snapshot_id='s1', document_title='Synthetic report', page_number=1, original_url='https://www.mom.gov.sg/synthetic', text='Synthetic text <script>attack()</script>', release_stage='final')
    put(tmp_path, 'data/passages/report.jsonl', json.dumps(passage))
    sample = [f'DEV-{n:03}' for n in range(1, 41)]
    cases = []
    for cid in sample + [f'HO-{n:03}' for n in range(1, 32)] + [c for c in EXTRA if c not in sample]:
        cases.append(dict(case_id=cid, question='What was the resident rate in Q2 2026?', family='factual_lookup', expected_behavior='answer', evidence_text=[{'passage_ids': ['report:p001:test']}], evidence_data=[{'observation_ids': ['obs1']}], reference_facts=['Synthetic 2.9%'], difficulty_note='Synthetic lookup'))
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
    assert len(soup.select('[data-check]')) == 12
    assert not soup.select('[src],link,iframe,img,form')
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
    assert 'file://' in path.read_text()


def test_export_schema():
    assert ReviewExport.model_validate(export_data()).reviewer_name == ''
    invalid = export_data()
    invalid['results'][0]['fields']['verdict'] = 'automatic pass'
    with pytest.raises(ValidationError):
        ReviewExport.model_validate(invalid)
    invalid = export_data()
    invalid['results'][0]['fields'] = {'label': 'disagree'}
    with pytest.raises(ValidationError):
        ReviewExport.model_validate(invalid)


def test_ingest_requires_owner_and_excludes_private_comments(fixture_root):
    data = export_data()
    file = put(fixture_root, 'private/export.json', json.dumps(data))
    with pytest.raises(ValueError, match='Reviewer name'):
        ingest_review(file, fixture_root)
    assert not (fixture_root / 'docs/human-review/owner-review-summary.md').exists()
    data['reviewer_name'] = 'Synthetic human'
    data['results'].append(dict(case_id='HO-001', tab='gold', fields={'label': 'disagree', 'proposed_behavior': 'clarify', 'comment': 'Shareable owner explanation', 'shareable': True}, timestamp='2026-10-31T00:00:00Z'))
    file.write_text(json.dumps(data))
    gold = (fixture_root / 'experiments/gold/draft_cases.jsonl').read_bytes()
    summary, proposal = ingest_review(file, fixture_root)
    assert 'private excerpt' not in summary.read_text()
    assert 'Synthetic text' not in summary.read_text()
    assert 'Synthetic human' in summary.read_text()
    assert 'Shareable owner explanation' in summary.read_text()
    assert '0/1 comparable' in summary.read_text()
    assert json.loads(proposal.read_text())['proposed_behavior'] == 'clarify'
    assert (fixture_root / 'experiments/gold/draft_cases.jsonl').read_bytes() == gold


def test_private_output_guard(fixture_root):
    (fixture_root / '.gitignore').write_text('')
    with pytest.raises(ValueError, match='gitignored'):
        build_pack(fixture_root)


@pytest.mark.corpus
def test_real_pack():
    if not (ROOT / 'data/processed/observations.parquet').exists():
        pytest.skip('Local corpus unavailable')
    path = build_pack(ROOT)
    soup = BeautifulSoup(path.read_text(), 'html.parser')
    assert len(soup.select('article[data-tab=answers]')) == 40
    assert len(soup.select('article[data-tab=gold][data-case^=HO-]')) == 31
    assert len(soup.select('article[data-tab=sources]')) == 30
