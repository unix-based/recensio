"""
Chat Service - Handle AI user prototype conversations
"""

import uuid
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from pydantic_ai import Agent
from app.config import settings
from app.logger import get_module_logger
from app.prompts import get_chat_system_prompt, get_user_prototype_prompt

logger = get_module_logger(__name__)

class ChatMessage(BaseModel):
    """Chat message model"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: str

class UserPrototype(BaseModel):
    """AI-generated user prototype based on agent profile"""
    name: str
    emoji: str
    personality: str
    communication_style: str
    background: str
    interests: List[str]
    speaking_patterns: str
    response_tone: str

class ChatService:
    """Service for managing AI user prototype conversations"""
    
    def __init__(self):
        """Initialize chat service with Claude AI"""
        # Initialize Claude AI agent for chat (with fallback)
        self.ai_available = False
        try:
            logger.info(f"🔧 Checking AI configuration...")
            logger.info(f"🔑 API Key available: {bool(settings.anthropic_api_key)}")
            logger.info(f"🤖 Model: {settings.claude_model}")
            
            if settings.anthropic_api_key:
                logger.info("🤖 Initializing Claude AI agents...")
                self.chat_agent = Agent(
                    settings.claude_model,
                    system_prompt=get_chat_system_prompt()
                )
                
                # Initialize prototype generation agent
                self.prototype_agent = Agent(
                    settings.claude_model,
                    output_type=UserPrototype,
                    system_prompt=get_user_prototype_prompt()
                )
                self.ai_available = True
                logger.info("✅ Claude AI agents initialized successfully")
            else:
                self.ai_available = False
                logger.warning("⚠️ ANTHROPIC_API_KEY not available, using fallback responses")
        except Exception as e:
            self.ai_available = False
            logger.warning(f"⚠️ Failed to initialize AI agents: {e}, using fallback responses")
            logger.warning(f"📍 Exception type: {type(e).__name__}")
        
        # In-memory storage for conversations (in production, use Redis)
        self.conversations = {}
        self.agent_prototypes = {}
    
    async def get_agent_prototype(self, agent_id: int) -> Optional[Dict[str, Any]]:
        """Get or create AI prototype for an agent"""
        try:
            logger.info(f"👤 Getting prototype for agent {agent_id}")
            
            # Check if prototype already exists
            if agent_id in self.agent_prototypes:
                logger.info(f"✅ Found existing prototype for agent {agent_id}")
                return self.agent_prototypes[agent_id]
            
            # Generate new prototype based on agent profile
            logger.info(f"🤖 Generating new prototype for agent {agent_id}")
            
            # Get agent data (this would normally come from storage)
            # For now, we'll create a mock agent profile
            agent_profile = await self._get_agent_profile(agent_id)
            
            if self.ai_available:
                # Generate prototype using AI
                prototype_prompt = f"""
                Create a detailed user prototype based on this agent profile:
                
                Name: {agent_profile.get('name', 'Unknown')}
                Age: {agent_profile.get('age', 30)}
                Occupation: {agent_profile.get('occupation', 'Professional')}
                Review: {agent_profile.get('review', 'No review available')}
                Ratings: {agent_profile.get('ratings', {})}
                
                Create a realistic, human-like prototype that would naturally engage in conversations
                about the product they reviewed. Make them feel like a real person with genuine
                opinions, concerns, and communication patterns.
                """
                
                result = await self.prototype_agent.run(prototype_prompt)
                prototype = result.output
                
                # Store prototype
                prototype_dict = {
                    "name": prototype.name,
                    "emoji": prototype.emoji,
                    "personality": prototype.personality,
                    "communication_style": prototype.communication_style,
                    "background": prototype.background,
                    "interests": prototype.interests,
                    "speaking_patterns": prototype.speaking_patterns,
                    "response_tone": prototype.response_tone
                }
            else:
                # Fallback prototype generation
                prototype_dict = self._generate_fallback_prototype(agent_profile)
            
            self.agent_prototypes[agent_id] = prototype_dict
            logger.info(f"✅ Generated prototype for agent {agent_id}: {prototype_dict['name']}")
            
            return prototype_dict
            
        except Exception as e:
            logger.error(f"💥 Error generating prototype for agent {agent_id}: {str(e)}")
            return None
    
    async def start_conversation(self, agent_id: int) -> str:
        """Start a new conversation with an agent prototype"""
        try:
            logger.info(f"🚀 Starting conversation with agent {agent_id}")
            
            # Generate conversation ID
            conversation_id = str(uuid.uuid4())
            
            # Get agent prototype
            prototype = await self.get_agent_prototype(agent_id)
            if not prototype:
                raise ValueError(f"Could not create prototype for agent {agent_id}")
            
            # Initialize conversation
            conversation = {
                "conversation_id": conversation_id,
                "agent_id": agent_id,
                "agent_name": prototype["name"],
                "agent_emoji": prototype["emoji"],
                "messages": [],
                "created_at": datetime.now().isoformat()
            }
            
            self.conversations[conversation_id] = conversation
            logger.info(f"✅ Started conversation {conversation_id} with agent {agent_id}")
            
            return conversation_id
            
        except Exception as e:
            logger.error(f"💥 Error starting conversation with agent {agent_id}: {str(e)}")
            raise
    
    async def send_message(self, agent_id: int, message: str, 
                          conversation_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a message to an agent prototype and get response"""
        try:
            logger.info(f"💬 Sending message to agent {agent_id}: '{message[:50]}...'")
            
            # Get agent prototype
            prototype = await self.get_agent_prototype(agent_id)
            if not prototype:
                logger.error(f"❌ Could not get prototype for agent {agent_id}")
                raise ValueError(f"Could not get prototype for agent {agent_id}")
            
            logger.info(f"✅ Got prototype for agent {agent_id}: {prototype['name']}")
            
            # Create conversation context
            context = self._build_conversation_context(prototype, conversation_history or [])
            logger.info(f"📝 Built conversation context: {len(context)} chars")
            
            if self.ai_available:
                try:
                    logger.info("🤖 Generating AI response...")
                    # Generate response using Claude AI
                    chat_prompt = f"""
                    You are {prototype['name']}, a {prototype['personality']} person with the following characteristics:
                    
                    Communication Style: {prototype['communication_style']}
                    Background: {prototype['background']}
                    Interests: {', '.join(prototype['interests'])}
                    Speaking Patterns: {prototype['speaking_patterns']}
                    Response Tone: {prototype['response_tone']}
                    
                    Conversation Context:
                    {context}
                    
                    User's latest message: {message}
                    
                    Respond as {prototype['name']} would naturally respond. Be authentic to their personality,
                    background, and communication style. Keep responses conversational and human-like.
                    """
                    
                    result = await self.chat_agent.run(chat_prompt)
                    response_content = result.content
                    logger.info(f"✅ AI response generated: {len(response_content)} chars")
                except Exception as ai_error:
                    logger.error(f"❌ AI response generation failed: {ai_error}")
                    logger.info("🔄 Falling back to simple response...")
                    response_content = self._generate_fallback_response(prototype, message, context)
            else:
                logger.info("🔄 Using fallback response generation...")
                # Fallback response generation
                response_content = self._generate_fallback_response(prototype, message, context)
            
            logger.info(f"✅ Generated response for agent {agent_id}: '{response_content[:50]}...'")
            
            return {
                "message": response_content,
                "agent_name": prototype["name"],
                "agent_emoji": prototype["emoji"],
                "conversation_id": str(uuid.uuid4())  # Generate new conversation ID
            }
            
        except Exception as e:
            logger.error(f"💥 Error sending message to agent {agent_id}: {str(e)}")
            logger.error(f"📍 Exception type: {type(e).__name__}")
            
            # Try to get a basic prototype for fallback
            try:
                agent_profile = await self._get_agent_profile(agent_id)
                fallback_prototype = self._generate_fallback_prototype(agent_profile)
                fallback_response = self._generate_fallback_response(fallback_prototype, message, "")
                
                return {
                    "message": fallback_response,
                    "agent_name": fallback_prototype["name"],
                    "agent_emoji": fallback_prototype["emoji"],
                    "conversation_id": str(uuid.uuid4())
                }
            except Exception as fallback_error:
                logger.error(f"💥 Fallback also failed: {fallback_error}")
                # Ultimate fallback
                return {
                    "message": f"Thanks for reaching out! I'd love to chat about my experience with this product. What would you like to know?",
                    "agent_name": f"User {agent_id}",
                    "agent_emoji": "😊",
                    "conversation_id": str(uuid.uuid4())
                }
    
    async def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get full conversation history"""
        try:
            logger.info(f"📜 Retrieving conversation {conversation_id}")
            
            if conversation_id not in self.conversations:
                logger.warning(f"⚠️ Conversation {conversation_id} not found")
                return None
            
            conversation = self.conversations[conversation_id]
            logger.info(f"✅ Retrieved conversation {conversation_id}")
            
            return conversation
            
        except Exception as e:
            logger.error(f"💥 Error retrieving conversation {conversation_id}: {str(e)}")
            return None
    
    def _build_conversation_context(self, prototype: Dict[str, Any], 
                                  conversation_history: List[Dict[str, Any]]) -> str:
        """Build conversation context from history"""
        if not conversation_history:
            return "This is the start of the conversation."
        
        context_parts = []
        for msg in conversation_history[-10:]:  # Last 10 messages
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            context_parts.append(f"{role}: {content}")
        
        return "\n".join(context_parts)
    
    async def _get_agent_profile(self, agent_id: int) -> Dict[str, Any]:
        """Get agent profile data (mock implementation)"""
        # In a real implementation, this would query the storage
        # For now, return mock data based on agent_id
        mock_profiles = {
            1: {
                "id": 1,
                "name": "Sarah Chen",
                "age": 28,
                "occupation": "Product Manager",
                "review": "This tool has completely transformed how I manage my team's workflow. The interface is clean and intuitive, and it saves me hours every week. I especially love the collaboration features!",
                "ratings": {"overall": 92, "clarity": 95, "ux": 88, "valueProposition": 90}
            },
            2: {
                "id": 2,
                "name": "Marcus Johnson",
                "age": 35,
                "occupation": "Software Engineer",
                "review": "Solid product overall. The core functionality works well, but I'd like to see more customization options. The performance is good and it integrates nicely with our existing tools.",
                "ratings": {"overall": 78, "clarity": 82, "ux": 75, "valueProposition": 80}
            },
            3: {
                "id": 3,
                "name": "Emily Rodriguez",
                "age": 24,
                "occupation": "Marketing Specialist",
                "review": "I'm really impressed with this platform! It's helped me streamline our marketing campaigns significantly. The analytics are detailed and the user experience is smooth.",
                "ratings": {"overall": 88, "clarity": 90, "ux": 85, "valueProposition": 87}
            }
        }
        
        return mock_profiles.get(agent_id, {
            "id": agent_id,
            "name": f"User {agent_id}",
            "age": 30,
            "occupation": "Professional",
            "review": "This product is really helpful for my daily workflow. I love how intuitive it is!",
            "ratings": {"overall": 85, "clarity": 90, "ux": 80, "valueProposition": 85}
        })
    
    def _generate_fallback_prototype(self, agent_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a fallback prototype when AI is not available"""
        name = agent_profile.get('name', 'User')
        occupation = agent_profile.get('occupation', 'Professional')
        review = agent_profile.get('review', '')
        
        # Simple personality based on review sentiment
        if 'love' in review.lower() or 'amazing' in review.lower() or 'great' in review.lower():
            personality = "enthusiastic and positive"
            emoji = "😊"
        elif 'good' in review.lower() or 'solid' in review.lower():
            personality = "practical and balanced"
            emoji = "😐"
        else:
            personality = "thoughtful and analytical"
            emoji = "🤔"
        
        return {
            "name": name,
            "emoji": emoji,
            "personality": personality,
            "communication_style": "friendly and professional",
            "background": f"A {occupation.lower()} with experience in their field",
            "interests": ["technology", "productivity", "innovation"],
            "speaking_patterns": "clear and direct communication",
            "response_tone": "helpful and engaging"
        }
    
    def _generate_fallback_response(self, prototype: Dict[str, Any], message: str, context: str) -> str:
        """Generate a fallback response when AI is not available"""
        name = prototype['name']
        personality = prototype['personality']
        
        # More contextual and natural responses
        if '?' in message:
            return f"Great question! As someone who's used this product, I'd say it really depends on your specific needs. What are you most curious about?"
        elif 'help' in message.lower() or 'problem' in message.lower() or 'issue' in message.lower():
            return f"I understand your concern. When I was first using this product, I had similar questions. The key is to start with the basics and build from there."
        elif 'feature' in message.lower() or 'function' in message.lower() or 'capability' in message.lower():
            return f"That's one of the features I really appreciate! It's made a big difference in how I work. Have you tried it yet?"
        elif 'like' in message.lower() or 'love' in message.lower() or 'enjoy' in message.lower():
            return f"I'm glad you're interested! I found this product really helpful for my workflow. What specific aspect are you most curious about?"
        elif 'think' in message.lower() or 'opinion' in message.lower() or 'thought' in message.lower():
            return f"Based on my experience, I think this product has a lot of potential. It's definitely worth exploring further. What's your main use case?"
        elif 'good' in message.lower() or 'bad' in message.lower() or 'better' in message.lower():
            return f"I've had a positive experience overall. There are definitely some areas for improvement, but the core functionality works well. What's your take on it?"
        else:
            return f"Thanks for reaching out! I'm happy to share my experience with this product. What would you like to know more about?"
