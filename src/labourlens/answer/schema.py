"""Structured answer contract (D-024). The same shape is sent to the model as a strict JSON schema and re-validated
here, because a model that follows a schema can still cite things it was never shown."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Status = Literal["answered", "abstained", "clarify", "refused"]


class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: str = Field(description="Passage label from the context, for example P3")
    quote: str = Field(description="Short verbatim excerpt (at most 40 words) from that passage supporting the claim")


class Claim(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str
    citations: list[Citation]


class Answer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Status
    summary: str
    claims: list[Claim]
    caveats: list[str]
    clarification_question: str
    reason: str


def json_schema() -> dict:
    """Strict-mode JSON schema for the OpenAI structured-outputs response_format."""
    cit = {"type": "object", "additionalProperties": False, "required": ["label", "quote"],
           "properties": {"label": {"type": "string"}, "quote": {"type": "string"}}}
    claim = {"type": "object", "additionalProperties": False, "required": ["text", "citations"],
             "properties": {"text": {"type": "string"}, "citations": {"type": "array", "items": cit}}}
    return {"type": "object", "additionalProperties": False,
            "required": ["status", "summary", "claims", "caveats", "clarification_question", "reason"],
            "properties": {
                "status": {"type": "string", "enum": ["answered", "abstained", "clarify", "refused"]},
                "summary": {"type": "string"},
                "claims": {"type": "array", "items": claim},
                "caveats": {"type": "array", "items": {"type": "string"}},
                "clarification_question": {"type": "string"},
                "reason": {"type": "string"}}}
