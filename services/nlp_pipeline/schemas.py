"""Pydantic schemas for NLP Pipeline service."""
from __future__ import annotations
from pydantic import BaseModel


class Entity(BaseModel):
    text: str
    label: str
    start: int
    end: int


class PreprocessedDocument(BaseModel):
    tokens: list[str]
    entities: list[Entity]
    sections: dict[str, str]
    original_text: str
    document_type: str
    job_id: str


class PreprocessRequest(BaseModel):
    text: str
    document_type: str  # "resume" | "jd"
    job_id: str


class SkillEntry(BaseModel):
    canonical_name: str
    confidence: float
    classification: str  # "required" | "preferred" | "general"


class SkillManifest(BaseModel):
    skills: list[SkillEntry]


class SkillExtractRequest(BaseModel):
    document: PreprocessedDocument
    document_type: str


class EmbedRequest(BaseModel):
    text: str
    job_id: str
    doc_type: str
    user_id: str
    sections: dict[str, str] = {}


class EmbeddingResult(BaseModel):
    full_document: list[float]
    sections: dict[str, list[float]]
    model_name: str
    dimensions: int
    cache_hit: bool = False
