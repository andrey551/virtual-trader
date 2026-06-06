from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime
from typing import Optional

class AssetBase(BaseModel):
    ticker: str
    name: str
    category: str
    accuracy_score: Decimal = Decimal("0.0")
    alpha_outperformance: Decimal = Decimal("0.0")
    system_verdict: str = "HOLD"
    confidence_level: Decimal = Decimal("0.0")

class AssetCreate(AssetBase):
    pass

class AssetUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    accuracy_score: Optional[Decimal] = None
    alpha_outperformance: Optional[Decimal] = None
    system_verdict: Optional[str] = None
    confidence_level: Optional[Decimal] = None

class AssetRead(AssetBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        coerce_numbers_to_str = True

class TechnicalReasonSchema(BaseModel):
    summary: str
    detail: str

class AssetReadWithPrice(AssetRead):
    price: float = 100.0
    changePercent: float = 0.0

class AssetDetailRead(AssetRead):
    price: float = 100.0
    change: float = 0.0
    changePercent: float = 0.0
    marketCap: str = "N/A"
    volume24h: str = "N/A"
    peRatio: Optional[str] = None
    rsi: float = 50.0
    macd: str = "Neutral"
    technicalReasons: list[TechnicalReasonSchema] = []
    fundamentalReasons: list[str] = []
    forecastTimeline: dict[str, list[float]] = {}
