"""Enhanced skill extraction with categorization."""

import logging
import re
from collections import defaultdict
from typing import Dict, List, Set

import spacy

logger = logging.getLogger(__name__)

# Load spaCy model once
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.warning(
        "spaCy model not found. Run: python -m spacy download en_core_web_sm"
    )
    nlp = None


# Categorized skill database
SKILL_DATABASE = {
    "programming_languages": {
        "Python",
        "Java",
        "JavaScript",
        "TypeScript",
        "Go",
        "Rust",
        "C++",
        "C#",
        "Ruby",
        "PHP",
        "Swift",
        "Kotlin",
        "Scala",
        "R",
        "MATLAB",
    },
    "web_frontend": {
        "React",
        "Vue.js",
        "Angular",
        "Next.js",
        "Svelte",
        "HTML",
        "CSS",
        "Tailwind CSS",
        "Bootstrap",
        "SASS",
        "Material-UI",
        "Redux",
        "Webpack",
        "Vite",
    },
    "web_backend": {
        "Node.js",
        "Express.js",
        "FastAPI",
        "Django",
        "Flask",
        "Spring Boot",
        "Ruby on Rails",
        "ASP.NET",
        "Laravel",
        "Nest.js",
    },
    "databases": {
        "PostgreSQL",
        "MySQL",
        "MongoDB",
        "Redis",
        "SQLite",
        "Cassandra",
        "DynamoDB",
        "Oracle",
        "SQL Server",
        "Elasticsearch",
        "Neo4j",
    },
    "cloud_devops": {
        "AWS",
        "Azure",
        "GCP",
        "Docker",
        "Kubernetes",
        "Terraform",
        "Jenkins",
        "GitHub Actions",
        "GitLab CI",
        "CircleCI",
        "Ansible",
        "Nginx",
        "Apache",
        "Linux",
        "Bash",
    },
    "ai_ml": {
        "TensorFlow",
        "PyTorch",
        "Keras",
        "scikit-learn",
        "Pandas",
        "NumPy",
        "OpenCV",
        "Hugging Face",
        "LangChain",
        "Machine Learning",
        "Deep Learning",
        "NLP",
        "Computer Vision",
        "LLM",
        "RAG",
    },
    "data_tools": {
        "Jupyter",
        "Matplotlib",
        "Seaborn",
        "Plotly",
        "Tableau",
        "Power BI",
        "Apache Spark",
        "Airflow",
        "Kafka",
    },
    "testing_tools": {"Jest", "Pytest", "JUnit", "Selenium", "Cypress", "Postman"},
    "soft_skills": {
        "Leadership",
        "Communication",
        "Problem Solving",
        "Team Collaboration",
        "Agile",
        "Scrum",
        "Project Management",
    },
}


def extract_skills(text: str) -> Dict[str, List[str]]:
    """Extract and categorize skills from resume text.

    Args:
        text: Resume text

    Returns:
        Dictionary of categorized skills
    """
    found_skills = defaultdict(set)
    text_lower = text.lower()

    # Extract skills from each category
    for category, skills in SKILL_DATABASE.items():
        for skill in skills:
            # Case-insensitive search with word boundaries
            pattern = r"\b" + re.escape(skill.lower()) + r"\b"
            if re.search(pattern, text_lower):
                found_skills[category].add(skill)

    # Use spaCy for additional skill extraction
    if nlp:
        found_skills = enhance_with_nlp(text, found_skills)

    # Convert sets to sorted lists
    categorized_skills = {
        category: sorted(list(skills))
        for category, skills in found_skills.items()
        if skills
    }

    # Add summary
    total_skills = sum(len(skills) for skills in categorized_skills.values())
    logger.info(
        f"Extracted {total_skills} skills across {len(categorized_skills)} categories"
    )

    return categorized_skills


def enhance_with_nlp(
    text: str, existing_skills: Dict[str, Set[str]]
) -> Dict[str, Set[str]]:
    """Use NLP to find additional technical terms."""
    doc = nlp(text)

    # Extract noun chunks that might be skills
    for chunk in doc.noun_chunks:
        chunk_text = chunk.text

        # Check if it's a potential skill (2-3 words, contains technical terms)
        if 2 <= len(chunk_text.split()) <= 3:
            # Check against known skills
            for category, skills in SKILL_DATABASE.items():
                for skill in skills:
                    if skill.lower() in chunk_text.lower():
                        existing_skills[category].add(skill)

    return existing_skills


def get_skill_summary(categorized_skills: Dict[str, List[str]]) -> dict:
    """Generate skill summary statistics."""
    return {
        "total_skills": sum(len(skills) for skills in categorized_skills.values()),
        "categories": len(categorized_skills),
        "top_category": (
            max(categorized_skills.items(), key=lambda x: len(x[1]))[0]
            if categorized_skills
            else None
        ),
        "breakdown": {cat: len(skills) for cat, skills in categorized_skills.items()},
    }
