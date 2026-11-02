"""Transport parity for the agent's tools (D-066): each tool gives the same ToolResult in process and over MCP.

Offline: a small fixture corpus (tests/mcp/agent_fixture.py) with fake embeddings, the committed observations table, a fake chat client. No key, no
network, no data/passages. Protocol tests start the fixture as a real stdio server. Tests marked `corpus` use the real index and cached vectors.
"""

import base64
import json
from pathlib import Path

import numpy as np
import pytest

import agent_fixture as fx
from labourlens.agent import graph
from labourlens.agent.graph import AgentConfig, run_agent
from labourlens.agent.served import MCP_ALL_ROUTED
from labourlens.agent.tools import Shared, StatsData, ToolResult, Tools
from labourlens.answer import llm
from labourlens.mcp import agent_tools as at
from labourlens.mcp.analysis import AnalysisError
from labourlens.mcp.client import ALLOWED_SERVERS, SyncStatsBackend, ToolReply, screen_result
from labourlens.mcp.models import AGENT_RESULT_MODELS
from labourlens.mcp.server import AGENT_TOOLS, ALL_TOOLS
from labourlens.retrieval import dense, rerank

FIXTURE = Path(__file__).with_name("agent_fixture.py")
STATS = {"source_id": "retrenched_employees", "period_from": "2026-Q1", "period_to": "2026-Q2"}
QUERIES = [("resident unemployment rate", "What was the resident unemployment rate in 2Q 2026?"),
           ("retrenchments first quarter", ""),
           ("employment growth 1Q 2026 final report", "Compare the advance release with the final report"),
           ("job vacancies per unemployed person", "job vacancies"),
           ("wage growth", "")]


@pytest.fixture(scope="module")
def stats():
    return StatsData()


@pytest.fixture
def prompts(monkeypatch):
    """Fake embeddings and a fake rerank/chat client that records the prompts it saw."""
    seen = []

    def chat(model, messages, max_completion_tokens=6000, **kwargs):
        seen.append((kwargs.get("schema_name"), messages[-1]["content"]))
        if kwargs.get("schema_name") == "rerank":
            return llm.LLMResult('{"ranking": ["C3", "C1", "C2"]}', 100, 20, 0, 0.02)
        pytest.fail(f"unexpected model call {kwargs.get('schema_name')}")

    monkeypatch.setattr(dense, "embed", fx.fake_embed)
    monkeypatch.setattr(llm, "chat", chat)
    return seen


class Loopback:
    """The MCP hop without a process: server logic, a JSON round trip through the result model, then the client's screening."""

    def __init__(self, world, stats):
        self.world, self.stats, self.calls = world, stats, []

    def query(self, *args):
        return self.stats.query(*args)

    def invoke(self, tool, **args):
        self.calls.append(tool)
        try:
            if tool == "search_reports":
                res = at.search_reports(self.world, args["query"], args.get("question", ""), args.get("retrieval", "r3"), args.get("k", 8), args["query_vector_b64"])
            elif tool == "calculate_change":
                res = at.calculate_change(self.stats, args["observation_id_a"], args["observation_id_b"], args.get("kind", "difference"))
            else:
                res = at.calculate_from_text_values(self.world, args["passage_a"], args.get("passage_id_a"), args["value_a"], args["unit_a"], args["basis_a"],
                                                    args["period_a"], args["passage_b"], args.get("passage_id_b"), args["value_b"], args["unit_b"], args["basis_b"],
                                                    args["period_b"], args.get("kind", "difference"))
        except AnalysisError as e:
            return None, ToolResult(False, message=e.message, error_kind=e.kind)
        clean, quarantined = screen_result(type(res).model_validate_json(res.model_dump_json()))
        return ToolReply(type(res).model_validate(clean), quarantined), None


def pair(stats, inject=False):
    """Two Tools over the same fixture: one in process, one routed over the loopback hop."""
    world = fx.build_world(inject)
    direct = Tools(Shared(world=world[:3], stats=stats), "r3")
    mcp_world = at.World(*world)
    sh = Shared(world=(None, {}, {}), stats=stats)
    sh.stats_backend, sh.mcp_routed = Loopback(mcp_world, stats), MCP_ALL_ROUTED
    return direct, Tools(sh, "r3"), sh


