# Elasticsearch
import logging
from typing import Any, Dict, Optional

from elasticsearch import Elasticsearch

logger = logging.getLogger(__name__)


class SearchManager:
    def __init__(self, es_url: str = "http://localhost:9200"):
        self.es_url = es_url
        self.es = None
        self.index_name = "jobs"
        self._initialized = False

    def _ensure_connection(self):
        if self._initialized:
            return

        try:
            self.es = Elasticsearch([self.es_url])
            self._create_index_if_not_exists()
            self._initialized = True
            logger.info("Elasticsearch connected")
        except Exception as e:
            logger.warning(f"Elasticsearch not available: {e}")
            self.es = None
            self._initialized = True

    def _create_index_if_not_exists(self):
        if not self.es:
            return

        try:
            if not self.es.indices.exists(index=self.index_name):
                self.es.indices.create(
                    index=self.index_name,
                    body={
                        "mappings": {
                            "properties": {
                                "id": {"type": "keyword"},
                                "title": {"type": "text", "analyzer": "standard"},
                                "description": {"type": "text", "analyzer": "standard"},
                                "company_id": {"type": "keyword"},
                                "created_by_id": {"type": "keyword"},
                                "job_type": {"type": "keyword"},
                                "experience_level": {"type": "keyword"},
                                "location": {"type": "text"},
                                "is_remote": {"type": "boolean"},
                                "salary_min": {"type": "integer"},
                                "salary_max": {"type": "integer"},
                                "status": {"type": "keyword"},
                                "created_at": {"type": "date"},
                                "published_at": {"type": "date"},
                                "views_count": {"type": "integer"},
                            }
                        }
                    },
                )
                logger.info(f"Created Elasticsearch index: {self.index_name}")
        except Exception as e:
            logger.warning(f"Failed to create ES index: {e}")

    async def index_job(self, job: Dict[str, Any]):
        self._ensure_connection()
        if not self.es:
            logger.debug("Elasticsearch not available, skipping indexing")
            return

        try:
            self.es.index(
                index=self.index_name,
                id=str(job.get("id", "")),
                document={
                    "id": str(job.get("id")),
                    "title": job.get("title"),
                    "description": job.get("description"),
                    "company_id": str(job.get("company_id")),
                    "created_by_id": str(job.get("created_by_id")),
                    "job_type": job.get("job_type"),
                    "experience_level": job.get("experience_level"),
                    "location": job.get("location"),
                    "is_remote": job.get("is_remote", False),
                    "salary_min": job.get("salary_min"),
                    "salary_max": job.get("salary_max"),
                    "status": job.get("status"),
                    "created_at": job.get("created_at"),
                    "published_at": job.get("published_at"),
                    "views_count": job.get("views_count", 0),
                },
            )
            logger.info(f"Indexed job: {job.get('id')}")
        except Exception as e:
            logger.warning(f"Elasticsearch index error: {e}")

    async def search_jobs(
        self,
        query: str = "",
        filters: Optional[Dict] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        self._ensure_connection()
        if not self.es:
            logger.debug("Elasticsearch not available, returning empty results")
            return {"total": 0, "jobs": []}

        try:
            must_clauses = []
            filter_clauses = [{"term": {"status": "PUBLISHED"}}]

            if query:
                must_clauses.append(
                    {
                        "multi_match": {
                            "query": query,
                            "fields": ["title^2", "description", "location"],
                            "fuzziness": "AUTO",
                        }
                    }
                )

            if filters:
                if filters.get("experience_level"):
                    filter_clauses.append(
                        {"term": {"experience_level": filters["experience_level"]}}
                    )
                if filters.get("is_remote") is not None:
                    filter_clauses.append({"term": {"is_remote": filters["is_remote"]}})
                if filters.get("location"):
                    filter_clauses.append({"match": {"location": filters["location"]}})
                if filters.get("salary_min"):
                    filter_clauses.append(
                        {"range": {"salary_min": {"gte": filters["salary_min"]}}}
                    )
                if filters.get("salary_max"):
                    filter_clauses.append(
                        {"range": {"salary_max": {"lte": filters["salary_max"]}}}
                    )
                if filters.get("job_type"):
                    filter_clauses.append({"term": {"job_type": filters["job_type"]}})

            body = {
                "query": {
                    "bool": {
                        "must": must_clauses if must_clauses else [{"match_all": {}}],
                        "filter": filter_clauses,
                    }
                },
                "from": (page - 1) * page_size,
                "size": page_size,
                "sort": [{"published_at": {"order": "desc"}}],
            }

            response = self.es.search(index=self.index_name, body=body)

            return {
                "total": response["hits"]["total"]["value"],
                "jobs": [hit["_source"] for hit in response["hits"]["hits"]],
            }
        except Exception as e:
            logger.warning(f"Elasticsearch search error: {e}")
            return {"total": 0, "jobs": []}

    async def delete_job(self, job_id: str):
        self._ensure_connection()
        if not self.es:
            return

        try:
            self.es.delete(index=self.index_name, id=job_id)
            logger.info(f"Deleted job from ES: {job_id}")
        except Exception as e:
            logger.warning(f"Elasticsearch delete error: {e}")


search_manager = SearchManager()
