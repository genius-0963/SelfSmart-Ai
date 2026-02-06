"""
SmartShelf AI - Copilot Configuration

Configuration settings for the AI Copilot service.
"""

import os
from typing import Dict, Any
from pydantic import BaseSettings


class VectorStoreConfig(BaseSettings):
    """Vector store configuration."""
    
    collection_name: str = "smartshelf_documents"
    persist_directory: str = "data/vector_store"
    embedding_model: str = "all-MiniLM-L6-v2"
    max_results: int = 10
    similarity_threshold: float = 0.7
    
    class Config:
        env_prefix = "VECTOR_"


class LLMConfig(BaseSettings):
    """LLM configuration."""
    
    provider: str = "openai"
    model: str = "gpt-3.5-turbo"
    api_key: str = os.getenv("OPENAI_API_KEY", "")
    max_tokens: int = 1000
    temperature: float = 0.7
    system_prompt: str = """You are SmartShelf AI, an intelligent assistant for retail decision support.
    You have access to real-time business data including sales, inventory, forecasts, and analytics.
    Provide helpful, data-driven insights and recommendations for inventory management, pricing optimization, and business growth.
    Always be concise, actionable, and cite your sources when possible."""
    
    class Config:
        env_prefix = "LLM_"


class RAGConfig(BaseSettings):
    """RAG pipeline configuration."""
    
    context_window_size: int = 4000
    max_context_docs: int = 5
    rerank_results: bool = True
    include_metadata: bool = True
    conversation_history_limit: int = 10
    
    class Config:
        env_prefix = "RAG_"


class CopilotConfig(BaseSettings):
    """Main copilot configuration."""
    
    service_name: str = "SmartShelf AI Copilot"
    version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # Component configurations
    vector_store: VectorStoreConfig = VectorStoreConfig()
    llm: LLMConfig = LLMConfig()
    rag: RAGConfig = RAGConfig()
    
    class Config:
        env_prefix = "COPILOT_"
        case_sensitive = False
