"""Provenance integrity, idempotence, and rights packaging. Need fetched data and a prior `build`."""
import hashlib
import subprocess

import pandas as pd
import pytest

from labourlens import paths
from labourlens.data import build, raw_store

manifest = raw_store.load_manifest()
pytestmark = pytest.mark.skipif(not manifest, reason="run `labourlens fetch` first")


def test_every_ok_entry_has_matching_file_hash():
    bad = []
    for sid, e in manifest.items():
        if e.retrieval_status != "ok":
            continue
        f = paths.ROOT / e.raw_path
        if not f.exists():
            bad.append((sid, "missing"))
        elif hashlib.sha256(f.read_bytes()).hexdigest() != e.sha256:
            bad.append((sid, "hash"))
    assert not bad


def test_every_source_has_rights_status_and_url():
    for sid, e in manifest.items():
        assert e.rights_status and e.canonical_url.startswith("https://"), sid


def test_all_rights_reserved_sources_are_not_public():
    for sid, e in manifest.items():
        if e.rights_status == "verified_all_rights_reserved":
            assert e.redistribution_policy != "commit_ok", sid


def test_observation_ids_unique_and_every_obs_traces_to_a_manifest_snapshot():
    obs = pd.read_parquet(paths.PROCESSED / "observations.parquet")
    assert obs.observation_id.is_unique
    snaps = {e.snapshot_id for e in manifest.values()}
    assert set(obs.snapshot_id) <= snaps


def test_build_is_idempotent():
    a, qa, _ = build.build_observations()
    b, qb, _ = build.build_observations()
    pd.testing.assert_frame_equal(a, b)
    on_disk = pd.read_parquet(paths.PROCESSED / "observations.parquet")
    assert list(on_disk.observation_id) == list(a.observation_id)


def _visible_to_git() -> list[str]:
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=paths.ROOT, capture_output=True, text=True, check=True)
    return out.stdout.splitlines()


def test_no_pdfs_or_mom_text_visible_to_git():
    files = _visible_to_git()
    assert files, "git returned no files"
    # web/ holds the application's own static pages, not fetched source pages.
    leaks = [f for f in files if (f.lower().endswith((".pdf", ".html", ".htm")) and not f.startswith("web/")) or f.startswith(("data/raw/", "data/passages/", "study/", "private/"))]
    assert not leaks


def test_only_open_licence_datasets_are_in_snapshots_dir():
    for f in _visible_to_git():
        if f.startswith("data/snapshots/") and f.endswith(".csv"):
            sid = f.split("/")[2]
            assert manifest[sid].source_type == "dataset_csv" and manifest[sid].rights_status == "verified_open_licence", f
