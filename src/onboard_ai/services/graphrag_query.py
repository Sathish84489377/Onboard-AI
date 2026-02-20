from pathlib import Path

from onboard_ai.graphrag_service import (
    has_data_citation,
    index_not_ready_message,
    index_ready,
    query_graphrag,
)
from onboard_ai.services.web_search import augment_answer_with_web, has_any_citation, web_search_enabled


def execute_query(
    *,
    root_dir: str,
    question: str,
    mode: str,
    response_type: str,
    community_level: int,
    enable_web_search: bool = True,
) -> tuple[str, bool, bool]:
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
