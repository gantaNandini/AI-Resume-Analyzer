"""Formatting signal detector. Requirements: 10.2"""
from __future__ import annotations
import re

SECTION_HEADERS = ["experience", "education", "skills", "summary", "objective", "projects", "certifications"]
BULLET_PATTERNS = [r"^\s*[-•*]\s+", r"^\s*\d+\.\s+"]


def compute_formatting_score(raw_text: str) -> float:
    """Score 0.0–1.0 based on formatting signals present in the resume text."""
    signals = 0
    total_signals = 5
    lower = raw_text.lower()

    # 1. Section headers present
    headers_found = sum(1 for h in SECTION_HEADERS if h in lower)
    if headers_found >= 3:
        signals += 1

    # 2. Bullet points used
    lines = raw_text.split("\n")
    bullet_lines = sum(1 for line in lines if any(re.match(p, line) for p in BULLET_PATTERNS))
    if bullet_lines >= 3:
        signals += 1

    # 3. Reasonable line length (not all very long lines)
    non_empty = [l for l in lines if l.strip()]
    if non_empty:
        avg_len = sum(len(l) for l in non_empty) / len(non_empty)
        if 20 <= avg_len <= 120:
            signals += 1

    # 4. Has contact-like info (email pattern)
    if re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", raw_text):
        signals += 1

    # 5. Reasonable total length
    word_count = len(raw_text.split())
    if 100 <= word_count <= 2000:
        signals += 1

    return signals / total_signals
