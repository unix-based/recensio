"""
Evaluation Service - Business logic for evaluations
"""

# Using Valkey/Redis for storage
from typing import List, Dict, Any, Optional
# Model imports removed - using Valkey/Redis storage
from app.schemas.evaluation import EvaluationCreate
from app.services.agent_storage_service import AgentStorageService
import random

class EvaluationService:
    """Service for managing evaluations"""
    
    def __init__(self, agent_storage: AgentStorageService):
        self.agent_storage = agent_storage
    
    def get_all_evaluations(self) -> List[Dict[str, Any]]:
        """Get all evaluations"""
        # For now, return empty list - evaluations will be stored in Valkey/Redis
        return []
    
    def get_evaluation_by_id(self, evaluation_id: int) -> Optional[Dict[str, Any]]:
        """Get evaluation by ID"""
        # For now, return None - evaluations will be stored in Valkey/Redis
        return None
    
    def create_evaluation(self, evaluation_data: EvaluationCreate) -> Dict[str, Any]:
        """Create new evaluation"""
        # For now, return empty dict - evaluations will be stored in Valkey/Redis
        return {}
    
    def simulate_all_agent_evaluations(self, product_url: str) -> List[Dict[str, Any]]:
        """Simulate evaluations from all active agents"""
        agents = self.agent_storage.list_agents()
        evaluations = []
        
        for agent in agents:
            # Simulate AI evaluation based on agent profile
            evaluation_data = self._simulate_agent_evaluation(agent, product_url)
            # For now, just append the evaluation data - will be stored in Valkey/Redis
            evaluations.append(evaluation_data)
        
        return evaluations
    
    def _simulate_agent_evaluation(self, agent: Dict[str, Any], product_url: str) -> Dict[str, Any]:
        """Simulate evaluation based on agent profile"""
        # Base scores influenced by agent characteristics
        base_score = 5.0
        
        # Tech-savvy agents tend to be more critical
        tech_factor = (10 - agent.tech_savviness) * 0.2
        
        # Age factor (younger agents might be more enthusiastic)
        age_factor = (45 - agent.age) * 0.05
        
        design_score = max(1, min(10, base_score + random.uniform(-2, 2) + tech_factor))
        usability_score = max(1, min(10, base_score + random.uniform(-2, 2) + tech_factor))
        value_score = max(1, min(10, base_score + random.uniform(-2, 2) + age_factor))
        overall_score = (design_score + usability_score + value_score) / 3
        
        return {
            "agent_id": agent.id,
            "product_url": product_url,
            "design_score": round(design_score, 1),
            "usability_score": round(usability_score, 1),
            "value_score": round(value_score, 1),
            "overall_score": round(overall_score, 1),
            "design_feedback": f"Design feedback from {agent.name}",
            "usability_feedback": f"Usability feedback from {agent.name}",
            "value_feedback": f"Value feedback from {agent.name}",
            "overall_feedback": f"Overall feedback from {agent.name}",
            "would_recommend": "yes" if overall_score > 6 else "no" if overall_score < 4 else "maybe",
            "purchase_likelihood": max(0, min(1, overall_score / 10))
        }
    
    def get_evaluation_summary(self, product_url: str) -> Dict[str, Any]:
        """Get evaluation summary for a product"""
        evaluations = self.db.query(Evaluation).filter(Evaluation.product_url == product_url).all()
        
        if not evaluations:
            return {"message": "No evaluations found for this product"}
        
        total = len(evaluations)
        avg_design = sum(e.design_score for e in evaluations) / total
        avg_usability = sum(e.usability_score for e in evaluations) / total
        avg_value = sum(e.value_score for e in evaluations) / total
        avg_overall = sum(e.overall_score for e in evaluations) / total
        
        recommendations = sum(1 for e in evaluations if e.would_recommend == "yes")
        avg_purchase = sum(e.purchase_likelihood for e in evaluations) / total
        
        return {
            "product_url": product_url,
            "total_evaluations": total,
            "average_design_score": round(avg_design, 1),
            "average_usability_score": round(avg_usability, 1),
            "average_value_score": round(avg_value, 1),
            "average_overall_score": round(avg_overall, 1),
            "recommendation_rate": round(recommendations / total * 100, 1),
            "purchase_likelihood": round(avg_purchase * 100, 1)
        }
