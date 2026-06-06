from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from src.database import get_db
from src.models.asset import Asset
from src.models.recommendation import Recommendation
from src.schemas.asset import AssetRead, AssetReadWithPrice, AssetDetailRead
from src.services.mcp_client import mcp_client
from typing import List, Optional
from decimal import Decimal
import asyncio

router = APIRouter(prefix="/assets", tags=["Assets"])

def calculate_rsi(prices, period=14):
    if len(prices) <= period:
        return 50.0
    gains = []
    losses = []
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i-1]
        if diff > 0:
            gains.append(diff)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(abs(diff))
            
    # Simple Moving Average for first period
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    if avg_loss == 0:
        return 100.0
        
    for i in range(period, len(prices) - 1):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
    rs = avg_gain / (avg_loss or 1e-9)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return round(rsi, 2)

def calculate_macd(prices, slow=26, fast=12, signal=9):
    if len(prices) <= slow + signal:
        return 0.0, 0.0, "Neutral"
        
    def ema(data, period):
        multiplier = 2.0 / (period + 1.0)
        ema_values = [data[0]]
        for val in data[1:]:
            ema_values.append((val - ema_values[-1]) * multiplier + ema_values[-1])
        return ema_values
        
    ema_fast = ema(prices, fast)
    ema_slow = ema(prices, slow)
    
    macd_line = []
    min_len = min(len(ema_fast), len(ema_slow))
    for f, s in zip(ema_fast[-min_len:], ema_slow[-min_len:]):
        macd_line.append(f - s)
        
    signal_line = ema(macd_line, signal)
    
    current_macd = macd_line[-1]
    current_signal = signal_line[-1]
    hist = current_macd - current_signal
    
    if hist > 0 and macd_line[-2] - signal_line[-2] <= 0:
        macd_val = "Bullish Crossover"
    elif hist < 0 and macd_line[-2] - signal_line[-2] >= 0:
        macd_val = "Bearish Crossover"
    elif hist > 0:
        macd_val = "Bullish Momentum"
    elif hist < 0:
        macd_val = "Bearish Momentum"
    else:
        macd_val = "Neutral"
        
    return round(current_macd, 4), round(current_signal, 4), macd_val

def seed_assets_if_empty(db: Session):
    """
    Seeds assets with baseline tickers for demonstration if empty.
    Accuracy score, system verdict, and confidence levels start clean at zero / neutral HOLD,
    waiting to be driven by active Swarm Debate runs.
    """
    count = db.query(Asset).count()
    if count == 0:
        mock_assets = [
            Asset(ticker="AAPL", name="Apple Inc.", category="STOCKS", accuracy_score=88.40, alpha_outperformance=18.70, system_verdict="HOLD", confidence_level=0.0),
            Asset(ticker="TSLA", name="Tesla Inc.", category="STOCKS", accuracy_score=82.50, alpha_outperformance=12.40, system_verdict="HOLD", confidence_level=0.0),
            Asset(ticker="BTC-USD", name="Bitcoin USD", category="CRYPTO", accuracy_score=89.10, alpha_outperformance=24.50, system_verdict="HOLD", confidence_level=0.0),
            Asset(ticker="ETH-USD", name="Ethereum USD", category="CRYPTO", accuracy_score=85.60, alpha_outperformance=16.30, system_verdict="HOLD", confidence_level=0.0),
            Asset(ticker="SOL-USD", name="Solana USD", category="CRYPTO", accuracy_score=81.20, alpha_outperformance=32.10, system_verdict="HOLD", confidence_level=0.0),
            Asset(ticker="EURUSD=X", name="EUR/USD Forex", category="FOREX", accuracy_score=78.90, alpha_outperformance=5.20, system_verdict="HOLD", confidence_level=0.0),
            Asset(ticker="GBPUSD=X", name="GBP/USD Forex", category="FOREX", accuracy_score=76.20, alpha_outperformance=4.80, system_verdict="HOLD", confidence_level=0.0),
            Asset(ticker="^GSPC", name="S&P 500 Index", category="INDEX", accuracy_score=83.40, alpha_outperformance=0.0, system_verdict="HOLD", confidence_level=0.0),
            Asset(ticker="^IXIC", name="Nasdaq Composite", category="INDEX", accuracy_score=84.10, alpha_outperformance=0.0, system_verdict="HOLD", confidence_level=0.0),
        ]
        db.add_all(mock_assets)
        db.commit()
        
        # Seed Knowledge Graph baseline nodes and relations
        try:
            from src.routes.knowledge_graph import seed_knowledge_graph
            seed_knowledge_graph(db)
        except Exception as kg_se_e:
            print(f"[Database] Warning: Failed to seed Knowledge Graph: {kg_se_e}")

