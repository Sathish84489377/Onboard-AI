"""Application-wide configuration backed by Pydantic.

Exports a singleton ``config`` instance consumed by the API layer and CLI.
"""

from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    """Application configuration with sensible defaults."""

    root_dir: str = Field(default=".", description="Project root directory.")
    default_response_type: str = Field(
        default="single paragraph", description="Default GraphRAG response format."
    )
    default_community_level: int = Field(
        default=0, description="Default community hierarchy level."
    )


config = AppConfig()
