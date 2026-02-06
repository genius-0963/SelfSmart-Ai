"""
SmartShelf AI - RAG Pipeline

Main RAG pipeline for processing queries with context retrieval and generation.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..vector_store.base import VectorStoreBase
from ..llm.base import LLMClientBase
from .document_processor import DocumentProcessor
from .context_retriever import ContextRetriever
from ..config import RAGConfig

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    Retrieval-Augmented Generation pipeline.
    
    Combines vector search with LLM generation for context-aware responses.
    """
    
    def __init__(
        self,
        vector_store: VectorStoreBase,
        llm_client: LLMClientBase,
        config: RAGConfig
    ):
        """
        Initialize RAG pipeline.
        
        Args:
            vector_store: Vector database client
            llm_client: LLM client for generation
            config: RAG configuration
        """
        self.vector_store = vector_store
        self.llm_client = llm_client
        self.config = config
        
        # Initialize components
        self.document_processor = DocumentProcessor()
        self.context_retriever = ContextRetriever(vector_store, config)
        
        # Conversation history (in production, use Redis or database)
        self.conversation_history = {}
        
        logger.info("RAG Pipeline initialized")
    
    async def process_query(
        self,
        query: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user query through the RAG pipeline.
        
        Args:
            query: User query
            session_id: Optional session ID for conversation context
            
        Returns:
            Generated response with context and metadata
        """
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Retrieve relevant context
            context_docs = await self.context_retriever.retrieve_context(
                query,
                max_results=self.config.max_context_docs
            )
            
            # Step 2: Build conversation context
            conversation_context = self._get_conversation_context(session_id)
            
            # Step 3: Generate response
            response = await self.llm_client.generate_response(
                query=query,
                context=context_docs,
                conversation_context=conversation_context
            )
            
            # Step 4: Update conversation history
            if session_id:
                self._update_conversation_history(session_id, query, response)
            
            # Step 5: Build response metadata
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = {
                "query": query,
                "response": response["text"],
                "context_sources": [
                    {
                        "id": doc.get("id", ""),
                        "source": doc.get("source", ""),
                        "content": doc.get("content", "")[:200] + "...",
                        "relevance": doc.get("score", 0.0)
                    }
                    for doc in context_docs
                ],
                "session_id": session_id,
                "metadata": {
                    "processing_time_seconds": processing_time,
                    "context_docs_count": len(context_docs),
                    "model_used": self.llm_client.model_name,
                    "tokens_used": response.get("tokens_used", 0),
                    "timestamp": datetime.utcnow().isoformat()
                },
                "suggested_questions": self._generate_suggested_questions(query, response),
                "related_topics": self._extract_related_topics(context_docs)
            }
            
            logger.info(f"Query processed in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            raise
    
    async def build_index(self) -> None:
        """Build or rebuild the document index."""
        logger.info("Building document index...")
        
        try:
            # Load documents from various sources
            documents = await self._load_documents()
            
            # Process and chunk documents
            processed_docs = await self.document_processor.process_documents(documents)
            
            # Add to vector store
            await self.vector_store.add_documents(processed_docs)
            
            logger.info(f"Index built with {len(processed_docs)} document chunks")
            
        except Exception as e:
            logger.error(f"Index building failed: {e}")
            raise
    
    async def _load_documents(self) -> List[Dict[str, Any]]:
        """Load documents from various sources."""
        documents = []
        
        # Load from database (mock implementation)
        documents.extend(await self._load_database_documents())
        
        # Load from knowledge base (mock implementation)
        documents.extend(await self._load_knowledge_base())
        
        # Load from analytics (mock implementation)
        documents.extend(await self._load_analytics_documents())
        
        return documents
    
    async def _load_database_documents(self) -> List[Dict[str, Any]]:
        """Load documents from the main database."""
        # Mock implementation - in production, query actual database
        return [
            {
                "id": "sales_summary_2024",
                "content": "Total sales for 2024: $609,523.18 across 50 products. Top categories: Electronics ($245,890), Clothing ($156,234), Home & Garden ($98,456). Average order value: $45.67.",
                "source": "database",
                "metadata": {
                    "type": "sales_summary",
                    "date": "2024-02-06",
                    "revenue": 609523.18
                }
            },
            {
                "id": "inventory_status",
                "content": "Current inventory status: 45 products in stock, 5 out of stock, 12 low stock alerts. Total inventory value: $125,450. Average days of supply: 14.2 days.",
                "source": "database",
                "metadata": {
                    "type": "inventory_status",
                    "date": "2024-02-06",
                    "out_of_stock": 5
                }
            },
            {
                "id": "forecast_accuracy",
                "content": "Demand forecasting accuracy: 87% overall. Prophet model performing well for Electronics (92% accuracy) and Clothing (85% accuracy). Forecast horizon: 30 days.",
                "source": "database",
                "metadata": {
                    "type": "forecast_metrics",
                    "accuracy": 0.87,
                    "model": "prophet"
                }
            }
        ]
    
    async def _load_knowledge_base(self) -> List[Dict[str, Any]]:
        """Load documents from the knowledge base."""
        return [
            {
                "id": "inventory_best_practices",
                "content": "Inventory best practices: Maintain 7-14 days of supply for fast-moving items, 14-30 days for medium-moving items. Use ABC analysis to prioritize inventory management. Implement automated reorder points at 30% stock level.",
                "source": "knowledge_base",
                "metadata": {
                    "category": "inventory_management",
                    "type": "best_practices"
                }
            },
            {
                "id": "pricing_strategies",
                "content": "Effective pricing strategies: Implement dynamic pricing based on demand elasticity. Monitor competitor prices daily. Use promotional pricing strategically during peak demand periods. Maintain minimum 20% profit margin.",
                "source": "knowledge_base",
                "metadata": {
                    "category": "pricing",
                    "type": "strategies"
                }
            },
            {
                "id": "demand_forecasting",
                "content": "Demand forecasting tips: Use at least 90 days of historical data. Consider seasonality patterns and holidays. Monitor forecast accuracy and adjust models regularly. Combine multiple forecasting methods for better accuracy.",
                "source": "knowledge_base",
                "metadata": {
                    "category": "forecasting",
                    "type": "guidelines"
                }
            }
        ]
    
    async def _load_analytics_documents(self) -> List[Dict[str, Any]]:
        """Load documents from analytics reports."""
        return [
            {
                "id": "revenue_trends",
                "content": "Revenue trends: 12% growth month-over-month. Strongest performance on weekends (35% higher sales). Peak shopping hours: 2-4 PM. Mobile sales account for 45% of total revenue.",
                "source": "analytics",
                "metadata": {
                    "type": "revenue_analysis",
                    "growth_rate": 0.12
                }
            },
            {
                "id": "product_performance",
                "content": "Top performing products: Electronics (highest revenue per unit), Clothing (highest volume), Home & Garden (highest profit margin). Underperforming categories need inventory optimization.",
                "source": "analytics",
                "metadata": {
                    "type": "product_analysis",
                    "top_category": "Electronics"
                }
            }
        ]
    
    def _get_conversation_context(self, session_id: Optional[str]) -> List[Dict[str, str]]:
        """Get conversation history for context."""
        if not session_id or session_id not in self.conversation_history:
            return []
        
        history = self.conversation_history[session_id]
        return history[-self.config.conversation_history_limit:]
    
    def _update_conversation_history(
        self,
        session_id: str,
        query: str,
        response: Dict[str, Any]
    ) -> None:
        """Update conversation history."""
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        
        self.conversation_history[session_id].append({
            "role": "user",
            "content": query,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        self.conversation_history[session_id].append({
            "role": "assistant",
            "content": response["text"],
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Limit history size
        if len(self.conversation_history[session_id]) > self.config.conversation_history_limit * 2:
            self.conversation_history[session_id] = self.conversation_history[session_id][-self.config.conversation_history_limit * 2:]
    
    def _generate_suggested_questions(
        self,
        query: str,
        response: Dict[str, Any]
    ) -> List[str]:
        """Generate suggested follow-up questions."""
        # Simple keyword-based suggestions
        query_lower = query.lower()
        
        if "stock" in query_lower or "inventory" in query_lower:
            return [
                "Which products should I reorder this week?",
                "What's my inventory turnover rate?",
                "Show me products at risk of stockout"
            ]
        elif "revenue" in query_lower or "sales" in query_lower:
            return [
                "What are my top selling products?",
                "How is revenue trending this month?",
                "Which categories are driving growth?"
            ]
        elif "forecast" in query_lower or "demand" in query_lower:
            return [
                "Show me the 30-day demand forecast",
                "Which products have highest forecast accuracy?",
                "What factors are driving demand changes?"
            ]
        elif "price" in query_lower or "pricing" in query_lower:
            return [
                "Which products need price adjustments?",
                "How do my prices compare to competitors?",
                "What's the revenue impact of pricing changes?"
            ]
        else:
            return [
                "Show me inventory alerts",
                "What's my revenue trend?",
                "Which products should I reorder?"
            ]
    
    def _extract_related_topics(self, context_docs: List[Dict[str, Any]]) -> List[str]:
        """Extract related topics from context documents."""
        topics = set()
        
        for doc in context_docs:
            metadata = doc.get("metadata", {})
            if "category" in metadata:
                topics.add(metadata["category"])
            if "type" in metadata:
                topics.add(metadata["type"])
        
        return list(topics)[:5]  # Limit to 5 topics
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        vector_stats = await self.vector_store.get_stats()
        
        return {
            "pipeline_type": "RAG",
            "config": {
                "max_context_docs": self.config.max_context_docs,
                "context_window_size": self.config.context_window_size,
                "rerank_results": self.config.rerank_results
            },
            "vector_store": vector_stats,
            "active_sessions": len(self.conversation_history),
            "total_conversations": sum(len(history) for history in self.conversation_history.values())
        }
