"""
Dashboard Routes - Analytics and insights
"""

from fastapi import APIRouter, Depends
from app.services.dashboard_service import DashboardService
from app.services.agent_storage_service import AgentStorageService
from app.dependencies import get_agent_storage_service

router = APIRouter()

@router.get("/stats")
async def get_dashboard_stats(agent_storage: AgentStorageService = Depends(get_agent_storage_service)):
    """Get overall dashboard statistics from real data"""
    service = DashboardService(agent_storage)
    return service.get_overall_stats()

@router.get("/insights")
async def get_insights(agent_storage: AgentStorageService = Depends(get_agent_storage_service)):
    """Get AI-generated insights from evaluations"""
    service = DashboardService(agent_storage)
    return service.get_ai_insights()

@router.get("/trends")
async def get_trends(agent_storage: AgentStorageService = Depends(get_agent_storage_service)):
    """Get evaluation trends and patterns"""
    service = DashboardService(agent_storage)
    return service.get_evaluation_trends()
