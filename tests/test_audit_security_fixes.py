"""Regressions for JSONL integrity, bounded admission logging and private pseudonyms."""

import hashlib
import hmac
import json
import os
import stat
from concurrent.futures import ThreadPoolExecutor

import pytest

from labourlens.audit import log
from labourlens.mcp.redact import redact, redact_values
from labourlens.report import audit


@pytest.fixture
def audit_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(log, "AUDIT_DIR", tmp_path)
    monkeypatch.delenv("LABOURLENS_AUDIT_SALT", raising=False)
    monkeypatch.setattr(audit, "_sample_clients", set())
    monkeypatch.setattr(audit, "_sample_minute", -1)
    return tmp_path


def event(ip="203.0.113.7", route="/api/ask", **detail):
    audit.log_event("request_rejected", "private-session", ip,
                    {"route": route, "status": 401, "reason": "Unauthorized", **detail})


def events(directory):
    return [json.loads(line) for path in directory.glob("events-*.jsonl")
            for line in path.read_text().split("\n") if line]


def test_redacts_nested_values_without_changing_keys_or_types(monkeypatch):
    monkeypatch.setenv("EXAMPLE_API_KEY", "very-private-secret")
    original = {"very-private-secret": ["very-private-secret", {"token": 'token=abcdefgh"'}],
                "number": 12, "boolean": False, "null": None}
    result = redact_values(original)
    assert result == {"very-private-secret": ["[REDACTED_SECRET]", {"token": 'token=[REDACTED]"'}],
                      "number": 12, "boolean": False, "null": None}
    assert original["very-private-secret"][0] == "very-private-secret"
    assert json.loads(json.dumps(result)) == result


def test_short_extra_secrets_are_ignored():
    assert redact("demo and abcdefg", ["", "demo", "abcdefg"]) == "demo and abcdefg"
    assert redact("abcdefgh", ["abcdefgh"]) == "[REDACTED_SECRET]"
    assert redact_values({"demo": ["demo", "abcdefgh"]}, ["demo", "abcdefgh"]) == {
        "demo": ["demo", "[REDACTED_SECRET]"]}


def test_key_pattern_never_consumes_backslashes():
    assert redact(r'token=abcdefgh\"') == r'token=[REDACTED]\"'


@pytest.mark.parametrize("separator", ["\u2028", "\u2029", "\u0085"])
def test_writer_preserves_json_and_escapes_unicode_line_separators(audit_dir, separator):
    text = 'token=abcdefgh"' + separator + '{"outcome":"forged"}'
    log._append("runs-2026-10-30.jsonl", {"question": text, "nested": [text]})
    raw = (audit_dir / "runs-2026-10-30.jsonl").read_bytes()
    assert raw.isascii()
    assert raw.count(b"\n") == 1
    record = json.loads(raw)
    assert record["question"] == 'token=[REDACTED]"' + separator + '{"outcome":"forged"}'
    assert log.read_runs() == [record]


@pytest.mark.parametrize("separator", ["\u2028", "\u2029", "\u0085"])
def test_readers_handle_legacy_unicode_and_skip_corrupt_lines(audit_dir, separator):
    record = {"question": "before" + separator + '{"outcome":"forged"}'}
    content = json.dumps(record, ensure_ascii=False) + '\n{"truncated":\n[]\nnull\n\n' + json.dumps({"valid": True}) + "\n"
    (audit_dir / "runs-2026-10-30.jsonl").write_text(content)
    (audit_dir / "feedback.jsonl").write_text(content)
    before = log.corrupt_lines()
    assert log.read_runs() == [record, {"valid": True}]
    assert log.read_feedback() == [record, {"valid": True}]
    assert log.corrupt_lines() == before + 6


def test_environment_salt_is_hmac_key(audit_dir, monkeypatch):
    monkeypatch.setenv("LABOURLENS_AUDIT_SALT", "installation-private-key")
    expected = hmac.new(b"installation-private-key", b"203.0.113.7", hashlib.sha256).hexdigest()[:16]
    assert log.salted_hash("203.0.113.7") == expected
    assert log.salted_hash(None) is None
    assert not (audit_dir / "salt").exists()


def test_generated_salt_is_private_persistent_and_install_specific(audit_dir, monkeypatch):
    first = log.salted_hash("203.0.113.7")
    salt = (audit_dir / "salt").read_bytes()
    assert len(salt) == 32
    assert stat.S_IMODE((audit_dir / "salt").stat().st_mode) == 0o600
    assert first == hmac.new(salt, b"203.0.113.7", hashlib.sha256).hexdigest()[:16]
    assert log.salted_hash("203.0.113.7") == first
    monkeypatch.setattr(log, "AUDIT_DIR", audit_dir / "other-install")
    assert log.salted_hash("203.0.113.7") != first


def test_concurrent_salt_creation_is_stable(audit_dir):
    with ThreadPoolExecutor(max_workers=12) as workers:
        hashes = list(workers.map(log.salted_hash, ["203.0.113.7"] * 48))
    assert len(set(hashes)) == 1
    assert len((audit_dir / "salt").read_bytes()) == 32
    assert not list(audit_dir.glob(".salt-*"))


