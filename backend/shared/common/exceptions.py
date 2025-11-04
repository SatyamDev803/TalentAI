class TalentAIException(Exception):
    def __init__(self, message: str, code: str = None, status_code: int = 500):
        self.message = message
        self.code = code or self.__class__.__name__
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(TalentAIException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_ERROR", 401)


class AuthorizationError(TalentAIException):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, "AUTHORIZATION_ERROR", 403)


class ResourceNotFoundError(TalentAIException):
    def __init__(self, resource: str = "Resource"):
        message = f"{resource} not found"
        super().__init__(message, "NOT_FOUND", 404)


class ValidationError(TalentAIException):
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, "VALIDATION_ERROR", 422)


class DuplicateError(TalentAIException):
    def __init__(self, resource: str = "Resource"):
        message = f"{resource} already exists"
        super().__init__(message, "DUPLICATE_ERROR", 409)


class DatabaseError(TalentAIException):
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, "DATABASE_ERROR", 500)


class ExternalServiceError(TalentAIException):
    def __init__(self, service: str = "External service", message: str = None):
        msg = message or f"{service} request failed"
        super().__init__(msg, "EXTERNAL_SERVICE_ERROR", 503)


class InvalidTokenError(AuthenticationError):
    def __init__(self, message: str = "Invalid or expired token"):
        super().__init__(message)


class TokenBlacklistedError(AuthenticationError):
    def __init__(self, message: str = "Token has been revoked"):
        super().__init__(message)
