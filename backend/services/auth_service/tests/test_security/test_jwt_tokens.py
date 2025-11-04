"""Security tests for JWT tokens."""

import pytest

from app.core.security import (create_tokens, decode_token, hash_password,
                               verify_password)


@pytest.mark.security
class TestJWTSecurity:
    """Test JWT token security."""

    def test_create_tokens(self):
        """Test token creation."""
        user_id = "user-123"
        tokens = create_tokens(user_id)

        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"

    def test_decode_valid_token(self):
        """Test decoding valid token."""
        user_id = "user-456"
        tokens = create_tokens(user_id)

        payload = decode_token(tokens["access_token"])
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "access"

    def test_decode_invalid_token(self):
        """Test decoding invalid token."""
        payload = decode_token("invalid.token.here")
        assert payload is None

    def test_refresh_token_type(self):
        """Test refresh token has correct type."""
        user_id = "user-789"
        tokens = create_tokens(user_id)

        payload = decode_token(tokens["refresh_token"])
        assert payload["type"] == "refresh"


@pytest.mark.security
class TestPasswordSecurity:
    """Test password hashing security."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "SecurePassword123"
        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) > len(password)

    def test_verify_correct_password(self):
        """Test verifying correct password."""
        password = "SecurePassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed)

    def test_verify_incorrect_password(self):
        """Test verifying incorrect password."""
        password = "SecurePassword123"
        hashed = hash_password(password)

        assert not verify_password("WrongPassword123", hashed)

    def test_argon2_salt_variation(self):
        """Test that each hash has different salt."""
        password = "SecurePassword123"
        hashes = [hash_password(password) for _ in range(3)]

        # All hashes should be different (different salts)
        assert len(set(hashes)) == 3

        # All should verify correctly
        for h in hashes:
            assert verify_password(password, h)
