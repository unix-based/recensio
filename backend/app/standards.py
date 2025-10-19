"""
Standardized patterns and templates for the Recensio application.
Provides consistent patterns for logging, documentation, and type hints.
"""

from typing import Any, Dict, List, Optional, Union, Callable, TypeVar, Generic
from functools import wraps
import time
from datetime import datetime

# Type aliases for common patterns
JsonDict = Dict[str, Any]
JsonList = List[Dict[str, Any]]
OptionalStr = Optional[str]
OptionalInt = Optional[int]
OptionalFloat = Optional[float]

# Generic type for service responses
T = TypeVar('T')
ServiceResponse = Union[T, Dict[str, Any]]


class StandardizedDocstring:
    """Template for standardized docstrings across the application."""
    
    @staticmethod
    def function_template(
        description: str,
        args: Optional[Dict[str, str]] = None,
        returns: Optional[str] = None,
        raises: Optional[Dict[str, str]] = None,
        examples: Optional[str] = None
    ) -> str:
        """Generate a standardized function docstring.
        
        Args:
            description: Brief description of what the function does
            args: Dictionary of parameter names and descriptions
            returns: Description of return value
            raises: Dictionary of exception types and descriptions
            examples: Optional usage examples
            
        Returns:
            Formatted docstring
        """
        docstring = f'"""{description}'
        
        if args:
            docstring += '\n\n    Args:'
            for param, desc in args.items():
                docstring += f'\n        {param}: {desc}'
        
        if returns:
            docstring += f'\n\n    Returns:\n        {returns}'
        
        if raises:
            docstring += '\n\n    Raises:'
            for exc, desc in raises.items():
                docstring += f'\n        {exc}: {desc}'
        
        if examples:
            docstring += f'\n\n    Examples:\n        {examples}'
        
        docstring += '\n    """'
        return docstring


class LoggingPatterns:
    """Standardized logging patterns for consistent messaging."""
    
    # Operation patterns
    START_OPERATION = "Starting {operation} for {target}"
    COMPLETE_OPERATION = "Completed {operation} for {target}"
    FAIL_OPERATION = "Failed {operation} for {target}: {error}"
    
    # Service patterns
    SERVICE_INIT = "Initializing {service} service"
    SERVICE_READY = "{service} service ready"
    SERVICE_ERROR = "{service} service error: {error}"
    
    # Data patterns
    DATA_CREATED = "Created {entity_type} with ID {entity_id}"
    DATA_UPDATED = "Updated {entity_type} with ID {entity_id}"
    DATA_DELETED = "Deleted {entity_type} with ID {entity_id}"
    DATA_RETRIEVED = "Retrieved {entity_type} with ID {entity_id}"
    
    # Performance patterns
    PERFORMANCE_METRIC = "Performance: {metric}={value} {unit}"
    TIMING_START = "Starting {operation} at {timestamp}"
    TIMING_END = "Completed {operation} in {duration}ms"
    
    # Error patterns
    VALIDATION_ERROR = "Validation failed for {field}: {error}"
    CONNECTION_ERROR = "Connection failed to {service}: {error}"
    TIMEOUT_ERROR = "Timeout waiting for {operation}: {timeout}s"
    
    # Success patterns
    SUCCESS_OPERATION = "✅ {operation} completed successfully"
    SUCCESS_DATA = "✅ {entity_type} {action} successfully"
    SUCCESS_SERVICE = "✅ {service} operation completed"


class TypeHints:
    """Standardized type hints for common patterns."""
    
    # Common return types
    OptionalDict = Optional[Dict[str, Any]]
    OptionalList = Optional[List[Any]]
    OptionalString = Optional[str]
    OptionalInt = Optional[int]
    OptionalFloat = Optional[float]
    
    # Service types
    ServiceResult = Union[Dict[str, Any], None]
    CacheResult = Union[str, Dict[str, Any], None]
    StorageResult = Union[Dict[str, Any], List[Dict[str, Any]], None]
    
    # API types
    APIResponse = Dict[str, Any]
    APIError = Dict[str, Union[str, int]]
    PaginatedResponse = Dict[str, Union[List[Dict[str, Any]], int, str]]
    
    # Model types
    AgentData = Dict[str, Union[str, int, float, bool, None]]
    EvaluationData = Dict[str, Union[str, int, float, bool, None]]
    SiteSnapshotData = Dict[str, Union[str, int, List[Dict[str, Any]], None]]


