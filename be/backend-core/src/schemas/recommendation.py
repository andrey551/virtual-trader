from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from typing import Optional

class RecommendationBase(BaseModel):
    ticker: str
    recommendation_type: str
    entry_price: Decimal
    target_price: Optional[Decimal] = None
    stop_loss: Optional[Decimal] = None
    current_price: Optional[Decimal] = None
    system_rating: Optional[Decimal] = None
    status: str = "ACTIVE"
    realized_return: Optional[Decimal] = None
    verdict_reasoning: Optional[str] = None

class RecommendationCreate(RecommendationBase):
    pass

class RecommendationRead(RecommendationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
