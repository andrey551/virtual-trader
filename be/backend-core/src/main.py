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
    await websocket.accept()
    print(f"[WebSocket Debate] Agent session {session_id} connected")
    
    # Mock debate messages representing the 10 agents arguing about market outlook
    mock_debate_messages = [
        {"agent": "Technical Node Agent", "avatar": "TECH_01", "msg": "Chỉ báo RSI đang rơi vào vùng quá bán (oversold) ngắn hạn. Mức hỗ trợ mạnh đang được duy trì vững vàng."},
        {"agent": "Fundamental Ledger Agent", "avatar": "FUND_02", "msg": "Tốc độ giảm nhiệt lạm phát lõi trong báo cáo CPI vừa qua là một bệ đỡ cơ bản vững chắc cho định giá tài sản."},
        {"agent": "Macro Risk Arbiter", "avatar": "MACR_03", "msg": "Nhưng hãy cẩn thận, sản lượng dầu cắt giảm từ OPEC có thể thổi bùng lại áp lực lạm phát chuỗi cung ứng."},
        {"agent": "Sentiment Indexer Agent", "avatar": "SENT_04", "msg": "Tâm lý tin tức vĩ mô (Sentiment score) đang dịch chuyển tích cực từ -0.2 lên +0.45 trong 24 giờ qua."},
        {"agent": "Volume Liquidity Node", "avatar": "VOLU_05", "msg": "Đồng ý. Volume mua chủ động ở vùng giá này tăng vọt 35%, cho thấy dòng tiền thông minh đang gom hàng."},
        {"agent": "Order Book Arbiter", "avatar": "BOOK_06", "msg": "Sổ lệnh Binance ghi nhận tường mua (buy walls) lớn ở mức giá ngay phía dưới. Lực bán đang cạn kiệt."},
        {"agent": "Volatility Estimator", "avatar": "VOLA_07", "msg": "Chỉ số biến động Bollinger Bands đang co thắt cực độ. Sắp có một cú bứt phá mạnh (breakout) xảy ra."},
        {"agent": "Correlated Flow Agent", "avatar": "FLOW_08", "msg": "Các tài sản tương quan chéo (như DXY và Lợi suất trái phiếu) đang giảm, tạo điều kiện thuận lợi cho đà phục hồi."},
        {"agent": "System Risk Auditor", "avatar": "RISK_09", "msg": "Tỷ lệ đòn bẩy ký quỹ đã giảm bớt, làm giảm rủi ro xảy ra các cú sập thanh lý hàng loạt (long squeeze)."},
        {"agent": "Consensus Leader Node", "avatar": "CONS_10", "msg": "Tổng hợp ý kiến từ 9 nodes, tỷ lệ đồng thuận tăng lên 88.5%. Tôi đề xuất xếp hạng Verdict là BUY với điểm số 85.0."}
    ]
    
    try:
        # Loop to stream agent messages step by step
        for item in mock_debate_messages:
            agent = item["agent"]
            avatar = item["avatar"]
            full_msg = item["msg"]
            
            # Send initial message header signaling agent is writing
            await websocket.send_json({
                "session_id": session_id,
                "agent_name": agent,
                "avatar_code": avatar,
                "message": "",
                "status": "TYPING"
            })
            await asyncio.sleep(0.5)
            
            # Stream the message text in chunks (simulating real-time typewriter thinking)
            chunk_size = 4
            for i in range(0, len(full_msg), chunk_size):
                chunk = full_msg[i:i+chunk_size]
                await websocket.send_json({
                    "session_id": session_id,
                    "agent_name": agent,
                    "avatar_code": avatar,
                    "message_chunk": chunk,
                    "status": "SPEAKING"
                })
                # Simulate typewriter latency
                await asyncio.sleep(0.1)
                
            # Signal message completed
            await websocket.send_json({
                "session_id": session_id,
                "agent_name": agent,
                "avatar_code": avatar,
                "message": full_msg,
                "status": "COMPLETED"
            })
            
            # Brief pause before next agent speaks
            await asyncio.sleep(2.5)
            
        # Hold connection open
        while True:
            await websocket.receive_text()
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        print(f"[WebSocket Debate] Agent session {session_id} disconnected")
    except Exception as e:
        print(f"[WebSocket Debate] Error: {str(e)}")
