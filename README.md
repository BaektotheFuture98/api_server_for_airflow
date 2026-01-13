# API Server (FastAPI) — Airflow DAG Trigger

이 저장소는 FastAPI 기반의 간단한 API 서버로, 요청 바디의 스키마에 따라 Airflow DAG를 트리거합니다. `service` 필드로 MySQL 또는 Elasticsearch 파이프라인을 구분하며, 요청/응답을 표준 로거로 기록하고, Airflow 토큰 발급/갱신을 처리합니다.

## 개요
- 서버 엔트리: [main.py](main.py)
- 서비스 연동: [services/airflow_public_api.py](services/airflow_public_api.py)
- 스키마 정의:
	- MySQL: [models/mysql_config.py](models/mysql_config.py)
	- Elasticsearch: [models/elasticsearch_config.py](models/elasticsearch_config.py)
- 로깅 설정: [config/logger.py](config/logger.py)
- 예외 정의: [config/exception.py](config/exception.py)
- 의존성 선언: [pyproject.toml](pyproject.toml)

요청 바디의 `service` 필드(`"mysql"` 또는 `"elasticsearch"`)를 판별자(discriminator)로 사용하여 두 스키마 중 하나로 유효성 검사를 수행합니다. 유효성 검사를 통과하면 Airflow Public API를 호출해 해당 DAG를 트리거합니다.

## 주요 기능
- `POST /register`: 요청 스키마에 맞는 Airflow DAG 트리거
- Airflow 토큰 자동 발급/재발급 및 보관(`.env`)
- 요청/응답 로깅(HTTP 메서드, 경로, 헤더, 바디, 상태코드)
- 필드 유효성 검사(허용 필드 목록, `project_name` 변환 등)

## 요구사항
- Python `>= 3.12`
- 의존성(일부): FastAPI, Pydantic, Requests, Uvicorn, python-dotenv
	- `python-dotenv`는 코드에서 `dotenv`를 사용하므로 필요합니다.

## 설치
가상환경 권장(Linux 예시).

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install .
```

또는 개발 모드로:

```bash
pip install -e .
```

## 환경변수 설정
서버는 Airflow와 통신을 위해 다음 환경변수를 사용합니다. `.env` 파일에 저장하면 자동 로드됩니다.

- `AIRFLOW_HOST`: Airflow 호스트(base URL), 예: `http://localhost:8080`
- `AIRFLOW_USER`: Airflow 사용자명
- `AIRFLOW_PASSWORD`: Airflow 비밀번호
- `AIRFLOW_TOKEN`(옵션): 미리 발급된 토큰이 있다면 지정 가능. 없거나 비어 있으면 자동 발급 후 `.env`에 저장됩니다.

`.env` 예시:

```env
AIRFLOW_HOST=http://localhost:8080
AIRFLOW_USER=admin
AIRFLOW_PASSWORD=admin
# AIRFLOW_TOKEN=eyJhbGciOi...
```

## 실행
개발 서버(자동 리로드):

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API
### 엔드포인트
- `POST /register`

요청 바디는 `service` 필드로 스키마를 구분합니다.

### 공통 규칙
- `service`: `"mysql"` 또는 `"elasticsearch"`
- `project_name`: 공백 불가, `-`는 `_`로 자동 변환
- `fields`: 최소 1개 이상 필요, 허용 목록만 가능
	- 허용 값: `an_title`, `in_date`, `kw_docid`, `an_content`

### MySQL 요청 스키마
정의: [models/mysql_config.py](models/mysql_config.py)

필드:
- `service`: `"mysql"`
- `project_name`: 문자열(공백 불가, `-`는 `_`로 치환)
- `st_seq`: 정수
- `es_source_index`: 문자열(기본값 `lucy_main_v4_20240314`)
- `query`: 문자열(SQL)
- `mysql_host`: 문자열
- `mysql_database`: 문자열
- `mysql_table`: 문자열
- `user`: 문자열
- `password`: 문자열
- `fields`: 문자열 배열(허용 목록 내 값만)

예시:

```json
{
	"service": "mysql",
	"project_name": "my-project",
	"st_seq": 1,
	"es_source_index": "lucy_main_v4_20240314",
	"query": "SELECT * FROM my_table WHERE id > 100",
	"mysql_host": "127.0.0.1",
	"mysql_database": "mydb",
	"mysql_table": "my_table",
	"user": "dbuser",
	"password": "dbpass",
	"fields": ["an_title", "in_date"]
}
```

### Elasticsearch 요청 스키마
정의: [models/elasticsearch_config.py](models/elasticsearch_config.py)

