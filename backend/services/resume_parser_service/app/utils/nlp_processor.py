"""NLP processing utilities using spaCy."""

import logging
import re
from typing import Optional

import spacy
from spacy.language import Language

from app.core.config import settings
from app.utils.skill_extractor import extract_skills

logger = logging.getLogger(__name__)

# Global spaCy model instance (loaded once)
_nlp_model: Optional[Language] = None


def load_spacy_model() -> Language:
    """Load spaCy model (singleton pattern).

    Returns:
        Loaded spaCy Language model
    """
    global _nlp_model

    if _nlp_model is None:
        logger.info(f"Loading spaCy model: {settings.spacy_model}")
        try:
            _nlp_model = spacy.load(settings.spacy_model)
            logger.info(f"spaCy model loaded successfully: {settings.spacy_model}")
        except Exception as e:
            logger.error(f"Error loading spaCy model: {str(e)}")
            raise RuntimeError(f"Failed to load spaCy model: {str(e)}")

    return _nlp_model


def extract_entities(text: str) -> dict:
    """Extract named entities from text.

    Args:
        text: Input text

    Returns:
        Dictionary of extracted entities
    """
    nlp = load_spacy_model()
    doc = nlp(text)

    entities = {
        "PERSON": [],
        "ORG": [],
        "GPE": [],  # Geo-Political Entity (locations)
        "DATE": [],
        "MONEY": [],
        "PERCENT": [],
        "PRODUCT": [],
        "EVENT": [],
        "WORK_OF_ART": [],
        "LAW": [],
        "LANGUAGE": [],
        "NORP": [],  # Nationalities, religious, political groups
    }

    for ent in doc.ents:
        if ent.label_ in entities:
            entities[ent.label_].append(ent.text)

    # Remove duplicates
    for key in entities:
        entities[key] = list(set(entities[key]))

    logger.debug(f"Extracted entities: {entities}")
    return entities


def extract_name(text: str) -> Optional[str]:
    """Extract person name from resume text.

    Args:
        text: Resume text

    Returns:
        Extracted name or None
    """
    # Strategy 1: Use first line heuristic (most reliable for resumes)
    lines = text.strip().split("\n")

    for line in lines[:5]:  # Check first 5 lines
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Check if line looks like a name
        words = line.split()

        # Name heuristics:
        # - 2-4 words
        # - All words capitalized
        # - No common resume keywords
        resume_keywords = [
            "resume",
            "cv",
            "curriculum",
            "vitae",
            "experience",
            "education",
            "skills",
            "summary",
            "objective",
            "contact",
            "profile",
            "engineer",
            "developer",
            "manager",
            "analyst",
            "designer",
            "specialist",
        ]

        if 2 <= len(words) <= 4:
            # Check if all words are capitalized and not keywords
            is_name = all(word[0].isupper() for word in words if word) and not any(
                keyword in line.lower() for keyword in resume_keywords
            )

            if is_name:
                return line

    # Strategy 2: Use spaCy NER
    entities = extract_entities(text)

    if entities["PERSON"]:
        # Filter out common false positives
        false_positives = ["docker", "kubernetes", "aws", "google", "microsoft"]

        for person in entities["PERSON"]:
            if person.lower() not in false_positives:
                return person

    return None


def extract_email(text: str) -> Optional[str]:
    """Extract email address from text.

    Args:
        text: Input text

    Returns:
        First email found or None
    """
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    matches = re.findall(email_pattern, text)

    if matches:
        return matches[0]

    return None


