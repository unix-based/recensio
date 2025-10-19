"""
Claude AI Service - Integration with Anthropic's Claude AI for target audience analysis
"""

from typing import Optional, Tuple, Dict, Any
from pydantic import BaseModel, Field, validator
from pydantic_ai import Agent
from app.config import settings
from app.services.cache_service import CacheService
from app.services.site_storage_service import SiteStorageService
from app.prompts import get_target_audience_system_prompt, get_website_analysis_prompt
from app.logger import get_module_logger

logger = get_module_logger(__name__)

class TargetAudienceProfile(BaseModel):
    """AI-generated target audience profile for website analysis.
    
    Contains demographic and psychographic characteristics
    of the ideal target audience for a given website.
    """
    age_range: Tuple[int, int] = Field(..., description="Age range as (min_age, max_age)")
    gender: str = Field(..., description="Target gender: male, female, or any")
    occupation: str = Field(..., description="Target occupation description")
    life_views: str = Field(..., description="Life views: progressive, moderate, or conservative")
    innovation_attitude: str = Field(..., description="Innovation attitude: conservative, moderate, or innovator")
    risk_tolerance: int = Field(..., ge=1, le=10, description="Risk tolerance level 1-10")
    gullibility: int = Field(..., ge=1, le=10, description="Gullibility level 1-10")
    reasoning: str = Field(..., description="Reasoning for these parameters")
    
    @validator('age_range')
    def validate_age_range(cls, v: Tuple[int, int]) -> Tuple[int, int]:
        """Validate age range is reasonable and properly formatted."""
        if len(v) != 2 or v[0] >= v[1] or v[0] < 18 or v[1] > 80:
            raise ValueError('Age range must be (min, max) with 18 <= min < max <= 80')
        return v
    
    @validator('gender')
    def validate_gender(cls, v: str) -> str:
        """Validate gender is one of the accepted values."""
        if v.lower() not in ['male', 'female', 'any']:
            raise ValueError('Gender must be one of: male, female, any')
        return v.lower()
    
    @validator('life_views')
    def validate_life_views(cls, v: str) -> str:
        """Validate life views is one of the accepted values."""
        if v.lower() not in ['progressive', 'moderate', 'conservative']:
            raise ValueError('Life views must be one of: progressive, moderate, conservative')
        return v.lower()
    
    @validator('innovation_attitude')
    def validate_innovation_attitude(cls, v: str) -> str:
        """Validate innovation attitude is one of the accepted values."""
        if v.lower() not in ['conservative', 'moderate', 'innovator']:
            raise ValueError('Innovation attitude must be one of: conservative, moderate, innovator')
        return v.lower()

    def to_frontend_format(self) -> Dict[str, Any]:
        """Convert to frontend-compatible dictionary format.
        
        Returns:
            Dictionary with keys matching frontend expectations
        """
        return {
            "ageRange": list(self.age_range),
            "gender": self.gender,
            "occupation": self.occupation,
            "lifeViews": self.life_views,
            "innovationAttitude": self.innovation_attitude,
            "riskTolerance": self.risk_tolerance,
            "gullibility": self.gullibility,
            "reasoning": self.reasoning
        }

class WebsiteAnalysisContext(BaseModel):
    """Context for website analysis"""
    url: str
    content: str

