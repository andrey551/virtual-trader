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
Base.metadata.create_all(bind=engine)

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
    from src.database import SessionLocal
    from src.models.asset import Asset

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
            # Default mock prices based on ticker
            mock_match = {
                "BTC-USD": 67250.45,
                "ETH-USD": 3450.80,
                "SOL-USD": 168.20,
                "AAPL": 189.84,
                "TSLA": 178.46,
                "NVDA": 948.22,
                "EURUSD=X": 1.0850,
                "GBPUSD=X": 1.2720,
                "^GSPC": 5277.51
            }
            price = mock_match.get(asset.ticker, 100.0)
    except Exception as e:
        print(f"[WebSocket Debate] DB lookup failed: {e}")
    finally:
        db.close()
        
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
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.path.dirname(script_path)
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
        
        # Keep connection alive
        while True:
            await websocket.receive_text()
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        print(f"[WebSocket Debate] Agent session {session_id} disconnected")
    except Exception as e:
        print(f"[WebSocket Debate] Connection closed: {str(e)}")
