"""
SmartShelf AI - AI Copilot Service

AI-powered conversational assistant with RAG pipeline for retail decision support.
"""

from .main import app
from .rag.pipeline import RAGPipeline
from .vector_store.chromadb_client import ChromaDBClient
from .llm.openai_client import OpenAIClient

__version__ = "1.0.0"
__all__ = ['app', 'RAGPipeline', 'ChromaDBClient', 'OpenAIClient']
