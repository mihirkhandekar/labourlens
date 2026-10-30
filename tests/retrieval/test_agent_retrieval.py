"""Opt-in agent retrieval; all clients/data are fake and no network is used."""
import json
from types import SimpleNamespace

import pandas as pd
import pytest

from labourlens.agent.graph import AgentConfig, run_agent
from labourlens.agent.tools import Shared, Tools
from labourlens.answer import llm
from labourlens.audit.log import run_record
from labourlens.retrieval import rerank
from labourlens.retrieval.dense import HybridIndex, rrf


class Ranking:
    def __init__(self, rows):
        self.rows = rows
        self.requests = []

    def search(self, query, k):
        self.requests.append(k)
        return self.rows[:k]


@pytest.fixture
def world(monkeypatch, tmp_path):
    chunks, passages = {}, {}
    # Matching chunks occur below the initial candidate depth in both rankings.
    for i in range(70):
        sid = 'mom-2026-q2-advance' if i >= 55 else 'mom-2026-q1-final'
        chunks[str(i)] = SimpleNamespace(chunk_id=str(i), source_id=sid, source_passage_ids=[f'p{i}'],
                                        document_title=sid, publication_date='2026-07-30', release_stage='advance' if i >= 55 else 'final',
                                        locator='p.1', text=f'Employment evidence {i}')
        passages[f'p{i}'] = dict(passage_id=f'p{i}', source_id=sid, document_title=sid, publication_date='2026-07-30',
                                release_stage=chunks[str(i)].release_stage, locator='p.1', text=chunks[str(i)].text)
    bm = Ranking([(str(i), 100 - i) for i in range(70)])
    de = Ranking([(str(i), 1 - i / 100) for i in range(70)])
    stats = SimpleNamespace(obs=pd.DataFrame({'source_id': ['s'], 'indicator_id': ['i']}), titles={}, catalogue_text=lambda: '')
    sh = Shared(world=(HybridIndex(bm, de), chunks, passages), stats=stats)
    monkeypatch.setattr(rerank, 'CACHE_DIR', tmp_path)
    return sh


@pytest.fixture
def fake_client(monkeypatch):
    calls = []

    def chat(model, messages, max_completion_tokens=6000, **kwargs):
        calls.append((model, kwargs))
        if kwargs.get('schema_name') == 'rerank':
            return llm.LLMResult('{"ranking": ["C2", "C1"]}', 100, 20, 0, .02)
        if kwargs.get('schema_name') == 'plan':
            plans = sum(k.get('schema_name') == 'plan' for _, k in calls)
            plan = {'decision': 'gather' if plans == 1 else 'finish', 'note': 'search',
                    'calls': [{'tool': 'search_reports', 'query': 'employment growth', 'k': 8}] if plans == 1 else []}
            return llm.LLMResult(json.dumps(plan), 10, 5, 0, .01)
        return llm.LLMResult(json.dumps(dict(status='abstained', summary='', claims=[], caveats=[],
                                            clarification_question='', reason='Insufficient evidence.')), 10, 5, 0, .01)

    monkeypatch.setattr(llm, 'chat', chat)
    return calls


def test_default_ranking_and_output_match_old_path(world, monkeypatch):
    query = '2Q 2026 advance release employment growth'
    # This is the pre-change HybridIndex.search implementation, computed independently.
    old = rrf([world.retriever.bm25.search(query, 50), world.retriever.dense.search(query, 50)], 8, 60)
    monkeypatch.setattr(rerank, 'rerank', lambda *a, **k: pytest.fail('default called reranker'))
    result = Tools(world).search_reports(query)
    assert [p.passage_id for p in result.items] == [f'p{cid}' for cid, _ in old]
    assert result.message == '8 new passages from 1 documents: ' + ', '.join(f'P{i + 1}=mom-2026-q1-final' for i in range(8))
    assert result.retrieval_trace == {} and result.usage == {}


def test_r3_filters_both_full_rankings_and_reranks(world, fake_client):
    result = Tools(world, 'r3', question='What did the 2Q 2026 advance release say?').search_reports('employment growth')
    assert all(p.source_id == 'mom-2026-q2-advance' for p in result.items)
    assert result.items[0].passage_id == 'p56'
    assert world.retriever.bm25.requests == [70] and world.retriever.dense.requests == [70]
    assert result.retrieval_trace['hints'] == {'quarters': ['2026-Q2'], 'stage': 'advance', 'stage_conflict': False}
    assert result.retrieval_trace['filtered_documents'] == 1
    assert result.retrieval_trace['filtered_chunks'] == 15
    assert result.retrieval_trace['reranked'] and result.usage['cost_usd'] > 0
    assert fake_client[0][0] == 'gpt-6-luna' and 0 < fake_client[0][1]['timeout_s'] < 10


