from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.chroma_manager import chroma_manager
from common.logging import get_logger

logger = get_logger(__name__)


class VectorSyncService:

    def __init__(self):
        self.chroma = chroma_manager

    async def sync_resume(
        self,
        db: AsyncSession,
        resume_id: str,
        resume_text: str,
        metadata: Optional[Dict] = None,
    ) -> bool:

        try:
            success = self.chroma.add_resume_embedding(
                resume_id=resume_id, text=resume_text, metadata=metadata
            )

            if success:
                logger.info(f"Resume {resume_id} synced to ChromaDB")
            else:
                logger.warning(f"Resume {resume_id} failed to sync to ChromaDB")

            return success

        except Exception as e:
            logger.error(f"Error syncing resume {resume_id}: {e}")
            return False

    async def sync_job(
        self,
        db: AsyncSession,
        job_id: str,
        job_text: str,
        metadata: Optional[Dict] = None,
    ) -> bool:

        try:
            success = self.chroma.add_job_embedding(
                job_id=job_id, text=job_text, metadata=metadata
            )

            if success:
                logger.info(f"Job {job_id} synced to ChromaDB")
            else:
                logger.warning(f"Job {job_id} failed to sync to ChromaDB")

            return success

        except Exception as e:
            logger.error(f"Error syncing job {job_id}: {e}")
            return False

    async def verify_consistency(
        self, db: AsyncSession, entity_id: str, entity_type: str = "resume"
    ) -> Dict[str, Any]:

        try:
            collection_name = f"{entity_type}_embeddings"
            collection = self.chroma.get_or_create_collection(collection_name)

            chroma_result = collection.get(ids=[entity_id])
            chroma_exists = len(chroma_result["ids"]) > 0

            return {
                "entity_id": entity_id,
                "entity_type": entity_type,
                "exists_in_chroma": chroma_exists,
                "checked_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Consistency check failed: {e}")
            return {"entity_id": entity_id, "error": str(e), "exists_in_chroma": False}

    async def batch_sync_resumes(
        self, db: AsyncSession, resumes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:

        total = len(resumes)
        successful = 0
        failed = 0

        for resume in resumes:
            success = await self.sync_resume(
                db=db,
                resume_id=str(resume["id"]),
                resume_text=resume.get("content", ""),
                metadata=resume.get("metadata", {}),
            )

            if success:
                successful += 1
            else:
                failed += 1

        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total * 100) if total > 0 else 0,
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "vector_db": "ChromaDB",
            "status": "operational",
            "embeddings_model": "all-MiniLM-L6-v2",
        }


vector_sync_service = VectorSyncService()
