import pytest

from labourlens.retrieval import bm25_index as bi
from labourlens.retrieval.chunk import CONFIGS, ChunkConfig, build_chunks, corpus_hash
from labourlens.retrieval.tokenize import TokConfig, tokenize


def _p(sid, n, heading, words, flag="ok", page=1):
    return dict(passage_id=f"{sid}:{n}", source_id=sid, snapshot_id="s", original_url="https://x", document_title="t",
                publication_date="2026-01-01", release_stage="final", page_number=page, section_heading=heading,
                locator=f"p.{page}", text=" ".join(f"w{n}_{i}" for i in range(words)), quality_flag=flag, rights_status="unresolved")


PASSAGES = [_p("A", i, "H1" if i < 6 else "H2", 40, page=1 + i // 3) for i in range(10)] + [_p("B", i, "H1", 40) for i in range(4)] \
    + [_p("A", 99, "H1", 40, flag="table_unreliable"), _p("A", 98, "H1", 40, flag="garbled")]


@pytest.mark.parametrize("name", ["blocks", "merge120", "fixed150"])
def test_every_chunk_traces_to_real_passages(name):
    ids = {p["passage_id"] for p in PASSAGES}
    chunks = build_chunks(CONFIGS[name], PASSAGES)
    assert chunks
    for c in chunks:
        assert c.source_passage_ids and set(c.source_passage_ids) <= ids
        assert all(i.startswith(c.source_id + ":") for i in c.source_passage_ids)
        assert c.word_count == len(c.text.split())


def test_flagged_passages_are_not_retrieved_by_default():
    used = {i for c in build_chunks(CONFIGS["merge120"], PASSAGES) for i in c.source_passage_ids}
    assert "A:99" not in used and "A:98" not in used
    with_tables = ChunkConfig("t", "merge", 120, 30, include_flags=("ok", "table_unreliable"))
    assert "A:99" in {i for c in build_chunks(with_tables, PASSAGES) for i in c.source_passage_ids}


def test_merge_never_crosses_heading_or_source_and_every_passage_is_covered():
    chunks = build_chunks(CONFIGS["merge120"], PASSAGES)
    by_id = {p["passage_id"]: p for p in PASSAGES}
    for c in chunks:
        assert len({by_id[i]["section_heading"] for i in c.source_passage_ids}) == 1
    covered = {i for c in chunks for i in c.source_passage_ids}
    assert covered == {p["passage_id"] for p in PASSAGES if p["quality_flag"] == "ok"}


def test_merge_overlap_repeats_some_passage():
    short = [_p("A", i, "H1", 20) for i in range(12)]  # whole-passage overlap needs passages shorter than the overlap budget (30 words)
    chunks = build_chunks(CONFIGS["merge120"], short)
    first_two = [set(c.source_passage_ids) for c in chunks[:2]]
    assert first_two[0] & first_two[1]


def test_fixed_windows_have_fixed_size_and_chunk_ids_are_stable():
    a = build_chunks(CONFIGS["fixed150"], PASSAGES)
    b = build_chunks(CONFIGS["fixed150"], PASSAGES)
    assert [c.chunk_id for c in a] == [c.chunk_id for c in b]
    assert max(c.word_count for c in a) == 150 and sum(c.word_count == 150 for c in a) >= len(a) - 2  # last window of each source may be shorter


def test_chunk_ids_differ_across_configs():
    assert {c.chunk_id for c in build_chunks(CONFIGS["blocks"], PASSAGES)}.isdisjoint({c.chunk_id for c in build_chunks(CONFIGS["merge120"], PASSAGES)})


@pytest.mark.parametrize("phrase", ["second quarter of 2026", "2Q 2026", "Q2 2026", "2nd quarter 2026", "quarter 2 2026"])
def test_period_phrases_normalise_to_same_tokens(phrase):
    assert {"q2", "2026"} <= set(tokenize(phrase))


def test_period_normalisation_can_be_switched_off():
    assert "q2" not in tokenize("second quarter 2026", TokConfig(period_normalise=False))


def test_numbers_stay_whole_and_commas_removed():
    t = tokenize("Employment rose by 11,400 or 2.9 per cent")
    assert "11400" in t and "2.9" in t


def test_stemming_is_optional_and_leaves_numbers():
    assert tokenize("retrenched retrenchments", TokConfig(stem=True)) == ["retrench", "retrench"]
    assert tokenize("retrenched", TokConfig(stem=False)) == ["retrenched"]
    assert "2026" in tokenize("2026", TokConfig(stem=True))


def test_bm25s_matches_reference_formula():
    docs = [["a", "b", "b", "c"], ["c", "d"], ["a", "c", "e", "e", "e"], ["f"]]
    import bm25s

    r = bm25s.BM25(k1=1.3, b=0.6, method="lucene")
    r.index(docs, show_progress=False)
    ref = bi.reference_scores(docs, ["b", "e", "c"], 1.3, 0.6)
    ids, sc = r.retrieve([["b", "e", "c"]], k=4, show_progress=False)
    got = {int(i): float(s) for i, s in zip(ids[0], sc[0])}
    for i, s in enumerate(ref):
        assert got.get(i, 0.0) == pytest.approx(s, rel=1e-5)


def test_exact_term_ranks_first_and_index_roundtrips(tmp_path, monkeypatch):
    monkeypatch.setattr(bi.paths, "INDEX", tmp_path)
    ps = [_p("A", i, "H", 30) for i in range(6)]
    ps[3]["text"] += " retrenchment services"
    chunks = build_chunks(CONFIGS["blocks"], ps)
    idx = bi.BM25Index.build(chunks, bi.BM25Config())
    top = idx.search("retrenchment", 3)
    assert top[0][0] == chunks[3].chunk_id and len(top) == 1
    d = idx.save("blocks")
    again = bi.BM25Index.load(d, chunks)
    assert again.search("retrenchment", 3) == top


def test_stale_index_fails_loudly(tmp_path, monkeypatch):
    monkeypatch.setattr(bi.paths, "INDEX", tmp_path)
    ps = [_p("A", i, "H", 30) for i in range(4)]
    chunks = build_chunks(CONFIGS["blocks"], ps)
    d = bi.BM25Index.build(chunks, bi.BM25Config()).save("blocks")
    ps[0]["text"] += " edited"
    with pytest.raises(bi.StaleIndexError):
        bi.BM25Index.load(d, build_chunks(CONFIGS["blocks"], ps))
    assert corpus_hash(chunks) != corpus_hash(build_chunks(CONFIGS["blocks"], ps))


def test_no_hits_returns_empty_not_error():
    chunks = build_chunks(CONFIGS["blocks"], [_p("A", 0, "H", 20)])
    assert bi.BM25Index.build(chunks, bi.BM25Config()).search("zzzunseen", 5) == []
