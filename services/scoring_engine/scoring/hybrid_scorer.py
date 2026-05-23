"""
Hybrid similarity combiner: 60% semantic + 40% TF-IDF.
Requirements: 9.3, 9.5
"""
from __future__ import annotations
import numpy as np


def compute_hybrid_similarity(semantic_score: float, tfidf_score: float) -> float:
    """Weighted combination clamped to [0.0, 1.0]. Requirements: 9.3, 9.5"""
    hybrid = 0.60 * semantic_score + 0.40 * tfidf_score
    return float(np.clip(hybrid, 0.0, 1.0))
