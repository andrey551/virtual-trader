import asyncio
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from src.config import settings
from src.database import engine, Base
from src.routes import assets, events, recommendations, mcp_bridge, knowledge_graph
from src.services.mcp_client import mcp_client
from src.workers.news_scheduler import start_scheduler, shutdown_scheduler
from src.metrics import (
    HTTP_REQUEST_DURATION,
    HTTP_REQUESTS_TOTAL,
    WS_CONNECTIONS_ACTIVE,
    SWARM_AGENT_AWAKENINGS,
    SWARM_TOKEN_USAGE,
    SWARM_CACHE_LOOKUPS,
    SWARM_DEBATE_DURATION,
)

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
from src.models.knowledge_graph import KnowledgeNode, KnowledgeEdge

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

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    path = request.url.path
    if path == "/metrics":
        return await call_next(request)
        
    method = request.method
    start_time = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception as e:
        status_code = 500
        raise e
    finally:
        duration = time.perf_counter() - start_time
        HTTP_REQUEST_DURATION.labels(method=method, endpoint=path, status=status_code).observe(duration)
        HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=path, status=status_code).inc()

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
app.include_router(knowledge_graph.router, prefix=settings.API_V1_STR)

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
    WS_CONNECTIONS_ACTIVE.labels(endpoint="/ws/prices").inc()
    
    # Parse query parameters (e.g. ?tickers=AAPL,BTC-USD)
    query_params = websocket.query_params
    tickers_str = query_params.get("tickers", "")
    tickers = [t.strip().upper() for t in tickers_str.split(",") if t.strip()]
    
    if not tickers:
        await websocket.send_json({"error": "No tickers provided"})
        await websocket.close()
        WS_CONNECTIONS_ACTIVE.labels(endpoint="/ws/prices").dec()
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
    finally:
        WS_CONNECTIONS_ACTIVE.labels(endpoint="/ws/prices").dec()

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
    WS_CONNECTIONS_ACTIVE.labels(endpoint="/ws/swarm-debate").inc()
    start_time = time.perf_counter()
    status = "success"
    
    print(f"[WebSocket Debate] Agent session {session_id} connected")
    
    # Default parameters
    ticker = "BTC-USD"
    category = "CRYPTO"
    price = 67250.45
    
    # Try resolving asset from ticker if session_id is a ticker
    if session_id != "live":
        ticker = session_id.upper()

        
    db = SessionLocal()
    try:
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
        cache_hit = False
        try:
            cache = db.query(PredictionCache).filter(PredictionCache.ticker == ticker).order_by(PredictionCache.created_at.desc()).first()
            if cache:
                diff_pct = abs(price - cache.price_at_predict) / cache.price_at_predict
                if diff_pct < 0.01:
                    cache_hit = True
                    SWARM_CACHE_LOOKUPS.labels(status="hit").inc()
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
                    
                    # Send the final consensus forecast payload from cache
                    consensus_payload = {
                        "type": "consensus_forecast",
                        "ticker": ticker,
                        "verdict": asset.system_verdict if asset else "HOLD",
                        "confidence": float(asset.confidence_level) if asset else 50.0,
                        "predict_price_5s": cache.predict_price_5s,
                        "predict_price_5m": cache.predict_price_5m,
                        "predict_price_5h": cache.predict_price_5h,
                        "predict_price_5d": cache.predict_price_5d,
                        "session_id": session_id
                    }
                    await websocket.send_json(consensus_payload)
                    
                    db.close()
                    # Keep connection alive
                    while True:
                        await websocket.receive_text()
                        await asyncio.sleep(1)
                    return
        except WebSocketDisconnect:
            raise
        except Exception as e:
            print(f"[WebSocket Debate] Cache check failed: {e}")
            
        if not cache_hit:
            SWARM_CACHE_LOOKUPS.labels(status="miss").inc()
            
        swarm_engine_url = os.getenv("SWARM_ENGINE_URL") or getattr(settings, "SWARM_ENGINE_URL", None)
        db_session_id = f"cache_{uuid.uuid4().hex[:8]}"
        temp_forecast_data = {}
        
        async def _process_swarm_line(line_str: str):
            try:
                # Parse JSON output from swarm-engine
                data = json.loads(line_str)
                print(f"[Swarm Engine] {line_str}")
                sys.stdout.flush()
                
                # Intercept metrics payload
                if data.get("type") == "metrics":
                    agent_name = data.get("agent_name", "Unknown")
                    model = data.get("model", "unknown")
                    if data.get("event") == "awake":
                        SWARM_AGENT_AWAKENINGS.labels(agent_name=agent_name, model=model).inc()
                    prompt_tokens = data.get("prompt_tokens", 0)
                    completion_tokens = data.get("completion_tokens", 0)
                    total_tokens = data.get("total_tokens", 0)
                    SWARM_TOKEN_USAGE.labels(agent_name=agent_name, model=model, token_type="prompt").inc(prompt_tokens)
                    SWARM_TOKEN_USAGE.labels(agent_name=agent_name, model=model, token_type="completion").inc(completion_tokens)
                    SWARM_TOKEN_USAGE.labels(agent_name=agent_name, model=model, token_type="total").inc(total_tokens)
                    return
                
                # Intercept consensus_forecast
                if data.get("type") == "consensus_forecast":
                    temp_forecast_data.update({
                        "predict_price_5s": data.get("predict_price_5s"),
                        "predict_price_5m": data.get("predict_price_5m"),
                        "predict_price_5h": data.get("predict_price_5h"),
                        "predict_price_5d": data.get("predict_price_5d"),
                        "verdict": data.get("verdict"),
                        "confidence": data.get("confidence")
                    })

                
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
                print(f"[WebSocket Debate Log] {line_str}")
                sys.stdout.flush()

        print("[WebSocket Debate] Waiting for Swarm Semaphore...")
        async with SWARM_SEMAPHORE:
            print("[WebSocket Debate] Semaphore acquired.")
            
            if swarm_engine_url:
                # Microservice mode: query persistent swarm-engine container via HTTP stream
                import aiohttp
                url = f"{swarm_engine_url}/debate"
                params = {"ticker": ticker, "category": category, "price": price}
                print(f"[WebSocket Debate] Connecting to swarm-engine service: {url} with params {params}")
                
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, params=params) as response:
                            if response.status != 200:
                                err_text = await response.text()
                                raise RuntimeError(f"Swarm service returned status {response.status}: {err_text}")
                                
                            async for line in response.content:
                                line_str = line.decode('utf-8').strip()
                                if line_str:
                                    await _process_swarm_line(line_str)
                except Exception as stream_err:
                    print(f"[WebSocket Debate Service Stream Error] {stream_err}")
                    await websocket.send_json({"status": "error", "message": f"Swarm Engine Service connection error: {stream_err}"})
                    status = "error"
            else:
                # Fallback CLI mode: spawn local python command
                use_docker = os.getenv("MCP_USE_DOCKER", "False").lower() in ("true", "1", "yes")
                cwd = None
                if use_docker:
                    # Spawn swarm-engine in its own container on the host docker daemon
                    cmd = [
                        "docker", "run", "-i", "--rm",
                        "-v", "/var/run/docker.sock:/var/run/docker.sock",
                        "--network", "virtual-trader_default",
                        "-e", f"GEMINI_API_KEY={os.getenv('GEMINI_API_KEY', '')}",
                        "-e", f"DATABASE_URL=postgresql://postgres:postgres@db:5432/virtual_trader",
                        "-e", f"MCP_USE_DOCKER={os.getenv('MCP_USE_DOCKER', 'False')}",
                        "virtual-trader-swarm-engine",
                        "--ticker", ticker,
                        "--category", category,
                        "--price", str(price)
                    ]
                else:
                    # Build absolute path to swarm-engine main.py CLI locally
                    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    script_path = os.path.abspath(os.path.join(base_dir, "..", "swarm-engine", "src", "main.py"))
                    cmd = [
                        sys.executable,
                        script_path,
                        "--ticker", ticker,
                        "--category", category,
                        "--price", str(price)
                    ]
                    cwd = os.path.dirname(script_path)
                
                print(f"[WebSocket Debate] Spawning local CLI subprocess: {' '.join(cmd)}")
                env = os.environ.copy()
                if settings.GEMINI_API_KEY:
                    env["GEMINI_API_KEY"] = settings.GEMINI_API_KEY
                
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=cwd,
                    env=env
                )
                
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    line_str = line.decode('utf-8').strip()
                    if line_str:
                        await _process_swarm_line(line_str)
                        
                stderr_data = await process.stderr.read()
                if stderr_data:
                    print(f"[WebSocket Debate Subprocess Stderr] {stderr_data.decode('utf-8')}")
                await process.wait()
            
            # Save Prediction Cache (if data was collected successfully)
            if temp_forecast_data:
                try:
                    # Update Asset table with new verdict and confidence
                    asset = db.query(Asset).filter(Asset.ticker == ticker.upper()).first()
                    if asset:
                        asset.system_verdict = temp_forecast_data.get("verdict") or asset.system_verdict
                        asset.confidence_level = temp_forecast_data.get("confidence") or asset.confidence_level
                        db.commit()
                        print(f"[WebSocket Debate] Updated Asset {ticker} to {asset.system_verdict} ({asset.confidence_level}%)")
                    
                    new_cache = PredictionCache(
                        ticker=ticker,
                        session_id=db_session_id,
                        price_at_predict=price,
                        predict_price_5s=temp_forecast_data.get("predict_price_5s"),
                        predict_price_5m=temp_forecast_data.get("predict_price_5m"),
                        predict_price_5h=temp_forecast_data.get("predict_price_5h"),
                        predict_price_5d=temp_forecast_data.get("predict_price_5d")
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
        status = "error"
        print(f"[WebSocket Debate] Connection closed: {str(e)}")
    finally:
        db.close()
        duration = time.perf_counter() - start_time
        SWARM_DEBATE_DURATION.labels(status=status).observe(duration)
        WS_CONNECTIONS_ACTIVE.labels(endpoint="/ws/swarm-debate").dec()

