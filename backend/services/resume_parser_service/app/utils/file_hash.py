"""File hashing utilities for duplicate detection."""

import hashlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def calculate_file_hash(file_path: str | Path) -> str:
    """Calculate SHA-256 hash of file content.

    Args:
        file_path: Path to file

    Returns:
        Hexadecimal hash string
    """
    try:
        file_path = Path(file_path)

        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return ""

        sha256_hash = hashlib.sha256()

        # Read file in chunks for memory efficiency
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        file_hash = sha256_hash.hexdigest()
        logger.info(f"✅ Calculated file hash: {file_hash[:16]}...")

        return file_hash

    except Exception as e:
        logger.error(f"❌ Error calculating file hash: {e}")
        return ""


def calculate_bytes_hash(file_bytes: bytes) -> str:
    """Calculate SHA-256 hash of file bytes.

    Args:
        file_bytes: File content as bytes

    Returns:
        Hexadecimal hash string
    """
    try:
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        logger.info(f"✅ Calculated bytes hash: {file_hash[:16]}...")
        return file_hash

    except Exception as e:
        logger.error(f"❌ Error calculating bytes hash: {e}")
        return ""
