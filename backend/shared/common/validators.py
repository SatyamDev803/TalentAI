import re
from typing import Optional


class Validator:
    @staticmethod
    def validate_email(email: str) -> bool:
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_password(password: str, min_length: int = 8) -> tuple[bool, str]:
        if len(password) < min_length:
            return False, f"Password must be at least {min_length} characters"

        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"

        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"

        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit"

        return True, ""

    @staticmethod
    def validate_username(username: str, min_length: int = 3) -> tuple[bool, str]:
        if len(username) < min_length:
            return False, f"Username must be at least {min_length} characters"

        pattern = r"^[a-zA-Z0-9_-]+$"
        if not re.match(pattern, username):
            return (
                False,
                "Username can only contain letters, numbers, underscores, and hyphens",
            )

        return True, ""

    @staticmethod
    def validate_not_empty(value, field_name: str) -> tuple[bool, str]:
        if not value or (isinstance(value, str) and not value.strip()):
            return False, f"{field_name} cannot be empty"

        return True, ""

    @staticmethod
    def validate_length(
        value: str,
        min_len: Optional[int] = None,
        max_len: Optional[int] = None,
    ) -> tuple[bool, str]:
        if min_len is not None and len(value) < min_len:
            return False, f"Length must be at least {min_len}"

        if max_len is not None and len(value) > max_len:
            return False, f"Length must be at most {max_len}"

        return True, ""
