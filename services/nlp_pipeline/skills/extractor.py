"""
Skill extraction with canonical taxonomy mapping and confidence scoring.
Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
"""
from __future__ import annotations
import re
from services.nlp_pipeline.schemas import PreprocessedDocument, SkillEntry, SkillManifest
from services.nlp_pipeline.skills.taxonomy import SKILL_TAXONOMY, canonicalize

REQUIRED_CONTEXT = {"required", "must have", "must-have", "mandatory", "essential", "need"}
PREFERRED_CONTEXT = {"preferred", "nice to have", "nice-to-have", "bonus", "plus", "desired", "ideally"}

_ALL_TAXONOMY_KEYS = list(SKILL_TAXONOMY.keys())


def _ngrams(tokens: list[str], n: int) -> list[str]:
    return [" ".join(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]


def _classify_from_context(text: str, skill: str) -> str:
    """Determine if a skill is required/preferred based on surrounding text."""
    lower = text.lower()
    idx = lower.find(skill.lower())
    if idx == -1:
        return "general"
    window = lower[max(0, idx - 120):idx + 120]
    if any(kw in window for kw in REQUIRED_CONTEXT):
        return "required"
    if any(kw in window for kw in PREFERRED_CONTEXT):
        return "preferred"
    return "general"


def extract_skills(doc: PreprocessedDocument, document_type: str) -> SkillManifest:
    """
    Extract skills from a preprocessed document.
    Uses token n-grams (1-3) matched against taxonomy.
    Assigns confidence: exact=1.0, NER-assisted=0.85, fuzzy=0.75
    """
    found: dict[str, SkillEntry] = {}  # canonical_name -> best entry
    tokens = doc.tokens
    original = doc.original_text

    # Check 1-grams, 2-grams, 3-grams
    for n in (1, 2, 3):
        for gram in _ngrams(tokens, n):
            canonical = canonicalize(gram)
            if canonical is None:
                continue
            # Determine confidence
            gram_lower = gram.lower()
            if gram_lower in {k.lower() for k in SKILL_TAXONOMY}:
                confidence = 1.0
            else:
                confidence = 0.75

            classification = "general"
            if document_type == "jd":
                classification = _classify_from_context(original, gram)

            existing = found.get(canonical)
            if existing is None or confidence > existing.confidence:
                found[canonical] = SkillEntry(
                    canonical_name=canonical,
                    confidence=confidence,
                    classification=classification,
                )

    # Also check NER entities
    for entity in doc.entities:
        canonical = canonicalize(entity.text)
        if canonical is None:
            continue
        confidence = 0.85
        classification = "general"
        if document_type == "jd":
            classification = _classify_from_context(original, entity.text)
        existing = found.get(canonical)
        if existing is None or confidence > existing.confidence:
            found[canonical] = SkillEntry(
                canonical_name=canonical,
                confidence=confidence,
                classification=classification,
            )

    return SkillManifest(skills=list(found.values()))
