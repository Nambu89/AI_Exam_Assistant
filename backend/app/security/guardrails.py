"""Lightweight, layered guardrails.

Two layers:
* **Offline lexical layer** (always on, no dependencies): flags obvious
  prompt-injection attempts. Deterministic and unit-testable.
* **Azure AI Content Safety** (optional): when configured, runs the input
  through the managed moderation service for jailbreak/harm detection.

Design choice: this is a *study assistant*; we do not try to be a full DLP
solution. The lexical layer exists to demonstrate defense-in-depth and to keep
the offline demo self-contained. Real deployments should rely on Content Safety
+ the model's own safety system.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.config import get_settings

_INJECTION_PATTERNS = [
    r"ignore (all )?(previous|prior|above) (instructions|prompts)",
    r"disregard (the )?(system|previous) (prompt|instructions)",
    r"reveal (your )?(system prompt|instructions)",
    r"you are now (a|an|in) ",
    r"\bDAN\b|\bdeveloper mode\b",
    r"print (your )?(system )?prompt",
]
_INJECTION_RE = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)


@dataclass(slots=True)
class GuardrailResult:
    allowed: bool
    reason: str = ""
    layer: str = ""


def _lexical_check(text: str) -> GuardrailResult:
    if _INJECTION_RE.search(text):
        return GuardrailResult(False, "Possible prompt-injection attempt.", layer="lexical")
    return GuardrailResult(True)


async def _content_safety_check(text: str) -> GuardrailResult:
    settings = get_settings()
    if not settings.enable_content_safety or not settings.azure_content_safety_endpoint:
        return GuardrailResult(True)
    try:
        from azure.ai.contentsafety.aio import ContentSafetyClient
        from azure.ai.contentsafety.models import AnalyzeTextOptions
        from azure.identity.aio import DefaultAzureCredential
    except ImportError:
        return GuardrailResult(True)  # extra not installed → skip cleanly

    credential = DefaultAzureCredential()
    client = ContentSafetyClient(settings.azure_content_safety_endpoint, credential)
    try:
        resp = await client.analyze_text(AnalyzeTextOptions(text=text))
        for cat in resp.categories_analysis:
            if cat.severity and cat.severity >= 4:
                return GuardrailResult(
                    False, f"Content flagged: {cat.category}", layer="content-safety"
                )
    except Exception:  # noqa: BLE001 - never let moderation availability break UX
        return GuardrailResult(True)
    finally:
        await client.close()
        await credential.close()
    return GuardrailResult(True)


async def check_input(text: str) -> GuardrailResult:
    lexical = _lexical_check(text)
    if not lexical.allowed:
        return lexical
    return await _content_safety_check(text)