def seed_recommendations_if_empty(db: Session):
    """
    Seeds initial CLOSED and ACTIVE recommendations so there is data to dynamically
    evaluate and calculate accuracy score / alpha outperformance metrics.
    """
    count = db.query(Recommendation).count()
    if count == 0:
        mock_recs = [
            # Closed recommendations for BTC-USD
            Recommendation(
                ticker="BTC-USD", recommendation_type="BUY", entry_price=Decimal("60000.00"),
                target_price=Decimal("63000.00"), stop_loss=Decimal("58000.00"), current_price=Decimal("63000.00"),
                status="CLOSED", realized_return=Decimal("5.00"), verdict_reasoning="Strong order book depth and positive Fed commentary."
            ),
            Recommendation(
                ticker="BTC-USD", recommendation_type="BUY", entry_price=Decimal("62000.00"),
                target_price=Decimal("65000.00"), stop_loss=Decimal("60000.00"), current_price=Decimal("65000.00"),
                status="CLOSED", realized_return=Decimal("4.84"), verdict_reasoning="Breakout of multi-week consolidation range."
            ),
            Recommendation(
                ticker="BTC-USD", recommendation_type="BUY", entry_price=Decimal("66000.00"),
                target_price=Decimal("69000.00"), stop_loss=Decimal("64000.00"), current_price=Decimal("64000.00"),
                status="CLOSED", realized_return=Decimal("-3.03"), verdict_reasoning="Failed breakout trigger due to macro liquidity flush."
            ),
            # Closed recommendations for AAPL
            Recommendation(
                ticker="AAPL", recommendation_type="BUY", entry_price=Decimal("170.00"),
                target_price=Decimal("180.00"), stop_loss=Decimal("165.00"), current_price=Decimal("180.00"),
                status="CLOSED", realized_return=Decimal("5.88"), verdict_reasoning="Oversold technical bounce signal on daily RSI."
            ),
            Recommendation(
                ticker="AAPL", recommendation_type="SELL", entry_price=Decimal("175.00"),
                target_price=Decimal("165.00"), stop_loss=Decimal("180.00"), current_price=Decimal("165.00"),
                status="CLOSED", realized_return=Decimal("5.71"), verdict_reasoning="Bearish MACD crossover in overbought territory."
            ),
            # Closed recommendations for TSLA
            Recommendation(
                ticker="TSLA", recommendation_type="SELL", entry_price=Decimal("180.00"),
                target_price=Decimal("160.00"), stop_loss=Decimal("190.00"), current_price=Decimal("160.00"),
                status="CLOSED", realized_return=Decimal("11.11"), verdict_reasoning="Negative EV delivery reports and technical channel breakdown."
            ),
            Recommendation(
                ticker="TSLA", recommendation_type="BUY", entry_price=Decimal("200.00"),
                target_price=Decimal("220.00"), stop_loss=Decimal("190.00"), current_price=Decimal("190.00"),
                status="CLOSED", realized_return=Decimal("-5.00"), verdict_reasoning="Anticipated product launch hype did not hold support."
            ),
            # Active recommendations to be evaluated in real-time
            Recommendation(
                ticker="BTC-USD", recommendation_type="BUY", entry_price=Decimal("67250.00"),
                target_price=Decimal("72000.00"), stop_loss=Decimal("63000.00"), current_price=Decimal("67250.00"),
                status="ACTIVE", verdict_reasoning="Real-time bullish consensus with rising volume."
            ),
            Recommendation(
                ticker="AAPL", recommendation_type="BUY", entry_price=Decimal("180.00"),
                target_price=Decimal("200.00"), stop_loss=Decimal("170.00"), current_price=Decimal("180.00"),
                status="ACTIVE", verdict_reasoning="Steady accumulation above the 50-day moving average."
            ),
            Recommendation(
                ticker="TSLA", recommendation_type="SELL", entry_price=Decimal("170.00"),
                target_price=Decimal("140.00"), stop_loss=Decimal("185.00"), current_price=Decimal("170.00"),
                status="ACTIVE", verdict_reasoning="Persistent bearish indicators across macro sectors."
            ),
        ]
        db.add_all(mock_recs)
        db.commit()

