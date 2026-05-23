"""Pydantic schemas for LLM Service."""
from __future__ import annotations
from pydantic import BaseModel


class Suggestion(BaseModel):
    title: str
    explanation: str
    example: str


class SuggestionRequest(BaseModel):
    ats_result: dict
    skill_gap: dict = {}
    resume_text: str
    jd_text: str


class SuggestionResult(BaseModel):
    suggestions: list[Suggestion]
    available: bool
    error: str | None = None
