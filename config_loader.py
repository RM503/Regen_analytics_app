# This script determines the appropriate way to load environment variables
import json
import os
from pathlib import Path

import boto3
from dotenv import load_dotenv

AWS_REGION = "us-east-1"
SECRETS_NAME = "regen_organics_analytics_app/env"

def running_in_eb() -> bool:
    """Detect if running in AWS Elastic Beanstalk."""
    return "AWS_EXECUTION_ENV" in os.environ or "EB_APP_STAGING_DIR" in os.environ

def running_in_docker() -> bool:
    """Detect if running in Docker but not EB."""
    return Path("/.dockerenv").exists() and not running_in_eb()

def load_from_sm(overwrite: bool = True) -> None:
    """Load secrets from AWS Secrets Manager into environment variables."""
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    try:
        secret_value = client.get_secret_value(SecretId=SECRETS_NAME)
        secrets = json.loads(secret_value["SecretString"])
    except client.exceptions.ResourceNotFoundException:
        print(f"SecretsManager: {SECRETS_NAME} not found.")
        return
    except Exception as e:
        print(f"SecretsManager error: {e}")
        return

    for key, value in secrets.items():
        if overwrite or key not in os.environ:
            os.environ[key] = value

def load_from_file(path: str, overwrite: bool = False) -> None:
    """Load environment variables from a .env file."""
    if Path(path).exists():
        load_dotenv(path, override=overwrite)

def init_config() -> None:
    """
    Initialize configuration in the correct order:
    1. EB (Secrets Manager)
    2. Docker (.env.docker)
    3. Local (.env)
    Precedence: EB > Docker > Local
    """
    if running_in_eb():
        load_from_sm(overwrite=True)
    elif running_in_docker():
        load_from_file(".env.docker", overwrite=False)
    else:
        load_from_file(".env", overwrite=False)
