import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_job_with_invalid_category_id():
    response = client.post(
        "/api/v1/jobs",
        json={
            "title": "Test Job",
            "description": "Test",
            "job_type": "FULL_TIME",
            "experience_level": "SENIOR",
            "location": "SF",
            "category_id": "invalid-uuid",
        },
        headers={"Authorization": "Bearer valid_token"},
    )
    assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR


def test_get_application_with_null_id():
    response = client.get(
        "/api/v1/applications/null", headers={"Authorization": "Bearer valid_token"}
    )
    assert response.status_code in [400, 401, 404]
    assert response.status_code != 500


def test_list_jobs_with_semantic_search():
    response = client.get(
        "/api/v1/jobs?query=python", headers={"Authorization": "Bearer valid_token"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "total" in data
    assert "jobs" in data
