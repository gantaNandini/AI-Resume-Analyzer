"""
Cosine similarity scorer for semantic embeddings.
Requirements: 9.1, 9.4
"""
from __future__ import annotations
import numpy as np


def compute_cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Cosine similarity clamped to [0.0, 1.0]."""
    a = np.array(vec_a, dtype=np.float32)
    b = np.array(vec_b, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    score = float(np.dot(a, b) / (norm_a * norm_b))
    return float(np.clip(score, 0.0, 1.0))


def compute_section_similarities(
    resume_sections: dict[str, list[float]],
    jd_sections: dict[str, list[float]],
) -> dict[str, float]:
    """Compute cosine similarity for matching section names."""
    results: dict[str, float] = {}
    for section_name, jd_vec in jd_sections.items():
        # Try exact match first, then partial match
        resume_vec = resume_sections.get(section_name)
        if resume_vec is None:
            for key in resume_sections:
                if section_name.lower() in key.lower() or key.lower() in section_name.lower():
                    resume_vec = resume_sections[key]
                    break
        if resume_vec is not None:
            results[section_name] = compute_cosine_similarity(resume_vec, jd_vec)
    return results
