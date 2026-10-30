"""Local/production single-worker server entry point."""
from labourlens import paths


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
    uvicorn.run(create_app(), host=host, port=port, workers=1, access_log=False, proxy_headers=True,
                forwarded_allow_ips="127.0.0.1")
