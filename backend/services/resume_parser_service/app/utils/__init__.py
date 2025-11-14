"""Utility functions and modules."""

from app.utils.file_parser import (
    FileParseError,
    extract_text_from_bytes,
    parse_docx,
    parse_file,
    parse_pdf,
    parse_with_ocr,
)
from app.utils.nlp_processor import (
    calculate_experience_years,
    extract_education,
    extract_email,
    extract_experience,
    extract_location,
    extract_name,
    extract_phone,
    extract_summary,
)
from app.utils.skill_extractor import (
    extract_skills,
    get_skill_summary,
    SKILL_DATABASE,
)
from app.utils.experience_extractor import (
    extract_experiences,
    calculate_total_experience_years,
)
from app.utils.embedding_generator import (
    generate_resume_embedding,
    get_embedding_model,
    calculate_similarity,  # NEW!
    search_similar_resumes,  # NEW!
)
from app.utils.ai_summary_generator import (
    generate_professional_summary,
)
from app.utils.file_hash import (
    calculate_file_hash,
    calculate_file_hash_from_bytes,
)

__all__ = [
    # File parsing
    "FileParseError",
    "extract_text_from_bytes",
    "parse_docx",
    "parse_file",
    "parse_pdf",
    "parse_with_ocr",
    # NLP processing
    "calculate_experience_years",
    "extract_education",
    "extract_email",
    "extract_experience",
    "extract_location",
    "extract_name",
    "extract_phone",
    "extract_summary",
    # Skill extraction
    "extract_skills",
    "get_skill_summary",
    "SKILL_DATABASE",
    # Experience extraction
    "extract_experiences",
    "calculate_total_experience_years",
    # Embeddings
    "generate_resume_embedding",
    "get_embedding_model",
    "calculate_similarity",
    "search_similar_resumes",
    # AI Summary
    "generate_professional_summary",
    # File Hash
    "calculate_file_hash",
    "calculate_file_hash_from_bytes",
]
