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

async def seed_events_if_empty(db: Session):
    """
    Triggers the real-time news crawler in background to pull real global financial
    news via MCP if the DB is empty on startup, instead of loading mock items.
    """
    count = db.query(NewsEvent).count()
    if count == 0:
        from src.workers.news_scheduler import scan_all_topics
        print("[Events Router] DB news feed is empty. Crawling live news feeds via MCP...")
        try:
            await scan_all_topics()
        except Exception as e:
            print(f"[Events Router] Failed to execute initial news crawler fetch: {e}")

@router.get("", response_model=List[NewsEventRead])
async def get_events(limit: int = 10, db: Session = Depends(get_db)):
    await seed_events_if_empty(db)
    return db.query(NewsEvent).order_by(NewsEvent.published_at.desc()).limit(limit).all()

@router.get("/search-similar", response_model=List[NewsEventRead])
async def search_similar_events(
    query_text: str = Query(..., description="Query news text to find similar events in database"),
    limit: int = 5,
    db: Session = Depends(get_db)
):
    await seed_events_if_empty(db)
    search_filter = f"%{query_text}%"
    return db.query(NewsEvent).filter(
        (NewsEvent.title.ilike(search_filter)) | (NewsEvent.summary.ilike(search_filter))
    ).order_by(NewsEvent.published_at.desc()).limit(limit).all()