def view(r: ToolResult):
    trace = {k: v for k, v in r.retrieval_trace.items() if k != "rerank_seconds"}
    items = [(i.label, i.passage_id, i.source_id, i.title, i.published, i.stage, i.locator, i.text, i.flags) for i in r.items]
    return r.ok, r.error_kind, r.message, items, trace, r.usage and {k: v for k, v in r.usage.items() if k != "llm_seconds"}


@pytest.mark.parametrize("retrieval", ["r3", "r3w", "hybrid"])
def test_search_reports_gives_the_same_result_in_process_and_over_mcp(stats, prompts, retrieval):
    for query, question in QUERIES:
        direct, mcp, _ = pair(stats)
        direct.retrieval = mcp.retrieval = retrieval
        direct.question = mcp.question = question
        a, b = direct.search_reports(query, 5), mcp.search_reports(query, 5)
        assert view(a) == view(b), (retrieval, query)
        assert b.transport == "mcp" and a.transport is None
        assert a.ok and a.items
    rerank_prompts = [m for name, m in prompts if name == "rerank"]
    if retrieval != "hybrid":  # the model saw the same candidates in the same order on both routes
        assert rerank_prompts and rerank_prompts[0::2] == rerank_prompts[1::2]


def test_search_reports_argument_errors_are_typed_the_same_way(stats, prompts):
    direct, mcp, sh = pair(stats)
    for kwargs in ({"query": "", "k": 5}, {"query": "x" * 301, "k": 5}, {"query": "ok", "k": 0}, {"query": "ok", "k": 11}):
        a, b = direct.search_reports(**kwargs), mcp.search_reports(**kwargs)
        assert (a.ok, a.error_kind, a.message) == (b.ok, b.error_kind, b.message) and not a.ok
    assert sh.stats_backend.calls == []  # rejected before any MCP call


def test_a_chunk_text_is_sent_only_when_it_is_not_the_joined_passage_text(stats):
    retriever, chunks, passages, corpus = fx.build_world()
    world = at.World(retriever, chunks, passages, corpus)
    vector = base64.b64encode(fx.vec("resident unemployment rate").tobytes()).decode()
    reply = at.search_reports(world, "resident unemployment rate", "", "r3", 5, vector)
    assert reply.chunks and all(c.text is None for c in reply.chunks)  # derivable: not sent twice
    odd = next(iter(chunks.values()))
    chunks[odd.chunk_id] = odd.model_copy(update={"text": odd.text + " (a differing chunk text)"})
    reply = at.search_reports(at.World(retriever, chunks, passages, corpus), "resident unemployment rate", "", "r3", 10, vector)
    sent = {c.chunk_id: c.text for c in reply.chunks}
    assert sent[odd.chunk_id].endswith("(a differing chunk text)") and sum(t is not None for t in sent.values()) == 1


def test_server_rejects_a_bad_query_vector(stats):
    world = at.World(*fx.build_world())
    for bad in ("!!!", base64.b64encode(b"\x00" * 12).decode(), base64.b64encode((np.zeros(3072, dtype="<f4") + 1).tobytes()).decode(),
                base64.b64encode(np.full(3072, np.nan, dtype="<f4").tobytes()).decode()):
        with pytest.raises(AnalysisError) as e:
            at.search_reports(world, "unemployment", "", "r3", 5, bad)
        assert e.value.kind == "invalid_arguments"


def test_mcp_search_withholds_an_instruction_passage_and_says_so(stats, prompts):
    direct, mcp, _ = pair(stats, inject=True)
    a, b = direct.search_reports("advance estimates third quarter 2025", 10), mcp.search_reports("advance estimates third quarter 2025", 10)
    assert any(i.flags for i in a.items)  # in process the passage arrives flagged
    assert not any(i.flags for i in b.items) and "instruction" not in " ".join(i.text for i in b.items).lower()
    assert any("withheld by the MCP client" in n for n in mcp.notes)


def observations(tools, stats, **kw):
    r = tools.get_series(**{**STATS, **kw})
    assert r.ok
    return r


