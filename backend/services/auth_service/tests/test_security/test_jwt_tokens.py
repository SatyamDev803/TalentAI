import pytest
from app.core.security import (
    create_tokens,
    decode_token,
    hash_password,
    verify_password,
)


@pytest.mark.security
class TestJWTSecurity:
    def test_create_tokens(self):
        user_id = "user-123"
        role = "RECRUITER"
        email = "test@example.com"
        company_id = "company-123"

        tokens = create_tokens(
            user_id=user_id,
            role=role,
            email=email,
            company_id=company_id,
        )

        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        assert "access_jti" in tokens
        assert "refresh_jti" in tokens

    def test_decode_valid_access_token(self):
        user_id = "user-456"
        tokens = create_tokens(user_id=user_id)

        payload = decode_token(tokens["access_token"])
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "access"
        assert "jti" in payload
        assert "exp" in payload
        assert "iat" in payload

    def test_decode_valid_refresh_token(self):
        user_id = "user-789"
        tokens = create_tokens(user_id=user_id)

        payload = decode_token(tokens["refresh_token"])
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"

    def test_decode_invalid_token(self):
        payload = decode_token("invalid.token.here")
        assert payload is None

    def test_decode_expired_token(self):
        import jwt
        from app.core.config import AuthConfig

        settings = AuthConfig()
        payload = {
            "sub": "user-123",
            "exp": 0,
            "type": "access",
        }

        expired_token = jwt.encode(
            payload,
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
        )

        result = decode_token(expired_token)
        assert result is None

    def test_token_contains_user_data(self):
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


@pytest.mark.security
class TestPasswordSecurity:

    def test_hash_password(self):
        password = "SecurePassword123"
        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) > len(password)
        assert hashed.startswith("$argon2")

    def test_verify_correct_password(self):
        password = "SecurePassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed)

    def test_verify_incorrect_password(self):
        password = "SecurePassword123"
        hashed = hash_password(password)

        assert not verify_password("WrongPassword123", hashed)

    def test_argon2_salt_variation(self):
        password = "SecurePassword123"
        hashes = [hash_password(password) for _ in range(3)]

        assert len(set(hashes)) == 3

        for h in hashes:
            assert verify_password(password, h)
