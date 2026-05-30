import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.database import engine, Base
from src.routes import assets, events, recommendations, mcp_bridge
from src.services.mcp_client import mcp_client
from src.workers.news_scheduler import start_scheduler, shutdown_scheduler

# Auto-create tables on startup (excellent out-of-the-box SQLite/PostgreSQL development)
if not settings.DATABASE_URL.startswith("sqlite"):
    from sqlalchemy import text
    try:
        print("[Database] Ensuring pgvector extension is enabled in PostgreSQL...")
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
    except Exception as e:
        print(f"[Database] Warning: Failed to create pgvector extension: {e}")

# Import models here to ensure they are registered before create_all
from src.models.asset import Asset
from src.models.event import NewsEvent, EventAssetImpact
from src.models.recommendation import Recommendation
from src.models.debate import AgentDebate
from src.models.prediction_cache import PredictionCache

Base.metadata.create_all(bind=engine)

# Semaphore to limit concurrent swarm-engine subprocesses
SWARM_SEMAPHORE = asyncio.Semaphore(3)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles lifecycle events: boots up MCP stdio subprocess and APScheduler news worker on startup,
    and terminates them cleanly on shutdown.
    """
    print("[Lifespan] Starting Backend Core...")
    # 1. Startup stdio channel with MCP server
    await mcp_client.start()
    
    # 2. Start background task scheduler
    start_scheduler()
    
    yield
    
    print("[Lifespan] Shutting down Backend Core...")
    # 1. Shutdown scheduler
    shutdown_scheduler()
    
    # 2. Stop MCP subprocess channel
    await mcp_client.stop()

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

# CORS configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(assets.router, prefix=settings.API_V1_STR)
app.include_router(events.router, prefix=settings.API_V1_STR)
app.include_router(recommendations.router, prefix=settings.API_V1_STR)
app.include_router(mcp_bridge.router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "api_docs": "/docs"
    }

# -------------------------------------------------------------
# WebSockets Realtime Price Stream
# -------------------------------------------------------------
@app.websocket("/ws/prices")
async def websocket_prices_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Parse query parameters (e.g. ?tickers=AAPL,BTC-USD)
    query_params = websocket.query_params
    tickers_str = query_params.get("tickers", "")
    tickers = [t.strip().upper() for t in tickers_str.split(",") if t.strip()]
    
    if not tickers:
        await websocket.send_json({"error": "No tickers provided"})
        await websocket.close()
        return
        
    print(f"[WebSocket Price] Connection accepted for tickers: {tickers}")
    
    # Store the last pushed prices to check for significant changes (user rule)
    last_pushed_prices = {}  # {ticker: price_float}
    # Significant change threshold: 0.15% (e.g. 0.0015 change ratio)
    price_change_threshold = 0.0015
    
    try:
        while True:
            # Poll prices and stream if they changed significantly
            for ticker in tickers:
                try:
                    price_val = None
                    change_val = 0.0
                    change_pct = 0.0
                    currency_val = "USD"
                    
                    # Determine whether it is crypto (Binance) or general yfinance
                    # Crypto tickers from Binance are usually letters only (e.g. BTCUSDT, ETHUSDT)
                    # general tickers have dashes/symbols (e.g. BTC-USD, AAPL)
                    is_binance_crypto = (
                        "USDT" in ticker 
                        and "-" not in ticker 
                        and "/" not in ticker
                    )
                    
                    if is_binance_crypto:
                        res = await mcp_client.call_tool("get_crypto_ticker", {"symbol": ticker, "depth": 1})
                        if res.get("status") == "success":
                            price_val = float(res.get("price", 0.0))
                            currency_val = "USDT"
                    else:
                        res = await mcp_client.call_tool("get_market_price", {"ticker": ticker})
                        if res.get("status") == "success":
                            price_val = float(res.get("price", 0.0))
                            change_val = float(res.get("change", 0.0))
                            change_pct = float(res.get("changePercent", 0.0))
                            currency_val = res.get("currency", "USD")
                            
                    if price_val is not None:
                        old_price = last_pushed_prices.get(ticker)
                        should_push = False
                        
                        if old_price is None:
                            # Always push the initial quote
                            should_push = True
                        else:
                            # Calculate percentage ratio shift
                            diff_pct = abs(price_val - old_price) / old_price
                            if diff_pct >= price_change_threshold:
                                should_push = True
                                
                        if should_push:
                            last_pushed_prices[ticker] = price_val
                            payload = {
                                "type": "price_update",
                                "ticker": ticker,
                                "price": price_val,
                                "change": change_val,
                                "changePercent": change_pct,
                                "currency": currency_val,
                                "significant_update": True
                            }
                            await websocket.send_json(payload)
                            
                except Exception as e:
                    # Log internal quote lookup issues silently to prevent ws disconnect
                    pass
                    
            # Check price updates every 3 seconds
            await asyncio.sleep(3)
            
    except WebSocketDisconnect:
        print(f"[WebSocket Price] Disconnected for tickers: {tickers}")
    except Exception as e:
        print(f"[WebSocket Price] Connection closed due to error: {str(e)}")

# -------------------------------------------------------------
# WebSockets Realtime Swarm Agent Debate Stream
# -------------------------------------------------------------
@app.websocket("/ws/swarm-debate/{session_id}")
async def websocket_debate_endpoint(websocket: WebSocket, session_id: str):
    import sys
    import os
    import json
    import uuid
    from src.database import SessionLocal
    from src.models.asset import Asset
    from src.models.debate import AgentDebate
    from src.models.prediction_cache import PredictionCache

    await websocket.accept()
    print(f"[WebSocket Debate] Agent session {session_id} connected")
    
    # Default parameters
    ticker = "BTC-USD"
    category = "CRYPTO"
    price = 67250.45
    
    # Try resolving asset from ticker if session_id is a ticker
    if session_id != "live" and "-" in session_id:
        ticker = session_id.upper()
        
    db = SessionLocal()
    try:
        asset = db.query(Asset).filter(Asset.ticker == ticker.upper()).first()
        if asset:
            category = asset.category
            
        # Fetch real-time price via MCP
        is_binance_crypto = ("USDT" in ticker and "-" not in ticker and "/" not in ticker)
        
        if is_binance_crypto:
            res = await mcp_client.call_tool("get_crypto_ticker", {"symbol": ticker, "depth": 1})
            if res.get("status") == "success":
                price = float(res.get("price", 0.0))
        else:
            res = await mcp_client.call_tool("get_market_price", {"ticker": ticker})
            if res.get("status") == "success":
                price = float(res.get("price", 0.0))
                
    except Exception as e:
        print(f"[WebSocket Debate] DB lookup or Price fetch failed: {e}")
        
    # Check Cache
    try:
        cache = db.query(PredictionCache).filter(PredictionCache.ticker == ticker).order_by(PredictionCache.created_at.desc()).first()
        if cache:
            diff_pct = abs(price - cache.price_at_predict) / cache.price_at_predict
            if diff_pct < 0.01:
                print(f"[WebSocket Debate] Cache HIT for {ticker}. Diff: {diff_pct:.4f}. Streaming cached debate...")
                debates = db.query(AgentDebate).filter(AgentDebate.session_id == cache.session_id).order_by(AgentDebate.id).all()
                for d in debates:
                    payload = {
                        "agent_name": d.agent_name,
                        "avatar_code": d.avatar_code,
                        "message": d.message,
                        "status": "COMPLETED",
                        "session_id": session_id
                    }
                    await websocket.send_json(payload)
                    await asyncio.sleep(0.1) # small delay for UX
                
                db.close()
                # Keep connection alive
                while True:
                    await websocket.receive_text()
                    await asyncio.sleep(1)
                return
    except Exception as e:
        print(f"[WebSocket Debate] Cache check failed: {e}")
        
    # Build absolute path to swarm-engine main.py CLI
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script_path = os.path.abspath(os.path.join(base_dir, "..", "swarm-engine", "src", "main.py"))
    
    cmd = [
        sys.executable,
        script_path,
        "--ticker", ticker,
        "--category", category,
        "--price", str(price)
    ]
    
    print(f"[WebSocket Debate] Spawning swarm-engine CLI subprocess: {' '.join(cmd)}")
    
    # Propagate GEMINI_API_KEY explicitly to child process environment
    env = os.environ.copy()
    if settings.GEMINI_API_KEY:
        env["GEMINI_API_KEY"] = settings.GEMINI_API_KEY
    
    db_session_id = f"cache_{uuid.uuid4().hex[:8]}"
    
    try:
        print("[WebSocket Debate] Waiting for Swarm Semaphore...")
        async with SWARM_SEMAPHORE:
            print("[WebSocket Debate] Semaphore acquired. Starting process.")
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.path.dirname(script_path),
                env=env
            )
            
            # Read standard output line-by-line asynchronously
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                    
                line_str = line.decode('utf-8').strip()
                if not line_str:
                    continue
                    
                try:
                    # Parse JSON output from swarm-engine
                    data = json.loads(line_str)
                    
                    # Save completed messages to DB cache
                    if "message" in data and data.get("status") == "COMPLETED" and data["message"].strip():
                        try:
                            new_debate = AgentDebate(
                                session_id=db_session_id,
                                ticker=ticker,
                                agent_name=data.get("agent_name", "Unknown"),
                                avatar_code=data.get("avatar_code", "UNK"),
                                message=data["message"]
                            )
                            db.add(new_debate)
                            db.commit()
                        except Exception as dbe:
                            print(f"[WebSocket Debate DB Error] {dbe}")
                            db.rollback()
                            
                    # Inject session_id parameter for frontend tracking
                    data["session_id"] = session_id
                    await websocket.send_json(data)
                except json.JSONDecodeError:
                    # Non-JSON logs (e.g. stdout prints or traceback errors)
                    print(f"[WebSocket Debate Subprocess Log] {line_str}")
                    
            # Wait for subprocess completion
            stderr_data = await process.stderr.read()
            if stderr_data:
                print(f"[WebSocket Debate Subprocess Stderr] {stderr_data.decode('utf-8')}")
                
            await process.wait()
            
            # Save Prediction Cache
            try:
                new_cache = PredictionCache(
                    ticker=ticker,
                    session_id=db_session_id,
                    price_at_predict=price
                )
                db.add(new_cache)
                db.commit()
                print(f"[WebSocket Debate] Saved cache for {ticker} at price {price}")
            except Exception as ce:
                print(f"[WebSocket Debate Cache Error] {ce}")
                db.rollback()
                
            db.close()
            
            # Keep connection alive
            while True:
                await websocket.receive_text()
                await asyncio.sleep(1)
                
    except WebSocketDisconnect:
        print(f"[WebSocket Debate] Agent session {session_id} disconnected")
    except Exception as e:
        print(f"[WebSocket Debate] Connection closed: {str(e)}")
    finally:
        db.close()
