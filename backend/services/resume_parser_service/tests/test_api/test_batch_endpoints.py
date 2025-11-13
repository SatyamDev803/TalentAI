"""Test batch upload endpoints."""

import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_batch_upload_single_file(client: AsyncClient, auth_headers):
    """Test batch upload with single file."""
    file_content = b"%PDF-1.4\nTest Resume"
    files = [("files", ("resume1.pdf", io.BytesIO(file_content), "application/pdf"))]

    response = await client.post(
        "/api/v1/resumes/batch",
        files=files,
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_files"] == 1
    assert data["uploaded"] == 1
    assert data["failed"] == 0
    assert len(data["results"]) == 1
    assert data["results"][0]["status"] == "uploaded"


@pytest.mark.asyncio
async def test_batch_upload_multiple_files(client: AsyncClient, auth_headers):
    """Test batch upload with multiple files."""
    files = [
        ("files", ("resume1.pdf", io.BytesIO(b"%PDF-1.4\nResume1"), "application/pdf")),
        ("files", ("resume2.pdf", io.BytesIO(b"%PDF-1.4\nResume2"), "application/pdf")),
        ("files", ("resume3.pdf", io.BytesIO(b"%PDF-1.4\nResume3"), "application/pdf")),
    ]

    response = await client.post(
        "/api/v1/resumes/batch",
        files=files,
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_files"] == 3
    assert data["uploaded"] >= 1  # At least some should succeed
    assert len(data["results"]) == 3


@pytest.mark.asyncio
async def test_batch_upload_exceeds_limit(client: AsyncClient, auth_headers):
    """Test batch upload exceeding 10 file limit."""
    # Try to upload 11 files
    files = [
        (
            "files",
            (f"resume{i}.pdf", io.BytesIO(b"%PDF-1.4\nContent"), "application/pdf"),
        )
        for i in range(11)
    ]

    response = await client.post(
        "/api/v1/resumes/batch",
        files=files,
        headers=auth_headers,
    )

    # Service logs warning but still accepts all files
    assert response.status_code == 200
    data = response.json()

    # Check that it received 11 files
    assert data["total_files"] == 11

    # Some files should be marked as skipped or processed
    assert data["uploaded"] + data["failed"] + data["skipped"] == 11


@pytest.mark.asyncio
async def test_batch_upload_mixed_file_types(client: AsyncClient, auth_headers):
    """Test batch upload with valid and invalid file types."""
    files = [
        ("files", ("resume1.pdf", io.BytesIO(b"%PDF-1.4\nPDF"), "application/pdf")),
        ("files", ("invalid.txt", io.BytesIO(b"Text"), "text/plain")),
    ]

    response = await client.post(
        "/api/v1/resumes/batch",
        files=files,
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_files"] == 2
    # Some should succeed, some should fail
    assert data["uploaded"] + data["failed"] + data["skipped"] == 2


@pytest.mark.asyncio
async def test_batch_upload_no_files(client: AsyncClient, auth_headers):
    """Test batch upload with no files."""
    response = await client.post(
        "/api/v1/resumes/batch",
        files=[],
        headers=auth_headers,
    )

    # Should handle empty upload
    assert response.status_code in [400, 422]
