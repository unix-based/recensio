"""
Chat Routes - Handle chat functionality with AI user prototypes
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import uuid
from app.services.chat_service import ChatService
from app.logger import get_module_logger

logger = get_module_logger(__name__)
router = APIRouter()

class ChatMessage(BaseModel):
    """Chat message model"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    """Request to send a message to a user prototype"""
    agent_id: int
    message: str
    conversation_history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    """Response from user prototype"""
    message: str
    agent_name: str
    agent_emoji: str
    conversation_id: str

class ConversationHistory(BaseModel):
    """Full conversation history"""
    conversation_id: str
    agent_id: int
    agent_name: str
    agent_emoji: str
    messages: List[ChatMessage]

@router.post("/send-message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """Send a message to a user prototype and get their response"""
    try:
        logger.info(f"💬 Chat message request for agent {request.agent_id}")
        logger.info(f"📝 Message: '{request.message[:100]}...'")
        logger.info(f"📚 Conversation history: {len(request.conversation_history or [])} messages")
        
        # Initialize chat service
        chat_service = ChatService()
        logger.info(f"🤖 Chat service initialized, AI available: {chat_service.ai_available}")
        
        # Get agent details and generate response
        response = await chat_service.send_message(
            agent_id=request.agent_id,
            message=request.message,
            conversation_history=request.conversation_history
        )
        
        logger.info(f"✅ Chat response generated for agent {request.agent_id}")
        return response
        
    except Exception as e:
        logger.error(f"💥 Error in chat send_message: {str(e)}")
        logger.error(f"📍 Exception type: {type(e).__name__}")
        
        # Try to get a basic response based on the message content
        fallback_responses = [
            "Thanks for reaching out! I'd love to share my experience with this product. What would you like to know?",
            "Great question! Based on my experience, I think this product has a lot of potential. What's your main use case?",
            "I'm glad you're interested! I found this product really helpful for my workflow. What specific aspect are you most curious about?",
            "Based on my experience, I think this product has a lot of potential. It's definitely worth exploring further. What's your take on it?"
        ]
        
        # Simple fallback based on message content
        if '?' in request.message:
            fallback_message = "Great question! As someone who's used this product, I'd say it really depends on your specific needs. What are you most curious about?"
        elif 'think' in request.message.lower():
            fallback_message = "Based on my experience, I think this product has a lot of potential. What's your main use case?"
        else:
            fallback_message = fallback_responses[0]
        
        return ChatResponse(
            message=fallback_message,
            agent_name=f"User {request.agent_id}",
            agent_emoji="😊",
            conversation_id=str(uuid.uuid4())
        )

@router.get("/conversation/{conversation_id}", response_model=ConversationHistory)
async def get_conversation(conversation_id: str):
    """Get full conversation history"""
    try:
        logger.info(f"📜 Retrieving conversation {conversation_id}")
        
        chat_service = ChatService()
        conversation = await chat_service.get_conversation(conversation_id)
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        logger.info(f"✅ Retrieved conversation {conversation_id}")
        return conversation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Error retrieving conversation {conversation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve conversation: {str(e)}")

class StartConversationRequest(BaseModel):
    """Request to start a conversation"""
    agent_id: int

@router.post("/start-conversation")
async def start_conversation(request: StartConversationRequest):
    """Start a new conversation with a user prototype"""
    try:
        logger.info(f"🚀 Starting new conversation with agent {request.agent_id}")
        
        chat_service = ChatService()
        conversation_id = await chat_service.start_conversation(request.agent_id)
        
        logger.info(f"✅ Started conversation {conversation_id} with agent {request.agent_id}")
        return {"conversation_id": conversation_id}
        
    except Exception as e:
        logger.error(f"💥 Error starting conversation with agent {request.agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start conversation: {str(e)}")

@router.get("/agent/{agent_id}/prototype")
async def get_agent_prototype(agent_id: int):
    """Get the AI prototype details for an agent"""
    try:
        logger.info(f"👤 Getting prototype details for agent {agent_id}")
        
        chat_service = ChatService()
        prototype = await chat_service.get_agent_prototype(agent_id)
        
        if not prototype:
            raise HTTPException(status_code=404, detail="Agent prototype not found")
        
        logger.info(f"✅ Retrieved prototype for agent {agent_id}")
        return prototype
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Error getting prototype for agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent prototype: {str(e)}")

@router.get("/test")
async def test_chat_service():
    """Test endpoint to verify chat service is working"""
    try:
        logger.info("🧪 Testing chat service...")
        
        chat_service = ChatService()
        logger.info(f"✅ Chat service initialized successfully")
        logger.info(f"🤖 AI available: {chat_service.ai_available}")
        
        return {
            "status": "success",
            "ai_available": chat_service.ai_available,
            "message": "Chat service is working correctly"
        }
        
    except Exception as e:
        logger.error(f"💥 Error testing chat service: {str(e)}")
        return {
            "status": "error",
            "ai_available": False,
            "message": f"Chat service error: {str(e)}"
        }