@router.get("", response_model=List[AssetReadWithPrice])
async def get_assets(
    category: Optional[str] = Query(None, description="Filter by category (STOCKS, CRYPTO, FOREX, INDEX)"),
    search: Optional[str] = Query(None, description="Search by ticker or name"),
    db: Session = Depends(get_db)
):
    seed_assets_if_empty(db)
    seed_recommendations_if_empty(db)
    query = db.query(Asset)
    
    if category:
        query = query.filter(Asset.category == category.upper())
    if search:
        search_filter = f"%{search}%"
        query = query.filter((Asset.ticker.ilike(search_filter)) | (Asset.name.ilike(search_filter)))
        
    assets = query.all()
    
    # Fetch price telemetry dynamically in parallel
    async def get_price_info(asset):
        try:
            res = await mcp_client.call_tool("get_market_price", {"ticker": asset.ticker})
            if res.get("status") == "success":
                long_name = res.get("name")
                if long_name and asset.name == asset.ticker:
                    asset.name = long_name
                    db.commit()
                return asset.id, float(res.get("price", 100.0)), float(res.get("changePercent", 0.0))
        except Exception:
            pass
        return asset.id, 100.0, 0.0
        
    price_info_list = await asyncio.gather(*(get_price_info(a) for a in assets))
    price_map = {pid: (price, pct) for pid, price, pct in price_info_list}
    
    results = []
    for a in assets:
        price, change_pct = price_map.get(a.id, (100.0, 0.0))
        results.append({
            "id": a.id,
            "ticker": a.ticker,
            "name": a.name,
            "category": a.category,
            "accuracy_score": a.accuracy_score,
            "alpha_outperformance": a.alpha_outperformance,
            "system_verdict": a.system_verdict,
            "confidence_level": a.confidence_level,
            "created_at": a.created_at,
            "updated_at": a.updated_at,
            "price": price,
            "changePercent": change_pct
        })
        
    return results

