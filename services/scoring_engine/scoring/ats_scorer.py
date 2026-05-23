"""
ATS score computation.
Requirements: 10.1, 10.2, 10.3
"""
from __future__ import annotations
import numpy as np


def compute_ats_score(
    hybrid_similarity: float,
    keyword_density: float,
    skill_coverage: float,
    formatting_score: float,
) -> int:
    """
    Weighted ATS score formula:
      40% hybrid_similarity + 25% keyword_density + 25% skill_coverage + 10% formatting
    Returns integer in [0, 100].
    """
    raw = (
        0.40 * hybrid_similarity
        + 0.25 * keyword_density
        + 0.25 * skill_coverage
        + 0.10 * formatting_score
    )
    score = int(round(float(np.clip(raw * 100, 0, 100))))
    return score


def classify_score(score: int) -> str:
    """Classify ATS score into band. Requirements: 10.3"""
    if score >= 75:
        return "Strong"
    elif score >= 50:
        return "Fair"
    return "Poor"
