from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from src.database import get_db
from src.models.asset import Asset
from src.schemas.asset import AssetRead
from src.services.mcp_client import mcp_client
from typing import List, Optional

router = APIRouter(prefix="/assets", tags=["Assets"])

def seed_assets_if_empty(db: Session):
    """
    Seeds mock assets in database for demonstration if the table is empty.
    """
    count = db.query(Asset).count()
    if count == 0:
        mock_assets = [
            Asset(ticker="AAPL", name="Apple Inc.", category="STOCKS", accuracy_score=88.40, alpha_outperformance=18.70, system_verdict="BUY", confidence_level=85.0),
            Asset(ticker="TSLA", name="Tesla Inc.", category="STOCKS", accuracy_score=82.50, alpha_outperformance=12.40, system_verdict="HOLD", confidence_level=60.0),
            Asset(ticker="BTC-USD", name="Bitcoin USD", category="CRYPTO", accuracy_score=89.10, alpha_outperformance=24.50, system_verdict="STRONG_BUY", confidence_level=92.0),
            Asset(ticker="ETH-USD", name="Ethereum USD", category="CRYPTO", accuracy_score=85.60, alpha_outperformance=16.30, system_verdict="BUY", confidence_level=78.0),
            Asset(ticker="SOL-USD", name="Solana USD", category="CRYPTO", accuracy_score=81.20, alpha_outperformance=32.10, system_verdict="STRONG_BUY", confidence_level=88.0),
            Asset(ticker="EURUSD=X", name="EUR/USD Forex", category="FOREX", accuracy_score=78.90, alpha_outperformance=5.20, system_verdict="HOLD", confidence_level=55.0),
            Asset(ticker="GBPUSD=X", name="GBP/USD Forex", category="FOREX", accuracy_score=76.20, alpha_outperformance=4.80, system_verdict="SELL", confidence_level=70.0),
            Asset(ticker="^GSPC", name="S&P 500 Index", category="INDEX", accuracy_score=83.40, alpha_outperformance=0.0, system_verdict="HOLD", confidence_level=50.0),
            Asset(ticker="^IXIC", name="Nasdaq Composite", category="INDEX", accuracy_score=84.10, alpha_outperformance=0.0, system_verdict="BUY", confidence_level=65.0),
        ]
        db.add_all(mock_assets)
        db.commit()

@router.get("", response_model=List[AssetRead])
def get_assets(
    category: Optional[str] = Query(None, description="Filter by category (STOCKS, CRYPTO, FOREX, INDEX)"),
    search: Optional[str] = Query(None, description="Search by ticker or name"),
    db: Session = Depends(get_db)
):
    seed_assets_if_empty(db)
    query = db.query(Asset)
    
    if category:
        query = query.filter(Asset.category == category.upper())
    if search:
        search_filter = f"%{search}%"
        query = query.filter((Asset.ticker.ilike(search_filter)) | (Asset.name.ilike(search_filter)))
        
    return query.all()

@router.get("/{ticker}", response_model=AssetRead)
async def get_asset_detail(ticker: str, db: Session = Depends(get_db)):
    seed_assets_if_empty(db)
    asset = db.query(Asset).filter(Asset.ticker == ticker.upper()).first()
    
    if not asset:
        # If ticker is not in DB, query the MCP server to verify if it is a valid ticker
        try:
            ticker_upper = ticker.upper()
            price_data = await mcp_client.call_tool("get_market_price", {"ticker": ticker_upper})
            if price_data.get("status") == "success":
                # Determine asset category based on ticker format
                category = "STOCKS"
                if "USD" in ticker_upper or ticker_upper.endswith("-USD"):
                    category = "CRYPTO"
                elif "=X" in ticker_upper:
                    category = "FOREX"
                elif ticker_upper.startswith("^"):
                    category = "INDEX"
                    
                asset = Asset(
                    ticker=ticker_upper,
                    name=ticker_upper,
                    category=category,
                    system_verdict="HOLD",
                    confidence_level=50.0
                )
                db.add(asset)
                db.commit()
                db.refresh(asset)
            else:
                raise HTTPException(status_code=404, detail=f"Asset {ticker_upper} not found in market feeds.")
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Failed to ingest ticker {ticker}: {str(e)}")
            
    return asset

@router.get("/{ticker}/candles")
async def get_asset_candles(
    ticker: str,
    interval: str = Query("1d", description="Candle interval (1m, 5m, 1h, 1d, 1wk, 1mo)"),
    period: str = Query("1mo", description="Historical period (1d, 5d, 1mo, 3mo, 1y, max)")
):
    res = await mcp_client.call_tool("get_historical_candles", {
        "ticker": ticker,
        "interval": interval,
        "period": period
    })
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res
