from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from typing import Optional, List

class EventAssetImpactBase(BaseModel):
    asset_ticker: str
    impact_direction: str = "NEUTRAL"
    estimated_impact_factor: Decimal = Decimal("0.0")

class EventAssetImpactRead(EventAssetImpactBase):
    id: int
    event_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class NewsEventBase(BaseModel):
    title: str
    summary: Optional[str] = None
    source: Optional[str] = None
    link: Optional[str] = None
    published_at: Optional[datetime] = None
    sentiment_score: Decimal = Decimal("0.0")

class NewsEventCreate(NewsEventBase):
    embedding: Optional[str] = None

class NewsEventRead(NewsEventBase):
    id: int
    created_at: datetime
    impacts: List[EventAssetImpactRead] = []

    class Config:
        from_attributes = True
