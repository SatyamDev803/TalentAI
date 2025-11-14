import hashlib
import logging
from pathlib import Path
from typing import Union

logger = logging.getLogger(__name__)


def calculate_file_hash_from_path(file_path: Union[str, Path]) -> str:
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
        logger.info(f"Calculated file hash: {file_hash[:16]}...")

        return file_hash

    except Exception as e:
        logger.error(f"Error calculating file hash: {e}")
        return ""


def calculate_file_hash_from_bytes(file_bytes: bytes) -> str:

    try:
        if not file_bytes:
            logger.warning("Empty file bytes provided")
            return ""

        file_hash = hashlib.sha256(file_bytes).hexdigest()
        logger.info(f"Calculated bytes hash: {file_hash[:16]}...")

        return file_hash

    except Exception as e:
        logger.error(f"Error calculating bytes hash: {e}")
        return ""


# backward compatibility
def calculate_file_hash(file_path: Union[str, Path]) -> str:
    return calculate_file_hash_from_path(file_path)
