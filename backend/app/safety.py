"""
LLMOps Step 3 — Content Safety Guardrails

Checks user input and LLM output against Azure Content Safety.
Blocks hate, violence, sexual, and self-harm content.

Severity levels: 0=safe, 2=low, 4=medium, 6=high
We block at severity >= 4 (medium+) — adjust threshold as needed.

Falls back gracefully if Content Safety is not configured (local dev).
"""
import logging

import httpx

from app.config import settings

logger = logging.getLogger("investment_coach")

_CATEGORIES = ["Hate", "Violence", "Sexual", "SelfHarm"]
_BLOCK_THRESHOLD = 4   # block medium severity and above


def _is_configured() -> bool:
    return bool(settings.content_safety_endpoint and settings.content_safety_key)


async def check_content(text: str, source: str = "input") -> tuple[bool, str]:
    """Check text against Azure Content Safety.

    Returns:
        (is_safe, reason) — reason is empty string when safe
    """
    if not _is_configured():
        return True, ""   # skip check in local dev

    url = f"{settings.content_safety_endpoint.rstrip('/')}/contentsafety/text:analyze?api-version=2024-09-01"
    payload = {
        "text": text[:10000],   # API limit
        "categories": _CATEGORIES,
        "outputType": "FourSeverityLevels",
    }

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.post(
                url,
                json=payload,
                headers={"Ocp-Apim-Subscription-Key": settings.content_safety_key},
            )
            resp.raise_for_status()
            result = resp.json()
    except Exception as e:
        # Safety check failure should not block the user — log and allow
        logger.warning("content_safety_check_failed source=%s error=%s", source, e)
        return True, ""

    for cat_result in result.get("categoriesAnalysis", []):
        category = cat_result.get("category", "")
        severity = cat_result.get("severity", 0)
        if severity >= _BLOCK_THRESHOLD:
            reason = f"{category} content detected (severity {severity})"
            logger.warning("content_safety_blocked source=%s category=%s severity=%d", source, category, severity)
            return False, reason

    return True, ""
