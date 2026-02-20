"""Tests for onboard_ai.agent_factory — agent creation and specialist routing."""

from __future__ import annotations

import sys
import types

from onboard_ai.agent_factory import (
    create_retriever,
    create_specialists,
    create_user_proxy,
    select_specialist,
    specialist_system_message,
)

# ---------------------------------------------------------------------------
# Stubs — autogen and chainlit are heavy; we mock at the module level.
# ---------------------------------------------------------------------------


def _ensure_autogen_stub() -> None:
    """Install a minimal ``autogen`` stub if the real package is not available."""
    if "autogen" in sys.modules and hasattr(sys.modules["autogen"], "__file__"):
        return  # real package present

    class _FakeAgent:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    autogen_pkg = types.ModuleType("autogen")
    autogen_pkg.__path__ = []  # make it a package
    ac_mod = types.ModuleType("autogen.agentchat")
    ac_mod.Agent = _FakeAgent  # type: ignore[attr-defined]
    ac_mod.AssistantAgent = _FakeAgent  # type: ignore[attr-defined]
    ac_mod.UserProxyAgent = _FakeAgent  # type: ignore[attr-defined]
    autogen_pkg.AssistantAgent = _FakeAgent  # type: ignore[attr-defined]

    sys.modules.setdefault("autogen", autogen_pkg)
    sys.modules.setdefault("autogen.agentchat", ac_mod)


def _ensure_chainlit_stub() -> None:
    """Install a minimal ``chainlit`` stub so chainlit_agents can be imported."""
    if "chainlit" in sys.modules and hasattr(sys.modules["chainlit"], "__file__"):
        return

    cl_mod = types.ModuleType("chainlit")

    class _FakeAction:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    class _FakeMessage:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

        def send(self):
            return self

    cl_mod.Action = _FakeAction  # type: ignore[attr-defined]
    cl_mod.Message = _FakeMessage  # type: ignore[attr-defined]
    cl_mod.run_sync = lambda x: x  # type: ignore[attr-defined]
    cl_mod.AskActionMessage = type("AskActionMessage", (), {})  # type: ignore[attr-defined]
    cl_mod.AskUserMessage = type("AskUserMessage", (), {})  # type: ignore[attr-defined]
    sys.modules.setdefault("chainlit", cl_mod)


_ensure_autogen_stub()
_ensure_chainlit_stub()


# ---------------------------------------------------------------------------
# specialist_system_message
# ---------------------------------------------------------------------------


class TestSpecialistSystemMessage:
    def test_contains_audience_name(self) -> None:
        msg = specialist_system_message("Developer")
        assert "Developer" in msg

    def test_contains_terminate_instruction(self) -> None:
        msg = specialist_system_message("QA")
        assert "TERMINATE" in msg

    def test_different_audiences_produce_different_messages(self) -> None:
        assert specialist_system_message("Developer") != specialist_system_message("Manager")


# ---------------------------------------------------------------------------
# create_retriever
# ---------------------------------------------------------------------------


class TestCreateRetriever:
    def test_returns_agent_with_correct_name(self) -> None:
        agent = create_retriever()
        assert agent.name == "Retriever"

    def test_max_auto_reply_is_one(self) -> None:
        agent = create_retriever()
        assert agent.max_consecutive_auto_reply == 1

    def test_human_input_mode_never(self) -> None:
        agent = create_retriever()
        assert agent.human_input_mode == "NEVER"


# ---------------------------------------------------------------------------
# create_user_proxy
# ---------------------------------------------------------------------------


class TestCreateUserProxy:
    def test_returns_proxy_with_correct_name(self) -> None:
        proxy = create_user_proxy()
        assert proxy.name == "User_Proxy"

    def test_human_input_mode_always(self) -> None:
        proxy = create_user_proxy()
        assert proxy.human_input_mode == "ALWAYS"

    def test_termination_message_detector(self) -> None:
        proxy = create_user_proxy()
        assert proxy.is_termination_msg({"content": "done TERMINATE"}) is True
        assert proxy.is_termination_msg({"content": "hello"}) is False


# ---------------------------------------------------------------------------
# create_specialists
# ---------------------------------------------------------------------------


class TestCreateSpecialists:
    def test_returns_three_specialists(self) -> None:
        specs = create_specialists()
        assert len(specs) == 3

    def test_expected_specialist_names(self) -> None:
        specs = create_specialists()
        assert set(specs.keys()) == {
            "Developer_Specialist",
            "QA_Specialist",
            "Manager_Specialist",
        }

    def test_each_specialist_has_system_message(self) -> None:
        specs = create_specialists()
        for _name, agent in specs.items():
            assert hasattr(agent, "system_message")
            assert "TERMINATE" in agent.system_message


# ---------------------------------------------------------------------------
# select_specialist
# ---------------------------------------------------------------------------


class TestSelectSpecialist:
    def test_selects_developer(self) -> None:
        specs = create_specialists()
        result = select_specialist("Developer", specs)
        assert result is not None
        assert result.name == "Developer_Specialist"

    def test_selects_qa(self) -> None:
        specs = create_specialists()
        result = select_specialist("QA", specs)
        assert result is not None
        assert result.name == "QA_Specialist"

    def test_selects_manager(self) -> None:
        specs = create_specialists()
        result = select_specialist("Manager", specs)
        assert result is not None
        assert result.name == "Manager_Specialist"

    def test_defaults_to_developer_for_unknown_audience(self) -> None:
        specs = create_specialists()
        result = select_specialist("Executive", specs)
        assert result is not None
        assert result.name == "Developer_Specialist"

    def test_defaults_to_developer_for_general(self) -> None:
        specs = create_specialists()
        result = select_specialist("General", specs)
        assert result is not None
        assert result.name == "Developer_Specialist"
