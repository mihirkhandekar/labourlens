"""Local/production single-worker server entry point."""
import os

from labourlens import paths

DEFAULT_FORWARDED_ALLOW_IPS = "127.0.0.1"


def forwarded_allow_ips() -> str:
    """Addresses whose X-Forwarded-For / X-Forwarded-Proto the server believes.

    Default: loopback only. A container deployment sets LABOURLENS_FORWARDED_ALLOW_IPS to the fixed address of its one
    reverse proxy (comma-separated IPs or CIDR networks). Never use '*': a client could then choose its own rate-limit key.
    """
    value = os.environ.get("LABOURLENS_FORWARDED_ALLOW_IPS", "").strip() or DEFAULT_FORWARDED_ALLOW_IPS
    if "*" in value:
        raise SystemExit("LABOURLENS_FORWARDED_ALLOW_IPS must list the proxy address; '*' is refused")
    return value


def run(host: str = "127.0.0.1", port: int = 8000):
    # Preserve externally supplied secrets and never print dotenv content.
    from dotenv import load_dotenv
    import uvicorn
    from labourlens.mcp.redact import RedactingFilter
    import logging

    load_dotenv(paths.ROOT / ".env", override=False)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(name).addFilter(RedactingFilter())
    from labourlens.report.app import create_app
    trusted_proxies = forwarded_allow_ips()
    logging.getLogger("uvicorn.error").warning("Trusted proxy headers enabled for: %s", trusted_proxies)
    uvicorn.run(create_app(), host=host, port=port, workers=1, access_log=False, proxy_headers=True,
                forwarded_allow_ips=trusted_proxies)
