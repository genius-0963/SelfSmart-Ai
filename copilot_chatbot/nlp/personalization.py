"""
Intelligent AI Backend - Personalization Engine
Production-grade OOP implementation for user preference learning and personalization
"""

import json
import logging
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class PreferenceType(Enum):
    """Enumeration of preference types"""
    TOPIC = "topic"
    PRODUCT_CATEGORY = "product_category"
    BRAND = "brand"
    PRICE_RANGE = "price_range"
    CONVERSATION_STYLE = "conversation_style"
    RESPONSE_LENGTH = "response_length"
    SPORTS_TEAM = "sports_team"
    CONTENT_TYPE = "content_type"
    INTERACTION_PATTERN = "interaction_pattern"


class PersonalizationLevel(Enum):
    """Enumeration of personalization levels"""
    NONE = "none"
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class UserPreference:
    """Data class for user preferences"""
    user_id: str
    preference_type: PreferenceType
    key: str
    value: Any
    confidence: float
    weight: float
    created_at: datetime
    updated_at: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserProfile:
    """Data class for comprehensive user profile"""
    user_id: str
    personalization_level: PersonalizationLevel
    preferences: Dict[PreferenceType, Dict[str, UserPreference]]
    interaction_patterns: Dict[str, Any]
    behavioral_traits: Dict[str, float]
    demographics: Dict[str, Any]
    created_at: datetime
    last_updated: datetime
    total_interactions: int = 0
    session_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class PreferenceExtractor(ABC):
    """Abstract base class for preference extraction"""
    
    @abstractmethod
    def extract_preferences(self, user_input: str, context: Dict[str, Any], 
                           current_profile: UserProfile) -> List[UserPreference]:
        """Extract preferences from user input and context"""
        pass


class TopicPreferenceExtractor(PreferenceExtractor):
    """Extract topic preferences from user interactions"""
    
    def extract_preferences(self, user_input: str, context: Dict[str, Any], 
                           current_profile: UserProfile) -> List[UserPreference]:
        """Extract topic preferences"""
        preferences = []
        
        # Analyze intent and entities for topic preferences
        intent = context.get('intent', '')
        entities = context.get('entities', {})
        
        # Extract topic from intent
        if intent:
            topic_preference = UserPreference(
                user_id=current_profile.user_id,
                preference_type=PreferenceType.TOPIC,
                key=intent,
                value=self._calculate_topic_affinity(intent, entities),
                confidence=0.7,
                weight=0.8,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata={'source': 'intent_analysis'}
            )
            preferences.append(topic_preference)
        
        # Extract entity-based preferences
        for entity_type, entity_values in entities.items():
            if entity_type in ['product_type', 'sport', 'brand']:
                for value in entity_values:
                    entity_preference = UserPreference(
                        user_id=current_profile.user_id,
                        preference_type=self._map_entity_to_preference_type(entity_type),
                        key=value,
                        value=self._calculate_entity_value(value, entity_type),
                        confidence=0.6,
                        weight=0.7,
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                        metadata={'source': 'entity_extraction', 'entity_type': entity_type}
                    )
                    preferences.append(entity_preference)
        
        return preferences
    
    def _calculate_topic_affinity(self, intent: str, entities: Dict[str, Any]) -> float:
        """Calculate affinity score for a topic"""
        base_score = 0.5
        
        # Boost score based on entities
        if entities:
            entity_boost = min(len(entities) * 0.1, 0.3)
            base_score += entity_boost
        
        # Specific intent boosts
        intent_boosts = {
            'sports_topic': 0.3,
            'product_inquiry': 0.2,
            'help_request': 0.1
        }
        
        base_score += intent_boosts.get(intent, 0)
        
        return min(base_score, 1.0)
    
    def _calculate_entity_value(self, value: str, entity_type: str) -> float:
        """Calculate preference value for an entity"""
        # Base value depends on entity type
        base_values = {
            'product_type': 0.6,
            'sport': 0.7,
            'brand': 0.5,
            'team': 0.8
        }
        
        return base_values.get(entity_type, 0.5)
    
    def _map_entity_to_preference_type(self, entity_type: str) -> PreferenceType:
        """Map entity type to preference type"""
        mapping = {
            'product_type': PreferenceType.PRODUCT_CATEGORY,
            'brand': PreferenceType.BRAND,
            'sport': PreferenceType.TOPIC,
            'team': PreferenceType.SPORTS_TEAM
        }
        return mapping.get(entity_type, PreferenceType.TOPIC)


