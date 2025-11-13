"""Tests for Batch Service."""

import io
import uuid
import pytest
from pathlib import Path
from fastapi import UploadFile
from app.services.batch_service import BatchService


@pytest.fixture
async def batch_service(db_session):
    """Create batch service instance."""
    return BatchService(db_session)


@pytest.fixture
def mock_upload_files():
    """Create mock upload files."""
    files = []
    for i in range(3):
        content = f"%PDF-1.4\nTest Resume {i}".encode()
        file = UploadFile(
            filename=f"resume{i}.pdf",
            file=io.BytesIO(content),
        )
        files.append(file)
    return files


@pytest.fixture
def mock_upload_dir(tmp_path):
    """Create mock upload directory."""
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


@pytest.mark.asyncio
async def test_batch_upload_success(
    batch_service, mock_upload_files, mock_upload_dir, test_user_id
):
    """Test successful batch upload."""
    result = await batch_service.batch_upload_resumes(
        files=mock_upload_files,
        user_id=test_user_id,
        upload_dir=mock_upload_dir,
    )

    assert result.total_files == 3
    assert result.uploaded >= 1
    assert len(result.results) == 3
    assert result.processing_time_seconds > 0


@pytest.mark.asyncio
async def test_batch_upload_single_file(batch_service, mock_upload_dir, test_user_id):
    """Test batch upload with single file."""
    content = b"%PDF-1.4\nSingle Resume"
    file = UploadFile(
        filename="single.pdf",
        file=io.BytesIO(content),
    )

    result = await batch_service.batch_upload_resumes(
        files=[file],
        user_id=test_user_id,
        upload_dir=mock_upload_dir,
    )

    assert result.total_files == 1
    assert result.uploaded == 1
    assert len(result.results) == 1
    assert result.results[0].status == "uploaded"


@pytest.mark.asyncio
async def test_batch_upload_mixed_results(batch_service, mock_upload_dir, test_user_id):
    """Test batch upload with mixed success/failure."""
    # Valid PDF
    valid_file = UploadFile(
        filename="valid.pdf",
        file=io.BytesIO(b"%PDF-1.4\nValid"),
    )

    # Invalid file (empty)
    invalid_file = UploadFile(
        filename="invalid.pdf",
        file=io.BytesIO(b""),
    )

    result = await batch_service.batch_upload_resumes(
        files=[valid_file, invalid_file],
        user_id=test_user_id,
        upload_dir=mock_upload_dir,
    )

    assert result.total_files == 2
    # At least one should succeed or fail
    assert result.uploaded + result.failed + result.skipped == 2


@pytest.mark.asyncio
async def test_batch_upload_duplicate_filenames(
    batch_service, mock_upload_dir, test_user_id
):
    """Test batch upload with duplicate filenames."""
    files = [
        UploadFile(
            filename="duplicate.pdf",
            file=io.BytesIO(b"%PDF-1.4\nFile1"),
        ),
        UploadFile(
            filename="duplicate.pdf",
            file=io.BytesIO(b"%PDF-1.4\nFile2"),
        ),
    ]

    result = await batch_service.batch_upload_resumes(
        files=files,
        user_id=test_user_id,
        upload_dir=mock_upload_dir,
    )

    assert result.total_files == 2
    # Should handle duplicates (rename or skip)
    assert len(result.results) == 2


@pytest.mark.asyncio
async def test_batch_upload_empty_list(batch_service, mock_upload_dir, test_user_id):
    """Test batch upload with empty file list."""
    result = await batch_service.batch_upload_resumes(
        files=[],
        user_id=test_user_id,
        upload_dir=mock_upload_dir,
    )

    assert result.total_files == 0
    assert result.uploaded == 0
    assert len(result.results) == 0


@pytest.mark.asyncio
async def test_batch_upload_result_details(
    batch_service, mock_upload_dir, test_user_id
):
    """Test batch upload result contains all details."""
    file = UploadFile(
        filename="test.pdf",
        file=io.BytesIO(b"%PDF-1.4\nTest"),
    )

    result = await batch_service.batch_upload_resumes(
        files=[file],
        user_id=test_user_id,
        upload_dir=mock_upload_dir,
    )

    assert result.total_files == 1
    upload_result = result.results[0]

    # Check result details
    assert upload_result.filename == "test.pdf"
    assert upload_result.resume_id is not None
    assert upload_result.status in ["uploaded", "failed", "skipped"]
    assert upload_result.file_size > 0
    assert isinstance(upload_result.queued_for_parsing, bool)
