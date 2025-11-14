import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class WorkExperience:
    title: str
    company: str
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_months: Optional[int] = None
    is_current: bool = False
    description: List[str] = None

    def __post_init__(self):
        if self.description is None:
            self.description = []


def extract_experiences(text: str) -> List[dict]:

    experiences = []

    # Find Experience section
    experience_pattern = r"(?:^|\n)(Experience|EXPERIENCE|Work Experience|WORK EXPERIENCE|Employment|EMPLOYMENT)\s*\n(.*?)(?=\n(?:Education|EDUCATION|Projects|PROJECTS|Skills|SKILLS|Certifications|$))"

    match = re.search(experience_pattern, text, re.DOTALL | re.MULTILINE)

    if not match:
        logger.warning("No experience section found")
        return []

    experience_section = match.group(2)

    # Pattern: Job Title, Date Range, Company, Location

    # Split by double newlines or significant gaps
    job_blocks = re.split(r"\n\s*\n", experience_section)

    for block in job_blocks:
        if len(block.strip()) < 20:  # Skip empty blocks
            continue

        lines = [line.strip() for line in block.split("\n") if line.strip()]

        if len(lines) < 2:
            continue

        first_line = lines[0]

        # Extract date range from first line
        date_pattern = r"([A-Z][a-z]{2,}\s+\d{4})\s*[–-]\s*([A-Z][a-z]{2,}\s+\d{4}|Present|Current)"
        date_match = re.search(date_pattern, first_line)

        if not date_match:
            continue

        title = first_line[: date_match.start()].strip()
        start_date = date_match.group(1)
        end_date = date_match.group(2)
        is_current = end_date.lower() in ["present", "current"]

        second_line = lines[1] if len(lines) > 1 else ""

        # Try to split company and location
        company_location = second_line

        # Extract location
        location_pattern = (
            r"\b(Remote|Hybrid|[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?(?:,\s*[A-Z]{2,})?)$"
        )
        location_match = re.search(location_pattern, company_location)

        if location_match:
            location = location_match.group(1)
            company = company_location[: location_match.start()].strip()
        else:
            company = company_location
            location = None

        # Clean company name
        company = re.sub(r"\s*\([^)]*\)\s*$", "", company).strip()

        # Calculate duration
        duration = calculate_duration(start_date, end_date, is_current)

        # Extract bullet points
        description = []
        for line in lines[2:]:
            if line.startswith(("–", "-", "•", "*")):
                desc = line.lstrip("–-•*").strip()
                if len(desc) > 20:
                    description.append(desc)

        exp = WorkExperience(
            title=title,
            company=company,
            location=location,
            start_date=start_date,
            end_date=end_date if not is_current else "Present",
            duration_months=duration,
            is_current=is_current,
            description=description[:5],
        )

        experiences.append(
            {
                "title": exp.title,
                "company": exp.company,
                "location": exp.location,
                "start_date": exp.start_date,
                "end_date": exp.end_date,
                "duration_months": exp.duration_months,
                "is_current": exp.is_current,
                "description": exp.description,
            }
        )

    logger.info(f"Extracted {len(experiences)} work experiences")
    return experiences


def calculate_duration(
    start_date: str, end_date: str, is_current: bool
) -> Optional[int]:
    try:
        # Parse start date
        start = datetime.strptime(start_date, "%b %Y")

        # Parse end date
        if is_current:
            end = datetime.now()
        else:
            end = datetime.strptime(end_date, "%b %Y")

        # Calculate months
        months = (end.year - start.year) * 12 + (end.month - start.month)
        return max(1, months)  # At least 1 month

    except Exception as e:
        logger.warning(f"Could not calculate duration: {e}")
        return None


def calculate_total_experience_years(experiences: List[dict]) -> float:
    total_months = 0

    for exp in experiences:
        if exp.get("duration_months"):
            total_months += exp["duration_months"]

    total_years = total_months / 12.0

    logger.info(f"Total experience: {total_years:.1f} years ({total_months} months)")
    return round(total_years, 1)
