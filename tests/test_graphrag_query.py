"""Tests for onboard_ai.services.graphrag_query — query orchestrator logic."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from onboard_ai.services.graphrag_query import execute_query

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ROOT = "."


def _make_index_ready(tmp_path: Path) -> None:
    """Create a minimal index artifact so index_ready returns True."""
    (tmp_path / "data" / "output" / "lancedb").mkdir(parents=True)


# ---------------------------------------------------------------------------
# Index not ready scenarios
# ---------------------------------------------------------------------------


class TestExecuteQueryIndexNotReady:
    def test_returns_not_ready_message(self, tmp_path: Path) -> None:
        answer, has_cite, ready = execute_query(
            root_dir=str(tmp_path),
            question="What is this?",
            mode="local",
            response_type="single paragraph",
            community_level=0,
            enable_web_search=False,
        )
        assert ready is False
        assert "not ready" in answer.lower()

    def test_not_ready_with_web_search_disabled(self, tmp_path: Path) -> None:
        answer, _, ready = execute_query(
            root_dir=str(tmp_path),
            question="test",
            mode="local",
            response_type="single paragraph",
            community_level=0,
            enable_web_search=False,
        )
        assert ready is False
        assert "Web" not in answer  # no web augmentation

    @patch("onboard_ai.services.graphrag_query.web_search_enabled", return_value=True)
    @patch(
        "onboard_ai.services.graphrag_query.augment_answer_with_web",
        side_effect=lambda answer, query: f"{answer}\n\n[Web: example.com]",
    )
    def test_not_ready_with_web_fallback(self, mock_augment, mock_enabled, tmp_path: Path) -> None:
        answer, has_cite, ready = execute_query(
            root_dir=str(tmp_path),
            question="test",
            mode="local",
            response_type="single paragraph",
            community_level=0,
            enable_web_search=True,
        )
        assert ready is False
        assert "[Web:" in answer
        assert has_cite is True


# ---------------------------------------------------------------------------
# Index ready scenarios
# ---------------------------------------------------------------------------


class TestExecuteQueryIndexReady:
    @patch(
        "onboard_ai.services.graphrag_query.query_graphrag",
        return_value="Answer [Data: reports (1)]",
    )
    def test_returns_answer_with_citation(self, mock_query, tmp_path: Path) -> None:
        _make_index_ready(tmp_path)
        answer, has_cite, ready = execute_query(
            root_dir=str(tmp_path),
            question="Explain architecture",
            mode="local",
            response_type="single paragraph",
            community_level=0,
            enable_web_search=False,
        )
        assert ready is True
        assert "[Data:" in answer
        mock_query.assert_called_once()

    @patch(
        "onboard_ai.services.graphrag_query.query_graphrag",
        return_value="Answer [Data: reports (1)]",
    )
    def test_no_web_augment_when_citation_present(self, mock_query, tmp_path: Path) -> None:
        """Web augment should be skipped when the answer already has a data citation."""
        _make_index_ready(tmp_path)
        with patch("onboard_ai.services.graphrag_query.augment_answer_with_web") as mock_augment:
            execute_query(
                root_dir=str(tmp_path),
                question="test",
                mode="local",
                response_type="single paragraph",
                community_level=0,
                enable_web_search=True,
            )
        mock_augment.assert_not_called()

    @patch(
        "onboard_ai.services.graphrag_query.query_graphrag",
        return_value="Plain answer without citations",
    )
    @patch("onboard_ai.services.graphrag_query.web_search_enabled", return_value=True)
    @patch(
        "onboard_ai.services.graphrag_query.augment_answer_with_web",
        side_effect=lambda answer, query: f"{answer}\n\n[Web: result.com]",
    )
    def test_web_augment_when_no_citation(
        self, mock_augment, mock_enabled, mock_query, tmp_path: Path
    ) -> None:
        _make_index_ready(tmp_path)
        answer, has_cite, ready = execute_query(
            root_dir=str(tmp_path),
            question="test",
            mode="local",
            response_type="single paragraph",
            community_level=0,
            enable_web_search=True,
        )
        assert ready is True
        assert "[Web:" in answer
        mock_augment.assert_called_once()

    @patch(
        "onboard_ai.services.graphrag_query.query_graphrag",
        return_value="Answer text",
    )
    def test_global_mode_passed_to_query(self, mock_query, tmp_path: Path) -> None:
        _make_index_ready(tmp_path)
        execute_query(
            root_dir=str(tmp_path),
            question="test",
            mode="global",
            response_type="multiple paragraphs",
            community_level=1,
            enable_web_search=False,
        )
        kwargs = mock_query.call_args.kwargs
        assert kwargs["local_search"] is False
        assert kwargs["community_level"] == 1
        assert kwargs["response_type"] == "multiple paragraphs"

    @patch(
        "onboard_ai.services.graphrag_query.query_graphrag",
        return_value="Answer text",
    )
    def test_local_mode_passed_to_query(self, mock_query, tmp_path: Path) -> None:
        _make_index_ready(tmp_path)
        execute_query(
            root_dir=str(tmp_path),
            question="test",
            mode="local",
            response_type="prioritized list",
            community_level=2,
            enable_web_search=False,
        )
        kwargs = mock_query.call_args.kwargs
        assert kwargs["local_search"] is True
        assert kwargs["community_level"] == 2
