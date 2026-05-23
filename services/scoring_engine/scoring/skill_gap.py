"""
Skill gap detection.
Requirements: 11.1, 11.2, 11.3, 11.5
"""
from __future__ import annotations


def compute_skill_gap(resume_skills: dict, jd_skills: dict) -> dict:
    """
    Compute the set of JD skills missing from the resume.
    Returns: {required_missing, preferred_missing, full_coverage}
    """
    resume_names = {s["canonical_name"].lower() for s in resume_skills.get("skills", [])}
    jd_list = jd_skills.get("skills", [])

    required_missing: list[str] = []
    preferred_missing: list[str] = []

    # Sort by confidence descending so most prominent skills appear first
    sorted_jd = sorted(jd_list, key=lambda s: s.get("confidence", 0.0), reverse=True)

    for skill in sorted_jd:
        name = skill["canonical_name"]
        if name.lower() not in resume_names:
            classification = skill.get("classification", "general")
            if classification == "required":
                required_missing.append(name)
            else:
                preferred_missing.append(name)

    full_coverage = len(required_missing) == 0 and len(preferred_missing) == 0

    return {
        "required_missing": required_missing,
        "preferred_missing": preferred_missing,
        "full_coverage": full_coverage,
    }