class InteractionPatternExtractor(PreferenceExtractor):
    """Extract interaction patterns from user behavior"""
    
    def extract_preferences(self, user_input: str, context: Dict[str, Any], 
                           current_profile: UserProfile) -> List[UserPreference]:
        """Extract interaction pattern preferences"""
        preferences = []
        
        # Analyze input characteristics
        input_length = len(user_input)
        word_count = len(user_input.split())
        has_question = '?' in user_input
        has_exclamation = '!' in user_input
        
        # Conversation style preference
        style_score = self._calculate_conversation_style(
            input_length, word_count, has_question, has_exclamation
        )
        
        style_preference = UserPreference(
            user_id=current_profile.user_id,
            preference_type=PreferenceType.CONVERSATION_STYLE,
            key='communication_style',
            value=style_score,
            confidence=0.5,
            weight=0.6,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={
                'input_length': input_length,
                'word_count': word_count,
                'has_question': has_question,
                'has_exclamation': has_exclamation
            }
        )
        preferences.append(style_preference)
        
        # Response length preference
        response_length_pref = self._determine_response_length_preference(word_count)
        
        length_preference = UserPreference(
            user_id=current_profile.user_id,
            preference_type=PreferenceType.RESPONSE_LENGTH,
            key='preferred_length',
            value=response_length_pref,
            confidence=0.4,
            weight=0.5,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={'word_count': word_count}
        )
        preferences.append(length_preference)
        
        return preferences
    
    def _calculate_conversation_style(self, input_length: int, word_count: int, 
                                    has_question: bool, has_exclamation: bool) -> Dict[str, float]:
        """Calculate conversation style scores"""
        style_scores = {
            'formal': 0.5,
            'casual': 0.5,
            'detailed': 0.5,
            'concise': 0.5,
            'inquisitive': 0.0,
            'enthusiastic': 0.0
        }
        
        # Adjust based on input characteristics
        if word_count > 15:
            style_scores['detailed'] += 0.3
            style_scores['concise'] -= 0.3
        elif word_count < 5:
            style_scores['concise'] += 0.3
            style_scores['detailed'] -= 0.3
        
        if has_question:
            style_scores['inquisitive'] += 0.4
        
        if has_exclamation:
            style_scores['enthusiastic'] += 0.4
            style_scores['casual'] += 0.2
            style_scores['formal'] -= 0.2
        
        # Normalize scores
        for key in style_scores:
            style_scores[key] = max(0.0, min(1.0, style_scores[key]))
        
        return style_scores
    
    def _determine_response_length_preference(self, word_count: int) -> str:
        """Determine preferred response length based on input"""
        if word_count <= 5:
            return 'short'
        elif word_count <= 12:
            return 'medium'
        else:
            return 'detailed'


