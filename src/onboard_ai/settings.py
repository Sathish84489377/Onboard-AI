"""Shared constants for AutoGen LLM configuration and audience-role mappings.

These values are consumed by ``agent_factory`` and ``chainlit_app`` to
configure AutoGen agents and route queries by audience persona.
"""

from typing import Any

LLM_CONFIG_AUTOGEN: dict[str, Any] = {
    "seed": 42,
    "temperature": 0,
    "config_list": [
        {"model": "litellm", "base_url": "http://0.0.0.0:4000/", "api_key": "ollama"},
    ],
    "timeout": 60000,
}

AUDIENCE_INSTRUCTION: dict[str, str] = {
    "General": "Use plain language and explain product terms briefly.",
    "Developer": "Focus on architecture, APIs, dependencies, and implementation detail.",
    "QA": "Focus on test scenarios, edge cases, validations, and release risk.",
    "Manager": "Focus on outcomes, timelines, risks, ownership, and business impact.",
}

SPECIALIST_NAME_BY_AUDIENCE: dict[str, str] = {
    "Developer": "Developer_Specialist",
    "QA": "QA_Specialist",
    "Manager": "Manager_Specialist",
}