def test_union_hints_retains_both_quarters_and_drops_conflicting_stage(world, fake_client):
    r = Tools(world, 'r3', question='2Q 2026 advance release').search_reports('1Q 2026 final report')
    assert r.retrieval_trace['hints'] == {'quarters': ['2026-Q1', '2026-Q2'], 'stage': None, 'stage_conflict': True}
    assert r.retrieval_trace['filtered_documents'] == 2


@pytest.mark.parametrize('exception', [RuntimeError('down'), TimeoutError('expired')])
def test_reranker_exception_keeps_filtered_order(world, monkeypatch, exception):
    def fail(*a, **k):
        raise exception
    monkeypatch.setattr(rerank, 'rerank', fail)
    r = Tools(world, 'r3').search_reports('2Q 2026 advance release')
    assert [p.passage_id for p in r.items] == [f'p{i}' for i in range(55, 63)]
    assert r.ok and r.retrieval_trace['rerank_fallback'] and not r.retrieval_trace['reranked']


def test_r3w_small_pool_widens_but_r3_does_not(world, fake_client):
    # Keep only two matching chunks, without changing catalogue or rankings.
    for i in range(57, 70):
        world.chunks_by_id[str(i)].source_id = 'mom-2026-q1-final'
    r3 = Tools(world, 'r3').search_reports('2Q 2026 advance release')
    wide = Tools(world, 'r3w').search_reports('2Q 2026 advance release')
    assert len(r3.items) == 2 and not r3.retrieval_trace['widened']
    assert wide.retrieval_trace['widened'] and wide.retrieval_trace['filtered_chunks'] == 2
    assert wide.items[0].passage_id == 'p1'


def test_r3w_weak_lexical_score_widens(world, fake_client):
    # Fifteen matching chunks survive, but their best raw lexical score is 45 < 0.5 * 100.
    r = Tools(world, 'r3w').search_reports('2Q 2026 advance release')
    assert r.retrieval_trace['filtered_chunks'] == 15 and r.retrieval_trace['widened']


@pytest.mark.parametrize('query', ['employment growth', 'Q2 2035 advance release'])
def test_no_hint_or_no_matching_document_does_not_filter(world, fake_client, query):
    r = Tools(world, 'r3').search_reports(query)
    assert not r.retrieval_trace['filter_applied'] and r.items[0].passage_id == 'p1'


def test_run_usage_and_audit_include_rerank(world, fake_client):
    r = run_agent('2Q 2026 advance release employment growth?', world, AgentConfig(retrieval='r3'), save_trace=False)
    assert r['usage']['calls'] == 4  # two planner calls, rerank, answer
    assert r['usage']['prompt_tokens'] == 130 and r['usage']['completion_tokens'] == 35
    assert r['usage']['rerank_cost_usd'] > 0
    from labourlens import prices
    assert r['usage']['cost_usd'] == pytest.approx(prices.chat_cost('gpt-6-luna', 130, 35), abs=2e-6)
    search = next(e['detail'] for e in r['trace'] if e['node'] == 'execute_tool')
    assert search['hints']['quarters'] == ['2026-Q2'] and search['reranked']
    audit = run_record(r, 'test')
    assert audit['tool_calls'][0]['rerank_cost_usd'] == search['rerank_cost_usd']
    assert audit['tool_calls'][0]['hints'] == search['hints']


def test_default_is_r3_and_the_legacy_hybrid_key_is_unchanged():
    assert AgentConfig().retrieval == 'r3' and AgentConfig().key().endswith('|retrieval=r3')  # D-030
    assert AgentConfig(retrieval='hybrid').key() == 'planner=gpt-6-luna|answer=gpt-6-luna|planner_v1|answer_v3'  # keys of earlier runs stay valid
    with pytest.raises(ValueError):
        AgentConfig(retrieval='unknown')


def test_rerank_http_deadline_falls_back(world, monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'test-key')

    async def expired(*args):
        raise TimeoutError('deadline')

    monkeypatch.setattr(llm, '_bounded_post', expired)
    r = Tools(world, 'r3').search_reports('2Q 2026 advance release')
    assert r.ok and r.retrieval_trace['rerank_fallback']
    assert r.items[0].passage_id == 'p55'
