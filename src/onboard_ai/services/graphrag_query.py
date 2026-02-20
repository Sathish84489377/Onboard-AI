"""High-level query orchestrator combining GraphRAG and web-search fallback.

Used by the FastAPI ``/query`` endpoint. Delegates index checks and search
execution to ``graphrag_service`` and enriches answers via ``web_search``.
"""

from pathlib import Path

from onboard_ai.graphrag_service import (
    has_data_citation,
    index_not_ready_message,
    index_ready,
    query_graphrag,
)
from onboard_ai.services.web_search import (
    augment_answer_with_web,
    has_any_citation,
    web_search_enabled,
)


def execute_query(
    *,
    root_dir: str,
    question: str,
    mode: str,
    response_type: str,
    community_level: int,
    enable_web_search: bool = True,
) -> tuple[str, bool, bool]:
    """Run a GraphRAG query with optional web-search fallback.

    Args:
        root_dir: Project root directory path.
        question: The user's natural-language question.
        mode: Search mode — ``'local'`` or ``'global'``.
        response_type: Desired response format.
        community_level: Community hierarchy level.
        enable_web_search: Whether to augment with web results.

    Returns:
        Tuple of (answer, has_citation, index_ready).
    """
    root = Path(root_dir)
    use_web = web_search_enabled(enable_web_search)
    ready = index_ready(root)
    if not ready:
        answer = index_not_ready_message()
        if use_web:
            answer = augment_answer_with_web(answer=answer, query=question)
        return answer, has_any_citation(answer), False

    answer = query_graphrag(
        root_dir=root,
        local_search=mode == "local",
        community_level=community_level,
        response_type=response_type,
        query=question,
    )
    if use_web and not has_data_citation(answer):
        answer = augment_answer_with_web(answer=answer, query=question)

    return answer, has_any_citation(answer), True
