"""Data contracts for Milestone 1.

Three records carry all provenance:
  SourceManifestEntry   one per acquired source file (dataset CSV, report PDF, release HTML)
  StatisticalObservation one validated number with unit, population, adjustment and lineage
  DocumentPassage       one citable block of document text with a real locator

Everything here is a plain pydantic model so it can be validated, serialised to JSON/Parquet and
re-read by later milestones without importing pipeline code.
"""

from __future__ import annotations

import hashlib
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "m1.1"
TRANSFORMATION_VERSION = "norm-0.1"
PARSER_VERSION = "extract-0.2"

SourceType = Literal["dataset_csv", "report_pdf", "release_html"]
ReleaseStage = Literal["advance", "final", "dataset_snapshot", "annual", "not_applicable"]
RightsStatus = Literal[
    "verified_open_licence",
    "verified_all_rights_reserved",
    "unresolved",
]
RetrievalStatus = Literal["ok", "failed", "skipped", "manual"]
Unit = Literal["percent", "ratio", "persons", "vacancies", "percentage_points", "per_thousand"]
Population = Literal[
    "resident", "citizen", "overall", "employees", "establishments", "not_applicable", "unverified_basis"
]
Adjustment = Literal["seasonally_adjusted", "not_adjusted", "not_applicable", "unspecified"]
QualityFlag = Literal["ok", "garbled", "table_unreliable", "multicolumn_uncertain", "empty"]


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class SourceManifestEntry(_Frozen):
    source_id: str
    source_type: SourceType
    title: str
    publisher: str
    canonical_url: str
    access_url_redacted: str | None = None  # signed query strings are always stripped
    access_method: Literal["api", "direct_http", "manual"] = "direct_http"
    publication_date: str | None = None  # ISO date, as stated by the publisher
    retrieval_utc: str | None = None
    reporting_period_start: str | None = None
    reporting_period_end: str | None = None
    release_stage: ReleaseStage = "not_applicable"
    licence_id: str | None = None
    licence_url: str | None = None
    rights_status: RightsStatus = "unresolved"
    rights_note: str = ""
    redistribution_policy: Literal["commit_raw", "local_only", "unresolved"] = "unresolved"
    snapshot_id: str | None = None
    sha256: str | None = None
    byte_count: int | None = None
    mime_type: str | None = None
    raw_path: str | None = None  # relative path under repo root
    retrieval_status: RetrievalStatus = "skipped"
    failure_reason: str | None = None
    notes: str = ""
    schema_version: str = SCHEMA_VERSION


class StatisticalObservation(_Frozen):
    observation_id: str
    source_id: str
    snapshot_id: str
    source_locator: str  # e.g. "row=137;col=jv_to_ue" or "row=Total Changes In Employment;col=20262Q"
    indicator_id: str
    period: str  # YYYY-Qn
    period_start: str
    period_end: str
    source_period_raw: str
    value: float | None
    raw_value: str
    missing_reason: str | None = None
    unit: Unit
    population: Population
    adjustment: Adjustment
    dimension: str = ""  # e.g. industry or sector label; "" when none
    sector_path: str = ""  # "A > B > C" for hierarchical tables
    sector_level: int | None = None
    release_stage: ReleaseStage = "dataset_snapshot"
    in_answer_scope: bool
    transformation_version: str = TRANSFORMATION_VERSION


class DocumentPassage(_Frozen):
    passage_id: str
    source_id: str
    snapshot_id: str
    original_url: str
    document_title: str
    publication_date: str | None
    release_stage: ReleaseStage
    page_number: int | None  # 1-based PDF page; None for HTML
    printed_page_label: str | None = None
    section_heading: str = ""
    block_index: int
    bbox: tuple[float, float, float, float] | None = None
    text: str
    text_sha256: str
    extraction_method: str
    quality_flag: QualityFlag = "ok"
    quality_note: str = ""
    raw_text_sha256: str | None = None
    transformations: tuple[str, ...] = ()
    source_block_indices: tuple[int, ...] = ()
    context_required: bool = False
    dup_group: str | None = None
    locator: str  # human-readable: "p.12" or "section: Main Findings, para 3"
    parser_version: str = PARSER_VERSION
    rights_status: RightsStatus = "unresolved"
    commit_text: bool = Field(default=False, description="True only if rights allow committing this text")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_id(*parts: object, length: int = 16) -> str:
    """Deterministic ID from ordered parts. Parts are joined with an unambiguous separator."""
    joined = "\x1f".join("" if p is None else str(p) for p in parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:length]
