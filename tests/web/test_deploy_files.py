"""Static checks on the deployment files. No Docker, network, corpus or API key needed.

scripts/check-build-context.sh proves the real build context with Docker; these tests keep the files consistent.
"""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def lines(path):
    return [x.strip() for x in (ROOT / path).read_text().splitlines()]


def test_dockerignore_is_an_allow_list_that_never_includes_the_corpus():
    rules = [x for x in lines(".dockerignore") if x and not x.startswith("#")]
    assert rules[0] == "*"  # everything excluded first
    allowed = {r[1:] for r in rules if r.startswith("!")}
    assert allowed == {"pyproject.toml", "uv.lock", "src", "specs", "prompts", "web"}
    for needed in ("data", "**/*.pdf", "**/.env", "**/.env.*"):
        assert needed in rules
    assert rules.index("data") > max(i for i, r in enumerate(rules) if r.startswith("!"))  # re-excluded last


def test_dockerfile_never_copies_the_corpus_or_whole_context():
    for line in lines("Dockerfile"):
        if line.startswith("COPY") and "--from" not in line:
            sources = line.split()[1:-1]
            assert all(s not in {".", "./", "data", "./data"} and not s.startswith("data/") for s in sources), line
    text = (ROOT / "Dockerfile").read_text()
    assert "USER 10001:10001" in text and "HEALTHCHECK" in text and "uv sync --frozen" in text


def test_runtime_data_list_is_a_precise_data_only_list():
    entries = [x for x in lines("deploy/runtime-data.txt") if x and not x.startswith("#")]
    assert len(entries) == len(set(entries))
    for e in entries:
        assert e.startswith("data/") and ".." not in e and "*" not in e, e
        assert not e.lower().endswith((".pdf", ".html", ".htm")) and not e.startswith(("data/raw/", "data/runs/")), e
    assert "data/processed/observations.parquet" in entries
    assert "data/manifests/manifest.json" in entries
    assert any(e.startswith("data/passages/") and e.endswith(".jsonl") for e in entries)
    assert "data/index/embeddings/text-embedding-3-large/cache.npz" in entries


def test_upload_script_is_dry_run_by_default():
    text = (ROOT / "scripts/upload-corpus.sh").read_text()
    assert 'mode="--dry-run"' in text and '--go) mode=""' in text and "deploy/runtime-data.txt" in text


def test_compose_structure():
    compose = yaml.safe_load((ROOT / "deploy/docker-compose.yml").read_text())
    services = compose["services"]
    assert set(services) == {"app", "caddy", "mcp"}
    app, caddy, mcp = services["app"], services["caddy"], services["mcp"]
    assert "ports" not in app and "ports" not in mcp, "only Caddy may publish ports"
    assert sorted(caddy["ports"]) == ["443:443", "80:80"]
    for s in (app, caddy, mcp):
        assert s["restart"] == "unless-stopped" and s["read_only"] is True and s["cap_drop"] == ["ALL"]
        assert "mem_limit" in s
    assert mcp["profiles"] == ["mcp"] and mcp["network_mode"] == "service:app"
    assert "/srv/labourlens/data:/app/data" in app["volumes"]
    assert app["env_file"].endswith("/srv/labourlens/.env}")
    assert "OPENAI_API_KEY" not in yaml.safe_dump(mcp)
    # The app trusts forwarded headers only from Caddy's fixed address.
    caddy_ip = caddy["networks"]["edge"]["ipv4_address"]
    assert app["environment"]["LABOURLENS_FORWARDED_ALLOW_IPS"] == caddy_ip
    assert "*" not in caddy_ip


def test_caddyfile_forwards_a_single_replaced_client_address():
    text = (ROOT / "deploy/Caddyfile").read_text()
    assert "header_up X-Forwarded-For {remote_host}" in text
    assert "max_size" in text and "encode" in text
    assert "Content-Security-Policy" not in text  # the app owns the CSP


def test_workflow_structure():
    wf = yaml.safe_load((ROOT / ".github/workflows/deploy.yml").read_text())
    assert wf["permissions"] == {}
    assert wf["concurrency"]["cancel-in-progress"] is False
    jobs = wf["jobs"]
    assert set(jobs) == {"test", "build-push", "deploy"}
    assert set(jobs["deploy"]["needs"]) == {"test", "build-push"}
    assert jobs["build-push"]["needs"] == "test"
    for job in jobs.values():
        assert job["permissions"]
        for step in job["steps"]:
            uses = step.get("uses")
            if uses:  # every third-party action is pinned to a 40-character commit SHA
                assert len(uses.split("@")[1]) == 40, uses
    text = (ROOT / ".github/workflows/deploy.yml").read_text()
    for secret in ("DROPLET_HOST", "DROPLET_USER", "DROPLET_SSH_KEY", "DROPLET_KNOWN_HOSTS"):
        assert f"secrets.{secret}" in text
    assert "StrictHostKeyChecking yes" in text
