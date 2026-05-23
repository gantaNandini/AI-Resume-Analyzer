"""Pydantic schemas for Scoring Engine."""
from __future__ import annotations
from pydantic import BaseModel


class ATSScoreRequest(BaseModel):
    resume_embedding: list[float]
    jd_embedding: list[float]
    resume_section_embeddings: dict[str, list[float]] = {}
    jd_section_embeddings: dict[str, list[float]] = {}
    resume_tokens: list[str]
    jd_tokens: list[str]
    resume_skills: dict
    jd_skills: dict
    resume_text: str = ""
    jd_text: str = ""


class ATSResult(BaseModel):
    score: int
    band: str
    hybrid_similarity: float
    section_scores: dict[str, float]
    keyword_density: float
    skill_coverage: float


class SkillGapRequest(BaseModel):
    resume_skills: dict
    jd_skills: dict


class SkillGapResult(BaseModel):
    required_missing: list[str]
    preferred_missing: list[str]
    full_coverage: bool
