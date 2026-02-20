from onboard_ai.services import graphrag_query
from onboard_ai.services.web_search import format_web_results, has_any_citation, web_search_enabled


def test_web_search_enabled_parsing(monkeypatch) -> None:
    monkeypatch.setenv("ENABLE_WEB_SEARCH", "true")
    assert web_search_enabled(None) is True
    assert web_search_enabled(False) is False
    assert web_search_enabled(True) is True


def test_web_search_enabled_defaults_to_true(monkeypatch) -> None:
    monkeypatch.delenv("ENABLE_WEB_SEARCH", raising=False)
    assert web_search_enabled(None) is True


def test_format_web_results_and_citation_detection() -> None:
    out = format_web_results(
        [
            {
                "title": "Example",
                "content": "Useful snippet",
                "url": "https://example.com",
            }
        ]
    )
    assert "### Web search context" in out
    assert "[Web: https://example.com]" in out
    assert has_any_citation(out) is True


def test_execute_query_uses_web_when_index_not_ready(monkeypatch) -> None:
    monkeypatch.setattr(graphrag_query, "index_ready", lambda _root: False)
    monkeypatch.setattr(graphrag_query, "index_not_ready_message", lambda: "Index is not ready")
    monkeypatch.setattr(
        graphrag_query,
        "augment_answer_with_web",
        lambda answer, query: f"{answer}\n\n- web hit [Web: https://example.com]",
    )

    answer, has_citation, is_ready = graphrag_query.execute_query(
        root_dir=".",
        question="what is python",
        mode="local",
        response_type="single paragraph",
        community_level=0,
        enable_web_search=True,
    )

    assert "[Web: https://example.com]" in answer
    assert has_citation is True
    assert is_ready is False
