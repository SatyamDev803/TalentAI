from uuid import UUID

from fastapi import HTTPException, status


def validate_uuid(value: str, field: str = "ID") -> str:
    if not value or value.lower() == "null":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {field}")
    try:
        UUID(value)
        return value
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {field} format"
        )
