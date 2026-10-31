"""Official-source acquisition with throttling, retries, host allow-listing and signed-URL redaction.

Rules (see docs/decisions.md D-001, D-004, ADR-003):
- Only allow-listed hosts are contacted. A redirect to any other host fails the request.
- Signed download URLs (data.gov.sg -> S3) carry security tokens. The query string is dropped before
  anything is logged or written to a manifest.
- data.gov.sg allows 5 requests per minute without an API key. Requests to that host are spaced.
- Raw bytes are never modified. Snapshot identity is the SHA-256 of the exact bytes.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse, urlunparse

import httpx

USER_AGENT = "labourlens-research/0.1 (take-home assessment; read-only public data)"
ALLOWED_HOSTS = {
    "api-open.data.gov.sg",
    "api-production.data.gov.sg",
    "data.gov.sg",
    "stats.mom.gov.sg",
    "www.mom.gov.sg",
    "isomer-user-content.by.gov.sg",  # MTI PDFs (corpus v3 batch); the www.mti.gov.sg page host is deliberately not allowed
}
S3_HOST = "s3.ap-southeast-1.amazonaws.com"
S3_PATH_PREFIX = "/table-downloads-ingest.data.gov.sg/"
DGS_MIN_INTERVAL_S = 13.0  # 5 requests/minute => at least 12 s; margin added
MAX_CSV_BYTES = 50 * 1024 * 1024
MAX_DOC_BYTES = 100 * 1024 * 1024
MAX_RETRIES = 3
TIMEOUT_S = 60.0


class AcquisitionError(Exception):
    """Raised for any failure that should be recorded in the manifest, never swallowed."""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def redact_url(url: str) -> str:
    p = urlparse(url)
    return urlunparse((p.scheme, p.netloc, p.path, "", "", ""))


def _check_host(url: str) -> None:
    p = urlparse(url)
    if p.scheme != "https":
        raise AcquisitionError(f"non-https URL refused: {redact_url(url)}")
    if p.netloc in ALLOWED_HOSTS:
        return
    if p.netloc == S3_HOST and ("/" + p.path.lstrip("/")).startswith(S3_PATH_PREFIX):
        return
    raise AcquisitionError(f"host not on allow-list: {p.netloc}")


@dataclass
class Fetched:
    content: bytes
    final_url_redacted: str
    content_type: str | None
    status: int


class Fetcher:
    def __init__(self) -> None:
        self._client = httpx.Client(
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT_S,
            follow_redirects=False,
        )
        self._last_dgs_call = 0.0

    def close(self) -> None:
        self._client.close()

    def _throttle(self, url: str) -> None:
        if urlparse(url).netloc == "api-open.data.gov.sg":
            wait = DGS_MIN_INTERVAL_S - (time.monotonic() - self._last_dgs_call)
            if wait > 0:
                time.sleep(wait)
            self._last_dgs_call = time.monotonic()

    def get(self, url: str, *, max_bytes: int, accept: str | None = None) -> Fetched:
        """GET with manual redirect handling (every hop is host-checked), retries and a size cap."""
        last_err: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                current = url
                for _hop in range(5):
                    _check_host(current)
                    self._throttle(current)
                    headers = {"Accept": accept} if accept else {}
                    with self._client.stream("GET", current, headers=headers) as r:
                        if r.status_code in (301, 302, 303, 307, 308):
                            loc = r.headers.get("location")
                            if not loc:
                                raise AcquisitionError("redirect without Location header")
                            current = str(httpx.URL(current).join(loc))
                            continue
                        if r.status_code == 429 or r.status_code >= 500:
                            raise AcquisitionError(f"HTTP {r.status_code} from {redact_url(current)}")
                        if r.status_code != 200 and r.status_code != 201:
                            # Non-retryable client error: fail immediately with a clear reason.
                            raise _NonRetryable(f"HTTP {r.status_code} from {redact_url(current)}")
                        buf = bytearray()
                        for chunk in r.iter_bytes():
                            buf.extend(chunk)
                            if len(buf) > max_bytes:
                                raise _NonRetryable(f"response exceeds size cap {max_bytes} bytes")
                        return Fetched(bytes(buf), redact_url(current), r.headers.get("content-type"), r.status_code)
                raise AcquisitionError("too many redirects")
            except _NonRetryable as e:
                raise AcquisitionError(str(e)) from e
            except (AcquisitionError, httpx.HTTPError) as e:
                last_err = e
                time.sleep(min(30, 5 * attempt) if "429" in str(e) else 2 * attempt)
        raise AcquisitionError(f"failed after {MAX_RETRIES} attempts: {last_err}")


class _NonRetryable(Exception):
    pass


def fetch_dataset_csv(fetcher: Fetcher, dataset_id: str) -> Fetched:
    """Documented two-step flow: initiate-download, then poll-download until the signed URL is ready."""
    base = f"https://api-open.data.gov.sg/v1/public/api/datasets/{dataset_id}"
    fetcher.get(f"{base}/initiate-download", max_bytes=1_000_000)
    signed_url: str | None = None
    for _ in range(6):
        r = fetcher.get(f"{base}/poll-download", max_bytes=1_000_000)
        import json

        try:
            body = json.loads(r.content)
        except ValueError as e:
            raise AcquisitionError(f"poll-download returned non-JSON for {dataset_id}") from e
        data = body.get("data") or {}
        if data.get("status") == "DOWNLOAD_SUCCESS" and data.get("url"):
            signed_url = data["url"]
            break
        if body.get("code") not in (0, None) or data.get("status") in ("FAILED", "ERROR"):
            raise AcquisitionError(f"poll-download reported failure for {dataset_id}: {data.get('status')}")
    if not signed_url:
        raise AcquisitionError(f"download not ready after polling for {dataset_id}")
    return fetcher.get(signed_url, max_bytes=MAX_CSV_BYTES)


def fetch_dataset_metadata(fetcher: Fetcher, dataset_id: str) -> Fetched:
    return fetcher.get(
        f"https://api-production.data.gov.sg/v2/public/api/datasets/{dataset_id}/metadata",
        max_bytes=2_000_000,
    )


def fetch_document(fetcher: Fetcher, url: str) -> Fetched:
    return fetcher.get(url, max_bytes=MAX_DOC_BYTES)
