"""
SmartShelf AI - Vector Store

Vector database implementations for document storage and retrieval.
"""

from .base import VectorStoreBase
from .chromadb_client import ChromaDBClient

__all__ = ['VectorStoreBase', 'ChromaDBClient']
