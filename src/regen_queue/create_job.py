from dataclasses import dataclass 
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from auth.supabase_service import get_service_supabase_client

def _get_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

@dataclass(frozen=True)
class JobCreationResult:
    job_id: str

def create_job(kind: str, payload: dict[str, Any], user_id: Optional[str]=None) -> JobCreationResult:
    """ 
    This function creates a 'job' row in the jobs DB.
    """
    job_id = str(uuid4())
    created_at = _get_utc_iso()

    row = {
        "job_id": job_id,
        "user_id": user_id,
        "kind": kind,
        "status": "queued",
        "payload": payload,      
        "created_at": created_at,
        "progress": 0,
        "result_ref": None,
        "error": None,
        "started_at": None,
        "finished_at": None,
    }

    client = get_service_supabase_client()
    response = client.table("jobs").insert(row).execute()
    
    if not getattr(response, "data", None):
        err = getattr(response, "error", None)
        raise RuntimeError(f"Failed to create job: {err or 'Unknown error'}")
    
    return JobCreationResult(job_id=job_id)