from pydantic import BaseModel, Field, HttpUrl
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class ConversationRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationMessage(BaseModel):
    role: ConversationRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UserProfile(BaseModel):
    user_id: str
    website_url: Optional[HttpUrl] = None
    industry: Optional[str] = None
    seo_goals: List[str] = Field(default_factory=list)
    current_challenges: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class SEORecommendation(BaseModel):
    id: str
    title: str
    description: str
    priority: str = Field(..., regex="^(high|medium|low)$")
    category: str
    implementation_status: str = Field(default="pending", regex="^(pending|in_progress|completed|dismissed)$")
    created_at: datetime = Field(default_factory=datetime.now)
    estimated_impact: Optional[str] = None


class WebsiteAnalysis(BaseModel):
    url: HttpUrl
    title: Optional[str] = None
    meta_description: Optional[str] = None
    h1_tags: List[str] = Field(default_factory=list)
    content_quality_score: Optional[float] = None
    ai_readiness_score: Optional[float] = None
    technical_issues: List[str] = Field(default_factory=list)
    content_suggestions: List[str] = Field(default_factory=list)
    analyzed_at: datetime = Field(default_factory=datetime.now)


class CompetitorAnalysis(BaseModel):
    competitor_url: HttpUrl
    content_gaps: List[str] = Field(default_factory=list)
    ai_citation_frequency: Optional[int] = None
    content_strategy_insights: List[str] = Field(default_factory=list)
    competitive_advantages: List[str] = Field(default_factory=list)
    analyzed_at: datetime = Field(default_factory=datetime.now)


class ConversationSession(BaseModel):
    session_id: str
    user_profile: UserProfile
    messages: List[ConversationMessage] = Field(default_factory=list)
    recommendations: List[SEORecommendation] = Field(default_factory=list)
    website_analyses: List[WebsiteAnalysis] = Field(default_factory=list)
    competitor_analyses: List[CompetitorAnalysis] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class AISearchMetrics(BaseModel):
    domain: str
    citation_count: int
    top_citing_queries: List[str] = Field(default_factory=list)
    ai_platforms: Dict[str, int] = Field(default_factory=dict)
    trending_topics: List[str] = Field(default_factory=list)
    measured_at: datetime = Field(default_factory=datetime.now)


class ToolResponse(BaseModel):
    tool_name: str
    success: bool
    data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    execution_time: Optional[float] = None