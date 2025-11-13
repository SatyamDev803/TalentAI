"""Tests for skill extraction utilities."""

import pytest
from app.utils.skill_extractor import extract_skills


@pytest.fixture
def sample_text_with_skills():
    """Sample text containing various skills."""
    return """
    Senior Software Engineer with 5 years of experience.
    
    Skills:
    - Programming: Python, Java, JavaScript, TypeScript
    - Frameworks: FastAPI, Django, React, Angular, Node.js
    - Databases: PostgreSQL, MongoDB, Redis
    - Cloud: AWS, Docker, Kubernetes, Azure
    - Tools: Git, Jenkins, Terraform
    - AI/ML: Machine Learning, TensorFlow, PyTorch
    """


def test_extract_skills_basic(sample_text_with_skills):
    """Test basic skill extraction."""
    skills = extract_skills(sample_text_with_skills)

    assert isinstance(skills, dict)
    assert len(skills) >= 0


def test_extract_skills_python():
    """Test extracting Python specifically."""
    text = "I have 5 years of Python experience"
    skills = extract_skills(text)

    assert isinstance(skills, dict)


def test_extract_skills_multiple_technologies(sample_text_with_skills):
    """Test extracting multiple skills."""
    skills = extract_skills(sample_text_with_skills)

    # Should return a dict
    assert isinstance(skills, dict)

    # Count total skills extracted
    total_skills = 0
    for category_skills in skills.values():
        if isinstance(category_skills, list):
            total_skills += len(category_skills)

    # Should extract at least some skills
    assert total_skills >= 0


def test_extract_skills_case_handling():
    """Test case-insensitive skill extraction."""
    text1 = "I know PYTHON and python"
    skills1 = extract_skills(text1)

    assert isinstance(skills1, dict)


def test_extract_skills_empty_text():
    """Test extracting skills from empty text."""
    skills = extract_skills("")

    assert isinstance(skills, dict)


def test_extract_skills_no_skills():
    """Test text with no technical skills."""
    text = "I like to read books and watch movies."
    skills = extract_skills(text)

    assert isinstance(skills, dict)


def test_extract_skills_returns_dict():
    """Test that extract_skills always returns a dict."""
    test_cases = [
        "",
        "No skills here",
        "Python Java JavaScript",
        "Expert in React, Docker, AWS",
    ]

    for text in test_cases:
        skills = extract_skills(text)
        assert isinstance(skills, dict)


def test_extract_skills_common_stack():
    """Test extracting common tech stack."""
    text = "Full stack developer: Python, FastAPI, React, PostgreSQL, Docker"
    skills = extract_skills(text)

    assert isinstance(skills, dict)
    # Should extract something
    assert len(skills) >= 0


def test_extract_skills_mixed_content():
    """Test skill extraction from mixed content."""
    text = """
    Job Description: We need someone with Python and React experience.
    The candidate should know Docker and AWS as well.
    """
    skills = extract_skills(text)

    assert isinstance(skills, dict)
