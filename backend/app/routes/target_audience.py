"""
Target Audience Routes - API endpoints for AI-powered target audience generation
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.claude_service import ClaudeService, TargetAudienceProfile
from app.dependencies import get_claude_service
from app.logger import get_module_logger

logger = get_module_logger(__name__)

router = APIRouter()

class TargetAudienceRequest(BaseModel):
    """Request model for target audience generation"""
    website_url: str

class TargetAudienceResponse(BaseModel):
    """Response model for target audience generation"""
    success: bool
    data: dict
    reasoning: str

@router.post("/generate", response_model=TargetAudienceResponse)
async def generate_target_audience(
    request: TargetAudienceRequest,
    claude_service: ClaudeService = Depends(get_claude_service)
):
    """
    Generate target audience recommendations based on website analysis
    
    Args:
        request: TargetAudienceRequest with website_url
        claude_service: Claude service for AI analysis
        
    Returns:
        TargetAudienceResponse with generated recommendations
    """
    try:
        logger.info(f"🚀 [API] Starting target audience generation for website: {request.website_url}")
        
        # Claude service is injected via dependency injection
        logger.info("🔧 [API] Claude service ready via dependency injection")
        
        # Analyze website and generate target audience profile
        logger.info(f"🤖 [API] Calling Claude service to analyze website: {request.website_url}")
        profile: TargetAudienceProfile = await claude_service.analyze_website_for_target_audience(
            request.website_url
        )
        
        logger.info(f"✅ [API] Claude analysis completed successfully")
        logger.info(f"📊 [API] Generated profile: Age {profile.age_range}, Gender: {profile.gender}, Occupation: {profile.occupation[:50]}...")
        
        # Convert to frontend-compatible format
        response_data = profile.to_frontend_format()
        logger.info(f"🔄 [API] Converted to frontend format: {response_data}")
        
        logger.info(f"🎉 [API] Successfully generated target audience for {request.website_url}")
        
        return TargetAudienceResponse(
            success=True,
            data=response_data,
            reasoning=profile.reasoning
        )
        
    except Exception as e:
        logger.error(f"💥 [API] Error generating target audience for {request.website_url}: {str(e)}")
        logger.error(f"📍 [API] Exception type: {type(e).__name__}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate target audience: {str(e)}"
        )

@router.get("/health")
async def health_check(claude_service: ClaudeService = Depends(get_claude_service)):
    """Health check endpoint for target audience service"""
    try:
        # Basic check to ensure Claude service can be initialized
        return {
            "status": "healthy",
            "service": "target_audience",
            "claude_configured": True
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "target_audience", 
            "error": str(e),
            "claude_configured": False
        }