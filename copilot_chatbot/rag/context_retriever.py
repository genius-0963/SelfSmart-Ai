"""
SmartShelf AI - Context Retriever

Retrieves relevant context documents for queries.
"""

import logging
from typing import List, Dict, Any
from ..vector_store.base import VectorStoreBase
from ..config import RAGConfig

logger = logging.getLogger(__name__)


class ContextRetriever:
    """Retrieves relevant context for queries."""
    
    def __init__(self, vector_store: VectorStoreBase, config: RAGConfig):
        """
        Initialize context retriever.
        
        Args:
            vector_store: Vector database client
            config: RAG configuration
        """
        self.vector_store = vector_store
        self.config = config
    
    async def retrieve_context(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context documents.
        
        Args:
            query: Query to search for
            max_results: Maximum number of results
            
        Returns:
            List of relevant documents
        """
        try:
            # Search vector store
            results = await self.vector_store.search(query, max_results)
            
            # Filter by similarity threshold
            filtered_results = [
                doc for doc in results 
                if doc.get("score", 0) >= self.config.similarity_threshold
            ]
            
            # Rerank if enabled
            if self.config.rerank_results and len(filtered_results) > 1:
                filtered_results = self._rerank_results(query, filtered_results)
            
            logger.info(f"Retrieved {len(filtered_results)} context documents")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Context retrieval failed: {e}")
            return []
    
    def _rerank_results(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rerank search results based on query relevance.
        
        Args:
            query: Original query
            results: Search results to rerank
            
        Returns:
            Reranked results
        """
        # Simple reranking based on keyword matching
        query_words = set(query.lower().split())
        
        for result in results:
            content = result.get("content", "").lower()
            content_words = set(content.split())
            
            # Calculate keyword overlap
            overlap = len(query_words & content_words)
            result["rerank_score"] = overlap / len(query_words)
        
        # Sort by combined score
        for result in results:
            result["combined_score"] = (
                result.get("score", 0) * 0.7 + 
                result.get("rerank_score", 0) * 0.3
            )
        
        return sorted(results, key=lambda x: x["combined_score"], reverse=True)
