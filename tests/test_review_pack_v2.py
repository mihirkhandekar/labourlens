"""Held-out v2 tab of the review pack: corpus-free, synthetic fixtures only."""
import json

import pytest
from bs4 import BeautifulSoup
from pydantic import ValidationError

from labourlens.review.pack import ReviewExport, build_pack, endorsement_statement, ingest_review
from tests.test_review_pack import export_data, fixture_root, put  # noqa: F401  (pytest fixture re-export)


def v2_case(n, behaviour='answer', group='dataset_ulc'):
    return dict(case_id=f'HO-V2-{n:03}', split='heldout', family='factual_lookup', question=f'Synthetic v2 question {n}?',
                expected_behavior=behaviour, evidence_text=[{'source_id': 'report', 'passage_ids': ['report:p001:test'], 'locator': 'p.1', 'primary': True, 'why': 'x'}],
                evidence_data=[{'source_id': 'test', 'period': '2026-Q2', 'dimension': '', 'observation_ids': ['obs1']}],
                context_only_evidence_data=[{'source_id': 'test', 'period': '2026-Q2', 'dimension': '', 'observation_ids': ['obs1']}],
                reference_facts=['Synthetic fact'], calculation=None, abstain_reason=None, adversarial=None, difficulty_note='Synthetic v2',
                drafted_by='ai:test', reviewed_by=None, review_status='draft', source_group=group)


@pytest.fixture
def v2_root(fixture_root):  # noqa: F811
    put(fixture_root, 'experiments/gold/heldout_v2_draft.jsonl', '\n'.join(json.dumps(v2_case(n)) for n in (1, 2, 3)))
    return fixture_root


def test_tab_cards_and_navigation(v2_root):
    page = build_pack(v2_root).read_text()
    soup = BeautifulSoup(page, 'html.parser')
    cards = soup.select('article[data-tab=heldout2]')
    assert [c['data-case'] for c in cards] == ['HO-V2-001', 'HO-V2-002', 'HO-V2-003']
    assert soup.select_one('[data-open=heldout2]').get_text() == 'Held-out v2 (3)'
    assert soup.select_one('#tab-filter option[value=heldout2]')
    card = soup.select_one('#heldout2-HO-V2-001')
    assert card.select_one('.fast-actions [data-act=right]') and card.select_one('.fast-actions [data-act=wrong]') and card.select_one('.fast-actions [data-act=unsure]')
    assert not card.select_one('[data-act=agree]') and not card.select_one('.agree-ai')
    assert card['data-ai-status'] == 'none' and card['data-quick'] == 'false'
    assert 'No AI has reviewed' in card.select_one('.ai-box').get_text()
    assert card.select('[data-field=label]') and card.select('[data-field=proposed_behavior]')
    assert card.select_one('details.gold')
    assert 'source group: dataset_ulc' in card.get_text()
    assert len(soup.select('article[data-tab=gold][data-case^=HO-0]')) == 31  # original held-out tab unchanged
    assert not soup.select('[data-field][checked]')
    assert 'goldLike(card)' in page  # same Fast review behaviour as the gold tab


def test_pack_without_v2_file_is_unchanged(fixture_root):  # noqa: F811
    soup = BeautifulSoup(build_pack(fixture_root).read_text(), 'html.parser')
    assert not soup.select('article[data-tab=heldout2]') and not soup.select('[data-open=heldout2]')


def test_pack_id_is_unchanged_by_v2_cards(fixture_root):  # noqa: F811
    import re
    before = re.search(r'const PACK_ID="(\w+)"', build_pack(fixture_root).read_text()).group(1)
    put(fixture_root, 'experiments/gold/heldout_v2_draft.jsonl', json.dumps(v2_case(1)))
    after = re.search(r'const PACK_ID="(\w+)"', build_pack(fixture_root).read_text()).group(1)
    assert before == after  # saved browser decisions for the other tabs survive adding v2


