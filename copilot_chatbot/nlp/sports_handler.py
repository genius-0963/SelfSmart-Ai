"""
Intelligent AI Backend - Sports Conversation Handler
Production-grade OOP implementation for sports discussions with deep football knowledge
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class SportType(Enum):
    """Enumeration of supported sports"""
    FOOTBALL = "football"
    SOCCER = "soccer"
    BASKETBALL = "basketball"
    TENNIS = "tennis"
    CRICKET = "cricket"
    BASEBALL = "baseball"


class ConversationTopic(Enum):
    """Enumeration of sports conversation topics"""
    MATCH_ANALYSIS = "match_analysis"
    PLAYER_PERFORMANCE = "player_performance"
    TRANSFER_NEWS = "transfer_news"
    TACTICS = "tactics"
    LEAGUE_STANDINGS = "league_standings"
    TOURNAMENTS = "tournaments"
    HISTORICAL = "historical"
    PREDICTIONS = "predictions"


@dataclass
class SportsContext:
    """Data class for sports conversation context"""
    sport_type: SportType
    topic: ConversationTopic
    entities: Dict[str, Any]
    user_preferences: Dict[str, Any]
    conversation_history: List[Dict[str, str]]


class SportsKnowledgeBase:
    """Comprehensive sports knowledge base with focus on football"""
    
    def __init__(self):
        self.football_data = self._initialize_football_knowledge()
        self.basketball_data = self._initialize_basketball_knowledge()
        self.general_sports_data = self._initialize_general_sports_knowledge()
        logger.info("Sports Knowledge Base initialized")
    
    def _initialize_football_knowledge(self) -> Dict[str, Any]:
        """Initialize comprehensive football knowledge"""
        return {
            'leagues': {
                'premier_league': {
                    'name': 'Premier League',
                    'country': 'England',
                    'teams': ['Manchester City', 'Arsenal', 'Liverpool', 'Chelsea', 'Manchester United', 'Newcastle', 'Brighton', 'Tottenham'],
                    'top_scorers': ['Erling Haaland', 'Harry Kane', 'Mohamed Salah', 'Son Heung-min'],
                    'founded': 1992,
                    'description': 'The most competitive and popular football league in the world'
                },
                'la_liga': {
                    'name': 'La Liga',
                    'country': 'Spain',
                    'teams': ['Real Madrid', 'Barcelona', 'Atletico Madrid', 'Sevilla', 'Real Betis', 'Villarreal'],
                    'top_scorers': ['Robert Lewandowski', 'Karim Benzema', 'Vinícius Júnior', 'Jude Bellingham'],
                    'founded': 1929,
                    'description': 'Home to technical football and legendary clubs like Real Madrid and Barcelona'
                },
                'champions_league': {
                    'name': 'UEFA Champions League',
                    'type': 'International Club Competition',
                    'current_champion': 'Manchester City',
                    'most_successful': ['Real Madrid', 'AC Milan', 'Liverpool', 'Bayern Munich'],
                    'description': 'The most prestigious club competition in world football'
                }
            },
            'teams': {
                'real_madrid': {
                    'full_name': 'Real Madrid CF',
                    'stadium': 'Santiago Bernabéu',
                    'city': 'Madrid',
                    'legendary_players': ['Cristiano Ronaldo', 'Zinedine Zidane', 'Alfredo Di Stéfano', 'Raúl'],
                    'current_stars': ['Jude Bellingham', 'Vinícius Júnior', 'Rodrygo'],
                    'achievements': '14-time Champions League winners',
                    'playing_style': 'Possession-based attacking football'
                },
                'barcelona': {
                    'full_name': 'FC Barcelona',
                    'stadium': 'Camp Nou',
                    'city': 'Barcelona',
                    'legendary_players': ['Lionel Messi', 'Xavi', 'Andrés Iniesta', 'Ronaldinho'],
                    'current_stars': ['Robert Lewandowski', 'Pedri', 'Gavi'],
                    'achievements': 'Multiple Champions League and La Liga titles',
                    'playing_style': 'Tiki-taka possession football'
                },
                'manchester_city': {
                    'full_name': 'Manchester City FC',
                    'stadium': 'Etihad Stadium',
                    'city': 'Manchester',
                    'legendary_players': ['Sergio Agüero', 'David Silva', 'Yaya Touré'],
                    'current_stars': ['Erling Haaland', 'Kevin De Bruyne', 'Phil Foden'],
                    'achievements': 'Recent Premier League dominance, Champions League winners',
                    'playing_style': 'High-pressing, possession-based, tactical flexibility'
                }
            },
            'players': {
                'messi': {
                    'full_name': 'Lionel Andrés Messi',
                    'nationality': 'Argentinian',
                    'position': 'Forward',
                    'current_club': 'Inter Miami',
                    'former_clubs': ['Barcelona', 'PSG'],
                    'achievements': ['8 Ballon d\'Or awards', 'World Cup winner', 'Champions League winner'],
                    'playing_style': 'Dribbling, vision, goal scoring, playmaking'
                },
                'ronaldo': {
                    'full_name': 'Cristiano Ronaldo dos Santos Aveiro',
                    'nationality': 'Portuguese',
                    'position': 'Forward',
                    'current_club': 'Al Nassr',
                    'former_clubs': ['Real Madrid', 'Manchester United', 'Juventus'],
                    'achievements': ['5 Ballon d\'Or awards', 'Champions League winner with multiple clubs', 'Euro 2016 winner'],
                    'playing_style': 'Athleticism, goal scoring, leadership, aerial ability'
                },
                'haaland': {
                    'full_name': 'Erling Braut Haaland',
                    'nationality': 'Norwegian',
                    'position': 'Striker',
                    'current_club': 'Manchester City',
                    'achievements': ['Premier League Golden Boot', 'Champions League winner', 'Multiple league titles'],
                    'playing_style': 'Physical presence, clinical finishing, movement off the ball'
                }
            },
            'tactics': {
                'formations': {
                    '4_3_3': {
                        'description': 'Four defenders, three midfielders, three attackers',
                        'strengths': ['Attacking width', 'Midfield control', 'High pressing'],
                        'famous_users': ['Barcelona (Guardiola)', 'Liverpool (Klopp)', 'Manchester City (Pep)'],
                        'best_for': 'Teams with creative wingers and attacking full-backs'
                    },
                    '4_2_3_1': {
                        'description': 'Four defenders, two defensive midfielders, three attacking midfielders, one striker',
                        'strengths': ['Defensive stability', 'Attacking flexibility', 'Midfield balance'],
                        'famous_users': ['Real Madrid (Ancelotti)', 'Germany (Low)', 'Chelsea (Tuchel)'],
                        'best_for': 'Teams with strong number 10 and defensive midfielders'
                    },
                    '3_5_2': {
                        'description': 'Three center-backs, five midfielders, two strikers',
                        'strengths': ['Central dominance', 'Wing-back attacks', 'Numerical superiority in midfield'],
                        'famous_users': ['Inter Milan (Conte)', 'Bayern Munich (Nagelsmann)', 'Italy (Mancini)'],
                        'best_for': 'Teams with versatile wing-backs and strong center-backs'
                    }
                },
                'playing_styles': {
                    'tika_taka': {
                        'description': 'Short passing, movement, and maintaining possession',
                        'origin': 'Johan Cruyff, perfected by Barcelona',
                        'key_principles': ['One-touch passing', 'Positional play', 'High defensive line'],
                        'famous_practitioners': ['Barcelona (Guardiola)', 'Spain (2008-2012)']
                    },
                    'gegenpressing': {
                        'description': 'Immediate counter-pressing after losing possession',
                        'origin': 'Jürgen Klopp',
                        'key_principles': ['Win ball back quickly', 'High intensity', 'Tactical fouling'],
                        'famous_practitioners': ['Liverpool (Klopp)', 'RB Leipzig (Rangnick)']
                    }
                }
            },
            'tournaments': {
                'world_cup': {
                    'frequency': 'Every 4 years',
                    'current_champion': 'Argentina',
                    'most_successful': ['Brazil (5 titles)', 'Germany (4 titles)', 'Italy (4 titles)'],
                    'description': 'The biggest football tournament in the world'
                },
                'euros': {
                    'frequency': 'Every 4 years',
                    'current_champion': 'Italy',
                    'most_successful': ['Germany (3 titles)', 'Spain (3 titles)'],
                    'description': 'European Championship, second most prestigious international tournament'
                }
            }
        }
    
    def _initialize_basketball_knowledge(self) -> Dict[str, Any]:
        """Initialize basketball knowledge"""
        return {
            'leagues': {
                'nba': {
                    'name': 'National Basketball Association',
                    'teams': ['Lakers', 'Warriors', 'Celtics', 'Heat', 'Nets', 'Bucks'],
                    'current_champion': 'Denver Nuggets',
                    'legendary_players': ['Michael Jordan', 'LeBron James', 'Kobe Bryant', 'Stephen Curry']
                }
            }
        }
    
    def _initialize_general_sports_knowledge(self) -> Dict[str, Any]:
        """Initialize general sports knowledge"""
        return {
            'topics': [
                'match analysis', 'player performance', 'transfer news', 'tactics',
                'league standings', 'tournaments', 'historical moments', 'predictions'
            ]
        }
    
    def get_team_info(self, team_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific team"""
        team_key = team_name.lower().replace(' ', '_')
        return self.football_data['teams'].get(team_key)
    
    def get_player_info(self, player_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific player"""
        player_key = player_name.lower().replace(' ', '_')
        return self.football_data['players'].get(player_key)
    
    def get_league_info(self, league_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific league"""
        league_key = league_name.lower().replace(' ', '_')
        return self.football_data['leagues'].get(league_key)


class SportsConversationHandler:
    """Handler for sports conversations with deep domain knowledge"""
    
    def __init__(self):
        self.knowledge_base = SportsKnowledgeBase()
        self.conversation_topics = self._initialize_conversation_topics()
        self.response_templates = self._initialize_response_templates()
        logger.info("Sports Conversation Handler initialized")
    
    def _initialize_conversation_topics(self) -> Dict[ConversationTopic, List[str]]:
        """Initialize conversation topic keywords"""
        return {
            ConversationTopic.MATCH_ANALYSIS: ['match', 'game', 'score', 'result', 'performance', 'played'],
            ConversationTopic.PLAYER_PERFORMANCE: ['player', 'goal', 'assist', 'performance', 'form', 'stats'],
            ConversationTopic.TRANSFER_NEWS: ['transfer', 'signing', 'deal', 'contract', 'move', 'rumor'],
            ConversationTopic.TACTICS: ['tactics', 'formation', 'strategy', 'style', 'system', 'approach'],
            ConversationTopic.LEAGUE_STANDINGS: ['league', 'table', 'standing', 'position', 'points', 'rank'],
            ConversationTopic.TOURNAMENTS: ['tournament', 'cup', 'championship', 'trophy', 'final', 'knockout'],
            ConversationTopic.HISTORICAL: ['history', 'legend', 'past', 'record', 'achievement', 'memorable'],
            ConversationTopic.PREDICTIONS: ['predict', 'future', 'chance', 'will', 'expect', 'forecast']
        }
    
    def _initialize_response_templates(self) -> Dict[str, str]:
        """Initialize response templates for different scenarios"""
        return {
            'team_discussion': "Great choice talking about {team}! {team_info} What specifically interests you about them?",
            'player_discussion': "Excellent question about {player}! {player_info} What aspect of their game fascinates you most?",
            'match_analysis': "Match analysis is fascinating! When analyzing games, I look at {factors}. Which match are you thinking about?",
            'tactical_discussion': "Tactics are the chess of football! {tactical_info} What formation or style do you find most interesting?",
            'league_discussion': "The {league} is incredible! {league_info} What's your take on the current season?",
            'general_football': "Football is the beautiful game! {general_info} What aspect would you like to explore?"
        }
    
    def handle_sports_conversation(self, user_input: str, context: Optional[SportsContext] = None) -> Dict[str, Any]:
        """Handle sports conversation with intelligent responses"""
        try:
            # Extract entities and determine topic
            entities = self._extract_sports_entities(user_input)
            topic = self._determine_conversation_topic(user_input)
            
            # Generate contextual response
            response = self._generate_sports_response(user_input, entities, topic, context)
            
            # Update context
            updated_context = self._update_context(context, user_input, entities, topic)
            
            return {
                'response': response,
                'context': updated_context,
                'entities': entities,
                'topic': topic.value,
                'follow_up_questions': self._generate_follow_up_questions(entities, topic)
            }
            
        except Exception as e:
            logger.error(f"Error handling sports conversation: {str(e)}")
            return self._generate_fallback_response()
    
    def _extract_sports_entities(self, text: str) -> Dict[str, Any]:
        """Extract sports-related entities from text"""
        entities = {}
        text_lower = text.lower()
        
        # Check for team mentions
        for team_key in self.knowledge_base.football_data['teams']:
            team_name = team_key.replace('_', ' ')
            if team_name in text_lower or team_key.replace('_', ' ') in text_lower:
                entities['team'] = team_name
                break
        
        # Check for player mentions
        for player_key in self.knowledge_base.football_data['players']:
            player_name = player_key.replace('_', ' ')
            if player_name in text_lower:
                entities['player'] = player_name
                break
        
        # Check for league mentions
        for league_key in self.knowledge_base.football_data['leagues']:
            league_name = league_key.replace('_', ' ')
            if league_name in text_lower:
                entities['league'] = league_name
                break
        
        # Check for sport type
        if any(sport in text_lower for sport in ['football', 'soccer']):
            entities['sport'] = 'football'
        elif 'basketball' in text_lower:
            entities['sport'] = 'basketball'
        
        return entities
    
    def _determine_conversation_topic(self, text: str) -> ConversationTopic:
        """Determine the conversation topic from text"""
        text_lower = text.lower()
        
        for topic, keywords in self.conversation_topics.items():
            if any(keyword in text_lower for keyword in keywords):
                return topic
        
        return ConversationTopic.MATCH_ANALYSIS  # Default topic
    
    def _generate_sports_response(self, user_input: str, entities: Dict[str, Any], 
                                topic: ConversationTopic, context: Optional[SportsContext]) -> str:
        """Generate intelligent sports response"""
        
        # Team-specific response
        if 'team' in entities:
            team_info = self.knowledge_base.get_team_info(entities['team'])
            if team_info:
                return self._generate_team_response(entities['team'], team_info, topic)
        
        # Player-specific response
        if 'player' in entities:
            player_info = self.knowledge_base.get_player_info(entities['player'])
            if player_info:
                return self._generate_player_response(entities['player'], player_info, topic)
        
        # League-specific response
        if 'league' in entities:
            league_info = self.knowledge_base.get_league_info(entities['league'])
            if league_info:
                return self._generate_league_response(entities['league'], league_info, topic)
        
        # Topic-specific response
        return self._generate_topic_response(topic, entities)
    
    def _generate_team_response(self, team_name: str, team_info: Dict[str, Any], topic: ConversationTopic) -> str:
        """Generate team-specific response"""
        full_name = team_info.get('full_name', team_name.title())
        stadium = team_info.get('stadium', 'their home ground')
        achievements = team_info.get('achievements', 'successful history')
        playing_style = team_info.get('playing_style', 'unique style')
        
        response = f"{full_name} is a fantastic club! Based at {stadium}, they have a {achievements}. "
        response += f"Their {playing_style} makes them exciting to watch. "
        
        if topic == ConversationTopic.MATCH_ANALYSIS:
            response += "When analyzing their matches, I look at their tactical setup, key player performances, and how they adapt to different opponents."
        elif topic == ConversationTopic.PLAYER_PERFORMANCE:
            response += "Their current stars and legendary players have created a rich footballing legacy."
        elif topic == ConversationTopic.TACTICS:
            response += f"Their tactical approach emphasizes {playing_style}."
        
        response += " What aspect of their play interests you most?"
        return response
    
    def _generate_player_response(self, player_name: str, player_info: Dict[str, Any], topic: ConversationTopic) -> str:
        """Generate player-specific response"""
        full_name = player_info.get('full_name', player_name.title())
        nationality = player_info.get('nationality', 'international')
        position = player_info.get('position', 'player')
        achievements = player_info.get('achievements', [])
        playing_style = player_info.get('playing_style', 'unique style')
        
        response = f"{full_name} is an incredible {nationality} {position}! "
        response += f"Known for their {playing_style}, they've achieved {', '.join(achievements[:2])}. "
        
        if topic == ConversationTopic.MATCH_ANALYSIS:
            response += "In match analysis, their impact goes beyond stats - they change games through moments of brilliance."
        elif topic == ConversationTopic.PLAYER_PERFORMANCE:
            response += f"Their performance metrics show consistency in {playing_style.split(', ')[0]}."
        
        response += " What about their game fascinates you the most?"
        return response
    
    def _generate_league_response(self, league_name: str, league_info: Dict[str, Any], topic: ConversationTopic) -> str:
        """Generate league-specific response"""
        name = league_info.get('name', league_name.title())
        description = league_info.get('description', 'exciting competition')
        
        response = f"The {name} is {description}! "
        
        if 'teams' in league_info:
            response += f"With teams like {', '.join(league_info['teams'][:4])}, the competition is always intense. "
        
        if topic == ConversationTopic.LEAGUE_STANDINGS:
            response += "The league table tells stories of consistency, surprises, and the relentless pursuit of excellence."
        elif topic == ConversationTopic.MATCH_ANALYSIS:
            response += "Every match weekend brings tactical battles and individual brilliance."
        
        response += " What's your take on the current season?"
        return response
    
    def _generate_topic_response(self, topic: ConversationTopic, entities: Dict[str, Any]) -> str:
        """Generate topic-specific response"""
        if topic == ConversationTopic.TACTICS:
            return """Tactics are the beautiful chess match of football! From Guardiola's tiki-taka to Klopp's gegenpressing, 
            each system has its philosophy. I love discussing formations like 4-3-3, 4-2-3-1, or 3-5-2. 
            What tactical approach interests you most?"""
        
        elif topic == ConversationTopic.TRANSFER_NEWS:
            return """Transfer windows are always exciting! The business of football combines strategy, finance, and player development. 
            From blockbuster signings to youth academy promotions, each transfer tells a story. 
            Any transfer news or rumors you're following?"""
        
        elif topic == ConversationTopic.PREDICTIONS:
            return """Football predictions blend analysis, intuition, and understanding of form. While nothing's certain, 
            we can analyze team dynamics, player fitness, and tactical matchups. 
            What match or situation are you thinking about?"""
        
        else:
            return """Football is absolutely incredible! The combination of skill, passion, and strategy makes it the world's most beautiful game. 
            I can discuss tactics, players, teams, leagues, or any aspect that interests you. 
            What would you like to explore?"""
    
    def _generate_follow_up_questions(self, entities: Dict[str, Any], topic: ConversationTopic) -> List[str]:
        """Generate relevant follow-up questions"""
        base_questions = [
            "What's your favorite team?",
            "Which player do you admire most?",
            "Do you prefer attacking or tactical football?",
            "What's the best match you've ever watched?"
        ]
        
        # Contextual questions based on entities
        if 'team' in entities:
            base_questions.insert(0, f"What do you think about {entities['team']}'s current form?")
        
        if 'player' in entities:
            base_questions.insert(0, f"How do you rate {entities['player']}'s performance this season?")
        
        if topic == ConversationTopic.TACTICS:
            base_questions.append("Which formation do you think is most effective?")
        elif topic == ConversationTopic.TRANSFER_NEWS:
            base_questions.append("Any transfers you're excited about?")
        
        return base_questions[:4]
    
    def _update_context(self, context: Optional[SportsContext], user_input: str, 
                       entities: Dict[str, Any], topic: ConversationTopic) -> SportsContext:
        """Update conversation context"""
        if context is None:
            return SportsContext(
                sport_type=SportType.FOOTBALL,
                topic=topic,
                entities=entities,
                user_preferences={},
                conversation_history=[{'user': user_input, 'timestamp': str(datetime.now())}]
            )
        
        context.entities.update(entities)
        context.topic = topic
        context.conversation_history.append({'user': user_input, 'timestamp': str(datetime.now())})
        
        return context
    
    def _generate_fallback_response(self) -> Dict[str, Any]:
        """Generate fallback response for errors"""
        return {
            'response': "I love discussing sports! Whether it's football tactics, player performances, or match analysis, I'm here to talk. What sports topic interests you?",
            'context': None,
            'entities': {},
            'topic': ConversationTopic.MATCH_ANALYSIS.value,
            'follow_up_questions': ["What's your favorite sport?", "Which team do you support?"]
        }


# Factory function for easy instantiation
def create_sports_handler() -> SportsConversationHandler:
    """Factory function to create sports conversation handler"""
    return SportsConversationHandler()


if __name__ == "__main__":
    # Test the sports conversation handler
    handler = create_sports_handler()
    
    test_inputs = [
        "Tell me about Real Madrid",
        "What do you think about Messi?",
        "Premier League is amazing",
        "I love tactical football",
        "Football is the best sport"
    ]
    
    print("=== Sports Conversation Handler Test ===")
    for test_input in test_inputs:
        result = handler.handle_sports_conversation(test_input)
        print(f"Input: '{test_input}'")
        print(f"Response: {result['response']}")
        print(f"Topic: {result['topic']}")
        print(f"Entities: {result['entities']}")
        print("-" * 50)
