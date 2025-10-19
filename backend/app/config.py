"""
Configuration management for the application

This module reads configuration from a .env file in the backend directory.
Create a .env file based on config.env.template to configure the application.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
# The .env file should be created in the backend directory
load_dotenv()

class Settings:
    """Application settings"""
    
    def __init__(self):
        # Cache settings
        self.valkey_url: str = os.getenv("VALKEY_URL", "redis://localhost:6379/0")
        self.cache_ttl: int = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour default
        
        # API settings
        self.api_host: str = os.getenv("API_HOST", "0.0.0.0")
        self.api_port: int = int(os.getenv("API_PORT", "8000"))
        
        # AI service settings
        self.anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
        self.claude_model: str = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001")  # Configurable via .env file
        self.claude_review_model: str = os.getenv("CLAUDE_REVIEW_MODEL", "claude-haiku-4-5-20251001")  # Using Haiku for speed
        self.model_speed: str = os.getenv("MODEL_SPEED", "fast")  # fast, balanced, quality
        self.max_concurrent_agents: int = int(os.getenv("MAX_CONCURRENT_AGENTS", "50"))  # Increased to 50 for maximum parallelization
        
        # Link verification settings
        self.link_verification_timeout: int = int(os.getenv("LINK_VERIFICATION_TIMEOUT", "30"))
        self.max_pages_to_analyze: int = int(os.getenv("MAX_PAGES_TO_ANALYZE", "5"))
        
        # Performance optimization settings
        self.ai_request_timeout: int = int(os.getenv("AI_REQUEST_TIMEOUT", "15"))  # Reduced timeout for faster failures
        self.ai_max_retries: int = int(os.getenv("AI_MAX_RETRIES", "2"))  # Fewer retries for speed
        self.ai_retry_delay: float = float(os.getenv("AI_RETRY_DELAY", "0.5"))  # Faster retry
        
    def validate(self) -> bool:
        """Validate that required settings are present"""
        if not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required but not found in environment variables. The application cannot function without AI.")
        return True

# Global settings instance
settings = Settings()