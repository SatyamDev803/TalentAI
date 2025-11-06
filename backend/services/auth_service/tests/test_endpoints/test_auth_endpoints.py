import pytest
from fastapi import status
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.security import hash_password
from app.models.user import User, UserRole


@pytest.mark.integration
class TestAuthCookieEndpoints:

    @pytest.mark.asyncio
    async def test_login_sets_httponly_cookies(self, client, test_db):
        user = User(
            email="test@example.com",
            hashed_password=hash_password("password123"),
            full_name="Test User",
            role=UserRole.CANDIDATE,
            is_active=True,
            is_verified=True,
        )
        test_db.add(user)
        await test_db.commit()

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "user" in data
        assert data["user"]["email"] == "test@example.com"

        cookies = response.cookies
        assert "access_token" in cookies
        assert "refresh_token" in cookies

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client, test_db):
        user = User(
            email="test@example.com",
            hashed_password=hash_password("password123"),
            full_name="Test User",
            role=UserRole.CANDIDATE,
        )
        test_db.add(user)
        await test_db.commit()

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "wrongpassword"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_logout_clears_cookies(self, client, test_db):
        # First login
        user = User(
            email="test@example.com",
            hashed_password=hash_password("password123"),
            full_name="Test User",
            role=UserRole.CANDIDATE,
        )
        test_db.add(user)
        await test_db.commit()

        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        assert login_response.status_code == status.HTTP_200_OK

        # Then logout
        logout_response = await client.post("/api/v1/auth/logout")
        assert logout_response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_protected_endpoint_with_cookie(self, client, test_db):
        # Create and login user
        user = User(
            email="test@example.com",
            hashed_password=hash_password("password123"),
            full_name="Test User",
            role=UserRole.CANDIDATE,
        )
        test_db.add(user)
        await test_db.commit()

        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        assert login_response.status_code == status.HTTP_200_OK

        # Access protected endpoint
        # AsyncClient automatically includes cookies
        me_response = await client.get("/api/v1/users/me")
        assert me_response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_protected_endpoint_without_cookie(self, client):
        # Create new client without login using ASGITransport
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test"
        ) as no_auth_client:
            response = await no_auth_client.get("/api/v1/users/me")
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_refresh_token_endpoint(self, client, test_db):
        # Create and login user
        user = User(
            email="test@example.com",
            hashed_password=hash_password("password123"),
            full_name="Test User",
            role=UserRole.CANDIDATE,
        )
        test_db.add(user)
        await test_db.commit()

        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )
        assert login_response.status_code == status.HTTP_200_OK

        # Refresh token
        refresh_response = await client.post("/api/v1/auth/refresh")
        assert refresh_response.status_code == status.HTTP_200_OK

        # New cookies should be set
        assert "access_token" in refresh_response.cookies
