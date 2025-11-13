"""End-to-end integration tests for complete workflows."""

import io
import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_resume_workflow(client: AsyncClient, auth_headers):
    """Test complete workflow: Upload → Parse → Search → Export."""

    # Step 1: Upload resume
    file_content = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\nJohn Doe\nPython Developer\nSkills: Python, FastAPI, Docker\n%%EOF"
    files = {"file": ("test_resume.pdf", io.BytesIO(file_content), "application/pdf")}

    upload_response = await client.post(
        "/api/v1/resumes/upload",
        files=files,
        headers=auth_headers,
    )

    assert upload_response.status_code == 201
    resume_id = upload_response.json()["resume_id"]

    # Step 2: Parse resume
    parse_response = await client.post(
        f"/api/v1/resumes/{resume_id}/parse",
        headers=auth_headers,
    )

    assert parse_response.status_code == 200
    parse_data = parse_response.json()
    assert parse_data["resume_id"] == resume_id

    # Step 3: Get resume details
    get_response = await client.get(
        f"/api/v1/resumes/{resume_id}",
        headers=auth_headers,
    )

    assert get_response.status_code == 200
    resume_data = get_response.json()
    assert resume_data["id"] == resume_id

    # Step 4: Search for resume
    search_response = await client.get(
        "/api/v1/search/semantic",
        params={"query": "Python developer", "top_k": 5, "min_score": 0.1},
        headers=auth_headers,
    )

    assert search_response.status_code == 200

    # Step 5: Export resumes
    export_response = await client.get(
        "/api/v1/resumes/export/csv",
        headers=auth_headers,
    )

    assert export_response.status_code == 200
    assert export_response.headers["content-type"] == "text/csv; charset=utf-8"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_batch_upload_and_search_workflow(client: AsyncClient, auth_headers):
    """Test batch upload followed by skill search."""

    # Step 1: Batch upload multiple resumes
    files = [
        (
            "files",
            (
                f"resume_{i}.pdf",
                io.BytesIO(b"%PDF-1.4\nTest Resume " + str(i).encode()),
                "application/pdf",
            ),
        )
        for i in range(3)
    ]

    batch_response = await client.post(
        "/api/v1/resumes/batch",
        files=files,
        headers=auth_headers,
    )

    assert batch_response.status_code == 200
    batch_data = batch_response.json()
    assert batch_data["total_files"] == 3
    assert batch_data["uploaded"] >= 1

    # Step 2: List all resumes
    list_response = await client.get(
        "/api/v1/resumes",
        params={"skip": 0, "limit": 10},
        headers=auth_headers,
    )

    assert list_response.status_code == 200
    list_data = list_response.json()
    assert list_data["total"] >= 3

    # Step 3: Get stats
    stats_response = await client.get(
        "/api/v1/resumes/stats",
        headers=auth_headers,
    )

    assert stats_response.status_code == 200
    stats = stats_response.json()
    assert stats["total_resumes"] >= 3


@pytest.mark.integration
@pytest.mark.asyncio
async def test_resume_update_and_search(
    client: AsyncClient, auth_headers, sample_resume_data, db_session
):
    """Test updating resume and searching for it."""
    from app.services.resume_service import ResumeService

    # Step 1: Create resume
    service = ResumeService(db_session)
    resume = await service.create_resume(sample_resume_data)

    # Step 2: Update resume with skills
    update_data = {
        "full_name": "Jane Smith",
        "email": "jane@example.com",
        "skills": {
            "programming_languages": ["Python", "JavaScript"],
            "frameworks": ["FastAPI", "React"],
        },
    }

    update_response = await client.patch(
        f"/api/v1/resumes/{resume.id}",
        json=update_data,
        headers=auth_headers,
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["full_name"] == "Jane Smith"

    # Step 3: Search by skills
    search_response = await client.get(
        "/api/v1/search/skills",
        params={"skills": "Python,FastAPI", "match_all": True},
        headers=auth_headers,
    )

    assert search_response.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_resume_lifecycle(client: AsyncClient, auth_headers):
    """Test complete resume lifecycle: Create → Update → Delete."""

    # Create
    file_content = b"%PDF-1.4\nTest Resume for Lifecycle"
    files = {"file": ("lifecycle.pdf", io.BytesIO(file_content), "application/pdf")}

    create_response = await client.post(
        "/api/v1/resumes/upload",
        files=files,
        headers=auth_headers,
    )

    assert create_response.status_code == 201
    resume_id = create_response.json()["resume_id"]

    # Read
    read_response = await client.get(
        f"/api/v1/resumes/{resume_id}",
        headers=auth_headers,
    )

    assert read_response.status_code == 200

    # Update
    update_response = await client.patch(
        f"/api/v1/resumes/{resume_id}",
        json={"full_name": "Updated Name"},
        headers=auth_headers,
    )

    assert update_response.status_code == 200

    # Soft Delete
    delete_response = await client.delete(
        f"/api/v1/resumes/{resume_id}",
        params={"hard_delete": False},
        headers=auth_headers,
    )

    assert delete_response.status_code == 204

    # Verify deleted (should return 404)
    verify_response = await client.get(
        f"/api/v1/resumes/{resume_id}",
        headers=auth_headers,
    )

    assert verify_response.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_export_workflow(client: AsyncClient, auth_headers):
    """Test searching and exporting results."""

    # Step 1: Perform semantic search
    search_response = await client.get(
        "/api/v1/search/semantic",
        params={"query": "Python FastAPI developer", "top_k": 10, "min_score": 0.2},
        headers=auth_headers,
    )

    assert search_response.status_code == 200

    # Step 2: Export search results as CSV
    csv_export = await client.get(
        "/api/v1/search/export",
        params={"query": "Python FastAPI developer", "format": "csv", "top_k": 10},
        headers=auth_headers,
    )

    assert csv_export.status_code == 200
    assert "text/csv" in csv_export.headers["content-type"]

    # Step 3: Export search results as JSON
    json_export = await client.get(
        "/api/v1/search/export",
        params={"query": "Python FastAPI developer", "format": "json", "top_k": 10},
        headers=auth_headers,
    )

    assert json_export.status_code == 200
    assert "application/json" in json_export.headers["content-type"]
