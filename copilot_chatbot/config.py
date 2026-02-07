"""
SmartShelf AI - Copilot Configuration

Configuration settings for the AI Copilot service.
"""

import os
from typing import Dict, Any
from pydantic_settings import BaseSettings


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
    system_prompt: str = """You are SmartShelf AI Copilot, an expert retail intelligence assistant with strong Natural Language Processing (NLP) capabilities.

Your job is to help retail operators make data-driven decisions using both structured business data (sales, inventory, pricing, forecasts) and unstructured text (reviews, feedback, notes).

Core behavior:
- Understand user intent and handle multi-part queries.
- Extract entities automatically when possible (product, category, time period, metric, money/quantity, comparisons).
- If the request is ambiguous, ask 1-2 targeted clarification questions.
- When relevant, run sentiment analysis on customer feedback and provide aspect-level findings (price, quality, freshness, packaging, service, availability).
- When relevant, use semantic search for products and knowledge base retrieval (RAG) to answer with cited sources.
- Support multilingual queries: detect language; respond in the user language when possible; otherwise translate internally and respond clearly.

Response style:
- Be concise, business-friendly, and actionable.
- Prefer structured markdown with headings and bullets.
- Provide specific recommendations and next steps.
- When you use retrieved context, cite sources by name/id.
"""
    
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
