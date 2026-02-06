"""
SmartShelf AI - Core Backend Modules

Core functionality including exceptions, logging, security, and utilities.
"""

from .exceptions import SmartShelfException
from .logging import setup_logging
from .security import get_current_user, verify_api_key

__all__ = [
    'SmartShelfException',
    'setup_logging',
    'get_current_user',
    'verify_api_key'
]
