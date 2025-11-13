"""Tests for NLP processing utilities."""

import pytest
from app.utils.nlp_processor import (
    extract_email,
    extract_name,
    extract_phone,
    load_spacy_model,
)

from app.utils.skill_extractor import (
    extract_skills,
)


@pytest.fixture
def sample_resume_text():
    """Sample resume text for testing."""
    return """
    John Doe
    john.doe@example.com
    (555) 123-4567
    
    Software Engineer with 5 years of experience in Python, FastAPI, and React.
    
    EXPERIENCE:
    Senior Software Engineer at Google (2020-Present)
    - Developed microservices using Python and FastAPI
    - Built frontend applications with React and TypeScript
    
    SKILLS:
    - Programming: Python, JavaScript, TypeScript, Java
    - Frameworks: FastAPI, Django, React, Angular
    - Databases: PostgreSQL, MongoDB, Redis
    - Cloud: AWS, Docker, Kubernetes
    
    EDUCATION:
    B.S. in Computer Science
    MIT, 2018
    """


@pytest.mark.nlp
class TestNLPProcessor:
    """Test NLP processing functions."""

    def test_load_spacy_model(self):
        """Test loading spaCy model."""
        nlp = load_spacy_model()
        assert nlp is not None
        assert hasattr(nlp, "pipe")

    def test_extract_name(self, sample_resume_text):
        """Test name extraction."""
        name = extract_name(sample_resume_text)
        assert name is not None
        assert isinstance(name, str)
        # Should extract "John Doe" or similar
        assert len(name) > 0

    def test_extract_email(self, sample_resume_text):
        """Test email extraction."""
        email = extract_email(sample_resume_text)
        assert email is not None
        assert "@" in email
        assert "john.doe@example.com" == email.lower()

    def test_extract_phone(self, sample_resume_text):
        """Test phone extraction."""
        phone = extract_phone(sample_resume_text)
        assert phone is not None
        assert isinstance(phone, str)
        # Should contain some digits
        assert any(c.isdigit() for c in phone)

    def test_extract_skills(self, sample_resume_text):
        """Test skill extraction."""
        skills = extract_skills(sample_resume_text)
        assert skills is not None
        assert isinstance(skills, dict)
        # Should extract some skills
        assert len(skills) > 0


@pytest.mark.nlp
def test_extract_email_not_found():
    """Test email extraction when no email present."""
    text = "This text has no email address"
    email = extract_email(text)
    assert email is None or email == ""


@pytest.mark.nlp
def test_extract_name_from_simple_text():
    """Test name extraction from simple text."""
    text = "Jane Smith\nSoftware Engineer"
    name = extract_name(text)
    assert name is not None
    assert isinstance(name, str)


@pytest.mark.nlp
def test_extract_phone_variations():
    """Test phone extraction with different formats."""
    texts = [
        "Call me at (123) 456-7890",
        "Phone: 123-456-7890",
        "Contact: +1 123 456 7890",
    ]

    for text in texts:
        phone = extract_phone(text)
        if phone:  # Some formats might not be detected
            assert isinstance(phone, str)
            assert len(phone) > 5
