"""Tests for onboard_ai.graphrag_service — index checks, citations, and query dispatch."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from onboard_ai.graphrag_service import (
    has_data_citation,
    index_not_ready_message,
    index_ready,
    query_graphrag,
)

# ---------------------------------------------------------------------------
# index_ready
# ---------------------------------------------------------------------------


class TestIndexReady:
    """Verify index_ready detects various artifact patterns."""

    def test_returns_false_when_output_dir_missing(self, tmp_path: Path) -> None:
        assert index_ready(tmp_path) is False

    def test_returns_false_when_output_dir_is_empty(self, tmp_path: Path) -> None:
        (tmp_path / "data" / "output").mkdir(parents=True)
        assert index_ready(tmp_path) is False

    def test_detects_lancedb_directory(self, tmp_path: Path) -> None:
        (tmp_path / "data" / "output" / "lancedb").mkdir(parents=True)
        assert index_ready(tmp_path) is True

    def test_detects_known_parquet_files(self, tmp_path: Path) -> None:
        output = tmp_path / "data" / "output"
        output.mkdir(parents=True)
        (output / "create_final_nodes.parquet").write_text("")
        assert index_ready(tmp_path) is True

    def test_detects_entities_parquet(self, tmp_path: Path) -> None:
        output = tmp_path / "data" / "output"
        output.mkdir(parents=True)
        (output / "create_final_entities.parquet").write_text("")
        assert index_ready(tmp_path) is True

    def test_detects_community_reports_parquet(self, tmp_path: Path) -> None:
        output = tmp_path / "data" / "output"
        output.mkdir(parents=True)
        (output / "create_final_community_reports.parquet").write_text("")
        assert index_ready(tmp_path) is True

    def test_detects_arbitrary_parquet_via_rglob(self, tmp_path: Path) -> None:
        nested = tmp_path / "data" / "output" / "sub"
        nested.mkdir(parents=True)
        (nested / "random.parquet").write_text("")
        assert index_ready(tmp_path) is True

    def test_returns_false_with_non_parquet_files(self, tmp_path: Path) -> None:
        output = tmp_path / "data" / "output"
        output.mkdir(parents=True)
        (output / "readme.txt").write_text("")
        assert index_ready(tmp_path) is False


# ---------------------------------------------------------------------------
# index_not_ready_message
# ---------------------------------------------------------------------------


class TestIndexNotReadyMessage:
    def test_contains_next_steps(self) -> None:
        msg = index_not_ready_message()
        assert "not ready" in msg.lower()
        assert "data/input" in msg

    def test_returns_string(self) -> None:
        assert isinstance(index_not_ready_message(), str)


# ---------------------------------------------------------------------------
# has_data_citation
# ---------------------------------------------------------------------------


class TestHasDataCitation:
    def test_positive(self) -> None:
        assert has_data_citation("Answer [Data: reports (1, 2)]") is True

    def test_negative(self) -> None:
        assert has_data_citation("No citations here.") is False

    def test_empty_string(self) -> None:
        assert has_data_citation("") is False

    def test_partial_match_no_colon(self) -> None:
        assert has_data_citation("[Data reports]") is False


# ---------------------------------------------------------------------------
# query_graphrag
# ---------------------------------------------------------------------------


class TestQueryGraphrag:
    """Verify query_graphrag dispatches to the right search function."""

    def test_local_search_dispatches_correctly(self, tmp_path: Path) -> None:
        with patch(
            "onboard_ai.graphrag_service.run_local_search",
            return_value=("local answer", None),
        ) as mock_local:
            result = query_graphrag(
                root_dir=tmp_path,
                local_search=True,
                community_level=0,
                response_type="single paragraph",
                query="What is X?",
            )
        assert result == "local answer"
        mock_local.assert_called_once()
        call_kwargs = mock_local.call_args
        assert call_kwargs.kwargs["query"] == "What is X?"

    def test_global_search_dispatches_correctly(self, tmp_path: Path) -> None:
        with patch(
            "onboard_ai.graphrag_service.run_global_search",
            return_value=("global answer", None),
        ) as mock_global:
            result = query_graphrag(
                root_dir=tmp_path,
                local_search=False,
                community_level=1,
                response_type="multiple paragraphs",
                query="Summarize Y",
            )
        assert result == "global answer"
        mock_global.assert_called_once()

    def test_local_search_passes_parameters(self, tmp_path: Path) -> None:
        with patch(
            "onboard_ai.graphrag_service.run_local_search",
            return_value=("ok", None),
        ) as mock_local:
            query_graphrag(
                root_dir=tmp_path,
                local_search=True,
                community_level=2,
                response_type="prioritized list",
                query="test",
            )
        kwargs = mock_local.call_args.kwargs
        assert kwargs["community_level"] == 2
        assert kwargs["response_type"] == "prioritized list"
        assert kwargs["root_dir"] == tmp_path
        assert kwargs["streaming"] is False