def test_get_series_and_calculate_change_match_including_every_refusal(stats, prompts):
    direct, mcp, sh = pair(stats)
    for tools in (direct, mcp):
        observations(tools, stats)
        observations(tools, stats, source_id="resident_unemployment_rate", period_from="2026-Q1", period_to="2026-Q2")
        observations(tools, stats, source_id="retrenched_by_industry", period_from="2024-Q3", period_to="2025-Q2", dimension="accommodation")
    assert direct._obs == mcp._obs
    acc = [o["label"] for o in direct._obs.values() if o["source_id"] == "retrenched_by_industry"]
    other = next(o["label"] for o in direct._obs.values() if o["source_id"] == "resident_unemployment_rate")
    assert any(o["value"] is None for o in direct._obs.values())  # the 2024-Q4 cell has no published number
    for kind in ("difference", "percent_change"):
        for pair_ in (("O1", "O2"), (acc[0], acc[2]), (acc[2], acc[3])):
            a, b = direct.calculate_change(*pair_, kind=kind), mcp.calculate_change(*pair_, kind=kind)
            assert view(a) == view(b) and a.ok and b.transport == "mcp" and a.transport is None, (pair_, kind)
    refusals = [("O1", "O1", "difference"), ("O1", "O2", "ratio"), ("O1", "O99", "difference"), ("O1", other, "difference"),
                (acc[0], acc[1], "difference"), (acc[1], acc[2], "percent_change")]
    for obs_a, obs_b, kind in refusals:
        a, b = direct.calculate_change(obs_a, obs_b, kind), mcp.calculate_change(obs_a, obs_b, kind)
        assert view(a) == view(b) and not a.ok, (obs_a, obs_b, kind)
    assert direct.calculate_change(acc[0], acc[1]).error_kind == "not_found" and "no published number" in direct.calculate_change(acc[0], acc[1]).message
    assert sh.stats_backend.calls.count("calculate_change") == 6 + 4  # an unknown label and a bad kind are refused before any MCP call


TEXT = dict(unit_a="percent", basis_a="resident unemployment rate", period_a="March 2026", unit_b="percent", basis_b="resident unemployment rate", period_b="June 2026")


def search_both(direct, mcp):
    for tools in (direct, mcp):
        tools.question = "resident unemployment rate"
        r = tools.search_reports("resident unemployment rate", 8)
        assert r.ok
    labels = {i.passage_id: i.label for i in direct.items}
    assert labels == {i.passage_id: i.label for i in mcp.items}
    return {i.text[:40]: i.label for i in direct.items}


def test_calculate_from_text_values_matches_including_every_refusal(stats, prompts):
    direct, mcp, _ = pair(stats)
    by = search_both(direct, mcp)
    a_label = next(v for k, v in by.items() if k.startswith("The resident unemployment rate was 2.9"))
    b_label = next(v for k, v in by.items() if k.startswith("The resident unemployment rate was 2.7"))
    direct.tool_set = mcp.tool_set = "v2"
    good = dict(passage_a=a_label, value_a="2.9", passage_b=b_label, value_b="2.7", **TEXT)
    for kind in ("difference", "percent_change"):
        a, b = direct.calculate_from_text_values(**good, kind=kind), mcp.calculate_from_text_values(**good, kind=kind)
        assert view(a) == view(b) and a.ok and b.transport == "mcp", kind
    bad = [dict(good, value_b="9.9"), dict(good, passage_b="P99"), dict(good, unit_b="dollars"), dict(good, basis_b="a different measure"),
           dict(good, value_a="two"), dict(good, unit_a="widgets", unit_b="widgets"), dict(good, passage_b=a_label, value_b="2.9", period_b="March 2026"),
           dict(good, basis_a=""), dict(good, kind="ratio"), dict(good, value_a="2.9 per cent")]
    for kwargs in bad:
        a, b = direct.calculate_from_text_values(**kwargs), mcp.calculate_from_text_values(**kwargs)
        assert view(a) == view(b) and not a.ok, kwargs


def test_the_transport_never_changes_the_evidence_ids_or_labels(stats, prompts):
    direct, mcp, _ = pair(stats)
    for tools in (direct, mcp):
        tools.search_reports("retrenchments", 4)
        observations(tools, stats)
        tools.calculate_change("O1", "O2")
    assert [(i.label, i.passage_id, i.text) for i in direct.items] == [(i.label, i.passage_id, i.text) for i in mcp.items]
    assert direct.notes == mcp.notes


# ---- the protocol: a real stdio server --------------------------------------------------------------------------------------------


