from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
import dotenv
import requests
import os

from config.logger import get_logger
logger = get_logger(__name__)

load_dotenv()

def get_token() : 
    vars = dotenv.dotenv_values(dotenv.find_dotenv())
    for key, value in vars.items(): 
        logger.debug(f"Env var: {key} = {value}")
        if key == "AIRFLOW_TOKEN" and value != "" and value is not None:
            return value
    token=gen_token()
    dotenv.set_key(dotenv.find_dotenv(), "AIRFLOW_TOKEN", token)
    return token 

def gen_token(airflow_url: str | None = None, username: str | None = None, password: str | None = None) -> str:
    airflow_host = airflow_url or os.environ.get("AIRFLOW_HOST")
    airflow_user = username or os.environ.get("AIRFLOW_USER")
    airflow_password = password or os.environ.get("AIRFLOW_PASSWORD")

    if not airflow_host:
        raise ValueError("AIRFLOW_HOST is not set. Set env or pass airflow_url.")
    if not airflow_user or not airflow_password:
        raise ValueError("AIRFLOW_USER/AIRFLOW_PASSWORD are not set. Set env or pass credentials.")

    token_url = f"{airflow_host}/auth/token"

    try:
        response = requests.post(
            url=token_url,
            headers={"Content-Type": "application/json"},
            json={
                "username": airflow_user,
                "password": airflow_password,
            },
            timeout=15,
        )
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error("Airflow token request failed: %s", str(e))
        raise HTTPException(status_code=502, detail=f"Airflow token request failed: {e}")

    try:
        data = response.json()
    except ValueError:
        raise HTTPException(status_code=502, detail="Invalid JSON in token response")

    token = (
        data.get("access_token")
        or data.get("token")
        or data.get("jwt")
        or data.get("accessToken")
    )

    if not token:
        raise HTTPException(status_code=502, detail="Token not found in Airflow response")

    return token


def post_dags_trigger(token: str, dag_id: str, conf: dict) -> requests.Response:
    response = requests.post(
        url=f"{os.environ.get('AIRFLOW_HOST')}/api/v2/dags/{dag_id}/dagRuns",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "logical_date": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(timespec="seconds"),
            "conf": conf,
        },
        timeout=30,
    )
    logger.info("Airflow trigger response: %s %s", response.status_code, response.reason)
    return response