def test_concurrent_process_salt_winner_is_used(audit_dir, monkeypatch):
    winner = os.urandom(32)

    def competing_link(source, target):
        # Simulate another worker publishing its complete salt first.
        with open(target, "xb") as stream:
            stream.write(winner)
        raise FileExistsError

    monkeypatch.setattr(log.os, "link", competing_link)
    assert log.salted_hash("client") == hmac.new(winner, b"client", hashlib.sha256).hexdigest()[:16]
    assert (audit_dir / "salt").read_bytes() == winner
    assert stat.S_IMODE((audit_dir / "salt").stat().st_mode) == 0o600
    assert not list(audit_dir.glob(".salt-*"))


def test_invalid_salt_never_uses_public_fallback(audit_dir):
    (audit_dir / "salt").write_bytes(b"")
    with pytest.raises(ValueError, match="invalid audit salt"):
        log.salted_hash("203.0.113.7")
    event()
    assert events(audit_dir) == []


def test_unknown_routes_never_create_events_or_client_state(audit_dir):
    for index in range(20):
        event(route=f"/api/arbitrary-{index}")
    assert events(audit_dir) == []
    assert audit._sample_clients == set()
    assert not (audit_dir / "salt").exists()


def test_events_sample_by_hmac_client_per_minute(audit_dir, monkeypatch):
    monkeypatch.setattr(audit.time, "monotonic", lambda: 120.0)
    event()
    event(route="/api/login")
    event(ip="203.0.113.8")
    records = events(audit_dir)
    assert len(records) == 2
    assert records[0]["client"] == log.salted_hash("203.0.113.7")
    assert records[0]["session"] == log.salted_hash("private-session")
    assert "203.0.113.7" not in json.dumps(records)
    assert "private-session" not in json.dumps(records)
    monkeypatch.setattr(audit.time, "monotonic", lambda: 180.0)
    event()
    assert len(events(audit_dir)) == 3


def test_sampling_memory_is_bounded_without_eviction_bypass(audit_dir, monkeypatch):
    monkeypatch.setattr(audit.time, "monotonic", lambda: 120.0)
    monkeypatch.setattr(audit, "EVENT_MAX_CLIENTS", 3)
    for index in range(30):
        event(ip=f"203.0.113.{index}")
    event(ip="203.0.113.0")
    assert len(audit._sample_clients) == 3
    assert len(events(audit_dir)) == 3
    monkeypatch.setattr(audit.time, "monotonic", lambda: 180.0)
    event(ip="203.0.113.29")
    assert len(audit._sample_clients) == 1
    assert len(events(audit_dir)) == 4


def test_event_daily_size_cap_preserves_complete_jsonl(audit_dir, monkeypatch):
    monkeypatch.setattr(audit, "EVENT_MAX_BYTES", 1100)
    for index in range(30):
        event(ip=f"203.0.113.{index}")
    path = next(audit_dir.glob("events-*.jsonl"))
    assert 0 < path.stat().st_size <= 1100
    assert 0 < len(events(audit_dir)) < 30
    assert path.read_bytes().endswith(b"\n")


def test_event_details_are_whitelisted_and_length_bounded(audit_dir):
    event(reason="x" * 10000, token="private-token", question="private question")
    record = events(audit_dir)[0]
    assert set(record["detail"]) == {"route", "status", "reason"}
    assert len(record["detail"]["reason"]) == 160


def test_writer_failure_is_counted_and_event_failure_never_raises(audit_dir, monkeypatch):
    blocked = audit_dir / "not-a-directory"
    blocked.write_text("blocked")
    monkeypatch.setattr(log, "AUDIT_DIR", blocked)
    before = log.failures()
    log._append("runs-2026-10-30.jsonl", {"question": "test"})
    assert log.failures() == before + 1
    event()
    assert log.failures() == before + 2


def test_concurrent_writes_respect_cap_without_partial_records(audit_dir):
    def append(index):
        log._append("events-concurrent.jsonl", {"index": index}, max_bytes=200)

    with ThreadPoolExecutor(max_workers=8) as workers:
        list(workers.map(append, range(100)))
    path = audit_dir / "events-concurrent.jsonl"
    assert 0 < path.stat().st_size <= 200
    assert 0 < len(events(audit_dir)) < 100
    assert path.read_bytes().endswith(b"\n")


def test_feedback_salt_failure_is_counted_without_fallback(audit_dir):
    (audit_dir / "salt").write_bytes(b"invalid")
    before = log.failures()
    record = log.log_feedback("abc123", "down", session="private-session")
    assert record["session"] is None
    assert log.failures() == before + 1
    assert not (audit_dir / "feedback.jsonl").exists()


def test_sampling_state_is_scoped_to_audit_directory(audit_dir, monkeypatch):
    monkeypatch.setattr(audit.time, "monotonic", lambda: 120.0)
    event()
    assert len(events(audit_dir)) == 1
    other = audit_dir / "other-install"
    monkeypatch.setattr(log, "AUDIT_DIR", other)
    event()
    assert len(events(other)) == 1
    assert len(audit._sample_clients) == 1