def extract_phone(text: str) -> Optional[str]:
    """Extract phone number from text.

    Args:
        text: Input text

    Returns:
        First phone number found or None
    """
    # Common phone patterns
    patterns = [
        r"\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}",
        r"\(\d{3}\)\s*\d{3}-\d{4}",
        r"\d{3}-\d{3}-\d{4}",
        r"\d{10,}",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            # Return first match, clean up
            phone = matches[0]
            # Remove spaces, dashes, parentheses for standardization
            phone = re.sub(r"[^\d+]", "", phone)
            return phone

    return None


def extract_location(text: str) -> Optional[str]:
    """Extract location from resume with improved parsing.

    Looks for location patterns in the header section.
    Avoids extracting section headers or education details.
    """
    # Only look in first 600 characters (header section)
    header = text[:600]

    # Pattern 1: Look for "Location: City, Country" format
    location_pattern = (
        r"(?:Location|Address|Based in):\s*([A-Z][a-zA-Z\s]+,\s*[A-Z][a-zA-Z\s]+)"
    )
    match = re.search(location_pattern, header, re.IGNORECASE)
    if match:
        location = match.group(1).strip()
        # Validate it's not a section header
        if location.lower() not in ["education", "experience", "projects", "skills"]:
            return location

    # Pattern 2: After email, look for City, Country
    email_pattern = r"@[a-z0-9.-]+\.[a-z]{2,}"
    email_match = re.search(email_pattern, header.lower())

    if email_match:
        after_email = header[email_match.end() : email_match.end() + 150]

        # Look for City, Country or City, State, Country
        city_country = re.search(
            r"\|\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*,\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
            after_email,
        )

        if city_country:
            city = city_country.group(1).strip()
            country = city_country.group(2).strip()

            # Validate city is not a degree or section
            invalid_terms = [
                "bachelor",
                "master",
                "phd",
                "education",
                "university",
                "college",
            ]
            if not any(term in city.lower() for term in invalid_terms):
                return f"{city}, {country}"

    # Pattern 3: Common country names in header
    countries = [
        "India",
        "USA",
        "United States",
        "UK",
        "United Kingdom",
        "Canada",
        "Australia",
        "Singapore",
        "Germany",
        "France",
    ]

    for country in countries:
        if country in header[:300]:
            # Try to find city before country
            city_match = re.search(
                rf"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),?\s+{country}", header[:300]
            )
            if city_match:
                city = city_match.group(1).strip()
                if city.lower() not in ["bachelor", "master", "university"]:
                    return f"{city}, {country}"
            return country

    return None


def extract_education(text: str) -> list[dict]:
    """Extract education information with improved parsing.

    Args:
        text: Resume text

    Returns:
        List of education entries
    """
    education = []

    # Find Education section
    education_pattern = r"(?:^|\n)(Education|EDUCATION)\s*\n(.*?)(?=\n(?:Experience|EXPERIENCE|Projects|PROJECTS|Skills|SKILLS|$))"

    match = re.search(education_pattern, text, re.DOTALL | re.MULTILINE)

    if not match:
        logger.warning("No education section found")
        return []

    education_section = match.group(2)

    # Split into blocks
    blocks = re.split(r"\n\s*\n", education_section)

    for block in blocks:
        if len(block.strip()) < 20:
            continue

        lines = [line.strip() for line in block.split("\n") if line.strip()]

        if len(lines) < 2:
            continue

        # First line: Usually institution + location
        institution_line = lines[0]

        # Extract location from end of line
        location_pattern = r"\b([A-Z][a-z]+(?:,\s*[A-Z][a-z]+)?)\s*$"
        location_match = re.search(location_pattern, institution_line)

        institution = institution_line
        location = None

        if location_match:
            location = location_match.group(1)
            institution = institution_line[: location_match.start()].strip()

        # Second line: Usually degree + date range
        degree_line = lines[1] if len(lines) > 1 else ""

        # Extract date range
        date_pattern = r"([A-Z][a-z]{2,}\s+\d{4})\s*[–-]\s*([A-Z][a-z]{2,}\s+\d{4}|Present|Current)"
        date_match = re.search(date_pattern, degree_line)

        degree = degree_line
        start_year = None
        end_year = None

        if date_match:
            # Remove date from degree
            degree = degree_line[: date_match.start()].strip()

            # Extract years
            start_match = re.search(r"\d{4}", date_match.group(1))
            end_match = re.search(r"\d{4}", date_match.group(2))

            if start_match:
                start_year = int(start_match.group())
            if end_match:
                end_year = int(end_match.group())

        # Extract GPA if present
        gpa_pattern = r"(?:GPA|CGPA|Grade):\s*([\d.]+)(?:/[\d.]+)?"
        gpa_match = re.search(gpa_pattern, block, re.IGNORECASE)
        gpa = gpa_match.group(1) if gpa_match else None

        education.append(
            {
                "degree": degree,
                "institution": institution,
                "location": location,
                "start_year": start_year,
                "end_year": end_year,
                "gpa": gpa,
                "is_current": "Present" in degree_line or "Current" in degree_line,
            }
        )

    logger.info(f"✅ Extracted {len(education)} education entries")
    return education


def extract_experience(text: str) -> list[dict]:
    """Extract work experience from text.

    Args:
        text: Resume text

    Returns:
        List of experience entries
    """
    nlp = load_spacy_model()
    doc = nlp(text)

    experience = []

    # Job title keywords (common titles)
    job_titles = [
        "engineer",
        "developer",
        "manager",
        "analyst",
        "designer",
        "consultant",
        "specialist",
        "coordinator",
        "director",
        "lead",
        "senior",
        "junior",
        "intern",
        "associate",
    ]

    # Extract organizations
    orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]

    # Simple heuristic: lines with job titles near organizations
    lines = text.split("\n")

    for i, line in enumerate(lines):
        line_lower = line.lower()

        # Check if line contains job title
        for title in job_titles:
            if title in line_lower:
                entry = {
                    "title": line.strip(),
                    "company": None,
                    "duration": None,
                }

                # Try to find company in nearby lines
                for j in range(max(0, i - 2), min(len(lines), i + 3)):
                    for org in orgs:
                        if org in lines[j]:
                            entry["company"] = org
                            break

                # Try to find date range
                date_pattern = r"\b(19|20)\d{2}\s*-\s*(19|20)\d{2}\b|\b(19|20)\d{2}\s*-\s*present\b"
                date_match = re.search(date_pattern, line, re.IGNORECASE)
                if date_match:
                    entry["duration"] = date_match.group(0)

                experience.append(entry)
                break

    return experience


