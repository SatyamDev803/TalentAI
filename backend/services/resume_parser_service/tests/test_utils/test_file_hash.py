import hashlib
from pathlib import Path
from tempfile import NamedTemporaryFile

from app.utils.file_hash import (
    calculate_file_hash_from_path,
    calculate_file_hash_from_bytes,
    calculate_file_hash,
)


class TestCalculateFileHashFromPath:

    def test_calculate_hash_from_existing_file(self):
        # Create temporary file
        with NamedTemporaryFile(mode="wb", delete=False) as f:
            content = b"This is test content for hashing"
            f.write(content)
            file_path = f.name

        try:
            # Calculate hash
            result = calculate_file_hash_from_path(file_path)

            # Verify result
            expected_hash = hashlib.sha256(content).hexdigest()
            assert result == expected_hash
            assert len(result) == 64  # SHA-256 produces 64 hex characters

        finally:
            # Cleanup
            Path(file_path).unlink()

    def test_hash_of_different_files_differs(self):
        # Create file 1
        with NamedTemporaryFile(mode="wb", delete=False) as f1:
            f1.write(b"Content A")
            file1_path = f1.name

        # Create file 2
        with NamedTemporaryFile(mode="wb", delete=False) as f2:
            f2.write(b"Content B")
            file2_path = f2.name

        try:
            hash1 = calculate_file_hash_from_path(file1_path)
            hash2 = calculate_file_hash_from_path(file2_path)

            assert hash1 != hash2

        finally:
            Path(file1_path).unlink()
            Path(file2_path).unlink()

    def test_hash_of_same_content_is_identical(self):
        content = b"Same content"

        # Create file 1
        with NamedTemporaryFile(mode="wb", delete=False) as f1:
            f1.write(content)
            file1_path = f1.name

        # Create file 2
        with NamedTemporaryFile(mode="wb", delete=False) as f2:
            f2.write(content)
            file2_path = f2.name

        try:
            hash1 = calculate_file_hash_from_path(file1_path)
            hash2 = calculate_file_hash_from_path(file2_path)

            assert hash1 == hash2

        finally:
            Path(file1_path).unlink()
            Path(file2_path).unlink()

    def test_file_not_found_returns_empty_string(self):
        fake_path = "/nonexistent/path/to/file.pdf"

        result = calculate_file_hash_from_path(fake_path)

        assert result == ""

    def test_handles_large_file(self):
        # Create a large file (>1MB)
        large_content = b"A" * (2 * 1024 * 1024)  # 2 MB

        with NamedTemporaryFile(mode="wb", delete=False) as f:
            f.write(large_content)
            file_path = f.name

        try:
            result = calculate_file_hash_from_path(file_path)

            # Verify hash
            expected_hash = hashlib.sha256(large_content).hexdigest()
            assert result == expected_hash

        finally:
            Path(file_path).unlink()

    def test_accepts_path_object(self):
        with NamedTemporaryFile(mode="wb", delete=False) as f:
            content = b"Test content"
            f.write(content)
            file_path = Path(f.name)

        try:
            result = calculate_file_hash_from_path(file_path)

            expected_hash = hashlib.sha256(content).hexdigest()
            assert result == expected_hash

        finally:
            file_path.unlink()


class TestCalculateFileHashFromBytes:

    def test_calculate_hash_from_bytes(self):
        content = b"This is test content"

        result = calculate_file_hash_from_bytes(content)

        expected_hash = hashlib.sha256(content).hexdigest()
        assert result == expected_hash
        assert len(result) == 64

    def test_empty_bytes_returns_empty_string(self):
        result = calculate_file_hash_from_bytes(b"")

        assert result == ""

    def test_none_returns_empty_string(self):
        result = calculate_file_hash_from_bytes(None)

        assert result == ""

    def test_different_bytes_produce_different_hashes(self):
        hash1 = calculate_file_hash_from_bytes(b"Content A")
        hash2 = calculate_file_hash_from_bytes(b"Content B")

        assert hash1 != hash2

    def test_identical_bytes_produce_identical_hashes(self):
        content = b"Same content"

        hash1 = calculate_file_hash_from_bytes(content)
        hash2 = calculate_file_hash_from_bytes(content)

        assert hash1 == hash2

    def test_large_bytes(self):
        large_content = b"X" * (5 * 1024 * 1024)

        result = calculate_file_hash_from_bytes(large_content)

        expected_hash = hashlib.sha256(large_content).hexdigest()
        assert result == expected_hash


class TestCalculateFileHashAlias:

    def test_alias_works_like_from_path(self):
        with NamedTemporaryFile(mode="wb", delete=False) as f:
            content = b"Test content"
            f.write(content)
            file_path = f.name

        try:
            result_alias = calculate_file_hash(file_path)
            result_original = calculate_file_hash_from_path(file_path)

            assert result_alias == result_original

        finally:
            Path(file_path).unlink()


class TestHashConsistency:

    def test_file_and_bytes_produce_same_hash(self):
        content = b"Consistent content test"

        # Create file
        with NamedTemporaryFile(mode="wb", delete=False) as f:
            f.write(content)
            file_path = f.name

        try:
            hash_from_file = calculate_file_hash_from_path(file_path)
            hash_from_bytes = calculate_file_hash_from_bytes(content)

            assert hash_from_file == hash_from_bytes

        finally:
            Path(file_path).unlink()
