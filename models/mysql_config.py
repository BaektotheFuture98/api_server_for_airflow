from pydantic import BaseModel, field_validator
from typing import Literal


class MySQLConfig(BaseModel):
    service: Literal["mysql"]
    project_name: str
    st_seq: int
    es_source_index: str = "lucy_main_v4_20240314"
    query: str

    mysql_host: str
    mysql_database: str
    mysql_table: str
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
    
    ## project_name을 통해 schema registry에 등록을 하므로 '-'을 '_'로 변경한다. (스키마 레지스트리는 '-'를 허용하지 않음)
    @field_validator("project_name")
    def check_project_name(cls, v: str):
        if " " in v:
            raise ValueError("project_name must not contain spaces")
        
        if "-" in v:
            v = v.replace("-", "_")
        return v