def timing_decorator(operation_name: str = "operation"):
    """Decorator to log timing information for operations.
    
    Args:
        operation_name: Name of the operation being timed
        
    Returns:
        Decorated function with timing logs
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            start_timestamp = datetime.now().isoformat()
            
            # Log start
            print(f"⏱️  Starting {operation_name} at {start_timestamp}")
            
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000  # Convert to milliseconds
                
                # Log completion
                print(f"✅ Completed {operation_name} in {duration:.2f}ms")
                return result
                
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                print(f"❌ Failed {operation_name} after {duration:.2f}ms: {str(e)}")
                raise
                
        return wrapper
    return decorator


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """Validate that required fields are present in data.
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
        
    Raises:
        ValueError: If any required fields are missing
    """
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")


def sanitize_log_data(data: Dict[str, Any], sensitive_fields: List[str] = None) -> Dict[str, Any]:
    """Sanitize data for logging by removing or masking sensitive fields.
    
    Args:
        data: Dictionary to sanitize
        sensitive_fields: List of fields to mask (defaults to common sensitive fields)
        
    Returns:
        Sanitized dictionary safe for logging
    """
    if sensitive_fields is None:
        sensitive_fields = ['password', 'token', 'key', 'secret', 'api_key', 'auth']
    
    sanitized = data.copy()
    for field in sensitive_fields:
        if field in sanitized:
            sanitized[field] = "***REDACTED***"
    
    return sanitized


# Standardized error messages
class ErrorMessages:
    """Standardized error messages for consistent error handling."""
    
    # Validation errors
    INVALID_INPUT = "Invalid input provided: {field}={value}"
    MISSING_REQUIRED = "Missing required field: {field}"
    INVALID_TYPE = "Invalid type for {field}: expected {expected}, got {actual}"
    
    # Service errors
    SERVICE_UNAVAILABLE = "Service {service} is unavailable"
    CONNECTION_FAILED = "Failed to connect to {service}: {error}"
    TIMEOUT_EXCEEDED = "Operation timed out after {timeout}s"
    
    # Data errors
    DATA_NOT_FOUND = "Data not found: {entity_type} with ID {entity_id}"
    DATA_ALREADY_EXISTS = "Data already exists: {entity_type} with ID {entity_id}"
    DATA_CORRUPTED = "Data corruption detected: {entity_type} with ID {entity_id}"
    
    # Permission errors
    ACCESS_DENIED = "Access denied for {resource}"
    INSUFFICIENT_PERMISSIONS = "Insufficient permissions for {action}"
    
    # System errors
    INTERNAL_ERROR = "Internal server error: {error}"
    CONFIGURATION_ERROR = "Configuration error: {setting}={value}"
    DEPENDENCY_ERROR = "Dependency error: {dependency} not available"


# Standardized success messages
class SuccessMessages:
    """Standardized success messages for consistent feedback."""
    
    # Operations
    OPERATION_SUCCESS = "Operation completed successfully"
    DATA_CREATED = "Data created successfully"
    DATA_UPDATED = "Data updated successfully"
    DATA_DELETED = "Data deleted successfully"
    
    # Services
    SERVICE_READY = "Service ready and operational"
    CONNECTION_ESTABLISHED = "Connection established successfully"
    CACHE_CLEARED = "Cache cleared successfully"
    
    # Processing
    PROCESSING_COMPLETE = "Processing completed successfully"
    VALIDATION_PASSED = "Validation passed successfully"
    MIGRATION_COMPLETE = "Migration completed successfully"
