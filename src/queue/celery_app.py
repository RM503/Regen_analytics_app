import os 

from celery import Celery 

def make_celery() -> Celery:
    broker_url = os.environ["CELERY_BROKER_URL"]
    backend_url = os.environ.get("CELERY_RESULT_BACKEND")

    celery = Celery(
        "regen_queue",
        broker=broker_url,
        backend=backend_url,
        include=["queue.tasks"], 
    )

    celery.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
    )

    return celery

celery_app = make_celery()