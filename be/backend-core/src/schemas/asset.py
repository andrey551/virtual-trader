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
