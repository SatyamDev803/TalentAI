from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class VectorSyncRequest(BaseModel):

    content: str = Field(..., description="Text content to embed and sync")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata"
    )


class VectorSyncResponse(BaseModel):

    success: bool
    entity_id: str
    entity_type: str
    message: str
    chroma_synced: Optional[bool] = None


class ConsistencyCheckResponse(BaseModel):

    entity_id: str
    entity_type: str
    chroma_exists: bool
    consistent: bool
    checked_at: str
