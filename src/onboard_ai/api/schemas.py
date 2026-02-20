from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    mode: str = Field(default="local", pattern="^(local|global)$")
    response_type: str = Field(default="single paragraph")
    community_level: int = Field(default=0, ge=0)
    enable_web_search: bool = Field(default=True)


class QueryResponse(BaseModel):
    answer: str
    has_citation: bool
    index_ready: bool
