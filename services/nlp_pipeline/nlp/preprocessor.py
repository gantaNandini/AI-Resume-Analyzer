"""
NLP preprocessing: tokenize, lemmatize, NER, section detection.
Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
"""
from __future__ import annotations

import os
import re
from functools import lru_cache

import spacy

from services.nlp_pipeline.schemas import Entity, PreprocessedDocument

SPACY_MODEL = os.getenv("SPACY_MODEL", "en_core_web_lg")

SECTION_KEYWORDS = {
    "experience", "work experience", "employment", "professional experience",
    "education", "academic background", "qualifications",
    "skills", "technical skills", "core competencies", "expertise",
    "summary", "objective", "profile", "about",
    "projects", "certifications", "awards", "publications",
    "languages", "interests", "references",
}

RELEVANT_NER_LABELS = {"ORG", "PRODUCT", "GPE", "PERSON", "WORK_OF_ART", "FAC"}


@lru_cache(maxsize=1)
def _load_nlp():
    try:
        return spacy.load(SPACY_MODEL)
    except OSError:
        # Fallback to small model if large not available
        return spacy.load("en_core_web_sm")


def _detect_sections(text: str) -> dict[str, str]:
    """Detect section boundaries by scanning for heading-like lines."""
    sections: dict[str, str] = {}
    current_section = "general"
    current_lines: list[str] = []

    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            current_lines.append("")
            continue

        # Heading detection: short line, all-caps or matches known keywords
        is_heading = (
            len(stripped) < 60
            and (
                stripped.upper() == stripped
                or stripped.lower().rstrip(":") in SECTION_KEYWORDS
                or any(kw in stripped.lower() for kw in SECTION_KEYWORDS)
            )
        )

        if is_heading and len(stripped) > 2:
            # Save previous section
            if current_lines:
                sections[current_section] = "\n".join(current_lines).strip()
            current_section = stripped.lower().rstrip(":").strip()
            current_lines = []
        else:
            current_lines.append(stripped)

    if current_lines:
        sections[current_section] = "\n".join(current_lines).strip()

    return sections


def preprocess(text: str, document_type: str = "resume", job_id: str = "") -> PreprocessedDocument:
    """
    Full NLP preprocessing pipeline.
    Returns tokens (lemmatized, no stop words), entities, sections, original text.
    """
    nlp = _load_nlp()

    # Truncate to ~10k words for performance
    words = text.split()
    if len(words) > 10_000:
        text = " ".join(words[:10_000])

    doc = nlp(text)

    # Tokens: lowercase, no stop words, no punctuation, lemmatized
    tokens = [
        token.lemma_.lower()
        for token in doc
        if not token.is_stop
        and not token.is_punct
        and not token.is_space
        and len(token.text.strip()) > 1
    ]

    # Named entities
    entities = [
        Entity(
            text=ent.text,
            label=ent.label_,
            start=ent.start_char,
            end=ent.end_char,
        )
        for ent in doc.ents
        if ent.label_ in RELEVANT_NER_LABELS
    ]

    sections = _detect_sections(text)

    return PreprocessedDocument(
        tokens=tokens,
        entities=entities,
        sections=sections,
        original_text=text,
        document_type=document_type,
        job_id=job_id,
    )
