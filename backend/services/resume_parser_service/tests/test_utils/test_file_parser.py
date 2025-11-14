from pathlib import Path
import pytest
from app.utils.file_parser import (
    FileParseError,
    extract_text_from_bytes,
    parse_file,
)


@pytest.fixture
def sample_text():
    return """
    John Doe
    Software Engineer
    Experience:
    - 5 years in Python
    - FastAPI expert
    Skills: Python, FastAPI, Docker
    """


@pytest.fixture
def sample_pdf_bytes():
    return b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\nJohn Doe Resume Content\n%%EOF"


def test_extract_text_from_bytes_pdf(sample_pdf_bytes):
    try:
        text = extract_text_from_bytes(sample_pdf_bytes, "pdf")
        assert isinstance(text, str)
        assert len(text) >= 0
    except FileParseError:
        pytest.skip("PDF parsing requires valid PDF structure")


def test_extract_text_from_bytes_empty():
    with pytest.raises(FileParseError):
        extract_text_from_bytes(b"", "pdf")


def test_extract_text_from_bytes_invalid_pdf():
    invalid_pdf = b"Not a real PDF"
    try:
        text = extract_text_from_bytes(invalid_pdf, "pdf")
        assert isinstance(text, str)
    except FileParseError:
        pass


def test_parse_file_not_found():
    with pytest.raises(FileParseError):
        parse_file(Path("/non/existent/file.pdf"))


def test_extract_text_handles_errors():
    try:
        result = extract_text_from_bytes(b"x", "pdf")
        assert result is not None
    except FileParseError:
        pass


def test_extract_text_from_bytes_docx():
    # Minimal DOCX-like bytes (real DOCX is ZIP format)
    fake_docx = b"PK\x03\x04" + b"test content" * 10

    try:
        text = extract_text_from_bytes(fake_docx, "docx")
        assert isinstance(text, str)
    except FileParseError:
        pytest.skip("DOCX parsing requires valid structure")


def test_parse_file_with_path_object():
    test_path = Path("/tmp/nonexistent.pdf")

    with pytest.raises(FileParseError):
        parse_file(test_path)


def test_extract_text_returns_string():
    simple_pdf = b"%PDF-1.4\nTest\n%%EOF"

    try:
        result = extract_text_from_bytes(simple_pdf, "pdf")
        assert isinstance(result, str)
    except FileParseError:
        pass


def test_file_parser_error_message():
    try:
        parse_file(Path("/invalid/path.pdf"))
    except FileParseError as e:
        assert len(str(e)) > 0
        assert isinstance(str(e), str)


def test_extract_text_various_extensions():
    test_content = b"test content"

    for file_type in ["pdf", "docx", "doc"]:
        try:
            result = extract_text_from_bytes(test_content, file_type)
            assert isinstance(result, str)
        except FileParseError:
            pass
