from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None


class UserLogin(BaseModel):
    username: str = Field(..., example="Anant")
    password: str = Field(..., example="EnterprisePass123!")


class IncidentRequest(BaseModel):
    raw_query: str = Field(
        ...,
        description="The detailed helpdesk incident or issue description.",
        example="Production EC2 instance CPU utilization is continuously above 95%."
    )
    department: Optional[str] = Field(default="Infrastructure", example="Infrastructure")


class IncidentResponse(BaseModel):
    thread_id: str
    user_name: str
    department: str
    intent: str
    sub_category: str
    guardrail_passed: bool
    guardrail_violation_reason: Optional[str] = None
    sanitized_query: str
    solution: str
    confidence_score: int
    is_cached_response: bool
    visited_nodes: List[str]
