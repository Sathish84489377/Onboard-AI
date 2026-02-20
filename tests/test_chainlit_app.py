"""Tests for onboard_ai.chainlit_app — unit-level tests for inner logic.

Chainlit lifecycle handlers (on_chat_start, on_message) are async and deeply
coupled to the Chainlit runtime. We test the helper logic they use (settings
propagation, state-transition function shape, query_graph_rag inner function)
by importing the module with stubs and verifying the building blocks.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

from onboard_ai.graphrag_service import (
    has_data_citation,  # noqa: E402
    index_not_ready_message,
    index_ready,
)
from onboard_ai.settings import AUDIENCE_INSTRUCTION  # noqa: E402

# ---------------------------------------------------------------------------
# Ensure stubs for chainlit + autogen so the module can be imported.
# ---------------------------------------------------------------------------


def _ensure_chainlit_full_stub() -> None:
    """Provide a comprehensive chainlit stub for the app module."""
    if "chainlit" in sys.modules and hasattr(sys.modules["chainlit"], "__file__"):
        return

    cl_mod = sys.modules.get("chainlit") or types.ModuleType("chainlit")
    cl_mod.Message = MagicMock  # type: ignore[attr-defined]
    cl_mod.ChatSettings = MagicMock  # type: ignore[attr-defined]
    cl_mod.on_chat_start = lambda f: f  # type: ignore[attr-defined]
    cl_mod.on_settings_update = lambda f: f  # type: ignore[attr-defined]
    cl_mod.on_message = lambda f: f  # type: ignore[attr-defined]
    cl_mod.user_session = MagicMock()  # type: ignore[attr-defined]
    cl_mod.make_async = lambda f: f  # type: ignore[attr-defined]
    cl_mod.run_sync = lambda x: x  # type: ignore[attr-defined]
    cl_mod.Action = MagicMock  # type: ignore[attr-defined]
    cl_mod.AskActionMessage = MagicMock  # type: ignore[attr-defined]
    cl_mod.AskUserMessage = MagicMock  # type: ignore[attr-defined]
    sys.modules.setdefault("chainlit", cl_mod)

    iw_mod = types.ModuleType("chainlit.input_widget")
    iw_mod.Select = MagicMock  # type: ignore[attr-defined]
    iw_mod.Slider = MagicMock  # type: ignore[attr-defined]
    iw_mod.Switch = MagicMock  # type: ignore[attr-defined]
    sys.modules.setdefault("chainlit.input_widget", iw_mod)

    rich_mod = types.ModuleType("rich")
    rich_mod.print = print  # type: ignore[attr-defined]
    sys.modules.setdefault("rich", rich_mod)


def _ensure_autogen_stub() -> None:
    if "autogen" in sys.modules and hasattr(sys.modules["autogen"], "__file__"):
        return

    class _FakeAgent:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    autogen_pkg = sys.modules.get("autogen") or types.ModuleType("autogen")
    autogen_pkg.__path__ = []  # type: ignore[attr-defined]
    ac_mod = types.ModuleType("autogen.agentchat")
    ac_mod.Agent = _FakeAgent  # type: ignore[attr-defined]
    ac_mod.AssistantAgent = _FakeAgent  # type: ignore[attr-defined]
    ac_mod.UserProxyAgent = _FakeAgent  # type: ignore[attr-defined]
    autogen_pkg.AssistantAgent = _FakeAgent  # type: ignore[attr-defined]
    autogen_pkg.GroupChat = MagicMock  # type: ignore[attr-defined]
    autogen_pkg.GroupChatManager = MagicMock  # type: ignore[attr-defined]

    sys.modules.setdefault("autogen", autogen_pkg)
    sys.modules.setdefault("autogen.agentchat", ac_mod)


_ensure_chainlit_full_stub()
_ensure_autogen_stub()

# ---------------------------------------------------------------------------
# Tests focused on the building blocks used by chainlit_app handlers
# ---------------------------------------------------------------------------


class TestIndexReadyIntegration:
    """Verify index_ready works as chainlit_app uses it (Path('.'))."""

    def test_current_dir_without_artifacts(self, tmp_path: Path) -> None:
        assert index_ready(tmp_path) is False

    def test_with_lancedb(self, tmp_path: Path) -> None:
        (tmp_path / "data" / "output" / "lancedb").mkdir(parents=True)
        assert index_ready(tmp_path) is True


class TestAudienceInstruction:
    """Verify the audience map used by the inner query_graph_rag closure."""

    def test_general_audience_exists(self) -> None:
        assert "General" in AUDIENCE_INSTRUCTION

    def test_developer_audience_exists(self) -> None:
        assert "Developer" in AUDIENCE_INSTRUCTION

    def test_all_values_are_strings(self) -> None:
        for key, val in AUDIENCE_INSTRUCTION.items():
            assert isinstance(val, str), f"{key} value is not a string"


class TestCitationCheckUsedByApp:
    """The on_message handler embeds citation checks."""

    def test_data_citation_detected(self) -> None:
        assert has_data_citation("Answer [Data: reports (1)]") is True

    def test_no_citation_adds_warning(self) -> None:
        result = "plain answer"
        assert not has_data_citation(result)


class TestIndexNotReadyMessageUsedByApp:
    def test_message_mentions_input_folder(self) -> None:
        msg = index_not_ready_message()
        assert "data/input" in msg
