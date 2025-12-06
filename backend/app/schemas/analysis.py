from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class AnalysisUploadRequest(BaseModel):
    image_path: str
    audio_path: Optional[str] = None
    client_timestamp: str

class AnalysisUploadResponse(BaseModel):
    log_id: UUID
    status: str
