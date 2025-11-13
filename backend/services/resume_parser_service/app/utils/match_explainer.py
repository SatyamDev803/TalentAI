"""Generate human-readable match explanations."""

import logging
from typing import List

from app.models.resume import Resume

logger = logging.getLogger(__name__)


def generate_match_reasons(resume: Resume, query: str, score: float) -> List[str]:
    """Generate reasons why a resume matched the query.

    Args:
        resume: Resume object
        query: Search query
        score: Similarity score

    Returns:
        List of human-readable match reasons
    """
    reasons = []
    query_lower = query.lower()
    query_terms = set(query_lower.split())

    # 1. Skills match
    if resume.skills:
        matched_skills = []
        if isinstance(resume.skills, dict):
            for category, category_skills in resume.skills.items():
                for skill in category_skills:
                    if any(term in skill.lower() for term in query_terms):
                        matched_skills.append(skill)

        if matched_skills:
            skills_str = ", ".join(matched_skills[:5])  # Top 5
            if len(matched_skills) > 5:
                skills_str += f" (+{len(matched_skills) - 5} more)"
            reasons.append(f"✓ Matching skills: {skills_str}")

    # 2. Experience level
    if resume.total_experience_years:
        exp_years = resume.total_experience_years
        if exp_years > 0:
            if exp_years < 2:
                level = "Junior"
            elif exp_years < 5:
                level = "Mid-level"
            elif exp_years < 10:
                level = "Senior"
            else:
                level = "Lead/Expert"
            reasons.append(f"✓ Experience: {exp_years} years ({level})")

    # 3. Education match
    if resume.education:
        edu_count = len(resume.education) if isinstance(resume.education, list) else 0
        if edu_count > 0:
            # Check for relevant education keywords
            edu_keywords = ["bachelor", "master", "phd", "computer", "engineering"]
            has_relevant = any(keyword in query_lower for keyword in edu_keywords)
            if has_relevant:
                reasons.append(f"✓ Relevant education ({edu_count} degrees)")
            else:
                reasons.append(f"✓ {edu_count} educational qualifications")

    # 4. Location match (if specified in query)
    if resume.location:
        location_keywords = ["remote", "location", "city", "country"]
        if any(keyword in query_lower for keyword in location_keywords):
            reasons.append(f"✓ Location: {resume.location}")

    # 5. Match quality
    if score >= 0.8:
        reasons.append("✓ Excellent match (80%+ similarity)")
    elif score >= 0.6:
        reasons.append("✓ Good match (60-80% similarity)")
    elif score >= 0.4:
        reasons.append("✓ Moderate match (40-60% similarity)")

    # 6. Name match (exact or partial)
    if resume.full_name and any(
        term in resume.full_name.lower() for term in query_terms
    ):
        reasons.append(f"✓ Name matches query: {resume.full_name}")

    # Default reason if nothing else matches
    if not reasons:
        reasons.append("✓ Semantic similarity with query")

    return reasons
