"""
TF-IDF keyword overlap scorer.
Requirements: 9.2
"""
from __future__ import annotations
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def compute_tfidf_score(resume_tokens: list[str], jd_tokens: list[str]) -> float:
    """TF-IDF cosine similarity between resume and JD token lists, clamped to [0.0, 1.0]."""
    if not resume_tokens or not jd_tokens:
        return 0.0
    resume_text = " ".join(resume_tokens)
    jd_text = " ".join(jd_tokens)
    try:
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([resume_text, jd_text])
        score = float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
        return float(np.clip(score, 0.0, 1.0))
    except Exception:
        return 0.0
