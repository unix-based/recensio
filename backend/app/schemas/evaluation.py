"""
Evaluation Schemas - Pydantic models for API validation
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EvaluationBase(BaseModel):
    """Base evaluation schema"""
    agent_id: int
    product_url: str
    design_score: Optional[float] = None
    usability_score: Optional[float] = None
    value_score: Optional[float] = None
    overall_score: Optional[float] = None
    design_feedback: Optional[str] = None
    usability_feedback: Optional[str] = None
    value_feedback: Optional[str] = None
    overall_feedback: Optional[str] = None
    would_recommend: Optional[str] = None
    purchase_likelihood: Optional[float] = None

class EvaluationCreate(EvaluationBase):
    """Schema for creating an evaluation"""
    pass

class EvaluationResponse(EvaluationBase):
    """Schema for evaluation API responses"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class EvaluationSummary(BaseModel):
    """Schema for evaluation summary"""
    product_url: str
    total_evaluations: int
    average_design_score: float
    average_usability_score: float
    average_value_score: float
    average_overall_score: float
    recommendation_rate: float
    purchase_likelihood: float
