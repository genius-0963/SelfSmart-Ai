"""
CRUD operations for database models
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_

from .models import User, ChatSession, Message, Product, AnalyticsEvent, UserPreference, UserRole, MessageRole, AnalyticsEventType
from .connection import get_db


class UserCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_user(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def create_user(self, email: str, name: str, hashed_password: str, role: UserRole = UserRole.USER) -> User:
        db_user = User(
            email=email,
            name=name,
            hashed_password=hashed_password,
            role=role
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        user = self.get_user(user_id)
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            user.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(user)
        return user

    def update_last_login(self, user_id: int) -> None:
        user = self.get_user(user_id)
        if user:
            user.last_login = datetime.utcnow()
            self.db.commit()


class ChatSessionCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_session(self, session_id: int) -> Optional[ChatSession]:
        return self.db.query(ChatSession).filter(ChatSession.id == session_id).first()

    def get_user_sessions(self, user_id: int, limit: int = 50) -> List[ChatSession]:
        return (
            self.db.query(ChatSession)
            .filter(ChatSession.user_id == user_id)
            .order_by(desc(ChatSession.updated_at))
            .limit(limit)
            .all()
        )

    def create_session(self, user_id: int, title: Optional[str] = None) -> ChatSession:
        db_session = ChatSession(
            user_id=user_id,
            title=title or "New Chat"
        )
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        return db_session

    def update_session(self, session_id: int, **kwargs) -> Optional[ChatSession]:
        session = self.get_session(session_id)
        if session:
            for key, value in kwargs.items():
                if hasattr(session, key):
                    setattr(session, key, value)
            session.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(session)
        return session

    def end_session(self, session_id: int) -> Optional[ChatSession]:
        return self.update_session(session_id, is_active=False, ended_at=datetime.utcnow())

    def increment_message_count(self, session_id: int) -> None:
        session = self.get_session(session_id)
        if session:
            session.message_count += 1
            session.updated_at = datetime.utcnow()
            self.db.commit()


class MessageCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_message(self, message_id: int) -> Optional[Message]:
        return self.db.query(Message).filter(Message.id == message_id).first()

    def get_session_messages(self, session_id: int, limit: int = 100) -> List[Message]:
        return (
            self.db.query(Message)
            .filter(Message.session_id == session_id)
            .order_by(Message.created_at)
            .limit(limit)
            .all()
        )

    def create_message(
        self,
        session_id: int,
        role: MessageRole,
        content: str,
        product_suggestions: Optional[List[Dict]] = None,
        **kwargs
    ) -> Message:
        db_message = Message(
            session_id=session_id,
            role=role,
            content=content,
            product_suggestions=product_suggestions,
            **kwargs
        )
        self.db.add(db_message)
        self.db.commit()
        self.db.refresh(db_message)
        
        # Update session message count
        session_crud = ChatSessionCRUD(self.db)
        session_crud.increment_message_count(session_id)
        
        return db_message


class ProductCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_product(self, product_id: int) -> Optional[Product]:
        return self.db.query(Product).filter(Product.id == product_id).first()

    def get_products_by_source(self, source: str, limit: int = 100) -> List[Product]:
        return (
            self.db.query(Product)
            .filter(Product.source == source)
            .order_by(desc(Product.created_at))
            .limit(limit)
            .all()
        )

    def search_products(
        self,
        query: str,
        source: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[Product]:
        filters = []
        
        if query:
            filters.append(
                or_(
                    Product.title.ilike(f"%{query}%"),
                    Product.description.ilike(f"%{query}%")
                )
            )
        
        if source:
            filters.append(Product.source == source)
        
        if category:
            filters.append(Product.category == category)
        
        return (
            self.db.query(Product)
            .filter(and_(*filters) if filters else True)
            .order_by(desc(Product.rating))
            .limit(limit)
            .all()
        )

    def create_or_update_product(self, product_data: Dict[str, Any]) -> Product:
        # Check if product already exists by source and source_id
        existing = None
        if product_data.get('source_id') and product_data.get('source'):
            existing = (
                self.db.query(Product)
                .filter(
                    and_(
                        Product.source == product_data['source'],
                        Product.source_id == product_data['source_id']
                    )
                )
                .first()
            )
        
        if existing:
            # Update existing product
            for key, value in product_data.items():
                if hasattr(existing, key) and value is not None:
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            existing.last_scraped = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # Create new product
            db_product = Product(**product_data)
            db_product.created_at = datetime.utcnow()
            db_product.last_scraped = datetime.utcnow()
            self.db.add(db_product)
            self.db.commit()
            self.db.refresh(db_product)
            return db_product

    def increment_view_count(self, product_id: int) -> None:
        product = self.get_product(product_id)
        if product:
            product.view_count += 1
            self.db.commit()

    def increment_click_count(self, product_id: int) -> None:
        product = self.get_product(product_id)
        if product:
            product.click_count += 1
            self.db.commit()


class AnalyticsCRUD:
    def __init__(self, db: Session):
        self.db = db

    def create_event(
        self,
        event_type: AnalyticsEventType,
        user_id: Optional[int] = None,
        event_data: Optional[Dict] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> AnalyticsEvent:
        db_event = AnalyticsEvent(
            event_type=event_type,
            user_id=user_id,
            event_data=event_data,
            session_id=session_id,
            **kwargs
        )
        self.db.add(db_event)
        self.db.commit()
        self.db.refresh(db_event)
        return db_event

    def get_user_events(
        self,
        user_id: int,
        event_type: Optional[AnalyticsEventType] = None,
        limit: int = 100
    ) -> List[AnalyticsEvent]:
        query = self.db.query(AnalyticsEvent).filter(AnalyticsEvent.user_id == user_id)
        
        if event_type:
            query = query.filter(AnalyticsEvent.event_type == event_type)
        
        return query.order_by(desc(AnalyticsEvent.created_at)).limit(limit).all()

    def get_analytics_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        query = self.db.query(AnalyticsEvent)
        
        if start_date:
            query = query.filter(AnalyticsEvent.created_at >= start_date)
        if end_date:
            query = query.filter(AnalyticsEvent.created_at <= end_date)
        
        # Get counts by event type
        event_counts = (
            query.with_entities(
                AnalyticsEvent.event_type,
                func.count(AnalyticsEvent.id).label('count')
            )
            .group_by(AnalyticsEvent.event_type)
            .all()
        )
        
        # Get unique users
        unique_users = query.with_entities(func.count(func.distinct(AnalyticsEvent.user_id))).scalar()
        
        return {
            'event_counts': {event_type.value: count for event_type, count in event_counts},
            'unique_users': unique_users or 0,
            'total_events': query.count()
        }


class UserPreferenceCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_preference(self, user_id: int, key: str) -> Optional[UserPreference]:
        return (
            self.db.query(UserPreference)
            .filter(and_(UserPreference.user_id == user_id, UserPreference.key == key))
            .first()
        )

    def set_preference(self, user_id: int, key: str, value: Any) -> UserPreference:
        preference = self.get_preference(user_id, key)
        
        if preference:
            preference.value = value
            preference.updated_at = datetime.utcnow()
        else:
            preference = UserPreference(
                user_id=user_id,
                key=key,
                value=value
            )
            self.db.add(preference)
        
        self.db.commit()
        self.db.refresh(preference)
        return preference

    def get_user_preferences(self, user_id: int) -> List[UserPreference]:
        return (
            self.db.query(UserPreference)
            .filter(UserPreference.user_id == user_id)
            .all()
        )
