from typing import Optional
import google.generativeai as genai
from openai import OpenAI


from common.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)

# Check available providers
HAS_GEMINI = True
HAS_OPENAI = True


def generate_with_gemini(context: str) -> Optional[str]:
    if not HAS_GEMINI:
        logger.warning("Gemini not available")
        return None

    if not settings.google_api_key:
        logger.warning("GOOGLE_API_KEY not set")
        return None

    try:
        genai.configure(api_key=settings.google_api_key)
        model = genai.GenerativeModel(settings.gemini_model)

        # Create prompt
        prompt = f"""Generate a professional 2-3 sentence summary for this candidate's resume.
Focus on their key skills, experience level, and specializations.
Be concise and impactful.

Resume Information:
{context}

Professional Summary:"""

        response = model.generate_content(prompt)

        summary = response.text.strip()

        logger.info(f"Generated summary with Gemini ({len(summary)} chars)")
        return summary

    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return None


def generate_with_openai(context: str) -> Optional[str]:
    if not HAS_OPENAI:
        logger.warning("OpenAI not available")
        return None

    if not settings.openai_api_key:
        logger.warning("OPENAI_API_KEY not set")
        return None

    try:
        client = OpenAI(api_key=settings.openai_api_key)

        prompt = f"""Generate a professional 2-3 sentence summary for this candidate's resume.
Focus on their key skills, experience level, and specializations.
Be concise and impactful.

Resume Information:
{context}

Professional Summary:"""

        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "You are a professional resume writer."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=150,
            temperature=0.7,
        )

        summary = response.choices[0].message.content.strip()

        logger.info(f"Generated summary with OpenAI ({len(summary)} chars)")
        return summary

    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        return None


def generate_fallback_summary(resume_data: dict) -> str:

    parts = []

    # Experience level
    years = resume_data.get("total_experience_years", 0)
    if years >= 5:
        parts.append(f"Experienced professional with {years:.0f}+ years")
    elif years >= 2:
        parts.append(f"Professional with {years:.0f} years of experience")
    else:
        parts.append("Emerging professional")

    # Skills
    if resume_data.get("skills"):
        if isinstance(resume_data["skills"], dict):
            # Get top 2 skill categories
            top_categories = sorted(
                resume_data["skills"].items(), key=lambda x: len(x[1]), reverse=True
            )[:2]

            category_names = {
                "programming_languages": "programming",
                "web_frontend": "frontend development",
                "web_backend": "backend development",
                "ai_ml": "AI/ML",
                "cloud_devops": "cloud & DevOps",
                "databases": "database management",
            }

            specializations = [
                category_names.get(cat, cat.replace("_", " "))
                for cat, _ in top_categories
            ]

            if specializations:
                parts.append(f"specializing in {' and '.join(specializations)}")

    # Education
    if resume_data.get("education") and resume_data["education"]:
        degree = resume_data["education"][0].get("degree", "")
        if "master" in degree.lower() or "phd" in degree.lower():
            parts.append("with advanced degree")

    summary = " ".join(parts) + "."
    logger.info(f"Generated fallback summary ({len(summary)} chars)")
    return summary


def build_context_from_resume(resume_data: dict) -> str:
    context_parts = []

    if resume_data.get("full_name"):
        context_parts.append(f"Name: {resume_data['full_name']}")

    if resume_data.get("total_experience_years"):
        years = resume_data["total_experience_years"]
        context_parts.append(f"Experience: {years:.1f} years")

    if resume_data.get("skills"):
        if isinstance(resume_data["skills"], dict):
            all_skills = []
            for skills_list in resume_data["skills"].values():
                all_skills.extend(skills_list[:10])
            skills_text = ", ".join(all_skills[:30])
        else:
            skills_text = ", ".join(resume_data["skills"][:30])
        context_parts.append(f"Skills: {skills_text}")

    if resume_data.get("experience"):
        exp_list = []
        for exp in resume_data["experience"][:3]:
            if exp.get("title") and exp.get("company"):
                exp_list.append(f"{exp['title']} at {exp['company']}")
        if exp_list:
            context_parts.append(f"Experience: {'; '.join(exp_list)}")

    if resume_data.get("education"):
        edu_list = []
        for edu in resume_data["education"][:2]:
            if edu.get("degree"):
                edu_list.append(edu["degree"])
        if edu_list:
            context_parts.append(f"Education: {'; '.join(edu_list)}")

    return "\n".join(context_parts)


def generate_professional_summary(resume_data: dict) -> str:
    # Build context
    context = build_context_from_resume(resume_data)

    if not context:
        logger.warning("No context for summary generation")
        return "Professional with relevant skills and experience."

    # Try providers in priority order
    for provider in settings.llm_providers_list:
        logger.info(f"Trying LLM provider: {provider}")

        if provider == "gemini":
            summary = generate_with_gemini(context)
            if summary:
                return summary

        elif provider == "openai":
            summary = generate_with_openai(context)
            if summary:
                return summary

        elif provider == "fallback":
            return generate_fallback_summary(resume_data)

    logger.warning("All providers failed, using final fallback")
    return generate_fallback_summary(resume_data)
