"""
SmartShelf AI - Copilot Exceptions

Custom exceptions for the AI Copilot service.
"""

from typing import Dict, Any, Optional


class CopilotException(Exception):
    """Base exception for the AI Copilot service."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_type: str = "copilot_error",
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Copilot exception.  
        
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
