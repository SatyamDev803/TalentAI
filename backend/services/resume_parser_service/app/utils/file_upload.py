"""File upload utilities."""

import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import UploadFile, HTTPException, status

from app.core.config import settings


# Ensure upload directory exists
UPLOAD_DIR = Path(settings.upload_dir)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def save_uploaded_file(
    file: UploadFile,
    user_id: uuid.UUID,
) -> tuple[str, int]:
    """Save uploaded file and return file path and size.

    Args:
        file: Uploaded file
        user_id: User ID for organizing files

    Returns:
        Tuple of (file_path, file_size)

    Raises:
        HTTPException: If file validation fails
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided"
        )

    file_extension = Path(file.filename).suffix.lower().lstrip(".")

    if file_extension not in settings.allowed_extensions_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {settings.allowed_extensions}",
        )

    # Read file content
    content = await file.read()
    file_size = len(content)

    # Validate file size
    if file_size > settings.max_file_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.max_file_size} bytes",
        )

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty"
        )

    # Create user-specific directory
    user_dir = UPLOAD_DIR / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = user_dir / unique_filename

    # Save file
    with open(file_path, "wb") as f:
        f.write(content)

    # Return relative path from upload directory
    relative_path = str(file_path.relative_to(UPLOAD_DIR.parent))

    return relative_path, file_size


def delete_file(file_path: str) -> bool:
    """Delete a file from filesystem.

    Args:
        file_path: Path to file

    Returns:
        True if deleted successfully
    """
    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            return True
        return False
    except Exception:
        return False


def get_file_size(file_path: str) -> Optional[int]:
    """Get file size in bytes.

    Args:
        file_path: Path to file

    Returns:
        File size or None if file doesn't exist
    """
    try:
        path = Path(file_path)
        if path.exists():
            return path.stat().st_size
        return None
    except Exception:
        return None
