from typing import List, Dict, Any, Optional, TypedDict
from pydantic import BaseModel

class AgentOpinion(BaseModel):
    agent_name: str
    verdict: str  # STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL
    confidence: float  # 0.0 to 100.0
    rationale: str
    key_argument: str = ""  # Brief 1-sentence summary of the specialist's core argument
    indicators_audited: List[str]

class DebateMessage(BaseModel):
    agent_name: str
    avatar_code: str
    message: str
    target_agent: Optional[str] = None
    status: str = "SPEAKING"  # SPEAKING, COMPLETED

class SwarmState(TypedDict):
    ticker: str
    category: str
    current_price: float
    market_data: Dict[str, Any]
    market_indicators: Dict[str, Any]  # Calculated indicators (RSI, MACD, SMA)
    similar_historical_events: List[Dict[str, Any]]
    knowledge_graph_paths: List[str]
    opinions: Dict[str, AgentOpinion]
    debate_history: List[DebateMessage]
    risk_profile: Dict[str, Any]
    consensus_verdict: str
    consensus_confidence: float
