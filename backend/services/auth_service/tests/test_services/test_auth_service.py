"""Unit tests for AuthService - Security tests only."""

import pytest

from app.core.security import (create_tokens, decode_token, hash_password,
                               verify_password)


@pytest.mark.unit
class TestJWTTokenGeneration:
    """Test JWT token generation."""

    def test_create_tokens(self):
        """Test token creation."""
        user_id = "user-123"
        tokens = create_tokens(user_id)

        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        assert tokens["access_jti"]
        assert tokens["refresh_jti"]

    def test_decode_access_token(self):
        """Test decoding access token."""
        user_id = "user-123"
        tokens = create_tokens(user_id)

        payload = decode_token(tokens["access_token"])

        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "access"


@pytest.mark.unit
class TestPasswordHashing:
    """Test password hashing."""

    def test_hash_and_verify_password(self):
        """Test password hashing and verification."""
        password = "SecurePassword123"
        hashed = hash_password(password)

        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("WrongPassword123", hashed)

    def test_different_hashes_same_password(self):
        """Test that same password produces different hashes."""
        password = "SecurePassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)
