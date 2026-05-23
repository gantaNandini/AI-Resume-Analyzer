"""
Sentence-transformer embedding generation.
Requirements: 8.1, 8.2
"""
from __future__ import annotations
import os
from functools import lru_cache
from sentence_transformers import SentenceTransformer
from services.nlp_pipeline.schemas import EmbeddingResult, PreprocessedDocument

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")


@lru_cache(maxsize=1)
def _load_model() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDING_MODEL)


def generate_embeddings(doc: PreprocessedDocument) -> EmbeddingResult:
    """
    Generate full-document and section-level embeddings.
    Returns EmbeddingResult with vectors as lists of floats.
    """
    model = _load_model()

    # Full document embedding
    full_vec = model.encode(doc.original_text, normalize_embeddings=True).tolist()

    # Section-level embeddings
    section_vecs: dict[str, list[float]] = {}
    for section_name, section_text in doc.sections.items():
        if section_text.strip():
            vec = model.encode(section_text, normalize_embeddings=True).tolist()
            section_vecs[section_name] = vec

    return EmbeddingResult(
        full_document=full_vec,
        sections=section_vecs,
        model_name=EMBEDDING_MODEL,
        dimensions=len(full_vec),
    )
