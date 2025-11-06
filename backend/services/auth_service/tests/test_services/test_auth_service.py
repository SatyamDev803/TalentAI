import pytest
from app.core.security import (
    create_tokens,
    decode_token,
    hash_password,
    verify_password,
)


@pytest.mark.unit
class TestJWTTokenGeneration:

    def test_create_tokens_basic(self):
        user_id = "user-123"
        tokens = create_tokens(user_id=user_id)

        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        assert tokens["access_jti"]
        assert tokens["refresh_jti"]

    def test_create_tokens_with_user_data(self):
        user_id = "user-123"
        role = "RECRUITER"
        email = "recruiter@example.com"
        company_id = "company-456"

        tokens = create_tokens(
            user_id=user_id,
            role=role,
            email=email,
            company_id=company_id,
        )

        payload = decode_token(tokens["access_token"])
        assert payload["sub"] == user_id
        assert payload["role"] == role
        assert payload["email"] == email
        assert payload["company_id"] == company_id

    def test_decode_access_token(self):
        user_id = "user-123"
        tokens = create_tokens(user_id=user_id)

        payload = decode_token(tokens["access_token"])

        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "access"

    def test_token_expiration_set(self):
        user_id = "user-123"
        tokens = create_tokens(user_id=user_id)

        payload = decode_token(tokens["access_token"])
        assert "exp" in payload
        assert "iat" in payload
        assert payload["exp"] > payload["iat"]


@pytest.mark.unit
class TestPasswordHashing:

    def test_hash_and_verify_password(self):
        password = "SecurePassword123"
        hashed = hash_password(password)

        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("WrongPassword123", hashed)

    def test_different_hashes_same_password(self):
        password = "SecurePassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)

    def test_password_max_length(self):
        from app.core.config import AuthConfig

        settings = AuthConfig()
        long_password = "a" * 200

        hashed = hash_password(long_password)
        assert verify_password(long_password[: settings.password_max_length], hashed)
