"""
LLM-powered resume improvement suggestion generator.
Supports OpenAI and Groq (free) via OpenAI-compatible API.
Requirements: 12.1–12.6
"""
from __future__ import annotations
import asyncio
import json
import logging
import os
from typing import Any

from openai import AsyncOpenAI
from dotenv import load_dotenv

from services.llm_service.schemas import Suggestion, SuggestionResult

load_dotenv()

logger = logging.getLogger("llm_service")
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT_SECONDS", "30"))

# Auto-detect provider based on key prefix
_api_key = os.getenv("OPENAI_API_KEY", "")
_is_groq = _api_key.startswith("gsk_")

if _is_groq:
    # Groq — free, OpenAI-compatible
    LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    _client = AsyncOpenAI(
        api_key=_api_key,
        base_url="https://api.groq.com/openai/v1",
    )
    logger.info("Using Groq LLM provider")
else:
    # OpenAI
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
    _client = AsyncOpenAI(api_key=_api_key)
    logger.info("Using OpenAI LLM provider")


def _build_prompt(
    ats_score: int,
    required_missing: list[str],
    preferred_missing: list[str],
    section_scores: dict,
    resume_text: str,
    jd_text: str,
) -> list[dict[str, str]]:
    system_msg = (
        "You are an expert resume coach and ATS optimization specialist. "
        "Analyze the resume against the job description and provide specific, actionable improvement suggestions. "
        "IMPORTANT: Do NOT reproduce verbatim content from the resume or job description. "
        "Return ONLY a valid JSON array (no markdown, no code blocks) of suggestion objects. "
        "Each object must have exactly three fields: "
        "'title' (short label), 'explanation' (1-2 sentences), 'example' (concrete recommended change). "
        f"Provide between 3 and 10 suggestions. "
        + ("Include at least one suggestion about keyword optimization for ATS parsing. " if ats_score < 50 else "")
    )

    user_msg = f"""ATS Score: {ats_score}/100
Required skills missing from resume: {', '.join(required_missing) if required_missing else 'None'}
Preferred skills missing: {', '.join(preferred_missing) if preferred_missing else 'None'}
Section similarity scores: {json.dumps(section_scores)}

RESUME (truncated):
{resume_text[:3000]}

JOB DESCRIPTION (truncated):
{jd_text[:2000]}

Provide 3-10 specific improvement suggestions as a JSON array."""

    return [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]


async def generate_suggestions(
    ats_score: int,
    skill_gap: dict,
    section_scores: dict,
    resume_text: str,
    jd_text: str,
) -> SuggestionResult:
    """
    Generate improvement suggestions using the LLM.
    Falls back gracefully on timeout or API error.
    Requirements: 12.1–12.6
    """
    required_missing = skill_gap.get("required_missing", [])
    preferred_missing = skill_gap.get("preferred_missing", [])

    messages = _build_prompt(ats_score, required_missing, preferred_missing, section_scores, resume_text, jd_text)

    try:
        response = await asyncio.wait_for(
            _client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,  # type: ignore[arg-type]
                temperature=0.7,
                max_tokens=2000,
            ),
            timeout=LLM_TIMEOUT,
        )

        content = response.choices[0].message.content or "[]"

        # Parse JSON — handle both array and object with "suggestions" key
        parsed: Any = json.loads(content)
        if isinstance(parsed, dict):
            raw_list = parsed.get("suggestions", parsed.get("items", [parsed]))
        elif isinstance(parsed, list):
            raw_list = parsed
        else:
            raw_list = []

        suggestions: list[Suggestion] = []
        for item in raw_list:
            if isinstance(item, dict):
                suggestions.append(Suggestion(
                    title=str(item.get("title", "Improvement")),
                    explanation=str(item.get("explanation", "")),
                    example=str(item.get("example", "")),
                ))

        # Enforce 3–10 range
        suggestions = suggestions[:10]
        if len(suggestions) < 3:
            logger.warning("LLM returned fewer than 3 suggestions", extra={"count": len(suggestions)})

        return SuggestionResult(suggestions=suggestions, available=True)

    except asyncio.TimeoutError:
        logger.warning("LLM request timed out", extra={"timeout": LLM_TIMEOUT})
        return SuggestionResult(suggestions=[], available=False, error="LLM service timeout")
    except Exception as e:
        logger.warning("LLM request failed", extra={"error": str(e)})
        return SuggestionResult(suggestions=[], available=False, error=str(e))
