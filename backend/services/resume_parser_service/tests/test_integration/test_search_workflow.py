# import pytest
# from httpx import AsyncClient


# @pytest.mark.integration
# @pytest.mark.asyncio
# async def test_semantic_to_skill_search(client: AsyncClient, auth_headers):

#     # First do semantic search
#     semantic_response = await client.get(
#         "/api/v1/search/semantic",
#         params={"query": "experienced Python developer", "top_k": 10, "min_score": 0.3},
#         headers=auth_headers,
#     )

#     assert semantic_response.status_code == 200
#     semantic_data = semantic_response.json()

#     # Then do skill-based search
#     skill_response = await client.get(
#         "/api/v1/search/skills",
#         params={"skills": "Python,FastAPI,Docker", "match_all": False},
#         headers=auth_headers,
#     )

#     assert skill_response.status_code == 200
#     skill_data = skill_response.json()

#     # Both should return valid results
#     assert isinstance(semantic_data, dict)
#     assert isinstance(skill_data, list)


# @pytest.mark.integration
# @pytest.mark.asyncio
# async def test_similar_resumes_workflow(
#     client: AsyncClient, auth_headers, sample_resume_data, db_session
# ):
#     from app.services.resume_service import ResumeService

#     # Create a resume
#     service = ResumeService(db_session)
#     resume = await service.create_resume(sample_resume_data)

#     # Find similar resumes
#     similar_response = await client.get(
#         f"/api/v1/search/similar/{resume.id}",
#         params={"top_k": 5, "min_score": 0.5},
#         headers=auth_headers,
#     )

#     assert similar_response.status_code == 200
#     similar_data = similar_response.json()

#     assert isinstance(similar_data, list)


# @pytest.mark.integration
# @pytest.mark.asyncio
# async def test_search_with_different_thresholds(client: AsyncClient, auth_headers):

#     query = "Senior Python Engineer"

#     # High threshold (strict)
#     strict_response = await client.get(
#         "/api/v1/search/semantic",
#         params={"query": query, "top_k": 10, "min_score": 0.8},
#         headers=auth_headers,
#     )

#     assert strict_response.status_code == 200
#     strict_results = strict_response.json()

#     # Low threshold (lenient)
#     lenient_response = await client.get(
#         "/api/v1/search/semantic",
#         params={"query": query, "top_k": 10, "min_score": 0.2},
#         headers=auth_headers,
#     )

#     assert lenient_response.status_code == 200
#     lenient_results = lenient_response.json()

#     # Lenient should return more or equal results
#     assert len(lenient_results.get("results", [])) >= len(
#         strict_results.get("results", [])
#     )


# @pytest.mark.integration
# @pytest.mark.asyncio
# async def test_skill_search_combinations(client: AsyncClient, auth_headers):

#     # Match ALL skills
#     all_response = await client.get(
#         "/api/v1/search/skills",
#         params={"skills": "Python,Docker", "match_all": True},
#         headers=auth_headers,
#     )

#     assert all_response.status_code == 200
#     all_results = all_response.json()

#     # Match ANY skill
#     any_response = await client.get(
#         "/api/v1/search/skills",
#         params={"skills": "Python,Docker", "match_all": False},
#         headers=auth_headers,
#     )

#     assert any_response.status_code == 200
#     any_results = any_response.json()

#     # ANY should return more or equal results than ALL
#     assert len(any_results) >= len(all_results)
