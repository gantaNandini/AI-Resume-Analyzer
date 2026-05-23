"""Skill coverage calculator. Requirements: 10.2, 11.1"""
from __future__ import annotations


def compute_skill_coverage(resume_skills: dict, jd_skills: dict) -> float:
    """Fraction of required JD skills present in resume skills."""
    jd_list = jd_skills.get("skills", [])
    required = [s for s in jd_list if s.get("classification") == "required"]
    if not required:
        return 1.0
    resume_names = {s["canonical_name"].lower() for s in resume_skills.get("skills", [])}
    matched = sum(1 for s in required if s["canonical_name"].lower() in resume_names)
    return matched / len(required)
