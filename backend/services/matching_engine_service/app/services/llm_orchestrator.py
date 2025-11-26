from typing import Dict, Any, Optional
from enum import Enum
import google.generativeai as genai
from openai import OpenAI


from common.logging import get_logger
from app.core.config import settings
from app.core.cache import cache_service


logger = get_logger(__name__)


class LLMProvider(str, Enum):
    GEMINI = "gemini"
    OPENAI = "openai"
    FALLBACK = "fallback"


class LLMOrchestrator:
    def __init__(self):
        self.providers = {}
        self.active_provider = LLMProvider.FALLBACK
        self._initialized = False

    def _ensure_initialized(self):
        # only initialize when first used
        if not self._initialized:
            self._initialize_providers()
            self._initialized = True

    def _initialize_providers(self):

        gemini_key = settings.google_api_key
        if gemini_key:
            try:
                genai.configure(api_key=gemini_key)
                self.providers[LLMProvider.GEMINI] = genai.GenerativeModel("gemini-pro")
                self.active_provider = LLMProvider.GEMINI
                logger.info("Gemini provider initialized")
            except Exception as e:
                logger.warning(f"Gemini initialization failed: {e}")
        else:
            logger.warning("No GOOGLE_API_KEY found, using fallback mode")

        # Initialize OpenAI
        openai_key = settings.openai_api_key
        if openai_key:
            try:

                self.providers[LLMProvider.OPENAI] = OpenAI(api_key=openai_key)
                if self.active_provider == LLMProvider.FALLBACK:
                    self.active_provider = LLMProvider.OPENAI
                logger.info("OpenAI provider initialized")
            except Exception as e:
                logger.warning(f"OpenAI initialization failed: {e}")

    async def generate_match_explanation(
        self,
        job_data: Dict[str, Any],
        candidate_data: Dict[str, Any],
        match_scores: Dict[str, Any],
        provider: Optional[LLMProvider] = None,
        skip_cache: bool = False,
    ) -> Dict[str, Any]:

        job_id = job_data.get("id", "unknown")
        candidate_id = candidate_data.get("id", "unknown")

        if not skip_cache:
            cached_explanation = await cache_service.get_llm_explanation(
                job_id, candidate_id
            )
            if cached_explanation:
                logger.info(f"LLM explanation cache HIT for {job_id}-{candidate_id}")
                return cached_explanation

        logger.info("LLM explanation cache MISS, Generating...")

        self._ensure_initialized()
        target_provider = provider or self.active_provider

        if target_provider != LLMProvider.FALLBACK:
            try:
                prompt = self._build_prompt(job_data, candidate_data, match_scores)

                if target_provider == LLMProvider.GEMINI:
                    explanation = self._generate_with_gemini(prompt)
                elif target_provider == LLMProvider.OPENAI:
                    explanation = self._generate_with_openai(prompt)
                else:
                    explanation = self._rule_based_explanation(
                        job_data, candidate_data, match_scores
                    )
            except Exception as e:
                logger.error(f"LLM generation failed: {e}")
                explanation = self._rule_based_explanation(
                    job_data, candidate_data, match_scores
                )
        else:
            explanation = self._rule_based_explanation(
                job_data, candidate_data, match_scores
            )

        # Cache the result
        await cache_service.cache_llm_explanation(job_id, candidate_id, explanation)

        return explanation

    def _build_prompt(
        self,
        job_data: Dict[str, Any],
        candidate_data: Dict[str, Any],
        match_scores: Dict[str, Any],
    ) -> str:

        job_skills = job_data.get("required_skills", [])
        candidate_skills = candidate_data.get("skills", [])

        prompt = f"""You are an expert technical recruiter. Analyze this candidate-job match.

**Job Requirements:**
Title: {job_data.get('title', 'N/A')}
Skills: {', '.join(job_skills[:10])}
Experience: {job_data.get('experience_level', 'N/A')}

**Candidate Profile:**
Skills: {', '.join(candidate_skills[:10])}
Experience: {candidate_data.get('total_experience', 'N/A')} years
Summary: {candidate_data.get('professional_summary', 'N/A')[:200]}

**Match Scores:**
Overall: {int(match_scores.get('overall_score', 0) * 100)}%
Skills: {int(match_scores.get('skill_score', 0) * 100)}%

Provide your analysis in this EXACT format:

EXPLANATION: [2-3 sentences about match quality]
STRENGTHS: [Comma-separated list of 3-5 strengths]
GAPS: [Comma-separated list of 2-4 gaps]
RECOMMENDATION: [One of: STRONG_HIRE, HIRE, CONSIDER, PASS]

Be concise and specific."""

        return prompt

    def _generate_with_gemini(self, prompt: str) -> Dict[str, Any]:
        model = self.providers[LLMProvider.GEMINI]
        response = model.generate_content(prompt)
        return self._parse_response(response.text)

    def _generate_with_openai(self, prompt: str) -> Dict[str, Any]:
        client = self.providers[LLMProvider.OPENAI]
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert technical recruiter."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=500,
        )
        return self._parse_response(response.choices[0].message.content)

    def _parse_response(self, text: str) -> Dict[str, Any]:
        result = {
            "explanation": "",
            "strengths": "",
            "gaps": "",
            "recommendation": "CONSIDER",
        }

        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("EXPLANATION:"):
                result["explanation"] = line.replace("EXPLANATION:", "").strip()
            elif line.startswith("STRENGTHS:"):
                result["strengths"] = line.replace("STRENGTHS:", "").strip()
            elif line.startswith("GAPS:"):
                result["gaps"] = line.replace("GAPS:", "").strip()
            elif line.startswith("RECOMMENDATION:"):
                rec = line.replace("RECOMMENDATION:", "").strip().upper()
                if rec in ["STRONG_HIRE", "HIRE", "CONSIDER", "PASS"]:
                    result["recommendation"] = rec

        if not result["explanation"]:
            result["explanation"] = "Match analysis based on provided scores."

        return result

    def _rule_based_explanation(
        self,
        job_data: Dict[str, Any],
        candidate_data: Dict[str, Any],
        match_scores: Dict[str, Any],
    ) -> Dict[str, Any]:

        score = match_scores.get("overall_score", 0)

        if score >= 0.85:
            rec, exp = "STRONG_HIRE", "Excellent match with strong alignment"
        elif score >= 0.70:
            rec, exp = "HIRE", "Strong candidate with good fit"
        elif score >= 0.55:
            rec, exp = "CONSIDER", "Moderate match with some gaps"
        else:
            rec, exp = "PASS", "Limited alignment with requirements"

        job_skills = set(job_data.get("required_skills", []))
        cand_skills = set(candidate_data.get("skills", []))

        return {
            "explanation": exp,
            "strengths": ", ".join(list(job_skills & cand_skills)[:5])
            or "Basic qualifications",
            "gaps": ", ".join(list(job_skills - cand_skills)[:4]) or "None identified",
            "recommendation": rec,
        }

    def get_provider_status(self) -> Dict[str, Any]:

        self._ensure_initialized()
        return {
            "active": self.active_provider.value,
            "available_providers": [p.value for p in self.providers.keys()],
            "total_providers": len(self.providers),
        }

    def switch_provider(self, provider: LLMProvider) -> bool:

        self._ensure_initialized()
        if provider in self.providers:
            self.active_provider = provider
            logger.info(f"Switched to provider: {provider.value}")
            return True
        logger.warning(f"Provider {provider.value} not available")
        return False


llm_orchestrator = LLMOrchestrator()
