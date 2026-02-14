"""
SmartShelf AI - Core Configuration
Production-ready settings with environment-based configuration
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # App Configuration
    app_name: str = "SmartShelf AI Backend"
    app_version: str = "2.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_prefix: str = "/api/v1"
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    
    # Database Configuration
    database_url: str = Field(default="sqlite:///./smartshelf.db", env="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # AI/ML Configuration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    deepseek_api_key: Optional[str] = Field(default=None, env="DEEPSEEK_API_KEY")
    openai_model: str = Field(default="gpt-3.5-turbo", env="OPENAI_MODEL")
    max_tokens: int = Field(default=1000, env="MAX_TOKENS")
    temperature: float = Field(default=0.7, env="TEMPERATURE")
    
    # Performance Configuration
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")
    max_concurrent_requests: int = Field(default=100, env="MAX_CONCURRENT_REQUESTS")
    request_timeout: int = Field(default=30, env="REQUEST_TIMEOUT")
    websocket_timeout: int = Field(default=60, env="WEBSOCKET_TIMEOUT")
    
    # Security Configuration
    jwt_secret_key: str = Field(default="your-secret-key-change-in-production", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expire_hours: int = Field(default=24, env="JWT_EXPIRE_HOURS")
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    
    # Amazon API Configuration
    amazon_api_key: Optional[str] = Field(default=None, env="AMAZON_API_KEY")
    amazon_api_host: str = Field(default="real-time-amazon-data.p.rapidapi.com", env="AMAZON_API_HOST")
    amazon_rate_limit: int = Field(default=10, env="AMAZON_RATE_LIMIT")
    
    # Monitoring Configuration
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    
    # File Storage Configuration
    upload_dir: str = Field(default="uploads", env="UPLOAD_DIR")
    max_file_size: int = Field(default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Global settings instance
settings = Settings()

# Environment-specific settings
def is_production() -> bool:
    return settings.environment.lower() == "production"

def is_development() -> bool:
    return settings.environment.lower() == "development"

def is_testing() -> bool:
    return settings.environment.lower() == "testing"

# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "formatter": "detailed",
            "class": "logging.FileHandler",
            "filename": "logs/app.log",
            "mode": "a",
        },
    },
    "root": {
        "level": settings.log_level,
        "handlers": ["default"] + (["file"] if not is_testing() else []),
    },
}

# CORS configuration
CORS_CONFIG = {
    "allow_origins": settings.cors_origins,
    "allow_credentials": True,
    "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["*"],
}

# Database configuration
DATABASE_CONFIG = {
    "url": settings.database_url,
    "echo": is_development(),
    "pool_pre_ping": True,
    "pool_recycle": 300,
}

# Redis configuration
REDIS_CONFIG = {
    "host": settings.redis_url.split("://")[1].split(":")[0] if "://" in settings.redis_url else "localhost",
    "port": int(settings.redis_url.split(":")[-1]) if ":" in settings.redis_url else 6379,
    "decode_responses": False,
    "socket_timeout": 5,
    "socket_connect_timeout": 5,
    "retry_on_timeout": True,
}