def calculate_experience_years(experience: list[dict]) -> float:
    """Calculate total years of experience.

    Args:
        experience: List of experience entries

    Returns:
        Total years of experience
    """
    total_years = 0.0

    for exp in experience:
        duration = exp.get("duration", "")
        if duration:
            # Extract years from duration
            years = re.findall(r"\b(19|20)\d{2}\b", duration)
            if len(years) >= 2:
                try:
                    start_year = int(years[0])
                    end_year = int(years[1])
                    total_years += end_year - start_year
                except ValueError:
                    pass
            elif len(years) == 1 and "present" in duration.lower():
                try:
                    start_year = int(years[0])
                    from datetime import datetime

                    current_year = datetime.now().year
                    total_years += current_year - start_year
                except ValueError:
                    pass

    return round(total_years, 1)


def extract_summary(text: str, max_sentences: int = 3) -> Optional[str]:
    """Extract summary from resume text.

    Args:
        text: Resume text
        max_sentences: Maximum number of sentences

    Returns:
        Extracted summary or None
    """
    nlp = load_spacy_model()
    doc = nlp(text)

    # Get first few sentences
    sentences = [sent.text.strip() for sent in doc.sents]

    if sentences:
        summary = " ".join(sentences[:max_sentences])
        return summary

    return None


def extract_resume_data(text: str) -> dict:
    """Extract all resume data from text.

    This is the main function that combines all extraction functions.

    Args:
        text: Raw resume text

    Returns:
        Dictionary containing all extracted resume data
    """
    logger.info("🧠 Extracting resume data using NLP...")

    # Extract individual components
    full_name = extract_name(text)
    email = extract_email(text)
    phone = extract_phone(text)
    location = extract_location(text)
    education = extract_education(text)
    experience = extract_experience(text)

    # Calculate total experience
    total_experience_years = calculate_experience_years(experience)

    # Extract skills (import from skill_extractor)
    try:
        from app.utils.skill_extractor import extract_skills

        skills = extract_skills(text)  # Returns Dict[str, List[str]]

        # Flatten skills for counting
        all_skills = []
        if isinstance(skills, dict):
            for category_skills in skills.values():
                all_skills.extend(category_skills)

        logger.info(
            f"✅ Extracted {len(all_skills)} skills across {len(skills)} categories"
        )

    except Exception as e:
        logger.warning(f"Failed to extract skills: {str(e)}")
        skills = {}
        all_skills = []

    # Build resume data dictionary
    resume_data = {
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "location": location,
        "skills": skills,  # Categorized dict
        "experience": experience,  # List of dicts
        "education": education,  # List of dicts
        "total_experience_years": total_experience_years,
        "certifications": [],
        "languages": [],
    }

    logger.info(
        f"✅ Resume data extracted: "
        f"Name={full_name}, "
        f"Email={email}, "
        f"Skills={len(all_skills)}, "
        f"Experience={total_experience_years}y"
    )

    return resume_data
