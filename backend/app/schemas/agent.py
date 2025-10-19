"""
Agent Schemas - Pydantic models for API validation
"""

from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

class RatingsModel(BaseModel):
    """Ratings schema"""
    overall: float
    clarity: float
    ux: float
    valueProposition: float

class AgentBase(BaseModel):
    """Base agent schema"""
    name: str
    age: int
    gender: str  # "male" or "female"
    occupation: str
    lifeViews: Optional[str] = None  # "progressive", "moderate", "conservative"
    innovationAttitude: Optional[str] = None  # "conservative", "moderate", "innovator"
    riskTolerance: Optional[int] = None  # 1-10
    gullibility: Optional[int] = None  # 1-10
    emoji: Optional[str] = None
    avatarColor: Optional[str] = None
    status: Optional[str] = "pending"
    
    # Legacy fields for backward compatibility
    interests: Optional[str] = None
    tech_savviness: Optional[int] = None
    budget_range: Optional[str] = None
    location: Optional[str] = None

class AgentCreate(AgentBase):
    """Schema for creating an agent"""
    pass

class AgentResponse(AgentBase):
    """Schema for agent API responses"""
    id: int
    is_active: bool
    created_at: Optional[datetime] = None
    ratings: Optional[RatingsModel] = None
    review: Optional[str] = None
    
    class Config:
        from_attributes = True

class AgentUpdate(BaseModel):
    """Schema for updating an agent"""
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    lifeViews: Optional[str] = None
    innovationAttitude: Optional[str] = None
    riskTolerance: Optional[int] = None
    gullibility: Optional[int] = None
    emoji: Optional[str] = None
    avatarColor: Optional[str] = None
    status: Optional[str] = None
    overall_rating: Optional[float] = None
    clarity_rating: Optional[float] = None
    ux_rating: Optional[float] = None
    value_proposition_rating: Optional[float] = None
    review_text: Optional[str] = None
    
    # Legacy fields
    interests: Optional[str] = None
    tech_savviness: Optional[int] = None
    budget_range: Optional[str] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None
