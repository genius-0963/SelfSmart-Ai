"""
SmartShelf AI - Custom Exceptions

Custom exception classes for the SmartShelf AI platform.
"""

from typing import Dict, Any, Optional


class SmartShelfException(Exception):
    """
    Base exception class for SmartShelf AI.
    
    All custom exceptions should inherit from this class.
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_type: str = "smartshelf_error",
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize SmartShelf exception.
        
        Args:
            message: Human-readable error message
            status_code: HTTP status code
            error_type: Machine-readable error type
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.details = details or {}


class ValidationError(SmartShelfException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_type="validation_error",
            details=details
        )


class NotFoundError(SmartShelfException):
    """Raised when a resource is not found."""
    
    def __init__(self, resource: str, identifier: Any = None):
        message = f"{resource} not found"
        if identifier:
            message += f" with identifier: {identifier}"
        
        super().__init__(
            message=message,
            status_code=404,
            error_type="not_found",
            details={"resource": resource, "identifier": str(identifier)}
        )


class DatabaseError(SmartShelfException):
    """Raised when database operations fail."""
    
    def __init__(self, message: str, operation: str = None):
        super().__init__(
            message=f"Database error: {message}",
            status_code=500,
            error_type="database_error",
            details={"operation": operation}
        )


class ModelError(SmartShelfException):
    """Raised when ML model operations fail."""
    
    def __init__(self, message: str, model_name: str = None):
        super().__init__(
            message=f"Model error: {message}",
            status_code=500,
            error_type="model_error",
            details={"model_name": model_name}
        )


class ForecastError(ModelError):
    """Raised when forecasting operations fail."""
    
    def __init__(self, message: str, product_id: int = None):
        super().__init__(
            message=message,
            model_name="demand_forecaster"
        )
        self.details["product_id"] = product_id
        self.error_type = "forecast_error"


class PricingError(ModelError):
    """Raised when pricing optimization fails."""
    
    def __init__(self, message: str, product_id: int = None):
        super().__init__(
            message=message,
            model_name="pricing_optimizer"
        )
        self.details["product_id"] = product_id
        self.error_type = "pricing_error"


class InventoryError(ModelError):
    """Raised when inventory operations fail."""
    
    def __init__(self, message: str, product_id: int = None):
        super().__init__(
            message=message,
            model_name="inventory_analyzer"
        )
        self.details["product_id"] = product_id
        self.error_type = "inventory_error"


class CopilotError(SmartShelfException):
    """Raised when AI Copilot operations fail."""
    
    def __init__(self, message: str, session_id: str = None):
        super().__init__(
            message=f"Copilot error: {message}",
            status_code=500,
            error_type="copilot_error",
            details={"session_id": session_id}
        )


class AuthenticationError(SmartShelfException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=401,
            error_type="authentication_error"
        )


class AuthorizationError(SmartShelfException):
    """Raised when authorization fails."""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            status_code=403,
            error_type="authorization_error"
        )


class RateLimitError(SmartShelfException):
    """Raised when rate limits are exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        super().__init__(
            message=message,
            status_code=429,
            error_type="rate_limit_error",
            details={"retry_after": retry_after}
        )


class ConfigurationError(SmartShelfException):
    """Raised when configuration is invalid."""
    
    def __init__(self, message: str, config_key: str = None):
        super().__init__(
            message=f"Configuration error: {message}",
            status_code=500,
            error_type="configuration_error",
            details={"config_key": config_key}
        )


class ExternalServiceError(SmartShelfException):
    """Raised when external service calls fail."""
    
    def __init__(self, message: str, service_name: str = None, status_code: int = 502):
        super().__init__(
            message=f"External service error: {message}",
            status_code=status_code,
            error_type="external_service_error",
            details={"service_name": service_name}
        )


class DataProcessingError(SmartShelfException):
    """Raised when data processing operations fail."""
    
    def __init__(self, message: str, operation: str = None):
        super().__init__(
            message=f"Data processing error: {message}",
            status_code=500,
            error_type="data_processing_error",
            details={"operation": operation}
        )
