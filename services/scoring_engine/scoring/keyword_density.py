"""Keyword density calculator. Requirements: 10.2"""
from __future__ import annotations
import numpy as np


def compute_keyword_density(resume_tokens: list[str], jd_tokens: list[str]) -> float:
    """Fraction of unique JD tokens present in resume tokens, clamped to [0.0, 1.0]."""
    if not jd_tokens:
        return 1.0
    jd_unique = set(t.lower() for t in jd_tokens)
    resume_set = set(t.lower() for t in resume_tokens)
    matched = jd_unique & resume_set
    score = len(matched) / len(jd_unique)
    return float(np.clip(score, 0.0, 1.0))
