# API Server for Airflow

FastAPI로 만든 간단한 API 서버입니다.  
`POST /register` 요청을 받아 `service` 값에 따라 Airflow DAG를 트리거합니다.

## What It Does

- `mysql` 또는 `elasticsearch` 요청 스키마를 검증합니다.
- Airflow 토큰이 없으면 발급하고, 있으면 재사용합니다.
- 해당 서비스용 DAG를 실행하고 Airflow 응답을 반환합니다.

## Requirements

- Python 3.12+

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install .
```

## Environment Variables

`.env` 파일에 아래 값을 설정합니다.

```env
AIRFLOW_HOST=http://localhost:8080
AIRFLOW_USER=admin
AIRFLOW_PASSWORD=admin
# AIRFLOW_TOKEN=optional
```

## Run

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API

### Endpoint

- `POST /register`

### Common Rules

- `service`: `mysql` 또는 `elasticsearch`
- `project_name`: 공백 불가, `-`는 `_`로 변경
- `fields`: 최소 1개 이상
- 허용 `fields`: `an_title`, `in_date`, `kw_docid`, `an_content`

### MySQL Example

```json
{
  "service": "mysql",
  "project_name": "sample_project",
  "st_seq": 1,
  "es_source_index": "sample_source_index",
  "query": "SELECT * FROM sample_table",
  "mysql_host": "127.0.0.1",
  "mysql_database": "sample_db",
  "mysql_table": "sample_table",
  "user": "db_user",
  "password": "db_password",
  "fields": ["an_title", "in_date"]
}
```

`es_source_index`를 생략하면 코드 기본값이 사용됩니다.

### Elasticsearch Example

```json
{
  "service": "elasticsearch",
  "project_name": "sample_project",
  "st_seq": 2,
  "es_source_index": "sample_source_index",
  "query": "an_content:AI",
  "es_target_hosts": "http://localhost:9200",
  "es_target_index": "sample_target_index",
  "user": "es_user",
  "password": "es_password",
  "fields": ["an_title", "kw_docid"]
}
```

### Response Shape

```json
{
  "dag_id": "mysql_pipeline_dag",
  "conf": {},
  "result": {}
}
```

## Notes

- DAG ID는 현재 `mysql_pipeline_dag`, `elasticsearch_pipeline_dag`로 고정되어 있습니다.
- 인증 실패 시 토큰을 다시 발급한 뒤 한 번 더 재시도합니다.
- 요청과 응답이 로그에 남으므로 운영 환경에서는 민감정보 로깅 여부를 점검하는 것이 좋습니다.

## Main Files

- `main.py`
- `services/airflow_public_api.py`
- `models/mysql_config.py`
- `models/elasticsearch_config.py`
- `config/logger.py`
