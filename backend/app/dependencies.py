"""
Dependency injection system for the application.
Provides clean dependency management and injection using Valkey/Redis services.
"""

from typing import Generator, Optional
from fastapi import Depends
from app.services.agent_service import AgentService
from app.services.evaluation_service import EvaluationService
from app.services.dashboard_service import DashboardService
from app.services.claude_service import ClaudeService
from app.services.link_verification_service import LinkVerificationService
from app.services.cache_service import CacheService
from app.services.agent_storage_service import AgentStorageService
from app.services.site_storage_service import SiteStorageService
from app.logger import get_module_logger

logger = get_module_logger(__name__)


def get_agent_storage_service() -> AgentStorageService:
    """Get agent storage service instance.
    
    Returns:
        AgentStorageService instance for Valkey/Redis storage
    """
    return AgentStorageService()


def get_site_storage_service() -> SiteStorageService:
    """Get site storage service instance.
    
    Returns:
        SiteStorageService instance for Valkey/Redis storage
    """
    return SiteStorageService()


def get_agent_service(
    agent_storage: AgentStorageService = Depends(get_agent_storage_service)
) -> AgentService:
    """Get agent service instance.
    
    Args:
        agent_storage: Agent storage service
        
    Returns:
        AgentService instance
    """
    return AgentService(agent_storage)


def get_evaluation_service(
    agent_storage: AgentStorageService = Depends(get_agent_storage_service)
) -> EvaluationService:
    """Get evaluation service instance.
    
    Args:
        agent_storage: Agent storage service
        
    Returns:
        EvaluationService instance
    """
    return EvaluationService(agent_storage)


def get_dashboard_service(
    agent_storage: AgentStorageService = Depends(get_agent_storage_service)
) -> DashboardService:
    """Get dashboard service instance.
    
    Args:
        agent_storage: Agent storage service
        
    Returns:
        DashboardService instance
    """
    return DashboardService(agent_storage)


def get_claude_service(
    site_storage: SiteStorageService = Depends(get_site_storage_service)
) -> ClaudeService:
    """Get Claude service instance.
    
    Args:
        site_storage: Site storage service for website content retrieval
        
    Returns:
        ClaudeService instance
    """
    return ClaudeService(site_storage)


def get_link_verification_service() -> LinkVerificationService:
    """Get link verification service instance.
    
    Returns:
        LinkVerificationService instance
    """
    return LinkVerificationService()


def get_cache_service() -> CacheService:
    """Get cache service instance.
    
    Returns:
        CacheService instance
    """
    return CacheService()