필드:
- `service`: `"elasticsearch"`
- `project_name`: 문자열(공백 불가, `-`는 `_`로 치환)
- `st_seq`: 정수
- `es_source_index`: 문자열
- `query`: 문자열(ES 쿼리 표현)
- `es_target_hosts`: 문자열(예: `http://es1:9200,http://es2:9200`)
- `es_target_index`: 문자열
- `user`: 문자열
- `password`: 문자열
- `fields`: 문자열 배열(허용 목록 내 값만)

예시:

```json
{
	"service": "elasticsearch",
	"project_name": "news-pipeline",
	"st_seq": 2,
	"es_source_index": "source_index",
	"query": "an_content:AI AND in_date:[2025-01-01 TO 2025-12-31]",
	"es_target_hosts": "http://localhost:9200",
	"es_target_index": "target_index",
	"user": "esuser",
	"password": "espass",
	"fields": ["an_title", "kw_docid"]
}
```

### 응답
성공 시:

```json
{
	"dag_id": "mysql_pipeline_dag",
	"conf": { /* 요청 바디 전체 */ },
	"result": { /* Airflow 응답 JSON */ }
}
```

`dag_id`는 `service`에 따라 아래와 같이 결정됩니다(변경 필요 시 [main.py](main.py) 수정).
- `mysql` → `mysql_pipeline_dag`
- `elasticsearch` → `elasticsearch_pipeline_dag`

Airflow 트리거에는 `logical_date`가 포함되며, 현재 시각 기준 UTC로 하루 전 날짜가 사용됩니다.

## 에러 처리
- 인증 문제(401, 403): 최초 토큰으로 실패 시 토큰 재발급 후 재시도. 재시도에도 실패하면 `401 Unauthorized` 반환
- 토큰 발급 실패/응답 비정상: `502 Bad Gateway`로 매핑해 반환
- 스키마 유효성 실패: Pydantic 예외 메시지로 상세 원인 포함(허용되지 않은 `fields`, 공백 포함 `project_name` 등)

## 로깅
모든 요청/응답은 미들웨어에서 로깅됩니다.
- 포맷: `time | level | logger name | message`
- 기록: 메서드, 경로, 헤더, 바디, 상태코드
- 참고: 민감정보가 헤더/바디에 포함될 수 있으므로 운영 환경에서 로깅 수준과 항목을 적절히 조정하세요.

설정은 [config/logger.py](config/logger.py)를 참고하세요.

## 동작 흐름
1. `POST /register` 수신
2. `service`에 따라 스키마 선택 및 유효성 검사
3. `.env`의 `AIRFLOW_TOKEN` 확인, 없으면 발급([services/airflow_public_api.py](services/airflow_public_api.py))
4. DAG ID 결정 후 Airflow API(`POST /api/v2/dags/{dag_id}/dagRuns`) 호출
5. 401/403일 경우 토큰 재발급 및 재시도
6. 결과 JSON 반환

## 테스트 예시
서버 실행 후 다음과 같이 테스트할 수 있습니다.

```bash
# MySQL 예시
curl -X POST http://localhost:8000/register \
	-H "Content-Type: application/json" \
	-d '{
		"service": "mysql",
		"project_name": "demo-project",
		"st_seq": 1,
		"query": "SELECT 1",
		"mysql_host": "127.0.0.1",
		"mysql_database": "testdb",
		"mysql_table": "t",
		"user": "u",
		"password": "p",
		"fields": ["an_title"]
	}'

# Elasticsearch 예시
curl -X POST http://localhost:8000/register \
	-H "Content-Type: application/json" \
	-d '{
		"service": "elasticsearch",
		"project_name": "es-pipeline",
		"st_seq": 2,
		"es_source_index": "source",
		"query": "an_content:AI",
		"es_target_hosts": "http://localhost:9200",
		"es_target_index": "target",
		"user": "u",
		"password": "p",
		"fields": ["an_content"]
	}'
```

## 프로젝트 구조
```
main.py
pyproject.toml
README.md
config/
	exception.py
	logger.py
models/
	elasticsearch_config.py
	mysql_config.py
services/
	airflow_public_api.py
```

## 개발 팁
- DAG ID 변경: [main.py](main.py)의 `/register` 핸들러에서 `dag_id` 분기 수정
- Airflow 연동: [services/airflow_public_api.py](services/airflow_public_api.py)에서 토큰 발급/트리거 로직 확인
- 필드 정책: [models/*](models) 내 Pydantic 유효성 검사 확인/수정

## 라이선스
내부 프로젝트로 가정하며 별도 라이선스 표기는 없습니다.

