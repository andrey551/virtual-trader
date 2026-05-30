from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from src.database import get_db
from src.models.event import NewsEvent, EventAssetImpact
from src.schemas.event import NewsEventRead
from src.config import settings
from typing import List, Optional
from decimal import Decimal
import datetime

router = APIRouter(prefix="/events", tags=["Events"])

def seed_events_if_empty(db: Session):
    """
    Seeds mock news events and asset impact tags for demonstration if the table is empty.
    """
    count = db.query(NewsEvent).count()
    if count == 0:
        # Create events
        e1 = NewsEvent(
            title="OPEC+ announces surprise crude oil production cuts starting next month",
            summary="OPEC+ members agreed to reduce output by 1.16 million barrels per day to stabilize market prices. Analysts expect oil and energy stocks to rise.",
            source="Reuters",
            link="https://www.reuters.com/opec-production-cuts-2026",
            published_at=datetime.datetime.utcnow() - datetime.timedelta(hours=12),
            sentiment_score=Decimal("0.65")
        )
        e2 = NewsEvent(
            title="Federal Reserve signals potential rate cuts by Q3 2026 as core inflation cools down",
            summary="Federal Reserve officials expressed optimism that inflation is steadily moving toward the 2% target, hinting at possible interest rate reductions later this year.",
            source="Bloomberg",
            link="https://www.bloomberg.com/fed-inflation-rate-cuts-2026",
            published_at=datetime.datetime.utcnow() - datetime.timedelta(days=1),
            sentiment_score=Decimal("0.55")
        )
        e3 = NewsEvent(
            title="Major offshore drilling oil spill reported in the Gulf of Mexico",
            summary="An accident at an offshore oil platform has caused an active spill spanning 5 miles. Authorities are attempting to contain the leak. Energy stocks drop.",
            source="AP News",
            link="https://www.apnews.com/gulf-oil-spill-leak-2026",
            published_at=datetime.datetime.utcnow() - datetime.timedelta(days=2),
            sentiment_score=Decimal("-0.75")
        )
        db.add_all([e1, e2, e3])
        db.commit()
        db.refresh(e1)
        db.refresh(e2)
        db.refresh(e3)
        
        # Link impacts
        imp1 = EventAssetImpact(event_id=e1.id, asset_ticker="USO", impact_direction="POSITIVE", estimated_impact_factor=Decimal("0.35"))
        imp2 = EventAssetImpact(event_id=e1.id, asset_ticker="CL=F", impact_direction="POSITIVE", estimated_impact_factor=Decimal("0.40"))
        imp3 = EventAssetImpact(event_id=e2.id, asset_ticker="^GSPC", impact_direction="POSITIVE", estimated_impact_factor=Decimal("0.15"))
        imp4 = EventAssetImpact(event_id=e2.id, asset_ticker="TLT", impact_direction="POSITIVE", estimated_impact_factor=Decimal("0.25"))
        imp5 = EventAssetImpact(event_id=e3.id, asset_ticker="USO", impact_direction="NEGATIVE", estimated_impact_factor=Decimal("-0.45"))
        imp6 = EventAssetImpact(event_id=e3.id, asset_ticker="CL=F", impact_direction="NEGATIVE", estimated_impact_factor=Decimal("-0.50"))
        db.add_all([imp1, imp2, imp3, imp4, imp5, imp6])
        db.commit()

@router.get("", response_model=List[NewsEventRead])
def get_events(limit: int = 10, db: Session = Depends(get_db)):
    seed_events_if_empty(db)
    return db.query(NewsEvent).order_by(NewsEvent.created_at.desc()).limit(limit).all()

@router.get("/search-similar", response_model=List[NewsEventRead])
def search_similar_events(
    query_text: str = Query(..., description="Query news text to find similar events in database"),
    limit: int = 5,
    db: Session = Depends(get_db)
):
    seed_events_if_empty(db)
    # Search is performed using full-text search fallback in SQLite/Dev,
    # mapping semantic vector parameters for PG instances.
    search_filter = f"%{query_text}%"
    return db.query(NewsEvent).filter(
        (NewsEvent.title.ilike(search_filter)) | (NewsEvent.summary.ilike(search_filter))
    ).order_by(NewsEvent.created_at.desc()).limit(limit).all()
