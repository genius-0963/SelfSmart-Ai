"""
SmartShelf AI - Copilot Configuration

Configuration settings for the AI Copilot service.
"""

import os
from pathlib import Path
from typing import Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    """LLM configuration. Reads OPENAI_API_KEY and DEEPSEEK_API_KEY from env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    provider: str = "openai"
    model: str = "gpt-3.5-turbo"
    api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
    deepseek_api_key: str = Field(default="", validation_alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = "https://api.deepseek.com"
    max_tokens: int = 1000
    temperature: float = 0.7
    system_prompt: str = """You are SmartShelf AI, a friendly and intelligent shopping assistant. You help users with product recommendations, shopping advice, and general questions—just like a helpful human assistant.

Your name is SmartShelf AI. When asked "what is your name" or "who are you", say you're SmartShelf AI, an intelligent shopping assistant.

Core behavior:
- Be conversational, warm, and helpful—like ChatGPT.
- Answer any question naturally: greetings, identity, general knowledge, products, shopping.
- Give direct, relevant answers. Avoid generic responses like "Thanks for sharing! How does that make you feel?"
- For product/shopping queries: recommend products, compare options, suggest based on needs.
- Use retrieved context when available to give accurate, cited answers.
- Support follow-up questions and multi-turn conversation.
- Keep responses concise but complete. Use markdown when listing items.

Response style:
- Natural and human-like
- Direct answers to direct questions
- Friendly tone, not robotic
"""


class RAGConfig(BaseSettings):
    """RAG pipeline configuration."""
    
    context_window_size: int = 4000
    max_context_docs: int = 5
    rerank_results: bool = True
    include_metadata: bool = True
    conversation_history_limit: int = 10
    
    class Config:
        env_prefix = "RAG_"


class ProductSuggestionConfig(BaseSettings):
    """Product suggestion system configuration."""
    
    embeddings_path: str = "data/amazon_product_embeddings"
    model_name: str = "all-MiniLM-L6-v2"
    similarity_threshold: float = 0.3
    max_recommendations: int = 10
    enable_cache: bool = True
    cache_ttl: int = 3600  # 1 hour
    
    class Config:
        env_prefix = "PRODUCT_SUGGESTION_"


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
    product_suggestion: ProductSuggestionConfig = ProductSuggestionConfig()
    
    class Config:
        env_prefix = "COPILOT_"
        case_sensitive = False
