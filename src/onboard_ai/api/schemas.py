"""Pydantic request/response schemas for the Onboard AI REST API."""

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Incoming query payload for the ``/query`` endpoint."""

    question: str = Field(min_length=1, description="The natural-language question to ask.")
    mode: str = Field(
        default="local",
        pattern="^(local|global)$",
        description="GraphRAG search mode: 'local' or 'global'.",
    )
    response_type: str = Field(
        default="single paragraph",
        description="Desired response format (e.g. 'single paragraph', 'prioritized list').",
    )
    community_level: int = Field(
        default=0, ge=0, description="Community hierarchy level for the search."
    )
    enable_web_search: bool = Field(
        default=True, description="Whether to augment with SearXNG web results."
    )


class QueryResponse(BaseModel):
    """Response payload returned by the ``/query`` endpoint."""

    answer: str = Field(description="The generated answer text.")
    has_citation: bool = Field(description="Whether the answer contains citations.")
    index_ready: bool = Field(description="Whether the GraphRAG index was available.")
