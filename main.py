from typing import Annotated, Union
from fastapi import FastAPI, HTTPException
from pydantic import Field
from services.airflow_public_api import get_token, post_dags_trigger, gen_token
from models.mysql_config import MySQLConfig
from models.elasticsearch_config import ElasticsearchConfig
from config.logger import get_logger

logger = get_logger(__name__)

app = FastAPI()

# 서로 다른 설정 스키마를 하나의 요청 타입으로 처리하기 위한 union 정의
RequestSchema = Annotated[
    Union[MySQLConfig, ElasticsearchConfig], # MySQLConfig 또는 ElasticsearchConfig 중 하나
    Field(discriminator="service") # 'service' 필드를 기준으로 구분
]

@app.post("/register")
def register(schema: RequestSchema):
    logger.info(f"Received registration request for service: {schema.service} with schema: {schema}")
    service = schema.service

    token = get_token()
    logger.info("Obtained Airflow token")

    dag_id = "mysql_pipeline_dag" if service == "mysql" else "elasticsearch_pipeline_dag"

    conf = schema.model_dump()
    logger.info(f"Triggering DAG '{dag_id}' with conf: {conf}")

    response = post_dags_trigger(dag_id=dag_id, conf=conf, token=token)

    if response.status_code in (401, 403):
        logger.info(f"Initial trigger unauthorized ({response.status_code}). Refreshing token and retrying.")
        token = gen_token()
        response = post_dags_trigger(dag_id=dag_id, conf=conf, token=token)
        if response.status_code in (401, 403):
            raise HTTPException(status_code=401, detail="Unauthorized: token invalid or expired.")

    return {"dag_id": dag_id, "conf": conf, "result": response.json()}