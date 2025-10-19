"""
Dashboard Service - Analytics and insights
"""

# Using Valkey/Redis for storage
from typing import Dict, Any
# Model imports removed - using Valkey/Redis storage
from app.services.agent_storage_service import AgentStorageService

class DashboardService:
    """Service for dashboard analytics"""
    
    def __init__(self, agent_storage: AgentStorageService):
        self.agent_storage = agent_storage
    
    def get_overall_stats(self) -> Dict[str, Any]:
        """Get overall dashboard statistics - ephemeral data only"""
        return {
            "total_evaluations": 0,  # No persistent evaluations
            "average_scores": {
                "design": 0,
                "usability": 0,
                "value": 0,
                "overall": 0
            }
        }
    
    def get_ai_insights(self) -> Dict[str, Any]:
        """Get AI-generated insights - ephemeral data only"""
        return {
            "key_insights": [],
            "recommendations": [],
            "trends": []
        }
    
    def get_evaluation_trends(self) -> Dict[str, Any]:
        """Get evaluation trends and patterns - ephemeral data only"""
        return {
            "score_distribution": {
                "design": {"1-3": 0, "4-6": 0, "7-10": 0},
                "usability": {"1-3": 0, "4-6": 0, "7-10": 0},
                "value": {"1-3": 0, "4-6": 0, "7-10": 0}
            },
            "recommendation_breakdown": {
                "yes": 0,
                "maybe": 0,
                "no": 0
            },
            "top_feedback_themes": []
        }
