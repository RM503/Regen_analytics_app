import json
import logging
import os
from pathlib import Path

import boto3
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)

AWS_REGION = "us-east-1"
SECRETS_NAME = "regen_organics_analytics_app/env"

def running_in_eb() -> bool:
    """
    Detect if running inside Elastic Beanstalk.

    EB does not set AWS_EXECUTION_ENV when you use a custom Docker image,
    so we also allow an explicit APP_ENV=eb flag.
    """
    return (
        "AWS_EXECUTION_ENV" in os.environ
        or "EB_APP_STAGING_DIR" in os.environ
        or os.environ.get("APP_ENV") == "eb"
    )

def running_in_docker() -> bool:
    """
    Detect generic Docker (non-EB).
    """
    return Path("/.dockerenv").exists() and not running_in_eb()

def load_from_sm(overwrite: bool = True) -> None:
    """
    Load environment variables from AWS Secrets Manager.
    """
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    try:
        secret_value = client.get_secret_value(SecretId=SECRETS_NAME)
        secrets = json.loads(secret_value["SecretString"])
    except client.exceptions.ResourceNotFoundException:
        logging.warning(f"SecretsManager: {SECRETS_NAME} not found.")
        return
    except Exception as e:
        logging.error(f"SecretsManager error: {e}")
        return

    for key, value in secrets.items():
        if overwrite or key not in os.environ:
            os.environ[key] = value

def load_from_file(path: str, overwrite: bool = False) -> None:
    if Path(path).exists():
        load_dotenv(path, override=overwrite)


def init_config() -> None:
    """
    Initialize configuration:

    1. EB (Secrets Manager)
    2. Docker (.env.docker)
    3. Local (.env)
    """
    if running_in_eb():
        logging.info("Running in AWS EB environment.")
        load_from_sm(overwrite=True)
    elif running_in_docker():
        logging.info("Running in plain Docker environment.")
        load_from_file(".env.docker", overwrite=False)
    else:
        logging.info("Running in local environment.")
        load_from_file(".env", overwrite=False)
