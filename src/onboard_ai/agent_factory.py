"""Factory functions for creating AutoGen agents used in the Chainlit chat session.

Creates a Retriever agent, a User Proxy, and audience-specific Specialist
agents (Developer, QA, Manager). The ``select_specialist`` helper picks the
right specialist based on the active audience setting.
"""

from autogen import AssistantAgent

from onboard_ai.chainlit_agents import ChainlitAssistantAgent, ChainlitUserProxyAgent
from onboard_ai.settings import LLM_CONFIG_AUTOGEN, SPECIALIST_NAME_BY_AUDIENCE


def specialist_system_message(audience: str) -> str:
    """Build the system prompt for an audience-specific specialist agent."""
    return (
        f"You are the {audience} onboarding specialist. "
        "Use query_graphRAG to gather evidence first, then provide an answer in that audience style. "
        "Always include citations from retrieved evidence when available. "
        "Output 'TERMINATE' once the response is complete."
    )


def create_retriever() -> AssistantAgent:
    """Create the Retriever agent that calls ``query_graphRAG``."""
    return AssistantAgent(
        name="Retriever",
        llm_config=LLM_CONFIG_AUTOGEN,
        system_message=(
            "Only execute the function query_graphRAG to look for context. "
            "Output 'TERMINATE' when an answer has been provided."
        ),
        max_consecutive_auto_reply=1,
        human_input_mode="NEVER",
        description="Retriever Agent",
    )


def create_user_proxy() -> ChainlitUserProxyAgent:
    """Create the User Proxy agent that represents the human user."""
    return ChainlitUserProxyAgent(
        name="User_Proxy",
        human_input_mode="ALWAYS",
        llm_config=LLM_CONFIG_AUTOGEN,
        is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
        code_execution_config=False,
        system_message="A human admin. Interact with the retriever to provide any context",
        description="User Proxy Agent",
    )


def create_specialists() -> dict[str, ChainlitAssistantAgent]:
    """Create one specialist agent per audience role (Developer, QA, Manager)."""
    return {
        "Developer_Specialist": ChainlitAssistantAgent(
            name="Developer_Specialist",
            llm_config=LLM_CONFIG_AUTOGEN,
            system_message=specialist_system_message("Developer"),
            max_consecutive_auto_reply=1,
            human_input_mode="NEVER",
            description="Developer audience specialist",
        ),
        "QA_Specialist": ChainlitAssistantAgent(
            name="QA_Specialist",
            llm_config=LLM_CONFIG_AUTOGEN,
            system_message=specialist_system_message("QA"),
            max_consecutive_auto_reply=1,
            human_input_mode="NEVER",
            description="QA audience specialist",
        ),
        "Manager_Specialist": ChainlitAssistantAgent(
            name="Manager_Specialist",
            llm_config=LLM_CONFIG_AUTOGEN,
            system_message=specialist_system_message("Manager"),
            max_consecutive_auto_reply=1,
            human_input_mode="NEVER",
            description="Manager audience specialist",
        ),
    }


def select_specialist(
    audience: str, specialists: dict[str, ChainlitAssistantAgent]
) -> ChainlitAssistantAgent | None:
    """Return the specialist agent for the given audience, defaulting to Developer."""
    name = SPECIALIST_NAME_BY_AUDIENCE.get(audience, "Developer_Specialist")
    return specialists.get(name)
