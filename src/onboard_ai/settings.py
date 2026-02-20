LLM_CONFIG_AUTOGEN = {
    "seed": 42,
    "temperature": 0,
    "config_list": [
        {"model": "litellm", "base_url": "http://0.0.0.0:4000/", "api_key": "ollama"},
    ],
    "timeout": 60000,
}

AUDIENCE_INSTRUCTION = {
    "General": "Use plain language and explain product terms briefly.",
    "Developer": "Focus on architecture, APIs, dependencies, and implementation detail.",
    "QA": "Focus on test scenarios, edge cases, validations, and release risk.",
    "Manager": "Focus on outcomes, timelines, risks, ownership, and business impact.",
}

SPECIALIST_NAME_BY_AUDIENCE = {
    "Developer": "Developer_Specialist",
    "QA": "QA_Specialist",
    "Manager": "Manager_Specialist",
}
