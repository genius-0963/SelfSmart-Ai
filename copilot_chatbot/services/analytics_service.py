"""
SmartShelf AI - Analytics Service
Comprehensive analytics and insights for chat conversations
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import logging

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Comprehensive analytics service for conversation insights"""
    
    def __init__(self):
        self.conversation_data = []
        self.user_metrics = defaultdict(dict)
        self.session_metrics = defaultdict(dict)
        self.product_analytics = defaultdict(dict)
        
        # Performance tracking
        self.daily_stats = defaultdict(lambda: {
            'conversations': 0,
            'users': set(),
            'avg_response_time': [],
            'intents': Counter(),
            'errors': 0
        })
        
    async def track_conversation(
        self, 
        session_id: str, 
        user_message: str, 
        ai_response: str, 
        intent: str, 
        confidence: float, 
        response_time: float,
        user_id: str = "anonymous",
        metadata: Dict[str, Any] = None
    ):
        """Track conversation data for analytics"""
        conversation_entry = {
            'session_id': session_id,
            'user_id': user_id,
            'timestamp': datetime.now(),
            'user_message': user_message,
            'ai_response': ai_response,
            'intent': intent,
            'confidence': confidence,
            'response_time': response_time,
            'message_length': len(user_message),
            'response_length': len(ai_response),
            'metadata': metadata or {}
        }
        
        self.conversation_data.append(conversation_entry)
        
        # Update daily stats
        date_key = conversation_entry['timestamp'].date()
        self.daily_stats[date_key]['conversations'] += 1
        self.daily_stats[date_key]['users'].add(user_id)
        self.daily_stats[date_key]['avg_response_time'].append(response_time)
        self.daily_stats[date_key]['intents'][intent] += 1
        
        if response_time > 5.0:  # Consider slow responses as errors
            self.daily_stats[date_key]['errors'] += 1
        
        # Update user metrics
        if user_id not in self.user_metrics:
            self.user_metrics[user_id] = {
                'total_messages': 0,
                'total_sessions': set(),
                'avg_response_time': [],
                'intents': Counter(),
                'satisfaction_scores': [],
                'first_seen': datetime.now(),
                'last_seen': datetime.now(),
                'message_lengths': [],
                'preferred_intents': Counter()
            }
        
        user_metrics = self.user_metrics[user_id]
        user_metrics['total_messages'] += 1
        user_metrics['total_sessions'].add(session_id)
        user_metrics['avg_response_time'].append(response_time)
        user_metrics['intents'][intent] += 1
        user_metrics['message_lengths'].append(len(user_message))
        user_metrics['last_seen'] = datetime.now()
        
        # Update session metrics
        if session_id not in self.session_metrics:
            self.session_metrics[session_id] = {
                'user_id': user_id,
                'start_time': datetime.now(),
                'last_activity': datetime.now(),
                'message_count': 0,
                'intents': Counter(),
                'avg_response_time': [],
                'session_duration': 0
            }
        
        session_metrics = self.session_metrics[session_id]
        session_metrics['message_count'] += 1
        session_metrics['intents'][intent] += 1
        session_metrics['avg_response_time'].append(response_time)
        session_metrics['last_activity'] = datetime.now()
        session_metrics['session_duration'] = (
            session_metrics['last_activity'] - session_metrics['start_time']
        ).total_seconds()
        
        # Track product-related analytics
        if metadata and 'product_suggestions' in metadata:
            product_count = len(metadata['product_suggestions'])
            self.product_analytics['total_suggestions'] = (
                self.product_analytics.get('total_suggestions', 0) + product_count
            )
            self.product_analytics['sessions_with_products'] = (
                self.product_analytics.get('sessions_with_products', 0) + 1
            )
    
    async def track_user_feedback(self, session_id: str, rating: int, feedback: str = ""):
        """Track user feedback for satisfaction analysis"""
        # Find the session and user
        if session_id in self.session_metrics:
            user_id = self.session_metrics[session_id]['user_id']
            if user_id in self.user_metrics:
                self.user_metrics[user_id]['satisfaction_scores'].append(rating)
    
    async def get_conversation_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get comprehensive conversation analytics"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Filter recent conversations
        recent_conversations = [
            conv for conv in self.conversation_data
            if conv['timestamp'] >= cutoff_date
        ]
        
        if not recent_conversations:
            return {"message": f"No data available for the last {days} days"}
        
        df = pd.DataFrame(recent_conversations)
        
        # Calculate comprehensive metrics
        analytics = {
            'period': f"Last {days} days",
            'total_conversations': len(df),
            'unique_sessions': df['session_id'].nunique(),
            'unique_users': df['user_id'].nunique(),
            'avg_response_time': df['response_time'].mean(),
            'p95_response_time': df['response_time'].quantile(0.95),
            'p99_response_time': df['response_time'].quantile(0.99),
            'avg_confidence': df['confidence'].mean(),
            'avg_message_length': df['message_length'].mean(),
            'avg_response_length': df['response_length'].mean(),
            
            # Intent analysis
            'top_intents': df['intent'].value_counts().head(10).to_dict(),
            'intent_distribution': df['intent'].value_counts().to_dict(),
            
            # Temporal analysis
            'daily_volume': df.groupby(df['timestamp'].dt.date).size().to_dict(),
            'hourly_volume': df.groupby(df['timestamp'].dt.hour).size().to_dict(),
            'weekday_volume': df.groupby(df['timestamp'].dt.day_name()).size().to_dict(),
            
            # Performance metrics
            'slow_responses': len(df[df['response_time'] > 3.0]),
            'fast_responses': len(df[df['response_time'] < 0.5]),
            'low_confidence_responses': len(df[df['confidence'] < 0.5]),
            
            # User engagement
            'messages_per_session': df.groupby('session_id').size().mean(),
            'sessions_per_user': df.groupby('user_id')['session_id'].nunique().mean(),
            
            # Quality metrics
            'error_rate': len(df[df['response_time'] > 5.0]) / len(df),
            'satisfaction_rate': self._calculate_satisfaction_rate(days)
        }
        
        return analytics
    
    async def get_user_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get detailed analytics for a specific user"""
        if user_id not in self.user_metrics:
            return {"message": "No data found for this user"}
        
        user_data = self.user_metrics[user_id]
        
        # Calculate engagement score
        engagement_score = self._calculate_engagement_score(user_data)
        
        # Get user's conversation history
        user_conversations = [
            conv for conv in self.conversation_data
            if conv['user_id'] == user_id
        ]
        
        # Analyze user patterns
        user_df = pd.DataFrame(user_conversations) if user_conversations else None
        
        analytics = {
            'user_id': user_id,
            'engagement_score': engagement_score,
            'total_messages': user_data['total_messages'],
            'total_sessions': len(user_data['total_sessions']),
            'avg_response_time': np.mean(user_data['avg_response_time']) if user_data['avg_response_time'] else 0,
            'most_common_intents': dict(user_data['intents'].most_common(5)),
            'intent_distribution': dict(user_data['intents']),
            'avg_message_length': np.mean(user_data['message_lengths']) if user_data['message_lengths'] else 0,
            'satisfaction_avg': np.mean(user_data['satisfaction_scores']) if user_data['satisfaction_scores'] else None,
            'first_seen': user_data['first_seen'].isoformat(),
            'last_seen': user_data['last_seen'].isoformat(),
            'activity_span_days': (user_data['last_seen'] - user_data['first_seen']).days,
            'messages_per_session': user_data['total_messages'] / max(len(user_data['total_sessions']), 1)
        }
        
        # Add temporal patterns if we have enough data
        if user_df is not None and len(user_df) > 5:
            analytics.update({
                'preferred_hours': user_df.groupby(user_df['timestamp'].dt.hour).size().to_dict(),
                'preferred_days': user_df.groupby(user_df['timestamp'].dt.day_name()).size().to_dict(),
                'activity_trend': self._calculate_activity_trend(user_df)
            })
        
        return analytics
    
    async def get_session_analytics(self, session_id: str) -> Dict[str, Any]:
        """Get detailed analytics for a specific session"""
        if session_id not in self.session_metrics:
            return {"message": "No data found for this session"}
        
        session_data = self.session_metrics[session_id]
        session_conversations = [
            conv for conv in self.conversation_data
            if conv['session_id'] == session_id
        ]
        
        if not session_conversations:
            return {"message": "No conversation data for this session"}
        
        session_df = pd.DataFrame(session_conversations)
        
        analytics = {
            'session_id': session_id,
            'user_id': session_data['user_id'],
            'message_count': session_data['message_count'],
            'session_duration_seconds': session_data['session_duration'],
            'avg_response_time': np.mean(session_data['avg_response_time']) if session_data['avg_response_time'] else 0,
            'top_intents': dict(session_data['intents'].most_common(3)),
            'intent_diversity': len(session_data['intents']),
            'start_time': session_data['start_time'].isoformat(),
            'last_activity': session_data['last_activity'].isoformat(),
            'messages_per_minute': session_data['message_count'] / max(session_data['session_duration'] / 60, 1),
            'avg_confidence': session_df['confidence'].mean(),
            'conversation_flow': self._analyze_conversation_flow(session_df)
        }
        
        return analytics
    
    async def get_product_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get product-related analytics"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Filter recent product conversations
        product_conversations = [
            conv for conv in self.conversation_data
            if conv['timestamp'] >= cutoff_date and 
               conv['metadata'] and 
               'product_suggestions' in conv['metadata']
        ]
        
        if not product_conversations:
            return {"message": f"No product data available for the last {days} days"}
        
        # Analyze product suggestions
        total_suggestions = sum(
            len(conv['metadata']['product_suggestions']) 
            for conv in product_conversations
        )
        
        # Product intent analysis
        product_intents = [
            conv['intent'] for conv in product_conversations
            if 'product' in conv['intent'].lower()
        ]
        
        return {
            'period': f"Last {days} days",
            'product_conversations': len(product_conversations),
            'total_suggestions': total_suggestions,
            'avg_suggestions_per_conversation': total_suggestions / len(product_conversations),
            'product_intents': Counter(product_intents).most_common(5),
            'suggestion_rate': len(product_conversations) / max(len([
                conv for conv in self.conversation_data
                if conv['timestamp'] >= cutoff_date
            ]), 1)
        }
    
    def _calculate_engagement_score(self, user_data: Dict) -> float:
        """Calculate user engagement score (0-100)"""
        score = 0
        
        # Message frequency (0-30 points)
        if user_data['total_messages'] > 100:
            score += 30
        elif user_data['total_messages'] > 50:
            score += 20
        elif user_data['total_messages'] > 10:
            score += 10
        
        # Session diversity (0-20 points)
        if len(user_data['total_sessions']) > 10:
            score += 20
        elif len(user_data['total_sessions']) > 5:
            score += 15
        elif len(user_data['total_sessions']) > 2:
            score += 10
        
        # Intent diversity (0-20 points)
        if len(user_data['intents']) > 5:
            score += 20
        elif len(user_data['intents']) > 3:
            score += 15
        elif len(user_data['intents']) > 1:
            score += 10
        
        # Response quality (0-30 points)
        avg_confidence = np.mean(user_data['satisfaction_scores']) if user_data['satisfaction_scores'] else 0
        score += avg_confidence * 30
        
        return min(score, 100)
    
    def _calculate_satisfaction_rate(self, days: int) -> float:
        """Calculate average satisfaction rate for the period"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_scores = []
        
        for user_id, user_data in self.user_metrics.items():
            for score in user_data['satisfaction_scores']:
                # This is a simplified approach - in production, you'd track timestamps
                recent_scores.append(score)
        
        return np.mean(recent_scores) if recent_scores else 0
    
    def _calculate_activity_trend(self, df: pd.DataFrame) -> str:
        """Calculate activity trend for a user"""
        if len(df) < 5:
            return "insufficient_data"
        
        # Group by day and calculate trend
        daily_counts = df.groupby(df['timestamp'].dt.date).size().sort_index()
        
        if len(daily_counts) < 2:
            return "stable"
        
        # Simple trend calculation
        recent_avg = daily_counts.tail(3).mean()
        earlier_avg = daily_counts.head(max(3, len(daily_counts) // 2)).mean()
        
        if recent_avg > earlier_avg * 1.2:
            return "increasing"
        elif recent_avg < earlier_avg * 0.8:
            return "decreasing"
        else:
            return "stable"
    
    def _analyze_conversation_flow(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze conversation flow patterns"""
        if len(df) < 2:
            return {"pattern": "single_message"}
        
        # Intent transitions
        intent_sequence = df['intent'].tolist()
        transitions = []
        
        for i in range(len(intent_sequence) - 1):
            transitions.append((intent_sequence[i], intent_sequence[i + 1]))
        
        transition_counts = Counter(transitions)
        
        return {
            "pattern": "multi_turn",
            "total_transitions": len(transitions),
            "common_transitions": transition_counts.most_common(3),
            "intent_variety": len(set(intent_sequence))
        }
    
    def get_health_metrics(self) -> Dict[str, Any]:
        """Get system health metrics"""
        total_conversations = len(self.conversation_data)
        
        if total_conversations == 0:
            return {"status": "no_data"}
        
        recent_conversations = [
            conv for conv in self.conversation_data
            if conv['timestamp'] > datetime.now() - timedelta(hours=1)
        ]
        
        return {
            "status": "healthy",
            "total_conversations": total_conversations,
            "active_users_last_hour": len(set(conv['user_id'] for conv in recent_conversations)),
            "conversations_last_hour": len(recent_conversations),
            "avg_response_time_last_hour": np.mean([conv['response_time'] for conv in recent_conversations]) if recent_conversations else 0,
            "error_rate_last_hour": len([conv for conv in recent_conversations if conv['response_time'] > 5.0]) / max(len(recent_conversations), 1)
        }

# Global analytics service instance
analytics_service = AnalyticsService()