def fixture_server(name, mode="", **spec):
    ALLOWED_SERVERS[name] = {**ALLOWED_SERVERS["labourlens-stats-agent"], "args": [str(FIXTURE)], "env": {"LABOURLENS_FIXTURE_MODE": mode}, **spec}
    return name


@pytest.fixture
def agent_backend(prompts):
    name = fixture_server("fixture-agent")
    backend = SyncStatsBackend(name, call_timeout_s=5.0)
    try:
        backend._run(backend._connect(), 90)
        yield backend
    finally:
        backend.close()
        ALLOWED_SERVERS.pop(name, None)


def mcp_shared(backend, stats):
    sh = Shared(world=(None, {}, {}), stats=stats)
    sh.stats_backend, sh.mcp_routed = backend, MCP_ALL_ROUTED
    return sh


def plans(*rounds):
    queue = list(rounds)

    def chat(model, messages, max_completion_tokens=6000, **kwargs):
        name = kwargs.get("schema_name")
        if name == "rerank":
            return llm.LLMResult('{"ranking": ["C1"]}', 10, 5, 0, 0.01)
        if name == "plan":
            calls = queue.pop(0) if queue else None
            plan = {"decision": "gather" if calls else "finish", "note": "n", "calls": calls or []}
            return llm.LLMResult(json.dumps(plan), 10, 5, 0, 0.01)
        return llm.LLMResult(json.dumps(dict(status="abstained", summary="", claims=[], caveats=[], clarification_question="", reason="Not enough evidence.")), 10, 5, 0, 0.01)
    return chat


def test_the_agent_trace_shows_transport_mcp_for_all_three_tools(agent_backend, stats, monkeypatch):
    sh = mcp_shared(agent_backend, stats)
    monkeypatch.setattr(dense, "embed", fx.fake_embed)
    monkeypatch.setattr(llm, "chat", plans(
        [{"tool": "search_reports", "query": "resident unemployment rate", "k": 5}, {"tool": "get_series", **STATS}],
        [{"tool": "calculate_change", "obs_a": "O1", "obs_b": "O2", "kind": "difference"}]))
    res = run_agent("What changed?", sh, AgentConfig(retrieval="r3"), save_trace=False)
    events = [e["detail"] for e in res["trace"] if e["node"] == "execute_tool"]
    assert [(d["tool"], d["transport"]) for d in events if d.get("transport")] == [("search_reports", "mcp"), ("get_series", "mcp"), ("calculate_change", "mcp")]
    assert all(e["event"] == "ok" for e in res["trace"] if e["node"] == "execute_tool")
    assert {c["tool"] for c in agent_backend.calls} == {"search_reports", "get_statistic", "calculate_change"}
    assert all("query_vector_b64" not in json.dumps(c) or c["arguments"]["query_vector_b64"] == "[omitted]" for c in agent_backend.calls)
    search = next(d for d in events if d["tool"] == "search_reports")
    assert search["hints"]["quarters"] == [] and search["reranked"] and "filtered_chunks" in search
    assert res["corpus"] is None or isinstance(res["corpus"], dict)


def test_a_direct_run_has_no_transport_marker(stats, monkeypatch):
    world = fx.build_world()
    sh = Shared(world=world[:3], stats=stats)
    monkeypatch.setattr(dense, "embed", fx.fake_embed)
    monkeypatch.setattr(llm, "chat", plans([{"tool": "search_reports", "query": "retrenchments", "k": 3}, {"tool": "get_series", **STATS}]))
    res = run_agent("q", sh, AgentConfig(retrieval="r3"), save_trace=False)
    assert all("transport" not in e["detail"] for e in res["trace"])


def test_server_exposes_the_agent_profile_only_when_asked(agent_backend):
    c = agent_backend.client
    assert set(AGENT_TOOLS) <= set(c.schemas) and set(c.schemas) == set(ALL_TOOLS) | set(AGENT_TOOLS) and c.ignored_tools == []
    assert set(AGENT_RESULT_MODELS) == set(AGENT_TOOLS)
    props = c.schemas["search_reports"]["properties"]
    assert "query_vector_b64" in props and "OPENAI_API_KEY" not in json.dumps(c.schemas)
    assert agent_backend.call_tool("describe_corpus").result.corpus.chunks == len(fx.build_world()[1])


