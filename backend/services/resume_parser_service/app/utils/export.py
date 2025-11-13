"""Export utilities for search results."""

import csv
import json
import logging
from io import StringIO
from typing import List

from app.schemas.search import ResumeSearchResult

logger = logging.getLogger(__name__)


def export_search_results_csv(results: List[ResumeSearchResult], query: str) -> str:
    """Export search results as CSV string.

    Args:
        results: List of search results
        query: Search query

    Returns:
        CSV string
    """
    output = StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(
        [
            "Rank",
            "Full Name",
            "Email",
            "Phone",
            "Location",
            "Experience (Years)",
            "Skills Count",
            "Education Count",
            "Similarity Score",
            "Match %",
            "Filename",
        ]
    )

    # Data rows
    for result in results:
        resume = result.resume

        # Count skills
        skills_count = 0
        if resume.skills:
            if isinstance(resume.skills, dict):
                skills_count = sum(len(s) for s in resume.skills.values())
            elif isinstance(resume.skills, list):
                skills_count = len(resume.skills)

        # Count education
        edu_count = len(resume.education) if resume.education else 0

        writer.writerow(
            [
                result.rank,
                resume.full_name or "",
                resume.email or "",
                resume.phone or "",
                resume.location or "",
                resume.total_experience_years or 0,
                skills_count,
                edu_count,
                result.similarity_score,
                result.match_percentage,
                resume.filename,
            ]
        )

    csv_content = output.getvalue()
    output.close()

    logger.info(f"✅ Exported {len(results)} results to CSV")

    return csv_content


def export_search_results_json(
    results: List[ResumeSearchResult], query: str, metadata: dict
) -> str:
    """Export search results as JSON string.

    Args:
        results: List of search results
        query: Search query
        metadata: Search metadata

    Returns:
        JSON string
    """
    # Build JSON structure
    export_data = {
        "query": query,
        "metadata": metadata,
        "total_results": len(results),
        "results": [],
    }

    for result in results:
        resume = result.resume

        result_dict = {
            "rank": result.rank,
            "similarity_score": result.similarity_score,
            "match_percentage": result.match_percentage,
            "match_reasons": result.match_reasons,
            "resume": {
                "id": str(resume.id),
                "full_name": resume.full_name,
                "email": resume.email,
                "phone": resume.phone,
                "location": resume.location,
                "skills": resume.skills,
                "experience": resume.total_experience_years,
                "education": resume.education,
                "filename": resume.filename,
            },
        }

        export_data["results"].append(result_dict)

    json_content = json.dumps(export_data, indent=2, default=str)

    logger.info(f"✅ Exported {len(results)} results to JSON")

    return json_content
