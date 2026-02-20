from fastapi import FastAPI

from onboard_ai.api.schemas import QueryRequest, QueryResponse
from onboard_ai.config import config
from onboard_ai.services.graphrag_query import execute_query


app = FastAPI(title="Onboard AI API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query(payload: QueryRequest) -> QueryResponse:
    answer, has_citation, ready = execute_query(
        root_dir=config.root_dir,
        question=payload.question,
        mode=payload.mode,
        response_type=payload.response_type,
        community_level=payload.community_level,
        enable_web_search=payload.enable_web_search,
    )
    return QueryResponse(answer=answer, has_citation=has_citation, index_ready=ready)