def test_v2_cards_are_excluded_from_endorse_all(v2_root):
    page = build_pack(v2_root).read_text()
    assert "card.dataset.tab !== 'heldout2' && !hasIndependentInput(card)" in page


def ts():
    return '2026-10-31T00:00:00Z'


def test_schema_accepts_v2_results_but_rejects_endorsement_and_agreement():
    data = export_data()
    data['reviewer_name'] = 'Owner'
    data['results'] = [dict(case_id='HO-V2-001', tab='heldout2', fields={'label': 'OK', 'evidence': 'OK', 'facts': 'OK'}, timestamp=ts(), decision_source='owner_manual')]
    assert ReviewExport.model_validate(data).results[0].tab == 'heldout2'
    bad_id = json.loads(json.dumps(data))
    bad_id['results'][0]['case_id'] = 'HO-001'
    with pytest.raises(ValidationError, match='Invalid tab/case id'):
        ReviewExport.model_validate(bad_id)
    endorsed = json.loads(json.dumps(data))
    endorsed['results'][0].update(fields={}, endorsement='owner_endorsed_ai', decision_source='')
    endorsed['attestation'] = dict(reviewer_name='Owner', statement=endorsement_statement(1), timestamp=ts(), counts={'answers': 0, 'gold': 1, 'sources': 0, 'decisions': 0})
    with pytest.raises(ValidationError, match='no AI review'):
        ReviewExport.model_validate(endorsed)
    agreed = json.loads(json.dumps(data))
    agreed['results'][0].update(decision_source='agreed_with_ai_suggestion', ai_basis='earlier_passes')
    with pytest.raises(ValidationError, match='no AI suggestion'):
        ReviewExport.model_validate(agreed)


def test_ingest_summarises_v2_separately_and_writes_separate_proposals(v2_root):
    data = export_data()
    data['reviewer_name'] = 'Owner'
    data['results'] = [
        dict(case_id='HO-V2-001', tab='heldout2', fields={'label': 'OK', 'evidence': 'OK', 'facts': 'issue'}, timestamp=ts(), decision_source='owner_manual'),
        dict(case_id='HO-V2-002', tab='heldout2', fields={'label': 'disagree', 'proposed_behavior': 'clarify'}, timestamp=ts(), decision_source='owner_manual'),
    ]
    path = put(v2_root, 'private/v2.json', json.dumps(data))
    gold = (v2_root / 'experiments/gold/heldout_v2_draft.jsonl').read_bytes()
    summary, proposal = ingest_review(path, v2_root)
    text = summary.read_text()
    assert 'Held-out v2' in text and "heldout2 / label: {'OK': 1, 'disagree': 1}" in text
    assert '| HO-V2-002 | answer | clarify |' in text
    assert proposal.read_text() == ''  # original held-out proposals stay untouched by v2
    v2 = [json.loads(line) for line in (v2_root / 'experiments/gold/proposed_label_changes_heldout_v2.jsonl').read_text().splitlines()]
    assert v2[0]['case_id'] == 'HO-V2-002' and v2[0]['status'] == 'proposed_not_applied'
    assert (v2_root / 'experiments/gold/heldout_v2_draft.jsonl').read_bytes() == gold  # ingestion never edits gold


def test_ingest_rejects_unknown_v2_case_and_incomplete_disagreement(v2_root):
    data = export_data()
    data['reviewer_name'] = 'Owner'
    data['results'] = [dict(case_id='HO-V2-099', tab='heldout2', fields={'label': 'OK'}, timestamp=ts(), decision_source='owner_manual')]
    with pytest.raises(ValueError, match='not in review pack'):
        ingest_review(put(v2_root, 'private/unknown.json', json.dumps(data)), v2_root)
    data['results'] = [dict(case_id='HO-V2-001', tab='heldout2', fields={'label': 'disagree'}, timestamp=ts(), decision_source='owner_manual')]
    with pytest.raises(ValueError, match='complete the proposed'):
        ingest_review(put(v2_root, 'private/incomplete.json', json.dumps(data)), v2_root)
