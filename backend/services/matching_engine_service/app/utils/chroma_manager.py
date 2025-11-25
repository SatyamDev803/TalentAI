from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from common.logging import get_logger

logger = get_logger(__name__)


class ChromaManager:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=Settings(anonymized_telemetry=False, allow_reset=True),
        )

        # Load sentence transformer model
        self.embedding_model = SentenceTransformer(settings.sentence_transformer_model)

        # Collection names
        self.resume_collection_name = "resume_embeddings"
        self.job_collection_name = "job_embeddings"

        logger.info("ChromaDB Manager initialized")

    def get_or_create_collection(self, collection_name: str):
        try:
            collection = self.client.get_or_create_collection(
                name=collection_name, metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Collection '{collection_name}' ready")
            return collection
        except Exception as e:
            logger.error(f"Failed to create collection '{collection_name}': {e}")
            raise

    def add_resume_embedding(
        self, resume_id: str, text: str, metadata: Optional[Dict] = None
    ) -> bool:
        try:
            collection = self.get_or_create_collection(self.resume_collection_name)

            # Generate embedding
            embedding = self.embedding_model.encode(text).tolist()

            # Add to collection
            collection.add(
                ids=[resume_id],
                embeddings=[embedding],
                metadatas=[metadata or {}],
                documents=[text[:1000]],  # Store truncated text
            )

            logger.debug(f"Added resume {resume_id} to Chroma")
            return True
        except Exception as e:
            logger.error(f"Failed to add resume {resume_id}: {e}")
            return False

    def add_job_embedding(
        self, job_id: str, text: str, metadata: Optional[Dict] = None
    ) -> bool:
        try:
            collection = self.get_or_create_collection(self.job_collection_name)

            embedding = self.embedding_model.encode(text).tolist()

            collection.add(
                ids=[job_id],
                embeddings=[embedding],
                metadatas=[metadata or {}],
                documents=[text[:1000]],
            )

            logger.debug(f"Added job {job_id} to Chroma")
            return True
        except Exception as e:
            logger.error(f"Failed to add job {job_id}: {e}")
            return False

    def search_similar_resumes(self, job_text: str, top_k: int = 10) -> List[Dict]:
        try:
            collection = self.get_or_create_collection(self.resume_collection_name)

            # Generate query embedding
            query_embedding = self.embedding_model.encode(job_text).tolist()

            # Search
            results = collection.query(
                query_embeddings=[query_embedding], n_results=top_k
            )

            # Format results
            matches = []
            for i in range(len(results["ids"][0])):
                matches.append(
                    {
                        "resume_id": results["ids"][0][i],
                        "score": 1
                        - results["distances"][0][i],  # Convert distance to similarity
                        "metadata": (
                            results["metadatas"][0][i] if results["metadatas"] else {}
                        ),
                    }
                )

            logger.info(f"Found {len(matches)} similar resumes")
            return matches
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def search_similar_jobs(self, resume_text: str, top_k: int = 10) -> List[Dict]:
        try:
            collection = self.get_or_create_collection(self.job_collection_name)

            query_embedding = self.embedding_model.encode(resume_text).tolist()

            results = collection.query(
                query_embeddings=[query_embedding], n_results=top_k
            )

            matches = []
            for i in range(len(results["ids"][0])):
                matches.append(
                    {
                        "job_id": results["ids"][0][i],
                        "score": 1 - results["distances"][0][i],
                        "metadata": (
                            results["metadatas"][0][i] if results["metadatas"] else {}
                        ),
                    }
                )

            logger.info(f"Found {len(matches)} similar jobs")
            return matches
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def delete_resume(self, resume_id: str) -> bool:
        try:
            collection = self.get_or_create_collection(self.resume_collection_name)
            collection.delete(ids=[resume_id])
            logger.info(f"Deleted resume {resume_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete resume {resume_id}: {e}")
            return False

    def get_collection_stats(self, collection_name: str) -> Dict:
        try:
            collection = self.get_or_create_collection(collection_name)
            count = collection.count()

            return {
                "collection_name": collection_name,
                "document_count": count,
                "embedding_dimension": settings.embedding_dimension,
            }
        except Exception as e:
            logger.error(f"Failed to get stats for {collection_name}: {e}")
            return {}

    def reset_collection(self, collection_name: str) -> bool:
        try:
            self.client.delete_collection(name=collection_name)
            self.get_or_create_collection(collection_name)
            logger.warning(f"Collection '{collection_name}' reset")
            return True
        except Exception as e:
            logger.error(f"Failed to reset collection '{collection_name}': {e}")
            return False


chroma_manager = ChromaManager()
