"""Offline tests of the served (tool_set annual) answer-evidence budget. Synthetic passages only; no model, key or network."""
from types import SimpleNamespace

from labourlens.agent import graph
from labourlens.agent.graph import SERVED_REPORT_PASSAGE_BUDGET, _SelectedTools, answer_evidence
from labourlens.agent.tools import Shared, Tools
from labourlens.answer.context import ContextPassage


def passage(n: int, source: str, text: str | None = None, stage: str = "final", label: str | None = None) -> ContextPassage:
    return ContextPassage(label or f"P{n}", f"{source}:p{n}", source, "t", None, stage, f"p.{n}", text or f"unique text {source} {n}")


def test_cap_is_total_across_rounds_and_keeps_numeric_items():
    items = [passage(i, f"s{i % 5}") for i in range(1, 41)]
    items.insert(3, ContextPassage("O1", "obs", "stat", "t", None, "final", "o", "rate 1"))
    items.append(ContextPassage("C1", "calc", "stat", "t", None, "calculated", "c", "diff 2"))
    kept = answer_evidence(items, "annual", {})
    assert sum(1 for i in kept if i.label.startswith("P")) == SERVED_REPORT_PASSAGE_BUDGET == 20
    assert {"O1", "C1"} <= {i.label for i in kept}
    assert [i.label for i in kept] == [i.label for i in items if i in kept]  # registry order and labels are preserved


def test_duplicate_id_and_same_release_text_dropped_but_independent_releases_kept():
    a = passage(1, "mom-2026-q2-final", "Same  words")
    dup_id = ContextPassage("P2", a.passage_id, a.source_id, "t", None, "final", "p.1", "Same words")
    dup_text = passage(3, "mom-2026-q2-final", "same words")
    advance = passage(4, "mom-2026-q2-advance", "Same words", stage="advance")
    kept = answer_evidence([a, dup_id, dup_text, advance], "annual", {})
    assert [i.label for i in kept] == ["P1", "P4"]


def test_source_diversity_and_rank_order_without_scores():
    big = [passage(i, "big") for i in range(1, 31)]
    small = [passage(100 + i, f"other{i}") for i in range(4)]
    items = big + small
    ranks = {p.passage_id: (n, 0) for n, p in enumerate(items)}
    ranks[small[-1].passage_id] = (0, 0)  # best returned chunk, though registered last
    kept = answer_evidence(items, "annual", ranks)
    assert all(p in kept for p in small)  # the capped first pass reaches every source before overflow fills the budget
    assert sum(1 for i in kept if i.label.startswith("P")) == SERVED_REPORT_PASSAGE_BUDGET
    assert [i.label for i in kept if i.source_id == "big"] == [f"P{n}" for n in range(1, 17)]  # 8 capped + 8 overflow in rank order
    # with room left nothing is withheld: one source below the budget keeps every passage
    few = [passage(i, "big") for i in range(1, 16)] + small[:1]
    filled = answer_evidence(few, "annual", {p.passage_id: (n, 0) for n, p in enumerate(few)})
    assert [i.label for i in filled if i.source_id == "big"] == [f"P{i}" for i in range(1, 16)]


def test_rank_decides_which_overflow_passages_survive():
    items = [passage(i, "one") for i in range(1, 31)]
    ranks = {p.passage_id: (30 - n, 0) for n, p in enumerate(items)}  # last registered passage is the best returned chunk
    kept = answer_evidence(items, "annual", ranks)
    assert {i.label for i in kept} == {f"P{n}" for n in range(11, 31)}


def test_legacy_modes_return_the_registry_unchanged():
    items = [passage(i, "s") for i in range(1, 41)]
    for mode in ("base", "v2"):
        assert answer_evidence(items, mode, {}) is items


def test_report_ranks_keep_best_position_and_exist_only_for_annual():
    chunks = {"c1": SimpleNamespace(source_passage_ids=["a", "b"]), "c2": SimpleNamespace(source_passage_ids=["b", "c"])}
    passages = {k: dict(source_id="s", document_title="t", publication_date=None, release_stage="final", locator=k, text=f"text {k}") for k in "abc"}

    def run(tool_set):
        tools = Tools(Shared(world=(None, {}, {}), stats=SimpleNamespace(obs=None, titles={})))
        tools.tool_set = tool_set
        tools._search = lambda q, k: ([("c2", 0.0), ("c1", 0.0)], {}, {}, chunks, passages)
        assert tools.search_reports("2026-Q2 retrenchment reasons").ok
        return tools.report_ranks

    assert run("annual") == {"b": (0, 0), "c": (0, 1), "a": (1, 0)}
    assert run("base") == {}


def test_selected_view_exposes_selection_and_delegates_other_attributes():
    real = SimpleNamespace(items=[1, 2, 3], marker="registry")
    view = _SelectedTools(real, lambda: [real.items[0]])
    assert view.items == [1] and view.marker == "registry" and real.items == [1, 2, 3]


def test_graph_exposes_the_selector_constants():
    assert graph.SERVED_SOURCE_PASSAGE_CAP <= graph.SERVED_REPORT_PASSAGE_BUDGET
