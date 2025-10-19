"""
Modern middleware for the application.
Provides structured logging, error handling, and performance monitoring.
"""

import time
import uuid
from typing import Callable, Dict, Any
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.exceptions import AppException, handle_app_exception
from app.logger import get_module_logger

logger = get_module_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request logging."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with structured logging.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response from next handler
        """
        # Generate request ID for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log request start
        start_time = time.time()
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent")
            }
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Log successful response
            duration = time.time() - start_time
            logger.info(
                f"Request completed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "duration": duration,
                    "response_size": response.headers.get("content-length", 0)
                }
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Log error response
            duration = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "duration": duration
                }
            )
            
            # Handle application exceptions
            if isinstance(e, AppException):
                return JSONResponse(
                    status_code=e.status_code,
                    content={
                        "error_code": e.error_code.value,
                        "message": e.message,
                        "details": e.details,
                        "request_id": request_id
                    }
                )
            
            # Handle unexpected exceptions
            return JSONResponse(
                status_code=500,
                content={
                    "error_code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred",
                    "request_id": request_id
                }
            )


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for performance monitoring."""
    
    def __init__(self, app, slow_request_threshold: float = 1.0):
        """Initialize performance monitoring middleware.
        
        Args:
            app: FastAPI application
            slow_request_threshold: Threshold for slow requests in seconds
        """
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Monitor request performance.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response from next handler
        """
        start_time = time.time()
        
        try:
            response = await call_next(request)
            return response
        finally:
            duration = time.time() - start_time
            
            # Log slow requests
            if duration > self.slow_request_threshold:
                logger.warning(
                    f"Slow request detected: {request.method} {request.url.path}",
                    extra={
                        "request_id": getattr(request.state, "request_id", None),
                        "duration": duration,
                        "threshold": self.slow_request_threshold,
                        "method": request.method,
                        "path": request.url.path
                    }
                )
            
            # Log performance metrics
            logger.debug(
                f"Request performance: {request.method} {request.url.path}",
                extra={
                    "request_id": getattr(request.state, "request_id", None),
                    "duration": duration,
                    "method": request.method,
                    "path": request.url.path
                }
            )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response with security headers
        """
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for centralized error handling."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle errors with structured responses.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response with error handling
        """
        try:
            return await call_next(request)
        except AppException as e:
            return handle_app_exception(e)
        except Exception as e:
            logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "error_code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred",
                    "request_id": getattr(request.state, "request_id", None)
                }
            )
