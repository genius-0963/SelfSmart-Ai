"""
Analytics engine for SmartShelf AI
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc

from ..database.connection import get_db
from ..database.models import User, ChatSession, Message, Product, AnalyticsEvent, UserPreference, MessageRole, AnalyticsEventType
from ..monitoring.logger import get_logger

logger = get_logger(__name__)


class AnalyticsEngine:
    """Central analytics engine for processing and analyzing data"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_dashboard_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive dashboard summary
        
        Args:
            start_date: Start date for analytics period
            end_date: End date for analytics period
        
        Returns:
            Dashboard summary data
        """
        try:
            # Default to last 30 days if not specified
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # User metrics
            user_metrics = await self._get_user_metrics(start_date, end_date)
            
            # Chat metrics
            chat_metrics = await self._get_chat_metrics(start_date, end_date)
            
            # Product metrics
            product_metrics = await self._get_product_metrics(start_date, end_date)
            
            # Engagement metrics
            engagement_metrics = await self._get_engagement_metrics(start_date, end_date)
            
            # Performance metrics
            performance_metrics = await self._get_performance_metrics(start_date, end_date)
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': (end_date - start_date).days
                },
                'users': user_metrics,
                'chats': chat_metrics,
                'products': product_metrics,
                'engagement': engagement_metrics,
                'performance': performance_metrics
            }
            
        except Exception as e:
            logger.error(f"Error generating dashboard summary: {e}")
            return {}
    
    async def _get_user_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get user-related metrics"""
        try:
            # Total users
            total_users = self.db.query(User).count()
            
            # New users in period
            new_users = self.db.query(User).filter(
                User.created_at >= start_date,
                User.created_at <= end_date
            ).count()
            
            # Active users (users with at least one session in period)
            active_users = self.db.query(User.id).join(ChatSession).filter(
                ChatSession.created_at >= start_date,
                ChatSession.created_at <= end_date
            ).distinct().count()
            
            # Daily active users
            daily_active_users = await self._get_daily_active_users(start_date, end_date)
            
            # User retention (users who returned after first session)
            retention_rate = await self._calculate_retention_rate(start_date, end_date)
            
            # User demographics
            user_roles = self.db.query(User.role, func.count(User.id)).group_by(User.role).all()
            
            return {
                'total_users': total_users,
                'new_users': new_users,
                'active_users': active_users,
                'daily_active_users': daily_active_users,
                'retention_rate': retention_rate,
                'user_roles': {role.value: count for role, count in user_roles},
                'growth_rate': (new_users / max(total_users - new_users, 1)) * 100
            }
            
        except Exception as e:
            logger.error(f"Error getting user metrics: {e}")
            return {}
    
    async def _get_chat_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get chat-related metrics"""
        try:
            # Total sessions
            total_sessions = self.db.query(ChatSession).filter(
                ChatSession.created_at >= start_date,
                ChatSession.created_at <= end_date
            ).count()
            
            # Total messages
            total_messages = self.db.query(Message).join(ChatSession).filter(
                ChatSession.created_at >= start_date,
                ChatSession.created_at <= end_date
            ).count()
            
            # Average session length (in messages)
            avg_session_length = self.db.query(func.avg(ChatSession.message_count)).filter(
                ChatSession.created_at >= start_date,
                ChatSession.created_at <= end_date,
                ChatSession.message_count > 0
            ).scalar() or 0
            
            # Messages by role
            messages_by_role = self.db.query(Message.role, func.count(Message.id)).join(ChatSession).filter(
                ChatSession.created_at >= start_date,
                ChatSession.created_at <= end_date
            ).group_by(Message.role).all()
            
            # Daily conversation counts
            daily_conversations = await self._get_daily_conversations(start_date, end_date)
            
            # Average response time
            avg_response_time = self.db.query(func.avg(Message.processing_time)).join(ChatSession).filter(
                ChatSession.created_at >= start_date,
                ChatSession.created_at <= end_date,
                Message.processing_time.isnot(None)
            ).scalar() or 0
            
            return {
                'total_sessions': total_sessions,
                'total_messages': total_messages,
                'avg_session_length': round(float(avg_session_length), 2),
                'messages_by_role': {role.value: count for role, count in messages_by_role},
                'daily_conversations': daily_conversations,
                'avg_response_time': round(float(avg_response_time), 3),
                'messages_per_session': total_messages / max(total_sessions, 1)
            }
            
        except Exception as e:
            logger.error(f"Error getting chat metrics: {e}")
            return {}
    
    async def _get_product_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get product-related metrics"""
        try:
            # Total products
            total_products = self.db.query(Product).count()
            
            # New products in period
            new_products = self.db.query(Product).filter(
                Product.created_at >= start_date,
                Product.created_at <= end_date
            ).count()
            
            # Products by source
            products_by_source = self.db.query(Product.source, func.count(Product.id)).group_by(Product.source).all()
            
            # Most viewed products
            most_viewed = self.db.query(Product).order_by(desc(Product.view_count)).limit(10).all()
            
            # Most clicked products
            most_clicked = self.db.query(Product).order_by(desc(Product.click_count)).limit(10).all()
            
            # Product categories
            categories = self.db.query(Product.category, func.count(Product.id)).filter(
                Product.category.isnot(None)
            ).group_by(Product.category).order_by(desc(func.count(Product.id))).limit(10).all()
            
            # Average product rating
            avg_rating = self.db.query(func.avg(Product.rating)).filter(
                Product.rating.isnot(None)
            ).scalar() or 0
            
            return {
                'total_products': total_products,
                'new_products': new_products,
                'products_by_source': {source: count for source, count in products_by_source},
                'most_viewed': [
                    {'id': p.id, 'title': p.title, 'views': p.view_count, 'source': p.source}
                    for p in most_viewed
                ],
                'most_clicked': [
                    {'id': p.id, 'title': p.title, 'clicks': p.click_count, 'source': p.source}
                    for p in most_clicked
                ],
                'top_categories': [{'category': cat, 'count': count} for cat, count in categories],
                'avg_rating': round(float(avg_rating), 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting product metrics: {e}")
            return {}
    
    async def _get_engagement_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get engagement metrics"""
        try:
            # Total events
            total_events = self.db.query(AnalyticsEvent).filter(
                AnalyticsEvent.created_at >= start_date,
                AnalyticsEvent.created_at <= end_date
            ).count()
            
            # Events by type
            events_by_type = self.db.query(
                AnalyticsEvent.event_type, 
                func.count(AnalyticsEvent.id)
            ).filter(
                AnalyticsEvent.created_at >= start_date,
                AnalyticsEvent.created_at <= end_date
            ).group_by(AnalyticsEvent.event_type).all()
            
            # User engagement score (average events per active user)
            active_users = self.db.query(User.id).join(ChatSession).filter(
                ChatSession.created_at >= start_date,
                ChatSession.created_at <= end_date
            ).distinct().count()
            
            engagement_score = total_events / max(active_users, 1)
            
            # Feature usage
            feature_usage = await self._get_feature_usage(start_date, end_date)
            
            return {
                'total_events': total_events,
                'events_by_type': {event_type.value: count for event_type, count in events_by_type},
                'engagement_score': round(engagement_score, 2),
                'feature_usage': feature_usage
            }
            
        except Exception as e:
            logger.error(f"Error getting engagement metrics: {e}")
            return {}
    
    async def _get_performance_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get performance metrics"""
        try:
            # Average response time by model
            response_times = self.db.query(
                Message.model_used,
                func.avg(Message.processing_time),
                func.count(Message.id)
            ).join(ChatSession).filter(
                ChatSession.created_at >= start_date,
                ChatSession.created_at <= end_date,
                Message.processing_time.isnot(None),
                Message.model_used.isnot(None)
            ).group_by(Message.model_used).all()
            
            # Token usage
            total_tokens = self.db.query(func.sum(Message.token_count)).join(ChatSession).filter(
                ChatSession.created_at >= start_date,
                ChatSession.created_at <= end_date,
                Message.token_count.isnot(None)
            ).scalar() or 0
            
            # Error rate
            total_messages = self.db.query(Message).join(ChatSession).filter(
                ChatSession.created_at >= start_date,
                ChatSession.created_at <= end_date
            ).count()
            
            # Get error messages (those with processing_time = None or very high)
            error_messages = self.db.query(Message).join(ChatSession).filter(
                ChatSession.created_at >= start_date,
                ChatSession.created_at <= end_date,
                or_(
                    Message.processing_time.is_(None),
                    Message.processing_time > 30  # Messages taking > 30 seconds
                )
            ).count()
            
            error_rate = (error_messages / max(total_messages, 1)) * 100
            
            return {
                'response_times': [
                    {
                        'model': model,
                        'avg_time': round(float(avg_time), 3),
                        'message_count': count
                    }
                    for model, avg_time, count in response_times
                ],
                'total_tokens': int(total_tokens),
                'error_rate': round(error_rate, 2),
                'total_messages': total_messages,
                'error_messages': error_messages
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {}
    
    async def _get_daily_active_users(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get daily active users count"""
        try:
            # Generate date range
            date_range = []
            current_date = start_date.date()
            end_date_only = end_date.date()
            
            while current_date <= end_date_only:
                date_range.append(current_date)
                current_date += timedelta(days=1)
            
            daily_users = []
            
            for date in date_range:
                day_start = datetime.combine(date, datetime.min.time())
                day_end = datetime.combine(date, datetime.max.time())
                
                active_count = self.db.query(User.id).join(ChatSession).filter(
                    ChatSession.created_at >= day_start,
                    ChatSession.created_at <= day_end
                ).distinct().count()
                
                daily_users.append({
                    'date': date.isoformat(),
                    'active_users': active_count
                })
            
            return daily_users
            
        except Exception as e:
            logger.error(f"Error getting daily active users: {e}")
            return []
    
    async def _get_daily_conversations(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get daily conversation counts"""
        try:
            # Generate date range
            date_range = []
            current_date = start_date.date()
            end_date_only = end_date.date()
            
            while current_date <= end_date_only:
                date_range.append(current_date)
                current_date += timedelta(days=1)
            
            daily_conversations = []
            
            for date in date_range:
                day_start = datetime.combine(date, datetime.min.time())
                day_end = datetime.combine(date, datetime.max.time())
                
                session_count = self.db.query(ChatSession).filter(
                    ChatSession.created_at >= day_start,
                    ChatSession.created_at <= day_end
                ).count()
                
                message_count = self.db.query(Message).join(ChatSession).filter(
                    ChatSession.created_at >= day_start,
                    ChatSession.created_at <= day_end
                ).count()
                
                daily_conversations.append({
                    'date': date.isoformat(),
                    'sessions': session_count,
                    'messages': message_count
                })
            
            return daily_conversations
            
        except Exception as e:
            logger.error(f"Error getting daily conversations: {e}")
            return []
    
    async def _calculate_retention_rate(self, start_date: datetime, end_date: datetime) -> float:
        """Calculate user retention rate"""
        try:
            # Get users who signed up before the period
            existing_users = self.db.query(User).filter(
                User.created_at < start_date
            ).all()
            
            if not existing_users:
                return 0.0
            
            # Check how many of these users were active during the period
            retained_count = 0
            
            for user in existing_users:
                has_activity = self.db.query(ChatSession).filter(
                    ChatSession.user_id == user.id,
                    ChatSession.created_at >= start_date,
                    ChatSession.created_at <= end_date
                ).first()
                
                if has_activity:
                    retained_count += 1
            
            return (retained_count / len(existing_users)) * 100
            
        except Exception as e:
            logger.error(f"Error calculating retention rate: {e}")
            return 0.0
    
    async def _get_feature_usage(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get feature usage statistics"""
        try:
            # Product search usage
            product_searches = self.db.query(AnalyticsEvent).filter(
                AnalyticsEvent.event_type == AnalyticsEventType.SEARCH_PERFORMED,
                AnalyticsEvent.created_at >= start_date,
                AnalyticsEvent.created_at <= end_date
            ).count()
            
            # Product clicks
            product_clicks = self.db.query(AnalyticsEvent).filter(
                AnalyticsEvent.event_type == AnalyticsEventType.PRODUCT_CLICKED,
                AnalyticsEvent.created_at >= start_date,
                AnalyticsEvent.created_at <= end_date
            ).count()
            
            # Sessions with product suggestions
            sessions_with_products = self.db.query(Message).join(ChatSession).filter(
                ChatSession.created_at >= start_date,
                ChatSession.created_at <= end_date,
                Message.product_suggestions.isnot(None),
                func.json_length(Message.product_suggestions) > 0
            ).distinct(ChatSession.id).count()
            
            total_sessions = self.db.query(ChatSession).filter(
                ChatSession.created_at >= start_date,
                ChatSession.created_at <= end_date
            ).count()
            
            return {
                'product_searches': product_searches,
                'product_clicks': product_clicks,
                'sessions_with_products': sessions_with_products,
                'product_suggestion_rate': (sessions_with_products / max(total_sessions, 1)) * 100
            }
            
        except Exception as e:
            logger.error(f"Error getting feature usage: {e}")
            return {}
    
    async def get_user_analytics(self, user_id: int) -> Dict[str, Any]:
        """Get analytics for a specific user"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {}
            
            # User sessions
            sessions = self.db.query(ChatSession).filter(
                ChatSession.user_id == user_id
            ).order_by(desc(ChatSession.created_at)).all()
            
            # User messages
            messages = self.db.query(Message).join(ChatSession).filter(
                ChatSession.user_id == user_id
            ).all()
            
            # User events
            events = self.db.query(AnalyticsEvent).filter(
                AnalyticsEvent.user_id == user_id
            ).all()
            
            # Calculate metrics
            total_sessions = len(sessions)
            total_messages = len(messages)
            total_events = len(events)
            
            # Average session length
            avg_session_length = sum(s.message_count for s in sessions) / max(total_sessions, 1)
            
            # Most active day
            day_activity = {}
            for session in sessions:
                day = session.created_at.date().isoformat()
                day_activity[day] = day_activity.get(day, 0) + 1
            
            most_active_day = max(day_activity.items(), key=lambda x: x[1])[0] if day_activity else None
            
            return {
                'user_id': user_id,
                'user_name': user.name,
                'join_date': user.created_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'total_sessions': total_sessions,
                'total_messages': total_messages,
                'total_events': total_events,
                'avg_session_length': round(avg_session_length, 2),
                'most_active_day': most_active_day,
                'day_activity': day_activity
            }
            
        except Exception as e:
            logger.error(f"Error getting user analytics: {e}")
            return {}
