import re
from typing import Dict, Any, TypedDict, List
from langgraph.graph import StateGraph, END


from common.logging import get_logger

logger = get_logger(__name__)


class MatchingState(TypedDict):

    job_data: Dict[str, Any]
    candidate_data: Dict[str, Any]
    initial_scores: Dict[str, float]
    vector_similarity: float
    skill_analysis: Dict[str, Any]
    experience_analysis: Dict[str, Any]
    final_recommendation: Dict[str, Any]
    reasoning_steps: List[str]


class LangGraphMatchingWorkflow:

    def __init__(self, llm_orchestrator):
        self.llm = llm_orchestrator
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:

        workflow = StateGraph(MatchingState)

        # Define nodes (steps)
        workflow.add_node("analyze_skills", self.analyze_skills)
        workflow.add_node("analyze_experience", self.analyze_experience)
        workflow.add_node("calculate_scores", self.calculate_scores)
        workflow.add_node("make_recommendation", self.make_recommendation)

        # Define edges (flow)
        workflow.set_entry_point("analyze_skills")
        workflow.add_edge("analyze_skills", "analyze_experience")
        workflow.add_edge("analyze_experience", "calculate_scores")
        workflow.add_edge("calculate_scores", "make_recommendation")
        workflow.add_edge("make_recommendation", END)

        return workflow.compile()

    async def analyze_skills(self, state: MatchingState) -> MatchingState:
        logger.info("Analyzing skills...")

        job_skills = set(state["job_data"].get("required_skills", []))
        candidate_skills = set(state["candidate_data"].get("skills", []))

        matching = job_skills & candidate_skills
        missing = job_skills - candidate_skills
        extra = candidate_skills - job_skills

        state["skill_analysis"] = {
            "matching_skills": list(matching),
            "missing_skills": list(missing),
            "extra_skills": list(extra),
            "match_ratio": len(matching) / len(job_skills) if job_skills else 0,
        }

        state["reasoning_steps"].append(
            f"Skill Analysis: {len(matching)}/{len(job_skills)} required skills matched"
        )

        return state

    async def analyze_experience(self, state: MatchingState) -> MatchingState:
        logger.info("Analyzing experience...")

        candidate_exp = state["candidate_data"].get("total_experience", 0)
        job_exp_str = state["job_data"].get("experience_level", "0")

        # Extract years from string
        match = re.search(r"(\d+)", job_exp_str)
        required_exp = int(match.group(1)) if match else 3

        exp_diff = candidate_exp - required_exp

        if exp_diff >= 2:
            exp_level = "exceeds"
        elif exp_diff >= 0:
            exp_level = "meets"
        elif exp_diff >= -1:
            exp_level = "slightly below"
        else:
            exp_level = "below"

        state["experience_analysis"] = {
            "candidate_years": candidate_exp,
            "required_years": required_exp,
            "difference": exp_diff,
            "assessment": exp_level,
        }

        state["reasoning_steps"].append(
            f"Experience Analysis: Candidate has {candidate_exp} years, {exp_level} requirement"
        )

        return state

    async def calculate_scores(self, state: MatchingState) -> MatchingState:
        logger.info("Calculating scores...")

        skill_score = state["skill_analysis"]["match_ratio"] * 100

        exp_score = min(
            100,
            (
                state["experience_analysis"]["candidate_years"]
                / max(1, state["experience_analysis"]["required_years"])
            )
            * 100,
        )

        vector_score = state.get("vector_similarity", 0.7) * 100

        # Weighted combination
        overall_score = skill_score * 0.4 + exp_score * 0.3 + vector_score * 0.3

        state["initial_scores"] = {
            "skill_score": skill_score,
            "experience_score": exp_score,
            "vector_score": vector_score,
            "overall_score": overall_score,
        }

        state["reasoning_steps"].append(
            f"Score Calculation: Overall={overall_score:.1f}% (Skills={skill_score:.1f}%, Exp={exp_score:.1f}%, Vector={vector_score:.1f}%)"
        )

        return state

    async def make_recommendation(self, state: MatchingState) -> MatchingState:
        logger.info("Making recommendation...")

        overall_score = state["initial_scores"]["overall_score"]
        skill_ratio = state["skill_analysis"]["match_ratio"]

        # Decision logic
        if overall_score >= 85 and skill_ratio >= 0.8:
            recommendation = "STRONG_HIRE"
            reason = "Excellent match across all criteria"
        elif overall_score >= 70 and skill_ratio >= 0.6:
            recommendation = "HIRE"
            reason = "Strong candidate with good alignment"
        elif overall_score >= 55:
            recommendation = "CONSIDER"
            reason = "Moderate match, some gaps exist"
        else:
            recommendation = "PASS"
            reason = "Insufficient alignment with requirements"

        state["final_recommendation"] = {
            "decision": recommendation,
            "confidence": min(100, overall_score),
            "reason": reason,
            "strengths": state["skill_analysis"]["matching_skills"][:5],
            "gaps": state["skill_analysis"]["missing_skills"][:4],
            "reasoning_chain": state["reasoning_steps"],
        }

        state["reasoning_steps"].append(f"Final Decision: {recommendation} - {reason}")

        logger.info(f"Recommendation: {recommendation} ({overall_score:.1f}%)")

        return state

    async def run_workflow(
        self,
        job_data: Dict[str, Any],
        candidate_data: Dict[str, Any],
        vector_similarity: float = 0.7,
    ) -> Dict[str, Any]:

        initial_state: MatchingState = {
            "job_data": job_data,
            "candidate_data": candidate_data,
            "initial_scores": {},
            "vector_similarity": vector_similarity,
            "skill_analysis": {},
            "experience_analysis": {},
            "final_recommendation": {},
            "reasoning_steps": [],
        }

        try:
            # Run workflow
            final_state = await self.workflow.ainvoke(initial_state)

            return {
                "recommendation": final_state["final_recommendation"],
                "scores": final_state["initial_scores"],
                "skill_analysis": final_state["skill_analysis"],
                "experience_analysis": final_state["experience_analysis"],
                "reasoning_chain": final_state["reasoning_steps"],
            }

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            raise


def get_langgraph_workflow():
    global langgraph_workflow

    if langgraph_workflow is None:
        from app.services.llm_orchestrator import llm_orchestrator

        langgraph_workflow = LangGraphMatchingWorkflow(llm_orchestrator)
        logger.info("LangGraph workflow initialized")

    return langgraph_workflow


langgraph_workflow = None