class ClaudeService:
    """Service for interacting with Claude AI to generate target audience profiles.
    
    Uses Anthropic's Claude AI to analyze websites and generate
    realistic target audience recommendations.
    """
    
    def __init__(self, site_storage: SiteStorageService) -> None:
        """Initialize Claude service with API key and site storage.
        
        Args:
            site_storage: Site storage service for website content retrieval
            
        Raises:
            ValueError: If ANTHROPIC_API_KEY is not configured
        """
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for Claude AI integration")
        
        self.cache_service = CacheService()
        self.site_storage = site_storage
        self.agent = Agent(
            settings.claude_model,
            output_type=TargetAudienceProfile,
            system_prompt=get_target_audience_system_prompt()
        )
    
    async def analyze_website_for_target_audience(self, website_url: str) -> TargetAudienceProfile:
        """
        Analyze a website and generate target audience recommendations
        
        Args:
            website_url: The URL of the website to analyze
            
        Returns:
            TargetAudienceProfile object with recommendations
        """
        try:
            logger.info(f"🌐 [CLAUDE] Starting website analysis for: {website_url}")
            
            # Get website content
            logger.info(f"📄 [CLAUDE] Retrieving website content...")
            website_content = await self._get_website_content(website_url)
            
            if not website_content:
                logger.warning(f"⚠️ [CLAUDE] Could not retrieve content for {website_url}, using default profile")
                return self._get_default_target_audience()
            
            logger.info(f"✅ [CLAUDE] Retrieved {len(website_content)} characters of content")
            
            # Create analysis context
            context = WebsiteAnalysisContext(url=website_url, content=website_content[:4000])
            logger.info(f"🔧 [CLAUDE] Created analysis context with {len(context.content)} characters")
            
            # Use Pydantic AI agent to analyze and get structured response
            prompt = get_website_analysis_prompt(website_url, context.content)
            logger.info(f"📝 [CLAUDE] Created analysis prompt (length: {len(prompt)} chars)")
            
            logger.info(f"🤖 [CLAUDE] Sending request to Claude AI...")
            result = await self.agent.run(prompt)
            
            logger.info(f"✅ [CLAUDE] Claude AI analysis completed successfully")
            
            # Fix: The AgentRunResult object provides model output on .output, not .data
            profile = result.output
            logger.info(f"📊 [CLAUDE] Result: {profile.age_range}, {profile.gender}, {profile.occupation[:30]}...")
            logger.info(f"💭 [CLAUDE] Reasoning: {profile.reasoning[:100]}...")
            
            return profile
            
        except Exception as e:
            logger.error(f"💥 [CLAUDE] Error analyzing website {website_url}: {str(e)}")
            logger.error(f"📍 [CLAUDE] Exception type: {type(e).__name__}")
            logger.info("🔄 [CLAUDE] Returning default target audience profile")
            return self._get_default_target_audience()
    
    async def _get_website_content(self, website_url: str) -> Optional[str]:
        """
        Retrieve website content for analysis
        
        Args:
            website_url: The URL to retrieve content from
            
        Returns:
            Website content as string, or None if retrieval fails
        """
        try:
            logger.info(f"🔍 [CLAUDE] Looking up website content in site storage for: {website_url}")
            
            # Try to get content from site storage first
            content = self.site_storage.get_combined_content_for_url(website_url)
            
            if content:
                logger.info(f"✅ [CLAUDE] Found content in site storage ({len(content)} chars)")
                return content
            
            # If not available, try to fetch content directly
            logger.warning(f"⚠️ [CLAUDE] Website content not found in storage for {website_url}")
            logger.info("🔄 [CLAUDE] Attempting to fetch content directly...")
            
            # Import here to avoid circular imports
            from app.services.link_verification_service import LinkVerificationService
            
            link_service = LinkVerificationService()
            
            # Extract main page content directly
            main_content = await link_service.extract_page_content(website_url)
            if main_content and main_content.text:
                logger.info(f"✅ [CLAUDE] Successfully fetched content directly ({len(main_content.text)} chars)")
                return main_content.text
            else:
                logger.warning(f"⚠️ [CLAUDE] Could not fetch content directly for {website_url}")
                return None
            
        except Exception as e:
            logger.error(f"💥 [CLAUDE] Error retrieving website content for {website_url}: {str(e)}")
            return None
    
    
    def _get_default_target_audience(self) -> TargetAudienceProfile:
        """
        Return a default target audience configuration when analysis fails
        
        Returns:
            Default TargetAudienceProfile
        """
        logger.info("🔧 [CLAUDE] Creating default target audience profile")
        
        default_profile = TargetAudienceProfile(
            age_range=(25, 45),
            gender="any",
            occupation="Technology professionals, entrepreneurs, and early adopters interested in digital solutions",
            life_views="moderate",
            innovation_attitude="moderate",
            risk_tolerance=6,
            gullibility=4,
            reasoning="Default configuration used when website analysis is unavailable. Targets tech-savvy professionals who are comfortable with digital tools and moderate risk-taking."
        )
        
        logger.info(f"✅ [CLAUDE] Created default profile: {default_profile.age_range}, {default_profile.gender}, {default_profile.occupation[:50]}...")
        return default_profile