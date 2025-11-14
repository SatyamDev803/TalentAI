import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_semantic_search(client: AsyncClient, auth_headers):
    response = await client.get(
        "/api/v1/search/semantic",
        params={
            "query": "Python developer with machine learning",
            "top_k": 5,
            "min_score": 0.1,  # Lower threshold for testing
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    # Check correct response schema
    assert "results" in data
    assert "metadata" in data
    assert isinstance(data["results"], list)
    assert data["metadata"]["query"] == "Python developer with machine learning"
    assert data["metadata"]["top_k"] == 5
    assert data["metadata"]["min_score_threshold"] == 0.1

    # Check result structure if any results found
    if len(data["results"]) > 0:
        result = data["results"][0]
        assert "resume" in result
        assert "similarity_score" in result
        assert "match_percentage" in result
        assert "match_reasons" in result
        assert "rank" in result


@pytest.mark.asyncio
async def test_skill_search_any(client: AsyncClient, auth_headers):
    response = await client.get(
        "/api/v1/search/skills",
        params={"skills": "Python,Java", "match_all": False},
        headers=auth_headers,
    )

    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_skill_search_all(client: AsyncClient, auth_headers):
    response = await client.get(
        "/api/v1/search/skills",
        params={"skills": "Python,Docker", "match_all": True},
        headers=auth_headers,
    )

    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_semantic_search_no_results(client: AsyncClient, auth_headers):
    response = await client.get(
        "/api/v1/search/semantic",
        params={
            "query": "COBOL mainframe developer",
            "top_k": 10,
            "min_score": 0.9,  # Very high threshold
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "metadata" in data
    assert len(data["results"]) == 0


@pytest.mark.asyncio
async def test_semantic_search_validation(client: AsyncClient, auth_headers):
    # Test invalid top_k
    response = await client.get(
        "/api/v1/search/semantic",
        params={"query": "Python", "top_k": 100, "min_score": 0.3},
        headers=auth_headers,
    )
    assert response.status_code == 422

    # Test invalid min_score
    response = await client.get(
        "/api/v1/search/semantic",
        params={"query": "Python", "top_k": 10, "min_score": 1.5},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_export_search_results_csv(client: AsyncClient, auth_headers):
    response = await client.get(
        "/api/v1/search/export",
        params={
            "query": "Python developer",
            "format": "csv",
            "top_k": 10,
            "min_score": 0.3,
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]


@pytest.mark.asyncio
async def test_export_search_results_json(client: AsyncClient, auth_headers):
    response = await client.get(
        "/api/v1/search/export",
        params={
            "query": "Python developer",
            "format": "json",
            "top_k": 10,
            "min_score": 0.3,
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert "attachment" in response.headers["content-disposition"]
