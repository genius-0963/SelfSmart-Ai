"""
SmartShelf AI - ChromaDB Client

ChromaDB implementation for vector storage.
"""

import logging
from typing import List, Dict, Any, Optional
import os
from pathlib import Path

try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None
    Settings = None

from .base import VectorStoreBase
from ..config import VectorStoreConfig

logger = logging.getLogger(__name__)


class ChromaDBClient(VectorStoreBase):
    """ChromaDB client for vector storage."""
    
    def __init__(self, config: VectorStoreConfig):
        """
        Initialize ChromaDB client.
        
        Args:
            config: Vector store configuration
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB and sentence-transformers are required. Install with: pip install chromadb sentence-transformers")
        
        self.config = config
        self.collection_name = config.collection_name
        self.persist_directory = Path(config.persist_directory)
        
        # Create persist directory
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(config.embedding_model)
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        logger.info(f"ChromaDB client initialized with collection: {self.collection_name}")
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Add documents to the vector store."""
        if not documents:
            return
        
        try:
            # Prepare documents for ChromaDB
            ids = []
            texts = []
            metadatas = []
            
            for doc in documents:
                ids.append(doc["id"])
                texts.append(doc["content"])
                
                metadata = {
                    "source": doc.get("source", ""),
                    **doc.get("metadata", {})
                }
                metadatas.append(metadata)
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(texts).tolist()
            
            # Add to collection
            self.collection.add(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )
            
            logger.info(f"Added {len(documents)} documents to vector store")
            
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise
    
    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query]).tolist()
            
            # Search collection
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=min(max_results, self.config.max_results),
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results["ids"][0])):
                formatted_results.append({
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": 1 - results["distances"][0][i]  # Convert distance to similarity
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        try:
            count = self.collection.count()
            
            return {
                "type": "chromadb",
                "collection_name": self.collection_name,
                "document_count": count,
                "embedding_model": self.config.embedding_model,
                "persist_directory": str(self.persist_directory),
                "similarity_metric": "cosine"
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"error": str(e)}
    
    def has_documents(self) -> bool:
        """Check if vector store has documents."""
        try:
            return self.collection.count() > 0
        except Exception:
            return False