class PersonalizationEngine:
    """Main personalization engine"""
    
    def __init__(self):
        self.extractors = [
            TopicPreferenceExtractor(),
            InteractionPatternExtractor()
        ]
        self.user_profiles: Dict[str, UserProfile] = {}
        self.preference_decay_rate = 0.95  # Daily decay factor
        self.min_confidence_threshold = 0.3
        logger.info("Personalization Engine initialized")
    
    def get_or_create_profile(self, user_id: str) -> UserProfile:
        """Get existing user profile or create new one"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserProfile(
                user_id=user_id,
                personalization_level=PersonalizationLevel.NONE,
                preferences={},
                interaction_patterns={},
                behavioral_traits={},
                demographics={},
                created_at=datetime.now(),
                last_updated=datetime.now()
            )
            logger.info(f"Created new profile for user {user_id}")
        
        return self.user_profiles[user_id]
    
    def update_preferences(self, user_id: str, user_input: str, context: Dict[str, Any]) -> List[UserPreference]:
        """Update user preferences based on new interaction"""
        profile = self.get_or_create_profile(user_id)
        
        # Extract new preferences
        new_preferences = []
        for extractor in self.extractors:
            extracted_prefs = extractor.extract_preferences(user_input, context, profile)
            new_preferences.extend(extracted_prefs)
        
        # Update existing preferences or add new ones
        for new_pref in new_preferences:
            self._update_preference(profile, new_pref)
        
        # Update profile statistics
        profile.total_interactions += 1
        profile.last_updated = datetime.now()
        
        # Update personalization level
        self._update_personalization_level(profile)
        
        # Apply preference decay
        self._apply_preference_decay(profile)
        
        logger.info(f"Updated preferences for user {user_id}: {len(new_preferences)} new preferences")
        return new_preferences
    
    def _update_preference(self, profile: UserProfile, new_preference: UserPreference):
        """Update or add a preference to the user profile"""
        pref_type = new_preference.preference_type
        
        if pref_type not in profile.preferences:
            profile.preferences[pref_type] = {}
        
        existing_pref = profile.preferences[pref_type].get(new_preference.key)
        
        if existing_pref:
            # Update existing preference using weighted average
            total_weight = existing_pref.weight + new_preference.weight
            existing_pref.value = (
                (existing_pref.value * existing_pref.weight + new_preference.value * new_preference.weight) 
                / total_weight
            )
            existing_pref.confidence = (
                (existing_pref.confidence * existing_pref.weight + new_preference.confidence * new_preference.weight) 
                / total_weight
            )
            existing_pref.weight = min(total_weight, 10.0)  # Cap weight at 10
            existing_pref.updated_at = datetime.now()
            existing_pref.access_count += 1
            existing_pref.last_accessed = datetime.now()
        else:
            # Add new preference
            profile.preferences[pref_type][new_preference.key] = new_preference
    
    def _update_personalization_level(self, profile: UserProfile):
        """Update personalization level based on profile completeness"""
        total_preferences = sum(len(prefs) for prefs in profile.preferences.values())
        avg_confidence = 0.0
        
        if total_preferences > 0:
            all_prefs = []
            for prefs in profile.preferences.values():
                all_prefs.extend(prefs.values())
            avg_confidence = sum(pref.confidence for pref in all_prefs) / len(all_prefs)
        
        # Determine personalization level
        if total_preferences == 0:
            level = PersonalizationLevel.NONE
        elif total_preferences < 5 and avg_confidence < 0.5:
            level = PersonalizationLevel.BASIC
        elif total_preferences < 15 and avg_confidence < 0.7:
            level = PersonalizationLevel.INTERMEDIATE
        elif total_preferences < 30 and avg_confidence < 0.8:
            level = PersonalizationLevel.ADVANCED
        else:
            level = PersonalizationLevel.EXPERT
        
        profile.personization_level = level
    
    def _apply_preference_decay(self, profile: UserProfile):
        """Apply time-based decay to preference weights and confidence"""
        current_time = datetime.now()
        
        for pref_type, preferences in profile.preferences.items():
            for key, preference in preferences.items():
                # Calculate days since last update
                days_since_update = (current_time - preference.updated_at).days
                
                if days_since_update > 0:
                    # Apply decay
                    decay_factor = self.preference_decay_rate ** days_since_update
                    preference.weight *= decay_factor
                    preference.confidence *= decay_factor
                    
                    # Remove preferences that have decayed too much
                    if preference.confidence < self.min_confidence_threshold:
                        del preferences[key]
        
        # Clean up empty preference types
        empty_types = [pref_type for pref_type, prefs in profile.preferences.items() if not prefs]
        for empty_type in empty_types:
            del profile.preferences[empty_type]
    
    def get_personalized_response_modifiers(self, user_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get response modifiers based on user preferences"""
        profile = self.get_or_create_profile(user_id)
        
        modifiers = {
            'response_length': 'medium',
            'conversation_style': 'balanced',
            'topic_preferences': {},
            'content_personalization': {},
            'confidence_boost': 0.0
        }
        
        # Apply conversation style preferences
        conv_style_prefs = profile.preferences.get(PreferenceType.CONVERSATION_STYLE, {})
        if 'communication_style' in conv_style_prefs:
            style_scores = conv_style_prefs['communication_style'].value
            modifiers['conversation_style'] = self._determine_conversation_style(style_scores)
        
        # Apply response length preferences
        length_prefs = profile.preferences.get(PreferenceType.RESPONSE_LENGTH, {})
        if 'preferred_length' in length_prefs:
            modifiers['response_length'] = length_prefs['preferred_length'].value
        
        # Apply topic preferences
        topic_prefs = profile.preferences.get(PreferenceType.TOPIC, {})
        for topic, pref in topic_prefs.items():
            modifiers['topic_preferences'][topic] = pref.value
        
        # Apply product category preferences
        product_prefs = profile.preferences.get(PreferenceType.PRODUCT_CATEGORY, {})
        for category, pref in product_prefs.items():
            modifiers['content_personalization'][category] = pref.value
        
        # Apply brand preferences
        brand_prefs = profile.preferences.get(PreferenceType.BRAND, {})
        if brand_prefs:
            modifiers['content_personalization']['preferred_brands'] = list(brand_prefs.keys())
        
        # Calculate confidence boost based on personalization level
        level_boosts = {
            PersonalizationLevel.NONE: 0.0,
            PersonalizationLevel.BASIC: 0.05,
            PersonalizationLevel.INTERMEDIATE: 0.1,
            PersonalizationLevel.ADVANCED: 0.15,
            PersonalizationLevel.EXPERT: 0.2
        }
        modifiers['confidence_boost'] = level_boosts.get(profile.personalization_level, 0.0)
        
        return modifiers
    
    def _determine_conversation_style(self, style_scores: Dict[str, float]) -> str:
        """Determine conversation style from style scores"""
        max_score = max(style_scores.values())
        dominant_styles = [style for style, score in style_scores.items() if score == max_score]
        
        if 'detailed' in dominant_styles:
            return 'detailed'
        elif 'casual' in dominant_styles:
            return 'casual'
        elif 'formal' in dominant_styles:
            return 'formal'
        elif 'inquisitive' in dominant_styles:
            return 'engaging'
        else:
            return 'balanced'
    
    def get_user_insights(self, user_id: str) -> Dict[str, Any]:
        """Get insights about user preferences and behavior"""
        profile = self.get_or_create_profile(user_id)
        
        insights = {
            'user_id': user_id,
            'personalization_level': profile.personalization_level.value,
            'total_interactions': profile.total_interactions,
            'session_count': profile.session_count,
            'preference_summary': {},
            'top_topics': [],
            'behavioral_patterns': {},
            'recommendation_accuracy': 0.0
        }
        
        # Summarize preferences by type
        for pref_type, preferences in profile.preferences.items():
            insights['preference_summary'][pref_type.value] = {
                'count': len(preferences),
                'avg_confidence': sum(pref.confidence for pref in preferences.values()) / len(preferences) if preferences else 0,
                'top_preferences': sorted(
                    [(key, pref.value, pref.confidence) for key, pref in preferences.items()],
                    key=lambda x: x[2], reverse=True
                )[:3]
            }
        
        # Get top topics
        topic_prefs = profile.preferences.get(PreferenceType.TOPIC, {})
        insights['top_topics'] = sorted(
            [(key, pref.value) for key, pref in topic_prefs.items()],
            key=lambda x: x[1], reverse=True
        )[:5]
        
        # Analyze behavioral patterns
        insights['behavioral_patterns'] = self._analyze_behavioral_patterns(profile)
        
        return insights
    
    def _analyze_behavioral_patterns(self, profile: UserProfile) -> Dict[str, Any]:
        """Analyze user behavioral patterns"""
        patterns = {
            'interaction_frequency': 'normal',
            'preferred_interaction_time': 'unknown',
            'content_engagement': 'medium',
            'exploration_tendency': 0.5,
            'loyalty_score': 0.5
        }
        
        # Calculate interaction frequency
        if profile.total_interactions > 50:
            patterns['interaction_frequency'] = 'high'
        elif profile.total_interactions < 10:
            patterns['interaction_frequency'] = 'low'
        
        # Calculate exploration tendency (variety of topics)
        topic_prefs = profile.preferences.get(PreferenceType.TOPIC, {})
        if len(topic_prefs) > 5:
            patterns['exploration_tendency'] = 0.8
        elif len(topic_prefs) < 2:
            patterns['exploration_tendency'] = 0.2
        
        # Calculate loyalty score (consistency in preferences)
        total_prefs = sum(len(prefs) for prefs in profile.preferences.values())
        if total_prefs > 0:
            avg_confidence = sum(
                pref.confidence 
                for prefs in profile.preferences.values() 
                for pref in prefs.values()
            ) / total_prefs
            patterns['loyalty_score'] = avg_confidence
        
        return patterns
    
    def get_similar_users(self, user_id: str, limit: int = 5) -> List[Tuple[str, float]]:
        """Find similar users based on preference similarity"""
        target_profile = self.get_or_create_profile(user_id)
        similarities = []
        
        for other_id, other_profile in self.user_profiles.items():
            if other_id == user_id:
                continue
            
            similarity = self._calculate_profile_similarity(target_profile, other_profile)
            if similarity > 0.1:  # Minimum similarity threshold
                similarities.append((other_id, similarity))
        
        # Sort by similarity and return top matches
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]
    
    def _calculate_profile_similarity(self, profile1: UserProfile, profile2: UserProfile) -> float:
        """Calculate similarity between two user profiles"""
        similarity_score = 0.0
        total_comparisons = 0
        
        # Compare each preference type
        for pref_type in PreferenceType:
            prefs1 = profile1.preferences.get(pref_type, {})
            prefs2 = profile2.preferences.get(pref_type, {})
            
            if not prefs1 or not prefs2:
                continue
            
            # Calculate similarity for this preference type
            type_similarity = 0.0
            common_keys = set(prefs1.keys()) & set(prefs2.keys())
            
            if common_keys:
                for key in common_keys:
                    pref1 = prefs1[key]
                    pref2 = prefs2[key]
                    
                    # Compare preference values (weighted by confidence)
                    value_similarity = 1.0 - abs(pref1.value - pref2.value)
                    confidence_weight = (pref1.confidence + pref2.confidence) / 2
                    type_similarity += value_similarity * confidence_weight
                
                type_similarity /= len(common_keys)
                similarity_score += type_similarity
                total_comparisons += 1
        
        if total_comparisons > 0:
            return similarity_score / total_comparisons
        else:
            return 0.0
    
    def export_profile(self, user_id: str) -> Dict[str, Any]:
        """Export user profile for backup or analysis"""
        profile = self.get_or_create_profile(user_id)
        
        export_data = {
            'user_id': profile.user_id,
            'personalization_level': profile.personalization_level.value,
            'total_interactions': profile.total_interactions,
            'session_count': profile.session_count,
            'created_at': profile.created_at.isoformat(),
            'last_updated': profile.last_updated.isoformat(),
            'preferences': {}
        }
        
        # Convert preferences to serializable format
        for pref_type, preferences in profile.preferences.items():
            export_data['preferences'][pref_type.value] = {}
            for key, pref in preferences.items():
                export_data['preferences'][pref_type.value][key] = {
                    'value': pref.value,
                    'confidence': pref.confidence,
                    'weight': pref.weight,
                    'created_at': pref.created_at.isoformat(),
                    'updated_at': pref.updated_at.isoformat(),
                    'access_count': pref.access_count,
                    'metadata': pref.metadata
                }
        
        return export_data
    
    def import_profile(self, profile_data: Dict[str, Any]) -> bool:
        """Import user profile from exported data"""
        try:
            user_id = profile_data['user_id']
            
            # Create or update profile
            profile = self.get_or_create_profile(user_id)
            profile.personization_level = PersonalizationLevel(profile_data['personalization_level'])
            profile.total_interactions = profile_data['total_interactions']
            profile.session_count = profile_data['session_count']
            profile.created_at = datetime.fromisoformat(profile_data['created_at'])
            profile.last_updated = datetime.fromisoformat(profile_data['last_updated'])
            
            # Import preferences
            profile.preferences = {}
            for pref_type_str, preferences in profile_data['preferences'].items():
                pref_type = PreferenceType(pref_type_str)
                profile.preferences[pref_type] = {}
                
                for key, pref_data in preferences.items():
                    preference = UserPreference(
                        user_id=user_id,
                        preference_type=pref_type,
                        key=key,
                        value=pref_data['value'],
                        confidence=pref_data['confidence'],
                        weight=pref_data['weight'],
                        created_at=datetime.fromisoformat(pref_data['created_at']),
                        updated_at=datetime.fromisoformat(pref_data['updated_at']),
                        access_count=pref_data['access_count'],
                        metadata=pref_data['metadata']
                    )
                    profile.preferences[pref_type][key] = preference
            
            logger.info(f"Successfully imported profile for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error importing profile: {str(e)}")
            return False


