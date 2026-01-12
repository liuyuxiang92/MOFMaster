"""Pydantic models for API Input/Output."""

from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from langchain_core.messages import BaseMessage


class InvokeRequest(BaseModel):
    """Request model for /invoke endpoint."""
    input: Dict[str, Any]
    
    class Config:
        arbitrary_types_allowed = True


class InvokeResponse(BaseModel):
    """Response model for /invoke endpoint."""
    output: Dict[str, Any]
    
    class Config:
        arbitrary_types_allowed = True


class SupervisorReview(BaseModel):
    """Structured output from Supervisor agent."""
    approved: bool
    feedback: str

