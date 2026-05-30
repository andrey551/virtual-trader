from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from src.database import get_db
from src.models.recommendation import Recommendation
from src.schemas.recommendation import RecommendationRead, RecommendationCreate
from typing import List, Optional
from decimal import Decimal
import datetime

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

def seed_recommendations_if_empty(db: Session):
    """
    Seeds mock recommendations in database for demonstration if the table is empty.
    """
    count = db.query(Recommendation).count()
    if count == 0:
        mock_recs = [
            Recommendation(
                ticker="BTC-USD",
                recommendation_type="BUY",
                entry_price=Decimal("62500.00"),
                target_price=Decimal("68500.00"),
                stop_loss=Decimal("59000.00"),
                current_price=Decimal("67250.45"),
                system_rating=Decimal("89.10"),
                status="ACTIVE",
                verdict_reasoning="Strong order book support combined with cooling core inflation signals massive upside."
            ),
            Recommendation(
                ticker="AAPL",
                recommendation_type="BUY",
                entry_price=Decimal("180.20"),
                target_price=Decimal("195.00"),
                stop_loss=Decimal("174.50"),
                current_price=Decimal("189.84"),
                system_rating=Decimal("85.00"),
                status="ACTIVE",
                verdict_reasoning="Consensus buy backed by robust institutional flows and technical breakouts above moving averages."
            ),
            Recommendation(
                ticker="GBPUSD=X",
                recommendation_type="SELL",
                entry_price=Decimal("1.2850"),
                target_price=Decimal("1.2500"),
                stop_loss=Decimal("1.3000"),
                current_price=Decimal("1.2720"),
                system_rating=Decimal("76.20"),
                status="CLOSED",
                realized_return=Decimal("1.01"),
                verdict_reasoning="Technical breakdown below support level combined with bearish macro currency indexes."
            ),
        ]
        db.add_all(mock_recs)
        db.commit()

@router.get("", response_model=List[RecommendationRead])
def get_recommendations(
    ticker: Optional[str] = Query(None, description="Filter by ticker"),
    status: Optional[str] = Query(None, description="Filter by status (ACTIVE, CLOSED)"),
    db: Session = Depends(get_db)
):
    seed_recommendations_if_empty(db)
    query = db.query(Recommendation)
    
    if ticker:
        query = query.filter(Recommendation.ticker == ticker.upper())
    if status:
        query = query.filter(Recommendation.status == status.upper())
        
    return query.order_by(Recommendation.created_at.desc()).all()

@router.post("", response_model=RecommendationRead)
def create_recommendation(rec_in: RecommendationCreate, db: Session = Depends(get_db)):
    db_rec = Recommendation(**rec_in.model_dump())
    db.add(db_rec)
    db.commit()
    db.refresh(db_rec)
    return db_rec
