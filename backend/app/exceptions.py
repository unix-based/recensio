"""
Modern exception handling for the application.
Provides structured error handling with proper HTTP status codes.
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException
from enum import Enum


class ErrorCode(Enum):
    """Standardized error codes for the application."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"


class AppException(Exception):
    """Base exception for application-specific errors."""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(AppException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            details=details,
            status_code=400
        )


class NotFoundError(AppException):
    """Raised when a requested resource is not found."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.NOT_FOUND,
            details=details,
            status_code=404
        )


class ExternalServiceError(AppException):
    """Raised when an external service fails."""
    
    def __init__(self, message: str, service: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            details={**details, "service": service} if details else {"service": service},
            status_code=502
        )


class AIServiceError(ExternalServiceError):
    """Raised when AI service fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            service="AI",
            details=details
        )


def handle_app_exception(exc: AppException) -> HTTPException:
    """Convert AppException to HTTPException for FastAPI."""
    return HTTPException(
        status_code=exc.status_code,
        detail={
            "error_code": exc.error_code.value,
            "message": exc.message,
            "details": exc.details
        }
    )
