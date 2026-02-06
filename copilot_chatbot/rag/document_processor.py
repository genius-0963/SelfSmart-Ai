"""
SmartShelf AI - Document Processor

Document processing and chunking for RAG pipeline.
"""

import logging
from typing import List, Dict, Any
import re

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Process and chunk documents for vector storage."""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        Initialize document processor.
        
        Args:
            chunk_size: Maximum size of each chunk
            chunk_overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    async def process_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process documents into chunks for vector storage.
        
        Args:
            documents: List of documents to process
            
        Returns:
            List of processed document chunks
        """
        processed_chunks = []
        
        for doc in documents:
            chunks = self._chunk_document(doc)
            processed_chunks.extend(chunks)
        
        logger.info(f"Processed {len(documents)} documents into {len(processed_chunks)} chunks")
        return processed_chunks
    
    def _chunk_document(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split a document into chunks.
        
        Args:
            document: Document to chunk
            
        Returns:
            List of document chunks
        """
        content = document.get("content", "")
        
        # Simple text chunking (in production, use more sophisticated methods)
        chunks = self._split_text(content)
        
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            chunk_doc = {
                "id": f"{document['id']}_chunk_{i}",
                "content": chunk,
                "source": document.get("source", ""),
                "metadata": {
                    **document.get("metadata", {}),
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "parent_id": document["id"]
                }
            }
            processed_chunks.append(chunk_doc)
        
        return processed_chunks
    
    def _split_text(self, text: str) -> List[str]:
        """
        Split text into chunks.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            # Find the best break point
            end = start + self.chunk_size
            
            if end >= len(text):
                chunks.append(text[start:])
                break
            
            # Try to break at sentence or paragraph
            break_point = self._find_break_point(text, start, end)
            chunks.append(text[start:break_point])
            
            # Move to next chunk with overlap
            start = max(start + 1, break_point - self.chunk_overlap)
        
        return chunks
    
    def _find_break_point(self, text: str, start: int, end: int) -> int:
        """
        Find the best break point in text.
        
        Args:
            text: Text to search
            start: Start position
            end: End position
            
        Returns:
            Break point position
        """
        # Look for paragraph breaks
        paragraph_break = text.rfind('\n\n', start, end)
        if paragraph_break > start:
            return paragraph_break + 2
        
        # Look for sentence breaks
        sentence_break = text.rfind('. ', start, end)
        if sentence_break > start:
            return sentence_break + 2
        
        # Look for word breaks
        word_break = text.rfind(' ', start, end)
        if word_break > start:
            return word_break + 1
        
        return end