def test_the_catalogue_says_the_agent_profile_serves_report_text(agent_backend):
    async def read():
        return await agent_backend.client.read_resource("labourlens://sources")
    cat = agent_backend._run(read(), 20)
    served = {d["source_id"]: d["text_served_by_this_server"] for d in cat["documents"]}
    assert served["mom-2026-q1-final"] is True and served["mom-2026-q2-final"] is False  # only documents with passages in the loaded corpus


def test_the_api_key_never_reaches_the_server_process(monkeypatch):
    from mcp.client.stdio import get_default_environment

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-a-real-key-000000000000")
    assert "OPENAI_API_KEY" not in get_default_environment()
    assert "env" not in ALLOWED_SERVERS["labourlens-stats-agent"] and "--agent-tools" in ALLOWED_SERVERS["labourlens-stats-agent"]["args"]
    assert "--agent-tools" not in ALLOWED_SERVERS["labourlens-stats"]["args"]


def test_search_over_stdio_matches_in_process(agent_backend, stats, prompts):
    direct = Tools(Shared(world=fx.build_world()[:3], stats=stats), "r3")
    mcp = Tools(mcp_shared(agent_backend, stats), "r3")
    for query, question in QUERIES[:3]:
        direct.question = mcp.question = question
        assert view(direct.search_reports(query, 5)) == view(mcp.search_reports(query, 5)), query
    assert {c["tool"] for c in agent_backend.calls} == {"search_reports"}


def test_a_slow_server_is_a_typed_operational_failure_and_never_falls_back_to_in_process(stats, monkeypatch):
    class Forbidden:
        def __getattr__(self, name):
            raise AssertionError("the in-process retriever must not be used")

    name = fixture_server("fixture-slow", "slow")
    backend = SyncStatsBackend(name, call_timeout_s=1.0)
    try:
        backend._run(backend._connect(), 90)
        sh = Shared(world=(Forbidden(), {}, {}), stats=stats)
        sh.stats_backend, sh.mcp_routed = backend, MCP_ALL_ROUTED
        monkeypatch.setattr(dense, "embed", fx.fake_embed)
        monkeypatch.setattr(llm, "chat", plans([{"tool": "search_reports", "query": "unemployment", "k": 3}]))
        res = run_agent("q", sh, AgentConfig(retrieval="r3", tool_timeout_s=10.0), save_trace=False)
        failures = [e["detail"] for e in res["trace"] if e["event"] == "operational_failure" and e["node"] == "execute_tool"]
        assert failures and failures[0]["transport"] == "mcp" and failures[0]["tool"] == "search_reports"
        assert res["outcome"] == "operational_failure" and res["evidence"] == []
        assert any(c["kind"] == "timeout" for c in backend.calls if not c["ok"])
    finally:
        backend.close()
        ALLOWED_SERVERS.pop(name, None)


def test_a_crashing_server_is_an_operational_failure_after_one_reconnect(stats, monkeypatch):
    name = fixture_server("fixture-crash", "crash")
    backend = SyncStatsBackend(name, call_timeout_s=3.0)
    try:
        backend._run(backend._connect(), 90)
        sh = mcp_shared(backend, stats)
        monkeypatch.setattr(dense, "embed", fx.fake_embed)
        monkeypatch.setattr(llm, "chat", plans([{"tool": "search_reports", "query": "unemployment", "k": 3}]))
        res = run_agent("q", sh, AgentConfig(retrieval="r3"), save_trace=False)
        assert res["outcome"] == "operational_failure"
        assert [c["attempt"] for c in backend.calls if c["tool"] == "search_reports"][:2] == [0, 1]  # one reconnect, then give up
    finally:
        backend.close()
        ALLOWED_SERVERS.pop(name, None)


def test_a_tool_error_from_the_server_is_a_correctable_tool_result_not_a_failure(agent_backend, stats, prompts):
    tools = Tools(mcp_shared(agent_backend, stats), "r3")
    r = tools.calculate_change("O1", "O2")  # no observations fetched in this run: refused locally, no MCP call
    assert not r.ok and r.error_kind == "invalid_arguments" and not agent_backend.calls and r.transport is None
    reply, err = agent_backend.invoke("calculate_change", observation_id_a="0" * 16, observation_id_b="1" * 16, kind="difference")
    assert reply is None and err.error_kind == "not_found"
    reply, err = agent_backend.invoke("search_reports", query="x", query_vector_b64="A" * 16384)
    assert reply is None and err.error_kind == "invalid_arguments"


