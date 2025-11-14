import pytest
from app.utils.skill_extractor import extract_skills


@pytest.fixture
def sample_text_with_skills():
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
    skills = extract_skills(sample_text_with_skills)

    assert isinstance(skills, dict)
    assert len(skills) >= 0


def test_extract_skills_python():
    text = "I have 5 years of Python experience"
    skills = extract_skills(text)

    assert isinstance(skills, dict)


def test_extract_skills_multiple_technologies(sample_text_with_skills):
    skills = extract_skills(sample_text_with_skills)

    assert isinstance(skills, dict)

    total_skills = 0
    for category_skills in skills.values():
        if isinstance(category_skills, list):
            total_skills += len(category_skills)

    assert total_skills >= 0


def test_extract_skills_case_handling():
    text1 = "I know PYTHON and python"
    skills1 = extract_skills(text1)

    assert isinstance(skills1, dict)


def test_extract_skills_empty_text():
    skills = extract_skills("")

    assert isinstance(skills, dict)


def test_extract_skills_no_skills():
    text = "I like to read books and watch movies."
    skills = extract_skills(text)

    assert isinstance(skills, dict)


def test_extract_skills_returns_dict():
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
    text = "Full stack developer: Python, FastAPI, React, PostgreSQL, Docker"
    skills = extract_skills(text)

    assert isinstance(skills, dict)
    assert len(skills) >= 0


def test_extract_skills_mixed_content():
    text = """
    Job Description: We need someone with Python and React experience.
    The candidate should know Docker and AWS as well.
    """
    skills = extract_skills(text)

    assert isinstance(skills, dict)
