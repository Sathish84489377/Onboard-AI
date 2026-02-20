from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    root_dir: str = Field(default=".")
    default_response_type: str = Field(default="single paragraph")
    default_community_level: int = Field(default=0)


config = AppConfig()
