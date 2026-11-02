"""Offline regressions for the submission audit's code findings."""
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from labourlens import paths
from labourlens.data import rights_scan
from labourlens.evaluation import harness, paired
from labourlens.mcp import client
from labourlens.retrieval import evaluate, experiments, experiments_dense


def test_mcp_connect_is_single_flight(monkeypatch):
    instances = []

    class FakeClient:
        def __init__(self, *args):
            self.closed = False
            instances.append(self)

        async def __aenter__(self):
            await asyncio.sleep(0.03)
            return self

        async def __aexit__(self, *args):
            await asyncio.sleep(0.01)
            self.closed = True

    monkeypatch.setattr(client, "McpStatsClient", FakeClient)
    backend = client.SyncStatsBackend()
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(backend._run, backend._connect(), 3) for _ in range(2)]
            for future in futures:
                future.result()
        assert len(instances) == 1
        old = backend.client
        backend._drop()
        backend._run(backend._connect(), 3)
        assert old.closed
        assert len(instances) == 2
        replacement = backend.client
        # A late failure from a caller using the old session must not drop its replacement.
        backend._drop(old)
        assert backend.client is replacement
    finally:
        backend.close()
    assert all(instance.closed for instance in instances)


def test_rights_quote_across_passages_and_lines(tmp_path):
    corpus = tmp_path / "passages"
    corpus.mkdir()
    (corpus / "doc.jsonl").write_text("\n".join(json.dumps({"source_id": "doc", "text": text}) for text in
        ("alpha bravo charlie delta", "echo foxtrot golf hotel")) + "\n")
    shingles = rights_scan.build_shingles(corpus)
    assert rights_scan.scan_text("alpha bravo charlie delta\necho foxtrot golf hotel", shingles) == [(1, 8)]


def test_rights_does_not_join_documents(tmp_path):
    (tmp_path / "docs.jsonl").write_text("\n".join(json.dumps({"source_id": source, "text": text}) for source, text in
        (("a", "alpha bravo charlie delta"), ("b", "echo foxtrot golf hotel"))) + "\n")
    assert rights_scan.scan_text("alpha bravo charlie delta echo foxtrot golf hotel", rights_scan.build_shingles(tmp_path)) == []


@pytest.mark.parametrize("suffix", ["metrics.json", "cases.jsonl"])
def test_write_run_refuses_partial_existing_pair(tmp_path, monkeypatch, suffix):
    monkeypatch.setattr(paths, "EXPERIMENTS", tmp_path)
    directory = tmp_path / "runs" / "sample"
    directory.mkdir(parents=True)
    existing = directory / f"label.{suffix}"
    existing.write_text("preserved")
    result = {"config": {}, "metrics": {}, "rows": []}
    with pytest.raises(FileExistsError, match="--force"):
        evaluate.write_run("sample", "label", result)
    assert existing.read_text() == "preserved"
    evaluate.write_run("sample", "label", result, force=True)


@pytest.mark.parametrize("driver,prefix", [(experiments, "dev"), (experiments_dense, "dev-dense")])
@pytest.mark.parametrize("suffix", ["SUMMARY.md", "summary.json"])
def test_drivers_refuse_summary_before_loading_corpus(tmp_path, monkeypatch, driver, prefix, suffix):
    monkeypatch.setattr(paths, "EXPERIMENTS", tmp_path)
    directory = tmp_path / "runs"
    directory.mkdir()
    (directory / f"{prefix}-{suffix}").write_text("preserved")
    monkeypatch.setattr(driver.ck, "load_passages", lambda: pytest.fail("loaded corpus before output guard"))
    with pytest.raises(FileExistsError, match="--force"):
        driver.run()


@pytest.mark.parametrize("suffix", ["judgements.json", "cases.jsonl", "metrics.json", "report"])
def test_eval_refuses_existing_outputs_before_judging(tmp_path, monkeypatch, suffix):
    monkeypatch.setattr(paths, "DATA", tmp_path / "data")
    monkeypatch.setattr(paths, "EXPERIMENTS", tmp_path / "experiments")
    raw = paths.DATA / "runs" / "sample"
    raw.mkdir(parents=True)
    (raw / "m.jsonl").write_text("{}\n")
    pub = paths.EXPERIMENTS / "eval" / "sample"
    pub.mkdir(parents=True)
    destination = pub.parent / "sample-REPORT.md" if suffix == "report" else pub / f"m.{suffix}"
    destination.write_text("preserved")
    monkeypatch.setattr(harness.ev, "load_cases", lambda *args: [])
    with pytest.raises(FileExistsError, match="--force"):
        harness.run("sample", judge=False)
    assert destination.read_text() == "preserved"


