"""
SmartShelf AI - Vector Store Base

Base class for vector store implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any

class VectorStoreBase(ABC):
    """Abstract base class for vector stores."""
    
    @abstractmethod
    async def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Add documents to the vector store."""
        pass
    
    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        pass
    
    @abstractmethod
    def has_documents(self) -> bool:
        """Check if vector store has documents."""
        pass