def test_make_shared_mcp_all_keeps_the_corpus_out_of_this_process(monkeypatch):
    from labourlens.agent import served

    name = fixture_server("fixture-shared")
    monkeypatch.setattr(served, "AGENT_SERVER", name)
    sh = served.make_shared("mcp_all")
    try:
        assert sh.mcp_routed == MCP_ALL_ROUTED and sh.retriever is None and sh.chunks_by_id == {} and sh.passages_by_id == {}
        assert sh.corpus == fx.build_world()[3]
        assert sh.tool_transport == "mcp_all"
    finally:
        sh.stats_backend.close()
        ALLOWED_SERVERS.pop(name, None)


def test_make_shared_rejects_an_unknown_transport():
    from labourlens.agent import served

    with pytest.raises(ValueError):
        served.make_shared("mcp-everything")


def test_shared_limits_agree_between_the_server_and_the_in_process_tool():
    from labourlens.agent import tools as T
    from labourlens.mcp import models

    assert (models.MAX_QUERY_CHARS, models.MAX_K, models.MAX_QUESTION_CHARS) == (T.MAX_QUERY_CHARS, T.MAX_K, graph.MAX_QUESTION_CHARS)
    assert at.candidates.POOL == rerank.POOL
    assert models.VECTOR_B64_CHARS == 4 * -(-models.EMBEDDING_DIMENSION * 4 // 3)


# ---- the real corpus (opt-in: needs data/passages and the cached vectors) ---------------------------------------------------------


@pytest.mark.corpus
def test_the_server_world_equals_the_in_process_world():
    from labourlens.retrieval.runtime import corpus_fingerprint, load_search_world, load_world

    retr, chunks, passages = load_world()
    s_retr, s_chunks, s_passages, corpus = load_search_world()
    assert corpus == corpus_fingerprint(passages, chunks) and set(s_chunks) == set(chunks)
    assert np.array_equal(retr.dense.matrix, s_retr.dense.matrix)
    cited = {pid for c in chunks.values() for pid in c.source_passage_ids}
    assert set(s_passages) == cited and all(s_passages[p] == passages[p] for p in cited)
    for q in ("resident unemployment rate 2026", "retrenchment first quarter 2026", "advance release employment"):
        assert retr.bm25.search(q, 20) == s_retr.bm25.search(q, 20)


@pytest.mark.corpus
def test_real_corpus_search_matches_in_process_for_cached_query_vectors(monkeypatch):
    """Queries use chunk vectors that are already in the cache, so no embedding call is possible."""
    from labourlens.retrieval.runtime import load_world

    world = load_world()
    retr, chunks, _ = world
    ids = list(chunks)
    for n, (query, question) in enumerate(QUERIES):
        vector = retr.dense.matrix[(n * 397) % len(ids)]
        monkeypatch.setattr(dense, "embed", lambda model, texts, purpose, v=vector: np.vstack([v for _ in texts]))
        st = StatsData()
        direct = Tools(Shared(world=world, stats=st), "r3")
        sh = Shared(world=(None, {}, {}), stats=st)
        sh.stats_backend, sh.mcp_routed = Loopback(at.World(*load_search_world_cached()), st), MCP_ALL_ROUTED
        mcp = Tools(sh, "r3")
        direct.question = mcp.question = question
        monkeypatch.setattr(rerank, "rerank", lambda q, cands, **kw: rerank.RerankResult(list(range(len(cands))), 0.0, 0.0, ok=True))
        a, b = direct.search_reports(query, 8), mcp.search_reports(query, 8)
        assert [(i.passage_id, i.locator, i.stage) for i in a.items] == [(i.passage_id, i.locator, i.stage) for i in b.items], query
        assert a.retrieval_trace == b.retrieval_trace
        assert [i.text for i in a.items] == [i.text for i in b.items]  # NFKC-clean passages: the MCP client's sanitising changes nothing here or Tools._add already did


_CACHED = {}


def load_search_world_cached():
    from labourlens.retrieval.runtime import load_search_world

    if "w" not in _CACHED:
        _CACHED["w"] = load_search_world()
    return _CACHED["w"]