def test_paired_refuses_existing_out_before_reading_arms(tmp_path):
    destination = tmp_path / "paired.json"
    destination.write_text("preserved")
    with pytest.raises(FileExistsError, match="--force"):
        paired.run(tmp_path / "absent-gold", "a", "b", ["m"], out=destination)
    assert destination.read_text() == "preserved"


def test_old_serve_finally_cannot_clear_replacement(monkeypatch):
    class FakeClient:
        def __init__(self, *args):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    monkeypatch.setattr(client, "McpStatsClient", FakeClient)
    backend = client.SyncStatsBackend()

    async def scenario():
        ready, stop = backend.loop.create_future(), asyncio.Event()
        task = asyncio.create_task(backend._serve(ready, stop))
        await ready
        replacement = object()
        backend.client = replacement
        stop.set()
        await task
        assert backend.client is replacement
        backend.client = None

    try:
        backend._run(scenario(), 3)
    finally:
        backend.close()


@pytest.mark.parametrize("driver,experiment,label", [
    (experiments, "dev-E1-chunking", "blocks"),
    (experiments_dense, "dev-dense-E7", "partial-winner"),
])
def test_driver_refuses_partial_pair_before_loading_corpus(tmp_path, monkeypatch, driver, experiment, label):
    monkeypatch.setattr(paths, "EXPERIMENTS", tmp_path)
    directory = tmp_path / "runs" / experiment
    directory.mkdir(parents=True)
    (directory / f"{label}.cases.jsonl").write_text("preserved")
    monkeypatch.setattr(driver.ck, "load_passages", lambda: pytest.fail("loaded corpus before guard"))
    with pytest.raises(FileExistsError, match="--force"):
        driver.run()


def test_paired_force_permits_replacement_but_preserves_gold_check(tmp_path, monkeypatch):
    gold = tmp_path / "gold.jsonl"
    gold.write_text("")
    destination = tmp_path / "paired.json"
    destination.write_text("preserved")
    with pytest.raises(paired.GoldMismatch):
        paired.run(gold, "absent", "also-absent", ["m"], out=destination, force=True)
    assert destination.read_text() == "preserved"
    monkeypatch.setattr(paired, "check_gold", lambda *args: None)
    result = paired.run(gold, "a", "b", [], out=destination, force=True)
    assert json.loads(destination.read_text()) == result


@pytest.mark.parametrize("command,module,arguments", [
    ("retrieval-exp", experiments, []),
    ("dense-exp", experiments_dense, []),
    ("eval", harness, ["--no-judge"]),
    ("paired", paired, ["--gold", "gold.jsonl", "--candidate", "a", "--baseline", "b", "--models", "m"]),
])
def test_force_flag_is_forwarded(command, module, arguments, monkeypatch):
    from labourlens.cli import main

    seen = []
    monkeypatch.setattr(module, "run", lambda *args, **kwargs: seen.append(kwargs) or {})
    assert main([command, *arguments, "--force"]) == 0
    assert len(seen) == 1
    assert seen[0]["force"] is True


def test_failed_mcp_startup_is_cleaned_before_concurrent_retry(monkeypatch):
    instances = []

    class FakeClient:
        def __init__(self, *args):
            self.closed = False
            instances.append(self)

        async def __aenter__(self):
            if len(instances) == 1:
                raise client.McpClientError("unavailable", "startup")
            await asyncio.sleep(0.01)
            return self

        async def __aexit__(self, *args):
            self.closed = True

    monkeypatch.setattr(client, "McpStatsClient", FakeClient)
    backend = client.SyncStatsBackend()
    try:
        with pytest.raises(client.McpClientError):
            backend._run(backend._connect(), 3)
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(backend._run, backend._connect(), 3) for _ in range(2)]
            connected = [future.result() for future in futures]
        assert len(instances) == 2
        assert connected[0] is connected[1] is instances[1]
    finally:
        backend.close()
    assert instances[1].closed
