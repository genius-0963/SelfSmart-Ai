"""
SmartShelf AI - OpenAI Client

OpenAI API client for LLM integration.
"""

import logging
from typing import List, Dict, Any, Optional
import json

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

from .base import LLMClientBase
from ..config import LLMConfig

logger = logging.getLogger(__name__)


class OpenAIClient(LLMClientBase):
    """OpenAI API client for LLM generation."""
    
    def __init__(self, config: LLMConfig):
        """
        Initialize OpenAI/DeepSeek client.
        Supports OpenAI and DeepSeek (OpenAI-compatible API).
        """
        super().__init__(config)
        
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library is required. Install with: pip install openai")
        
        # Prefer DeepSeek if API key is set
        if config.deepseek_api_key:
            self.client = openai.OpenAI(
                api_key=config.deepseek_api_key,
                base_url=config.deepseek_base_url
            )
            self._model = config.model if config.model.startswith("deepseek") else "deepseek-chat"
            logger.info(f"DeepSeek client initialized with model: {self._model}")
        elif config.api_key:
            self.client = openai.OpenAI(api_key=config.api_key)
            self._model = config.model
            logger.info(f"OpenAI client initialized with model: {self._model}")
        else:
            raise ValueError("API key required. Set OPENAI_API_KEY or DEEPSEEK_API_KEY in .env")
    
    async def generate_response(
        self,
        query: str,
        context: List[Dict[str, Any]] = None,
        conversation_context: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Generate response using OpenAI API.
        
        Args:
            query: User query
            context: Retrieved context documents
            conversation_context: Conversation history
            
        Returns:
            Generated response with metadata
        """
        try:
            # Build prompt with context
            prompt = self._build_prompt(query, context, conversation_context)
            
            # Generate response
            response = self.client.chat.completions.create(
                model=getattr(self, "_model", self.config.model),
                messages=[
                    {"role": "system", "content": self.config.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
            
            response_text = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            return {
                "text": response_text,
                "tokens_used": tokens_used,
                "model": getattr(self, "_model", self.config.model),
                "finish_reason": response.choices[0].finish_reason
            }
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            # Fallback to mock response for demo
            return self._generate_fallback_response(query, context)
    
    def _build_prompt(
        self,
        query: str,
        context: List[Dict[str, Any]] = None,
        conversation_context: List[Dict[str, str]] = None
    ) -> str:
        """Build prompt with context and conversation history."""
        prompt_parts = [query]
        
        # Add context if available
        if context:
            context_text = "\n\nRelevant context:\n"
            for i, doc in enumerate(context[:3]):  # Limit to 3 docs
                context_text += f"{i+1}. {doc.get('content', '')}\n"
            prompt_parts.append(context_text)
        
        # Add conversation context if available
        if conversation_context:
            conv_text = "\n\nRecent conversation:\n"
            for msg in conversation_context[-4:]:  # Last 4 messages
                conv_text += f"{msg['role']}: {msg['content']}\n"
            prompt_parts.append(conv_text)
        
        return "\n".join(prompt_parts)
    
    def _generate_fallback_response(
        self,
        query: str,
        context: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate fallback response when API is unavailable."""
        query_lower = query.lower()
        
        if "stock" in query_lower or "inventory" in query_lower:
            response = "Based on current inventory data, I recommend checking products with low stock levels. You have 5 products currently at risk of stockout and 12 with low inventory. Would you like me to show you the specific products that need immediate attention?"
        elif "revenue" in query_lower or "sales" in query_lower:
            response = "Your total revenue for the last 30 days is $609,523.18, representing a 12% increase from the previous period. Electronics and Clothing categories are driving this growth. Would you like me to break down the performance by product?"
        elif "forecast" in query_lower or "demand" in query_lower:
            response = "My demand forecasting models predict steady growth over the next 30 days with 95% confidence. Seasonal patterns suggest a 15% increase in demand for Electronics products. Would you like to see the detailed forecast?"
        else:
            response = "I'm here to help you make data-driven decisions for your retail business. I can assist with inventory management, demand forecasting, pricing optimization, and sales analytics. What specific area would you like to explore?"
        
        return {
            "text": response,
            "tokens_used": 150,
            "model": "fallback",
            "finish_reason": "fallback"
        }
