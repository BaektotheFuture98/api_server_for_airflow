from typing import Literal
from pydantic import BaseModel, field_validator
from config.logger import get_logger   

logger = get_logger(__name__)

class ElasticsearchConfig(BaseModel):
    service: Literal["elasticsearch"]
    project_name: str
    st_seq: int
    es_source_index: str
    query: str

    es_target_hosts: str
    es_target_index: str
    user: str
    password: str

    fields: list[str]

    @field_validator("fields")
    def check_fields(cls, v: list[str]):
        allowed = {"an_title", "in_date", "kw_docid", "an_content"}
        if not v:
            raise ValueError("fields must be at least one")
        invalid = [field for field in v if field not in allowed]
        if invalid:
            raise ValueError(
                f"Invalid fields: {invalid}. Allowed: {sorted(allowed)}"
            )
        return v

    @field_validator("project_name")
    def check_project_name(cls, v: str):
        if " " in v:
            raise ValueError("project_name must not contain spaces")
        if "-" in v:
            v = v.replace("-", "_")
        return v