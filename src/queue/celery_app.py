import os 

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

def make_celery() -> Celery:
    broker_url = os.getenv["CELERY_BROKER_URL"]
    backend_url = os.getenv("CELERY_RESULT_BACKEND")

    app = Celery(
        "regen_queue",
        broker=broker_url,
        backend=backend_url,
        include=["regen_queue.tasks"], 
    )

    # Configuration settings
    app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
    )

    return app

celery_app = make_celery()