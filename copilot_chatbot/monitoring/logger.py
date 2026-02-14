"""
Structured logging configuration for SmartShelf AI
"""

import logging
import logging.handlers
import sys
import os
import json
from datetime import datetime
from typing import Any, Dict
import structlog
from pythonjsonlogger import jsonlogger


class JSONFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields"""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp if not present
        if not log_record.get('timestamp'):
            log_record['timestamp'] = datetime.utcnow().isoformat()
        
        # Add log level
        log_record['level'] = record.levelname
        
        # Add service name
        log_record['service'] = 'smartshelf-ai'
        
        # Add environment
        log_record['environment'] = os.getenv('ENVIRONMENT', 'development')
        
        # Add module and function
        if record.module:
            log_record['module'] = record.module
        if record.funcName:
            log_record['function'] = record.funcName
        if record.lineno:
            log_record['line_number'] = record.lineno


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Add color to level name
        level_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{level_color}{record.levelname}{self.COLORS['RESET']}"
        
        # Format the message
        formatted = super().format(record)
        
        return formatted


def setup_logging(
    level: str = "INFO",
    log_file: str = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    enable_json: bool = None
) -> None:
    """
    Setup structured logging for the application
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup log files to keep
        enable_json: Force JSON logging (auto-detected if None)
    """
    
    # Auto-detect JSON logging for production
    if enable_json is None:
        enable_json = os.getenv('ENVIRONMENT', 'development') == 'production'
    
    # Set root logger level
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    
    if enable_json:
        console_formatter = JSONFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if log file specified)
    if log_file:
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(getattr(logging, level.upper()))
        
        # Always use JSON format for files
        file_formatter = JSONFormatter(
            '%(timestamp)s %(level)s %(name)s %(module)s %(function)s %(line_number)s %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Structured logger instance
    """
    return structlog.get_logger(name)


class LoggerMixin:
    """Mixin class to add logging capabilities to any class"""
    
    @property
    def logger(self):
        """Get logger for this class"""
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__module__ + '.' + self.__class__.__name__)
        return self._logger


# Context manager for logging performance
class LogPerformance:
    """Context manager for logging execution time"""
    
    def __init__(self, logger: logging.Logger, operation: str, level: str = "INFO"):
        self.logger = logger
        self.operation = operation
        self.level = getattr(logging, level.upper())
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.utcnow()
        self.logger.log(self.level, f"Starting {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.utcnow() - self.start_time).total_seconds()
        
        if exc_type:
            self.logger.error(
                f"Failed {self.operation} after {duration:.2f}s",
                extra={
                    'operation': self.operation,
                    'duration': duration,
                    'error': str(exc_val),
                    'error_type': exc_type.__name__ if exc_type else None
                }
            )
        else:
            self.logger.log(
                self.level,
                f"Completed {self.operation} in {duration:.2f}s",
                extra={
                    'operation': self.operation,
                    'duration': duration
                }
            )


# Decorator for logging function performance
def log_performance(operation: str = None, level: str = "INFO"):
    """Decorator to log function execution time"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            op_name = operation or f"{func.__module__}.{func.__name__}"
            
            with LogPerformance(logger, op_name, level):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Initialize logging on module import
if not logging.getLogger().handlers:
    setup_logging(
        level=os.getenv('LOG_LEVEL', 'INFO'),
        log_file=os.getenv('LOG_FILE'),
        enable_json=os.getenv('ENVIRONMENT') == 'production'
    )