# Factory function for easy instantiation
def create_personalization_engine() -> PersonalizationEngine:
    """Factory function to create personalization engine"""
    return PersonalizationEngine()


if __name__ == "__main__":
    # Test the personalization engine
    engine = create_personalization_engine()
    
    print("=== Personalization Engine Test ===")
    
    # Simulate user interactions
    user_id = "test_user"
    
    interactions = [
        ("Hi there!", {"intent": "greeting", "entities": {}}),
        ("Tell me about laptops", {"intent": "product_inquiry", "entities": {"product_type": ["laptop"]}}),
        ("I love football!", {"intent": "sports_topic", "entities": {"sport": ["football"]}}),
        ("What's the best laptop for programming?", {"intent": "product_inquiry", "entities": {"product_type": ["laptop"]}}),
        ("Real Madrid is the best team", {"intent": "sports_topic", "entities": {"team": ["real madrid"]}})
    ]
    
    for message, context in interactions:
        preferences = engine.update_preferences(user_id, message, context)
        print(f"Processed: '{message}' - {len(preferences)} preferences updated")
    
    # Get user insights
    insights = engine.get_user_insights(user_id)
    print(f"\nUser Insights for {user_id}:")
    print(f"Personalization Level: {insights['personalization_level']}")
    print(f"Total Interactions: {insights['total_interactions']}")
    print(f"Top Topics: {insights['top_topics']}")
    
    # Get personalized response modifiers
    modifiers = engine.get_personalized_response_modifiers(user_id, {})
    print(f"\nResponse Modifiers:")
    print(f"Response Length: {modifiers['response_length']}")
    print(f"Conversation Style: {modifiers['conversation_style']}")
    print(f"Topic Preferences: {modifiers['topic_preferences']}")
    
    # Find similar users
    # Create another user for comparison
    user_id2 = "test_user2"
    for message, context in interactions[:3]:  # Partial interactions
        engine.update_preferences(user_id2, message, context)
    
    similar_users = engine.get_similar_users(user_id)
    print(f"\nSimilar Users: {similar_users}")
    
    print("\nPersonalization engine test completed!")
