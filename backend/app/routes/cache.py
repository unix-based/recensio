"""
Cache management routes
"""

from fastapi import APIRouter, Depends
from app.services.cache_service import CacheService
from app.dependencies import get_cache_service
from app.logger import get_module_logger

logger = get_module_logger(__name__)
router = APIRouter()


@router.get("/stats")
async def get_cache_stats(cache_service: CacheService = Depends(get_cache_service)):
    """Get cache statistics"""
    try:
        stats = cache_service.get_storage_stats()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/health")
async def cache_health_check(cache_service: CacheService = Depends(get_cache_service)):
    """Check cache service health"""
    try:
        is_healthy = cache_service.health_check()
        return {
            "success": True,
            "healthy": is_healthy
        }
    except Exception as e:
        logger.error(f"Error checking cache health: {str(e)}")
        return {
            "success": False,
            "healthy": False,
            "error": str(e)
        }


@router.post("/clear")
async def clear_cache(cache_service: CacheService = Depends(get_cache_service)):
    """Clear all cached data"""
    try:
        success = cache_service.clear_all_cache()
        return {
            "success": success,
            "message": "Cache cleared successfully" if success else "Failed to clear cache"
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
