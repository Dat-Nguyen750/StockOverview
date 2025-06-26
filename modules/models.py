from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from enum import Enum

class InvestmentVerdict(str, Enum):
    STRONG_BUY = "🟢 Strong Buy"
    BUY = "✅ Investable"
    HOLD = "🟡 Hold/Monitor"
    AVOID = "🔴 Avoid"

class ScoreBreakdown(BaseModel):
    financial_health: float = Field(..., ge=0, le=100, description="Financial health score (0-100)")
    business_fundamentals: float = Field(..., ge=0, le=100, description="Business fundamentals score (0-100)")
    valuation: float = Field(..., ge=0, le=100, description="Valuation score (0-100)")
    growth_potential: float = Field(..., ge=0, le=100, description="Growth potential score (0-100)")
    sentiment: float = Field(..., ge=0, le=100, description="Sentiment and red flags score (0-100)")

class EvaluationResponse(BaseModel):
    ticker: str
    company_name: str
    score_breakdown: ScoreBreakdown
    composite_score: float = Field(..., ge=0, le=100)
    verdict: InvestmentVerdict
    explanation: str
    general_summary: str
    detailed_analysis: Optional[Dict[str, Any]] = None
    evaluation_timestamp: str
    data_sources: List[str]

class EvaluationRequest(BaseModel):
    ticker: str
    include_detailed_analysis: bool = False
    custom_weights: Optional[Dict[str, float]] = None
