from autogen import AssistantAgent  # type: ignore[import-not-found]

from onboard_ai.settings import LLM_CONFIG_AUTOGEN, SPECIALIST_NAME_BY_AUDIENCE
from onboard_ai.chainlit_agents import ChainlitAssistantAgent, ChainlitUserProxyAgent


def specialist_system_message(audience: str) -> str:
    return (
        f"You are the {audience} onboarding specialist. "
        "Use query_graphRAG to gather evidence first, then provide an answer in that audience style. "
        "Always include citations from retrieved evidence when available. "
        "Output 'TERMINATE' once the response is complete."
    )


def create_retriever() -> AssistantAgent:
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


def select_specialist(audience: str, specialists: dict):
    name = SPECIALIST_NAME_BY_AUDIENCE.get(audience, "Developer_Specialist")
    return specialists.get(name)