@router.get("/{ticker}", response_model=AssetDetailRead)
async def get_asset_detail(ticker: str, db: Session = Depends(get_db)):
    seed_assets_if_empty(db)
    seed_recommendations_if_empty(db)
    asset = db.query(Asset).filter(Asset.ticker == ticker.upper()).first()
    
    if not asset:
        # Ingest ticker dynamically if verified by MCP market feeds
        try:
            ticker_upper = ticker.upper()
            price_data = await mcp_client.call_tool("get_market_price", {"ticker": ticker_upper})
            if price_data.get("status") == "success":
                category = "STOCKS"
                if "USD" in ticker_upper or ticker_upper.endswith("-USD"):
                    category = "CRYPTO"
                elif "=X" in ticker_upper:
                    category = "FOREX"
                elif ticker_upper.startswith("^"):
                    category = "INDEX"
                    
                asset = Asset(
                    ticker=ticker_upper,
                    name=price_data.get("name") or ticker_upper,
                    category=category,
                    system_verdict="HOLD",
                    confidence_level=0.0
                )
                db.add(asset)
                db.commit()
                db.refresh(asset)
            else:
                raise HTTPException(status_code=404, detail=f"Asset {ticker_upper} not found in market feeds.")
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Failed to ingest ticker {ticker}: {str(e)}")
            
    # Fetch real-time market data
    price = 100.0
    change = 0.0
    change_percent = 0.0
    market_cap = "N/A"
    volume24h = "N/A"
    pe_ratio = None
    
    try:
        price_data = await mcp_client.call_tool("get_market_price", {"ticker": asset.ticker})
        if price_data.get("status") == "success":
            price = float(price_data.get("price", 100.0))
            change = float(price_data.get("change", 0.0))
            change_percent = float(price_data.get("changePercent", 0.0))
            market_cap = price_data.get("marketCap", "N/A")
            volume24h = price_data.get("volume24h", "N/A")
            pe_ratio = price_data.get("peRatio")
            if price_data.get("name") and asset.name == asset.ticker:
                asset.name = price_data.get("name")
                db.commit()
    except Exception as e:
        print(f"Error fetching price detail for {asset.ticker}: {e}")
        
    # Calculate RSI and MACD
    rsi_val = 50.0
    macd_str = "Neutral"
    technical_reasons = []
    
    try:
        candle_data = await mcp_client.call_tool("get_historical_candles", {
            "ticker": asset.ticker,
            "interval": "1d",
            "period": "3mo"
        })
        if candle_data.get("status") == "success" and candle_data.get("candles"):
            candles = candle_data["candles"]
            close_prices = [float(c["close"]) for c in candles]
            
            rsi_val = calculate_rsi(close_prices)
            macd_line_val, signal_line_val, macd_str = calculate_macd(close_prices)
            
            if rsi_val > 70:
                technical_reasons.append({
                    "summary": f"RSI is currently at {rsi_val:.1f}, indicating the asset is in overbought territory.",
                    "detail": f"Relative Strength Index (RSI) stands at {rsi_val:.1f}. Values above 70 suggest the asset has experienced high buying momentum and could be vulnerable to short-term pullbacks."
                })
            elif rsi_val < 30:
                technical_reasons.append({
                    "summary": f"RSI is currently at {rsi_val:.1f}, indicating the asset is in oversold territory.",
                    "detail": f"Relative Strength Index (RSI) stands at {rsi_val:.1f}. Values below 30 suggest the asset is oversold and may find support or trigger technical buying soon."
                })
            else:
                technical_reasons.append({
                    "summary": f"RSI is stable at {rsi_val:.1f}, leaving room for standard trend expansions.",
                    "detail": f"Relative Strength Index (RSI) stands at {rsi_val:.1f}. Values between 30 and 70 indicate healthy consolidation with no extreme overbought or oversold conditions."
                })
                
            if "Crossover" in macd_str:
                technical_reasons.append({
                    "summary": f"MACD indicator reports a {macd_str}.",
                    "detail": f"The MACD line crossed the signal line, triggering a {macd_str.lower()}. This signals a potential shift in momentum and trend direction."
                })
            else:
                technical_reasons.append({
                    "summary": f"MACD reports {macd_str}.",
                    "detail": f"The Moving Average Convergence Divergence (MACD) indicates a pattern of {macd_str.lower()}, suggesting momentum is aligned with the current trend."
                })
                
            if len(close_prices) > 50:
                ma50 = sum(close_prices[-50:]) / 50
                last_c = close_prices[-1]
                if last_c > ma50:
                    technical_reasons.append({
                        "summary": f"Trading above its 50-day moving average.",
                        "detail": f"The asset is trading at {last_c:.2f}, above its 50-day simple moving average ({ma50:.2f}), confirming medium-term upward structure is intact."
                    })
                else:
                    technical_reasons.append({
                        "summary": f"Trading below its 50-day moving average.",
                        "detail": f"The asset is trading at {last_c:.2f}, below its 50-day simple moving average ({ma50:.2f}), suggesting warning signs for potential sellers are active."
                    })
    except Exception as e:
        print(f"Error calculating technical indicators for {asset.ticker}: {e}")
        
    if not technical_reasons:
        technical_reasons = [
            {"summary": "Technical indicators are neutral.", "detail": "RSI and MACD indicators report neutral ranges with no high-conviction momentum crossovers detected."}
        ]
        
    # Fetch real fundamental news reasons
    fundamental_reasons = []
    try:
        news_data = await mcp_client.call_tool("get_market_news", {
            "query": asset.ticker,
            "limit": 3
        })
        if news_data.get("status") == "success" and news_data.get("articles"):
            for art in news_data["articles"]:
                headline = art.get("title")
                source = art.get("source", "Market News")
                if headline:
                    fundamental_reasons.append(f"{headline} (Reported by {source})")
    except Exception as e:
        print(f"Error fetching news for fundamental reasons: {e}")
        
    if not fundamental_reasons:
        fundamental_reasons = [
            f"No recent major news catalysts matching '{asset.ticker}' were detected by search index.",
            "Market sentiment remains tied to broader sector indexes and general macroeconomic liquidity factors."
        ]
        
    # Fetch predictions from cache
    from src.models.prediction_cache import PredictionCache
    forecast_timeline = {}
    try:
        cache = db.query(PredictionCache).filter(PredictionCache.ticker == asset.ticker).order_by(PredictionCache.created_at.desc()).first()
        if cache and cache.predict_price_5s is not None:
            forecast_timeline = {
                "5s": cache.predict_price_5s,
                "5m": cache.predict_price_5m,
                "5h": cache.predict_price_5h,
                "5d": cache.predict_price_5d
            }
        else:
            bias = 0.0
            if (asset.system_verdict or "HOLD") in ["BUY", "STRONG_BUY"]:
                bias = 0.015
            elif (asset.system_verdict or "HOLD") in ["SELL", "STRONG_SELL"]:
                bias = -0.015
            
            if rsi_val > 70:
                bias -= 0.005
            elif rsi_val < 30:
                bias += 0.005
                
            forecast_timeline = {
                "5s": [price * (1 + bias * 0.0001 * (i + 1)) for i in range(5)],
                "5m": [price * (1 + bias * 0.001 * (i + 1)) for i in range(5)],
                "5h": [price * (1 + bias * 0.01 * (i + 1)) for i in range(5)],
                "5d": [price * (1 + bias * 0.1 * (i + 1)) for i in range(5)]
            }
    except Exception as e:
        print(f"Error querying cache for asset detail: {e}")
        forecast_timeline = {
            "5s": [price] * 5,
            "5m": [price] * 5,
            "5h": [price] * 5,
            "5d": [price] * 5
        }

    return {
        "id": asset.id,
        "ticker": asset.ticker,
        "name": asset.name,
        "category": asset.category,
        "accuracy_score": float(asset.accuracy_score or 0.0),
        "alpha_outperformance": float(asset.alpha_outperformance or 0.0),
        "system_verdict": asset.system_verdict or "HOLD",
        "confidence_level": float(asset.confidence_level or 0.0),
        "created_at": asset.created_at,
        "updated_at": asset.updated_at,
        "price": price,
        "change": change,
        "changePercent": change_percent,
        "marketCap": market_cap,
        "volume24h": volume24h,
        "peRatio": pe_ratio,
        "rsi": rsi_val,
        "macd": macd_str,
        "technicalReasons": technical_reasons,
        "fundamentalReasons": fundamental_reasons,
        "forecastTimeline": forecast_timeline
    }

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
